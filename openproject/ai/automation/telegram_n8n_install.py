"""Install one dedicated outgoing workflow through authenticated local n8n APIs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import httpx

from automation.telegram_n8n import NAME, build_workflow
from n8n_owner import LocalN8n

HEADER_NAME = 'QLDAPM Telegram Notification Key'
BOT_NAME = 'QLDAPM AI Commander Telegram'
RUNTIME = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'QLDAPM/openproject-ai'


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def rows(value):
    return value.get('data', []) if isinstance(value, dict) else value


def verify_workflow(current,workflow,version):
    def nodes(values):
        return [{k:v for k,v in node.items() if k!='webhookId' or node.get('type')!='n8n-nodes-base.telegram'} for node in values]
    return (current.get('active') is True and current.get('versionId')==version
            and current.get('name')==workflow['name'] and current.get('connections')==workflow['connections']
            and nodes(current.get('nodes',[]))==nodes(workflow['nodes'])
            and all(current.get('settings',{}).get(k)==v for k,v in workflow['settings'].items()))


def install(api, token, key, receipt):
    receipt = Path(receipt)
    if receipt.exists():
        saved = json.loads(receipt.read_text(encoding='utf-8'))
        if not saved.get('workflow_id') or len(saved.get('created_credential_ids',[]))!=2:
            raise ValueError('PARTIAL_INSTALL_RECONCILE_BEFORE_RETRY')
        if saved.get('secret_hashes') != [hashlib.sha256(v.encode()).hexdigest() for v in (token,key)]:
            raise ValueError('EXISTING_CREDENTIALS_PRESERVED_CONFIG_CHANGED')
        current = api.request('GET','/rest/workflows/'+saved['workflow_id'])
        if not verify_workflow(current,build_workflow(*saved['created_credential_ids']),saved['version_id']):
            raise ValueError('EXISTING_WORKFLOW_CHANGED_REVIEW_REQUIRED')
        saved.update(status='PUBLISHED',published_at=saved.get('published_at') or time.time());save(receipt,saved)
        return saved
    workflows = rows(api.request('GET','/rest/workflows'))
    credentials = rows(api.request('GET','/rest/credentials'))
    if any(w.get('name') == NAME for w in workflows) or any(c.get('name') in {HEADER_NAME,BOT_NAME} for c in credentials):
        raise ValueError('EXISTING_NAMED_OBJECT_PRESERVED_RECONCILE_REQUIRED')
    state = {'status':'INSTALLING','secret_hashes':[hashlib.sha256(v.encode()).hexdigest() for v in (token,key)],
             'old_workflow_ids':[w['id'] for w in workflows], 'created_credential_ids':[]}
    save(receipt,state)
    # No update or delete endpoint is used, even during recovery from a partial install.
    for name,kind,data in [(HEADER_NAME,'httpHeaderAuth',{'name':'X-QLDAPM-Notification-Key','value':key}),
                           (BOT_NAME,'telegramApi',{'accessToken':token,'baseUrl':'https://api.telegram.org'})]:
        created = api.request('POST','/rest/credentials',{'name':name,'type':kind,'data':data})
        state['created_credential_ids'].append(created['id']);save(receipt,state)
    workflow = build_workflow(*state['created_credential_ids'])
    created = api.request('POST','/rest/workflows',workflow)
    identifier = created['id']
    if not re.fullmatch('[A-Za-z0-9_-]{1,128}',identifier):
        raise ValueError('N8N_WORKFLOW_ID_INVALID')
    state.update(workflow_id=identifier,version_id=created['versionId']);save(receipt,state)
    api.request('POST','/rest/workflows/'+identifier+'/activate',{'versionId':created['versionId']})
    current = api.request('GET','/rest/workflows/'+identifier)
    if not verify_workflow(current,workflow,created['versionId']):
        raise ValueError('N8N_PUBLISHED_WORKFLOW_READBACK_MISMATCH')
    state.update(status='PUBLISHED',published_at=time.time());save(receipt,state)
    return state


class API:
    def __init__(self):
        owner_file = RUNTIME / 'operator/n8n-main-owner/owner.json'
        owner = json.loads(owner_file.read_text(encoding='utf-8'))
        client = LocalN8n('http://localhost:5679')
        if owner['endpoint'] != client.base:
            raise ValueError('N8N_OWNER_ENDPOINT_MISMATCH')
        identity = client.request('/rest/login',{'emailOrLdapLoginId':owner['email'],'password':owner['password']})
        role = identity.get('role')
        if isinstance(role,dict):role=role.get('slug')
        if role != 'global:owner' or not client.cookie:
            raise PermissionError('N8N_OWNER_NOT_VERIFIED')
        self.client = httpx.Client(base_url=client.base,headers={'Cookie':client.cookie,'Origin':client.base,
            'Referer':client.base+'/'},follow_redirects=False,trust_env=False,timeout=30)

    def request(self,method,path,body=None):
        if method not in {'GET','POST'} or not re.fullmatch(r'/rest/(?:credentials|workflows)(?:/[A-Za-z0-9_-]+(?:/activate)?)?',path):
            raise PermissionError('N8N_INSTALL_ENDPOINT_DENIED')
        response=self.client.request(method,path,json=body)
        if response.status_code>=300:
            raise RuntimeError('N8N_INSTALL_HTTP_'+str(response.status_code))
        return response.json()['data']


def backup_n8n(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    target='/tmp/qldapm-telegram-backup-'+str(int(time.time()))+'.sqlite'
    code="const {DatabaseSync,backup}=require('node:sqlite');const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});backup(d,process.argv[1]).then(()=>d.close());"
    subprocess.run(['docker','exec','qldapm-n8n-main','node','-e',code,target],check=True,capture_output=True,timeout=120)
    subprocess.run(['docker','cp','qldapm-n8n-main:'+target,str(directory/'n8n.sqlite')],check=True,capture_output=True,timeout=120)
    subprocess.run(['docker','exec','qldapm-n8n-main','node','-e',"require('fs').unlinkSync(process.argv[1])",target],check=True,capture_output=True)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    from free_tier_staging import private_directory
    local=RUNTIME/'telegram-ai';config={}
    for line in (local/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            name,value=line.split('=',1);config[name.strip()]=value.strip().strip('"').strip("'")
    token=config.get('TELEGRAM_BOT_TOKEN','')
    key=(local/'secrets/notification.key').read_text().strip()
    if not re.fullmatch(r'[0-9]{5,16}:[A-Za-z0-9_-]{20,}',token) or not 32<=len(key)<=512:
        raise ValueError('LOCAL_TELEGRAM_TOKEN_AND_NOTIFICATION_KEY_REQUIRED')
    private=RUNTIME/'operator/telegram-notifications';private_directory(private)
    receipt=private/'install.json'
    if not receipt.exists():backup_n8n(private/('backup-'+str(int(time.time()))))
    api=API()
    try:result=install(api,token,key,receipt)
    finally:api.client.close()
    print(json.dumps({k:result[k] for k in ('status','workflow_id','version_id')}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'BLOCKED','error_type':type(error).__name__,
                          'reason':str(error) if type(error) in {ValueError,RuntimeError,PermissionError} else 'LOCAL_INSTALL_FAILED',
                          'existing_objects_overwritten':False}));raise SystemExit(1)

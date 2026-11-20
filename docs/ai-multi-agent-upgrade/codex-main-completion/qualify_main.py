"""Restore Main into a fresh isolated clone; never reset or clean existing resources."""
import ipaddress
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

OUT=Path(__file__).parent
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'openproject/ai'))
from free_tier_staging import private_directory
from jira_sync_backup import command, database_state

LABEL='qldapm.qualification=codex-main-20261020'
PREFIX='qldapm-codex-main-20261020'

def docker(*args,data=None,timeout=90):
    return command(['docker',*args],data=data,timeout=timeout).decode().strip()

def main():
    assert not (OUT/'clone.json').exists(), 'Clone exists; resume explicitly, never provision twice'
    backup=json.loads((OUT/'backup-receipt.json').read_text())
    private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/codex-main-completion/qualification'
    assert not private.exists() or not any(private.iterdir()), 'Private clone exists; reconcile before continuing'
    private_directory(private)
    net_ids=docker('network','ls','-q').splitlines()
    used=[ipaddress.ip_network(c['Subnet']) for n in json.loads(docker('network','inspect',*net_ids)) for c in (n['IPAM'].get('Config') or []) if c.get('Subnet')]
    free=[]
    for i in range(210,254):
        subnet=ipaddress.ip_network(f'10.253.{i}.0/28')
        if not any(subnet.overlaps(n) for n in used):free.append(str(subnet))
        if len(free)==2:break
    assert len(free)==2,'NO_FREE_SUBNET'
    db,web,net,front=[PREFIX+s for s in ('-db','-web','-internal','-front')]
    record={'label':LABEL,'private':str(private),'backup':backup['directory'],'names':{'db':db,'web':web,'network':net,'front':front},
            'image':docker('image','inspect','qldapm-openproject:codex-main-20261020','--format','{{.Id}}'),'status':'PREPARING'}
    (OUT/'clone.json').write_text(json.dumps(record,indent=2))
    docker('network','create','--internal','--subnet',free[0],'--label',LABEL,net)
    docker('network','create','--subnet',free[1],'--label',LABEL,front)
    password=secrets.token_hex(24)
    (private/'db.env').write_text('POSTGRES_DB=openproject\nPOSTGRES_PASSWORD=PUBLICATION_REDACTED\n')
    docker('run','-d','--name',db,'--label',LABEL,'--network',net,'--network-alias','qa-db',
           '--env-file',str(private/'db.env'),'--memory','512m','--mount',f'type=bind,src={backup["directory"]}/database.dump,dst=/backup.dump,readonly',
           'postgres@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3')
    for _ in range(40):
        p=subprocess.run(['docker','exec',db,'pg_isready','-U','postgres'],capture_output=True,timeout=5)
        if p.returncode==0:break
        time.sleep(1)
    else:raise RuntimeError('CLONE_DB_NOT_READY')
    docker('exec',db,'pg_restore','-U','postgres','--exit-on-error','--no-owner','-d','openproject','/backup.dump',timeout=180)
    expected=json.loads((Path(backup['directory'])/'database-state.json').read_text())
    actual=database_state(db)
    assert actual==expected, 'MAIN_DATABASE_RESTORE_PARITY_FAILED'
    record['restored_tables']=len(actual);record['restore_verified']=True
    env={'DATABASE_URL':'postgres://postgres:PUBLICATION_REDACTED@qa-db/openproject','SECRET_KEY_BASE':secrets.token_hex(64),
         'OPENPROJECT_HOST__NAME':'localhost:18088','OPENPROJECT_ADDITIONAL__HOST__NAMES':'["localhost:18088","127.0.0.1:18088"]',
         'OPENPROJECT_HTTPS':'false','OPENPROJECT_HSTS':'false','OPENPROJECT_WEB_WORKERS':'1','RAILS_ENV':'production',
         'OPENPROJECT_RAILS__CACHE__STORE':'file_store','OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL':'',
         'QLDAPM_QUALIFICATION':'codex-main-20261020','MIGRATE':'false'}
    (private/'core.env').write_text('\n'.join(k+'='+v for k,v in env.items())+'\n')
    docker('run','-d','--name',web,'--label',LABEL,'--network',net,'--memory','1536m','--env-file',str(private/'core.env'),
           '--entrypoint','sleep','--mount',f'type=bind,src={REPO}/openproject/ai/core,dst=/qa-tests,readonly',
           '--mount',f'type=bind,src={private},dst=/qa-private',record['image'],'infinity')
    docker('network','connect',front,web)
    record['status']='RESTORED_READY_FOR_TESTS'
    (OUT/'clone.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()

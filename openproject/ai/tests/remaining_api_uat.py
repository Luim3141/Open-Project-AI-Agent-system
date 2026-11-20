"""Real Native/Gateway qualification on existing owned synthetic fixtures; no serving targets."""
import concurrent.futures
import hashlib
import hmac
import json
import subprocess
import time
import uuid

import httpx
from tests.remaining_browser_uat import PRIVATE,OUT,BASE,GATEWAY
from tests.qualify_remaining import docker,snapshot


def main():
    data=json.loads((PRIVATE/'fixture-credentials.json').read_text());users=data['users']
    pm=next(a for a in users if a['role']=='PM');be=next(a for a in users if a['role']=='BE')
    identifier=data['work_package_id'];name='qldapm-rd-gateway-20261018'
    image=json.loads((OUT/'candidate-images.json').read_text())['gateway']['image']
    info=json.loads(docker('inspect',name))[0]
    assert info['Image']==image and info['Config']['Labels']['qldapm.qualification']=='remaining-20261018'
    assert all(a['login'].startswith('rd-fixture-') for a in users) and not (PRIVATE/'state/gemini.key').exists()
    report={'scope':'ISOLATED_REAL_NATIVE_NEW_FIXTURES_ONLY','image':image,'checks':[]}
    output=OUT/('api-uat-'+str(int(time.time()))+'.json');before=snapshot()
    def check(case,ok,actual=None):
        report['checks'].append({'id':case,'status':'PASS' if ok else 'FAIL','actual':actual,'exit_code':0 if ok else 1})
        output.write_text(json.dumps(report,indent=2));assert ok,case
    def command(account,action,args=None,key=None,auto=False):
        return httpx.post(GATEWAY+'/api/v1/commands',headers={'Authorization':'Bearer '+account['gateway_token']},
            json={'action':action,'arguments':args or {},'idempotency_key':key,'auto_execute':auto},trust_env=False,timeout=90)
    def native(account,path,method='GET',body=None):
        return httpx.request(method,BASE+path,auth=('apikey',account['token']),json=body,trust_env=False,timeout=60)
    def confirm(account,proposal,hash_value=None):
        assertion={'actor':account['id'],'project':data['project_id'],'audience':'qldapm-ai-ui','at':int(time.time()),
            'nonce':uuid.uuid4().hex,'operation':'confirm','command':{'id':proposal['id'],'hash':hash_value or proposal['hash']}}
        body=json.dumps(assertion).encode();signature=hmac.new((PRIVATE/'state/ui.key').read_bytes(),body,hashlib.sha256).hexdigest()
        return httpx.post(GATEWAY+'/internal/ui',content=body,
            headers={'Content-Type':'application/json','X-Qldapm-Signature':signature},trust_env=False,timeout=90)
    def wp():return native(pm,f'/api/v3/work_packages/{identifier}').json()
    def index(account):return command(account,'knowledge_ingest',{'id':identifier},uuid.uuid4().hex)
    def search(account):return command(account,'knowledge_search',{'query':'knowledge login'}).json()['result']['items']
    original=wp();check('API-FIXTURE-SCOPE',original['subject'].startswith('RD isolated knowledge login fixture'))
    def start(account):
        response=command(account,'start_ai_run',{'prompt':f'Phân tích yêu cầu công việc #{identifier}','engine':'supervisor'},uuid.uuid4().hex)
        return account,response
    started=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:admitted=list(pool.map(start,users))
    check('API-5-CONCURRENT-ADMISSIONS',all(r.status_code==200 for _,r in admitted),{'http':[r.status_code for _,r in admitted]})
    runs=[(a,r.json()['result']['id']) for a,r in admitted];pending=dict((rid,a) for a,rid in runs);finished={}
    deadline=time.monotonic()+180
    while pending and time.monotonic()<deadline:
        for rid,a in list(pending.items()):
            response=command(a,'get_ai_run',{'id':rid});value=response.json().get('result',{})
            if value.get('state')!='running':finished[rid]=value;pending.pop(rid)
        if pending:time.sleep(1)
    check('API-5-REAL-WORKERS',len(finished)==5 and all(r.get('state')=='done' and r['result'].get('engine')=='local_supervisor'
        and r['result']['model_used'] is False for r in finished.values()),{'completed':len(finished),'seconds':round(time.monotonic()-started,2)})
    check('API-CROSS-ACTOR-RUN-DENIED',command(be,'get_ai_run',{'id':next(r for a,r in runs if a['role']=='PM')}).status_code==403)
    for a in users:
        item=wp();text='RD isolated '+a['role']+' comment '+uuid.uuid4().hex[:8]
        response=command(a,'comment',{'id':identifier,'lock_version':item['lockVersion'],'text':text},uuid.uuid4().hex,True)
        activities=native(a,f'/api/v3/work_packages/{identifier}/activities').json().get('_embedded',{}).get('elements',[])
        check('API-COMMENT-'+a['role'],response.status_code==200 and any(text in row.get('comment',{}).get('raw','') for row in activities),{'http':response.status_code})
    item=wp();args={'id':identifier,'lock_version':item['lockVersion'],'changes':{'subject':item['subject']+' API verified'}}
    proposed=command(pm,'update_work_package',args,uuid.uuid4().hex);proposal=proposed.json()['result']
    check('API-PREVIEW-NO-WRITE',wp()['lockVersion']==item['lockVersion'] and proposal['human_confirmation_required'])
    check('API-PROPOSAL-CROSS-ACTOR',confirm(be,proposal).status_code==403)
    check('API-PROPOSAL-BAD-HASH',confirm(pm,proposal,'0'*64).status_code in (403,409,422))
    confirmed=confirm(pm,proposal);after=wp()
    check('API-PROPOSAL-NATIVE-READBACK',confirmed.status_code==200 and after['subject']==args['changes']['subject'] and after['lockVersion']>item['lockVersion'])
    replay=confirm(pm,proposal)
    check('API-PROPOSAL-NO-REPLAY',replay.status_code in (403,409,422) and wp()['lockVersion']==after['lockVersion'])
    old_run=next(r for a,r in runs if a['role']=='PM')
    stale=command(pm,'get_ai_run',{'id':old_run}).json()['result']['result']
    check('API-RUN-NATIVE-STALE',stale.get('stale') is True and 'agent_result' not in stale)
    pending=command(pm,'update_work_package',{'id':identifier,'lock_version':after['lockVersion'],'changes':{'subject':after['subject']+' MUST_NOT_APPLY'}},uuid.uuid4().hex).json()['result']
    changed=command(pm,'update_work_package',{'id':identifier,'lock_version':after['lockVersion'],'changes':{'subject':after['subject']+' fresh'}},uuid.uuid4().hex,True)
    current=wp();denied=confirm(pm,pending)
    check('API-PROPOSAL-STALE',changed.status_code==200 and denied.status_code in (409,422) and wp()['subject']==current['subject'])
    check('API-KNOWLEDGE-STALE-HIDDEN',search(pm)==[])
    for a in users:check('API-KNOWLEDGE-REINDEX-'+a['role'],index(a).status_code==200 and len(search(a))==1)
    deindex=command(pm,'knowledge_deindex',{'id':identifier},uuid.uuid4().hex)
    check('API-KNOWLEDGE-ACTOR-ISOLATION',deindex.status_code==200 and search(pm)==[] and len(search(be))==1)
    index(pm)
    # Second project is new and isolated; actor membership is real in both projects.
    other=json.loads((PRIVATE/'other-project.json').read_text());pid=other['project_id']
    native_type=next(t['id'] for t in command(pm,'get_project_options').json()['result']['types'] if t['name']=='Task')
    created=native(pm,'/api/v3/work_packages','POST',{'subject':'RD other project knowledge fixture',
        '_links':{'project':{'href':f'/api/v3/projects/{pid}'},'type':{'href':f'/api/v3/types/{native_type}'}}})
    check('API-OTHER-PROJECT-NATIVE-MEMBER',created.status_code==201,{'http':created.status_code})
    foreign=created.json()['id']
    check('API-KNOWLEDGE-CROSS-PROJECT',native(pm,f'/api/v3/work_packages/{foreign}').status_code==200 and
        command(pm,'knowledge_ingest',{'id':foreign},uuid.uuid4().hex).status_code==403 and
        command(pm,'get_work_package',{'id':foreign}).status_code==403)
    # Read-only backup runs in Linux, never a host SQLite connection to the bind.
    backup_name='qualification-knowledge-'+uuid.uuid4().hex+'.sqlite'
    code="""import json,sqlite3
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
s=KnowledgeStorage(KnowledgeStorageConfig(db_path='/state/knowledge.sqlite'));p=s.backup_file('/state/NAME')
r=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(p)))
with r._connection() as d:print(json.dumps({'documents':r.count_documents(),'chunks':d.execute('SELECT COUNT(*) FROM knowledge_chunks').fetchone()[0],'integrity':d.execute('PRAGMA integrity_check').fetchone()[0]}))
""".replace('NAME',backup_name)
    backed=json.loads(docker('exec',name,'python','-c',code));check('API-KNOWLEDGE-PHYSICAL-BACKUP',backed['documents']==5 and backed['chunks']>=5 and backed['integrity']=='ok',backed)
    busy=docker('exec',name,'python','-c',"import sqlite3;d=sqlite3.connect('/state/gateway.sqlite');print(d.execute(\"SELECT COUNT(*) FROM ai_queue WHERE state IN ('queued','executing')\").fetchone()[0]);d.close()")
    assert busy=='0'
    docker('restart',name)
    for _ in range(30):
        try:
            if httpx.get(GATEWAY+'/health',trust_env=False).status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(1)
    check('API-RESTART-PERSISTENCE',all(len(search(a))==1 and command(a,'get_agent_trace',{'id':rid}).json()['result']['total']>0 for a,rid in runs))
    usage=json.loads(docker('exec',name,'python','-c',"import sqlite3,json;d=sqlite3.connect('/state/gateway.sqlite');print(json.dumps({'usage_rows':d.execute('SELECT COUNT(*) FROM gemini_usage').fetchone()[0]}));d.close()"))
    check('API-ZERO-PROVIDER',usage['usage_rows']==0,usage)
    check('API-SERVING-UNCHANGED',snapshot()==before)
    report['passed']=True;report['finished_at']=time.time();output.write_text(json.dumps(report,indent=2));print(json.dumps({'evidence':str(output),'checks':len(report['checks']),'passed':True}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'passed':False,'error_type':type(error).__name__,'details_private':True}));raise SystemExit(1)

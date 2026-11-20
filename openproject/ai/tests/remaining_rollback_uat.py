"""Old Gateway image compatibility on a private post-candidate snapshot, never the original state."""
import json
import time
import uuid
import httpx
from tests.qualify_remaining import PRIVATE,OUT,LABEL,docker,snapshot


def main():
    name='qldapm-rd-rollback-'+uuid.uuid4().hex[:12];directory='rollback-copy-'+uuid.uuid4().hex
    old='sha256:006b9c6cd8cec7f5e41cf7ae4fe9abae762475b7fd685d8dde66191f10554233'
    source='qldapm-rd-gateway-20261018';info=json.loads(docker('inspect',source))[0]
    assert info['Config']['Labels']['qldapm.qualification']=='remaining-20261018'
    before=snapshot()
    code="""import sqlite3,pathlib,shutil,json
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
root=pathlib.Path('/state');target=root/'DIRECTORY';target.mkdir()
with sqlite3.connect(root/'gateway.sqlite') as source:
 assert source.execute("SELECT COUNT(*) FROM ai_queue WHERE state IN ('queued','executing')").fetchone()[0]==0
 with sqlite3.connect(target/'gateway.sqlite') as dest:source.backup(dest)
for name in ('config.json','credentials.json','ui.key','automation.key'):
 if (root/name).exists():shutil.copyfile(root/name,target/name)
config=json.loads((target/'config.json').read_text());config['hosts']+=['localhost:18097'];(target/'config.json').write_text(json.dumps(config))
KnowledgeStorage(KnowledgeStorageConfig(db_path=str(root/'knowledge.sqlite'))).backup_file(target/'knowledge.sqlite')
print('PRIVATE_SNAPSHOT_READY')
""".replace('DIRECTORY',directory)
    docker('exec',source,'python','-c',code)
    candidate=json.loads((OUT/'candidate-images.json').read_text())['gateway']['image']
    docker('run','-d','--name',name,'--label',LABEL,'--network','qldapm-rd-20261018',
        '-p','127.0.0.1:18097:8090','--memory','384m','--pids-limit','96','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges:true','--tmpfs','/tmp:size=32m,mode=1777',
        '--mount','type=bind,src='+str(PRIVATE/'state'/directory)+',dst=/state',candidate)
    docker('network','connect','qldapm-rd-loopback-20261018',name)
    for _ in range(30):
        try:
            if httpx.get('http://localhost:18097/health',trust_env=False).status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(1)
    fixture=json.loads((PRIVATE/'fixture-credentials.json').read_text());account=next(a for a in fixture['users'] if a['role']=='PM')
    checks=[]
    for actor in fixture['users']:
        r=httpx.post('http://localhost:18097/api/v1/commands',headers={'Authorization':'Bearer '+actor['gateway_token']},
            json={'action':'knowledge_search','arguments':{'query':'knowledge login'}},trust_env=False,timeout=60)
        items=r.json().get('result',{}).get('items',[])
        checks.append({'id':'RESTORE-KNOWLEDGE-'+actor['role'],'status':'PASS' if r.status_code==200 and len(items)==1
            and items[0]['native_id']==fixture['work_package_id'] else 'FAIL','http':r.status_code,'results':len(items)})
    docker('stop',name);docker('rm',name)
    docker('run','-d','--name',name,'--label',LABEL,'--network','qldapm-rd-20261018',
        '-p','127.0.0.1:18097:8090','--memory','384m','--pids-limit','96','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges:true','--tmpfs','/tmp:size=32m,mode=1777',
        '--mount','type=bind,src='+str(PRIVATE/'state'/directory)+',dst=/state',old)
    docker('network','connect','qldapm-rd-loopback-20261018',name)
    for _ in range(30):
        try:
            if httpx.get('http://localhost:18097/health',trust_env=False).status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(1)
    for action,args in [('get_work_package',{'id':fixture['work_package_id']}),('get_action_history',{})]:
        r=httpx.post('http://localhost:18097/api/v1/commands',headers={'Authorization':'Bearer '+account['gateway_token']},
            json={'action':action,'arguments':args},trust_env=False,timeout=60)
        checks.append({'id':'ROLLBACK-'+action,'http':r.status_code,'status':'PASS' if r.status_code==200 else 'FAIL'})
    sql="import sqlite3,json;d=sqlite3.connect('/state/gateway.sqlite');print(json.dumps({'integrity':d.execute('PRAGMA integrity_check').fetchone()[0],'runs':d.execute('SELECT COUNT(*) FROM agent_runs').fetchone()[0],'provider_usage':d.execute('SELECT COUNT(*) FROM gemini_usage').fetchone()[0]}));d.close()"
    state=json.loads(docker('exec',name,'python','-c',sql))
    checks.append({'id':'ROLLBACK-SCHEMA','status':'PASS' if state['integrity']=='ok' and state['runs']>=10 and state['provider_usage']==0 else 'FAIL','actual':state})
    docker('stop',name)
    assert snapshot()==before,'SERVING_CONTAINER_DRIFT'
    report={'scope':'RESTORED_CANDIDATE_THEN_OLD_GATEWAY_PRIVATE_COPY_ONLY','image':old,'restored_candidate':candidate,'checks':checks,
        'passed':all(c['status']=='PASS' for c in checks),'core_rollback':'Not boot-tested as a pair; candidate Core adds no migration, original image retained',
        'original_state_changed':False,'private_snapshot_retained':True}
    (OUT/'rollback-qualification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())

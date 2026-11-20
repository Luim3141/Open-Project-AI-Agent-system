"""One RUN ONCE for the exact WP/unit published by the verified planning run."""
import http.client,json,re
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway import engineering

root=Path('/state');store=Store(root);config=json.loads((root/'config.json').read_text())
service=engineering.scoped_service(Service(store,config,'/workspaces'),6)
native,identity=engineering.authorized(service,20)
parent_run='8751d17a-4c6c-4f5f-b00c-6e1239f5353c';unit='feedback-9d0ff35386a63183'
with store.connect() as db:
    plan=json.loads(db.execute('SELECT document FROM engineering_plans WHERE id=?',(parent_run,)).fetchone()[0])
    status=json.loads(db.execute('SELECT result FROM ai_runs WHERE id=?',(parent_run,)).fetchone()[0])
    definition=json.loads(db.execute('SELECT document FROM engineering_unit_definitions WHERE id=?',(unit,)).fetchone()[0])
    assert plan['state']=='PUBLISHED' and status['status']=='succeeded'
    assert plan['native_units'][unit]['id']==definition['native_id']==390
    assert db.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]==0
    assert db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]=='OFF'
package=native.package(390)
assert package['_links']['project']['href']=='/api/v3/projects/6' and package['_links']['parent']['href']=='/api/v3/work_packages/379'
credentials=json.loads((root/'credentials.json').read_text())
bearer=store.issue_token(20,'BA',store.credential(20),ttl=3600)
assert json.loads((root/'credentials.json').read_text())==credentials
body={'action':'engineering_run_once','arguments':{'native_id':390,'lock_version':package['lockVersion'],'unit':unit},
      'idempotency_key':'QLDAPM-E2E-20261102-PHASE2-FINAL-001-DEV','project_id':6,'auto_execute':False}
connection=http.client.HTTPConnection('127.0.0.1',8090,timeout=90)
try:
    connection.request('POST','/api/v1/commands',json.dumps(body).encode(),
                       {'Content-Type':'application/json','Host':'localhost:8090','Authorization':'Bearer '+bearer})
    response=connection.getresponse();document=json.loads(response.read());result=document.get('result',{})
    out={'http_status':response.status,'unit':unit,'native_id':390,'lock_version':package['lockVersion'],
         'run_id':result.get('id'),'deduplicated':result.get('deduplicated'),'mode':result.get('mode')}
    if response.status>=400:
        code=str(document.get('error','UNKNOWN'));out['error']=code if re.fullmatch('[A-Z][A-Z0-9_]{0,100}',code) else 'SEE_PRIVATE_SERVER_LOG'
    print(json.dumps(out),flush=True)
finally:connection.close()

"""Resume the same known-terminal run through the normal Gateway HTTP contract."""
import http.client,json,re
from pathlib import Path
from gateway.store import Store
root=Path('/state');store=Store(root);run='f136866a-b7e4-4ad8-bbd7-d846343163d0'
with store.connect() as db:
    checkpoint=db.execute('SELECT version,document FROM engineering_checkpoints WHERE run_id=?',(run,)).fetchone()
    saved=json.loads(checkpoint['document'])
    row=db.execute('SELECT state FROM ai_queue WHERE id=?',(run,)).fetchone()
    assert row['state']=='finished' and saved['terminal_known'] and saved['resumable']
    assert not db.execute("SELECT 1 FROM requests WHERE actor=20 AND key LIKE ? AND state NOT IN ('done','rejected')",('engineering-'+run+'-%',)).fetchone()
before=json.loads((root/'credentials.json').read_text());token=store.issue_token(20,'BA',store.credential(20),ttl=3600)
assert json.loads((root/'credentials.json').read_text())==before
body={'action':'engineering_resume','arguments':{'run_id':run,'checkpoint_version':checkpoint['version']},
      'idempotency_key':'QLDAPM-E2E-20261101-POST-ROLLOUT-001-RESUME-1','project_id':6,'auto_execute':False}
c=http.client.HTTPConnection('127.0.0.1',8090,timeout=90)
try:
    c.request('POST','/api/v1/commands',json.dumps(body).encode(),{'Content-Type':'application/json','Host':'localhost:8090','Authorization':'Bearer '+token})
    response=c.getresponse();doc=json.loads(response.read());result=doc.get('result',{})
    out={'http_status':response.status,'run_id':result.get('id'),'recovery_count':result.get('recovery_count'),'mode':result.get('mode')}
    if response.status>=400:
        code=str(doc.get('error','UNKNOWN'));out['error']=code if re.fullmatch('[A-Z][A-Z0-9_]{0,100}',code) else 'SEE_PRIVATE_SERVER_LOG'
    print(json.dumps(out),flush=True)
finally:c.close()

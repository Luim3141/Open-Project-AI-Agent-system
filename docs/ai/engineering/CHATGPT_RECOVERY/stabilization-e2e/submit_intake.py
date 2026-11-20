"""One controlled Project 6 intake through the UI's Gateway HTTP contract."""
import http.client,json,re
from pathlib import Path
from gateway.store import Store

root=Path('/state');store=Store(root)
before=json.loads((root/'credentials.json').read_text())
bearer=store.issue_token(20,'BA',store.credential(20),ttl=3600)
assert json.loads((root/'credentials.json').read_text())==before
marker='QLDAPM-E2E-20261102-STABILIZATION-001'
feedback=(marker+': Add GET /tasks/{task_id}/exists to check whether a numeric task ID exists. '
          'Return HTTP 200 JSON {"exists": true} for an existing task and {"exists": false} for a missing task; '
          'return HTTP 422 for a non-integer ID. Add focused automated tests. '
          'Preserve GET /tasks/{task_id}, /tasks/summary, /healthz, CRUD and search; do not change the SQLite schema. '
          'Produce one isolated feature branch and PR; do not merge or deploy it.')
body={'action':'engineering_plan','arguments':{'native_id':379,'lock_version':4,'feedback':feedback},
      'idempotency_key':marker,'project_id':6,'auto_execute':False}
c=http.client.HTTPConnection('127.0.0.1',8090,timeout=90)
try:
    c.request('POST','/api/v1/commands',json.dumps(body).encode(),{'Content-Type':'application/json','Host':'localhost:8090','Authorization':'Bearer '+bearer})
    response=c.getresponse();document=json.loads(response.read());result=document.get('result',{})
    out={'http_status':response.status,'marker':marker,'run_id':result.get('id'),'deduplicated':result.get('deduplicated'),'mode':result.get('mode')}
    if response.status>=400:
        code=str(document.get('error','UNKNOWN'));out['error']=code if re.fullmatch('[A-Z][A-Z0-9_]{0,100}',code) else 'SEE_PRIVATE_SERVER_LOG'
    print(json.dumps(out),flush=True)
finally:c.close()

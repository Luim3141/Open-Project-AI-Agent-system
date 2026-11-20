"""One controlled Project 6 intake through the UI's Gateway HTTP contract."""
import http.client,json,re
from pathlib import Path
from gateway.store import Store

root=Path('/state');store=Store(root)
before=json.loads((root/'credentials.json').read_text())
bearer=store.issue_token(20,'BA',store.credential(20),ttl=3600)
assert json.loads((root/'credentials.json').read_text())==before
marker='QLDAPM-E2E-20261102-PHASE2-FINAL-001'
feedback=(marker+': Add GET /tasks/{task_id}/title that returns HTTP 200 JSON {"id": task_id, "title": the exact stored title} for an existing numeric task ID. '
          'Return HTTP 404 for a missing task and HTTP 422 for a non-integer ID. Preserve Unicode titles exactly. '
          'Add focused automated tests for existing, missing, invalid and Unicode title. Preserve all existing CRUD, search, /healthz, /tasks/summary and /exists routes. '
          'Do not change the SQLite schema. Create one isolated feature branch and PR based on the latest verified PR8 source; do not merge or deploy it.')
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

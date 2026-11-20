"""One authorized Project 6 intake through the real Gateway HTTP command contract."""
import http.client
import json
import re
from pathlib import Path
from gateway.store import Store

root=Path('/state')
store=Store(root)
credentials=json.loads((root/'credentials.json').read_text())
native_token=store.credential(20)
bearer=store.issue_token(20,'BA',native_token,ttl=3600)
assert json.loads((root/'credentials.json').read_text())==credentials
marker='QLDAPM-E2E-20261101-POST-ROLLOUT-001'
feedback=(marker+': Add GET /tasks/{task_id} to retrieve one existing task by numeric ID. '
          'Return the existing id, title and status fields, or HTTP 404 if the task is absent. '
          'Add focused automated tests including persistence and invalid or absent IDs. '
          'Preserve GET /tasks/summary, /healthz, CRUD and search; do not change the database schema. '
          'Produce one isolated feature branch and PR, do not merge.')
body={'action':'engineering_plan','arguments':{'native_id':379,'lock_version':4,'feedback':feedback},
      'idempotency_key':marker,'project_id':6,'auto_execute':False}
connection=http.client.HTTPConnection('127.0.0.1',8090,timeout=90)
try:
    connection.request('POST','/api/v1/commands',json.dumps(body).encode(),
                       {'Content-Type':'application/json','Host':'localhost:8090','Authorization':'Bearer '+bearer})
    response=connection.getresponse();document=json.loads(response.read())
    result=document.get('result',{})
    out={'http_status':response.status,'marker':marker,'run_id':result.get('id'),
         'deduplicated':result.get('deduplicated'),'mode':result.get('mode')}
    if response.status>=400:
        code=str(document.get('error','UNKNOWN'))
        out['error']=code if re.fullmatch('[A-Z][A-Z0-9_]{0,100}',code) else 'SEE_PRIVATE_SERVER_LOG'
    print(json.dumps(out),flush=True)
finally:
    connection.close()

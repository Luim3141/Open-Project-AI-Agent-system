import base64,http.client,json,sys
from pathlib import Path
from gateway.store import Store

action=sys.argv[1]; key=sys.argv[2]; args=json.loads(base64.b64decode(sys.argv[3]))
root=Path('/state');store=Store(root);before=json.loads((root/'credentials.json').read_text())
token=store.issue_token(20,'BA',store.credential(20),ttl=3600)
assert json.loads((root/'credentials.json').read_text())==before
body={'action':action,'arguments':args,'idempotency_key':key,'project_id':6,'auto_execute':False}
c=http.client.HTTPConnection('127.0.0.1',8090,timeout=180)
try:
    c.request('POST','/api/v1/commands',json.dumps(body).encode(),{'Content-Type':'application/json','Host':'localhost:8090','Authorization':'Bearer '+token})
    r=c.getresponse(); result=json.loads(r.read()); print(json.dumps({'http_status':r.status,'response':result},ensure_ascii=False))
finally:c.close()

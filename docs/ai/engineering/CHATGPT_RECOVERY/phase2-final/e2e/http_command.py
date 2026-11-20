"""Gateway-container helper: one authorized HTTP command, never print a bearer."""
import http.client,json,sys
from pathlib import Path
from gateway.store import Store

body=json.loads(sys.stdin.read())
store=Store('/state');before=Path('/state/credentials.json').read_bytes()
bearer=store.issue_token(20,'BA',store.credential(20),ttl=1800)
assert Path('/state/credentials.json').read_bytes()==before
connection=http.client.HTTPConnection('127.0.0.1',8090,timeout=120)
try:
    connection.request('POST','/api/v1/commands',json.dumps({**body,'project_id':6}).encode(),
        {'Content-Type':'application/json','Host':'localhost:8090','Authorization':'Bearer '+bearer})
    response=connection.getresponse();data=json.loads(response.read())
    print(json.dumps({'http_status':response.status,'response':data},ensure_ascii=False))
finally:connection.close()

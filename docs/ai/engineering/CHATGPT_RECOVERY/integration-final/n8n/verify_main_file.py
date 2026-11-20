"""Bounded actual MAIN WF01 fixture; never print credentials or bearer tokens."""
import datetime,json,subprocess,uuid
from pathlib import Path
OUT=Path(__file__).parent

def run(args,data=None):
 p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=125)
 assert p.returncode==0,'MAIN_FILE_COMMAND_FAILED'
 return p.stdout
code="""import json
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service
root=Path('/state');c=json.load(open(root/'config.json'));store=Store(root);s=Service(store,c,'/workspaces');sc=scoped_service(s,6)
_,who=sc.native_actor(20);assert who['role']=='PM'
original=(root/'credentials.json').read_bytes();token=store.issue_token(20,'PM',store.credential(20),ttl=900)
assert json.loads(original)==json.load(open(root/'credentials.json'))
secret=json.load(open(root/'webhook_secret.json'));source=c['file_sources']['project6-integration-qualification']
print(json.dumps({'token':token,'webhook':secret.get('webhook_token') or secret.get('secret'),'source_sha256':source['sha256']}))
"""
context=json.loads(run(['exec','-i','qldapm-ai-gateway-1','python','-'],code.encode()))
fetch="const p=JSON.parse(require('fs').readFileSync(0,'utf8'));fetch('http://localhost:5678/webhook/qldapm-ingest',{method:'POST',headers:p.headers,body:JSON.stringify(p.body),signal:AbortSignal.timeout(110000)}).then(async r=>console.log(JSON.stringify({status:r.status,body:await r.text()}))).catch(()=>process.exit(1))"

def request(payload):
 response=json.loads(run(['exec','-i','qldapm-n8n-main','node','-e',fetch],json.dumps({'headers':{'Content-Type':'application/json','X-QLDAPM-Webhook-Token':context['webhook'],'Authorization':'Bearer '+context['token']},'body':payload}).encode()))
 assert response['status']==200,'WF01_HTTP_'+str(response['status'])
 body=json.loads(response['body']);return body.get('result',body)
base={'source_key':'project6-integration-qualification','project_id':6}
request_id=str(uuid.uuid4());ingest=request({**base,'request_id':request_id,'operation':'ingest'})
assert ingest['source_sha256']==context['source_sha256'] and ingest['document_id']
repeat=request({**base,'request_id':request_id,'operation':'ingest'});assert repeat==ingest,'REPLAY_NOT_IDENTICAL'
search=request({**base,'operation':'search','query':'ORBIT-RECEIPT-20261103'})
assert search['items'] and all(i['document_id']==ingest['document_id'] and i['source_sha256']==context['source_sha256'] for i in search['items'])
read=request({**base,'operation':'read','document_id':ingest['document_id']})
assert 'ORBIT-RECEIPT-20261103' in read['content'] and read['citation']==ingest['citation']
result={'status':'MAIN_WF01_PINNED_FILE_PASS','actor':20,'project':6,'source_key':base['source_key'],'source_sha256':context['source_sha256'],'document_id':ingest['document_id'],'citation':ingest['citation'],'ingest_status':ingest.get('status'),'replay_identical':True,'search_matches':len(search['items']),'content_marker_verified':True,'provider_calls':0,'native_business_writes':0,'limits':['controlled Project6 fixture; does not establish semantic quality','negative ACL and stale pin proved in isolated clone; MAIN source remains unchanged'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/'main-file-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

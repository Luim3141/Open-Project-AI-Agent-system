"""MAIN scheduled collectors: actual daily webhook and signed weekly machine branch."""
import datetime,json,subprocess
from pathlib import Path

out=Path(__file__).parent
code=r'''
import hashlib,hmac,json,time,httpx,uuid
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from gateway.service import Service
from gateway.store import Store,canonical,digest
from gateway.automation import signing_message,signing_key
from gateway.daily_brief import day,projection,fingerprint
from gateway.weekly_report import scheduled_week
root=Path('/state');config=json.load(open(root/'config.json'));store=Store(root);service=Service(store,config,'/workspaces')
assert config['automation_readers']==[20,21,22,23]
secret_doc=json.load(open(root/'webhook_secret.json'));secret=secret_doc.get('webhook_token') or secret_doc['secret']
url=urlsplit(config['n8n_lifecycle']['webhook_url']);daily_url=urlunsplit((url.scheme,url.netloc,'/webhook/qldapm-daily-brief','',''))
with httpx.Client(timeout=110,follow_redirects=False,trust_env=False) as client:
 first=client.post(daily_url,json={},headers={'X-QLDAPM-Webhook-Token':secret});assert first.status_code==200
 daily=first.json()['result'];assert daily['state']=='COMPLETED' and daily['status']=='READY' and daily['ready']==daily['targets']==4
 again=client.post(daily_url,json={},headers={'X-QLDAPM-Webhook-Token':secret});assert again.status_code==200 and again.json()['result']==daily
 issued=int(time.time());_,key=scheduled_week(issued)
 command={'version':1,'kind':'weekly_summary','request_key':key,'nonce':'demo-final-'+str(uuid.uuid4()),'issued_at':issued}
 machine=(root/'automation.key').read_text();signature=hmac.new(signing_key(machine).encode(),signing_message(command),hashlib.sha256).hexdigest()
 headers={'Host':'localhost:18089','X-QLDAPM-Machine-Key':machine,'X-QLDAPM-Command-Signature':signature}
 response=client.post('http://127.0.0.1:8090/internal/automation/commands',json=command,headers=headers);assert response.status_code==200
 weekly=response.json()['result'];assert weekly['state']=='COMPLETED' and weekly['status']=='READY' and weekly['ready']==weekly['targets']==4
 replay=client.post('http://127.0.0.1:8090/internal/automation/commands',json=command,headers=headers);assert replay.status_code==200 and replay.json()['result']==weekly
proof=[]
for actor in [20,21,22,23]:
 native,who=service.native_actor(actor);snapshot=projection(native.summary(actor));report=store.daily_brief(actor,5,day())
 assert report['state']=='READY' and report['snapshot']==snapshot and report['fingerprint']==fingerprint(actor,who['role'],5,snapshot)
 proof.append({'actor':actor,'project':5,'count':snapshot['count'],'fingerprint_verified':True,'source':'fresh Native daily_summary GET'})
try:service.native_actor(19);raise AssertionError('ACTOR19_MUST_REMAIN_DENIED')
except PermissionError:denied=True
with store.connect() as db:
 persisted=[]
 for item in weekly['reports']:
  actor=item['actor'];row=db.execute('SELECT document,refs FROM operational_reports WHERE id=? AND actor=? AND project=5',(item['report_id'],actor)).fetchone();assert row
  document=json.loads(row[0]);references=json.loads(row[1]);assert references
  persisted.append({'actor':actor,'report_id':item['report_id'],'document_sha256':digest(canonical(document)),'reference_count':len(references)})
print(json.dumps({'status':'LIVE_REPORT_COLLECTORS_VERIFIED','daily':{k:daily.get(k) for k in ['run_id','state','status','targets','ready','target_selection']},
 'weekly':{k:weekly.get(k) for k in ['run_id','state','status','targets','ready','target_selection']},'daily_native_source_readback':proof,
 'weekly_persisted_readback':persisted,'actor19_still_denied':denied,'retry_idempotency':'same persisted receipt on duplicate daily webhook and exact signed weekly command',
 'route':{'daily':'actual MAIN WF07 webhook → credential HMAC/machine → collector','weekly':'exact signed scheduled machine contract; actual WF12 branch exercised on n8n clone, MAIN cron read-back separately'},
 'native_writes':0,'model_calls':0}))
'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=260)
if p.returncode:
 import os
 private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/demo-final-report-readback-failure.log'
 private.write_bytes(p.stdout+p.stderr);raise RuntimeError('MAIN_REPORT_READBACK_FAILED_PRIVATE_LOG')
result=json.loads(p.stdout.decode().splitlines()[-1]);result['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'main-report-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

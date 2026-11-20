"""Exact serving/source/pins/worker/gate verification; no provider or Native writes."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[5];out=Path(__file__).parent
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
deploy=json.loads((out/'deployment.json').read_text());names={'gateway':'qldapm-ai-gateway-1','core':'qldapm-openproject-web-1','n8n':'qldapm-n8n-main'}
def run(args):return subprocess.check_output(args,timeout=60)
containers={}
for role,name in names.items():
 row=json.loads(run(['docker','inspect',name]))[0]
 if role in deploy['images']:assert row['Image']==deploy['images'][role] and row['State']['Health']['Status']=='healthy'
 containers[role]={'image':row['Image'],'state':row['State']['Status'],'health':row['State'].get('Health',{}).get('Status','NOT_CONFIGURED')}
pin=json.loads((runtime/'openproject-ai/image-lock.json').read_text())
assert pin['AI_IMAGE']==deploy['images']['gateway'] and pin['CORE_IMAGE']==deploy['images']['core']
assert json.loads((runtime/'openproject/ui-bridge.yml').read_text())['services']['web']['image']==deploy['images']['core']
files={}
for rel,expected in deploy['source_files'].items():
 source=root/rel;assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
 gateway='/gateway/' in rel;internal='/app/gateway/'+source.name if gateway else '/app/'+rel.split('/core/overlay/',1)[1]
 assert run(['docker','exec',names['gateway' if gateway else 'core'],'sha256sum',internal]).decode().split()[0]==expected
 files[rel]=expected
host={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'openproject/ai/automation'/n for n in ['engineering_worker.py','openclaw_health.py','openclaw_provider_gate.py']]}
code=r'''import json,sqlite3,time
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
r='b7fd6aec-3357-495f-b9e5-f7ba04d67ad6'
worker=d.execute('select seen,run_id from engineering_worker_state where project=6').fetchone()
row=d.execute('select state,payload from ai_queue where id=?',(r,)).fetchone();cp=d.execute('select version,document from engineering_checkpoints where run_id=?',(r,)).fetchone()
print(json.dumps({'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0],
'active':d.execute("select count(*) from ai_queue where state!='finished'").fetchone()[0],
'worker_age_seconds':time.time()-worker[0],'worker_run_id':worker[1],
'provider_receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0],
'wp391':{'queue_state':row[0],'recovery_count':json.loads(row[1]).get('recovery_count'),'checkpoint_version':cp[0],
'generation_calls':d.execute("select count(*) from gemini_call_receipts where run_id=? and json_extract(document,'$.phase')='generateContent'",(r,)).fetchone()[0]}}))'''
engineering=json.loads(subprocess.check_output(['docker','exec','-i',names['gateway'],'python','-'],input=code.encode(),timeout=30))
assert engineering['mode']=='OFF' and engineering['active']==0 and engineering['worker_age_seconds']<30 and engineering['worker_run_id'] is None
gate_code="import json,hashlib;from pathlib import Path;d=json.loads(Path('/root/.qldapm-openclaw/active.json').read_text());print(json.dumps({'active':d.get('active'),'sha256':hashlib.sha256(Path('/root/.qldapm-openclaw/provider_gate.py').read_bytes()).hexdigest()}))"
gate=json.loads(run(['wsl','-d','OpenClawGateway','-u','root','--exec','/usr/bin/python3','-c',gate_code]))
assert gate['active'] is False and gate['sha256']==host['openproject/ai/automation/openclaw_provider_gate.py']
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'SERVING_SOURCE_IMAGES_PINS_WORKER_GATE_VERIFIED','containers':containers,
 'runtime_source_sha256':files,'host_source_sha256':host,'engineering':engineering,'provider_gate':gate,'owner_uat':'PENDING OWNER'}
(out/'final-live-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

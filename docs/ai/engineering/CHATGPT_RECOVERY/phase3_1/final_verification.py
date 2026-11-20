"""Verify serving allowlist/pins and preserve execution/data fingerprints after final rollout."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).parent
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
deployment=json.loads((OUT/'deployment.json').read_text())
images=deployment['images']
names={'gateway':'qldapm-ai-gateway-1','core':'qldapm-openproject-web-1','n8n':'qldapm-n8n-main'}
containers={}
for role,name in names.items():
    row=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
    if role in images:assert row['Image']==images[role] and row['State']['Health']['Status']=='healthy'
    containers[role]={'image':row['Image'],'state':row['State']['Status'],'health':row['State'].get('Health',{}).get('Status','NOT_CONFIGURED')}
pins=json.loads((runtime/'openproject-ai/image-lock.json').read_text())
assert pins['AI_IMAGE']==images['gateway'] and pins['CORE_IMAGE']==images['core']
assert json.loads((runtime/'openproject/ui-bridge.yml').read_text())['services']['web']['image']==images['core']
files={}
for rel,expected in deployment['source_files'].items():
    source=ROOT/rel
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected,'HOST_SOURCE_CHANGED '+rel
    is_gateway='/gateway/' in rel
    internal='/app/gateway/'+source.name if is_gateway else '/app/'+rel.split('/core/overlay/',1)[1]
    actual=subprocess.check_output(['docker','exec',names['gateway' if is_gateway else 'core'],'sha256sum',internal]).decode().split()[0]
    assert actual==expected,'SERVING_SOURCE_MISMATCH '+rel
    files[rel]=actual
worker=ROOT/'openproject/ai/automation/engineering_worker.py'
worker_hash=hashlib.sha256(worker.read_bytes()).hexdigest()
task=subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',"(Get-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery').State.ToString()"]).decode().strip()
assert task=='Running'
baseline=json.loads((OUT/'wp391-before.json').read_text())
code="""import sqlite3,json,hashlib,time
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);out={}
for table,key in [('ai_queue','id'),('ai_runs','id'),('engineering_checkpoints','run_id')]:
 rows=d.execute('select * from '+table+' where '+key+'=?',('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6',)).fetchall()
 out[table]=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
out['provider_receipts']=d.execute('select count(*) from gemini_call_receipts').fetchone()[0]
out['mode']=d.execute('select mode from engineering_control where project=6').fetchone()[0]
out['active']=d.execute("select count(*) from ai_queue where state!='finished'").fetchone()[0]
worker=d.execute('select seen,run_id from engineering_worker_state where project=6').fetchone()
out['worker_age_seconds']=time.time()-worker[0];out['worker_run_id']=worker[1]
print(json.dumps(out))
"""
engineering=json.loads(subprocess.check_output(['docker','exec',names['gateway'],'python','-c',code]))
assert all(engineering[key]==baseline[key] for key in ['ai_queue','ai_runs','engineering_checkpoints','provider_receipts'])
assert engineering['mode']=='OFF' and engineering['active']==0 and engineering['worker_age_seconds']<30 and engineering['worker_run_id'] is None
gate_code="import json;from pathlib import Path;d=json.loads(Path('/root/.qldapm-openclaw/active.json').read_text());print(json.dumps({'active':d.get('active')}))"
provider_gate=json.loads(subprocess.check_output(['wsl','-d','OpenClawGateway','-u','root','--exec','/usr/bin/python3','-c',gate_code],timeout=30))
assert provider_gate['active'] is False
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'SERVING_SOURCE_IMAGES_PINS_AND_EXECUTION_PRESERVATION_PASS',
    'containers':containers,'engineering':engineering,'scheduled_worker':task,'host_worker_sha256':worker_hash,
    'runtime_source_sha256':files,'image_pins_match':True,'provider_gate':provider_gate,'provider_inference_calls':0,'wp391_resume_executed':False,
    'owner_uat':'PENDING OWNER','scope':'Exact allowlist and scoped Project5 integrity snapshots; not whole DB/physical DR/whole-image coding E2E'}
(OUT/'final-live-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ['status','containers','engineering','scheduled_worker','owner_uat']}))

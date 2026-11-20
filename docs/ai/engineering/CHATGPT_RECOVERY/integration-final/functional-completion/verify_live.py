"""Final read-only serving/source/pin/idle verification; never starts inference."""
import datetime,hashlib,json,os,subprocess,time,urllib.request
from pathlib import Path
from status_patch import release,OUT
from fresh_e2e import py

deploy=json.loads((OUT/'status-patch/deployment.json').read_text())
images={**deploy['images'],'n8n':'sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269'}
containers={}
for role,image in images.items():
    name=release.TARGETS[role][0] if role!='n8n' else 'qldapm-n8n-main'
    row=json.loads(release.run(['docker','inspect',name]))[0]
    assert row['Image']==image and row['State']['Status']=='running'
    if role!='n8n':assert row['State']['Health']['Status']=='healthy'
    containers[role]={'image':image,'state':row['State']['Status'],'health':row['State'].get('Health',{}).get('Status','NOT_CONFIGURED')}
    if role!='n8n':assert release.runtime_hashes(role)=={k:v for k,v in deploy['source_hashes'].items() if release.SOURCES[k][0]==role}
release.guard_sources(release.ROOT,deploy['source_hashes'])
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
pins=json.loads((runtime/'openproject-ai/image-lock.json').read_text());assert pins['AI_IMAGE']==images['gateway'] and pins['CORE_IMAGE']==images['core']
assert json.loads((runtime/'openproject/ui-bridge.yml').read_text())['services']['web']['image']==images['core']
config=json.loads((runtime/'openproject-ai/gateway/config.json').read_text())
assert config['engineering']['github_sync']['enabled'] and config['n8n_integration']['enabled'] and not config.get('maintenance')
release.queue()
state=py("""import sqlite3,json,time;c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);w=c.execute('select seen,run_id from engineering_worker_state where project=6').fetchone()
out={'mode':c.execute('select mode from engineering_control where project=6').fetchone()[0],'active':c.execute("select count(*) from ai_queue where state!='finished'").fetchone()[0],'worker_age_seconds':time.time()-w[0],'worker_run_id':w[1],'provider_receipts':c.execute('select count(*) from gemini_call_receipts').fetchone()[0],'runs':{}}
for rid in ('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6','301dbdd8-6f6f-4df4-b6c6-b5ca3f073795'):
 r=c.execute('select q.state,q.payload,r.result from ai_queue q join ai_runs r on r.id=q.id where q.id=?',(rid,)).fetchone();p=json.loads(r[1]);v=json.loads(r[2]);out['runs'][rid]={'queue_state':r[0],'result_status':v.get('status'),'error':v.get('error'),'recovery_count':p.get('recovery_count',0),'head_sha':v.get('head_sha'),'pr_url':v.get('pr_url'),'provider_calls':c.execute('select count(*) from gemini_call_receipts where run_id=?',(rid,)).fetchone()[0]}
print(json.dumps(out))""")
assert state['worker_age_seconds']<30 and state['worker_run_id'] is None
gate=json.loads(release.run(['wsl','-d','OpenClawGateway','-u','root','--exec','/usr/bin/python3','-c',"import json;from pathlib import Path;d=json.loads(Path('/root/.qldapm-openclaw/active.json').read_text());print(json.dumps({'active':d.get('active')}))"]))
assert gate['active'] is False
with urllib.request.urlopen('http://127.0.0.1:5679/healthz/readiness',timeout=5) as r:assert r.status==200
with urllib.request.urlopen('http://127.0.0.1:18789/readyz',timeout=5) as r:openclaw=json.load(r)
assert openclaw.get('ready') is True and openclaw.get('coreReady') is True
cli=json.loads((runtime/'openproject-ai/gateway/openclaw-health.json').read_text())
assert cli['health']=='READY' and cli['gateway_rpc_ok'] is True and time.time()-cli['checked_at']<150
host={name:hashlib.sha256((release.ROOT/'openproject/ai/automation'/name).read_bytes()).hexdigest() for name in ('engineering_worker.py','workflow_status_snapshot.py','openclaw_health.py','openclaw_provider_gate.py')}
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'SERVING_SOURCE_IMAGES_PINS_IDLE_GATE_VERIFIED','containers':containers,'source_hashes':deploy['source_hashes'],'host_source_hashes':host,'engineering':state,'provider_gate_active':False,'github_sync_enabled':True,'n8n_integration_enabled':True,'openclaw':{'http_ready':True,'core_ready':True,'cli':cli},'browser_uat':'NOT_PERFORMED'}
(OUT/'final-live-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'engineering':state,'provider_gate_active':False}))

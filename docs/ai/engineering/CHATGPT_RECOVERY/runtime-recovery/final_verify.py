"""Final serving/source/control/data verification with explicit authorized test deltas."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
OUT=Path(__file__).parent
base=json.loads((OUT/'baseline.json').read_text());smoke=json.loads((OUT/'isolated-provider-smoke.json').read_text())
code=r'''
import sqlite3,json,time,hashlib,sys
from pathlib import Path
from gateway.engineering import scoped_service,status
from gateway.service import Service
from gateway.store import Store
root=Path('/state');service=scoped_service(Service(Store(root),json.loads((root/'config.json').read_text()),'/workspaces'),6);s=status(service,18)
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
names=['engineering_control','engineering_owner_revision','ai_queue','ai_runs','engineering_checkpoints','engineering_unit_definitions','engineering_plans','delegated_control','gemini_usage','gemini_blocks','gemini_recovery','gemini_call_receipts'];pins={}
for name in names:
 rows=[dict(r) for r in d.execute('SELECT * FROM '+name)];data=sorted(json.dumps(r,sort_keys=True,ensure_ascii=False) for r in rows);pins[name]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(data).encode()).hexdigest()}
unknown=[dict(r) for r in d.execute("SELECT * FROM requests WHERE state NOT IN ('done','rejected') ORDER BY rowid")];n=int(sys.argv[1])
pins['unknown_requests']={'count':len(unknown),'original_subset_sha256':hashlib.sha256(json.dumps(sorted(json.dumps(r,sort_keys=True) for r in unknown[:n])).encode()).hexdigest(),'extra':[{'actor':r['actor'],'key':r['key'],'action':json.loads(r['payload'])['action']} for r in unknown[n:]]}
last=json.loads(d.execute('SELECT document FROM gemini_call_receipts ORDER BY rowid DESC LIMIT 1').fetchone()[0]);last={k:last.get(k) for k in ['id','actor','run_id','agent','phase','source','state','http_status','usage','at','completed_at']}
commands=[json.loads(r[0]) for r in d.execute('SELECT document FROM engineering_owner_commands ORDER BY sequence DESC LIMIT 12')]
tables={r[0] for r in d.execute("SELECT name FROM sqlite_master WHERE type='table'")}
dead=[]
if 'integration_event_outbox' in tables:
 for r in d.execute("SELECT state,attempts,document FROM integration_event_outbox WHERE state='DEAD'"):
  event=json.loads(r['document'])
  if event.get('payload',{}).get('native_id')==385:dead.append({'state':r['state'],'attempts':r['attempts'],'event_id':event['event_id'],'timestamp':event.get('timestamp')})
print(json.dumps({'pins':pins,'control':s['control'],'queue':s['queue'],'worker':s['delivery_worker'],'delegation':s['delegated_approval']['enabled'],'native':s['tasks'],'provider_health':s['provider_health'],'integration_health':s['integration_health'],'schedule':s['reporting_schedule'],'prs':[{k:r.get(k) for k in ['number','state','merged_at','mergedAt','url']} for r in s['github'].get('prs',[]) if r.get('number') in [11,12]],'github_operations':s['github_operations'],'commands':commands,'last_provider_receipt':last,'wp385_dead_events':dead}))
'''
v=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code,str(base['pins']['unknown_requests']['count'])],timeout=70))
(OUT/'final-candidate-readback.json').write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
allowed={'engineering_control','engineering_owner_revision','gemini_usage','gemini_call_receipts','unknown_requests'}
for k,p in base['pins'].items():
    if k not in allowed:assert v['pins'][k]==p,k
assert v['pins']['unknown_requests']['original_subset_sha256']==base['pins']['unknown_requests']['sha256']
extra=v['pins']['unknown_requests']['extra'];assert extra==[{'actor':18,'key':'owner6:'+hashlib.sha256(b'62c2ecdc-6f47-4000-9eed-79f21e9e9350').hexdigest(),'action':'engineering_run_once'}]
assert any(c.get('request_id')=='62c2ecdc-6f47-4000-9eed-79f21e9e9350' and c['accepted'] is False and c['reason_code']=='NO_ELIGIBLE_WORK' for c in v['commands'])
assert v['pins']['gemini_call_receipts']['count']==base['pins']['gemini_call_receipts']['count']+1
assert v['last_provider_receipt']['id']==smoke['receipt_id'] and v['last_provider_receipt']['http_status']==200 and v['last_provider_receipt']['run_id'] is None
assert v['control']['desired_mode']=='PAUSED' and v['control']['effective_state']=='PAUSED' and v['queue']['active']==0 and v['delegation'] is False
assert v['control']['state_revision']==50 and v['worker']['state']=='ALIVE'
protected=[r for r in v['native'] if r['id'] in {386,387,389,390,391,394}];assert len(protected)==6 and all(r['status']=='READY FOR RELEASE' and r['lock_version']==10 for r in protected)
sys.path.insert(0,str(OUT.parent/'button-audit'));import release_buttons
manifest=json.loads((OUT.parent/'button-audit/candidate-v10/manifest.json').read_text())
for role,image in manifest['images'].items():
    row=release_buttons.release.inspect(role);assert row['Image']==image and row['State']['Health']['Status']=='healthy'
    assert release_buttons.release.runtime_hashes(role)=={k:h for k,h in manifest['source_hashes'].items() if release_buttons.release.SOURCES[k][0]==role}
v['images']=manifest['images'];v['n8n_image']=base['containers']['qldapm-n8n-main']['image']
host=json.loads((OUT/'host-release.json').read_text());root=OUT.resolve().parents[4]
assert all(hashlib.sha256((root/'openproject/ai/automation'/name).read_bytes()).hexdigest()==value for name,value in host['files'].items())
v.update(status='RESTART_AND_POST_UAT_INVARIANTS_VERIFIED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host_source_hashes=host['files'],legitimate_deltas={'control_revision':'47→50 by explicit OFF/AUTO_IDLE/PAUSED UAT','provider_receipts':'533→534: exactly one authorized isolated fixed-public generation','gemini_usage':'One real shared-limiter reservation/settlement, limits unchanged','pending_requests':'Original38 byte-for-byte preserved; one new conservative reservation from rejected no-work request62c2... has a durable NO_ELIGIBLE_WORK rejection; no admission/Native effect. No SQLite state was manually completed.','business':'One read-only Sprint Risk source/event/report+notification and GitHub Sync; no Native writes'})
(OUT/'final-live-verification.json').write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'status':v['status'],'revision':v['control']['state_revision'],'provider_receipts':v['pins']['gemini_call_receipts']['count'],'queue':v['queue']['active'],'worker':v['worker']['state'],'provider':v['provider_health']['state'],'protected_native':len(protected),'prs':v['prs']}))

"""Fresh serving image/source, safe state and protected counter read-back."""
import datetime,json,os,subprocess,uuid
from pathlib import Path
import httpx
import release_buttons
OUT=Path(__file__).parent
release=release_buttons.release
manifest=json.loads((release_buttons.BUNDLE/'manifest.json').read_text())
proof={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'images':manifest['images'],'source_hashes':manifest['source_hashes']}
for role,image in manifest['images'].items():
    row=release.inspect(role)
    assert row['Image']==image and row['State']['Health']['Status']=='healthy'
    assert release.runtime_hashes(role)=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]==role}
release.guard_sources(release.ROOT,manifest['source_hashes'])
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/cc-stabilization'
token=json.loads((private/'baseline-native.json').read_text(encoding='utf-8'))['token']
r=httpx.post('http://127.0.0.1:18089/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+token},json={'action':'engineering_status','arguments':{},'project_id':6,'idempotency_key':str(uuid.uuid4())},timeout=60,trust_env=False)
assert r.status_code==200
state=r.json()['result']
proof.update(control=state['control'],queue=state['queue'],worker=state['delivery_worker'],schedule=state['reporting_schedule'],delegation=state['delegated_approval']['enabled'],native=state['tasks'],github_operations=state['github_operations'],integration_health=state['integration_health'])
code="""import sqlite3,json
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
print(json.dumps({'provider_receipts':d.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0],'coding_runs':d.execute("SELECT count(*) FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw'").fetchone()[0],'runs':[{'id':r[0],'status':json.loads(r[1]).get('status')} for r in d.execute("SELECT id,result FROM ai_runs WHERE id IN ('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6','301dbdd8-6f6f-4df4-b6c6-b5ca3f073795')")]}))
"""
proof['counters']=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code]))
assert proof['counters']['provider_receipts']==531 and proof['counters']['coding_runs']==21
assert len(proof['counters']['runs'])==2 and all(r['status']=='succeeded' for r in proof['counters']['runs'])
assert state['mode']=='PAUSED' and state['queue']['active']==0 and proof['delegation'] is False
expected={386,387,389,390,391,394}
native=[r for r in state['tasks'] if r['id'] in expected]
assert len(native)==6 and all(r['status']=='READY FOR RELEASE' and r['lock_version']==10 for r in native)
proof['n8n_image']=json.loads(subprocess.check_output(['docker','inspect','qldapm-n8n-main']))[0]['Image']
metadata_code="import json,time;v=json.load(open('/state/n8n-workflow-status.json'));print(json.dumps({'checked_at':v['checked_at'],'age_seconds':time.time()-v['checked_at'],'workflows':[{k:w.get(k) for k in ['code','id','active','published_version_id','definition_sha256']} for w in v['workflows']]}))"
proof['workflow_metadata']=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',metadata_code]))
assert len(proof['workflow_metadata']['workflows'])==16 and all(w['active'] for w in proof['workflow_metadata']['workflows'])
assert proof['n8n_image']=='sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269'
assert httpx.get('http://127.0.0.1:5679/healthz/readiness',trust_env=False,timeout=5).status_code==200
proof['status']='SOURCE_HEALTH_IDLE_COUNTERS_VERIFIED_NOT_FULL_ACCEPTANCE'
(OUT/'final-live-verification.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':proof['status'],'mode':state['mode'],'active':state['queue']['active'],'counters':proof['counters'],'native_count':len(native)}))

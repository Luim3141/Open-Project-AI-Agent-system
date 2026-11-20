"""Read-only deployed source/health/business/performance proof; private HTTP credential."""
import datetime,json,os,statistics,subprocess,time,uuid,sys,importlib
from pathlib import Path
import httpx
reports='--reports' in sys.argv;polish='--polish' in sys.argv or reports
suffix='-reports' if reports else '-polish' if polish else ''
setup=importlib.import_module('release_reports' if reports else 'release_polish' if polish else 'release_cc')
OUT=Path(__file__).parent;release=setup.release
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/cc-stabilization'
deploy=json.loads((setup.BUNDLE/'deployment.json').read_text());proof={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'images':deploy['images'],'source_hashes':deploy['source_hashes']}
for role,image in deploy['images'].items():
    live=release.inspect(role);assert live['Image']==image and live['State']['Health']['Status']=='healthy'
    assert release.runtime_hashes(role)=={k:v for k,v in deploy['source_hashes'].items() if release.SOURCES[k][0]==role}
release.guard_sources(release.ROOT,deploy['source_hashes'])
token=json.loads((private/'baseline-native.json').read_text(encoding='utf-8'))['token'];rows=[]
for index in range(5):
    start=time.monotonic()
    response=httpx.post('http://127.0.0.1:18089/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+token},json={'action':'engineering_status','arguments':{},'project_id':6,'idempotency_key':str(uuid.uuid4())},timeout=40,trust_env=False)
    rows.append({'index':index,'seconds':round(time.monotonic()-start,4),'http':response.status_code,'bytes':len(response.content)})
    assert response.status_code==200
    status=response.json()['result'];(private/'status-after.json').write_text(json.dumps(status,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(rows[-1]),flush=True)
proof['performance']={'scope':'Actual Main Gateway HTTP; separate from Core/browser timings','rows':rows,'p50_seconds':statistics.median(r['seconds'] for r in rows),'p95_seconds':max(r['seconds'] for r in rows),'sample_count':5}
proof['control']=status['control'];proof['queue']=status['queue'];proof['worker']=status['delivery_worker']
proof['native']=[t for t in status['tasks'] if t['id'] in {387,389,390,391,394}]
proof['native_status_sync']=status.get('native_status_sync');proof['github']={k:status['github'].get(k) for k in ['status','checked_at','release','sync_meta']}
proof['prs']=[{k:p.get(k) for k in ['number','state','is_merged','merge_target','head_sha','html_url','deployment_state']} for p in status['github'].get('prs',[])]
proof['github_operations']=status['github_operations'];proof['delegation']=status['delegated_approval'].get('enabled')
proof['runs']=[{'id':r['id'],'state':r['result'].get('status'),'native_id':r['native_id']} for r in status['runs'] if r['native_id'] in {391,394}]
proof['counters']=json.loads(release.run(['docker','exec','qldapm-ai-gateway-1','python','-c',"import json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'provider_receipts':d.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0],'coding_runs':d.execute(\"SELECT count(*) FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw'\").fetchone()[0],'delegation_enabled':d.execute('SELECT enabled FROM delegated_control WHERE project=6').fetchone()[0]}))"]))
assert status['mode']=='PAUSED' and status['queue']['active']==0 and proof['counters']['provider_receipts']==531 and proof['counters']['delegation_enabled']==0
proof['n8n']=json.loads(release.run(['docker','inspect','qldapm-n8n-main']))[0]['Image']
assert proof['n8n']=='sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269'
assert httpx.get('http://127.0.0.1:5679/healthz/readiness',trust_env=False,timeout=5).status_code==200
(OUT/('main-readback'+suffix+'.json')).write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps({'mode':status['mode'],'performance':proof['performance'],'native':proof['native'],'github':proof['github'],'counters':proof['counters']}))

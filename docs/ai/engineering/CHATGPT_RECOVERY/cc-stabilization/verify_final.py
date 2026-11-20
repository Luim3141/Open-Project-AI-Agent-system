"""Final read-only runtime proof. Keep raw status and credentials private."""
import datetime,json,os,re,subprocess,time,uuid
from pathlib import Path
import httpx
import release_caption as setup
OUT=Path(__file__).parent;release=setup.release
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/cc-stabilization'
deployment=json.loads((setup.BUNDLE/'deployment.json').read_text());previous=json.loads((OUT/'main-readback-reports.json').read_text())
proof={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'images':deployment['images'],'source_hashes':deployment['source_hashes']}
for role,image in deployment['images'].items():
    row=release.inspect(role);assert row['Image']==image and row['State']['Health']['Status']=='healthy'
    assert release.runtime_hashes(role)=={k:v for k,v in deployment['source_hashes'].items() if release.SOURCES[k][0]==role}
release.guard_sources(release.ROOT,deployment['source_hashes'])
assert previous['images']['gateway']==deployment['images']['gateway']
caption='openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'
assert all(value==deployment['source_hashes'][key] for key,value in previous['source_hashes'].items() if key!=caption)
proof['performance']={**previous['performance'],'measured_utc':previous['utc'],'reuse_reason':'Same immutable Gateway and same Native/API executable logic; subsequent Core changes are a literal historical-artifact caption and full-navigation HTML attributes only.'}
token=json.loads((private/'baseline-native.json').read_text(encoding='utf-8'))['token']
response=httpx.post('http://127.0.0.1:18089/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+token},json={'action':'engineering_status','project_id':6,'arguments':{},'idempotency_key':str(uuid.uuid4())},timeout=40,trust_env=False)
assert response.status_code==200
status=response.json()['result'];(private/'status-final.json').write_text(json.dumps(status,ensure_ascii=False),encoding='utf-8')
proof.update(control=status['control'],queue=status['queue'],worker=status['delivery_worker'],delegation=status['delegated_approval'].get('enabled'),
 native=[{k:t.get(k) for k in ['id','status','lock_version','status_sync']} for t in status['tasks'] if t['id'] in {386,387,389,390,391,394}],
 github_operations=status['github_operations'],github={k:status['github'].get(k) for k in ['status','checked_at','release','sync_meta']},
 prs=[{k:p.get(k) for k in ['number','state','is_merged','merge_target','head_sha','html_url','deployment_state']} for p in status['github'].get('prs',[])],
 workflow_status=status['workflow_status'],provider_health=status['provider_health'],
 runs=[{'id':r['id'],'native_id':r['native_id'],'state':r['result'].get('status')} for r in status['runs'] if r['native_id'] in {391,394}])
proof['counters']=json.loads(release.run(['docker','exec','qldapm-ai-gateway-1','python','-c',"import json,sqlite3;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'provider_receipts':d.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0],'coding_runs':d.execute(\"SELECT count(*) FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw'\").fetchone()[0],'delegation_enabled':d.execute('SELECT enabled FROM delegated_control WHERE project=6').fetchone()[0]}))"]))
assert status['mode']=='PAUSED' and status['queue']['active']==0 and proof['counters']=={'provider_receipts':531,'coding_runs':21,'delegation_enabled':0}
assert all(t['status']=='READY FOR RELEASE' and t['lock_version']==10 for t in proof['native'])
assert {t['id'] for t in proof['native']}=={386,387,389,390,391,394}
assert all(r['state']=='succeeded' for r in proof['runs'])
proof['n8n_image']=json.loads(release.run(['docker','inspect','qldapm-n8n-main']))[0]['Image']
assert proof['n8n_image']=='sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269'
assert httpx.get('http://127.0.0.1:5679/healthz/readiness',trust_env=False,timeout=5).status_code==200
logs=subprocess.run(['docker','logs','--since','45m','qldapm-openproject-web-1'],capture_output=True)
timings=[]
for line in (logs.stdout+logs.stderr).decode(errors='replace').splitlines():
    if 'path=/projects/ai-dev-demo/qldapm-ai' in line and 'duration=' in line:
        timings.append({k:re.search(r'\b'+k+r'=([^ ]+)',line).group(1) for k in ['method','path','status','duration']})
proof['core_http_observations_ms']=timings[-30:]
proof['runtime_limits']={'gateway_nano_cpus':release.inspect('gateway')['HostConfig']['NanoCpus'],'gateway_memory_bytes':release.inspect('gateway')['HostConfig']['Memory']}
proof['readiness']='FUNCTIONAL_REPAIRS_VERIFIED_PERFORMANCE_GATE_OPEN'
(OUT/'final-live-verification.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'readiness':proof['readiness'],'images':proof['images'],'mode':status['mode'],'counters':proof['counters'],'native_ids':[t['id'] for t in proof['native']],'p50':proof['performance']['p50_seconds']}))

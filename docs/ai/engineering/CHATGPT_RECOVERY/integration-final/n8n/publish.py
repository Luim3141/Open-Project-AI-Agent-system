"""Publish only clone-qualified metadata branches; preserve container/image/key/users/history/crons."""
import datetime,hashlib,json,os,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.n8n_integration_adapter import attach,WORKFLOWS
from automation.n8n_publish_guards import verify_idle,verify_runtime
OUT=Path(__file__).parent
proof=json.loads((OUT/'business-clone-result.json').read_text());assert proof['status']=='PASS' and proof['passed']==proof['total']
required={'LOCAL_DOCUMENT_P6','DURABLE_PRODUCERS','GITHUB_PRODUCER'}
assert required<={r['workflow'] for r in proof['checks'] if r['status']=='BUSINESS_PASS_IN_CLONE'},'N8N_P6_AND_PRODUCER_PROOF_REQUIRED'
previous=json.loads((OUT/'business-clone-attempt4.json').read_text())
assert {f'WF{i:02d}' for i in range(1,17)}<={r['workflow'] for r in previous['checks'] if r['status']=='BUSINESS_PASS_IN_CLONE'},'N8N_WF01_16_CLONE_PROOF_REQUIRED'
source_names=['app.py','service.py','integration_events.py','engineering_github_sync.py','engineering_github_details.py','engineering_github_poll.py']
for name in source_names:
 assert hashlib.sha256((ROOT/'openproject/ai/gateway'/name).read_bytes()).hexdigest()==proof['gateway_sources'][name],'GATEWAY_SOURCE_CHANGED_SINCE_CLONE: '+name
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('integration-n8n-publish-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'));private.mkdir(parents=True,exist_ok=False)
def docker(*args,data=None,timeout=240):
 p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
 if p.returncode:(private/'failure.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('N8N_PUBLISH_FAILED_PRIVATE_LOG')
 return p.stdout
READ="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT w.id,w.name,w.active,w.activeVersionId,h.nodes,h.connections,w.settings FROM workflow_entity w JOIN workflow_history h ON h.versionId=w.activeVersionId ORDER BY w.name').all()));d.close()"
STATE="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true}),h=t=>require('crypto').createHash('sha256').update(JSON.stringify(d.prepare('select * from \"'+t+'\" order by id').all())).digest('hex');console.log(JSON.stringify({credentials:h('credentials_entity'),users:h('user'),executions:d.prepare('select count(*) n from execution_entity').get().n,unfinished:d.prepare(\"select count(*) n from execution_entity where status in ('new','running','waiting')\").get().n}));d.close()"
before=json.loads(docker('exec','qldapm-n8n-main','node','-e',READ));state=json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE));assert len(before)==16 and all(r['active'] for r in before)
verify_idle(state)
assert hashlib.sha256(json.dumps([{k:r[k] for k in ['id','name','nodes','connections','settings']} for r in before],sort_keys=True).encode()).hexdigest()==proof['published_source_sha256'],'PUBLISHED_SOURCE_CHANGED_SINCE_CLONE'
assert hashlib.sha256((ROOT/'openproject/ai/automation/n8n_integration_adapter.py').read_bytes()).hexdigest()==proof['adapter_sha256'],'ADAPTER_CHANGED_SINCE_CLONE'
old=json.loads(docker('inspect','qldapm-n8n-main'))[0];image=old['Image'];assert image==proof['n8n_image']
runtime_code="import hashlib,json,pathlib; names="+repr(source_names)+";print(json.dumps({n:hashlib.sha256((pathlib.Path('/app/gateway')/n).read_bytes()).hexdigest() for n in names}))"
runtime=json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',runtime_code))
verify_runtime({name:proof['gateway_sources'][name] for name in source_names},runtime)
original=[{**r,'nodes':json.loads(r['nodes']),'connections':json.loads(r['connections']),'settings':json.loads(r['settings'])} for r in before if r['name'][:4] in WORKFLOWS]
candidate=[attach(s) for s in original];assert len(candidate)==len(WORKFLOWS)==7
(private/'old.json').write_text(json.dumps(original));(private/'candidate.json').write_text(json.dumps(candidate))
env=old['Config']['Env'];assert all('\r' not in e and '\n' not in e for e in env);(private/'preserved.env').write_text('\n'.join(env)+'\n')
def cli(path):
 base=['run','--rm','--network','none','--env-file',str(private/'preserved.env'),'--volume','qldapm-n8n-main-data:/home/node/.n8n','--mount',f'type=bind,source={private},target=/fixture,readonly','--entrypoint','n8n',image]
 docker(*base,'import:workflow','--input=/fixture/'+path)
 for spec in original:docker(*base,'publish:workflow','--id='+spec['id'])
def ready():
 for _ in range(100):
  try:
   if urllib.request.urlopen('http://127.0.0.1:5679/healthz/readiness',timeout=2).status==200:return
  except Exception:time.sleep(1)
 raise RuntimeError('N8N_READINESS_TIMEOUT')
stopped=False;import_attempted=False
try:
 verify_idle(json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE)))
 docker('stop','--time','45','qldapm-n8n-main');stopped=True
 stopped_state=json.loads(docker('run','--rm','--network','none','--mount','type=volume,source=qldapm-n8n-main-data,target=/home/node/.n8n,readonly','--entrypoint','node',image,'-e',STATE))
 verify_idle(stopped_state)
 cold=docker('run','--rm','--network','none','--mount','type=volume,source=qldapm-n8n-main-data,target=/data,readonly','--entrypoint','tar',image,'-C','/data','-cf','-','.')
 (private/'cold-volume.tar').write_bytes(cold)
 import_attempted=True;cli('candidate.json');docker('start','qldapm-n8n-main');stopped=False;ready()
 after=json.loads(docker('exec','qldapm-n8n-main','node','-e',READ));newstate=json.loads(docker('exec','qldapm-n8n-main','node','-e',STATE))
 assert len(after)==16 and all(r['active'] for r in after)
 for a,b in zip(before,after):
  assert a['id']==b['id']
  if a['name'][:4] not in WORKFLOWS:assert a==b
  else:
   assert json.loads(a['settings'])==json.loads(b['settings'])
   expected=next(s for s in candidate if s['id']==b['id']);assert json.loads(b['nodes'])==expected['nodes'] and json.loads(b['connections'])==expected['connections']
 assert state['credentials']==newstate['credentials'] and state['users']==newstate['users'] and newstate['executions']>=state['executions']
 assert json.loads(docker('inspect','qldapm-n8n-main'))[0]['Id']==old['Id']
 (private/'published-after-private.json').write_text(json.dumps(after))
 safe=[{**{k:r[k] for k in ['id','name','active','activeVersionId']},'nodes_sha256':hashlib.sha256(r['nodes'].encode()).hexdigest(),'connections_sha256':hashlib.sha256(r['connections'].encode()).hexdigest(),'settings_sha256':hashlib.sha256(r['settings'].encode()).hexdigest(),'node_count':len(json.loads(r['nodes'])),'trigger_types':sorted({n['type'] for n in json.loads(r['nodes']) if n['type'] in {'n8n-nodes-base.scheduleTrigger','n8n-nodes-base.webhook'}})} for r in after]
 (OUT/'published-after.json').write_text(json.dumps(safe,indent=2)+'\n')
 result={'status':'DEPLOYED_PENDING_GATEWAY_EVENT_READBACK','image':image,'container_preserved':True,'backup':str(private),'cold_volume_sha256':hashlib.sha256(cold).hexdigest(),'credentials_users_preserved':True,'execution_count_before':state['executions'],'execution_count_after':newstate['executions'],'unchanged_other_workflows':16-len(WORKFLOWS),'changed_workflows':sorted(WORKFLOWS),'production_cron_settings_preserved':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 (OUT/'deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
except Exception:
 if import_attempted:
  if not stopped:docker('stop','--time','45','qldapm-n8n-main');stopped=True
  cli('old.json')
 if stopped:docker('start','qldapm-n8n-main');ready()
 (OUT/'deployment-error.json').write_text(json.dumps({'state':'ROLLED_BACK_WORKFLOW_DEFINITIONS' if import_attempted else 'ABORTED_BEFORE_WORKFLOW_IMPORT','backup':str(private)}))
 raise


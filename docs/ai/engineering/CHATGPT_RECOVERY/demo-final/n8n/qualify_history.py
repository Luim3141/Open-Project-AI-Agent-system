"""Actual n8n server retention against real Gateway lifecycle Store/source validation."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,uuid

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.n8n_lifecycle_adapter import canonical_history_workflow
OUT=Path(__file__).parent
IMAGE=json.loads(subprocess.check_output(['docker','image','inspect','qldapm-n8n:demo-final']))[0]['Id']
GATEWAY_IMAGE=json.loads(subprocess.check_output(['docker','inspect','qldapm-ai-gateway-1']))[0]['Image']
ident=uuid.uuid4().hex[:10];prefix='qldapm-history-'+ident
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/prefix
private.mkdir(parents=True,exist_ok=False)
network,n8n,gateway=[prefix+'-'+n for n in ['net','n8n','gateway']]
created=[];result={'started_utc':time.time(),'image':IMAGE,'gateway_base_image':GATEWAY_IMAGE,'tests':[],'main_mutations':0}
def docker(*args,data=None,check=True,timeout=180):
 p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
 if check and p.returncode:
  (private/'error.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('CLONE_COMMAND_FAILED_PRIVATE_LOG '+args[0])
 return p.stdout
def node(code,data=None):
 return json.loads(docker('exec','-i',n8n,'node','-e',code,data=json.dumps(data).encode() if data is not None else None))
FETCH="const p=JSON.parse(require('fs').readFileSync(0,'utf8'));fetch(p.url,{method:p.method||'GET',headers:p.headers||{},body:p.body,signal:AbortSignal.timeout(10000)}).then(async r=>console.log(JSON.stringify({status:r.status,body:await r.text()}))).catch(e=>{console.error(e.name);process.exit(1)})"
def get(path):return json.loads(node(FETCH,{'url':'http://gateway:8090'+path})['body'])
def webhook(body,auth=True):
 return node(FETCH,{'url':'http://localhost:5678/webhook/qldapm-lifecycle','method':'POST','headers':{'Content-Type':'application/json',**({'X-QLDAPM-Webhook-Token':'synthetic-transport'} if auth else {})},'body':json.dumps(body)})
GATEWAY=r'''import json,sys,uuid,time
sys.path=['/app']+[p for p in sys.path if p!='/fixtures']
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from types import SimpleNamespace
from gateway.store import Store,canonical
from gateway.execution_events import append
from gateway.n8n_lifecycle_outbox import observe,sign_envelope
store=Store('/tmp/state');scope=SimpleNamespace(run_id='11111111-1111-4111-8111-111111111111',trace_id='22222222-2222-4222-8222-222222222222',actor_id=20,project_id=6)
with store.connect() as db:
 for key in ['success','restart','retry']:append(db,scope,'AGENT_STARTED',agent='dev',status='RUNNING',key=key)
failure=True
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/events':
   with store.connect() as db:body=[sign_envelope(json.loads(r[0]),'a'*64) for r in db.execute('SELECT document FROM n8n_lifecycle_outbox ORDER BY rowid')]
  elif self.path=='/state':
   with store.connect() as db:body={'observations':db.execute('SELECT count(*) FROM n8n_lifecycle_observations').fetchone()[0],'executions':[dict(r) for r in db.execute('SELECT event_id,execution_id FROM n8n_lifecycle_execution_metadata')]}
  else:body={'ready':True}
  self.reply(200,body)
 def reply(self,status,body):
  data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_POST(self):
  global failure
  try:
   payload=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
   if self.path=='/fail-next':failure=True;return self.reply(200,{})
   if self.path!='/internal/automation/lifecycle-observation':return self.reply(404,{})
   if failure:failure=False;return self.reply(503,{'error':'SYNTHETIC_TRANSIENT'})
   self.reply(200,observe(store,payload,'a'*64,self.headers.get('X-QLDAPM-N8N-Execution')))
  except (ValueError,PermissionError,TypeError):self.reply(403,{'error':'LIFECYCLE_OBSERVATION_DENIED'})
ThreadingHTTPServer(('0.0.0.0',8090),Handler).serve_forever()
'''
READ="""const s=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));const d=new s.Database('/home/node/.n8n/database.sqlite',s.OPEN_READONLY);d.all('SELECT id,status,finished,mode,workflowId,deletedAt FROM execution_entity ORDER BY id',(e,r)=>{if(e)throw e;console.log(JSON.stringify(r));d.close()})"""
try:
 spec=canonical_history_workflow({'id':'elfapV5D2PTnLiHW','name':'WF04: Multi-Agent Execution Tracking'},'http://gateway:8090')
 (private/'workflow.json').write_text(json.dumps([spec]))
 (private/'credentials.json').write_text(json.dumps([{'id':'2w9dSdmYbywZDuMB','name':'QLDAPM Webhook Header Auth','type':'httpHeaderAuth','data':{'name':'X-QLDAPM-Webhook-Token','value':'synthetic-transport'}}]))
 (private/'gateway.py').write_text(GATEWAY)
 code=private/'code/gateway';code.mkdir(parents=True)
 for p in (ROOT/'openproject/ai/gateway').iterdir():
  if p.is_file() and p.suffix in {'.py','.json'}:(code/p.name).write_bytes(p.read_bytes())
 result['gateway_source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in code.iterdir() if p.name in ['n8n_lifecycle_outbox.py','execution_events.py','store.py']}
 docker('network','create','--internal','--label','org.qldapm.history='+ident,network);created.append(('network',network))
 docker('run','-d','--name',gateway,'--network',network,'--network-alias','gateway','--label','org.qldapm.history='+ident,'--read-only','--tmpfs','/tmp:rw,size=128m','--mount',f'type=bind,source={private},target=/fixtures,readonly','--mount',f'type=bind,source={code},target=/app/gateway,readonly','--entrypoint','python',GATEWAY_IMAGE,'/fixtures/gateway.py');created.append(('container',gateway))
 docker('run','-d','--name',n8n,'--network',network,'--label','org.qldapm.history='+ident,'--tmpfs','/home/node/.n8n:rw,uid=1000,gid=1000,mode=0700','--mount',f'type=bind,source={private},target=/fixtures,readonly','-e','N8N_DIAGNOSTICS_ENABLED=false','-e','N8N_VERSION_NOTIFICATIONS_ENABLED=false','-e','N8N_TEMPLATES_ENABLED=false','-e','N8N_SECURE_COOKIE=false','-e','EXECUTIONS_DATA_PRUNE=true','-e','EXECUTIONS_DATA_MAX_AGE=168','-e','EXECUTIONS_DATA_PRUNE_MAX_COUNT=2000','--entrypoint','/bin/sh',IMAGE,'-c','sleep 1800');created.append(('container',n8n))
 docker('exec',n8n,'n8n','user-management:reset');docker('exec',n8n,'n8n','import:credentials','--input=/fixtures/credentials.json');docker('exec',n8n,'n8n','import:workflow','--input=/fixtures/workflow.json');docker('exec',n8n,'n8n','publish:workflow','--id=elfapV5D2PTnLiHW')
 docker('exec','-d',n8n,'/bin/sh','-c','n8n start >/tmp/n8n.log 2>&1')
 for _ in range(75):
  try:
   if webhook({},False)['status']==403:break
  except Exception:pass
  time.sleep(1)
 else:raise RuntimeError('WEBHOOK_NOT_READY')
 result['tests'].append({'case':'transport_auth','status':'PASS'})
 events=get('/events');event=events[0]
 first=webhook(event);assert first['status']>=400
 second=webhook(event);assert second['status']==200 and json.loads(second['body'])['event_id']==event['event']['event_id']
 third=webhook(event);assert third['status']==200
 assert get('/state')['observations']==1
 result['tests'].append({'case':'transient_failure_fresh_retry_business_observation_dedup','status':'PASS'})
 bad={**events[1],'nested':{'secret':'SYNTHETIC_NESTED_SHOULD_NOT_PERSIST'}}
 bad['event']={**bad['event'],'arbitrary':'SYNTHETIC_NESTED_SHOULD_NOT_PERSIST'}
 assert webhook(bad)['status']>=400
 result['tests'].append({'case':'untrusted_nested_signed_payload_rejected','status':'PASS'})
 docker('exec',n8n,'/bin/sh','-c',"kill $(pgrep -f '^node /usr/local/bin/n8n' | head -1)",check=False)
 # Restart the server process using the same isolated tmpfs SQLite/files, not a fresh instance.
 time.sleep(2);docker('exec','-d',n8n,'/bin/sh','-c','n8n start >/tmp/n8n-restarted.log 2>&1')
 for _ in range(60):
  try:
   response=webhook(get('/events')[2])
   if response['status']==200:break
  except Exception:pass
  time.sleep(1)
 else:raise RuntimeError('RESTART_ACK_FAILED')
 result['tests'].append({'case':'same_database_restart_business_ack','status':'PASS'})
 time.sleep(1);executions=node(READ)
 assert any(e['status']=='success' and not e['deletedAt'] for e in executions)
 assert any(e['status']=='error' and not e['deletedAt'] for e in executions)
 scan=node("const fs=require('fs'),path=require('path');let leaked=false;function walk(p){for(const e of fs.readdirSync(p,{withFileTypes:true})){const f=path.join(p,e.name);if(e.isDirectory())walk(f);else if(fs.readFileSync(f).includes('SYNTHETIC_NESTED_SHOULD_NOT_PERSIST'))leaked=true}}walk('/home/node/.n8n');console.log(JSON.stringify({leaked}))")
 assert not scan['leaked'];result['tests'].append({'case':'retained_success_error_and_nested_canary_absence','status':'PASS'})
 result.update(status='PASS',executions=executions,observations=get('/state'),retention={'success':'all','error':'all','progress':False,'age_hours':168,'max_count':2000},limitations=['Actual n8n+real Gateway lifecycle Store/source/HMAC validation; synthetic execution source events and injected503, no Native/provider work','n8n UI retry of a persisted redacted signature is not authorized; Gateway outbox sends a fresh signed retry','Physical disk/machine DR is outside this tmpfs server test'])
finally:
 for kind,name in reversed(created):
  row=json.loads(docker('inspect',name) if kind=='container' else docker('network','inspect',name))[0]
  labels=row['Config']['Labels'] if kind=='container' else row['Labels'];assert labels.get('org.qldapm.history')==ident
  if kind=='container':(private/(name+'.log')).write_bytes(docker('logs',name,check=False));docker('rm','-f',name)
  else:docker('network','rm',name)
 result['finished_utc']=time.time();(OUT/'history-clone-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

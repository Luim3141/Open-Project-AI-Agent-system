"""Image-only Phase3 rollout with idle/backup/candidate guards and image-only rollback."""
import datetime,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[5];sys.path.insert(0,str(root/'openproject/ai'))
from automation import main_operations as ops
out=Path(__file__).parent;runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
private=runtime/'openproject-ai/operator'/('demo-final-rollout-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
private.mkdir(parents=True,exist_ok=False)
def run(args,timeout=240):
 p=subprocess.run(args,capture_output=True,timeout=timeout)
 if p.returncode:(private/'failure.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('ROLLOUT_COMMAND_FAILED_PRIVATE_LOG')
 return p.stdout
def queue():
 code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':d.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0],'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0]}))"
 return json.loads(run(['docker','exec','qldapm-ai-gateway-1','python','-c',code]))
def inspect(name):return json.loads(run(['docker','inspect',name]))[0]
def health(name,expected):
 for _ in range(120):
  r=inspect(name)
  if r['Image']==expected and r['State'].get('Health',{}).get('Status')=='healthy':return
  time.sleep(1)
 raise RuntimeError('ROLLOUT_HEALTH_TIMEOUT')
old=json.loads((out.parent/'phase3_1/deployment.json').read_text())['images']
new={k:json.loads(run(['docker','image','inspect',tag]))[0]['Id'] for k,tag in [('gateway','qldapm-gateway:demo-final'),('core','qldapm-core:demo-final')]}
qualified=json.loads((out/'gateway-candidate-final.json').read_text());assert qualified['exit_code']==0 and qualified['image']==new['gateway']
qualified_core=json.loads((out/'core-clone-result.json').read_text());assert qualified_core['status']=='PASS' and qualified_core['image']==new['core']
assert inspect('qldapm-ai-gateway-1')['Image']==old['gateway'] and inspect('qldapm-openproject-web-1')['Image']==old['core']
assert queue()=={'active':0,'mode':'OFF'}
# Freeze exact deploy source and verify immutable candidate contents before changing MAIN.
files={}
allowlist=json.loads((out/'source-allowlist.json').read_text())
for name in allowlist['gateway']:
 path=root/'openproject/ai/gateway'/name;h=hashlib.sha256(path.read_bytes()).hexdigest()
 actual=run(['docker','run','--rm','--network','none','--entrypoint','sha256sum',new['gateway'],'/app/gateway/'+name]).decode().split()[0];assert actual==h
 files[str(path.relative_to(root)).replace('\\','/')]=h
for rel in allowlist['core']:
 path=root/'openproject/ai/core/overlay'/rel;h=hashlib.sha256(path.read_bytes()).hexdigest()
 actual=run(['docker','run','--rm','--network','none','--entrypoint','sha256sum',new['core'],'/app/'+rel]).decode().split()[0];assert actual==h
 files[str(path.relative_to(root)).replace('\\','/')]=h
manifest=ops.capture();backup=ops.backup(manifest,private/'backup')
baseline=json.loads((out/'M0.json').read_text())['manifest']
assert manifest['unknown_sha256']==baseline['unknown_sha256'] and manifest['historical_pending']==baseline['historical_pending']
worker_source=root/'openproject/ai/automation/engineering_worker.py'
worker_original=worker_source.read_bytes()
# The scheduled task executes this workspace file; private copy permits image/protocol rollback.
(private/'engineering_worker.py.candidate').write_bytes(worker_original)
previous_worker=(runtime/'openproject-ai/operator/phase3_1-final-rollout-20261102T154856/engineering_worker.py.candidate').read_bytes()
assert hashlib.sha256(previous_worker).hexdigest()==json.loads((out.parent/'phase3_1/final-live-verification.json').read_text())['host_worker_sha256']
(private/'engineering_worker.py.before').write_bytes(previous_worker)
env=runtime/'openproject-ai/.env';lock=runtime/'openproject-ai/image-lock.json';bridge=runtime/'openproject/ui-bridge.yml'
originals={env:env.read_bytes(),lock:lock.read_bytes(),bridge:bridge.read_bytes()}
runtime_config=runtime/'openproject-ai/gateway/config.json'
originals[runtime_config]=runtime_config.read_bytes()
provider_token=runtime/'openproject-ai/gateway/engineering-provider-token'
token_before=provider_token.read_bytes() if provider_token.exists() else None
gate_path='/root/.qldapm-openclaw/provider_gate.py'
gate_prefix=['wsl','-d','OpenClawGateway','-u','root','--exec']
old_gate=run(gate_prefix+['/usr/bin/cat',gate_path]);(private/'provider_gate.py.before').write_bytes(old_gate)
new_gate=(root/'openproject/ai/automation/openclaw_provider_gate.py').read_bytes()
client_token=run(gate_prefix+['/usr/bin/cat','/root/.qldapm-openclaw/client-token']).strip()
assert len(client_token)>=32

def install_gate(data):
 p=subprocess.run(gate_prefix+['/usr/bin/python3','-c',"import sys;from pathlib import Path;p=Path('/root/.qldapm-openclaw/provider_gate.py');t=p.with_suffix('.tmp');t.write_bytes(sys.stdin.buffer.read());t.chmod(0o600);t.replace(p)"],input=data,capture_output=True,timeout=30)
 assert p.returncode==0
 run(gate_prefix+['/usr/bin/systemctl','restart','qldapm-openclaw-provider.service'])
 assert run(gate_prefix+['/usr/bin/systemctl','is-active','qldapm-openclaw-provider.service']).strip()==b'active'
for path,data in originals.items():(private/(path.parent.name+'-'+path.name+'.before')).write_bytes(data)
assert json.loads(originals[lock])['AI_IMAGE']==old['gateway'] and json.loads(originals[lock])['CORE_IMAGE']==old['core']
gprefix=['docker','compose','-p','qldapm-ai','--env-file',str(env),'-f',str(root/'openproject/ai/compose.yml'),'-f',str(root/'openproject/ai/gemini-free.main.yml')]
cprefix=['docker','compose','-p','qldapm-openproject','--env-file',str(runtime/'openproject/.env'),'-f',str(root/'openproject/compose.yml'),'-f',str(bridge)]
overrides={}
for kind,prefix,service in [('gateway',gprefix,'gateway'),('core',cprefix,'web')]:
 override=private/(kind+'-candidate.json');override.write_text(json.dumps({'services':{service:{'image':new[kind],'pull_policy':'never'}}}))
 before=json.loads(run(prefix+['config','--format','json']))['services'][service]
 after=json.loads(run(prefix+['-f',str(override),'config','--format','json']))['services'][service]
 assert {k:v for k,v in before.items() if k not in ('image','pull_policy')}=={k:v for k,v in after.items() if k not in ('image','pull_policy')}
 overrides[kind]=override
changed=[];restart_worker=True
try:
 run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Stop-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])
 for _ in range(20):
  count=run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?(3)?\\.exe$' -and $_.CommandLine -like '*openproject*ai*automation*engineering_worker.py*--watch*' }).Count"]).decode().strip()
  if count=='0':break
  time.sleep(1)
 else:raise RuntimeError('WORKER_NOT_STOPPED')
 assert queue()=={'active':0,'mode':'OFF'}
 gate_state=json.loads(run(gate_prefix+['/usr/bin/python3','-c',"import json;from pathlib import Path;d=json.loads(Path('/root/.qldapm-openclaw/active.json').read_text());print(json.dumps({'active':d.get('active')}))"]))
 assert gate_state['active'] is False
 settings=json.loads(originals[runtime_config])
 assert 'localhost:18089' in settings['hosts']
 settings.setdefault('integration_health_urls',{}).update(openclaw='http://host.docker.internal:18789',demo='http://host.docker.internal:18791')
 settings.setdefault('engineering',{})['provider_limits']={'rpm':10,'tpm':175000}
 settings['automation_readers']=[20,21,22,23]
 settings.setdefault('n8n_lifecycle',{})['authenticated_webhook']=True
 runtime_config.write_text(json.dumps(settings,indent=2)+'\n')
 provider_token.write_bytes(client_token+b'\n')
 install_gate(new_gate)
 changed.append('gateway');run(gprefix+['-f',str(overrides['gateway']),'up','-d','--no-deps','gateway']);health('qldapm-ai-gateway-1',new['gateway'])
 changed.append('core');run(cprefix+['-f',str(overrides['core']),'up','-d','--no-deps','web']);health('qldapm-openproject-web-1',new['core'])
 env_text=originals[env].decode('utf-8-sig');assert len(re.findall(r'(?m)^AI_IMAGE=.*$',env_text))==1
 env.write_text(re.sub(r'(?m)^AI_IMAGE=.*$','AI_IMAGE='+new['gateway'],env_text),encoding='utf-8')
 pin=json.loads(originals[lock]);pin.update(AI_IMAGE=new['gateway'],CORE_IMAGE=new['core']);lock.write_text(json.dumps(pin,indent=2)+'\n')
 config=json.loads(originals[bridge]);config['services']['web']['image']=new['core'];bridge.write_text(json.dumps(config,indent=2)+'\n')
 assert queue()=={'active':0,'mode':'OFF'}
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'DEPLOYED_HEALTHY_PENDING_BUSINESS_READBACK','previous_images':old,'images':new,'source_files':files,'backup':str(private/'backup'),'compose_parity_image_only':True,'mode':'OFF','queue_active':0,'host_worker_sha256':hashlib.sha256(worker_original).hexdigest(),'provider_gate_sha256':hashlib.sha256(new_gate).hexdigest(),'configuration_changes':{'provider_limits':{'rpm':10,'tpm':175000},'automation_readers':[20,21,22,23],'n8n_authenticated_webhook':True,'health_urls':'verified host.docker.internal18789/18791'},'rollback':'restore private before-files/worker/gate and image pins when idle; no automatic database restore'}
 (out/'deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
except Exception:
 for path,data in originals.items():path.write_bytes(data)
 worker_source.write_bytes(previous_worker)
 if token_before is not None:provider_token.write_bytes(token_before)
 elif provider_token.exists():provider_token.unlink()
 rollback_errors=[]
 try:install_gate(old_gate)
 except Exception:rollback_errors.append('PROVIDER_GATE_ROLLBACK_FAILED')
 for kind,prefix,service,name in [('core',cprefix,'web','qldapm-openproject-web-1'),('gateway',gprefix,'gateway','qldapm-ai-gateway-1')]:
  if kind in changed:
   try:run(prefix+['up','-d','--no-deps',service]);health(name,old[kind])
   except Exception:rollback_errors.append(kind.upper()+'_IMAGE_ROLLBACK_FAILED')
 if rollback_errors:
  restart_worker=False
  (private/'rollback-errors.json').write_text(json.dumps(rollback_errors))
  raise RuntimeError('ROLLBACK_INCOMPLETE_WORKER_LEFT_STOPPED')
 raise
finally:
 if restart_worker:run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Start-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])


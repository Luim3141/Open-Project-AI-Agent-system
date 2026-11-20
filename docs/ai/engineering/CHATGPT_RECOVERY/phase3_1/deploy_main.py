"""Image-only Phase3 rollout with idle/backup/candidate guards and image-only rollback."""
import datetime,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[5];sys.path.insert(0,str(root/'openproject/ai'))
from automation import main_operations as ops
out=Path(__file__).parent;runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
private=runtime/'openproject-ai/operator'/('phase3_1-rollout-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
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
old={'gateway':'sha256:ce047f82692e7c46db1ddcb675be85d43a99936f0859e055db5513219a9ab6d4','core':'sha256:7649e1f923e6af20ea6d3eb8820ff4d4466840728893374846b7875893e9bcc2'}
new={k:json.loads(run(['docker','image','inspect',tag]))[0]['Id'] for k,tag in [('gateway','qldapm-gateway:phase3_1'),('core','qldapm-core:phase3_1')]}
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
baseline=json.loads((out/'runtime-before.json').read_text())['manifest']
assert manifest['unknown_sha256']==baseline['unknown_sha256'] and manifest['historical_pending']==baseline['historical_pending']
worker_source=root/'openproject/ai/automation/engineering_worker.py'
worker_original=worker_source.read_bytes()
# The scheduled task executes this workspace file; private copy permits image/protocol rollback.
(private/'engineering_worker.py.candidate').write_bytes(worker_original)
previous_worker=worker_original.replace(b"    calls=reservation['calls']\r\n",b'').replace(b"    calls=reservation['calls']\n",b'')
assert previous_worker!=worker_original
assert hashlib.sha256(previous_worker).hexdigest()==json.loads((out.parent/'phase3-owner/final-source-manifest.json').read_text())['files']['openproject/ai/automation/engineering_worker.py']
(private/'engineering_worker.py.before').write_bytes(previous_worker)
env=runtime/'openproject-ai/.env';lock=runtime/'openproject-ai/image-lock.json';bridge=runtime/'openproject/ui-bridge.yml'
originals={env:env.read_bytes(),lock:lock.read_bytes(),bridge:bridge.read_bytes()}
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
changed=[]
try:
 run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Stop-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])
 for _ in range(20):
  count=run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?(3)?\\.exe$' -and $_.CommandLine -like '*openproject*ai*automation*engineering_worker.py*--watch*' }).Count"]).decode().strip()
  if count=='0':break
  time.sleep(1)
 else:raise RuntimeError('WORKER_NOT_STOPPED')
 assert queue()=={'active':0,'mode':'OFF'}
 changed.append('gateway');run(gprefix+['-f',str(overrides['gateway']),'up','-d','--no-deps','gateway']);health('qldapm-ai-gateway-1',new['gateway'])
 changed.append('core');run(cprefix+['-f',str(overrides['core']),'up','-d','--no-deps','web']);health('qldapm-openproject-web-1',new['core'])
 env_text=originals[env].decode('utf-8-sig');assert len(re.findall(r'(?m)^AI_IMAGE=.*$',env_text))==1
 env.write_text(re.sub(r'(?m)^AI_IMAGE=.*$','AI_IMAGE='+new['gateway'],env_text),encoding='utf-8')
 pin=json.loads(originals[lock]);pin.update(AI_IMAGE=new['gateway'],CORE_IMAGE=new['core']);lock.write_text(json.dumps(pin,indent=2)+'\n')
 config=json.loads(originals[bridge]);config['services']['web']['image']=new['core'];bridge.write_text(json.dumps(config,indent=2)+'\n')
 assert queue()=={'active':0,'mode':'OFF'}
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'DEPLOYED_HEALTHY_PENDING_BUSINESS_READBACK','previous_images':old,'images':new,'source_files':files,'backup':str(private/'backup'),'config_parity_image_only':True,'mode':'OFF','queue_active':0,'host_protocol_unchanged':True,'rollback':'restore three pin/config before-files, recreate previous images when idle; do not restore databases automatically'}
 (out/'deployment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
except Exception:
 for path,data in originals.items():path.write_bytes(data)
 worker_source.write_bytes(previous_worker)
 if 'core' in changed:run(cprefix+['up','-d','--no-deps','web']);health('qldapm-openproject-web-1',old['core'])
 if 'gateway' in changed:run(gprefix+['up','-d','--no-deps','gateway']);health('qldapm-ai-gateway-1',old['gateway'])
 raise
finally:
 run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Start-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])


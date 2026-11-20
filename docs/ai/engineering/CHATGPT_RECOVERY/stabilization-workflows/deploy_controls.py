import hashlib,json,os,subprocess,sys,time
from pathlib import Path

root=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(root/'openproject/ai'))
from automation import main_operations as ops

local=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
private=local/'openproject-ai/operator/stabilization-controls-rollout-20261102'
private.mkdir(parents=True,exist_ok=False)
core_runtime=local/'openproject'; ai_runtime=local/'openproject-ai'
bridge=core_runtime/'ui-bridge.yml'; lock=ai_runtime/'image-lock.json'
bridge_before=bridge.read_bytes();lock_before=lock.read_bytes()
(private/'ui-bridge-before.json').write_bytes(bridge_before);(private/'image-lock-before.json').write_bytes(lock_before)
old='sha256:c237e4a792608e5ff5b95a7c9c36d41dc0392ceb3ec07f451fbee0d96dca06c9'
new='sha256:524614e9e8dcdb53296e8b30f0261df523d42da501c8a3461c992ccde773cdff'
worker=root/'openproject/ai/automation/engineering_delivery.py'
previous=ai_runtime/'operator/approved-rollout-20261101T110426Z/clean-source/openproject/ai/automation/engineering_delivery.py'
expected='cb81961147ad93aa2e0c9ed0e044dcb08a1f69b2d7f71aaaf9379f43fc85abeb'
assert hashlib.sha256(worker.read_bytes()).hexdigest()==expected
(private/'worker-before.py').write_bytes(previous.read_bytes());(private/'worker-candidate.py').write_bytes(worker.read_bytes())
def run(args,timeout=240):
 p=subprocess.run(args,capture_output=True,timeout=timeout)
 if p.returncode:
  (private/'failure.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('COMMAND_FAILED_PRIVATE_LOG')
 return p.stdout
def queue():
 code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':d.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0],'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0]}))"
 return json.loads(run(['docker','exec','qldapm-ai-gateway-1','python','-c',code]))
def health(image):
 for _ in range(120):
  row=json.loads(run(['docker','inspect','qldapm-openproject-web-1']))[0]
  if row['Image']==image and row['State']['Status']=='running' and row['State'].get('Health',{}).get('Status')=='healthy':return
  time.sleep(1)
 raise RuntimeError('CORE_HEALTH_TIMEOUT')
assert json.loads(run(['docker','inspect','qldapm-openproject-web-1']))[0]['Image']==old
assert json.loads(bridge_before)['services']['web']['image']==old
assert json.loads(lock_before)['CORE_IMAGE']==old
assert queue()=={'active':0,'mode':'OFF'}
ops.backup(ops.capture(),private/'backup')
override=private/'candidate.json';override.write_text(json.dumps({'services':{'web':{'image':new,'pull_policy':'never'}}}))
prefix=['docker','compose','-p','qldapm-openproject','--env-file',str(core_runtime/'.env'),'-f',str(root/'openproject/compose.yml'),'-f',str(bridge)]
before=json.loads(run(prefix+['config','--format','json']))['services']['web']
after=json.loads(run(prefix+['-f',str(override),'config','--format','json']))['services']['web']
assert {k:v for k,v in before.items() if k not in ('image','pull_policy')}=={k:v for k,v in after.items() if k not in ('image','pull_policy')}
changed=False
try:
 run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Stop-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])
 for _ in range(20):
  n=run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?(3)?\\.exe$' -and $_.CommandLine -like '*openproject*ai*automation*engineering_worker.py*--watch*' }).Count"]).decode().strip()
  if n=='0':break
  time.sleep(1)
 else:raise RuntimeError('WORKER_STILL_RUNNING')
 assert queue()=={'active':0,'mode':'OFF'}
 changed=True;run(prefix+['-f',str(override),'up','-d','--no-deps','web']);health(new)
 doc=json.loads(bridge_before);doc['services']['web']['image']=new;bridge.write_text(json.dumps(doc,indent=2)+'\n')
 doc=json.loads(lock_before);doc['CORE_IMAGE']=new;lock.write_text(json.dumps(doc,indent=2)+'\n')
 assert queue()=={'active':0,'mode':'OFF'}
 (Path(__file__).parent/'controls-deployment.json').write_text(json.dumps({'status':'CORE_HEALTHY','image':new,'previous':old,'worker_sha256':expected,'backup':str(private/'backup'),'config_parity':True},indent=2)+'\n')
 print('CORE_CONTROLS_AND_HOST_WORKER_READY')
except Exception:
 bridge.write_bytes(bridge_before);lock.write_bytes(lock_before)
 if changed:run(prefix+['up','-d','--no-deps','web']);health(old)
 raise
finally:
 run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Start-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])

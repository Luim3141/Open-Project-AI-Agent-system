import hashlib,json,os,subprocess,sys,time
from pathlib import Path

root=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(root/'openproject/ai'))
from automation import main_operations as ops

local=Path(os.environ['LOCALAPPDATA'])/'QLDAPM'
private=local/'openproject-ai/operator/phase2-final-core-rollout-r3-20261102'
private.mkdir(parents=True,exist_ok=False)
core_runtime=local/'openproject'; ai_runtime=local/'openproject-ai'
bridge=core_runtime/'ui-bridge.yml'; lock=ai_runtime/'image-lock.json'
bridge_before=bridge.read_bytes();lock_before=lock.read_bytes()
(private/'ui-bridge-before.json').write_bytes(bridge_before);(private/'image-lock-before.json').write_bytes(lock_before)
old='sha256:00f1e372ded7dc3ee0bcb02275233e0baad08990893f8d1c27511b5a66cb9cd8'
new='sha256:a6a61b685014039049f46d1d93a90340d4108265dccbed93cc6d04fbe3f027fd'
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
idle_state=queue();assert idle_state['active']==0 and idle_state['mode'] in {'OFF','PAUSED'}
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
 assert queue()==idle_state
 changed=True;run(prefix+['-f',str(override),'up','-d','--no-deps','web']);health(new)
 doc=json.loads(bridge_before);doc['services']['web']['image']=new;bridge.write_text(json.dumps(doc,indent=2)+'\n')
 doc=json.loads(lock_before);doc['CORE_IMAGE']=new;lock.write_text(json.dumps(doc,indent=2)+'\n')
 assert queue()==idle_state
 (Path(__file__).parent/'core-deployment.json').write_text(json.dumps({'status':'CORE_HEALTHY','image':new,'previous':old,'backup':str(private/'backup'),'config_parity':True},indent=2)+'\n')
 print('CORE_PHASE2_READY')
except Exception:
 bridge.write_bytes(bridge_before);lock.write_bytes(lock_before)
 if changed:run(prefix+['up','-d','--no-deps','web']);health(old)
 raise
finally:
 run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Start-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])

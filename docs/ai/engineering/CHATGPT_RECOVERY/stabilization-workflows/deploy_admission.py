import json, os, re, subprocess, sys, time
from pathlib import Path

root=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(root/'openproject/ai'))
from automation import main_operations as ops

out=Path(__file__).parent
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
private=runtime/'operator/stabilization-admission-rollout-20261102'
private.mkdir(parents=True,exist_ok=False)
old='sha256:9d02446cecd21fccbed2bcc43ae0a7d488f3b5ae2617f1d918926b4ba39aa0d6'
new='sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb'
env=runtime/'.env';lock=runtime/'image-lock.json'
env_before=env.read_bytes();lock_before=lock.read_bytes()
(private/'env-before').write_bytes(env_before);(private/'image-lock-before.json').write_bytes(lock_before)
assert json.loads(subprocess.check_output(['docker','inspect','qldapm-ai-gateway-1']))[0]['Image']==old
assert json.loads(subprocess.check_output(['docker','image','inspect','qldapm-gateway:stabilization-admission']))[0]['Id']==new
manifest=ops.capture();ops.backup(manifest,private/'backup')
prefix=['docker','compose','-p','qldapm-ai','--env-file',str(env),'-f',str(root/'openproject/ai/compose.yml'),'-f',str(root/'openproject/ai/gemini-free.main.yml')]
override=private/'candidate.json';override.write_text(json.dumps({'services':{'gateway':{'image':new,'pull_policy':'never'}}}))
def run(args,timeout=240):
    p=subprocess.run(args,capture_output=True,timeout=timeout)
    if p.returncode:
        (private/'failure.log').write_bytes(p.stdout+p.stderr)
        raise RuntimeError('Command failed; details in private operator directory')
    return p.stdout
def queue():
    code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':d.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0],'mode':d.execute('select mode from engineering_control where project=6').fetchone()[0]}))"
    return json.loads(run(['docker','exec','qldapm-ai-gateway-1','python','-c',code]))
def health(expected):
    for _ in range(90):
        row=json.loads(run(['docker','inspect','qldapm-ai-gateway-1']))[0]
        if row['Image']==expected and row['State']['Status']=='running' and row['State'].get('Health',{}).get('Status')=='healthy':return
        time.sleep(1)
    raise RuntimeError('GATEWAY_HEALTH_TIMEOUT')
assert queue()=={'active':0,'mode':'OFF'}
before=json.loads(run(prefix+['config','--format','json']))['services']['gateway']
after=json.loads(run(prefix+['-f',str(override),'config','--format','json']))['services']['gateway']
assert {k:v for k,v in before.items() if k not in ('image','pull_policy')}=={k:v for k,v in after.items() if k not in ('image','pull_policy')}
started=False
try:
    run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Stop-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])
    for _ in range(20):
        count=run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?(3)?\\.exe$' -and $_.CommandLine -like '*openproject*ai*automation*engineering_worker.py*--watch*' }).Count"]).decode().strip()
        if count=='0':break
        time.sleep(1)
    else:raise RuntimeError('WORKER_STILL_RUNNING')
    assert queue()=={'active':0,'mode':'OFF'}
    started=True
    run(prefix+['-f',str(override),'up','-d','--no-deps','gateway'])
    health(new)
    text=env_before.decode('utf-8-sig');assert len(re.findall(r'(?m)^AI_IMAGE=.*$',text))==1
    env.write_text(re.sub(r'(?m)^AI_IMAGE=.*$', 'AI_IMAGE='+new,text),encoding='utf-8')
    doc=json.loads(lock_before);assert doc['AI_IMAGE']==old;doc['AI_IMAGE']=new
    lock.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    assert queue()=={'active':0,'mode':'OFF'}
    (out/'gateway-admission-deployment.json').write_text(json.dumps({'status':'READY','old':old,'image':new,'config_parity':True,'backup':str(private/'backup')},indent=2)+'\n')
    print('GATEWAY_ADMISSION_READY')
except Exception:
    env.write_bytes(env_before);lock.write_bytes(lock_before)
    if started:
        run(prefix+['up','-d','--no-deps','gateway']);health(old)
    raise
finally:
    run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"Start-ScheduledTask -TaskName 'QLDAPMEngineeringDelivery'"])

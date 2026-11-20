"""Immutable Gateway qualification, offline adapters and no mounted runtime state."""
import datetime
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).parent
image=json.loads(subprocess.check_output(['docker','image','inspect','qldapm-gateway:phase3_1']))[0]['Id']
command=['docker','run','--rm','--network','none','--memory','512m','--cpus','2',
    '-e','PYTHONPATH=/app:/app/tests:/fixture/openproject/ai',
    '--mount',f'type=bind,source={ROOT / "openproject/ai/tests"},target=/app/tests,readonly',
    '--mount',f'type=bind,source={ROOT / "openproject/ai/automation"},target=/fixture/openproject/ai/automation,readonly',
    image,'python','-m','unittest','test_owner_uat_recovery','test_phase31_integration_health',
    'test_engineering_owner_controls','test_engineering_auto_mode','test_engineering_continuation',
    'test_engineering_github_owner_contract','test_engineering_reporting','test_engineering_fencing',
    'test_engineering_worker_recovery']
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(command,capture_output=True,timeout=300)
(OUT/'gateway-candidate-final.log').write_bytes(p.stdout+p.stderr)
result={'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'image':image,'command':command,'exit_code':p.returncode,'outcome':'PASS' if p.returncode==0 else 'FAIL',
    'environment':'network-none immutable Gateway; synthetic fixtures; read-only tests/hostadapter; no production data',
    'evidence':'gateway-candidate-final.log'}
(OUT/'gateway-candidate-final.json').write_text(json.dumps(result,indent=2)+'\n')
print((p.stdout+p.stderr).decode(errors='replace')[-1600:])
print(json.dumps(result))
raise SystemExit(p.returncode)

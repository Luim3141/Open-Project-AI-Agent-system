"""Bounded, payload-free WSL CLI health snapshot for the existing worker heartbeat."""
import json
import os
from pathlib import Path
import subprocess
import time
from contextlib import nullcontext

def collect(run=subprocess.run):
    started=time.monotonic()
    base=['wsl','-d','OpenClawGateway','-u','openclaw','--exec','/usr/local/bin/openclaw']
    result={'checked_at':time.time(),'check_type':'WSL OpenClaw health --json + gateway status --json','health':'UNKNOWN'}
    try:
        running=run(['wsl','--list','--running','--quiet'],capture_output=True,timeout=12)
        if running.returncode!=0:raise ValueError('WSL status unavailable')
        names=running.stdout.decode('utf-16').lstrip('\ufeff').splitlines()
        if 'OpenClawGateway' not in [name.strip() for name in names]:
            result.update(health='DOWN',wsl_distro='OpenClawGateway',wsl_running=False,last_error='OPENCLAW_WSL_STOPPED')
            result['latency_ms']=round((time.monotonic()-started)*1000,1)
            return result
        health=run(base+['health','--json','--timeout','3000'],capture_output=True,timeout=12)
        process=run(base+['gateway','status','--json'],capture_output=True,timeout=12)
        h=json.loads(health.stdout);p=json.loads(process.stdout)
        rpc=(p.get('rpc') or {}).get('ok') is True
        runtime=(p.get('service') or {}).get('runtime',{})
        healthy=health.returncode==0 and h.get('ok') is True
        ready=healthy and rpc and runtime.get('status')=='running'
        result.update(health='READY' if ready else 'DOWN',wsl_distro='OpenClawGateway',wsl_running=True,
            gateway_rpc_ok=rpc,cli_health_ok=healthy,process_state=runtime.get('status'),pid=runtime.get('pid'),
            service_loaded=(p.get('service') or {}).get('loaded'),
            startup_state='RPC_READY' if ready else 'SERVICE_STARTING' if runtime.get('status')=='running' else 'SERVICE_STOPPED',
            child_runtime_available=(h.get('childRuntime') or {}).get('available'),
            last_error=None if ready else 'OPENCLAW_SERVICE_NOT_RUNNING' if runtime.get('status')!='running' else 'OPENCLAW_RPC_NOT_READY' if not rpc else 'OPENCLAW_HEALTH_NOT_READY')
    except (OSError,ValueError,subprocess.TimeoutExpired):result.update(health='DOWN',last_error='OPENCLAW_CLI_UNAVAILABLE_OR_TIMEOUT')
    result['latency_ms']=round((time.monotonic()-started)*1000,1)
    return result

def ensure(*,recovery_guard=None):
    """Repair only the installed user service; starting it never admits an agent task."""
    document=collect()
    if document['health']=='READY':return document
    # Never stop/restart a live runtime or guess an identity when CLI observation failed.
    if document.get('service_loaded') is not True:return document
    started=document.get('process_state')=='stopped'
    exit_code=None
    if started:
        with (recovery_guard() if recovery_guard is not None else nullcontext(True)) as allowed:
            if not allowed:return {**document,'recovery_start_attempted':False,'last_error':'WORKER_BUSY_RECOVERY_DEFERRED'}
            try:
                process=subprocess.run(['wsl','-d','OpenClawGateway','-u','openclaw','--exec','/usr/local/bin/openclaw','gateway','start'],capture_output=True,timeout=45)
                exit_code=process.returncode
            except (OSError,subprocess.TimeoutExpired):pass
    for attempt in range(4):
        time.sleep(2**attempt)
        document=collect()
        if document['health']=='READY':break
    return {**document,'recovery_start_attempted':started,'recovery_start_exit_code':exit_code,'recovery_probe_attempts':attempt+1}

def persist(root=None,*,recover=False,recovery_guard=None):
    root=Path(root or Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway')
    path=root/'openclaw-health.json';temp=path.with_suffix('.tmp')
    document=ensure(recovery_guard=recovery_guard) if recover else collect();temp.write_text(json.dumps(document)+'\n');temp.replace(path)
    return document

if __name__=='__main__':print(json.dumps(persist()))

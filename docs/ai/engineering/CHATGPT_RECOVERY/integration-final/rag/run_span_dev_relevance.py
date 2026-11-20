"""Run the DEV-only snapshot experiment and stop the owned Qdrant clone on exit."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parent;WORKSPACE=ROOT.parents[5]
NAME='qldapm-integration-rag-dev';LABEL='org.qldapm.integration-rag-dev'
assert not (ROOT/'span-dev-relevance.json').exists(),'PRESERVE_EXISTING_DEV_EVIDENCE'
def command(args,timeout=60):
    r=subprocess.run(args,capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError('OWNED_DEV_CLONE_COMMAND_FAILED: '+r.stderr.decode(errors='replace')[-300:])
    return r.stdout
info=json.loads(command(['docker','inspect',NAME]))[0]
assert info['Config']['Labels'].get(LABEL)=='true' and info['State']['Status']=='exited'
assert info['HostConfig']['Memory']==512*1024*1024 and info['HostConfig']['NanoCpus']==1000000000
started=False
try:
    command(['docker','start',NAME]);started=True
    for _ in range(30):
        try:
            if httpx.get('http://127.0.0.1:16341/healthz',timeout=2,trust_env=False).status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(1)
    else:raise RuntimeError('OWNED_DEV_QDRANT_NOT_READY')
    env=dict(os.environ);env['PYTHONPATH']=str(WORKSPACE/'openproject/ai')
    prepare=subprocess.run([sys.executable,str(ROOT/'span_dev_prepare.py')],cwd=str(WORKSPACE),env=env,timeout=180)
    if prepare.returncode:raise RuntimeError('DEV_PREPARATION_FAILED')
    score=subprocess.run([sys.executable,str(ROOT/'run_span_dev_score.py')],cwd=str(WORKSPACE),env=env,timeout=360)
    if score.returncode:raise RuntimeError('DEV_SCORING_FAILED')
finally:
    if started:
        current=json.loads(command(['docker','inspect',NAME]))[0]
        assert current['Id']==info['Id'] and current['Config']['Labels'].get(LABEL)=='true','OWNED_CLONE_ID_CHANGED'
        command(['docker','stop',NAME],timeout=30)

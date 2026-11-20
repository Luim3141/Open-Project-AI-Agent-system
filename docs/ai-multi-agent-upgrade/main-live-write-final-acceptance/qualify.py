"""Exact candidate build + offline Linux tests. No serving change, no Google."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from free_tier_staging import private_directory

def run(*args):
    p=subprocess.run(args,capture_output=True,timeout=180)
    assert p.returncode==0,'QUALIFICATION_COMMAND_FAILED:'+str(args[:3])
    return p.stdout.decode()

def main():
    assert not (OUT/'qualification.json').exists(),'QUALIFICATION_EXISTS_RECONCILE'
    private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/main-live-write-final-acceptance';private_directory(private)
    previous=json.loads((OUT.parent/'main-write-403-recovery/qualification.json').read_text())
    files={p.relative_to(ROOT/'openproject/ai').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT/'openproject/ai/gateway').rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    sha=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    r={'source':files,'source_sha256':sha,'rollback_gateway':previous['gateway_image'],'core_image':previous['core_image'],'phase':'BUILDING','google_calls':0}
    def save():(OUT/'qualification.json').write_text(json.dumps(r,indent=2))
    save()
    before=private/'source-before';private_directory(before)
    for name in ('ai_worker.py','gemini.py'):
        run('docker','cp','qldapm-ai-gateway-1:/app/gateway/'+name,str(before/name))
    with (OUT/'gateway-build.log').open('wb') as log:
        p=subprocess.run(['docker','build','-f','openproject/ai/Dockerfile','-t','qldapm-ai:owner-live-write-20261021',
            '--label','org.qldapm.source.sha256='+sha,'openproject/ai'],stdout=log,stderr=subprocess.STDOUT,timeout=600)
    assert p.returncode==0,'BUILD_FAILED'
    r['gateway_image']=run('docker','image','inspect','qldapm-ai:owner-live-write-20261021','--format','{{.Id}}').strip();save()
    with (OUT/'linux-tests.log').open('wb') as log:
        p=subprocess.run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=256m',
            '--mount',f'type=bind,src={ROOT}/openproject/ai/tests,dst=/tests,readonly',
            '--env','PYTHONPATH=/app:/','--env','QLDAPM_AI_RUNTIME=','--entrypoint','python',r['gateway_image'],
            '-m','unittest','tests.test_business_acceptance','tests.test_main_write_routing','tests.test_ai_worker',
            'tests.test_assistant_business','tests.test_live_agents','tests.test_main_business_mode'],stdout=log,stderr=subprocess.STDOUT,timeout=180)
    r['linux_exit']=p.returncode;r['phase']='LINUX_PASS' if p.returncode==0 else 'LINUX_FAIL';save()
    assert p.returncode==0,'LINUX_TESTS_FAILED'
    print(json.dumps({k:v for k,v in r.items() if k!='source'}))

if __name__=='__main__':main()

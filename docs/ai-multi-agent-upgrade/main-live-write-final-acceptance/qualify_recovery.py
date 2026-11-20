"""Second minimal recovery candidate; keeps original build/test/live receipts intact."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
def main():
    assert not (OUT/'qualification-recovery.json').exists(),'RECOVERY_QUALIFICATION_EXISTS'
    source={p.relative_to(ROOT/'openproject/ai').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT/'openproject/ai/gateway').rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    sha=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
    r={'source':source,'source_sha256':sha,'phase':'BUILDING','google_calls':0,'native_mutations':0}
    def save():(OUT/'qualification-recovery.json').write_text(json.dumps(r,indent=2))
    save()
    with (OUT/'recovery-build.log').open('wb') as f:
        p=subprocess.run(['docker','build','-f','openproject/ai/Dockerfile','-t','qldapm-ai:owner-live-recovery-20261022',
            '--label','org.qldapm.source.sha256='+sha,'openproject/ai'],stdout=f,stderr=subprocess.STDOUT,timeout=600)
    assert p.returncode==0,'BUILD_FAILED'
    r['gateway_image']=subprocess.check_output(['docker','image','inspect','qldapm-ai:owner-live-recovery-20261022','--format','{{.Id}}'],text=True).strip();save()
    with (OUT/'recovery-linux-tests.log').open('wb') as f:
        p=subprocess.run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=256m',
            '--mount',f'type=bind,src={ROOT}/openproject/ai/tests,dst=/tests,readonly','--env','PYTHONPATH=/app:/',
            '--env','QLDAPM_AI_RUNTIME=','--entrypoint','python',r['gateway_image'],'-m','unittest',
            'tests.test_native_create_recovery','tests.test_business_acceptance','tests.test_main_write_routing','tests.test_ai_worker',
            'tests.test_assistant_business','tests.test_live_agents','tests.test_main_business_mode'],stdout=f,stderr=subprocess.STDOUT,timeout=180)
    r['linux_exit']=p.returncode;save();assert p.returncode==0,'LINUX_TESTS_FAILED'
    private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/main-live-write-final-acceptance/clone-state'
    with (OUT/'clone-recovery.log').open('wb') as f:
        p=subprocess.run(['docker','run','--rm','--network','qldapm-write403-20261021-internal','--read-only','--tmpfs','/tmp:size=64m',
            '--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','512m','--env','PYTHONPATH=/app',
            '--mount',f'type=bind,src={private},dst=/state','--mount',f'type=bind,src={OUT}/clone_recovery.py,dst=/qualification.py,readonly',
            '--entrypoint','python',r['gateway_image'],'/qualification.py'],stdout=f,stderr=subprocess.STDOUT,timeout=180)
    r['clone_exit']=p.returncode;save();assert p.returncode==0,'CLONE_RECOVERY_FAILED'
    shutil.copy2(private/'clone-recovery-result.json',OUT/'clone-recovery-result.json')
    r['phase']='RECOVERY_QUALIFIED_NO_NEW_CREATE';save();print(json.dumps({k:v for k,v in r.items() if k!='source'}))
if __name__=='__main__':main()

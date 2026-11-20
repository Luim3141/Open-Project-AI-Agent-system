"""Build immutable candidates and test offline. Never changes a serving container."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
SUITES=['test_business_lifecycle','test_native_create_recovery','test_business_acceptance','test_main_write_routing',
 'test_ai_worker','test_assistant_business','test_live_agents','test_main_business_mode','test_execution_monitor',
 'test_rbac','test_control_center_authorization','test_rbac_cross_role_matrix','test_prompt_injection_and_secret_exfil']
def run(args,log,timeout=600):
    with (OUT/log).open('wb') as f:p=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,timeout=timeout)
    assert p.returncode==0,'QUALIFICATION_FAILED: '+log
def main():
    previous=json.loads((OUT/'qualification.json').read_text()) if (OUT/'qualification.json').exists() else None
    files={p.relative_to(ROOT/'openproject/ai').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
      for folder in ('gateway','core/overlay') for p in (ROOT/'openproject/ai'/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    sha=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    run(['docker','build','-f','openproject/ai/Dockerfile','-t','qldapm-ai:closeout-20261022','--label','org.qldapm.source.sha256='+sha,'openproject/ai'],'gateway-build.log')
    if '--gateway-only' in sys.argv:
        assert previous and {p:h for p,h in files.items() if p.startswith('core/overlay/')}=={p:h for p,h in previous['source'].items() if p.startswith('core/overlay/')}
        core_image=subprocess.check_output(['docker','inspect','qldapm-openproject-web-1','--format','{{.Image}}'],text=True).strip()
        assert core_image==previous['core_image'],'CORE_DRIFT'
    else:
        base=json.loads((OUT/'baseline.json').read_text())['containers']['qldapm-openproject-web-1']['image']
        subprocess.run(['docker','tag',base,'qldapm-core:closeout-baseline-20261022'],check=True)
        run(['docker','build','-f','openproject/ai/automation/ExecutionMonitorCore.Dockerfile','--build-arg','CORE_IMAGE=qldapm-core:closeout-baseline-20261022',
            '--build-arg','SOURCE_SHA256='+sha,'-t','qldapm-core:closeout-20261022','openproject/ai'],'core-build.log')
        core_image=subprocess.check_output(['docker','image','inspect','qldapm-core:closeout-20261022','--format','{{.Id}}'],text=True).strip()
    q={'source':files,'source_sha256':sha,'gateway_image':subprocess.check_output(['docker','image','inspect','qldapm-ai:closeout-20261022','--format','{{.Id}}'],text=True).strip(),
       'core_image':core_image,'phase':'BUILT_NOT_QUALIFIED'}
    (OUT/'qualification.json').write_text(json.dumps(q,indent=2))
    run([str(ROOT/'openproject/ai/.venv/Scripts/python.exe'),'-m','unittest',*['tests.'+s for s in SUITES]],'windows-tests.log',180)
    linux=['tests.'+s for s in SUITES if s not in {'test_rbac','test_control_center_authorization'}]+[
       'tests.test_rbac.RbacTests.'+name for name in ('test_native_effective_permissions_can_remove_pm_tools',
       'test_all_roles_rest_mcp_native_and_strict_deny_before_proposal_or_native_write',
       'test_gemini_declarations_are_filtered_by_backend_role_and_prompt_cannot_restore_tools','test_comment_endpoint_rejects_business_fields')]
    run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=256m','--mount',f'type=bind,src={ROOT}/openproject/ai/tests,dst=/tests,readonly',
       '--env','PYTHONPATH=/app:/','--env','QLDAPM_AI_RUNTIME=','--entrypoint','python',q['gateway_image'],'-m','unittest',*linux],'linux-tests.log',180)
    current=json.loads(subprocess.check_output(['docker','run','--rm','--network','none','--entrypoint','python',q['gateway_image'],'-c',
        "import hashlib,json;from pathlib import Path;print(json.dumps({str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/gateway').rglob('*') if p.is_file() and '__pycache__' not in str(p)}))"]))
    assert all(files.get(p)==h for p,h in current.items())
    q.update(phase='UNIT_SECURITY_PARITY_PASS_CLONE_PENDING',packaged_gateway_files=len(current),windows_exit=0,linux_exit=0)
    (OUT/'qualification.json').write_text(json.dumps(q,indent=2));print(json.dumps({k:v for k,v in q.items() if k!='source'}))
if __name__=='__main__':main()

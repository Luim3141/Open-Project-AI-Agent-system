import json,subprocess,sys,importlib
from pathlib import Path
reports='--reports' in sys.argv;polish='--polish' in sys.argv or reports
suffix='-reports' if reports else '-polish' if polish else ''
setup=importlib.import_module('release_reports' if reports else 'release_polish' if polish else 'release_cc')
OUT=Path(__file__).parent;ROOT=OUT.resolve().parents[4]
manifest=json.loads((setup.BUNDLE/'manifest.json').read_text());tests=['test_engineering_status_sync','test_engineering_owner_controls','test_engineering_auto_mode','test_cc_github_operations','test_cc_github_snapshot','test_store_wal_connections','test_phase31_integration_health','test_engineering_reporting','test_owner_uat_recovery','test_engineering_fencing','test_delegated_approval','test_integration_events','test_workflow_status','test_engineering_github_owner_contract']
image=manifest['images']['gateway']
if polish:tests.append('test_cc_summary_reads')
if reports:tests.extend(['test_owner_project_authority','test_cc_background_idle'])
p=subprocess.run(['docker','run','--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--tmpfs','/tmp:mode=1777','--mount',f'type=bind,source={ROOT/"openproject/ai/tests"},target=/tests,readonly','--mount',f'type=bind,source={ROOT/"openproject/ai/automation"},target=/qa/openproject/ai/automation,readonly','-e','PYTHONPATH=/app:/tests:/qa/openproject/ai','-e','QLDAPM_AI_RUNTIME=','--entrypoint','python',image,'-m','unittest',*tests,'-q'],capture_output=True,timeout=240)
result={'image':image,'tests':tests,'exit_code':p.returncode,'stdout_tail':p.stdout.decode()[-2000:],'stderr_tail':p.stderr.decode()[-2500:]}
(OUT/('image-regression'+suffix+'.json')).write_text(json.dumps(result,indent=2)+'\n');assert p.returncode==0,result;print(json.dumps(result))

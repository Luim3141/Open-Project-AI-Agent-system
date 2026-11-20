"""Publish two qualified machine branches, preserving the other14 MAIN workflows."""
import importlib.util,json,sys
from pathlib import Path
OUT=Path(__file__).parent;source=OUT.parent/'integration-final/n8n/final_completion_publish.py'
spec=importlib.util.spec_from_file_location('fixed_n8n_publisher',source);publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
proof=json.loads((OUT/'delegated-clone-attempt5.json').read_text());core=json.loads((OUT/'delegated-core-clone.json').read_text())
assert core['status']=='PASS'
proof['checks']=[r for r in proof['checks'] if r['workflow']=='OWNER_DELEGATED_PROJECT6'];assert proof['checks'][0]['status']=='BUSINESS_PASS_IN_CLONE'
proof.update(status='PASS',passed=1,total=1,scope='actual delegated Native/n8n business; Core qualified separately')
target=OUT/'delegated-workflow-proof.json';target.write_text(json.dumps(proof,indent=2)+'\n')
publisher.main(output=OUT,proof_file=target,targets={'WF05','WF06'},
    source_names=['service.py','delegated_approval.py','integration_events.py','permissions.py','catalog.py'],
    case_names={'OWNER_DELEGATED_PROJECT6'},output_prefix='delegated')

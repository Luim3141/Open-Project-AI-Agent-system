"""Read-only consistency check of handoff, frozen source and evidence."""
from pathlib import Path
import hashlib,json
RUN=Path(__file__).parent;ROOT=RUN.parents[4];DOC=RUN.parent
m=json.loads((RUN/'source-versioning-manifest.json').read_text())
for row in m['included']:
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
for name in ['N8N_EVENT_PUBLISHER_EVIDENCE.md','N8N_SECRET_RETENTION_REMEDIATION.md','BACKUP_RESTORE_DRILL.md',
             'WP385_RECOVERY_PROPOSAL.md','DEMO_RELEASE_CANDIDATE.md','FINAL_PRE_ROLLOUT_ACCEPTANCE.md']:
    assert (DOC/name).is_file() and (DOC/name).stat().st_size>500,name
matrix=json.loads((DOC/'09_TEST_EXECUTION_RESULTS.json').read_text())
assert matrix['fix_commit']==m['commit']
assert len([r for r in matrix['suites'] if r['test_id']=='P2-LINUX'])==1
assert 'Ran 182 tests' in (RUN/'linux-final-regression.log').read_text()
assert all(c['exit_code']==0 for c in json.loads((RUN/'final-checks.json').read_text()))
assert len(json.loads((RUN/'candidate-final-parity.json').read_text()))==15
assert not any(p.suffix in {'.dump','.sqlite','.db'} for p in RUN.rglob('*') if p.is_file())
proposal=(RUN/'rollout-proposal.json').read_bytes();digest=hashlib.sha256(proposal).hexdigest()
assert digest in (DOC/'FINAL_PRE_ROLLOUT_ACCEPTANCE.md').read_text()
assert digest in (DOC/'12_CONTINUATION_HANDOFF.md').read_text()
result={'status':'EVIDENCE_CONSISTENT','frozen_source_files':len(m['included']),'commit':m['commit'],
        'affected_tests':182,'image_parity_files':15,'proposal_sha256':digest,'db_artifacts_in_run':0,
        'main_applied':False,'manual_uat':'PENDING OWNER MANUAL UAT'}
(RUN/'final-evidence-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

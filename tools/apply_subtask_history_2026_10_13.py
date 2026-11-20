"""Apply only the exact owner-approved additive Subtask history gate, never replay."""
import hashlib
import json
from pathlib import Path
import jira_admin_mcp as admin

root = Path(__file__).resolve().parents[1]
assert hashlib.sha256((root/'forge/qag3-validator/manifest.yml').read_bytes()).hexdigest() == '73e07c827783c6471237ddce83d84bd5315367c1a854761f6e40bc0437a07f3a'
assert hashlib.sha256((root/'forge/qag3-validator/manifest.subtask-history-split-candidate.yml').read_bytes()).hexdigest() == 'b8e9648dc25dc7f2c420612a2fbede46dd47837e50f12a2bcf4003fff6c645f7'
result = admin.apply_change('67fad996-051e-4871-a0c3-1c2065f3f940',
    'da7c55436b262ca7b064057521727bff19c020e2fbd91fa6939d675caad9316f')
assert result['status'] == 'VERIFIED'
transition = next(t for t in result['workflow']['workflows'][0]['transitions'] if t['id'] == '4')
for key in ('qag3-subtask-acceptance', 'qag3-qa-freshness', 'qag3-subtask-history'):
    assert any(v.get('parameters', {}).get('key') == admin.FORGE_EXTENSION + key and
        v['parameters'].get('disabled') == 'false' for v in transition['validators'])
print(json.dumps({'previewId': result['previewId'], 'status': result['status'],
    'workflowVersion': result['workflow']['workflows'][0]['version'], 'threeGatesVerified': True}))

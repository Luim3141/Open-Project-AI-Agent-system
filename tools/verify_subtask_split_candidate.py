"""Read-only fixed Subtask split candidate; never deploys or mutates Jira."""
import hashlib
import json
import re
from pathlib import Path
import jira_admin_mcp as admin

admin.preflight()
data = (Path(__file__).resolve().parents[1] / 'forge/qag3-validator/manifest.subtask-history-split-candidate.yml').read_bytes()
matches = re.findall(r'    - key: ([a-z0-9-]+)\r?\n.*?      expression: >-\r?\n(.*?)      errorMessage:', data.decode(), re.S)
assert len(matches) == 12
expressions = {key: ' '.join(line.strip() for line in body.splitlines()) for key, body in matches}
print(json.dumps({'candidateSha256': hashlib.sha256(data).hexdigest(), 'moduleCount': len(matches)}))
for key in ('qag3-subtask-acceptance', 'qag3-subtask-history'):
    expression = expressions[key]
    analysis = admin.request('POST', '/expression/analyse', params={'check': 'complexity'},
        body={'expressions': [expression], 'contextVariables': {'originalIssue': 'Issue'}})
    print(json.dumps({'module': key, 'analysis': [{k: result.get(k) for k in ('valid', 'type', 'complexity', 'errors')} for result in analysis['results']]}))
    for fixture in ('QAG3-335', 'QAG3-336'):
        result = admin.request('POST', '/expression/evaluate', params={'expand': 'meta.complexity'},
            body={'expression': expression, 'context': {'issue': {'key': fixture},
                'custom': {'originalIssue': {'type': 'issue', 'key': fixture}}}}, expected=(200, 400))
        print(json.dumps({'module': key, 'fixture': fixture, 'value': result.get('value'),
            'errors': result.get('errorMessages'), 'meta': result.get('meta'), 'nativeProof': False}))

# Isolate the cost before proposing another native deployment.
for label, probe in (
    ('history-ids', 'originalIssue.changelogs.map(change => change.id).length'),
    ('history-items', 'originalIssue.changelogs.map(change => change.items.map(item => item.fieldId)).length'),
    ('history-authors', 'originalIssue.changelogs.map(change => change.author).length'),
    ('latest-status', "originalIssue.getNewestChangelog('status') != null"),
):
    result = admin.request('POST', '/expression/evaluate', params={'expand': 'meta.complexity'},
        body={'expression': probe, 'context': {'issue': {'key': 'QAG3-336'},
            'custom': {'originalIssue': {'type': 'issue', 'key': 'QAG3-336'}}}}, expected=(200, 400))
    print(json.dumps({'costProbe': label, 'value': result.get('value'),
        'errors': result.get('errorMessages'), 'meta': result.get('meta'), 'nativeProof': False}))

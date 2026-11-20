"""Read-only explicit Boolean history-snapshot candidate; fixed335/336 only."""
import hashlib
import json
import re
from pathlib import Path
import jira_admin_mcp as admin
admin.preflight()
data=(Path(__file__).resolve().parents[1]/'forge/qag3-validator/manifest.subtask-history-candidate.yml').read_bytes()
matches=re.findall(r'    - key: ([a-z0-9-]+)\r?\n.*?      expression: >-\r?\n(.*?)      errorMessage:',data.decode(),re.S)
assert len(matches)==11
expressions={key:' '.join(line.strip() for line in body.splitlines()) for key,body in matches}
expression=expressions['qag3-subtask-acceptance']
result=admin.request('POST','/expression/analyse',params={'check':'complexity'},
    body={'expressions':[expression],'contextVariables':{'originalIssue':'Issue'}})
print(json.dumps({'candidateSha256':hashlib.sha256(data).hexdigest(),
    'analysis':[{k:r.get(k) for k in ('valid','type','complexity','errors')} for r in result['results']]}))
for issue in ('QAG3-335','QAG3-336'):
    response=admin.request('POST','/expression/evaluate',params={'expand':'meta.complexity'},
        body={'expression':expression,'context':{'issue':{'key':issue},
            'custom':{'originalIssue':{'type':'issue','key':issue}}}},expected=(200,400))
    print(json.dumps({'issueKey':issue,'value':response.get('value'),
        'errors':response.get('errorMessages'),'meta':response.get('meta')}))

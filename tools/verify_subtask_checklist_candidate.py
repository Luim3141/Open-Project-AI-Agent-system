"""Read-only candidate analysis on fixed QAG3-332/335/336; no deploy/transition."""
import hashlib
import json
import re
from pathlib import Path
import jira_admin_mcp as admin

admin.preflight()
data=(Path(__file__).resolve().parents[1]/'forge/qag3-validator/manifest.subtask-checklist-candidate.yml').read_bytes()
matches=re.findall(r'    - key: ([a-z0-9-]+)\r?\n.*?      expression: >-\r?\n(.*?)      errorMessage:',data.decode(),re.S)
assert len(matches)==11
expressions={key:' '.join(line.strip() for line in body.splitlines()) for key,body in matches}
print(json.dumps({'candidateSha256':hashlib.sha256(data).hexdigest()}))
for key in ('qag3-subtask-acceptance','qag3-qa-freshness'):
    expression=expressions[key]
    result=admin.request('POST','/expression/analyse',params={'check':'complexity'},
        body={'expressions':[expression],'contextVariables':{'originalIssue':'Issue'}})
    print(json.dumps({'module':key,'analysis':[{k:r.get(k) for k in ('valid','type','complexity','errors')} for r in result['results']]}))
    for issue in ('QAG3-332','QAG3-336'):
        response=admin.request('POST','/expression/evaluate',params={'expand':'meta.complexity'},
            body={'expression':expression,'context':{'issue':{'key':issue},
                'custom':{'originalIssue':{'type':'issue','key':issue}}}},expected=(200,400))
        print(json.dumps({'module':key,'issueKey':issue,'value':response.get('value'),
                          'errors':response.get('errorMessages'),'meta':response.get('meta')}))

source=expressions['qag3-subtask-acceptance']
for label, projection in (
    ('history-row-snapshot', "originalIssue.changelogs.map(change => ({id:change.id,author:change.author,created:change.created,items:change.items}))"),
    ('history-item-snapshot', "originalIssue.changelogs.map(change => ({id:change.id,author:change.author,created:change.created,items:change.items.map(item => ({fieldId:item.fieldId,from:item.from,to:item.to,fromString:item.fromString,toString:item.toString}))}))")):
    candidate=source.replace('let history = originalIssue.changelogs;', 'let history = '+projection+';')
    result=admin.request('POST','/expression/analyse',params={'check':'complexity'},
        body={'expressions':[candidate],'contextVariables':{'originalIssue':'Issue'}})
    response=admin.request('POST','/expression/evaluate',params={'expand':'meta.complexity'},
        body={'expression':candidate,'context':{'issue':{'key':'QAG3-336'},
            'custom':{'originalIssue':{'type':'issue','key':'QAG3-336'}}}},expected=(200,400))
    print(json.dumps({'case':label,'analysis':[{k:r.get(k) for k in ('valid','type','complexity','errors')} for r in result['results']],
        'value':response.get('value'),'errors':response.get('errorMessages'),'meta':response.get('meta')}))

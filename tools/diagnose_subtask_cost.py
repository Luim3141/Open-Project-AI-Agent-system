"""Read-only cost probes for the two fixed QAG3 Subtask qualification fixtures."""
import json
import hashlib
import re
from pathlib import Path
import jira_admin_mcp as admin

admin.preflight()
admin.pinned_expressions()
# Preserve the failed deployed2.16 experiment after source promotion.
baseline=(Path(__file__).resolve().parents[1]/'forge/qag3-validator/manifest.before-subtask-cost-2026-10-13.yml').read_bytes()
fingerprint=hashlib.sha256(baseline).hexdigest()
assert fingerprint=='6b4782bda709d0e3333ff8f547b59d23139d5cf0cfedb7715246f476ec13d3df'
matches=re.findall(r'    - key: ([a-z0-9-]+)\r?\n.*?      expression: >-\r?\n(.*?)      errorMessage:',baseline.decode(),re.S)
assert len(matches)==11
expressions=[(key,' '.join(line.strip() for line in body.splitlines())) for key,body in matches]
source = dict(expressions)['qag3-subtask-acceptance']
qa_source = dict(expressions)['qag3-qa-current']
plain = qa_source[qa_source.index('let plain ='):qa_source.index('let project =')]
plain = plain.replace("task && typeof value", "typeof value")
candidate = plain + source[source.index('let evidence ='):]
aliases = {'issue.project': 'scopeProject', 'issue.assignee': 'currentAssignee',
           'originalIssue.assignee': 'previousAssignee', 'issue.description': 'currentDescription',
           'originalIssue.description': 'previousDescription', 'issue.parent': 'currentParent',
           'originalIssue.parent': 'previousParent'}
for field, alias in aliases.items():
    candidate = candidate.replace(field, alias)
candidate = ' '.join(f'let {alias} = {field};' for field, alias in aliases.items()) + ' ' + candidate
pending = (
    "issue.summary == originalIssue.summary && (issue.description == null ? null : issue.description.plainText) == (originalIssue.description == null ? null : originalIssue.description.plainText) && "
    "(issue.parent == null ? originalIssue.parent == null : originalIssue.parent != null && issue.parent.id == originalIssue.parent.id) && ")
assert source.count(pending) == 2
split = plain + source[source.index('let evidence ='):]
split = split.replace(pending, '').replace(
    "(issue.assignee == null ? originalIssue.assignee == null : originalIssue.assignee != null && issue.assignee.accountId == originalIssue.assignee.accountId) && ", '')
split = split.replace("issue.assignee.accountId == originalIssue.assignee.accountId && ", '')
split = split.replace('issue.assignee', 'committedAssignee').replace('originalIssue.assignee', 'committedAssignee')
split = 'let committedAssignee = originalIssue.assignee; ' + split
split = split.replace('issue.project', 'scopeProject')
split = 'let scopeProject = issue.project; ' + split
split = split.replace('evidence == plain(originalIssue.customfield_10045)', 'evidence == previous')
companion = (
    "let currentAssignee = issue.assignee; let previousAssignee = originalIssue.assignee; "
    "let currentParent = issue.parent; let previousParent = originalIssue.parent; "
    "let currentDescription = issue.description; let previousDescription = originalIssue.description; "
    "issue.key.indexOf('QAG3-') == 0 && issue.issueType.id == 10010 && originalIssue.status.id == 10012 && "
    "issue.summary == originalIssue.summary && "
    "(currentDescription == null ? null : currentDescription.plainText) == (previousDescription == null ? null : previousDescription.plainText) && "
    "(currentParent == null ? previousParent == null : previousParent != null && currentParent.id == previousParent.id) && "
    "(currentAssignee == null ? previousAssignee == null : previousAssignee != null && currentAssignee.accountId == previousAssignee.accountId)")
policy_split = split.replace('let scopeProject = issue.project; ', '')
policy_split = policy_split.replace("scopeProject.id == 10002 && scopeProject.key == 'QAG3' && ", '')
policy_split = policy_split.replace('committedAssignee.active && ', '')
policy_split = policy_split.replace("user != null && user.active && ['712020:0d04982c-00bf-46af-b3a7-446d0f44edfb', '712020:47b24428-aa71-4363-b68f-29ed2285aad8'].includes(user.accountId) && ", '')
policy_split = policy_split.replace('issue.issueType.id == 10010 && originalIssue.status.id == 10012 && ', '')
policy_split = policy_split.replace('[10011, 10010].includes(issue.issueType.id) && [10012, 10019].includes(originalIssue.status.id) && ', '')
policy_companion = (
    "let scopeProject = issue.project; " + companion.rsplit('; ', 1)[0] + '; ' +
    "scopeProject.id == 10002 && scopeProject.key == 'QAG3' && "
    "user != null && user.active && ['712020:0d04982c-00bf-46af-b3a7-446d0f44edfb', '712020:47b24428-aa71-4363-b68f-29ed2285aad8'].includes(user.accountId) && "
    "currentAssignee != null && currentAssignee.active && " + companion.rsplit('; ', 1)[1])
def function_body(expression):
    declarations, _, final = expression.rpartition('; ')
    return declarations + '; return ' + final + ';'

combined_companion = ('let subtaskGate = ignored => {' + function_body(policy_companion) + '}; '
    + 'let taskGate = ignored => {' + function_body(dict(expressions)['qag3-qa-freshness']) + '}; '
    + 'issue.issueType.id == 10010 ? subtaskGate(true) : taskGate(true)')
print(json.dumps({'candidateExpressions': {'qag3-subtask-acceptance': policy_split,
    'qag3-qa-freshness': combined_companion}}))
business_evidence = '\\n'.join(('Revision: SIMULATION-BUSINESS-2026-10-13-v1',
    'Review scope: Native business acceptance candidate', 'Review result: SIMULATED ACCEPTED',
    'Evidence: SIMULATION ONLY - synthetic fixture; no real acceptance'))
business_pending = policy_split.replace('let evidence = plain(issue.customfield_10045);',
                                        'let evidence = ' + json.dumps(business_evidence) + ';')
for label, expression in [('deployed', source), ('cache-and-ADF-candidate', candidate),
                          ('split-acceptance-candidate', split), ('pending-fields-companion', companion),
                          ('split-with-actor-scope-companion', policy_split), ('actor-scope-pending-companion', policy_companion),
                          ('combined-existing-companion', combined_companion), ('business-pending-read-only', business_pending)]:
    analysis = admin.request('POST', '/expression/analyse', params={'check':'complexity'},
        body={'expressions':[expression], 'contextVariables':{'originalIssue':'Issue'}})
    results = analysis.get('results', [])
    print(json.dumps({'case':label, 'manifestSha256':fingerprint,
        'analysis':[{k:r.get(k) for k in ('valid','type','complexity','errors')} for r in results]}))
    for key in ('QAG3-335', 'QAG3-336'):
        result = admin.request('POST','/expression/evaluate', params={'expand':'meta.complexity'},
            body={'expression':expression, 'context':{'issue':{'key':key},
                'custom':{'originalIssue':{'type':'issue','key':key}}}}, expected=(200,400))
        print(json.dumps({'case':label, 'issueKey':key, 'value':result.get('value'),
            'errors':result.get('errorMessages'), 'meta':result.get('meta')}))

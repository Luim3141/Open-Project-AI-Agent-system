"""Read only the four fixed QAG3 rules; emit configuration checks, not email bodies/secrets."""
import json
import jira_admin_mcp as admin

admin.preflight()
expected = ('01a12eca-5f11-7ef3-9c33-3898c7b1e9f2', '01a12ee4-1276-76b4-ba01-49bdeda52f9d',
            '01a13075-71e9-7e0f-b65f-006ec2a4b83b', '01a13075-71e9-750f-9913-5e43ba4adaf0')
summaries = admin.inspect_automation()
assert summaries['readComplete']

def components(nodes):
    for node in nodes:
        yield node
        yield from components(node.get('children', []))

for rule_id in expected:
    assert any(row['uuid'] == rule_id for row in summaries['rules'])
    rule = admin.request('GET', f'/rest/v1/rule/{rule_id}', automation=True,
                         params={'redactSensitiveFields':'true'})['rule']
    assert rule['uuid'] == rule_id and rule['ruleScopeARIs'] == [admin.SCOPE_ARI]
    nodes = list(components(rule['components']))
    serialized = json.dumps(rule)
    if rule_id == expected[-1]:
        variable = next(node['value'] for node in nodes if node['type'] == 'jira.create.variable')
        assert variable['name']['value'] == 'qagReviewEventKey' and variable['lazy'] is False
        assert variable['query']['value'] == 'qag3-a05-{{triggerIssue.status.id}}-{{triggerIssue.updated.format("yyyyMMddHHmmssSSS")}}'
        guard = next(node['value'] for node in nodes if node['type'] == 'jira.comparator.condition')
        assert guard == {'first':'{{issue.status.id}}-{{qagReviewEventKey.length}}',
                         'second':'{{qagReviewEventKey.substring(9,14)}}-32', 'operator':'EQUALS'}
        dedup = next(node['value'] for node in nodes if node['type'] == 'jira.jql.condition')
        assert 'status in (10016,10012,10019)' in dedup and 'labels not in ("{{qagReviewEventKey}}")' in dedup
        comments = [node['value'] for node in nodes if node['type'] == 'jira.issue.comment']
        assert len(comments) == 2 and not any('email' in node['type'] for node in nodes)
        for comment, account in zip(comments, (
                '712020:0d04982c-00bf-46af-b3a7-446d0f44edfb',
                '712020:47b24428-aa71-4363-b68f-29ed2285aad8')):
            assert comment['comment'].startswith(f'[~accountid:{account}]\n')
            assert '{{qagReviewEventKey}}' in comment['comment'] and '[SIMULATION' in comment['comment']
            assert comment['addCommentOnce'] is False and comment['sendNotifications']
            assert comment['commentVisibility'] is None and comment['publicComment'] is False
        print(json.dumps({'a05CommentConfigurationVerified': True, 'commentActions': len(comments),
                          'nativeIssueOnceGuard': False, 'eventKeyDedupGuard': True, 'emailActions': 0}))
    checks = {'uuid':rule_id, 'name':rule['name'], 'state':rule['state'],
              'eventToStatus': rule.get('trigger', {}).get('value', {}).get('toStatus'),
              'testScope': 'qag3-test' in json.dumps(rule.get('trigger')),
              'oldVariableReferences': serialized.count('qag3A05EventKey'),
              'unsupportedToMillisReferences': serialized.count('toMillis'),
              'nodeCount':len(nodes), 'emailRecipientTypes':[
                  [recipient.get('type') for recipient in node.get('value',{}).get('to',[])]
                  for node in nodes if 'email' in node.get('type','')],
              'componentTypes':sorted({node.get('type','') for node in nodes})}
    print(json.dumps(checks))

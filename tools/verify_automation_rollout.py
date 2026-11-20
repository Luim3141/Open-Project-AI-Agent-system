"""Read-only semantic verification after four fixed UI trigger scope changes."""
import json
import jira_admin_mcp as admin

admin.preflight()
before = json.loads((admin.AUDIT_ROOT / 'automation-rollout-before-2026-10-13.json').read_text(encoding='utf-8'))
assert len(before['rules']) == 4
assert {rule['uuid'] for rule in before['rules']} == {
    '01a12eca-5f11-7ef3-9c33-3898c7b1e9f2', '01a12ee4-1276-76b4-ba01-49bdeda52f9d',
    '01a13075-71e9-7e0f-b65f-006ec2a4b83b', '01a13075-71e9-750f-9913-5e43ba4adaf0'}
for old in before['rules']:
    rule = admin.request('GET', f"/rest/v1/rule/{old['uuid']}", automation=True,
        params={'redactSensitiveFields': 'true'})['rule']
    assert rule['uuid'] == old['uuid'] and rule['state'] == 'ENABLED'
    assert rule['ruleScopeARIs'] == old['ruleScopeARIs'] == [admin.SCOPE_ARI]
    assert rule['actor'] == old['actor']
    assert rule['components'] == old['components'], 'No action, branch, marker or gate change is approved in this rollout.'
    expected = json.loads(json.dumps(old['trigger']).replace(' AND labels = qag3-test', ''))
    if old['uuid'] == '01a12eca-5f11-7ef3-9c33-3898c7b1e9f2':
        expected['value']['toStatus'] = [{'type': 'NAME', 'value': 'Done'}]
    assert rule['trigger'] == expected
    print(json.dumps({'uuid': rule['uuid'], 'name': rule['name'], 'state': rule['state'],
        'qag3Only': True, 'testLabelRequired': False, 'actorPreserved': True,
        'componentsPreserved': True, 'onlyApprovedTriggerChanges': True,
        'eventToDoneOnly': old['uuid'] == '01a12eca-5f11-7ef3-9c33-3898c7b1e9f2'}))

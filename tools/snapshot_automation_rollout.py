"""Read-only before snapshot of four fixed rules for authorized UI scope rollout."""
import json
import jira_admin_mcp as admin

admin.preflight()
ids = ('01a12eca-5f11-7ef3-9c33-3898c7b1e9f2', '01a12ee4-1276-76b4-ba01-49bdeda52f9d',
    '01a13075-71e9-7e0f-b65f-006ec2a4b83b', '01a13075-71e9-750f-9913-5e43ba4adaf0')
target = admin.AUDIT_ROOT / 'automation-rollout-before-2026-10-13.json'
assert not target.exists(), 'Preserve existing before snapshot; do not overwrite or rerun.'
rules = []
for uuid in ids:
    rule = admin.request('GET', f'/rest/v1/rule/{uuid}', automation=True,
        params={'redactSensitiveFields': 'true'})['rule']
    assert rule['uuid'] == uuid and rule['ruleScopeARIs'] == [admin.SCOPE_ARI]
    assert rule['state'] == 'ENABLED' and 'labels = qag3-test' in json.dumps(rule['trigger'])
    rules.append(rule)
admin.AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
admin.save_record(target, {'rules': rules, 'site': 'luimjiraqldapm.atlassian.net', 'purpose': 'UI removal of qag3-test predicate only; not a Jira write'})
print(json.dumps({'snapshot': str(target), 'ruleCount': len(rules), 'readComplete': True}))

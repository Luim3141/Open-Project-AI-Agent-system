"""Additive history companion cannot replace either retained Subtask gate."""
import copy
import unittest
from test_jira_forge_gates import fixtures
import jira_admin_mcp as admin


class SubtaskHistoryTests(unittest.TestCase):
    def test_retained_partners_and_idempotency(self):
        before, _ = fixtures()
        wf = before['workflows'][0]
        wf['id'] = admin.WORKFLOWS['subtask']
        wf['transitions'] = [dict(id='4', name='Approve work', toStatusReference='10009',
            links=[{'fromStatusReference': '10012'}], actions=[{'ruleKey': 'retained'}],
            transitionScreen={'ruleKey': 'system:transition-screen', 'parameters': {'screenId': '10010'}},
            validators=[{'ruleKey': 'forge:expression-validator', 'parameters': {
                'key': admin.FORGE_EXTENSION + key, 'disabled': 'false', 'config': '{}'}}
                for key in ('qag3-subtask-acceptance', 'qag3-qa-freshness')])]
        snapshot = copy.deepcopy(before)
        catalog = [{'id': admin.FORGE_EXTENSION + key, 'ruleKey': 'forge:expression-validator',
            'ruleType': 'Validator'} for key in ('qag3-qa-freshness', 'qag3-subtask-history')]
        payload, changes = admin.subtask_history_payload(before, catalog)
        self.assertEqual(snapshot, before)
        self.assertEqual([c['transitionId'] for c in changes], ['4'])
        old, new = wf['transitions'][0], payload['workflows'][0]['transitions'][0]
        self.assertEqual(new['validators'][:-1], old['validators'])
        for field in ('links', 'actions', 'transitionScreen'):
            self.assertEqual(old[field], new[field])
        _, repeated = admin.subtask_history_payload({'statuses': before['statuses'],
            'workflows': [{**payload['workflows'][0], 'isEditable': True}]}, catalog)
        self.assertEqual(repeated, [])
        for index in (0, 1):
            for action in ('remove', 'disable'):
                bad = copy.deepcopy(before)
                gates = bad['workflows'][0]['transitions'][0]['validators']
                if action == 'remove': gates.pop(index)
                else: gates[index]['parameters']['disabled'] = 'true'
                with self.subTest(index=index, action=action), self.assertRaises(ValueError):
                    admin.subtask_history_payload(bad, catalog)
        for field, value in (('id', '13'), ('name', 'Retest'), ('toStatusReference', '3')):
            bad = copy.deepcopy(before)
            bad['workflows'][0]['transitions'][0][field] = value
            with self.assertRaises(ValueError): admin.subtask_history_payload(bad, catalog)


if __name__ == '__main__': unittest.main()

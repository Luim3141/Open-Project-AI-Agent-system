import copy
import unittest
from test_jira_forge_gates import fixtures
import jira_admin_mcp as admin


class EpicReturnTests(unittest.TestCase):
    def test_fixed_additive_reason_and_screen(self):
        before, _ = fixtures()
        wf = before['workflows'][0]
        wf['transitions'] = [dict(id='7', name='Return / scope changed', toStatusReference='3',
            links=[{'fromStatusReference':'10012'}], validators=[], actions=[{'ruleKey':'retained'}])]
        original = copy.deepcopy(before)
        rules = [{'id':admin.FORGE_EXTENSION+'qag3-fresh-change-reason',
                  'ruleKey':'forge:expression-validator','ruleType':'Validator'}]
        payload, changes = admin.epic_return_reason_payload(before, rules)
        self.assertEqual(before, original)
        self.assertEqual(len(changes), 2)
        transition = payload['workflows'][0]['transitions'][0]
        self.assertEqual(transition['actions'], wf['transitions'][0]['actions'])
        self.assertEqual(transition['transitionScreen']['parameters'], {'screenId':'10011'})
        _, repeat = admin.epic_return_reason_payload({'statuses':before['statuses'],
            'workflows':[{**payload['workflows'][0], 'isEditable':True}]}, rules)
        self.assertEqual(repeat, [])
        for diff in ('wrong-target','wrong-screen','wrong-id'):
            bad = copy.deepcopy(before)
            target = bad['workflows'][0]['transitions'][0]
            if diff == 'wrong-target': target['toStatusReference']='10009'
            elif diff == 'wrong-id': target['id']='8'
            else: target['transitionScreen']={'ruleKey':'system:transition-screen','parameters':{'screenId':'10010'}}
            with self.subTest(diff=diff), self.assertRaises(ValueError):
                admin.epic_return_reason_payload(bad, rules)

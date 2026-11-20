"""Additive/idempotent Subtask companion preparation; no Jira writes."""
import copy
import unittest
from test_jira_forge_gates import fixtures
import jira_admin_mcp as admin


class SubtaskFreshnessTests(unittest.TestCase):
    def test_fixed_transition_and_retained_partner(self):
        before, _ = fixtures()
        wf = before['workflows'][0]
        wf['id'] = admin.WORKFLOWS['subtask']
        wf['transitions'] = [dict(id='4', name='Approve work', toStatusReference='10009',
            links=[{'fromStatusReference':'10012'}], actions=[{'ruleKey':'retained'}],
            transitionScreen={'ruleKey':'system:transition-screen','parameters':{'screenId':'10010'}},
            validators=[{'ruleKey':'forge:expression-validator','parameters':{
                'key':admin.FORGE_EXTENSION+'qag3-subtask-acceptance','disabled':'false'}}])]
        original = copy.deepcopy(before)
        catalog = [{'id':admin.FORGE_EXTENSION+'qag3-qa-freshness',
                    'ruleKey':'forge:expression-validator','ruleType':'Validator'}]
        payload, changes = admin.subtask_qa_freshness_payload(before,catalog)
        self.assertEqual(before,original)
        self.assertEqual([c['transitionId'] for c in changes],['4'])
        old, new = wf['transitions'][0],payload['workflows'][0]['transitions'][0]
        self.assertEqual(old['validators'],new['validators'][:-1])
        for field in ('actions','transitionScreen','links'): self.assertEqual(old[field],new[field])
        _, repeated = admin.subtask_qa_freshness_payload({'statuses':before['statuses'],
            'workflows':[{**payload['workflows'][0],'isEditable':True}]},catalog)
        self.assertEqual(repeated,[])
        for mutation in ('partner-missing','partner-disabled','wrong-target','wrong-workflow'):
            bad=copy.deepcopy(before)
            if mutation=='partner-missing': bad['workflows'][0]['transitions'][0]['validators']=[]
            elif mutation=='partner-disabled': bad['workflows'][0]['transitions'][0]['validators'][0]['parameters']['disabled']='true'
            elif mutation=='wrong-target': bad['workflows'][0]['transitions'][0]['toStatusReference']='3'
            else: bad['workflows'][0]['id']=admin.WORKFLOWS['task']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                admin.subtask_qa_freshness_payload(bad,catalog)


if __name__=='__main__': unittest.main()

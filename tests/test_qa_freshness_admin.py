"""Fixed additive Task companion preview; no real Jira writes."""
import copy
import unittest
from test_jira_forge_gates import fixtures
import jira_admin_mcp as admin


class QaFreshnessTests(unittest.TestCase):
    def test_additive_idempotent_and_partner_required(self):
        before, _ = fixtures()
        wf = before['workflows'][0]
        wf['id'] = admin.WORKFLOWS['task']
        wf['transitions'] = [dict(id=tid, name=name, toStatusReference=target,
            links=[{'fromStatusReference': source}], actions=[{'ruleKey':'retained'}],
            validators=[{'ruleKey':'forge:expression-validator','parameters':{
                'key':admin.FORGE_EXTENSION+'qag3-qa-current','disabled':'false'}}])
            for tid, name, source, target in [('13','Approve','10012','10019'),('14','Deploy','10019','10009')]]
        original = copy.deepcopy(before)
        rules=[{'id':admin.FORGE_EXTENSION+'qag3-qa-freshness','ruleKey':'forge:expression-validator','ruleType':'Validator'}]
        payload, changes=admin.qa_freshness_payload(before,rules)
        self.assertEqual(before,original)
        self.assertEqual([change['transitionId'] for change in changes],['13','14'])
        for old,new in zip(wf['transitions'],payload['workflows'][0]['transitions']):
            self.assertEqual(old['actions'],new['actions'])
            self.assertEqual(old['validators'],new['validators'][:-1])
        _, repeated=admin.qa_freshness_payload({'statuses':before['statuses'],'workflows':[
            {**payload['workflows'][0],'isEditable':True}]},rules)
        self.assertEqual(repeated,[])
        for diff in ['missing','disabled','wrong-target']:
            bad=copy.deepcopy(before)
            if diff=='missing': bad['workflows'][0]['transitions'][0]['validators']=[]
            elif diff=='disabled': bad['workflows'][0]['transitions'][0]['validators'][0]['parameters']['disabled']='true'
            else: bad['workflows'][0]['transitions'][0]['toStatusReference']='3'
            with self.subTest(diff=diff), self.assertRaises(ValueError): admin.qa_freshness_payload(bad,rules)


if __name__=='__main__': unittest.main()

import json
import shutil
import subprocess
import unittest

from automation.deploy_real_n8n_workflows import build_workflows


@unittest.skipUnless(shutil.which('node'),'Node required for actual n8n adapter evaluation')
class NativeWbsWorkflowTests(unittest.TestCase):
    def route(self,body):
        w=build_workflows()['WF10'];code=next(n for n in w['nodes'] if n['type']=='n8n-nodes-base.code')['parameters']['jsCode']
        program="const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(new Function('$input',x.code)({first:()=>({json:{body:x.body}})})[0].json));"
        return json.loads(subprocess.check_output(['node','-e',program],input=json.dumps({'code':code,'body':body}).encode()))

    def test_legacy_options_and_own_plan_get_are_preserved(self):
        self.assertEqual(self.route({}),{'action':'get_project_options','arguments':{}})
        self.assertEqual(self.route({'operation':'get','id':'plan'}),{'action':'wbs_get','arguments':{'id':'plan'}})
        self.assertTrue(self.route({'operation':'get','id':'plan','actor_id':18})['action'].startswith('INVALID'))

    def test_draft_and_next_forward_data_and_exact_hash_but_no_approval(self):
        request='22222222-2222-4222-8222-222222222222'
        route=self.route({'operation':'draft','requirements':[],'nodes':[],'share_for_review':True,'request_id':request})
        self.assertEqual(route,{'action':'wbs_draft','arguments':{'requirements':[],'nodes':[],'share_for_review':True},'idempotency_key':'wf10-'+request})
        route=self.route({'operation':'next','id':'plan','hash':'a'*64,'request_id':request})
        self.assertEqual(route['action'],'wbs_next');self.assertEqual(route['arguments'],{'id':'plan','hash':'a'*64})
        self.assertTrue(self.route({'operation':'next','id':'plan','hash':'a'*64,'request_id':request,'approved':True})['action'].startswith('INVALID'))
        relations=[{'predecessor':'first','successor':'second','lag':2}]
        self.assertEqual(self.route({'operation':'draft','requirements':[],'nodes':[],'relations':relations,'request_id':request})['arguments']['relations'],relations)

    def test_ba_conversion_preserves_own_run_and_exact_output_hash(self):
        request='22222222-2222-4222-8222-222222222222'
        route=self.route({'operation':'from_ba','run_id':request,'output_hash':'a'*64,'share_for_review':True,'request_id':request})
        self.assertEqual(route,{'action':'wbs_from_ba','arguments':{'run_id':request,'output_hash':'a'*64,'share_for_review':True},'idempotency_key':'wf10-'+request})
        self.assertTrue(self.route({'operation':'from_ba','run_id':request,'output_hash':'a'*64,'actor_id':18,'request_id':request})['action'].startswith('INVALID'))

    def test_dependency_only_prepares_an_exact_proposal_and_rejects_authority_claims(self):
        request='22222222-2222-4222-8222-222222222222'
        body={'operation':'dependency','predecessor_id':376,'successor_id':377,'lag':2,'request_id':request}
        self.assertEqual(self.route(body),{'action':'create_dependency','arguments':{'predecessor_id':376,'successor_id':377,'lag':2},'idempotency_key':'wf10-'+request})
        for field in ['actor_id','approved','scope_hash','proposal_id','proposal_hash']:
            self.assertTrue(self.route({**body,field:True})['action'].startswith('INVALID'))

    def test_relation_changes_forward_only_explicit_relation_and_lag_without_approval(self):
        request='22222222-2222-4222-8222-222222222222'
        for operation,action,args in [('dependency_update','update_dependency',{'relation_id':353,'lag':2}),('dependency_delete','delete_dependency',{'relation_id':353})]:
            body={'operation':operation,**args,'request_id':request}
            self.assertEqual(self.route(body),{'action':action,'arguments':args,'idempotency_key':'wf10-'+request})
            for field in ['actor_id','approved','scope_hash','proposal_id','predecessor_id','successor_id','unexpected']:
                self.assertTrue(self.route({**body,field:True})['action'].startswith('INVALID'))
            self.assertTrue(self.route({**body,'request_id':'invalid'})['action'].startswith('INVALID'))


if __name__=='__main__':unittest.main()

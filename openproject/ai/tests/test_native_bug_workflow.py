import json
import shutil
import subprocess
import unittest

from automation.deploy_real_n8n_workflows import build_workflows


@unittest.skipUnless(shutil.which('node'),'Node required for actual n8n adapter evaluation')
class NativeBugWorkflowTests(unittest.TestCase):
    def route(self,body):
        workflow=build_workflows()['WF09']
        code=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.code')['parameters']['jsCode']
        program="const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(new Function('$input',x.code)({first:()=>({json:{body:x.body}})})[0].json));"
        return json.loads(subprocess.check_output(['node','-e',program],input=json.dumps({'code':code,'body':body}).encode()))

    def test_legacy_context_and_new_triage_keep_explicit_targets(self):
        self.assertEqual(self.route({'id':370}),{'action':'get_work_package','arguments':{'id':370,'include_context':True}})
        self.assertEqual(self.route({'operation':'triage','report':{'subject':'draft'}}),{'action':'bug_triage','arguments':{'report':{'subject':'draft'}}})
        self.assertTrue(self.route({})['action'].startswith('INVALID'))

    def test_proposal_adapter_preserves_lock_and_uses_stable_key_without_approval(self):
        body={'operation':'retest','id':39,'lock_version':3,'text':'submitted evidence','request_id':'11111111-1111-4111-8111-111111111111'}
        route=self.route(body)
        self.assertEqual(route['action'],'bug_propose');self.assertEqual(route['arguments']['lock_version'],3)
        self.assertEqual(route['idempotency_key'],'wf09-'+body['request_id'])
        self.assertTrue(self.route({**body,'approved':True})['action'].startswith('INVALID'))
        self.assertTrue(self.route({**body,'request_id':'bad'})['action'].startswith('INVALID'))

    def test_reviewed_qa_binding_reaches_native_transition_proposal(self):
        body={'operation':'transition','id':371,'lock_version':1,'status_id':9,
              'request_id':'11111111-1111-4111-8111-111111111111',
              'qa_evidence_id':'22222222-2222-4222-8222-222222222222','qa_evidence_hash':'a'*64}
        self.assertEqual(self.route(body)['arguments']['qa_evidence_hash'],'a'*64)
        self.assertTrue(self.route({**body,'qa_pass':True})['action'].startswith('INVALID'))


if __name__=='__main__':unittest.main()

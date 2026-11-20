import json
import shutil
import subprocess
import unittest

from automation.deploy_real_n8n_workflows import build_workflows


@unittest.skipUnless(shutil.which('node'), 'Node required for actual n8n adapter evaluation')
class NativeQaWorkflowTests(unittest.TestCase):
    def route(self, body):
        workflow=build_workflows()['WF11']
        code=next(n for n in workflow['nodes'] if n['type']=='n8n-nodes-base.code')['parameters']['jsCode']
        program="const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(new Function('$input',x.code)({first:()=>({json:{body:x.body}})})[0].json));"
        return json.loads(subprocess.check_output(['node','-e',program],input=json.dumps({'code':code,'body':body}).encode()))

    def test_legacy_guard_and_explicit_qa_capture_keep_caller_identity(self):
        self.assertEqual(self.route({'id':370,'approved':True}),{'action':'qa_evidence_list','arguments':{'native_id':370}})
        request='11111111-1111-4111-8111-111111111111'
        body={'operation':'capture','native_id':371,'activity_id':4242,'request_id':request}
        self.assertEqual(self.route(body),{'action':'qa_evidence_capture','arguments':{'native_id':371,'activity_id':4242},'idempotency_key':'wf11-'+request})
        for flag in ['actor_id','role','admin','owner','approved','qa_pass','file_path','extra']:
            self.assertTrue(self.route({**body,flag:True})['action'].startswith('INVALID'))

    def test_review_uses_separate_exact_decision_endpoint_and_prepare_is_only_proposal(self):
        identifier='11111111-1111-4111-8111-111111111111'
        body={'operation':'review','evidence_id':identifier,'decision':'accept','hash':'a'*64}
        self.assertEqual(self.route(body),{'qa_decision':True,'evidence_id':identifier,'payload':{'decision':'accept','hash':'a'*64}})
        command=self.route({'operation':'transition_prepare','evidence_id':identifier,'hash':'a'*64,'status_id':9,'request_id':identifier})
        self.assertEqual(command,{'action':'qa_transition_prepare','arguments':{'id':identifier,'hash':'a'*64,'status_id':9},'idempotency_key':'wf11-'+identifier})
        self.assertTrue(self.route({**body,'hash':'bad'})['action'].startswith('INVALID'))
        fetch=next(n for n in build_workflows()['WF11']['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
        self.assertIn('/api/v1/qa-evidence/',fetch['parameters']['url'])
        self.assertIn('headers.authorization',json.dumps(fetch['parameters']))

    def test_automated_runner_routes_are_read_only_and_never_accept_client_test_results(self):
        request='11111111-1111-4111-8111-111111111111'
        self.assertEqual(self.route({'operation':'run','native_id':375,'request_id':request}),
            {'action':'qa_test_run','arguments':{'native_id':375},'idempotency_key':'wf11-'+request})
        self.assertEqual(self.route({'operation':'run_get','run_id':request}),{'action':'qa_test_get','arguments':{'id':request}})
        self.assertEqual(self.route({'operation':'from_run','run_id':request,'request_id':request}),
            {'action':'qa_evidence_from_run','arguments':{'run_id':request},'idempotency_key':'wf11-'+request})
        for flag in ['passed','tests','producer','actor','role','approved','artifact','source_version']:
            self.assertTrue(self.route({'operation':'run','native_id':375,'request_id':request,flag:True})['action'].startswith('INVALID'))
        self.assertEqual(self.route({'operation':'list'}),{'action':'qa_evidence_list','arguments':{}})
        self.assertTrue(self.route({'operation':'list','actor_id':18})['action'].startswith('INVALID'))


if __name__=='__main__':unittest.main()

import json
import shutil
import subprocess
import unittest

from automation.deploy_real_n8n_workflows import build_workflows
from automation.n8n_integration_adapter import attach, enable_project6_business


@unittest.skipUnless(shutil.which('node'), 'Node required for actual adapter evaluation')
class Project6BusinessAdapterTests(unittest.TestCase):
    def route(self, code, body):
        workflow=build_workflows()[code]
        identifier='sprint_parameters' if code=='WF08' else 'explicit_request'
        source=next(n for n in workflow['nodes'] if n['id']==identifier)['parameters']['jsCode']
        program="const x=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log(JSON.stringify(new Function('$input',x.source)({first:()=>({json:{body:x.body}})})[0].json));"
        return json.loads(subprocess.check_output(['node','-e',program],input=json.dumps({'source':source,'body':body}).encode()))

    def test_explicit_project6_preserves_risk_bug_and_wbs_parameters(self):
        for code,body,action in [('WF08',{'as_of_date':'2026-11-03'},'sprint_risks'),
                                 ('WF09',{'operation':'triage','id':401},'bug_triage'),
                                 ('WF10',{'operation':'get','id':'plan'},'wbs_get')]:
            legacy=self.route(code,body)
            self.assertEqual(legacy['action'],action)
            self.assertNotIn('project_id',legacy)
            self.assertEqual(self.route(code,{**body,'project_id':6}),{**legacy,'project_id':6})
            for invalid in [5,7,'6',None,True]:
                self.assertEqual(self.route(code,{**body,'project_id':invalid})['action'],'INVALID_WORKFLOW_PROJECT_SCOPE')

    def test_scope_does_not_enable_native_materialization_or_authority_claims(self):
        request='22222222-2222-4222-8222-222222222222'
        self.assertEqual(self.route('WF10',{'operation':'next','id':'plan','hash':'a'*64,'request_id':request,'project_id':6})['action'],'INVALID_PROJECT6_WORKFLOW_ACTION')
        self.assertTrue(self.route('WF09',{'operation':'transition','id':401,'request_id':request,'project_id':6,'approved':True})['action'].startswith('INVALID'))

    def test_published_attachment_is_idempotent_and_adds_observer_to_wf10(self):
        for code in ['WF08','WF09','WF10']:
            workflow=build_workflows()[code]
            self.assertEqual(enable_project6_business(workflow),workflow)
            attached=attach(workflow)
            self.assertEqual(attach(attached),attached)
            if code=='WF10':self.assertTrue(any(n['id']=='integration-trigger' for n in attached['nodes']))


if __name__=='__main__':unittest.main()

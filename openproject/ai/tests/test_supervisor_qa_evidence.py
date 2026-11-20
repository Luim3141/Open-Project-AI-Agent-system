"""Supervisor may report a verified Native artifact, never invent execution or review."""
import json
import time
import unittest
import uuid
from unittest.mock import patch

import test_native_qa_runs as fixture
from gateway.agent_models import AgentTask,RunScope
from gateway.native import NativeError
from gateway.supervisor import Supervisor


class SupervisorQaEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.NativeQaRunTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.service=self.f.service;self.store=self.f.store

    def report(self,actor=19,version=1):
        from gateway.native_qa_runs import latest_report
        return latest_report(self.service,actor,371,version)

    def produce(self,key='supervisor-artifact'):
        return self.f.call(19,'qa_test_run',{'native_id':371},key)

    def task(self,actor=19):
        now=time.time();task=AgentTask(task_id=str(uuid.uuid4()),actor_id=actor,project_id=5,
            conversation_id=str(uuid.uuid4()),agent='qa',instruction='QA xác minh kết quả kiểm thử #371',created_at=now,expires_at=now+300)
        return task,RunScope(run_id=str(uuid.uuid4()),task_id=task.task_id,actor_id=actor,project_id=5,trace_id=str(uuid.uuid4()))

    def test_latest_report_is_actor_authorized_typed_and_bound_to_current_native_version(self):
        self.assertIsNone(self.report());run=self.produce();report=self.report(18)
        self.assertEqual((report.actor_id,report.project_id,report.native_id,report.version),(18,5,371,1))
        self.assertEqual(report.run_id,run['id']);self.assertEqual(report.verdict,'PASSED')
        for actor in [20,21,22]:self.assertIsNone(self.report(actor))
        self.assertIsNone(self.report(version=2))
        self.f.native.row['lockVersion']=2
        with self.assertRaises(NativeError):self.report()

    def test_latest_failed_or_tampered_report_never_falls_back_to_older_pass(self):
        self.produce();self.f.native.row['startDate']='2026-10-29';failed=self.produce('failed-newest')
        self.assertEqual(self.report().verdict,'FAILED')
        with self.store.connect() as db:
            body=json.loads(db.execute('select document from qa_test_runs where id=?',(failed['id'],)).fetchone()[0]);body['verdict']='PASSED'
            db.execute('update qa_test_runs set document=? where id=?',(json.dumps(body),failed['id']))
        with self.assertRaisesRegex(ValueError,'INTEGRITY_FAILED'):self.report()

    def test_local_supervisor_reports_verified_artifact_without_promoting_human_qa_or_writing(self):
        from gateway.native_qa_runs import latest_report
        run=self.produce();task,scope=self.task();lookups=[]
        def trusted(identifier,version):lookups.append((identifier,version));return latest_report(self.service,scope.actor_id,identifier,version)
        supervisor=Supervisor(qa_report=trusted);plan,result=supervisor.execute_task(task,scope,[self.f.native.row],actor_role='PM')
        self.assertEqual(lookups,[(371,1)]);self.assertIn('PASSED',result.summary);self.assertIn(run['artifact_sha256'],result.summary)
        self.assertIn('không phải human QA review',result.summary);self.assertFalse(result.model_used)
        self.assertEqual(self.f.native.writes,[])
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from qa_evidence').fetchone()[0],0)
            self.assertEqual(db.execute('select count(*) from qa_evidence_reviews').fetchone()[0],0)
            self.assertEqual(db.execute('select count(*) from proposals').fetchone()[0],0)

    def test_missing_forged_or_cross_actor_callback_result_cannot_claim_pass(self):
        from gateway.qa_agent import VerifiedTestReport,_REPORT_ISSUER
        task,scope=self.task()
        wrong=VerifiedTestReport(_REPORT_ISSUER,18,5,371,1,str(uuid.uuid4()),'PASSED','fixture',time.time(),'a'*64)
        for candidate in [None,{'runner_executed':True,'status':'PASSED'},wrong]:
            supervisor=Supervisor(qa_report=lambda *_:candidate)
            _,result=supervisor.execute_task(task,scope,[self.f.native.row],actor_role='PM')
            self.assertIn('NOT_RUN',result.summary);self.assertNotIn('Trạng thái kiểm thử:** PASSED',result.summary)

    def test_authenticated_service_queue_reaches_trusted_report_with_persisted_scope_and_no_model(self):
        artifact=self.produce()
        with patch.object(self.service,'start_dispatcher'),patch.object(self.service.gemini,'settings',side_effect=AssertionError('NO_PROVIDER_FOR_LOCAL_QA')):
            started=self.f.call(19,'start_ai_run',{'engine':'supervisor','prompt':'QA xác minh kết quả kiểm thử #371'},'supervisor-qa-service')
            claimed=self.store.claim_run();self.assertEqual(claimed['id'],started['id'])
            result=self.service.run_supervisor(19,claimed['id'])
        self.assertEqual(result['status'],'succeeded');self.assertIn(artifact['artifact_sha256'],result['text'])
        self.assertEqual(result['tools'],[]);self.assertFalse(result['model_used'])
        self.store.finish_run(19,claimed['id'],result,'done')
        persisted=self.store.agent_run(19,5,claimed['id'])
        self.assertEqual(persisted.state,'COMPLETED')
        self.assertEqual(result['agent_result']['trace_id'],persisted.trace_id)
        self.assertEqual(self.f.native.writes,[])
        with self.store.connect() as db:
            self.assertEqual(db.execute('select count(*) from gemini_call_receipts').fetchone()[0],0)
            self.assertEqual(db.execute('select count(*) from proposals').fetchone()[0],0)


if __name__=='__main__':unittest.main()

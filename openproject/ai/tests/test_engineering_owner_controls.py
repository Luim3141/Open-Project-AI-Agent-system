"""Owner P0 contract: isolated durable state, no provider or Native business writes."""
import json
import time
import tempfile
import concurrent.futures
import threading
import unittest
from unittest.mock import patch

import test_engineering_auto_mode as auto
import test_owner_project_authority as authority
from gateway import engineering
from gateway.store import canonical


class OwnerControlsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.service=auto.make_service(self.tmp.name)
        engineering.setup(self.service.store)

    def test_status_reuses_one_fresh_native_authority_within_the_request(self):
        with patch.object(self.service,'native_actor',wraps=self.service.native_actor) as identity:
            engineering.status(self.service,18)
        self.assertEqual(identity.call_count,1,'full status repeats remote identity for every internal panel')

    def test_async_sync_admission_authorizes_once_and_worker_must_recheck(self):
        fixture=authority.TestOwnerProjectAuthority();fixture.setUp();self.addCleanup(fixture.tearDown)
        service=engineering.scoped_service(fixture.service,6)
        with patch.object(service,'native_actor',wraps=service.native_actor) as identity:
            result=service.execute_actor(18,{'action':'engineering_github_sync','arguments':{},'idempotency_key':'single-auth'})['result']
            self.assertEqual(result['operation_state'],'QUEUED')
            self.assertEqual(identity.call_count,1,'duplicate Native authority checks delay the persisted ACK')
            from gateway.engineering_github_operations import process_pending
            with patch('gateway.engineering_github_sync.reconcile_github_with_openproject',return_value={'status':'SUCCESS','items':[]}):process_pending(service)
            self.assertEqual(identity.call_count,2,'worker failed to revalidate current Native authority')

    def test_command_has_durable_revision_and_readback(self):
        response = engineering.control(self.service, 18, 'PAUSED')
        self.assertTrue(response['accepted'])
        self.assertEqual(response['desired_state'], 'PAUSED')
        self.assertGreater(response['state_revision'], 0)
        with patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[]):
            status = engineering.status(self.service, 18)
        self.assertEqual(status['control']['last_command']['command_id'], response['command_id'])
        self.assertEqual(status['control']['state_revision'], response['state_revision'])

    def test_old_revision_rejected_without_changing_mode(self):
        first = engineering.control(self.service, 18, 'PAUSED')
        engineering.control(self.service, 18, 'OFF')
        result = engineering.control(self.service, 18, 'AUTO', expected_revision=first['state_revision'])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['reason_code'], 'ENGINEERING_STATE_REVISION_CONFLICT')
        self.assertEqual(result['mode'], 'OFF')

    def test_auto_empty_keeps_requested_mode_and_explains_idle(self):
        with patch('gateway.engineering_planning.definitions', return_value={}):
            result = engineering.control(self.service, 18, 'AUTO')
            with patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[]):
                status = engineering.status(self.service, 18)
        self.assertEqual(result['mode'], 'AUTO')
        self.assertEqual(status['control']['effective_state'], 'AUTO_IDLE')
        self.assertEqual(status['queue']['reason_code'], 'NO_ELIGIBLE_WORK')

    def test_status_does_not_generate_reports_and_telemetry_excludes_payload(self):
        admitted = engineering.admit(self.service, 20, {'native_id': 379, 'lock_version': 5,
            'unit': 'create-list-persistence-v1'}, 'telemetry')
        engineering.claim(self.service, 20)
        engineering.progress(self.service, 20, admitted['id'], 'DEVELOPING', {'agent': 'dev', 'private_prompt': 'SECRET_CANARY'})
        with self.service.store.connect() as db:
            db.execute("INSERT INTO gemini_call_receipts VALUES(?,?,?,?,?)", ('receipt', 'quota-project', 20, admitted['id'],
                canonical({'agent': 'dev', 'state': 'LIVE_SUCCESS', 'model': 'gemini-free', 'at': time.time(),
                           'prompt': 'SECRET_CANARY', 'error': 'secret=SECRET_CANARY'})))
        with patch('gateway.engineering_github_sync.fetch_pull_requests', return_value=[]), patch(
                'gateway.engineering_reporting.check_and_run_scheduled_reports') as generate:
            status = engineering.status(self.service, 18)
        generate.assert_not_called()
        telemetry = status['telemetry']
        self.assertNotIn('SECRET_CANARY', json.dumps(telemetry))
        self.assertEqual(telemetry['runs'][0]['agent'], 'dev')
        self.assertEqual(telemetry['events'][-1]['event_type'], 'AGENT_STARTED')
        self.assertEqual(telemetry['events'][-1]['sequence'], telemetry['cursor'])
        self.assertEqual(next(step for step in telemetry['runs'][0]['pipeline'] if step['agent']=='dev')['status'], 'RUNNING')
        self.assertEqual(status['control']['effective_state'], 'WORKER_STALE')

    def test_pause_executing_is_requested_until_worker_checkpoint(self):
        admitted = engineering.admit(self.service, 20, {'native_id': 379, 'lock_version': 5,
            'unit': 'create-list-persistence-v1'}, 'pause-active')
        engineering.claim(self.service, 20)
        result = engineering.control(self.service, 18, 'PAUSED')
        self.assertEqual(result['current_state'], 'PAUSE_REQUESTED')
        self.assertEqual(result['affected_run_id'], admitted['id'])

    def test_off_race_during_auto_source_read_cannot_reenable_scheduler(self):
        native, _ = self.service.native_actor(18)
        package = native.package
        def off_before_admission(identifier):
            engineering.control(self.service,18,'OFF')
            return package(identifier)
        native.package=off_before_admission
        original=self.service.native_actor
        self.service.native_actor=lambda actor:(native,original(actor)[1])
        result=engineering.control(self.service,18,'AUTO')
        self.assertEqual(result['mode'],'OFF')
        with self.service.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM ai_queue').fetchone()[0],0)

    def test_run_once_cannot_bypass_served_checkpoint_resume_guards(self):
        args={'native_id':379,'lock_version':5,'unit':'create-list-persistence-v1'}
        admitted=engineering.admit(self.service,20,args,'before-pause')
        engineering.claim(self.service,20)
        engineering.finish(self.service,20,admitted['id'],{'status':'paused','error':'ENGINEERING_PAUSED_CHECKPOINT_REQUIRED'})
        result=engineering.admit(self.service,18,args,'bypass-attempt')
        self.assertTrue(result['requires_reconciliation'])
        with self.service.store.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM ai_queue').fetchone()[0],'finished')

    def test_pipeline_requires_current_artifacts_for_pass(self):
        args={'native_id':379,'lock_version':5,'unit':'create-list-persistence-v1'}
        admitted=engineering.admit(self.service,20,args,'pipeline-evidence')
        engineering.claim(self.service,20)
        review={'revision':'b'*64,'verdict':'PASS','findings':[],'qa':{'status':'PASS','exit_code':0}}
        result={'status':'succeeded','head_sha':'a'*40,'pr_url':'https://github.com/Luim3141/mini-task-manager/pull/1',
            'test_evidence':{'exit_code':0,'log_sha256':'c'*64},'review_evidence':review,
            'native_readback':{'project_id':6,'child_id':380,'child_version':2},
            'knowledge_readback':{'project_id':6,'child_id':380,'retrieval_count':1,'references':[{'native_id':380,'citation':'/work_packages/380'}]}}
        engineering.finish(self.service,20,admitted['id'],result)
        with patch('gateway.engineering_github_sync.fetch_pull_requests',return_value=[]):
            observed=engineering.status(self.service,18)['telemetry']['runs'][0]
        pipeline={step['agent']:step['status'] for step in observed['pipeline']}
        self.assertEqual(pipeline['reviewer'],'PASS')
        self.assertEqual(pipeline['qa'],'PASS')
        self.assertEqual(pipeline['github'],'PASS')
        self.assertEqual(pipeline['native'],'PASS')
        self.assertEqual(pipeline['rag'],'PASS')
        self.assertEqual(pipeline['reports'],'UNKNOWN')
        self.assertEqual(observed['review']['kind'],'INTERNAL')
        self.assertEqual(observed['artifacts']['diff_sha256'],'b'*64)

    def test_auto_admission_does_not_fetch_dashboard_sources(self):
        with patch('gateway.engineering.status',side_effect=AssertionError('dashboard network reads')):
            result=engineering.control(self.service,18,'AUTO')
        self.assertTrue(result['scheduled']['scheduled'])

    def test_all_web_mutations_have_request_correlated_durable_receipts(self):
        fixture=authority.TestOwnerProjectAuthority()
        fixture.setUp(); self.addCleanup(fixture.tearDown)
        service=engineering.scoped_service(fixture.service,6)
        operations=[('engineering_github_sync',{},'gateway.engineering.github_sync'),
            ('engineering_plan',{'native_id':379,'lock_version':1},'gateway.engineering.admit'),
            ('engineering_report_generate',{},'gateway.engineering_reporting.generate_report'),
            ('engineering_report_schedule_update',{},'gateway.engineering_reporting.update_schedule'),
            ('engineering_notifications_dismiss',{'id':'notification'},'gateway.engineering_reporting.dismiss_notification')]
        for index,(action,args,target) in enumerate(operations):
            request_id='request-'+str(index)
            with self.subTest(action=action),patch(target,return_value={'status':'SUCCESS'}):
                result=service.execute_actor(18,{'action':action,'arguments':args,'idempotency_key':request_id})['result']
                self.assertEqual(result['request_id'],request_id)
                with fixture.store.connect() as db:
                    receipt=json.loads(db.execute('SELECT document FROM engineering_owner_commands ORDER BY sequence DESC LIMIT 1').fetchone()[0])
                self.assertEqual(receipt['request_id'],request_id)

    def test_old_auto_request_replay_does_not_override_new_off(self):
        fixture=authority.TestOwnerProjectAuthority(); fixture.setUp(); self.addCleanup(fixture.tearDown)
        service=engineering.scoped_service(fixture.service,6)
        command={'action':'engineering_control','arguments':{'mode':'AUTO'},'idempotency_key':'original-auto'}
        with patch('gateway.engineering_auto.schedule_next_auto_unit',return_value={'scheduled':False,'reason':'NO_ELIGIBLE_WORK'}):
            original=service.execute_actor(18,command)
            service.execute_actor(18,{'action':'engineering_control','arguments':{'mode':'OFF'},'idempotency_key':'new-off'})
            repeated=service.execute_actor(18,command)
        self.assertEqual(repeated,original)
        with fixture.store.connect() as db:
            self.assertEqual(db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],'OFF')
        with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_CONFLICT'):
            service.execute_actor(18,{**command,'arguments':{'mode':'PAUSED'}})

    def test_concurrent_report_same_request_reserves_one_effect_and_caches_result(self):
        fixture=authority.TestOwnerProjectAuthority(); fixture.setUp(); self.addCleanup(fixture.tearDown)
        service=engineering.scoped_service(fixture.service,6)
        entered=threading.Event(); release=threading.Event()
        def generate(*args):
            entered.set(); release.wait(5)
            return {'id':'persisted-report'}
        command={'action':'engineering_report_generate','arguments':{},'idempotency_key':'one-report'}
        with patch('gateway.engineering_reporting.generate_report',side_effect=generate) as report:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(service.execute_actor,18,command)
                self.assertTrue(entered.wait(5))
                try:
                    with self.assertRaisesRegex(ValueError,'PENDING_RECONCILE_FIRST'):
                        service.execute_actor(18,command)
                finally:
                    release.set()
                original=first.result(timeout=5)
            repeated=service.execute_actor(18,command)
        self.assertEqual(report.call_count,1)
        self.assertEqual(repeated,original)


if __name__ == '__main__':
    unittest.main()

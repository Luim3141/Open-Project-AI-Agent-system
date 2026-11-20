import concurrent.futures
import copy
import hashlib
import hmac
import json
import time
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from gateway import engineering
from gateway.store import Store,digest
from gateway.service import Service
from gateway.bridge import verify_assertion


class NativeFixture:
    def call(self, path):
        if path != '/api/v3/projects/6':
            raise AssertionError(path)
        return {'id':6,'identifier':'ai-dev-demo','active':True}

    def package(self, identifier):
        if identifier != 379:
            raise PermissionError()
        return {'id':379,'lockVersion':0,'description':{'raw':'Create/list with SQLite persistence'},
            '_links':{'project':{'href':'/api/v3/projects/6'}}}


class EngineeringTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name))
        self.service=SimpleNamespace(store=self.store,config={'project_id':6,'engineering':{'enabled':True}},
            native_actor=lambda actor:(NativeFixture(),{'user_id':actor,'role':'PM' if actor==20 else 'BA'}))
        self.args={'native_id':379,'lock_version':0,'unit':engineering.UNIT}

    def test_two_sources_claim_one_unit_and_legacy_worker_cannot_execute_it(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda key:engineering.admit(self.service,20,self.args,key),['event-a','event-b']))
        self.assertEqual(results[0]['id'],results[1]['id'])
        self.assertIsNone(self.store.claim_run())
        claim=engineering.claim(self.service,20)
        self.assertEqual(claim['id'],results[0]['id'])
        self.assertIsNone(engineering.claim(self.service,20))
        engineering.finish(self.service,20,claim['id'],{'status':'blocked','text':'test checkpoint'})
        self.assertEqual(engineering.status(self.service,20)['mode'],'OFF')
        self.assertEqual(self.store.agent_run(20,6,claim['id']).state,'FAILED')

    def test_source_stale_non_pm_other_project_and_wrong_unit_are_denied(self):
        for actor,args in [(19,self.args),(20,{**self.args,'lock_version':1}),(20,{**self.args,'native_id':5})]:
            with self.assertRaises((PermissionError,ValueError)):
                engineering.admit(self.service,actor,args,'denied')
        self.service.config['project_id']=5
        with self.assertRaises(PermissionError):engineering.admit(self.service,20,self.args,'denied')
        with self.store.connect() as db:self.assertEqual(db.execute('select count(*) from ai_runs').fetchone()[0],0)

    def test_pause_prevents_claim_and_incomplete_proof_cannot_complete(self):
        receipt=engineering.admit(self.service,20,self.args,'pause')
        engineering.control(self.service,20,'PAUSED')
        self.assertIsNone(engineering.claim(self.service,20))
        self.assertEqual(self.store.agent_run(20,6,receipt['id']).state,'QUEUED')
        with self.assertRaises(ValueError):
            engineering.finish(self.service,20,receipt['id'],{'status':'succeeded','text':'model says PASS'})
        resumed=engineering.admit(self.service,20,self.args,'resume-paused')
        self.assertEqual(resumed['id'],receipt['id']);self.assertTrue(resumed['resumed_before_execution'])
        self.assertEqual(engineering.claim(self.service,20)['id'],receipt['id'])

    def test_cancel_before_claim_can_reactivate_but_started_job_cannot_and_pause_survives_finish(self):
        identifier=engineering.admit(self.service,20,self.args,'cancel')['id']
        engineering.control(self.service,20,'OFF')
        self.assertTrue(engineering.admit(self.service,20,self.args,'restart')['resumed_before_execution'])
        engineering.claim(self.service,20)
        engineering.control(self.service,20,'PAUSED')
        self.assertEqual(engineering.finish(self.service,20,identifier,{'status':'blocked'})['mode'],'PAUSED')
        self.assertNotIn('resumed_before_execution',engineering.admit(self.service,20,self.args,'not-replay'))

    def test_finished_lease_recovery_cannot_leave_mode_running_forever(self):
        identifier=engineering.admit(self.service,20,self.args,'lease')['id'];engineering.claim(self.service,20)
        self.store.finish_run(20,identifier,{'status':'failed','error':'WORKER_LOST'},'failed_or_unknown')
        self.assertIsNone(engineering.claim(self.service,20))
        self.assertEqual(engineering.status(self.service,20)['mode'],'OFF')

    def test_project_scope_policy_is_opt_in_and_never_falls_back_to_main(self):
        base=SimpleNamespace(config={'project_id':5},store=self.store)
        self.assertIs(engineering.scoped_service(base,5),base)
        for project in [6,7,'6',True]:
            with self.assertRaises(PermissionError):engineering.scoped_service(base,project)

    def test_second_unit_requires_verified_first_head_and_legacy_wait_does_not_rewrite_engineering_queue(self):
        second={**self.args,'unit':engineering.EXPANSION}
        with self.assertRaisesRegex(ValueError,'DEPENDENCY_NOT_VERIFIED'):
            engineering.admit(self.service,20,second,'premature')
        first=engineering.admit(self.service,20,self.args,'first')['id'];engineering.claim(self.service,20)
        proof={k:'fixture proof' for k in ['test_evidence','review_evidence','pr_url','native_readback','knowledge_readback']}
        engineering.finish(self.service,20,first,{'status':'succeeded','head_sha':'a'*40,**proof})
        next_run=engineering.admit(self.service,20,second,'second')['id']
        self.assertNotEqual(first,next_run)
        self.store.wait_queued({'queue_state':'BLOCKED_KEY_OR_MODEL','retry_at':None})
        self.assertEqual(self.store.agent_run(20,6,next_run).state,'QUEUED')
        self.assertEqual(engineering.project_for_run(self.service,20,next_run),6)
        self.assertIsNone(engineering.project_for_run(self.service,19,next_run))
        claim=engineering.claim(self.service,20);self.assertEqual(claim['base_sha'],'a'*40)
        engineering.progress(self.service,20,next_run,'DEVELOPING',{'agent':'dev'})
        trace=self.store.agent_trace_page(20,6,next_run)
        self.assertEqual(trace['items'][-1]['action'],'engineering_stage')

    def test_rest_trace_used_by_wf04_resolves_owned_project6_and_rechecks_membership(self):
        from starlette.testclient import TestClient
        from gateway.app import create_app
        run=engineering.admit(self.service,20,self.args,'rest')['id'];engineering.claim(self.service,20)
        engineering.progress(self.service,20,run,'DEVELOPING',{'agent':'dev'})
        roles={20:'PM',19:'BA'}
        def factory(url,credential,project):
            native=NativeFixture()
            native.identity=lambda actor:{'user_id':actor,'role':roles[actor] if project==6 else 'BA'}
            return native
        config={'project_id':5,'gateway_mode':'native','users':{'20':'BA','19':'BA'},'openproject_url':'http://127.0.0.1',
            'hosts':['testserver'],'max_users':20,'engineering':{'enabled':True,'actors':{'20':'PM'}}}
        service=Service(self.store,config,Path(self.tmp.name)/'workspaces',factory)
        client=TestClient(create_app(self.store.root,service));self.addCleanup(client.close)
        tokens={actor:self.store.issue_token(actor,'BA','fixture-native-'+str(actor)) for actor in roles}
        url='/api/v1/agent-runs/'+run+'/trace'
        response=client.get(url,headers={'Authorization':'Bearer '+tokens[20]})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['result']['items'][-1]['project_id'],6)
        self.assertEqual(client.get(url,headers={'Authorization':'Bearer '+tokens[19]}).status_code,403)
        roles[20]='BA'
        denied=client.get(url,headers={'Authorization':'Bearer '+tokens[20]})
        self.assertEqual(denied.status_code,403)
        self.assertNotIn('engineering_stage',denied.text)

    def test_rpm_recovery_preserves_actual_rework_feedback_and_same_unit(self):
        run=engineering.admit(self.service,20,self.args,'rpm')['id'];engineering.claim(self.service,20)
        engineering.finish(self.service,20,run,{'status':'blocked','error':'GEMINI_LOCAL_RPM_EXHAUSTED'})
        with self.store.connect() as db:sha=digest(db.execute('SELECT result FROM ai_runs WHERE id=?',(run,)).fetchone()[0])
        receipt=engineering.resume_reconciled(self.service,20,run,sha,rework_feedback='Actual acceptance failed: literal wildcard search')
        claim=engineering.claim(self.service,20)
        self.assertEqual(receipt['id'],run)
        self.assertEqual(claim['resume_stage'],'REWORK')
        self.assertIn('literal wildcard',claim['rework_feedback'])

    def test_usage_ids_are_session_scoped_so_rework_does_not_overwrite_previous_attempt(self):
        from gateway.engineering_operator import usage_receipt_id
        run='00000000-0000-4000-8000-000000000001'
        first='00000000-0000-4000-8000-000000000002';second='00000000-0000-4000-8000-000000000003'
        self.assertEqual(usage_receipt_id(run,'dev-1',0,first),usage_receipt_id(run,'dev-1',0,first))
        self.assertNotEqual(usage_receipt_id(run,'dev-1',0,first),usage_receipt_id(run,'dev-1',0,second))

    def test_project_specific_role_does_not_change_main_and_scope_cannot_enable_generic_writes(self):
        config={'project_id':5,'gateway_mode':'native','users':{'20':'BA'},'engineering':{'enabled':True,'actors':{'20':'PM'}}}
        base=Service(self.store,config,Path(self.tmp.name)/'workspaces')
        scoped=engineering.scoped_service(base,6)
        self.assertEqual(scoped.config['users'],{'20':'PM'})
        self.assertEqual(base.config['users'],{'20':'BA'})
        for action in ['create_work_package','start_ai_run','write_code','transition']:
            with self.assertRaisesRegex(PermissionError,'ENGINEERING_CAPABILITY_REQUIRED'):
                scoped.execute_actor(20,{'action':action,'arguments':{}})

    def test_signed_bridge_requires_opt_in_correct_project_actor_and_single_use_nonce(self):
        (self.store.root/'ui.key').write_bytes(b'fixture-ui-key-not-a-credential')
        config={'project_id':5,'users':{'18':'AI_SYSTEM_OWNER'},'engineering':{'enabled':True,'actors':{'20':'PM'}}}
        def signed(project=6,actor=20,nonce='unique-fixture-nonce'):
            body=json.dumps({'actor':actor,'project':project,'audience':'qldapm-ai-ui','at':time.time(),
                'nonce':nonce,'operation':'command','command':{'action':'engineering_status','arguments':{}}}).encode()
            return body,hmac.new((self.store.root/'ui.key').read_bytes(),body,hashlib.sha256).hexdigest()
        body,signature=signed()
        self.assertEqual(verify_assertion(self.store,config,body,signature)['project'],6)
        with self.assertRaises(PermissionError):verify_assertion(self.store,config,body,signature)
        for project,actor in [(5,20),(6,18),(7,20),(True,20)]:
            with self.assertRaises(PermissionError):verify_assertion(self.store,config,*signed(project,actor,'denied-'+str(project)+str(actor)))
        config['engineering']['enabled']=False
        with self.assertRaises(PermissionError):verify_assertion(self.store,config,*signed(nonce='disabled-fixture'))

    def test_finished_or_unclaimed_run_cannot_accept_late_success(self):
        run=engineering.admit(self.service,20,self.args,'late')['id']
        proof={k:'not-proof' for k in ['head_sha','test_evidence','review_evidence','pr_url','native_readback','knowledge_readback']}
        with self.assertRaisesRegex(ValueError,'ENGINEERING_RUN_NOT_CLAIMED'):
            engineering.finish(self.service,20,run,{'status':'succeeded',**proof})
        engineering.claim(self.service,20)
        engineering.finish(self.service,20,run,{'status':'blocked'})
        with self.assertRaisesRegex(ValueError,'ENGINEERING_RUN_NOT_CLAIMED'):
            engineering.finish(self.service,20,run,{'status':'succeeded',**proof})

    def test_project6_native_artifact_links_index_as_opaque_references_without_weakening_main_classifier(self):
        from gateway.openproject_loader import actor_work_package_document,work_package_to_document
        from gateway.knowledge_classifier import SecurityValidationError,classify_document,KnowledgeDocType
        item=NativeFixture().package(379)
        item.update(subject='Mini Task Manager',description={'raw':'SQLite persistence https://github.com/Luim3141/mini-task-manager'})
        document=actor_work_package_document(item,6,20,'PM',[])
        self.assertIn('SQLite persistence',document.content)
        self.assertIn('[Native-reference:',document.content)
        self.assertNotIn('github.com',document.content)
        self.assertEqual(document.project_id,'6')
        self.assertIn('[Native-reference:',work_package_to_document(item,'6').content)
        with self.assertRaises(SecurityValidationError):actor_work_package_document(item,5,20,'BA',[])
        with self.assertRaises(SecurityValidationError):classify_document(KnowledgeDocType.WORK_PACKAGE,'6','fixture','x','https://github.com/evil')

    def test_owner_authorized_in_project6_and_shares_history_with_pm20_without_duplication(self):
        # Setup actors: 20 is PM, 18 is AI_SYSTEM_OWNER, 19 is Project Admin / unauthorized for engineering
        roles = {20: 'PM', 18: 'AI_SYSTEM_OWNER', 19: 'Project admin'}
        def native_actor_fixture(actor):
            return NativeFixture(), {'user_id': actor, 'role': roles.get(actor, 'UNKNOWN')}
        self.service.native_actor = native_actor_fixture
        self.service.config['engineering']['actors'] = {'20': 'PM', '18': 'AI_SYSTEM_OWNER'}

        # Scoped service must accept AI_SYSTEM_OWNER in actors policy
        base = Service(self.store, {'project_id': 5, 'engineering': {'enabled': True, 'actors': {'20': 'PM', '18': 'AI_SYSTEM_OWNER'}}}, Path(self.tmp.name)/'workspaces')
        scoped = engineering.scoped_service(base, 6)
        self.assertIn('18', scoped.config['users'])

        # PM20 admits a unit
        pm_run = engineering.admit(self.service, 20, self.args, 'pm-admit-key')
        run_id = pm_run['id']

        # Owner 18 queries status: must see PM20's run, backlog and delivery worker state
        owner_status = engineering.status(self.service, 18)
        self.assertEqual(len(owner_status['runs']), 1)
        self.assertEqual(owner_status['runs'][0]['id'], run_id)
        self.assertEqual(len(owner_status['backlog']), 2)

        # Owner 18 admits the same unit: must deduplicate to the same run_id, no duplicate job
        owner_admit = engineering.admit(self.service, 18, self.args, 'owner-admit-key')
        self.assertEqual(owner_admit['id'], run_id)
        self.assertTrue(owner_admit.get('deduplicated'))

        # Unauthorized actor 19 is denied
        with self.assertRaises(PermissionError):
            engineering.authorized(self.service, 19)
        with self.assertRaises(PermissionError):
            engineering.status(self.service, 19)
        with self.assertRaises(PermissionError):
            engineering.admit(self.service, 19, self.args, 'unauthorized-key')

        # Project 5 unchanged: scoped_service to other projects denied
        with self.assertRaises(PermissionError):
            engineering.scoped_service(self.service, 5)

    def test_reconciled_terminal_failure_resumes_same_unit_with_bounded_repairs_and_unknown_cannot_replay(self):
        run=engineering.admit(self.service,20,self.args,'repair')['id']
        engineering.claim(self.service,20)
        engineering.finish(self.service,20,run,{'status':'blocked','error':'OPENCLAW_OUTCOME_UNKNOWN'})
        def result_hash():
            with self.store.connect() as db:return digest(db.execute('SELECT result FROM ai_runs WHERE id=?',(run,)).fetchone()[0])
        artifact={'diff_sha256':'c'*64,'test_log_sha256':'d'*64,'terminal_run_id':'00000000-0000-4000-8000-000000000001'}
        for proof in [None,artifact]:
            with self.assertRaisesRegex(ValueError,'RECONCILIATION_UNSUPPORTED'):
                engineering.resume_reconciled(self.service,20,run,result_hash(),proof)
        with self.store.connect() as db:db.execute('UPDATE ai_runs SET result=? WHERE id=?',(json.dumps({'status':'blocked','error':'OPENCLAW_STEP_NOT_COMPLETED'}),run))
        with self.assertRaisesRegex(ValueError,'RECONCILIATION_CHANGED'):
            engineering.resume_reconciled(self.service,20,run,'wrong-hash')
        self.assertEqual(engineering.resume_reconciled(self.service,20,run,result_hash())['attempt'],1)
        self.assertEqual(engineering.admit(self.service,20,self.args,'another-trigger')['id'],run)
        claim=engineering.claim(self.service,20);self.assertEqual(claim['attempt'],1)
        engineering.finish(self.service,20,run,{'status':'blocked','error':'OPENCLAW_STEP_NOT_COMPLETED'})
        self.assertEqual(engineering.resume_reconciled(self.service,20,run,result_hash())['attempt'],2)
        engineering.claim(self.service,20)
        engineering.finish(self.service,20,run,{'status':'blocked','error':'OPENCLAW_STEP_NOT_COMPLETED'})
        with self.assertRaisesRegex(ValueError,'RECONCILIATION_UNSUPPORTED'):
            engineering.resume_reconciled(self.service,20,run,result_hash())
        self.assertEqual(engineering.resume_reconciled(self.service,20,run,result_hash(),artifact)['attempt'],3)
        engineering.claim(self.service,20)
        engineering.finish(self.service,20,run,{'status':'blocked','error':'OPENCLAW_STEP_NOT_COMPLETED'})
        with self.assertRaisesRegex(ValueError,'ARTIFACT_RECONCILIATION_INVALID'):
            engineering.resume_reconciled(self.service,20,run,result_hash(),artifact)


if __name__=='__main__':unittest.main()

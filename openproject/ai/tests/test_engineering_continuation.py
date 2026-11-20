import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from gateway import engineering
from gateway import engineering_lifecycle as lifecycle
from gateway.engineering_planning import PLANNING,DevelopmentPlan,validate_plan
from gateway.store import Store,canonical


class Native:
    def call(self,path):return {'identifier':'ai-dev-demo','active':True}
    def package(self,identifier):return {'id':identifier,'lockVersion':0,'subject':'Mini Task Manager','description':{'raw':'CRUD and reliable web UI'}}


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.native=Native()
        self.service=SimpleNamespace(store=self.store,config={'project_id':6,'engineering':{'enabled':True}},native_actor=lambda actor:(self.native,{'user_id':actor,'role':'PM' if actor==20 else 'BA'}))
        self.args={'native_id':379,'lock_version':0,'unit':engineering.UNIT}

    def test_cancel_is_distinct_and_resume_preserves_same_unit_and_completed_stage(self):
        run=engineering.admit(self.service,20,self.args,'start')['id'];engineering.claim(self.service,20)
        checkpoint=lifecycle.save(self.service,20,run,{'stage':'review-0','completed_steps':['context','prepare','dev-0'],'terminal_known':True,'resumable':True,'revision':'a'*64,'session_id':None,'error':None})
        cancelled=lifecycle.cancel(self.service,20,run)
        self.assertEqual(cancelled['state'],'cancelling');self.assertTrue(lifecycle.signal(self.store,20,run)['cancel_requested'])
        engineering.finish(self.service,20,run,{'status':'cancelled','error':'ENGINEERING_CANCELLED'})
        receipt=lifecycle.resume(self.service,20,run,checkpoint['version'])
        self.assertEqual(receipt['id'],run);self.assertEqual(engineering.claim(self.service,20)['recovery_count'],1)
        self.assertEqual(lifecycle.load(self.store,run)['completed_steps'],['context','prepare','dev-0'])

    def test_resume_denies_unknown_checkpoint_changed_revision_and_pending_native_writes(self):
        run=engineering.admit(self.service,20,self.args,'unknown')['id'];engineering.claim(self.service,20)
        saved=lifecycle.save(self.service,20,run,{'stage':'publish','completed_steps':[],'terminal_known':False,'resumable':True,'revision':None,'session_id':None,'error':'UNKNOWN'})
        engineering.finish(self.service,20,run,{'status':'blocked'})
        with self.assertRaisesRegex(ValueError,'RECONCILIATION_REQUIRED'):lifecycle.resume(self.service,20,run,saved['version'])
        with self.store.connect() as db:db.execute('UPDATE engineering_checkpoints SET document=? WHERE run_id=?',(canonical({**saved,'terminal_known':True,'resumable':True}),run))
        self.store.begin(20,'engineering-'+run+'-child',{'action':'engineering_native_child'})
        with self.assertRaisesRegex(ValueError,'NATIVE_OUTCOME'):lifecycle.resume(self.service,20,run,saved['version'])

    def test_expired_worker_lease_invalidates_prior_safe_checkpoint(self):
        run=engineering.admit(self.service,20,self.args,'expired-lease')['id'];engineering.claim(self.service,20)
        saved=lifecycle.save(self.service,20,run,{'stage':'prepare','completed_steps':['context'],
            'terminal_known':True,'resumable':True,'revision':None,'session_id':None,'error':None})
        with self.store.connect() as db:db.execute('UPDATE ai_queue SET lease_until=0 WHERE id=?',(run,))
        self.assertIsNone(self.store.claim_run(openclaw_only=True))
        checkpoint=lifecycle.load(self.store,run)
        self.assertGreater(checkpoint['version'],saved['version'])
        self.assertFalse(checkpoint['terminal_known'])
        self.assertFalse(checkpoint['resumable'])
        with self.assertRaisesRegex(ValueError,'RECONCILIATION_REQUIRED'):
            lifecycle.resume(self.service,20,run,checkpoint['version'])

    def test_duplicate_resume_does_not_spend_recovery_budget_twice(self):
        run=engineering.admit(self.service,20,self.args,'resume-idempotency')['id'];engineering.claim(self.service,20)
        saved=lifecycle.save(self.service,20,run,{'stage':'prepare','completed_steps':['context'],
            'terminal_known':True,'resumable':True,'revision':None,'session_id':None,'error':None})
        engineering.finish(self.service,20,run,{'status':'paused','error':'ENGINEERING_PAUSED_CHECKPOINT_REQUIRED'})
        first=lifecycle.resume(self.service,20,run,saved['version'])
        second=lifecycle.resume(self.service,20,run,saved['version'])
        self.assertTrue(second['deduplicated'])
        self.assertEqual(second['recovery_count'],first['recovery_count'])
        self.assertEqual(engineering.claim(self.service,20)['id'],run)
        self.assertIsNone(engineering.claim(self.service,20))

    def test_paused_queued_resume_does_not_spend_budget_without_execution(self):
        run=engineering.admit(self.service,20,self.args,'paused-queued')['id'];engineering.claim(self.service,20)
        saved=lifecycle.save(self.service,20,run,{'stage':'prepare','completed_steps':['context'],
            'terminal_known':True,'resumable':True,'revision':None,'session_id':None,'error':None})
        engineering.finish(self.service,20,run,{'status':'paused','error':'ENGINEERING_PAUSED_CHECKPOINT_REQUIRED'})
        first=lifecycle.resume(self.service,20,run,saved['version'])
        engineering.control(self.service,20,'PAUSED')
        with self.store.connect() as db:
            payload=json.loads(db.execute('SELECT payload FROM ai_queue WHERE id=?',(run,)).fetchone()[0])
            payload['deadline']=1
            db.execute('UPDATE ai_queue SET payload=? WHERE id=?',(canonical(payload),run))
        second=lifecycle.resume(self.service,20,run,saved['version'])
        self.assertEqual(second['recovery_count'],first['recovery_count'])
        self.assertEqual(second['mode'],'RUN_ONCE')
        with self.store.connect() as db:
            self.assertGreater(json.loads(db.execute('SELECT payload FROM ai_queue WHERE id=?',(run,)).fetchone()[0])['deadline'],time.time())
            self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE action='engineering_resume' AND target=? AND outcome='queued-unpaused'",(run,)).fetchone()[0],1)
        self.assertEqual(engineering.claim(self.service,20)['id'],run)

    def test_old_created_time_does_not_expire_an_active_worker_with_valid_lease(self):
        run=engineering.admit(self.service,20,self.args,'long-active')['id'];engineering.claim(self.service,20)
        with self.store.connect() as db:
            db.execute('UPDATE ai_queue SET created=?,lease_until=? WHERE id=?',(time.time()-3600,time.time()+600,run))
        new={**self.args,'unit':PLANNING,'feedback':'A separate fixture request'}
        with self.assertRaisesRegex(ValueError,'ENGINEERING_UNIT_ALREADY_ACTIVE'):
            engineering.admit(self.service,20,new,'new-while-active')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM ai_queue WHERE id=?',(run,)).fetchone()[0],'executing')
            self.assertEqual(db.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0],1)

    def test_planning_feedback_deduplicates_on_requirement_and_is_queued_without_model_call(self):
        args={**self.args,'unit':PLANNING,'feedback':'Show network errors and preserve filter state'}
        first=engineering.admit(self.service,20,args,'plan-a');second=engineering.admit(self.service,20,args,'plan-b')
        self.assertEqual(first['id'],second['id'])
        claim=engineering.claim(self.service,20)
        self.assertEqual(claim['kind'],'planning');self.assertIn('network errors',claim['definition']['feedback'])
        with self.assertRaises(PermissionError):engineering.admit(self.service,19,args,'plan-denied')

    def test_plan_cannot_invent_units_or_cyclic_dependencies(self):
        def plan(assignments):return DevelopmentPlan(summary='Plan',assignments=assignments,blockers=[],next_action='Implement')
        allowed={'a':{'dependencies':[]},'b':{'dependencies':['a']}}
        valid=plan([{'unit':'a','priority':1,'objective':'A','dependencies':[]},{'unit':'b','priority':2,'objective':'B','dependencies':['a']}])
        self.assertIs(validate_plan(valid,allowed),valid)
        invalid=valid.model_copy(deep=True);invalid.assignments.reverse()
        with self.assertRaisesRegex(ValueError,'DEPENDENCY'):validate_plan(invalid,allowed)

    def test_delivery_journal_skips_completed_steps_after_host_restart(self):
        from automation.engineering_delivery import DeliveryJournal
        from automation.engineering_worker import save
        calls=[]
        worker=SimpleNamespace(EVIDENCE=Path(self.tmp.name)/'artifacts',save=save,operator=lambda op,**kw:({'mode':'RUN_ONCE','queue_state':'executing','cancel_requested':False,'deadline':9999999999} if op=='signal' else {}))
        claim={'id':'00000000-0000-4000-8000-000000000001'}
        first=DeliveryJournal(worker,claim)
        first.step('published',lambda:calls.append('write') or {'native_id':381})
        recovered=DeliveryJournal(worker,claim)
        self.assertEqual(recovered.step('published',lambda:calls.append('duplicate')),{'native_id':381})
        self.assertEqual(calls,['write'])

    def test_role_bootstrap_evidence_rejects_advertised_but_unloaded_persona(self):
        from automation.engineering_bootstrap import verify_report
        report={'injectedWorkspaceFiles':[],'skills':{'entries':[{'name':'engineering-development'}]}}
        doc={'result':{'meta':{'systemPromptReport':report}}}
        with self.assertRaisesRegex(RuntimeError,'NOT_LOADED'):verify_report(doc,'dev')
        report['injectedWorkspaceFiles']=[{'name':v,'injectedChars':80,'missing':False,'truncated':False} for v in ['AGENTS.md','SOUL.md']]
        self.assertIn('engineering-development',verify_report(doc,'dev')['skills_loaded'])

    def test_worker_heartbeat_is_durable_without_admission_or_model_call(self):
        lifecycle.heartbeat(self.store,'00000000-0000-4000-8000-000000000001')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM engineering_worker_state').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM ai_queue').fetchone()[0],0)

    def test_native_recovery_preserves_rejected_receipt_and_reuses_known_success(self):
        from gateway.engineering_operator import native_once
        from gateway.native import NativeError
        calls=[]
        def native(path,method,payload):
            calls.append(payload)
            if len(calls)==1:raise NativeError(422,'OPENPROJECT_422')
            return {'id':381}
        client=SimpleNamespace(call=native)
        with self.assertRaisesRegex(ValueError,'REJECTED_422'):native_once(self.service,client,'run','child','/api/v3/work_packages','POST',{'subject':'before'})
        self.assertEqual(native_once(self.service,client,'run','child','/api/v3/work_packages','POST',{'subject':'fixed'}),{'id':381})
        self.assertEqual(native_once(self.service,client,'run','child','/api/v3/work_packages','POST',{'subject':'fixed'}),{'id':381})
        self.assertEqual(len(calls),2)

    def test_new_feedback_uses_latest_verified_delivery_and_blocks_parallel_stale_work(self):
        from gateway.engineering_planning import feedback_base_unit
        from gateway.engineering_units import UNITS,EXPANSION
        known={**UNITS,'feedback-old':{'base_unit':EXPANSION}}
        delivered={EXPANSION:{'head_sha':'a'*40},'feedback-old':{'head_sha':'b'*40}}
        self.assertEqual(feedback_base_unit(known,delivered,'feedback-new'),'feedback-old')
        with self.assertRaisesRegex(ValueError,'PENDING_FEEDBACK'):
            feedback_base_unit(known,{EXPANSION:delivered[EXPANSION]},'feedback-new')

    def test_incomplete_planning_handoff_cannot_dispatch_defined_feedback_unit(self):
        lifecycle.setup(self.store)
        definition={'native_id':382,'kind':'development','plan_id':'unpublished','title':'UI feedback','base_unit':None,'base_branch':'main','acceptance_file':'test_crud_web.py','acceptance':{}}
        with self.store.connect() as db:db.execute('INSERT INTO engineering_unit_definitions VALUES(?,?,?,?)',('feedback-fixture',20,382,canonical(definition)))
        with self.assertRaisesRegex(ValueError,'PLAN_HANDOFF_REQUIRED'):
            engineering.admit(self.service,20,{'native_id':382,'lock_version':0,'unit':'feedback-fixture'},'not-before-plan')

    def test_recovered_finish_keeps_both_failure_and_success_events(self):
        run=engineering.admit(self.service,20,self.args,'events')['id'];engineering.claim(self.service,20)
        saved=lifecycle.save(self.service,20,run,{'stage':'review-0','completed_steps':['dev-0'],'terminal_known':True,'resumable':True,'revision':'a'*64,'session_id':None,'error':None})
        engineering.finish(self.service,20,run,{'status':'blocked'})
        lifecycle.resume(self.service,20,run,saved['version']);engineering.claim(self.service,20)
        proof={k:'fixture' for k in ['head_sha','test_evidence','review_evidence','pr_url','native_readback','knowledge_readback']}
        engineering.finish(self.service,20,run,{'status':'succeeded',**proof})
        events,_=self.store.execution_records(20,6,run)
        kinds=[e['event_type'] for e in events]
        self.assertIn('RUN_FAILED',kinds);self.assertIn('RUN_COMPLETED',kinds);self.assertIn('RETRY_SCHEDULED',kinds)

    def test_engineering_projection_uses_actual_role_receipts_in_existing_monitor_schema(self):
        from gateway.engineering_monitor import project
        identifier=engineering.admit(self.service,20,self.args,'monitor')['id'];contract=engineering.claim(self.service,20)
        result={'status':'succeeded','text':'fixture delivery','files_changed':['app.py'],'head_sha':'a'*40,'pr_url':'https://github.com/Luim3141/mini-task-manager/pull/1','test_evidence':{'exit_code':0},'review_evidence':{'verdict':'PASS','qa':{'status':'PASS'}},'native_readback':{'child_id':382},'knowledge_readback':{'project_id':6}}
        engineering.finish(self.service,20,identifier,result)
        run=self.store.agent_run(20,6,identifier);task=self.store.agent_task(20,6,run.task_id)
        receipts=[{'id':role,'agent':role,'phase':'generateContent','state':'LIVE_SUCCESS','model':'fixture-model','usage':{'totalTokenCount':5},'at':1.0,'completed_at':2.0} for role in ['dev','reviewer','qa']]
        view=project(self.service,{'user_id':20,'role':'PM'},self.store.run(20,identifier),task,run,contract,receipts,[])
        self.assertEqual([n['agent'] for n in view['nodes']],['supervisor','dev','reviewer','qa','final'])
        self.assertEqual(view['metrics']['calls'],3);self.assertEqual(view['metrics']['tokens'],15)
        self.assertTrue(all(e['origin']=='RECORDED_PROVIDER_RECEIPT' for e in view['events']))

    def test_own_published_version_can_resume_but_later_external_edit_cannot(self):
        contract={'native_id':382,'source_version':0,'spec_sha256':'original-hash'}
        item={'id':382,'lockVersion':1,'description':{'raw':'spec plus verified delivery'},'_links':{'project':{'href':'/api/v3/projects/6'}}}
        key='engineering-owned-run-child';command={'action':'engineering_native_child','project_id':6,'method':'PATCH','path':'/api/v3/work_packages/382','payload':{}}
        self.store.begin(20,key,command);self.store.finish(20,key,item)
        self.assertTrue(lifecycle.source_matches(self.store,20,'owned-run',contract,item))
        self.assertFalse(lifecycle.source_matches(self.store,20,'owned-run',contract,{**item,'lockVersion':2}))

    def test_knowledge_retry_never_replays_unknown_outcome(self):
        from automation.engineering_delivery import knowledge_retry
        calls=[]
        def unknown(op,**args):calls.append(op);raise RuntimeError('OUTCOME_UNKNOWN_RECONCILE_FIRST')
        with self.assertRaisesRegex(RuntimeError,'UNKNOWN'):
            knowledge_retry(SimpleNamespace(operator=unknown),SimpleNamespace(id='fixture',check=lambda:None),383)
        self.assertEqual(calls,['knowledge'])


if __name__=='__main__':unittest.main()

import unittest
from gateway.agent_observer import project_task, task_progress

class ObserverProjectionTests(unittest.TestCase):
    def test_pr_creation_evidence_requires_matching_native_publication_receipt(self):
        monitor=self.monitor();url='https://github.com/owner/repo/pull/1'
        monitor['execution_summary']['pr_url']=url
        monitor['_runtime_result']={'status':'succeeded','native_readback':{'pr_url':url,'project_id':6}}
        result=project_task(self.package(),6,[monitor],now=1010)
        self.assertEqual(result['artifacts'][-1]['verification_status'],'VERIFIED')
        monitor['_runtime_result']['native_readback']['pr_url']='https://github.com/owner/repo/pull/2'
        result=project_task(self.package(),6,[monitor],now=1010)
        self.assertEqual(result['artifacts'][-1]['verification_status'],'RECORDED_ARTIFACT')
    def test_explicit_blocked_outcome_is_not_generic_failure(self):
        monitor=self.monitor('FAILED');monitor['_runtime_result']={'status':'blocked'}
        result=project_task(self.package(),6,[monitor],now=1010)
        self.assertEqual(result['workflow_status'],'BLOCKED')

    def test_rejected_review_is_failed_even_when_a_review_artifact_exists(self):
        monitor=self.monitor();monitor['nodes'][0]['agent']='reviewer'
        monitor['_runtime_result']={'review_evidence':{'verdict':'FAIL'}}
        result=project_task(self.package(),6,[monitor],now=1010)
        self.assertEqual(result['stages'][0]['status'],'FAILED')
    def package(self):
        return {'id':391,'subject':'Actual task','lockVersion':8,'_links':{'project':{'href':'/api/v3/projects/6'},'status':{'title':'READY FOR RELEASE'}}}

    def monitor(self,state='COMPLETED',updated=1000):
        return {'run_id':'run-1','state':state,'created_at':900,'updated_at':updated,'nodes':[{'id':'1','agent':'dev','state':state,'calls':3,'output':'files changed','output_origin':'STORED_ENGINEERING_ARTIFACT','started_at':900,'ended_at':1000}], 'events':[{'event_id':'event-1','event_type':'AGENT_COMPLETED','agent_id':'dev','timestamp':1000,'sequence':1}], 'execution_summary':{'checkpoint':{'version':2,'resumable':False}},'warnings':[]}

    def test_success_is_not_owner_acceptance_and_missing_stages_are_not_invented(self):
        result=project_task(self.package(),6,[self.monitor()],now=1010)
        self.assertEqual([s['agent_role'] for s in result['stages']],['dev'])
        self.assertNotEqual(result['acceptance_status'],'COMPLETED')
        self.assertEqual(result['business_status'],'READY FOR RELEASE')
        self.assertEqual(result['stages'][0]['status'],'COMPLETED')
        self.assertEqual(result['events'][0]['source_record_id'],'event-1')

    def test_stale_running_is_unknown_and_conflict_is_visible(self):
        result=project_task(self.package(),6,[self.monitor('RUNNING',1000)],now=2000)
        self.assertEqual(result['workflow_status'],'UNKNOWN')
        self.assertIsNone(result['current_agent'])
        self.assertTrue(result['source_conflicts'])
        self.assertEqual(result['freshness']['freshness_status'],'STALE')

    def test_retries_remain_under_one_task_with_all_runs_and_no_duplicate_events(self):
        first=self.monitor(); second=self.monitor();second.update(run_id='run-2',updated_at=1015)
        result=project_task(self.package(),6,[first,second],now=1020)
        self.assertEqual(len(result['runs']),2)
        self.assertEqual(result['stages'][0]['attempts'],2)
        self.assertEqual(len(result['events']),2)
        self.assertEqual(result['task_id'],391)

    def test_missing_telemetry_and_owner_gate_cannot_be_invented_from_closed_status(self):
        package=self.package();package['_links']['status']['title']='DONE'
        result=project_task(package,6,[],now=1000)
        self.assertEqual(result['workflow_status'],'UNKNOWN')
        self.assertEqual(result['acceptance_status'],'NOT_RECORDED')
        self.assertEqual(result['stages'],[])

    def test_wrong_native_project_is_denied(self):
        with self.assertRaises(PermissionError):project_task(self.package(),5,[],now=1000)

    def test_plaintext_evidence_is_redacted(self):
        monitor=self.monitor();monitor['nodes'][0]['output']='api_key=secret-value'
        result=project_task(self.package(),6,[monitor],now=1010)
        self.assertNotIn('secret-value',str(result))

if __name__=='__main__':unittest.main()

class ObserverAcceptanceTests(unittest.TestCase):
    def fixture(self):
        case=ObserverProjectionTests();p=case.package();m=case.monitor();m['terminal']=True
        m['nodes'] += [{'id':'2','agent':'reviewer','state':'COMPLETED','output':'PASS','output_origin':'STORED_ENGINEERING_ARTIFACT'},{'id':'3','agent':'qa','state':'COMPLETED','output':'PASS','output_origin':'STORED_ENGINEERING_ARTIFACT'}]
        m['_runtime_result']={'status':'succeeded','head_sha':'a'*40,'test_evidence':{'exit_code':0},'review_evidence':{'revision':'b'*64,'verdict':'PASS','findings':[],'qa':{'status':'PASS','exit_code':0}},'native_readback':{'child_id':391,'project_id':6,'child_version':7},'knowledge_readback':{'project_id':6}}
        m['execution_summary']['checkpoint']={'revision':'b'*64,'terminal_known':True}
        approval={'task_id':391,'project_id':6,'lock_version':8,'status_id':25,'is_closed':True,'status_name':'DONE','verified':True,'gate_errors':[], 'status_change':{'journal_id':900,'journal_version':9,'actor_id':18,'current_actor_role':'AI_SYSTEM_OWNER','at':1100,'to_status_id':25}}
        p['_links']['status']={'title':'DONE','href':'/api/v3/statuses/25'}
        return p,m,approval

    def test_real_current_closed_pm_transition_with_all_runtime_gates_can_complete(self):
        p,m,approval=self.fixture();result=project_task(p,6,[m],now=1200,approval=approval)
        self.assertEqual(result['acceptance_status'],'COMPLETED')
        self.assertFalse(result['acceptance']['missing_gates'])
        self.assertTrue(result['acceptance']['evidence_refs'])

    def test_final_acceptance_journal_is_a_new_source_event_after_the_runtime(self):
        p,m,approval=self.fixture();result=project_task(p,6,[m],now=1200,approval=approval)
        self.assertEqual(result['events'][-1]['timestamp'],1100)
        self.assertEqual(result['events'][-1]['event_type'],'TASK_ACCEPTANCE_COMPLETED')

    def test_missing_review_qa_journal_or_exact_version_blocks_completion(self):
        import copy
        for missing in ['review','qa','journal','version','revision','closed','runtime']:
            with self.subTest(missing=missing):
                p,m,approval=self.fixture()
                if missing=='review':m['_runtime_result']['review_evidence']['verdict']='FAIL'
                if missing=='qa':m['_runtime_result']['review_evidence']['qa']['exit_code']=1
                if missing=='journal':approval['status_change']=None
                if missing=='version':approval['lock_version']=7
                if missing=='revision':m['execution_summary']['checkpoint']['revision']='c'*64
                if missing=='closed':approval['is_closed']=False
                if missing=='runtime':m['_runtime_result']={}
                self.assertNotEqual(project_task(p,6,[m],now=1200,approval=approval)['acceptance_status'],'COMPLETED')

class ObserverServiceTests(unittest.TestCase):
    def test_a_missing_historical_reference_preserves_task_as_unknown(self):
        from unittest.mock import patch
        from gateway.native import NativeError
        from gateway.agent_observer import execute
        with patch('gateway.agent_observer.recorded_monitor',side_effect=NativeError(404,'OPENPROJECT_404')):
            result=execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1})
        self.assertEqual(result['workflow_status'],'UNKNOWN')
        self.assertEqual(result['source_conflicts'][0]['reason'],'RUN_REFERENCES_NOT_VISIBLE')
    def test_legacy_schema_is_visible_as_unknown_without_breaking_the_task_list(self):
        import json
        from gateway.agent_observer import execute
        with self.service.store.connect() as db:
            row=db.execute('SELECT document FROM agent_runs WHERE id=?',(self.fixture.scope.run_id,)).fetchone()
            document=json.loads(row[0]);document.update(state='historical-failed',result={'error':'LEGACY'})
            db.execute('UPDATE agent_runs SET document=? WHERE id=?',(json.dumps(document),self.fixture.scope.run_id))
        result=execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1})
        self.assertEqual(result['workflow_status'],'UNKNOWN')
        self.assertEqual(result['source_conflicts'][0]['reason'],'LEGACY_AGENT_RUN_SCHEMA_UNSUPPORTED')

    def test_system_summary_does_not_load_task_histories(self):
        from unittest.mock import patch
        from gateway.agent_observer import execute
        with patch('gateway.agent_observer._rows',side_effect=AssertionError('history loaded')):
            result=execute(self.service,self.who,self.native,'observer_active',{'summary_only':True})
        self.assertEqual(result['items'],[])
        self.assertIn('system',result)
    def setUp(self):
        from tests.test_execution_monitor import ExecutionMonitorTests
        from gateway.agent_models import NativeReference
        self.fixture=ExecutionMonitorTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.fixture.task=self.fixture.task.model_copy(update={'references':[NativeReference(work_package_id=1,lock_version=1)]})
        self.fixture.save();self.service=self.fixture.s
        self.native,self.who=self.service.native_actor(7)
        original=self.native.call
        self.native.call=lambda path,*a,**kw: {'task_id':1,'project_id':3,'lock_version':1,'verified':False} if path.startswith('/api/v3/qldapm/observer_acceptance/') else original(path,*a,**kw)

    def test_action_reuses_real_stored_monitor_and_keeps_actor_scope(self):
        from gateway.agent_observer import execute
        before={}
        with self.service.store.connect() as db:
            for table in ['ai_queue','ai_runs','agent_runs','requests']:
                before[table]=[tuple(row) for row in db.execute('SELECT * FROM '+table)]
        result=execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1})
        self.assertEqual(result['task_id'],1)
        self.assertEqual(len(result['runs']),1)
        self.assertEqual(result['runs'][0]['run_id'],self.fixture.scope.run_id)
        self.assertFalse(result['acceptance_status']=='COMPLETED')
        with self.service.store.connect() as db:
            for table,rows in before.items():self.assertEqual([tuple(row) for row in db.execute('SELECT * FROM '+table)],rows)
        other_native,other=self.service.native_actor(8)
        self.assertEqual(execute(self.service,other,other_native,'observer_active',{})['items'],[])

    def test_revoked_native_reference_cannot_be_read_through_task_or_run(self):
        from gateway.agent_observer import execute
        self.fixture.fixture.state.visible[7]=set()
        with self.assertRaises(PermissionError):execute(self.service,self.who,self.native,'observer_task_progress',{'task_id':1})
        with self.assertRaises(PermissionError):execute(self.service,self.who,self.native,'observer_run_details',{'run_id':self.fixture.scope.run_id})

    def test_validation_unknown_arguments_and_extra_project_denied(self):
        from gateway.agent_observer import execute
        for args in [{'task_id':True},{'task_id':-1},{'task_id':1,'actor':18}]:
            with self.assertRaises(ValueError):execute(self.service,self.who,self.native,'observer_task_progress',args)
        for args in [{'limit':0},{'limit':True},{'query':'x'*161},{'state':'FAKE'}]:
            with self.assertRaises(ValueError):execute(self.service,self.who,self.native,'observer_active',args)

    def test_registered_command_dispatch_uses_same_read_model(self):
        from unittest.mock import patch
        with patch.object(self.service,'native_actor',return_value=(self.native,self.who)):
            result=self.service.execute_actor(7,{'action':'observer_task_progress','arguments':{'task_id':1}})['result']
        self.assertEqual(result['task_id'],1)
        self.assertEqual(result['project_id'],3)

"""Synthetic Native timing/response loss, durable READ recovery and worker/UI contracts. No network."""
import copy,json,tempfile,time,unittest,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager
import httpx
from gateway.business_runs import register,link_command,recover,resume,load,project_view,monitor,ProviderBudget,read_analysis
from gateway.native import Native,NativeError
from gateway.service import Service
from gateway.store import Store
from gateway.gemini import Gemini,ProviderError

class BusinessLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.service=Service(self.store,{'project_id':5,'gateway_mode':'native',
            'source_field':'customField11','type_ids':[10],'users':{'7':'PM','8':'QA'}},Path(self.tmp.name)/'workspaces')
        self.run=self.store.create_run(7);self.key='ai-'+self.run+'-2'
        self.args={'source_id':'synthetic-marker','subject':'test','type_id':10,'parent_id':50,'assignee_id':8}
        self.row={'id':367,'subject':'test','lockVersion':0,'customField11':'synthetic-marker','description':{'raw':''},
            '_links':{k:{'href':v} for k,v in {'project':'/api/v3/projects/5','type':'/api/v3/types/10',
                'parent':'/api/v3/work_packages/50','assignee':'/api/v3/users/8','author':'/api/v3/users/7','status':'/api/v3/statuses/1'}.items()}}
        self.rows=[self.row];self.reads=0
        def packages():self.reads+=1;return self.rows
        self.native=SimpleNamespace(packages=packages,package=lambda _:self.row)
        self.service.native_actor=lambda actor,**kw:(self.native,{'user_id':actor,'role':'PM'})
        register(self.store,7,5,self.run,{'prompt':'Create synthetic fixture'})
        link_command(self.service,7,self.run,self.key)
        self.store.begin(7,self.key,{'action':'create_work_package','arguments':self.args})

    def failed(self,calls=None):
        calls=calls if calls is not None else [{'action':'identity','arguments':{},'result':{'result':{'role':'PM'}}},
            {'action':'create_work_package','arguments':self.args,'result':{'error':'NativeError','outcome_unknown':True}}]
        self.store.finish_run(7,self.run,{'error':'GEMINI_RUN_DEADLINE','tools':calls},'failed_or_unknown')

    def test_lost_response_auto_reconciles_without_post_and_preserves_original(self):
        self.failed();raw=self.store.run(7,self.run);resume(self.service)
        d=load(self.store,7,5,self.run);self.assertEqual(d['state'],'RECONCILED_SUCCESS')
        self.assertEqual(d['synthesis'],'SYSTEM_GENERATED');self.assertEqual(self.reads,1)
        self.assertEqual(self.store.run(7,self.run),raw)
        projected=project_view(self.service,7,raw,self.native)
        self.assertEqual(projected['state'],'reconciled_success');self.assertEqual(projected['worker_state'],'failed_or_unknown')
        self.assertIn('Native API',projected['result']['heading']);self.assertEqual(projected['result']['synthesis_origin'],'SYSTEM')
        view=monitor(self.service,{'user_id':7,'role':'PM'},projected,d)
        self.assertTrue(view['terminal']);self.assertEqual(view['state'],'RECONCILED_SUCCESS')
        self.assertFalse(any(n['agent']=='supervisor' for n in view['nodes']))
        before=len(view['events']);resume(self.service)
        self.assertEqual(len(monitor(self.service,{'user_id':7,'role':'PM'},projected,d)['events']),before)

    def test_recovery_after_hard_worker_kill_uses_stored_command(self):
        self.failed([]);d=recover(self.service,7,self.run,lambda _:False)
        self.assertEqual(d['state'],'RECONCILED_SUCCESS');self.assertEqual(d['view']['outcomes'][0]['work_package_id'],367)

    def test_missing_duplicate_and_mismatched_marker_never_confirm_or_retry(self):
        self.failed()
        for rows in ([],[self.row,self.row],[{**self.row,'customField11':'wrong'}]):
            with self.subTest(rows=len(rows)):
                self.rows=rows
                with self.store.connect() as db:
                    d=load(self.store,7,5,self.run);d['attempts']=0
                    db.execute('update business_runs set document=? where id=?',(json.dumps(d),self.run))
                d=recover(self.service,7,self.run,lambda _:False)
                self.assertEqual(d['state'],'UNKNOWN_REQUIRES_REVIEW');self.assertEqual(d['attempts'],3)
                self.assertEqual(self.store.request_status(7,self.key)['state'],'pending')

    def test_permissions_revoked_before_reconcile_and_result_projection(self):
        self.failed()
        def denied(*a,**kw):raise PermissionError('ROLE_REVOKED')
        self.service.native_actor=denied
        d=recover(self.service,7,self.run,lambda _:False)
        self.assertEqual(d['state'],'UNKNOWN_REQUIRES_REVIEW');self.assertEqual(self.reads,0)
        with self.assertRaises(PermissionError):load(self.store,8,5,self.run)
        with self.assertRaises(PermissionError):load(self.store,7,6,self.run)

    def test_done_receipt_requires_current_proof_before_business_success(self):
        self.failed();self.store.finish_reconciliation(7,self.key,self.row,5)
        self.row['subject']='changed'
        d=recover(self.service,7,self.run,lambda _:False)
        self.assertEqual(d['state'],'UNKNOWN_REQUIRES_REVIEW');self.assertEqual(d['view']['status'],'partial')

    def test_read_only_result_hides_stale_native_version(self):
        with self.store.connect() as db:
            d=load(self.store,7,5,self.run);d.update(read_only=True,commands=[])
            db.execute('update business_runs set document=? where id=?',(json.dumps(d),self.run))
        r=Gemini.business_result('get_work_package',{'result':self.row})
        self.store.finish_run(7,self.run,{'synthesis_origin':'MODEL','text':'Old analysis','tools':[{'action':'get_work_package','arguments':{'id':367},'result':r}]},'done')
        recover(self.service,7,self.run);self.row['lockVersion']=1
        result=project_view(self.service,7,self.store.run(7,self.run),self.native)
        self.assertTrue(result['result']['stale']);self.assertNotIn('Old analysis',json.dumps(result))

    def test_command_not_submitted_remains_failed_not_success(self):
        self.failed([])
        with self.store.connect() as db:db.execute('delete from requests where key=?',(self.key,))
        d=recover(self.service,7,self.run,lambda _:False)
        self.assertEqual(d['state'],'FAILED');self.assertEqual(d['view']['status'],'failed');self.assertEqual(self.reads,0)

    def test_comment_rechecks_work_package_not_activity_id(self):
        args={'id':50,'lock_version':1,'text':'fixture'};calls=[]
        with self.store.connect() as db:
            db.execute('update requests set payload=? where actor=7 and key=?',(json.dumps({'action':'comment','arguments':args}),self.key))
        self.store.finish(7,self.key,{'result':{'id':999,'_type':'Activity::Comment'}})
        self.native.package=lambda identifier:calls.append(identifier) or self.row
        self.failed([{'action':'identity','arguments':{},'result':{}},{'action':'comment','arguments':args,'result':{'error':'NativeError','outcome_unknown':True}}])
        recover(self.service,7,self.run)
        project_view(self.service,7,self.store.run(7,self.run),self.native)
        self.assertEqual(calls,[50,50])

    def test_unrelated_unknown_create_is_not_overwritten(self):
        first={'action':'create_work_package','arguments':{**self.args,'source_id':'other'},'result':{'error':'NativeError','outcome_unknown':True}}
        self.failed([first,{'action':'create_work_package','arguments':self.args,'result':{'error':'NativeError','outcome_unknown':True}}])
        d=recover(self.service,7,self.run,lambda _:False)
        self.assertTrue(d['view']['tools'][0]['result']['outcome_unknown'])
        self.assertEqual(d['state'],'UNKNOWN_REQUIRES_REVIEW')

    def test_read_model_final_text_and_usage_are_not_replaced_by_system_fallback(self):
        register(self.store,7,5,self.run,{'prompt':'Read fixture'})
        with self.store.connect() as db:
            d=load(self.store,7,5,self.run);d['commands']=[]
            db.execute('update business_runs set document=? where id=?',(json.dumps(d),self.run))
        text='Work Package #367 có parent #50 và QA #8.'
        self.store.finish_run(7,self.run,{'synthesis_origin':'MODEL','text':text,'tools':[]},'done')
        d=recover(self.service,7,self.run);self.assertEqual(d['state'],'COMPLETED');self.assertEqual(d['view']['text'],text)

    def test_history_filter_sort_pagination_and_actor_isolation(self):
        self.failed();recover(self.service,7,self.run)
        for _ in range(3):
            identifier=self.store.create_run(7);register(self.store,7,5,identifier,{'prompt':'other'})
        p=self.store.execution_history(7,5,limit=2);self.assertEqual(p['total'],4);self.assertEqual(p['next_offset'],2)
        second=self.store.execution_history(7,5,limit=2,offset=2)
        self.assertFalse(set(r['run_id'] for r in p['items']) & set(r['run_id'] for r in second['items']))
        self.assertEqual(self.store.execution_history(7,5,state='RECONCILED_SUCCESS')['total'],1)
        self.assertEqual(self.store.execution_history(8,5)['total'],0)

    def test_only_exact_receipt_is_atomic_once_even_concurrent_proof(self):
        r=self.store.finish_reconciliation(7,self.key,self.row,5)
        self.assertEqual(self.store.finish_reconciliation(7,self.key,self.row,5),r)
        with self.store.connect() as db:
            self.assertEqual(db.execute("select count(*) from audit where action='reconcile_request'").fetchone()[0],1)

    def test_native_create_delays_and_deadline_no_post_retry(self):
        for delay in (5,30,55,75,95):
            with self.subTest(delay=delay):
                clock=[100.0];posts=[]
                @contextmanager
                def wire(method,url,**kw):
                    posts.append(method);clock[0]+=delay
                    yield httpx.Response(201,json=self.row,request=httpx.Request(method,url))
                with patch('gateway.native.time.monotonic',lambda:clock[0]),patch('gateway.native.httpx.stream',wire):
                    n=Native('http://localhost:8088','synthetic',5)
                    if delay>90:
                        with self.assertRaises(NativeError):n.call('/api/v3/work_packages','POST',{})
                    else:self.assertEqual(n.call('/api/v3/work_packages','POST',{})['id'],367)
                self.assertEqual(posts,['POST'])

    def test_provider_cap_checked_before_seventh_http_and_usage_reservation(self):
        context=ProviderBudget(self.service,{'actor':7,'id':self.run,'business_read_only':True})
        for _ in range(3):
            for phase in ('countTokens','generateContent'):
                context.check_phase(phase);context.budget.before_attempt(phase)
        with self.assertRaises(ProviderError):context.check_phase('countTokens')
        self.assertEqual(context.budget.http_attempts,6);self.assertEqual(context.budget.generations,3)

    def test_failed_commit_is_not_native_success(self):
        self.store.finish(7,self.key,{'error':'NATIVE_REJECTED','status':422,'outcome_unknown':False})
        self.failed([{'action':'create_work_package','arguments':self.args,'result':{'error':'NativeError','status':422}}])
        d=recover(self.service,7,self.run,lambda _:False)
        self.assertEqual(d['state'],'FAILED');self.assertEqual(d['native'],'NOT_APPLIED');self.assertEqual(self.reads,0)

    def test_repeat_known_rejection_returns_error_without_new_post(self):
        self.rows=[];calls=[];self.native.project_id=5;self.service.assignee=lambda _:None
        def call(path,method='GET',payload=None):
            calls.append([method,path])
            if path=='/api/v3/work_packages':raise NativeError(422,'OPENPROJECT_422')
            return {}
        self.native.call=call
        command={'action':'create_work_package','arguments':self.args,'idempotency_key':'rejection-proof'}
        for _ in range(2):
            # Exercise trusted post-approval execution, not the removed client auto-execute bypass.
            with self.assertRaises(NativeError) as error:self.service.execute_actor(7,command,confirmed=True)
            self.assertEqual(error.exception.status,422)
        self.assertEqual(sum(path=='/api/v3/work_packages' for method,path in calls),1)

    def test_readback_permission_failure_after_commit_is_unknown(self):
        native=SimpleNamespace(project_id=5,packages=lambda:[],package=lambda _:self.row,call=lambda *args:self.row)
        self.service.assignee=lambda _:None
        count=[0]
        def package(_):
            count[0]+=1
            if count[0]>1:raise NativeError(403,'OPENPROJECT_403')
            return self.row
        native.package=package
        with self.assertRaisesRegex(NativeError,'READBACK_OUTCOME_UNKNOWN'):
            self.service.perform({'user_id':7,'role':'PM'},native,'create_work_package',self.args)

    def test_explicit_read_engine_rejects_consent_and_never_uses_local_query(self):
        with self.assertRaises(PermissionError):self.service.start_run({'user_id':7,'role':'PM'},
            {'engine':'gemini_read','prompt':'Read #367','allow_routine_writes':True},native=self.native)
        with patch.object(self.service.gemini,'validate_prompt',return_value={}),patch.object(self.service,'start_dispatcher'):
            r=self.service.start_run({'user_id':7,'role':'PM'},{'engine':'gemini_read','prompt':'đọc công việc 367'},native=self.native)
        self.assertEqual(r['result']['state'],'running')
        self.assertTrue(load(self.store,7,5,r['result']['id'])['read_only'])

    def test_single_turn_read_uses_native_before_sdk_and_mock_stays_mock(self):
        events=[];root=Path(self.tmp.name);(root/'gemini.key').write_text('synthetic-only')
        policy={'model':'gemini-3.5-flash-lite','data_scope':'project-business-content','project':'offline-fixture',
            'limits':{'rpm':100,'rpd':100,'tpm':1000000}}
        def execute(actor,command):
            self.assertEqual(command['action'],'get_work_package');events.append('native')
            return {'result':{**self.row,'id':command['arguments']['id']}}
        def wire(request):
            self.assertEqual(events[:2],['native','native']);body=json.loads(request.content)
            if request.url.path.endswith(':countTokens'):events.append('count');return httpx.Response(200,json={'totalTokens':20})
            self.assertNotIn('tools',body);self.assertEqual(body['generationConfig']['maxOutputTokens'],3000);events.append('generate')
            return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':[{'text':json.dumps({
                'citations':[367,50],'facts':[{'id':367,'parent_id':50,'assignee_id':8},{'id':50,'parent_id':50,'assignee_id':8}],'explanation':'Native #367 và #50, chỉ đọc.'})}]}}],
                'usageMetadata':{'promptTokenCount':20,'candidatesTokenCount':30,'totalTokenCount':50}})
        sdk=Gemini.sdk_client
        def offline(gemini,transport=None,timeout=120):return sdk(gemini,httpx.MockTransport(wire),timeout)
        with patch.object(self.service,'execute_actor',execute),patch.object(Gemini,'settings',return_value=policy),patch.object(Gemini,'sdk_client',offline):
            result=read_analysis(self.service,{'actor':7,'id':self.run,'prompt':'Read #367 and #50','write_scope_ids':[367,50]})
        self.assertEqual(events,['native','native','count','generate']);self.assertFalse(result['model_used'])
        self.assertEqual(result['read_budget']['generations'],1);self.assertEqual(result['read_budget']['http_attempts'],2)
        self.assertEqual(result['synthesis_origin'],'MODEL')
        with self.store.connect() as db:
            receipts=[json.loads(r[0]) for r in db.execute('select document from gemini_call_receipts')]
        self.assertTrue(all(r['state']=='MOCK_SUCCESS' for r in receipts))

    def test_single_turn_read_revoked_acl_stops_before_provider(self):
        with patch.object(self.service,'execute_actor',side_effect=PermissionError('CURRENT_ROLE_DENIED')),patch.object(Gemini,'sdk_client',side_effect=AssertionError('NO_PROVIDER')):
            with self.assertRaises(PermissionError):read_analysis(self.service,{'actor':7,'id':self.run,'prompt':'Read','write_scope_ids':[367]})
        with self.assertRaises(ValueError):read_analysis(self.service,{'actor':7,'id':self.run,'prompt':'Read','write_scope_ids':[]})

    def test_read_citations_reject_foreign_missing_and_ambiguous_ids(self):
        from gateway.business_runs import ReadAnswer
        def execute(actor,command):return {'result':{**self.row,'id':command['arguments']['id']}}
        for answer in (ReadAnswer(facts=[{'id':367,'parent_id':50,'assignee_id':8},{'id':50,'parent_id':50,'assignee_id':8}],citations=[999],explanation='Foreign #999'),ReadAnswer(facts=[{'id':367,'parent_id':50,'assignee_id':8},{'id':50,'parent_id':50,'assignee_id':8}],citations=[367],explanation='Missing parent'),
                       ReadAnswer(facts=[{'id':367,'parent_id':50,'assignee_id':8},{'id':50,'parent_id':50,'assignee_id':8}],citations=[367,50],explanation='Native #367 assignee #8')):
            with self.subTest(answer=answer),patch.object(self.service,'execute_actor',execute),patch.object(self.service.gemini,'structured',return_value=answer):
                with self.assertRaisesRegex(ProviderError,'CITATION_INVALID'):
                    read_analysis(self.service,{'actor':7,'id':self.run,'prompt':'Read','write_scope_ids':[367,50]})

    def test_read_canonical_claims_are_host_derived_from_native_not_model_paths(self):
        from gateway.business_runs import ReadAnswer
        def execute(actor,command):return {'result':{**self.row,'id':command['arguments']['id']}}
        with (patch.object(self.service,'execute_actor',execute),patch.object(self.service.gemini,'structured',return_value=ReadAnswer(facts=[{'id':367,'parent_id':50,'assignee_id':8},{'id':50,'parent_id':50,'assignee_id':8}],
                citations=[367,50],explanation='Native #367 có Parent #50 và assignee User8.')),
                patch.object(self.service.gemini,'settings',return_value={'model':'gemini-3.5-flash-lite'})):
            result=read_analysis(self.service,{'actor':7,'id':self.run,'prompt':'Read','write_scope_ids':[367,50]})
        self.assertEqual([c['value'] for c in result['claims']],[367,50])
        self.assertTrue(all(c['path']==['result','id'] and c['source_hash'] for c in result['claims']))

    def test_read_parent_and_assignee_must_equal_native_fields(self):
        from gateway.business_runs import ReadAnswer
        for changed in ('parent_id','assignee_id'):
            facts=[{'id':367,'parent_id':50,'assignee_id':8},{'id':50,'parent_id':50,'assignee_id':8}];facts[0][changed]=999
            with self.subTest(field=changed),patch.object(self.service,'execute_actor',lambda actor,c:{'result':{**self.row,'id':c['arguments']['id']}}),patch.object(
                    self.service.gemini,'structured',return_value=ReadAnswer(facts=facts,citations=[367,50],explanation='Native #367 Parent #50')):
                with self.assertRaisesRegex(ProviderError,'FACT_INVALID'):read_analysis(self.service,{'actor':7,'id':self.run,'prompt':'Read','write_scope_ids':[367,50]})

if __name__=='__main__':unittest.main()

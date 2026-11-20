"""Application contract tests; synthetic Native adapter, no live provider or serving writes."""
import json
import time
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient
from gateway.app import create_app
from gateway.gemini import ProviderError
from gateway.quota_panel import get_quota_panel_data
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.knowledge_classifier import classify_document,KnowledgeDocType
from gateway.knowledge_ingestion import KnowledgeIngester,IngestionStatus
from tests import test_local_queries as fixture


class RemainingIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fx=fixture.LocalQueryTests();self.fx.setUp();self.addCleanup(self.fx.tearDown)
        self.service,self.store=self.fx.service,self.fx.store
        self.service.config['hosts']=['testserver']
        self.tokens={a:self.store.issue_token(a,r,f'synthetic-native-{a}') for a,r in self.fx.state.roles.items()}
        self.client=TestClient(create_app(self.fx.root,self.service))
        self.dispatch=patch.object(self.service,'start_dispatcher');self.dispatch.start();self.addCleanup(self.dispatch.stop)

    def command(self,action,args=None,actor=7,key=None):
        body={'action':action,'arguments':args or {}}
        if key: body['idempotency_key']=key
        return self.client.post('/api/v1/commands',json=body,headers={'Authorization':'Bearer '+self.tokens[actor]})

    def start(self,key='run'):
        r=self.command('start_ai_run',{'prompt':'Phân tích yêu cầu công việc #2','engine':'supervisor'},key=key)
        self.assertEqual(r.status_code,200,r.text)
        return r.json()

    def test_queue_worker_results_trace_and_native_revalidation(self):
        with patch.object(self.service.gemini,'settings',side_effect=ProviderError('DISABLED')):
            receipt=self.start();self.assertEqual(self.start(),receipt)
            claimed=self.store.claim_run(local_only=True)
            result=self.service.run_supervisor(7,claimed['id'])
            self.assertEqual(result['agent_result']['state'],'COMPLETED')
            self.assertFalse(result['model_used']);self.assertEqual(result['engine'],'local_supervisor')
            self.store.finish_run(7,claimed['id'],result,'done')
            polled=self.command('get_ai_run',{'id':claimed['id']})
            self.assertIn('Phân tích',polled.text)
            agent=self.store.agent_run(7,3,claimed['id'])
            self.assertEqual(agent.result.references[0].work_package_id,2)
            trace=self.store.agent_trace_page(7,3,claimed['id'])
            self.assertGreaterEqual(trace['total'],2)
            self.assertEqual(self.command('get_ai_run',{'id':claimed['id']},actor=8).status_code,403)
            self.fx.state.rows[1]['lockVersion']+=1
            stale=self.command('get_ai_run',{'id':claimed['id']}).json()['result']['result']
            self.assertTrue(stale['stale']);self.assertNotIn('agent_result',stale)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM gemini_usage').fetchone()[0],0)

    def test_explicit_multiple_specialists_execute_and_aggregate_without_provider(self):
        response = self.command('start_ai_run', {'prompt':
            'BA, Developer và QA: Phân tích công việc #2; chỉ đọc; không ghi thay đổi.',
            'engine': 'supervisor'}, key='three-specialists')
        self.assertEqual(response.status_code, 200, response.text)
        claimed = self.store.claim_run(local_only=True)
        result = self.service.run_supervisor(7, claimed['id'])
        steps = result['plan']['steps']
        self.assertEqual([s['agent'] for s in steps], ['ba', 'dev', 'qa', 'reviewer'])
        self.assertEqual(steps[-1]['dependencies'], [1, 2, 3])
        self.assertEqual([o['agent'] for o in result['agent_outputs']], ['ba', 'dev', 'qa', 'reviewer'])
        self.assertEqual(result['agent_result']['state'], 'COMPLETED')
        self.assertFalse(result['model_used'])
        self.store.finish_run(7, claimed['id'], result, 'done')
        monitor = self.command('get_execution_monitor', {'id': claimed['id']})
        self.assertEqual(monitor.status_code, 200, monitor.text)
        self.assertEqual([n['agent'] for n in monitor.json()['result']['nodes']],
                         ['supervisor', 'ba', 'dev', 'qa', 'reviewer', 'final'])
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM gemini_usage').fetchone()[0], 0)

    def test_changed_command_cannot_reuse_key_and_no_implicit_consent(self):
        self.start()
        self.assertEqual(self.command('start_ai_run',{'prompt':'Other','engine':'supervisor'},key='run').status_code,422)
        self.assertEqual(self.command('start_ai_run',{'prompt':'Other','engine':'supervisor','allow_routine_writes':True},key='other').status_code,403)

    def test_native_business_denies_operator_tools_before_workspace_or_job_access(self):
        from gateway.permissions import SANDBOX_ONLY,allowed
        for action in SANDBOX_ONLY:
            self.assertTrue(allowed('PM',action,'strict'))
            self.assertFalse(allowed('PM',action,'native'))
            response=self.command(action,{},key='operator-'+action)
            self.assertEqual(response.status_code,403,response.text)
            self.assertEqual(response.json()['error'],'NATIVE_BUSINESS_OPERATOR_TOOL_DENIED')
            with self.assertRaisesRegex(PermissionError,'NATIVE_BUSINESS_OPERATOR_TOOL_DENIED'):
                self.service.perform({'user_id':7,'role':'PM'},None,action,{})
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],0)

    def test_native_pm_mcp_catalog_does_not_expose_operator_tools(self):
        from gateway.permissions import SANDBOX_ONLY
        with TestClient(create_app(self.fx.root,self.service)) as client:
            headers={'Authorization':'Bearer '+self.tokens[7],'Accept':'application/json, text/event-stream'}
            response=client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':'initialize','params':{
                'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'synthetic','version':'1'}}})
            self.assertEqual(response.status_code,200,response.text)
            response=client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':2,'method':'tools/list'})
            names={row['name'] for row in response.json()['result']['tools']}
            self.assertFalse(names & SANDBOX_ONLY)
            self.assertIn('start_ai_run',names);self.assertIn('knowledge_search',names)

    def test_pm_worker_accepts_native_null_assignee_link(self):
        self.fx.state.rows[1]['_links']['assignee']={'href':None,'title':None}
        dashboard=self.command('analyze')
        self.assertEqual(dashboard.status_code,200,dashboard.text)
        self.assertEqual(dashboard.json()['result']['control_center']['progress']['limit'],10)
        r=self.command('start_ai_run',{'prompt':'Phân tích rủi ro sprint công việc #2','engine':'supervisor'},key='unassigned')
        self.assertEqual(r.status_code,200,r.text)
        claimed=self.store.claim_run(local_only=True)
        result=self.service.run_supervisor(7,claimed['id'])
        self.assertEqual(result['agent_result']['state'],'COMPLETED')
        self.assertFalse(result['model_used'])
        self.assertEqual(result['agent_result']['references'],[{'schema_version':1,'work_package_id':2,'lock_version':1}])

    def test_explicit_local_scope_never_scans_unrelated_project_packages(self):
        with patch.object(self.fx.native_factory,'packages',side_effect=AssertionError('NO_UNRELATED_COLLECTION')):
            self.start();claimed=self.store.claim_run(local_only=True)
            result=self.service.run_supervisor(7,claimed['id'])
            self.assertEqual(result['source_ids'],[2])
            self.store.finish_run(7,claimed['id'],result,'done')
            response=self.command('get_ai_run',{'id':claimed['id']})
            self.assertEqual(response.status_code,200,response.text)
            self.assertIn('agent_result',response.json()['result']['result'])
            self.fx.state.visible[7]=[1]
            self.assertEqual(self.command('get_ai_run',{'id':claimed['id']}).status_code,403)

    def test_explicit_local_scope_is_bounded_before_enqueue(self):
        r=self.command('start_ai_run',{'prompt':'Analyze '+', '.join('#'+str(i) for i in range(1,12)),
            'engine':'supervisor'},key='too-many')
        self.assertEqual(r.status_code,422,r.text)
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM ai_queue').fetchone()[0],0)

    def test_cancellation_owns_scope_and_does_not_replay(self):
        identifier=self.start()['result']['id']
        self.assertEqual(self.command('cancel_agent_run',{'id':identifier},actor=8,key='deny').status_code,403)
        response=self.command('cancel_agent_run',{'id':identifier},key='cancel')
        self.assertEqual(response.status_code,200,response.text)
        self.assertIsNone(self.store.claim_run())
        self.assertEqual(self.store.agent_run(7,3,identifier).result.error_code,'AI_RUN_FAILED_OR_UNKNOWN')

    def test_cancellation_records_one_terminal_event_and_cannot_be_overwritten(self):
        identifier = self.start(key='cancel-trace')['result']['id']
        self.assertEqual(self.store.claim_run(local_only=True)['id'], identifier)
        self.assertEqual(self.command('cancel_agent_run', {'id': identifier}, key='cancel-trace-once').status_code, 200)
        self.assertEqual(self.command('cancel_agent_run', {'id': identifier}, key='cancel-trace-twice').status_code, 200)
        # A late worker completion may release its queue lease, but never replace cancellation.
        self.store.finish_run(7, identifier, {'status': 'succeeded', 'text': 'LATE_OUTPUT'}, 'done')
        self.assertEqual(self.store.run(7, identifier)['result']['error'], 'AGENT_CANCELLED')
        events, _ = self.store.execution_records(7, 3, identifier)
        terminal = [e for e in events if e['event_type'] in ('RUN_FAILED', 'RUN_COMPLETED')]
        self.assertEqual(len(terminal), 1)
        self.assertEqual(terminal[0]['event_type'], 'RUN_FAILED')
        self.assertEqual(terminal[0]['error_code'], 'AGENT_CANCELLED')
        self.assertEqual(sum(e['event_type'] == 'RESULT_AVAILABLE' for e in events), 1)
        self.assertEqual(self.command('get_execution_monitor', {'id': identifier}).json()['result']['state'], 'CANCELLED')

    def test_cancellation_retains_partial_specialist_output_for_monitor(self):
        from gateway.agent_models import AgentResult, NativeReference, RunScope
        from gateway.planner import plan_request
        from gateway.store import canonical, digest
        identifier = self.start(key='cancel-partial')['result']['id']
        self.store.claim_run(local_only=True)
        run = self.store.agent_run(7, 3, identifier)
        task = self.store.agent_task(7, 3, run.task_id)
        plan = plan_request(task, 'PM')
        output = AgentResult(**{k: getattr(run, k) for k in RunScope.model_fields},
            state='COMPLETED', summary='PARTIAL_SAVED_OUTPUT', references=[NativeReference(work_package_id=2, lock_version=1)])
        self.store.progress_run(7, identifier, {'engine': 'local_supervisor', 'plan': plan.model_dump(),
            'source_ids': [2], 'source_fingerprint': digest(canonical([(2, 1)])),
            'agent_outputs': [{'step_id': 1, 'agent': plan.steps[0].agent, 'result': output.model_dump()}]})
        self.assertEqual(self.command('cancel_agent_run', {'id': identifier}, key='cancel-partial-confirm').status_code, 200)
        self.assertEqual(self.store.run(7, identifier)['result']['agent_outputs'][0]['result']['summary'], 'PARTIAL_SAVED_OUTPUT')
        monitor = self.command('get_execution_monitor', {'id': identifier})
        self.assertEqual(monitor.status_code, 200, monitor.text)
        self.assertEqual(monitor.json()['result']['state'], 'CANCELLED')
        self.assertIn('PARTIAL_SAVED_OUTPUT', monitor.text)

    def test_second_brain_lifecycle_actor_acl_stale_source_and_reopen(self):
        r=self.command('knowledge_ingest',{'id':2},key='index')
        self.assertEqual(r.status_code,200,r.text)
        def search(actor=7):
            r=self.command('knowledge_search',{'query':'Synthetic'},actor=actor)
            self.assertEqual(r.status_code,200,r.text)
            return r.json()['result']['items']
        self.assertEqual(search()[0]['native_id'],2)
        self.assertEqual(search(8),[])
        self.assertEqual(KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fx.root/'knowledge.sqlite'))).count_documents(),1)
        self.fx.state.rows[1]['lockVersion']=2
        self.assertEqual(search(),[])
        self.command('knowledge_ingest',{'id':2},key='reindex')
        self.assertEqual(search()[0]['lock_version'],2)
        self.fx.state.visible[7]=[1]
        self.assertEqual(search(),[])
        self.fx.state.visible[7]=[1,2]
        self.assertTrue(self.command('knowledge_deindex',{'id':2},key='delete').json()['result']['deleted'])
        self.assertEqual(search(),[])

    def test_scope_and_source_cannot_be_supplied_by_client(self):
        self.assertEqual(self.command('knowledge_ingest',{'id':1},actor=8,key='no-access').status_code,403)
        for args in ({'id':2,'actor_id':7},{'id':2,'content':'spoof'},{'id':2,'project_id':4},{'id':'https://example.org'}):
            self.assertIn(self.command('knowledge_ingest',args,key=str(args)).status_code,(403,422))
        self.assertEqual(self.command('knowledge_search',{'query':'x','limit':-1}).status_code,422)
        self.assertEqual(self.command('start_ai_run',{'prompt':'Analyze','engine':{}},key='bad-engine').status_code,422)

    def test_knowledge_actor_scope_precedes_fts_and_result_limits(self):
        storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fx.root/'knowledge.sqlite')))
        # Another actor's index must not crowd an authorized result out of the top100/top10.
        for index in range(120):
            doc = classify_document(KnowledgeDocType.WORK_PACKAGE, '3', f'actor:8:wp:{index}',
                'actorlimit', 'actorlimit', allowed_roles=['PM'],
                metadata={'actor_id': 8, 'native_id': 2, 'lock_version': 1})
            self.assertTrue(storage.store_document(doc))
        other_project = classify_document(KnowledgeDocType.WORK_PACKAGE, '4', 'actor:7:wp:2',
            'actorlimit', 'actorlimit', allowed_roles=['PM'],
            metadata={'actor_id': 7, 'native_id': 2, 'lock_version': 1})
        self.assertTrue(storage.store_document(other_project))
        self.fx.state.rows[1]['subject'] = 'actorlimit'
        self.assertEqual(self.command('knowledge_ingest', {'id': 2}, key='actor-index').status_code, 200)
        response = self.command('knowledge_search', {'query': 'actorlimit', 'limit': 1})
        self.assertEqual(response.status_code, 200, response.text)
        items = response.json()['result']['items']
        self.assertEqual([item['source_id'] for item in items], ['actor:7:wp:2'])
        self.assertEqual([item['native_id'] for item in items], [2])

    def test_knowledge_actor_scope_rejects_invalid_internal_identity(self):
        from gateway.knowledge_search import KnowledgeSearchEngine
        storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fx.root/'knowledge.sqlite')))
        for actor in (True, '7', 0, -1):
            with self.subTest(actor_type=type(actor).__name__):
                with self.assertRaisesRegex(ValueError, 'KNOWLEDGE_ACTOR_SCOPE_REQUIRED'):
                    KnowledgeSearchEngine(storage).search('example', '3', 'PM', actor_id=actor)

    def test_local_instruction_secret_is_redacted_before_persistence(self):
        marker='synthetic-local-credential-do-not-persist'
        response=self.command('start_ai_run',{'prompt':'Analyze password='+marker,'engine':'supervisor'},key='secret')
        self.assertEqual(response.status_code,200,response.text)
        with self.store.connect() as db:
            for table,column in (('requests','payload'),('agent_tasks','document'),('ai_queue','payload')):
                self.assertNotIn(marker,str([row[0] for row in db.execute('SELECT '+column+' FROM '+table)]))

    def test_physical_backup_preserves_fts_chunks_and_blocks_stale_revision(self):
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fx.root/'wal.sqlite')))
        newer=classify_document(KnowledgeDocType.WORK_PACKAGE,'3','wp:3','Đăng nhập','Tiêu chí đăng nhập',metadata={'lock_version':2})
        self.assertTrue(storage.store_document(newer))
        older=classify_document(KnowledgeDocType.WORK_PACKAGE,'3','wp:3','Old','Old content',metadata={'lock_version':1})
        self.assertFalse(storage.store_document(older))
        path=storage.backup_file(self.fx.root/'backup.sqlite')
        restored=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(path)))
        self.assertEqual(restored.count_documents(),1)
        self.assertGreater(KnowledgeIngester(restored).count_chunks(newer.source_hash),0)
        from gateway.knowledge_search import KnowledgeSearchEngine
        self.assertEqual(KnowledgeSearchEngine(restored).search('dang nhap','3','PM')[0].title,'Đăng nhập')
        with self.assertRaises(FileExistsError):storage.backup_file(path)
        bad=self.fx.root/'corrupt.sqlite';bad.write_bytes(b'NOT_A_SQLITE_DATABASE')
        with self.assertRaisesRegex(ValueError,'KNOWLEDGE_STORE_UNAVAILABLE'):
            KnowledgeStorage(KnowledgeStorageConfig(db_path=str(bad)))

    def test_acl_metadata_revision_and_real_sqlite_restore(self):
        a=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fx.root/'a.sqlite')))
        ing=KnowledgeIngester(a)
        doc=classify_document(KnowledgeDocType.ADR,'3','adr:1','Title','Đăng nhập',metadata={'lock_version':1})
        ing.ingest(doc)
        updated=classify_document(KnowledgeDocType.ADR,'3','adr:1','Title','Đăng nhập',metadata={'lock_version':2})
        self.assertEqual(ing.ingest(updated).status,IngestionStatus.UPDATED)
        b=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fx.root/'b.sqlite')))
        self.assertTrue(b.restore_schema(a.backup_schema()).success)
        self.assertGreater(KnowledgeIngester(b).count_chunks(doc.source_hash),0)
        with b._connection() as db:self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0],'wal')
        with self.assertRaises(ValueError):b.restore_schema(a.backup_schema())

    def test_quota_provider_key_windows_and_unknown_tokens(self):
        now=time.time()
        with self.store.connect() as db:
            db.executemany('INSERT INTO gemini_usage VALUES(?,?,?)',[('provider-project',now,12),('provider-project',now-70,900),('3',now,9999)])
        policy={'project':'provider-project','model':'configured-free-model','quota':{'rpm':15,'tpm':250000,'rpd':500},'limits':{'rpm':13,'tpm':225000,'rpd':450}}
        data=get_quota_panel_data(self.store,7,3,self.service.config,policy)
        self.assertEqual(data['usage_last_60s']['rpm_reserved'],1)
        self.assertEqual(data['usage_last_60s']['input_tpm_reserved'],12)
        self.assertEqual(data['usage_today']['rpd_used'],2)
        self.assertIsNone(data['usage_last_60s']['total_tokens_remaining'])
        self.assertFalse(get_quota_panel_data(self.store,7,3)['available'])


if __name__=='__main__':unittest.main()

"""Selected Native context stays bounded while project scope and authorized RAG remain accurate."""
import copy
import json
import unittest
from unittest.mock import patch

from gateway.gemini import Gemini
from gateway.local_queries import match_query
from gateway.store import canonical
from gateway.knowledge_classifier import KnowledgeDocType,classify_document
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.knowledge_ingestion import KnowledgeIngester
from tests import test_local_queries as fixtures
from tests import test_live_agents as live
from tests.test_rag_recovery import VectorFixture


class SupervisorProjectScopeTests(unittest.TestCase):
    def test_status_breakdown_alias_stays_a_native_read_intent(self):
        self.assertEqual(match_query('thống kê trạng thái công việc'),('statuses','analyze',{}))

    def setUp(self):
        self.h=fixtures.LocalQueryTests();self.h.setUp();self.addCleanup(self.h.tearDown)
        self.sdk=live.LiveAgentsTests();self.sdk.setUp();self.addCleanup(self.sdk.doCleanups)
        for identifier in range(3,13):
            row=copy.deepcopy(self.h.state.rows[0]);row.update(id=identifier,subject=f'Synthetic scope {identifier}')
            self.h.state.rows.append(row)
        self.h.state.visible[7]=list(range(1,13));self.h.config.update(type_ids=[1],status_ids=[1,2])
        for row in self.h.state.rows:row['_embedded']={'relations':{'total':0,'_embedded':{'elements':[]}}}

    def start(self,actor,prompt,engine):
        s=self.h.service
        receipt=s.execute_actor(actor,{'action':'start_ai_run','arguments':{'engine':engine,'prompt':prompt},'idempotency_key':'scope-test'})
        claim=self.h.store.claim_run();self.assertEqual(claim['id'],receipt['result']['id'])
        return s.run_supervisor(actor,claim['id'],live=engine=='supervisor_gemini')

    def test_local_summary_distinguishes_ten_selected_from_twelve_visible_and_keeps_readback(self):
        with patch.object(self.h.service,'start_dispatcher'):
            result=self.start(7,'BA phân tích yêu cầu toàn dự án, chỉ phân tích.','supervisor')
        self.assertIn('10/12 công việc',result['text'])
        self.assertEqual(result['source_ids'],list(range(1,11)))
        run_id=result['agent_result']['run_id'];self.h.store.finish_run(7,run_id,result,'done')
        read=self.h.service.execute_actor(7,{'action':'get_ai_run','arguments':{'id':run_id}})['result']
        self.assertNotEqual(read['result'].get('status'),'stale')

    def live_context(self,prompt,actor=7,roles=None,expected_citation=12):
        s=self.h.service;(self.h.root/'gemini.json').write_text(json.dumps({'multi_agent':{'enabled':True}}))
        (self.h.root/'gemini.key').write_text('synthetic-offline-scope-key')
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.h.root/'knowledge.sqlite')));vector=VectorFixture()
        doc=classify_document(KnowledgeDocType.WORK_PACKAGE,'3','op:wp:12','Scope knowledge',
            'Scope knowledge: requirements beyond the first ten Native items.',allowed_roles=roles or ['PM'],metadata={'native_id':12,'lock_version':1})
        KnowledgeIngester(storage,vector).ingest(doc);vector.hits=[{'payload':point['payload'],'score':.9} for point in vector.points.values()]
        answer={**self.sdk.analysis,'summary':f'Synthetic scope analysis #{expected_citation}','citations':[expected_citation]}
        transport,_=self.sdk.client(answer);original=Gemini.structured;contexts=[]
        def offline(instance,*args,**kwargs):
            contexts.append(json.loads(args[0]));return original(instance,*args,**kwargs,transport=transport)
        with patch('gateway.vector_client.VectorClient',return_value=vector),patch.object(s,'start_dispatcher'),\
             patch.object(s.gemini,'settings',return_value=self.sdk.policy),patch.object(s.gemini,'validate_prompt',return_value=self.sdk.policy),\
             patch.object(self.h.native_factory,'summary',return_value={'count':12},create=True),\
             patch.object(self.h.native_factory,'sprints',return_value=[],create=True),\
             patch.object(self.h.native_factory,'collection',return_value=[],create=True),patch.object(Gemini,'structured',offline):
            result=self.start(actor,prompt,'supervisor_gemini')
        self.assertEqual(result['execution_mode'],'MOCK_TEST');self.assertFalse(result['model_used'])
        self.assertLessEqual(len(result['source_ids']),10)
        return result,contexts

    def test_global_rag_source_beyond_first_ten_enters_the_bounded_native_context(self):
        result,contexts=self.live_context('BA phân tích yêu cầu toàn dự án, chỉ phân tích.')
        self.assertIn(12,result['source_ids'])
        self.assertEqual(contexts[0]['project_context']['project_summary']['count'],12)
        self.assertIn(12,{row['id'] for row in contexts[0]['native_items']})
        self.assertTrue(contexts[0]['retrieved_knowledge'])

    def test_explicit_targets_and_document_acl_do_not_expand_to_global_rag_hits(self):
        result,contexts=self.live_context('BA phân tích yêu cầu #1, chỉ phân tích.',expected_citation=1)
        self.assertEqual(result['source_ids'],[1]);self.assertEqual(contexts[0]['retrieved_knowledge'],[])

    def test_default_developer_assignment_is_selected_before_the_ten_item_cap(self):
        self.h.state.visible[8]=list(range(1,13))
        self.h.state.rows[-1]['_links']['assignee']={'href':'/api/v3/users/8'}
        result,contexts=self.live_context('BE phân tích yêu cầu trong phạm vi được giao, chỉ phân tích.',actor=8,roles=['BE'])
        self.assertEqual(result['source_ids'],[12])
        self.assertEqual([v['id'] for v in contexts[0]['native_items']],[12])

    def test_role_restricted_knowledge_never_enters_manager_context(self):
        result,contexts=self.live_context('BA phân tích yêu cầu toàn dự án, chỉ phân tích.',roles=['QA'],expected_citation=1)
        self.assertNotIn(12,result['source_ids'])
        self.assertEqual(contexts[0]['retrieved_knowledge'],[])

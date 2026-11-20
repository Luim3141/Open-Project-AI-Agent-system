"""Production knowledge seams with isolated registered file/SQLite/vector fixtures."""
import unittest
from unittest.mock import patch
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from tests import test_allowlisted_file_knowledge as existing


class Phase4KnowledgeTests(unittest.TestCase):
    def test_answer_uses_existing_structured_provider_and_rechecks_pin_after_generation(self):
        import json
        from gateway.live_agents import LiveConfig
        class Gemini:
            calls=0
            def multi_agent_settings(self):return LiveConfig(enabled=True)
            def structured(inner,prompt,schema,**kw):
                inner.calls+=1;self.assertEqual(kw['scope'].actor_id,7);self.assertIsNone(kw['scope'].run_id)
                kw['budget'].generations+=1;kw['budget'].http_attempts+=1
                text=json.loads(prompt)['sources'][0]['text']
                return schema(supported=True,quotes=[{'source':1,'quote':text}])
        provider=Gemini();self.service.gemini=provider
        r=self.search(mode='answer');self.assertEqual(r['answerability']['state'],'SUPPORTED');self.assertTrue(r['model_used'])
        self.assertEqual(provider.calls,1)
        real=provider.structured
        def changed(*a,**kw):
            value=real(*a,**kw);self.fixture.path.write_text('source changed during inference');return value
        provider.structured=changed
        r=self.search(mode='answer');self.assertIsNone(r['answer']);self.assertEqual(r['items'],[])
        self.assertEqual(r['reason_code'],'KNOWLEDGE_SOURCE_CHANGED_DURING_GENERATION')
    def setUp(self):
        self.fixture=existing.AllowlistedFileKnowledgeTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.service=self.fixture.service;self.vector=self.fixture.vector
        class Native:
            def packages(self):return []
            def package(self,identifier):raise PermissionError('NATIVE_NOT_VISIBLE')
        self.native=Native();self.who={'user_id':7,'role':'PM'}
        self.fixture.call(self.fixture.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'indexed')
        self.vector.hits=[{'payload':p['payload'],'score':.9} for p in self.vector.points.values()]

    def search(self,**args):return self.service.knowledge(self.who,self.native,'knowledge_search',{'query':'workflow citation',**args})

    def test_generic_search_includes_registered_current_file_and_retains_search_only(self):
        r=self.search();self.assertEqual(r['items'][0]['source_id'],'file:workflow-contract')
        self.assertIsNone(r['answer'])

    def test_explicit_answer_has_exact_validated_chunk_quote(self):
        r=self.search(mode='extract');self.assertEqual(r['answerability']['state'],'EXTRACTS_AVAILABLE')
        quote=r['answer']['claims'][0]['quote'];self.assertIn(quote,self.fixture.path.read_text())
        self.assertEqual(r['answer']['claims'][0]['citation']['source_sha256'],self.fixture.source['sha256'])

    def test_revoked_role_pin_change_and_native_id_scope_never_admit_file(self):
        self.who={'user_id':9,'role':'BE'};self.assertEqual(self.search()['items'],[])
        self.who={'user_id':7,'role':'PM'};self.assertEqual(self.search(native_ids=[12])['items'],[])
        self.fixture.path.write_text('changed');self.assertEqual(self.search()['items'],[])

    def test_file_change_during_retrieval_is_rechecked_before_return(self):
        real=KnowledgeSearchEngine.search
        def changed(engine,*a,**kw):
            hits=real(engine,*a,**kw);self.fixture.path.write_text('changed after retrieval');return hits
        with patch.object(KnowledgeSearchEngine,'search',changed):self.assertEqual(self.search()['items'],[])

    def test_dense_passage_is_full_validated_chunk_and_survives_rank_fusion(self):
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fixture.store.root/'knowledge.sqlite')))
        doc=storage.query_documents('5','PM')[0]
        engine=KnowledgeSearchEngine(storage,vector_client=self.vector)
        hit=engine.search('workflow citation','5','PM',document_ids=[doc.source_hash])[0]
        self.assertEqual(hit.passage,doc.content)
        self.assertEqual(hit.chunk_hash,next(iter(self.vector.points.values()))['payload']['chunk_hash'])

    def test_many_chunks_from_one_source_do_not_starve_another_document(self):
        from gateway.knowledge_classifier import classify_document,KnowledgeDocType
        from gateway.knowledge_ingestion import KnowledgeIngester
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fixture.store.root/'knowledge.sqlite')))
        doc=storage.query_documents('5','PM')[0]
        noisy=classify_document(KnowledgeDocType.WORK_PACKAGE,'5','op:wp:13','Other source','irrelevant padding '*500,allowed_roles=['PM'],metadata={'native_id':13,'lock_version':1})
        KnowledgeIngester(storage,self.vector).ingest(noisy)
        hits=[{'payload':p['payload'],'score':.9} for p in self.vector.points.values() if p['payload']['document_id']==noisy.source_hash]+[{'payload':p['payload'],'score':.85} for p in self.vector.points.values() if p['payload']['document_id']==doc.source_hash]
        self.vector.search_dense=lambda **kw:hits[:kw['limit']]
        results=KnowledgeSearchEngine(storage,vector_client=self.vector).search('Một diễn đạt hoàn toàn khác','5','PM',limit=2,document_ids=[noisy.source_hash,doc.source_hash])
        self.assertIn(doc.source_id,[r.source_id for r in results])

    def test_literal_reference_in_a_long_question_beats_common_word_noise(self):
        import hashlib
        from gateway.knowledge_classifier import classify_document,KnowledgeDocType
        from gateway.knowledge_ingestion import KnowledgeIngester
        marker='ORBIT-RECEIPT-20261103'
        self.fixture.path.write_text('Marker '+marker+'. This fixture does not certify Owner acceptance.')
        self.fixture.source['sha256']=hashlib.sha256(self.fixture.path.read_bytes()).hexdigest()
        self.fixture.call(self.fixture.pm,'knowledge_file_ingest',{'source_key':'workflow-contract'},'revision2')
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(self.fixture.store.root/'knowledge.sqlite')))
        file_doc=storage.query_documents('5','PM')[0]
        noise=classify_document(KnowledgeDocType.WORK_PACKAGE,'5','op:wp:13','Owner acceptance','Tai lieu co ma noi gi va co chung nhan Owner acceptance khong?',allowed_roles=['PM'],metadata={'native_id':13,'lock_version':1})
        KnowledgeIngester(storage,self.vector).ingest(noise)
        self.vector.hits=[{'payload':p['payload'],'score':.9 if p['payload']['source_id']==noise.source_id else .6} for p in self.vector.points.values()]
        hits=KnowledgeSearchEngine(storage,vector_client=self.vector).search('Tài liệu có mã '+marker+' nói gì và có chứng nhận Owner acceptance không?','5','PM',limit=1,document_ids=[file_doc.source_hash,noise.source_hash])
        self.assertEqual(hits[0].source_id,'file:workflow-contract')


if __name__=='__main__':unittest.main()

"""Persistent SQLite plus synthetic vector failures; no Main data or network."""
import copy
import tempfile
import unittest
from pathlib import Path

from gateway.knowledge_classifier import classify_document, KnowledgeDocType
from gateway.knowledge_ingestion import KnowledgeIngester, IngestionStatus
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
from gateway.vector_client import VectorClient


class VectorFixture:
    enabled = True
    deterministic_uuid = VectorClient.deterministic_uuid

    def __init__(self):
        self.points = {}
        self.fail_upsert = False
        self.fail_delete = False
        self.hits = []

    def close(self):
        pass

    def embed_texts(self, texts):
        return [[0.1] * 1024 for _ in texts]

    def upsert_points(self, points):
        if self.fail_upsert:
            return False
        self.points.update({p['id']: copy.deepcopy(p) for p in points})
        return True

    def verify_points(self, points):
        return all(p['id'] in self.points and self.points[p['id']]['payload'] == p['payload'] for p in points)

    def delete_stale_points(self, source_id, project_id, doc_type, keep_ids):
        if self.fail_delete:
            return False
        self.points = {k:p for k,p in self.points.items() if k in keep_ids or
            (p['payload']['source_id'], p['payload']['project_id'], p['payload']['doc_type']) != (source_id,project_id,doc_type)}
        return True

    def delete_registered_points(self, candidates, keep_ids):
        if self.fail_delete:raise ValueError('SYNTHETIC_VECTOR_DELETE_FAILURE')
        allowed={}
        for point in candidates:
            if point['id'] not in keep_ids:allowed.setdefault(point['id'],[]).append(point['payload'])
        if any(identifier in self.points and self.points[identifier]['payload'] not in payloads for identifier,payloads in allowed.items()):
            raise ValueError('KNOWLEDGE_DELETE_PAYLOAD_MISMATCH_HOLD')
        for identifier in allowed:self.points.pop(identifier,None)

    def delete_by_source_id(self, source_id, project_id=None):
        if self.fail_delete:
            return False
        self.points = {k:p for k,p in self.points.items() if p['payload']['source_id'] != source_id or
            (project_id is not None and p['payload']['project_id'] != project_id)}
        return True

    def search_dense(self, **kwargs):
        return self.hits

    def scroll_points(self, project_id):
        return [copy.deepcopy(p) for p in self.points.values() if p['payload']['project_id']==project_id]


class RAGRecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(Path(temporary.name)/'knowledge.sqlite')))
        self.vector = VectorFixture()
        self.ingester = KnowledgeIngester(self.storage,self.vector)

    def document(self, text='Synthetic requirements for authorization.', revision=1):
        return classify_document(KnowledgeDocType.WORK_PACKAGE,'5','actor:7:wp:12','Synthetic fixture',text,
            allowed_roles=['PM'],metadata={'actor_id':7,'native_id':12,'lock_version':revision})

    def test_failed_vector_commit_is_not_reported_as_complete_and_retry_repairs(self):
        self.vector.fail_upsert=True
        first=self.ingester.ingest(self.document())
        self.assertEqual(first.status,IngestionStatus.FAILED)
        self.assertFalse(first.vector_indexed)
        self.assertEqual(self.storage.count_documents(),1)
        self.vector.fail_upsert=False
        restarted=KnowledgeIngester(self.storage,self.vector)
        repaired=restarted.ingest(self.document())
        self.assertTrue(repaired.vector_indexed)
        self.assertEqual(len(self.vector.points),repaired.chunks_count)

    def test_unchanged_document_repairs_a_missing_vector(self):
        first=self.ingester.ingest(self.document())
        self.assertTrue(first.vector_indexed)
        self.vector.points.clear()
        second=self.ingester.ingest(self.document())
        self.assertTrue(second.vector_indexed)
        self.assertEqual(len(self.vector.points),second.chunks_count)

    def test_update_keeps_old_vectors_until_new_revision_is_verified(self):
        self.ingester.ingest(self.document())
        old=copy.deepcopy(self.vector.points)
        self.vector.fail_upsert=True
        updated=self.document('A different verified revision of requirements.',2)
        result=self.ingester.ingest(updated)
        self.assertEqual(result.status,IngestionStatus.FAILED)
        self.assertEqual(self.vector.points,old)
        self.vector.fail_upsert=False
        result=KnowledgeIngester(self.storage,self.vector).ingest(updated)
        self.assertTrue(result.vector_indexed)
        self.assertTrue(all(p['payload']['document_id']==updated.source_hash for p in self.vector.points.values()))

    def test_delete_failure_retains_sqlite_until_retry_succeeds(self):
        self.ingester.ingest(self.document())
        self.vector.fail_delete=True
        self.assertFalse(self.ingester.deindex_source('actor:7:wp:12','5'))
        self.assertEqual(self.storage.count_documents(),1)
        self.vector.fail_delete=False
        self.assertTrue(self.ingester.deindex_source('actor:7:wp:12','5'))
        self.assertEqual(self.storage.count_documents(),0)
        self.assertEqual(self.vector.points,{})

    def test_orphan_and_cross_actor_dense_payloads_are_rejected(self):
        self.ingester.ingest(self.document())
        payload=copy.deepcopy(next(iter(self.vector.points.values()))['payload'])
        self.vector.hits=[{'payload':payload,'score':0.99}]
        engine=KnowledgeSearchEngine(self.storage,vector_client=self.vector)
        self.assertEqual(engine._dense_search('zebra absent','5','QA',5,actor_id=7),[])
        self.assertEqual(engine._dense_search('zebra absent','5','PM',5,actor_id=8),[])
        payload['document_id']='orphan'
        self.assertEqual(engine._dense_search('zebra absent','5','PM',5,actor_id=7),[])

    def test_dense_citation_uses_verified_native_identity_instead_of_unverified_alias(self):
        doc = self.document()
        self.ingester.ingest(doc)
        payload = copy.deepcopy(next(iter(self.vector.points.values()))['payload'])
        payload['work_package_id'] = 999
        self.vector.hits = [{'payload': payload, 'score': .99}]
        hits = KnowledgeSearchEngine(self.storage, vector_client=self.vector)._dense_search(
            'authorization requirements', '5', 'PM', 5, actor_id=7)
        self.assertEqual([hit.native_id for hit in hits], [12])

    def test_ingestion_lock_rejects_overlapping_writer_without_modifying_data(self):
        from gateway.knowledge_lock import lease
        with lease(self.storage.db_path+'.ingest.lock'):
            with self.assertRaisesRegex(ValueError,'KNOWLEDGE_BUSY'):
                self.ingester.ingest(self.document())
        self.assertEqual(self.storage.count_documents(),0)
        self.assertEqual(self.vector.points,{})

    def test_persistent_lexical_path_returns_actual_bm25_rank(self):
        self.ingester.ingest(self.document())
        hits=KnowledgeSearchEngine(self.storage).search('authorization','5','PM',actor_id=7,
            document_ids=[self.document().source_hash])
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0].match_type,'FTS_BM25')
        with self.storage._connection() as db:
            rank=db.execute("SELECT bm25(knowledge_fts) FROM knowledge_fts WHERE knowledge_fts MATCH 'authorization'").fetchone()[0]
        self.assertEqual(hits[0].score,-rank)

    def test_only_pending_idempotent_ingestion_can_retry_without_reconciliation(self):
        from gateway.store import Store
        store=Store(Path(self.storage.db_path).parent/'execution')
        payload={'action':'knowledge_ingest','arguments':{'id':12}}
        self.assertIsNone(store.begin(7,'repair',payload))
        self.assertIsNone(store.begin(7,'repair',payload))
        with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_KEY_REUSED'):
            store.begin(7,'repair',{'action':'knowledge_ingest','arguments':{'id':13}})
        mutation={'action':'comment','arguments':{'id':12,'text':'fixture'}}
        store.begin(7,'mutation',mutation)
        with self.assertRaisesRegex(ValueError,'OUTCOME_UNKNOWN'):
            store.begin(7,'mutation',mutation)

    def test_service_scopes_shared_corpus_and_rechecks_native_version_after_search(self):
        from unittest.mock import patch
        from gateway.service import Service
        from gateway.store import Store
        root=Path(self.storage.db_path).parent
        documents=[]
        for identifier,source,metadata in [(12,'op:wp:12',{}),(13,'actor:7:wp:13',{'actor_id':7}),
                (99,'actor:8:wp:99',{'actor_id':8}),(14,'op:wp:14',{})]:
            doc=classify_document(KnowledgeDocType.WORK_PACKAGE,'5',source,'Authorization fixture',
                'Authorization acceptance requirements.',allowed_roles=['PM'],
                metadata={**metadata,'native_id':identifier,'lock_version':1})
            self.ingester.ingest(doc)
            documents.append(doc)
        self.vector.hits=[{'payload':p['payload'],'score':0.9} for p in self.vector.points.values()]
        class Native:
            def packages(self):
                return [{'id':i,'lockVersion':1} for i in (12,13,99)]
            def package(self,identifier):
                return {'id':identifier,'lockVersion':2 if identifier==12 else 1}
        service=Service(Store(root),{'project_id':5},root/'workspace')
        with patch('gateway.vector_client.VectorClient',return_value=self.vector):
            result=service.knowledge({'user_id':7,'role':'PM'},Native(),'knowledge_search',{'query':'authorization'})
        self.assertEqual({p['native_id'] for p in result['items']},{13})

    def test_native_ids_filter_precedes_ranking_and_cannot_expand_visibility(self):
        from unittest.mock import patch
        from gateway.service import Service
        from gateway.store import Store
        root = Path(self.storage.db_path).parent
        for identifier in (12, 13, 99):
            self.ingester.ingest(classify_document(KnowledgeDocType.WORK_PACKAGE, '5', f'op:wp:{identifier}',
                'Authorization fixture', 'Authorization acceptance requirements.', allowed_roles=['PM'],
                metadata={'native_id': identifier, 'lock_version': 1}))
        self.vector.hits = [{'payload': p['payload'], 'score': .9} for p in self.vector.points.values()]
        class Native:
            def packages(self): return [{'id': i, 'lockVersion': 1} for i in (12, 13)]
            def package(self, identifier):
                if identifier not in (12, 13): raise PermissionError('NOT_VISIBLE')
                return {'id': identifier, 'lockVersion': 1}
        service = Service(Store(root), {'project_id': 5}, root/'workspace')
        with patch('gateway.vector_client.VectorClient', return_value=self.vector):
            result = service.knowledge({'user_id': 7, 'role': 'PM'}, Native(), 'knowledge_search',
                {'query': 'authorization', 'limit': 1, 'native_ids': [13]})
            self.assertEqual([hit['native_id'] for hit in result['items']], [13])
            self.assertRegex(result['items'][0]['document_id'], r'^[a-f0-9]{64}$')
            denied = service.knowledge({'user_id': 7, 'role': 'PM'}, Native(), 'knowledge_search',
                {'query': 'authorization', 'native_ids': [99]})
            self.assertEqual(denied['items'], [])
            for invalid in (None, [], [True], ['13'], [0], [13, 13], list(range(1, 12)), '13'):
                with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'KNOWLEDGE_NATIVE_IDS'):
                    service.knowledge({'user_id': 7, 'role': 'PM'}, Native(), 'knowledge_search',
                        {'query': 'authorization', 'native_ids': invalid})

    def test_repeated_dense_chunks_do_not_outvote_a_more_relevant_document(self):
        from gateway.knowledge_search import SearchResult
        from unittest.mock import patch
        engine=KnowledgeSearchEngine(self.storage,vector_client=self.vector)
        def hit(source):
            return SearchResult(source,source,source,'fixture',0.9,'DENSE_VECTOR',KnowledgeDocType.WORK_PACKAGE)
        with patch.object(engine,'_dense_search',return_value=[hit('best'),hit('long'),hit('long'),hit('long')]), \
                patch.object(engine,'_lexical_search',return_value=[]):
            self.assertEqual(engine.search('fixture','5','PM')[0].source_id,'best')

    def test_hybrid_snippet_shows_exact_comment_beyond_document_prefix(self):
        query = 'Retest [QA] comment proof 7391'
        doc = self.document('Retest fixture header. ' + 'Background context. ' * 15 + '\n' + query)
        self.ingester.ingest(doc)
        self.vector.hits = [{'payload':p['payload'],'score':0.95} for p in self.vector.points.values()]
        hits = KnowledgeSearchEngine(self.storage,vector_client=self.vector).search(
            query,'5','PM',actor_id=7,document_ids=[doc.source_hash])
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0].match_type,'HYBRID_RRF')
        self.assertEqual(hits[0].native_id,12)
        self.assertIn(query,hits[0].snippet)

    def test_unrelated_query_is_not_answered_from_two_common_words(self):
        doc=self.document('Mật mã đăng nhập và tài khoản nội bộ.')
        self.ingester.ingest(doc)
        self.vector.hits=[{'payload':p['payload'],'score':0.43} for p in self.vector.points.values()]
        self.assertEqual(KnowledgeSearchEngine(self.storage,vector_client=self.vector).search(
            'mật mã tàu sao Hỏa zebra absent 902178','5','PM',actor_id=7),[])

    def test_single_keyword_email_does_not_accept_unrelated_high_dense_score(self):
        doc = self.document('Route GET /healthz returns status ok.')
        self.ingester.ingest(doc)
        self.vector.hits = [{'payload': p['payload'], 'score': 0.99} for p in self.vector.points.values()]
        engine = KnowledgeSearchEngine(self.storage, vector_client=self.vector)
        self.assertEqual(engine.search('email', '5', 'PM', actor_id=7), [])
        self.assertTrue(engine.search('healthz', '5', 'PM', actor_id=7))

    def test_multiword_vietnamese_and_english_semantic_queries_keep_dense_recall(self):
        for content, query in [('Authentication authorization sign-in.', 'đăng nhập người dùng'),
                               ('Đăng nhập bằng tài khoản được cấp.', 'user sign in')]:
            with self.subTest(query=query):
                doc = self.document(content)
                self.ingester.ingest(doc)
                self.vector.hits = [{'payload': p['payload'], 'score': 0.9} for p in self.vector.points.values()]
                hits = KnowledgeSearchEngine(self.storage, vector_client=self.vector).search(
                    query, '5', 'PM', actor_id=7)
                self.assertTrue(hits)
                self.assertEqual(hits[0].match_type, 'DENSE_VECTOR')

    def test_weak_semantic_result_abstains_but_provider_outage_allows_lexical_fallback(self):
        from unittest.mock import patch
        doc=self.document('Cơ chế điều khiển không có trong dự án nội bộ.')
        self.ingester.ingest(doc)
        self.vector.hits=[{'payload':p['payload'],'score':0.42} for p in self.vector.points.values()]
        engine=KnowledgeSearchEngine(self.storage,vector_client=self.vector)
        query='Cơ chế điều khiển tàu vũ trụ sao Hải Vương không có trong dự án'
        self.assertEqual(engine.search(query,'5','PM',actor_id=7),[])
        self.assertEqual(engine.dense_state,'READY')
        with patch.object(self.vector,'embed_texts',side_effect=RuntimeError('synthetic outage')):
            self.assertTrue(engine.search('điều khiển dự án','5','PM',actor_id=7))
        self.assertEqual(engine.dense_state,'FALLBACK')

    def test_malformed_dense_response_preserves_partial_lexical_fallback(self):
        self.ingester.ingest(self.document())
        self.vector.hits = [{'payload': None, 'score': 0.99}]
        engine = KnowledgeSearchEngine(self.storage, vector_client=self.vector)
        self.assertTrue(engine.search('authorization requirements missingterm', '5', 'PM', actor_id=7))
        self.assertEqual(engine.dense_state, 'FALLBACK')

    def test_complete_lexical_match_survives_weak_or_empty_dense_results(self):
        doc = self.document('Cơ chế điều khiển không có trong dự án nội bộ.')
        self.ingester.ingest(doc)
        weak_hits = [{'payload': p['payload'], 'score': 0.42} for p in self.vector.points.values()]
        engine = KnowledgeSearchEngine(self.storage, vector_client=self.vector)
        for hits in (weak_hits, []):
            with self.subTest(hits=bool(hits)):
                self.vector.hits = hits
                results = engine.search('điều khiển dự án', '5', 'PM', actor_id=7)
                self.assertEqual([result.document_id for result in results], [doc.source_hash])
                self.assertEqual(results[0].match_type, 'FTS_BM25')
                self.assertEqual(engine.dense_state, 'READY')

    def test_partial_lexical_fallback_requires_dense_unavailable_and_resets_each_search(self):
        from unittest.mock import patch
        doc = self.document('Cơ chế điều khiển không có trong dự án nội bộ.')
        self.ingester.ingest(doc)
        query = 'Cơ chế điều khiển tàu vũ trụ sao Hải Vương không có trong dự án'
        engine = KnowledgeSearchEngine(self.storage, vector_client=self.vector)
        self.vector.hits = []
        self.assertEqual(engine.search(query, '5', 'PM', actor_id=7), [])
        self.assertEqual(engine.dense_state, 'READY')
        with patch.object(self.vector, 'embed_texts', side_effect=RuntimeError('synthetic outage')):
            self.assertTrue(engine.search(query, '5', 'PM', actor_id=7))
        self.assertEqual(engine.dense_state, 'FALLBACK')
        self.assertEqual(engine.search(query, '5', 'PM', actor_id=7), [])
        self.assertEqual(engine.dense_state, 'READY')
        self.vector.enabled = False
        self.assertTrue(engine.search(query, '5', 'PM', actor_id=7))
        self.assertEqual(engine.dense_state, 'DISABLED')
        self.assertTrue(KnowledgeSearchEngine(self.storage).search(query, '5', 'PM', actor_id=7))

    def test_native_ingestion_includes_authorized_comments_and_redacts_credentials(self):
        from gateway.service import Service
        from gateway.store import Store
        from unittest.mock import patch
        root=Path(self.storage.db_path).parent
        class Native:
            def package(self,identifier):
                return {'id':identifier,'lockVersion':2,'subject':'Comment fixture','description':{'raw':'Authorization requirements.'}}
            def collection(self,path):
                assert path=='/api/v3/work_packages/12/activities'
                return [{'id':17,'comment':{'raw':'Retest marker verified. password=synthetic-secret'}}]
        service=Service(Store(root),{'project_id':5},root/'workspace')
        with patch('gateway.vector_client.VectorClient',return_value=self.vector):
            result=service.knowledge({'user_id':7,'role':'PM'},Native(),'knowledge_ingest',{'id':12})
        self.assertTrue(result['vector_indexed'])
        doc=self.storage.query_documents('5','PM')[0]
        self.assertIn('Retest marker verified',doc.content)
        self.assertNotIn('synthetic-secret',doc.content)
        self.assertEqual(doc.metadata['activity_ids'],[17])

    def test_embedding_batches_cannot_exceed_two_or_restart_the_total_deadline(self):
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        client=VectorClient(batch_size=100)
        self.addCleanup(client.close)
        self.assertEqual(client.batch_size,2)
        response=SimpleNamespace(status_code=200,json=lambda:{'embeddings':[[0.1]*1024]*2})
        with patch('gateway.vector_client.time',SimpleNamespace(monotonic=Mock(side_effect=[0,0,91]))), \
                patch.object(client._http,'post',return_value=response) as call:
            with self.assertRaisesRegex(TimeoutError,'TOTAL_DEADLINE'):
                client._embed_texts(['one','two','three'])
            self.assertEqual(call.call_count,1)


if __name__=='__main__':
    unittest.main()

"""Only registered point identities may be removed; unknown legacy vectors survive."""
import copy
import json
import unittest
from unittest.mock import patch

import httpx

from gateway.knowledge_ingestion import KnowledgeIngester,IngestionStatus
from gateway.knowledge_storage import KnowledgeStorage
from gateway.vector_client import VectorClient
from tests import test_rag_recovery as fixtures


class RegisteredPruningTests(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.RAGRecoveryTests();self.h.setUp();self.addCleanup(self.h.doCleanups)
        self.h.ingester.ingest(self.h.document())
        self.legacy=copy.deepcopy(next(iter(self.h.vector.points.values())))
        self.legacy['id']=self.h.vector.deterministic_uuid('unregistered-same-source-legacy')
        self.legacy['payload']['document_id']='unregistered-historical-document'
        self.h.vector.points[self.legacy['id']]=copy.deepcopy(self.legacy)

    def assert_legacy_preserved(self):self.assertEqual(self.h.vector.points.get(self.legacy['id']),self.legacy)

    def test_unchanged_ingestion_does_not_delete_same_source_unregistered_point(self):
        result=self.h.ingester.ingest(self.h.document())
        self.assertTrue(result.vector_indexed);self.assert_legacy_preserved()

    def test_revision_prunes_only_registered_old_points_after_new_points_verify(self):
        old=set(self.h.vector.points)-{self.legacy['id']}
        result=self.h.ingester.ingest(self.h.document('New authorization requirements.',2))
        self.assertTrue(result.vector_indexed);self.assert_legacy_preserved()
        self.assertFalse(old & self.h.vector.points.keys())

    def test_vector_outage_then_full_storage_restart_keeps_exact_pruning_plan(self):
        old=set(self.h.vector.points)-{self.legacy['id']};doc=self.h.document('Durable changed requirements.',2)
        self.h.vector.fail_upsert=True
        self.assertEqual(self.h.ingester.ingest(doc).status,IngestionStatus.FAILED)
        self.assertTrue(old<=self.h.vector.points.keys());self.assert_legacy_preserved()
        self.h.vector.fail_upsert=False
        storage=KnowledgeStorage(self.h.storage.config)
        result=KnowledgeIngester(storage,self.h.vector).ingest(doc)
        self.assertTrue(result.vector_indexed);self.assertFalse(old & self.h.vector.points.keys());self.assert_legacy_preserved()

    def test_explicit_deindex_removes_registered_points_only(self):
        self.assertTrue(self.h.ingester.deindex_source('actor:7:wp:12','5'))
        self.assert_legacy_preserved();self.assertEqual(set(self.h.vector.points),{self.legacy['id']})

    def test_failed_stale_cleanup_is_pending_then_recovers_after_storage_restart(self):
        self.h.vector.fail_delete=True;doc=self.h.document('Cleanup failure requirements.',2)
        self.assertEqual(self.h.ingester.ingest(doc).status,IngestionStatus.FAILED)
        self.assertTrue(self.h.storage.pending_vector_cleanup(('5','WORK_PACKAGE','actor:7:wp:12')))
        self.h.vector.fail_delete=False
        storage=KnowledgeStorage(self.h.storage.config)
        self.assertTrue(KnowledgeIngester(storage,self.h.vector).ingest(doc).vector_indexed)
        self.assertFalse(storage.pending_vector_cleanup(('5','WORK_PACKAGE','actor:7:wp:12')));self.assert_legacy_preserved()

    def test_failed_same_hash_metadata_update_then_new_content_uses_registered_history(self):
        self.h.vector.fail_upsert=True
        changed=self.h.document();changed.title='New title not yet indexed';changed.metadata['lock_version']=2
        self.assertEqual(self.h.ingester.ingest(changed).status,IngestionStatus.FAILED)
        self.h.vector.fail_upsert=False
        storage=KnowledgeStorage(self.h.storage.config);doc=self.h.document('Later content after metadata indexing outage.',3)
        self.assertTrue(KnowledgeIngester(storage,self.h.vector).ingest(doc).vector_indexed)
        self.assert_legacy_preserved();self.assertEqual(len(self.h.vector.points),2)

    def transport_client(self):
        client=VectorClient(enabled=False);client._http.close();client.enabled=True;self.deletes=[];self.lose_delete_reply=False
        def transport(request):
            if request.method=='GET':return httpx.Response(200,json={'result':{'config':{'params':{'vectors':{'size':1024,'distance':'Cosine'}}}}})
            body=json.loads(request.content)
            if request.url.path.endswith('/points') and request.method=='POST':
                return httpx.Response(200,json={'result':[{'id':i,'payload':self.h.vector.points[i]['payload']} for i in body['ids'] if i in self.h.vector.points]})
            if request.url.path.endswith('/points/delete'):
                self.assertEqual(set(body),{'points'});self.deletes.append(body['points'])
                for i in body['points']:self.h.vector.points.pop(i,None)
                if self.lose_delete_reply:self.lose_delete_reply=False;raise httpx.ReadTimeout('FIXTURE_LOST_DELETE_ACK')
                return httpx.Response(200,json={'result':{'status':'completed'}})
            if request.url.path.endswith('/points') and request.method=='PUT':
                self.h.vector.points.update({p['id']:copy.deepcopy(p) for p in body['points']})
                return httpx.Response(200,json={'result':{'status':'completed'}})
            raise AssertionError(str(request.url))
        client._http=httpx.Client(transport=httpx.MockTransport(transport));client.embed_texts=lambda texts:[[0.1]*1024 for _ in texts]
        self.addCleanup(client.close);return client

    def test_real_client_exact_delete_lost_reply_and_sqlite_restart_preserve_legacy(self):
        client=self.transport_client();self.lose_delete_reply=True;doc=self.h.document('Actual client registered pruning.',2)
        self.assertEqual(KnowledgeIngester(self.h.storage,client).ingest(doc).status,IngestionStatus.FAILED)
        self.assertEqual(len(self.deletes),1);self.assert_legacy_preserved()
        storage=KnowledgeStorage(self.h.storage.config)
        self.assertTrue(KnowledgeIngester(storage,client).ingest(doc).vector_indexed)
        self.assert_legacy_preserved();self.assertFalse(storage.pending_vector_cleanup(('5','WORK_PACKAGE','actor:7:wp:12')))

    def test_real_client_validates_every_batch_before_any_delete(self):
        client=self.transport_client();points=[]
        for i in range(101):
            p={'id':client.deterministic_uuid('registered-point-'+str(i)),'payload':{'proof':i}}
            points.append(p);self.h.vector.points[p['id']]=copy.deepcopy(p)
        self.h.vector.points[points[-1]['id']]['payload']={'unregistered':'different owner'}
        with self.assertRaisesRegex(ValueError,'PAYLOAD_MISMATCH'):client.delete_registered_points(points,[])
        self.assertFalse(self.deletes);self.assert_legacy_preserved()

    def test_intent_persistence_failure_precedes_metadata_or_vector_replacement(self):
        before=copy.deepcopy(self.h.vector.points);original=self.h.document();doc=self.h.document('Must not replace without durable intent.',2)
        with patch.object(self.h.storage,'save_vector_cleanup',side_effect=RuntimeError('FIXTURE_INTENT_DISK_FAILURE')):
            with self.assertRaisesRegex(RuntimeError,'INTENT_DISK_FAILURE'):self.h.ingester.ingest(doc)
        self.assertEqual(self.h.vector.points,before)
        self.assertEqual(self.h.storage.query_documents('5')[0].source_hash,original.source_hash)

    def test_metadata_failure_retains_source_and_durable_cleanup_for_retry(self):
        before=copy.deepcopy(self.h.vector.points);doc=self.h.document('Metadata failure retains old proof.',2)
        with patch.object(self.h.storage,'store_document',return_value=False):
            self.assertEqual(self.h.ingester.ingest(doc).error,'PERSISTENCE_FAILED')
        self.assertEqual(self.h.vector.points,before)
        storage=KnowledgeStorage(self.h.storage.config)
        self.assertTrue(storage.pending_vector_cleanup(('5','WORK_PACKAGE','actor:7:wp:12')))
        with self.assertRaisesRegex(ValueError,'PENDING_VECTOR_CLEANUP'):storage.rollback_schema()
        self.assertTrue(KnowledgeIngester(storage,self.h.vector).ingest(doc).vector_indexed);self.assert_legacy_preserved()

    def test_corrupt_cross_scope_intent_cannot_select_foreign_vectors(self):
        candidate=copy.deepcopy(next(p for i,p in self.h.vector.points.items() if i!=self.legacy['id']))
        candidate.pop('vector',None);candidate['payload']['project_id']='6'
        self.h.storage.save_vector_cleanup(('5','WORK_PACKAGE','actor:7:wp:12'),[candidate])
        before=copy.deepcopy(self.h.vector.points)
        with self.assertRaisesRegex(ValueError,'PLAN_SCOPE_OR_HASH_HOLD'):self.h.ingester.ingest(self.h.document())
        self.assertEqual(self.h.vector.points,before)


if __name__=='__main__':unittest.main()

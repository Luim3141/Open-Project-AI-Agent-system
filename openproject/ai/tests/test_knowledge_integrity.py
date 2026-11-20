"""Reconciliation detects exact synthetic drift without changing any point or document."""
import copy
import unittest
from pathlib import Path

from gateway.knowledge_integrity import reconcile
from tests import test_rag_recovery as fixture


class KnowledgeIntegrityTests(unittest.TestCase):
    document=fixture.RAGRecoveryTests.document

    def setUp(self):
        fixture.RAGRecoveryTests.setUp(self)
        self.ingester.ingest(self.document())

    def audit(self,version=1):
        return reconcile(Path(self.storage.db_path).parent,5,[{'id':12,'lockVersion':version}],self.vector)

    def test_verified_reconciliation_does_not_change_data(self):
        before=copy.deepcopy(self.vector.points)
        result=self.audit()
        self.assertEqual(result['status'],'VERIFIED')
        self.assertEqual(self.vector.points,before)

    def test_exact_missing_payload_and_native_version_drift_are_reported(self):
        identifier=next(iter(self.vector.points))
        original=self.vector.points.pop(identifier)
        self.assertEqual(self.audit()['missing_point_ids'],[identifier])
        self.vector.points[identifier]=original
        self.vector.points[identifier]['payload']['chunk_text']='tampered payload'
        self.assertEqual(self.audit()['payload_mismatch_ids'],[identifier])
        self.assertEqual(self.audit(2)['stale_sources'],['actor:7:wp:12'])

    def test_unmatched_point_is_preserved_and_not_called_verified(self):
        original=copy.deepcopy(next(iter(self.vector.points.values())))
        original['id']=self.vector.deterministic_uuid('unknown')
        original['payload']['source_id']='unknown:fixture'
        self.vector.points[original['id']]=original
        result=self.audit()
        self.assertEqual(result['status'],'PARTIAL_UNMATCHED_POINTS')
        self.assertEqual(result['unmatched_points'],[{'id':original['id'],'source_id':'unknown:fixture'}])
        self.assertIn(original['id'],self.vector.points)

    def test_missing_fts_and_tampered_sqlite_source_hash_are_reported(self):
        with self.storage._connection() as db:
            db.execute('DELETE FROM knowledge_fts')
            db.execute("UPDATE knowledge_documents SET content='tampered content'")
            db.commit()
        result=self.audit()
        self.assertEqual(result['status'],'DRIFT_DETECTED')
        self.assertEqual(result['invalid_source_hashes'],['actor:7:wp:12'])
        self.assertEqual(result['fts_error_sources'],['actor:7:wp:12'])

    def test_non_pm_cannot_read_global_index_metadata(self):
        from gateway.store import Store
        from gateway.service import Service
        from tests.test_takeover_security import NativeFixture
        root=Path(self.storage.db_path).parent
        store=Store(root);token=store.issue_token(8,'BA','BA')
        service=Service(store,{'users':{'8':'BA'},'project_id':5,'gateway_mode':'native',
            'openproject_url':'http://127.0.0.1:8088'},root/'workspaces',NativeFixture)
        with self.assertRaisesRegex(PermissionError,'PM_REQUIRED'):
            service.execute(token,{'action':'knowledge_integrity','arguments':{}})

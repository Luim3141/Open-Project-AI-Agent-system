import unittest
import json
from unittest.mock import MagicMock, patch
from openproject.ai.gateway.knowledge_storage import (
    KnowledgeStorage,
    KnowledgeStorageConfig,
    MigrationResult,
    SCHEMA_NAME,
)
from openproject.ai.gateway.knowledge_classifier import (
    KnowledgeDocType,
    KnowledgeDocument,
    classify_document,
)

class TestKnowledgeStorage(unittest.TestCase):
    def setUp(self):
        # Configure storage in isolated test mode
        self.config = KnowledgeStorageConfig(
            schema_name=SCHEMA_NAME,
            enable_pgvector=False,
            is_mock=True,
        )
        self.storage = KnowledgeStorage(config=self.config)

    def test_schema_name_isolation(self):
        self.assertEqual(self.storage.schema_name, "qldapm_knowledge")
        self.assertNotEqual(self.storage.schema_name, "public")

    def test_migration_and_rollback(self):
        res = self.storage.migrate_schema()
        self.assertTrue(res.success)
        self.assertIn("qldapm_knowledge.knowledge_documents", res.tables_created)
        self.assertIn("qldapm_knowledge.knowledge_chunks", res.tables_created)

        # Verify business schema is not touched
        self.assertTrue(all(not t.startswith("public.") for t in res.tables_created))

        # Rollback
        rollback_res = self.storage.rollback_schema()
        self.assertTrue(rollback_res.success)
        self.assertEqual(len(self.storage.get_tables()), 0)

    def test_pgvector_detection_fallback(self):
        # When pgvector is unavailable, should fall back to FTS without error
        config_no_vec = KnowledgeStorageConfig(schema_name=SCHEMA_NAME, enable_pgvector=True, is_mock=True)
        storage_no_vec = KnowledgeStorage(config=config_no_vec)
        storage_no_vec.pgvector_available = False
        res = storage_no_vec.migrate_schema()
        self.assertTrue(res.success)
        self.assertFalse(storage_no_vec.has_vector_support())
        self.assertTrue(storage_no_vec.has_fts_support())

    def test_isolated_backup_and_restore(self):
        self.storage.migrate_schema()
        doc = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id="QAG3",
            source_id="docs/adr/0001.md",
            title="ADR 0001",
            content="Local multi-agent architecture.",
        )
        self.storage.store_document(doc)

        backup_data = self.storage.backup_schema()
        self.assertIn("qldapm_knowledge", backup_data["schema"])
        self.assertEqual(len(backup_data["documents"]), 1)
        self.assertEqual(backup_data["documents"][0]["source_hash"], doc.source_hash)

        # Clear and restore
        self.storage.rollback_schema()
        self.storage.migrate_schema()
        self.assertEqual(self.storage.count_documents(), 0)

        restore_res = self.storage.restore_schema(backup_data)
        self.assertTrue(restore_res.success)
        self.assertEqual(self.storage.count_documents(), 1)

    def test_crud_and_project_isolation(self):
        self.storage.migrate_schema()
        doc_qag3 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="QAG3",
            source_id="wp:101",
            title="WP 101 Task",
            content="Implement login",
            allowed_roles=["PM", "DEV"],
        )
        self.storage.store_document(doc_qag3)

        # Query by project
        results_qag3 = self.storage.query_documents(project_id="QAG3", role="DEV")
        self.assertEqual(len(results_qag3), 1)
        self.assertEqual(results_qag3[0].source_id, "wp:101")

        # Query by different role without permission
        results_qa = self.storage.query_documents(project_id="QAG3", role="QA")
        self.assertEqual(len(results_qa), 0)

        # Query by different project
        results_other = self.storage.query_documents(project_id="DEMO", role="DEV")
        self.assertEqual(len(results_other), 0)

        # Delete
        del_res = self.storage.delete_document(doc_qag3.source_hash)
        self.assertTrue(del_res)
        self.assertEqual(self.storage.count_documents(), 0)

if __name__ == '__main__':
    unittest.main()

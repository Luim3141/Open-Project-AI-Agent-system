"""Test real persistence for QLDAPM Local Second Brain across Gateway restarts."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from gateway.knowledge_storage import (
    KnowledgeStorage,
    KnowledgeStorageConfig,
    SCHEMA_NAME,
)
from gateway.knowledge_classifier import (
    KnowledgeDocType,
    KnowledgeDocument,
    classify_document,
)
from gateway.knowledge_search import KnowledgeSearchEngine


class TestSecondBrainPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_knowledge.sqlite")
        self.config = KnowledgeStorageConfig(
            schema_name=SCHEMA_NAME,
            db_path=self.db_path,
            is_mock=False,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_persistence_across_gateway_restart(self):
        """Simulate storing knowledge, stopping gateway, restarting gateway, and verifying no data loss."""
        # --- Instance 1: Store documents before restart ---
        storage1 = KnowledgeStorage(config=self.config)
        doc1 = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id="QAG3",
            source_id="docs/adr/0001-architecture.md",
            title="ADR 0001 Local Architecture",
            content="Local multi-agent architecture with zero-dependency SQLite and FTS5 persistence.",
            allowed_roles=["PM", "DEV", "BA"],
        )
        doc2 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="QAG3",
            source_id="wp:101",
            title="Work Package 101: Authentication",
            content="Strict fail-closed PM-only-write RBAC enforcement.",
            allowed_roles=["PM"],
        )
        doc3_other_proj = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id="DEMO",
            source_id="docs/adr/9999.md",
            title="Secret Project Decision",
            content="Confidential information from another project.",
            allowed_roles=["PM"],
        )

        self.assertTrue(storage1.store_document(doc1))
        self.assertTrue(storage1.store_document(doc2))
        self.assertTrue(storage1.store_document(doc3_other_proj))
        self.assertEqual(storage1.count_documents(), 3)

        # Verify DB file physically exists on disk and is non-empty
        self.assertTrue(os.path.exists(self.db_path))
        self.assertGreater(os.path.getsize(self.db_path), 0)

        # --- SIMULATE GATEWAY RESTART: Destroy storage1 completely ---
        del storage1

        # --- Instance 2: Gateway boots up fresh and connects to existing DB ---
        storage2 = KnowledgeStorage(config=self.config)
        
        # 1. Total document count must be strictly preserved
        self.assertEqual(storage2.count_documents(), 3)

        # 2. ACL check: Project QAG3, Role PM can access doc1 and doc2
        pm_results = storage2.query_documents(project_id="QAG3", role="PM")
        self.assertEqual(len(pm_results), 2)
        pm_titles = {d.title for d in pm_results}
        self.assertIn("ADR 0001 Local Architecture", pm_titles)
        self.assertIn("Work Package 101: Authentication", pm_titles)

        # 3. ACL check: Role BA can only access doc1 (allowed_roles: PM, DEV, BA)
        ba_results = storage2.query_documents(project_id="QAG3", role="BA")
        self.assertEqual(len(ba_results), 1)
        self.assertEqual(ba_results[0].title, "ADR 0001 Local Architecture")

        # 4. ACL check: Role QA is not in allowed_roles for doc1 or doc2 -> gets 0 results
        qa_results = storage2.query_documents(project_id="QAG3", role="QA")
        self.assertEqual(len(qa_results), 0)

        # 5. Project isolation: QAG3 queries must NEVER leak DEMO content
        for r in pm_results:
            self.assertNotEqual(r.project_id, "DEMO")
            self.assertNotIn("Confidential", r.content)

        # 6. FTS Search works across restart
        search_engine = KnowledgeSearchEngine(storage=storage2)
        search_results = search_engine.search(
            query="zero-dependency persistence",
            project_id="QAG3",
            role="DEV",
        )
        self.assertGreater(len(search_results), 0)
        self.assertEqual(search_results[0].title, "ADR 0001 Local Architecture")

    def test_backup_and_restore_persistence(self):
        """Test export, wipe, and restore with persistent verification."""
        storage = KnowledgeStorage(config=self.config)
        doc = classify_document(
            doc_type=KnowledgeDocType.SPRINT_REPORT,
            project_id="QAG3",
            source_id="sprint:42",
            title="Sprint 42 Report",
            content="Sprint 42 completed on schedule with zero escaped defects.",
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        )
        storage.store_document(doc)
        backup_data = storage.backup_schema()
        self.assertEqual(len(backup_data["documents"]), 1)

        # Wipe schema
        storage.rollback_schema()
        self.assertEqual(storage.count_documents(), 0)

        # Restore from backup
        restore_result = storage.restore_schema(backup_data)
        self.assertTrue(restore_result.success)
        self.assertEqual(storage.count_documents(), 1)

        # Restart gateway and verify restored data persisted
        del storage
        storage_restarted = KnowledgeStorage(config=self.config)
        self.assertEqual(storage_restarted.count_documents(), 1)
        restored_doc = storage_restarted.query_documents(project_id="QAG3", role="QA")
        self.assertEqual(len(restored_doc), 1)
        self.assertEqual(restored_doc[0].title, "Sprint 42 Report")


if __name__ == "__main__":
    unittest.main()

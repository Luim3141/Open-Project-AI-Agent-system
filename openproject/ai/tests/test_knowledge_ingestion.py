import unittest
from openproject.ai.gateway.knowledge_classifier import (
    KnowledgeDocType,
    classify_document,
)
from openproject.ai.gateway.knowledge_storage import (
    KnowledgeStorage,
    KnowledgeStorageConfig,
    SCHEMA_NAME,
)
from openproject.ai.gateway.knowledge_ingestion import (
    KnowledgeIngester,
    IngestionStatus,
    IngestionResult,
    chunk_text,
)

class TestKnowledgeIngestion(unittest.TestCase):
    def setUp(self):
        self.storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, is_mock=True))
        self.storage.migrate_schema()
        self.ingester = KnowledgeIngester(storage=self.storage, chunk_size=200, chunk_overlap=30)

    def test_chunking_deterministic_and_bounded(self):
        text = "Paragraph 1: Core system architecture for 5 LAN users. " * 5
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
        self.assertGreater(len(chunks), 1)
        for i, chk in enumerate(chunks):
            self.assertEqual(chk["chunk_index"], i)
            self.assertTrue(chk["chunk_hash"])
            self.assertLessEqual(len(chk["chunk_text"]), 150)

    def test_idempotent_ingest_twice(self):
        doc = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id="QAG3",
            source_id="docs/adr/0002.md",
            title="ADR 0002: Local n8n",
            content="Use local self-hosted n8n Community edition without enterprise features.",
        )

        # 1st ingestion: CREATED
        res1 = self.ingester.ingest(doc)
        self.assertEqual(res1.status, IngestionStatus.CREATED)
        self.assertEqual(self.storage.count_documents(), 1)
        initial_chunks = self.ingester.count_chunks(doc.source_hash)

        # 2nd ingestion: SKIPPED_UNCHANGED (No duplicates)
        res2 = self.ingester.ingest(doc)
        self.assertEqual(res2.status, IngestionStatus.SKIPPED_UNCHANGED)
        self.assertEqual(self.storage.count_documents(), 1)
        self.assertEqual(self.ingester.count_chunks(doc.source_hash), initial_chunks)

    def test_update_revision_changes_hash(self):
        doc_v1 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="QAG3",
            source_id="wp:105",
            title="Task 105",
            content="Initial version description.",
            metadata={"lock_version": 1},
        )
        res1 = self.ingester.ingest(doc_v1)
        self.assertEqual(res1.status, IngestionStatus.CREATED)

        # Revision v2 with updated content
        doc_v2 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="QAG3",
            source_id="wp:105",
            title="Task 105",
            content="Updated version description with new AC and technical specs.",
            metadata={"lock_version": 2},
        )
        res2 = self.ingester.ingest(doc_v2)
        self.assertEqual(res2.status, IngestionStatus.UPDATED)
        self.assertEqual(self.storage.count_documents(), 1)

    def test_deindex_source_policy(self):
        doc = classify_document(
            doc_type=KnowledgeDocType.COMMENT,
            project_id="QAG3",
            source_id="wp:105:comment:1",
            title="Comment 1",
            content="This is a temporary discussion comment.",
        )
        self.ingester.ingest(doc)
        self.assertEqual(self.storage.count_documents(), 1)

        # Deindex policy
        deindex_ok = self.ingester.deindex_source("wp:105:comment:1")
        self.assertTrue(deindex_ok)
        self.assertEqual(self.storage.count_documents(), 0)
        self.assertEqual(self.ingester.count_chunks(doc.source_hash), 0)

    def test_acl_metadata_propagation(self):
        doc = classify_document(
            doc_type=KnowledgeDocType.SPRINT_REPORT,
            project_id="QAG3",
            source_id="sprint:report:1",
            title="Confidential Sprint Review",
            content="Sprint 1 review with team capacity notes.",
            allowed_roles=["PM"],
        )
        self.ingester.ingest(doc)

        stored_docs = self.storage.query_documents(project_id="QAG3", role="PM")
        self.assertEqual(len(stored_docs), 1)
        self.assertEqual(stored_docs[0].allowed_roles, ["PM"])

        # Role without permission
        denied_docs = self.storage.query_documents(project_id="QAG3", role="FE")
        self.assertEqual(len(denied_docs), 0)

if __name__ == '__main__':
    unittest.main()

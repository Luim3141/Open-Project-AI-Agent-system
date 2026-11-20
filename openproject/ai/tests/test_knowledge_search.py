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
)
from openproject.ai.gateway.knowledge_search import (
    KnowledgeSearchEngine,
    SearchResult,
)

class TestKnowledgeSearch(unittest.TestCase):
    def setUp(self):
        self.storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, is_mock=True))
        self.storage.migrate_schema()
        self.ingester = KnowledgeIngester(storage=self.storage)
        self.search_engine = KnowledgeSearchEngine(storage=self.storage, ingester=self.ingester)

        # Ingest test docs
        doc1 = classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id="QAG3",
            source_id="docs/architecture.md",
            title="Local Docker Multi-Agent System Architecture",
            content="This document describes the 5 LAN user setup with Python gateway and local OpenProject.",
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        )
        doc2 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="QAG3",
            source_id="wp:201",
            title="Authentication Login Screen Bug",
            content="Users on Windows 11 cannot submit the login form when username contains dots.",
            allowed_roles=["PM", "FE", "QA"],
            metadata={"native_id": 201, "lock_version": 3},
        )
        doc3 = classify_document(
            doc_type=KnowledgeDocType.SPRINT_REPORT,
            project_id="QAG3",
            source_id="sprint:report:1",
            title="Sprint 1 Risk Assessment and Capacity",
            content="Confidential review: FE capacity reduced due to sickness. PM only notes.",
            allowed_roles=["PM"],
            metadata={"native_id": 999, "lock_version": 1},
        )
        doc4 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="DEMO",
            source_id="wp:301",
            title="Demo Task Outside QAG3",
            content="Should never leak into QAG3 search results.",
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        )
        self.ingester.ingest(doc1)
        self.ingester.ingest(doc2)
        self.ingester.ingest(doc3)
        self.ingester.ingest(doc4)

    def test_fts_keyword_search_ranking(self):
        # Searching for "Authentication Login" should find wp:201
        results = self.search_engine.search(query="Authentication Login", project_id="QAG3", role="FE")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].source_id, "wp:201")
        self.assertEqual(results[0].native_id, 201)
        self.assertEqual(results[0].lock_version, 3)
        self.assertIn("FTS", results[0].match_type)

    def test_strict_project_and_role_acl_filtering(self):
        # 1. FE cannot see PM-only sprint report
        results_fe = self.search_engine.search(query="Capacity Risk Assessment", project_id="QAG3", role="FE")
        for r in results_fe:
            self.assertNotEqual(r.source_id, "sprint:report:1")

        # 2. PM can see sprint report
        results_pm = self.search_engine.search(query="Capacity Risk Assessment", project_id="QAG3", role="PM")
        pm_sources = [r.source_id for r in results_pm]
        self.assertIn("sprint:report:1", pm_sources)

        # 3. Cross-project isolation: QAG3 search never returns DEMO project docs
        results_qag3 = self.search_engine.search(query="Demo Task", project_id="QAG3", role="PM")
        self.assertEqual(len(results_qag3), 0)

    def test_zero_paid_embedding_calls(self):
        # Ensure search operates locally without external API consumption
        self.assertEqual(self.search_engine.remote_embedding_calls_count, 0)
        self.search_engine.search(query="Architecture 5 users", project_id="QAG3", role="BA")
        self.assertEqual(self.search_engine.remote_embedding_calls_count, 0)

    def test_empty_or_no_match(self):
        results = self.search_engine.search(query="NonexistentKeywordXYZ999", project_id="QAG3", role="PM")
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()

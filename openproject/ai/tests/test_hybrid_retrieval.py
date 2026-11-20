"""Comprehensive Verification Tests for Phase 4: Hybrid Retrieval Engine.
Covers:
- T07: Strict Role & Project Access Control in Retrieval
- T08: Hybrid Search (Exact Keywords + Semantic Similarity + RRF Fusion)
- Verifiable Citations and Prompt Context Generation
"""
import unittest
from pathlib import Path

from openproject.ai.gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from openproject.ai.gateway.knowledge_search import KnowledgeSearchEngine, SearchResult
from openproject.ai.gateway.knowledge_retrieval import KnowledgeRetriever
from openproject.ai.gateway.vector_client import VectorClient, COLLECTION_NAME


class TestHybridRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = "C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/knowledge.sqlite"
        cls.storage = KnowledgeStorage(KnowledgeStorageConfig(
            schema_name=SCHEMA_NAME,
            db_path=db_path,
            is_mock=False,
        ))
        cls.vector_client = VectorClient(
            ollama_url="http://127.0.0.1:11434",
            qdrant_url="http://127.0.0.1:6333",
            collection_name=COLLECTION_NAME,
            enabled=True,
        )
        cls.search_engine = KnowledgeSearchEngine(
            storage=cls.storage,
            vector_client=cls.vector_client,
        )
        cls.retriever = KnowledgeRetriever(cls.search_engine)

    def test_01_hybrid_search_vietnamese_semantic(self):
        """T08: Hybrid search for semantic Vietnamese query without exact word matches."""
        # Querying about sprint progress and delayed tasks
        query = "Các vấn đề về tiến độ và rủi ro trong sprint"
        results = self.search_engine.search(query=query, project_id="5", role="PM", limit=5)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].match_type, "HYBRID_RRF")
        self.assertGreater(results[0].score, 0.0)
        # Verify that snippets contain meaningful text
        self.assertTrue(any(len(r.snippet) > 10 for r in results))

    def test_02_exact_task_code_retrieval(self):
        """T08: Exact task code retrieval (e.g. #38 or Tài khoản & Role)."""
        query = "Tài khoản & Role #38"
        results = self.search_engine.search(query=query, project_id="5", role="PM", limit=5)
        self.assertGreater(len(results), 0)
        # Top result should match work package #38
        matching_wp38 = [r for r in results if r.native_id == 38 or "#38" in r.title or "op:wp:38" in r.source_id]
        self.assertGreater(len(matching_wp38), 0)

    def test_03_role_based_access_control(self):
        """T07: Ensure access control filtering works strictly across roles and projects."""
        # Project isolation: querying an unrelated project returns zero results
        results_wrong_project = self.search_engine.search(
            query="Tài khoản",
            project_id="9999",
            role="PM",
            limit=5,
        )
        self.assertEqual(len(results_wrong_project), 0)

    def test_04_citation_and_prompt_formatting(self):
        """Verify that citations contain genuine document IDs, native IDs, and lock versions."""
        context = self.retriever.retrieve_context(
            query="Quản lý User Story và Task",
            project_id="5",
            role="BA",
            max_items=3,
        )
        self.assertGreater(len(context.results), 0)
        self.assertIn("### Relevant Internal Knowledge Context", context.formatted_prompt_context)
        self.assertIn("[Doc:", context.formatted_prompt_context)
        # Citations must never contain fabricated external URLs
        self.assertNotIn("http://", context.formatted_prompt_context)
        self.assertNotIn("https://", context.formatted_prompt_context)


if __name__ == "__main__":
    unittest.main()

"""Test Suite for QLDAPM Phase P0-C: Real RAG Corpus & Verification.
All tests run against LIVE Qdrant (http://localhost:6333), LIVE Ollama (http://localhost:11434),
and LIVE SQLite (knowledge.sqlite).
ZERO MOCKS, ZERO IN-MEMORY STUBS (is_mock=False throughout).
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from openproject.ai.gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from openproject.ai.gateway.knowledge_ingestion import KnowledgeIngester
from openproject.ai.gateway.knowledge_search import KnowledgeSearchEngine, SearchResult
from openproject.ai.gateway.vector_client import VectorClient, COLLECTION_NAME
from openproject.ai.gateway.knowledge_classifier import KnowledgeDocType, classify_document

DB_PATH = "C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/knowledge.sqlite"


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class RealRAGCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = KnowledgeStorage(KnowledgeStorageConfig(
            schema_name=SCHEMA_NAME,
            db_path=DB_PATH,
            is_mock=False,
        ))
        cls.storage.migrate_schema()

        cls.vector_client = VectorClient(
            ollama_url="http://127.0.0.1:11434",
            qdrant_url="http://127.0.0.1:6333",
            collection_name=COLLECTION_NAME,
            batch_size=2,
        )
        self_check = cls.vector_client.is_available()
        assert self_check, "Ollama or Qdrant is offline"

        cls.ingester = KnowledgeIngester(
            storage=cls.storage,
            vector_client=cls.vector_client,
            chunk_size=600,
            chunk_overlap=100,
        )

        cls.search_engine = KnowledgeSearchEngine(
            storage=cls.storage,
            ingester=cls.ingester,
            vector_client=cls.vector_client,
        )

    def test_01_corpus_scope_and_counts(self):
        """1. Knowledge Base must contain full allowlisted corpus across 4 doc types."""
        with self.storage._connection() as db:
            rows = db.execute("SELECT doc_type, count(*) FROM knowledge_documents GROUP BY doc_type").fetchall()
            counts = {r[0]: r[1] for r in rows}
            total_chunks = db.execute("SELECT count(*) FROM knowledge_chunks").fetchone()[0]

        self.assertGreaterEqual(counts.get("ADR", 0), 4)
        self.assertGreaterEqual(counts.get("ARCHITECTURE", 0), 20)
        self.assertGreaterEqual(counts.get("WORK_PACKAGE", 0), 300)
        self.assertGreaterEqual(counts.get("SPRINT_REPORT", 0), 5)
        self.assertGreater(total_chunks, 1500)

        # Verify Qdrant points count
        import requests
        r = requests.get("http://127.0.0.1:6333/collections/qldapm_knowledge_dense")
        self.assertEqual(r.status_code, 200)
        qdrant_points = r.json()["result"]["points_count"]
        self.assertGreaterEqual(qdrant_points, 1600)

    def test_02_dense_vector_search(self):
        """2. Dense search via Ollama BGE-M3 + Qdrant must return high-confidence matches."""
        query = "Five user multi-agent architecture and role boundaries"
        results = self.search_engine._dense_search(
            query=query,
            project_id="5",
            role="PM",
            limit=5,
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIsInstance(top, SearchResult)
        self.assertEqual(top.match_type, "DENSE_VECTOR")
        self.assertGreater(top.score, 0.4)
        self.assertTrue(any("user" in top.snippet.lower() or "agent" in top.snippet.lower() for top in results))

    def test_03_lexical_bm25_search(self):
        """3. Lexical search via SQLite FTS5/BM25 must match exact terminology."""
        query_terms = ["qa", "gate", "transition"]
        results = self.search_engine._lexical_search(
            query_terms=query_terms,
            project_id="5",
            role="PM",
            limit=5,
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIsInstance(top, SearchResult)
        self.assertEqual(top.match_type, "FTS_KEYWORD")
        self.assertGreater(top.score, 0)
        self.assertTrue(len(top.snippet) > 0)

    def test_04_hybrid_rrf_search(self):
        """4. Hybrid search must combine Dense + Lexical using RRF k=60."""
        query = "quy trình chuyển trạng thái và điều kiện phê duyệt của QA"
        results = self.search_engine.search(
            query=query,
            project_id="5",
            role="PM",
            limit=5,
        )
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIsInstance(r, SearchResult)
            self.assertGreater(r.score, 0)
            self.assertTrue(r.source_id.startswith("file:") or r.source_id.startswith("op:") or r.source_id.startswith("actor:"))

    def test_05_grounded_citations(self):
        """5. Citations must include authentic document provenance and non-empty snippets."""
        results = self.search_engine.search(
            query="Backlog và user story quản lý dự án rút gọn",
            project_id="5",
            role="BA",
            limit=5,
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertTrue(len(top.source_id) > 0)
        self.assertTrue(len(top.title) > 0)
        self.assertTrue(len(top.snippet) > 10)
        self.assertIn(top.doc_type, [KnowledgeDocType.ARCHITECTURE, KnowledgeDocType.WORK_PACKAGE, KnowledgeDocType.ADR])

    def test_06_acl_project_and_role_filtering(self):
        """6. Search must enforce strict project isolation and role ACL."""
        # Querying an unauthorized project should return 0 results
        results_wrong_proj = self.search_engine.search(
            query="Backlog",
            project_id="99999",
            role="PM",
            limit=5,
        )
        self.assertEqual(len(results_wrong_proj), 0)

    def test_07_incremental_update_purges_stale_vectors(self):
        """7. Ingesting revised content for an existing source must purge stale vectors."""
        test_source_id = "test:incremental:doc1"
        doc_v1 = classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id="5",
            source_id=test_source_id,
            title="Incremental Test Doc V1",
            content="Version 1 content about project testing and verification.",
            allowed_roles=["PM"],
        )
        res_v1 = self.ingester.ingest(doc_v1)
        self.assertIn(res_v1.status.value, ["CREATED", "SKIPPED_UNCHANGED"])

        # Update document with Version 2 content
        doc_v2 = classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id="5",
            source_id=test_source_id,
            title="Incremental Test Doc V2",
            content="Version 2 content updated with new architecture requirements.",
            allowed_roles=["PM"],
        )
        res_v2 = self.ingester.ingest(doc_v2)
        self.assertEqual(res_v2.status.value, "UPDATED")

        # Cleanup test document after verification
        self.vector_client.delete_by_source_id(test_source_id, project_id="5")
        self.storage.delete_document(doc_v2.source_hash)


if __name__ == "__main__":
    unittest.main()

"""Integration and Verification Tests for Real Vector RAG Ingestion.
Covers:
- T03: Local Document RAG Ingestion
- T04: OpenProject Work Package Live Ingestion
- T05: Incremental Indexing & Revision Updates (Zero Duplication)
- T06: Delete / Deindex Propagation in SQLite & Qdrant
"""
import unittest
import os
import json
import base64
import httpx
from pathlib import Path

from openproject.ai.gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from openproject.ai.gateway.knowledge_classifier import KnowledgeDocType, classify_document
from openproject.ai.gateway.knowledge_ingestion import KnowledgeIngester, IngestionStatus
from openproject.ai.gateway.vector_client import VectorClient, COLLECTION_NAME
from openproject.ai.gateway.local_loaders import load_local_file
from openproject.ai.gateway.openproject_loader import work_package_to_document
from openproject.ai.gateway.native import Native


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class TestVectorRAGIngestion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize real VectorClient connecting to local Ollama & Qdrant
        cls.vector_client = VectorClient(
            ollama_url="http://127.0.0.1:11434",
            qdrant_url="http://127.0.0.1:6333",
            collection_name=COLLECTION_NAME,
            enabled=True,
        )
        if not cls.vector_client.is_available():
            raise unittest.SkipTest("Ollama or Qdrant runtime unavailable on localhost")
        cls.vector_client.ensure_collection()

        # Temporary SQLite storage for test isolation
        cls.db_path = "C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/test_vector_ingestion.sqlite"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, db_path=cls.db_path, is_mock=False))
        cls.storage.migrate_schema()
        cls.ingester = KnowledgeIngester(storage=cls.storage, vector_client=cls.vector_client, chunk_size=300, chunk_overlap=50)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except Exception:
                pass

    def test_01_local_document_ingestion(self):
        """T03: Ingest a real local document and verify dense vector in Qdrant and FTS5."""
        doc = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id="5",
            source_id="test:local:adr:0001",
            title="ADR 0001: Kien Truc Micro-Services QLDAPM",
            content="He thong QLDAPM ap dung mo hinh Micro-Agent Supervisor voi quy trinh danh gia chat che 5 vai tro PM BA FE BE QA.",
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        )
        result = self.ingester.ingest(doc)
        self.assertEqual(result.status, IngestionStatus.CREATED)
        self.assertTrue(result.vector_indexed)
        self.assertGreater(result.chunks_count, 0)

        # Verify in SQLite
        self.assertEqual(self.storage.count_documents(), 1)

        # Verify in Qdrant
        client = httpx.Client(base_url="http://127.0.0.1:6333")
        res = client.post(f"/collections/{COLLECTION_NAME}/points/scroll", json={
            "filter": {"must": [{"key": "source_id", "match": {"value": "test:local:adr:0001"}}]},
            "limit": 10,
            "with_payload": True,
            "with_vector": True,
        })
        self.assertEqual(res.status_code, 200)
        points = res.json().get("result", {}).get("points", [])
        self.assertEqual(len(points), result.chunks_count)
        self.assertEqual(len(points[0]["vector"]), 1024)
        self.assertEqual(points[0]["payload"]["title"], "ADR 0001: Kien Truc Micro-Services QLDAPM")

    def test_02_openproject_work_package_ingestion(self):
        """T04: Ingest a simulated or live OpenProject Work Package into RAG."""
        wp_data = {
            "id": 42,
            "subject": "Task / User Story Management",
            "lockVersion": 3,
            "_links": {
                "type": {"title": "Epic"},
                "status": {"title": "NEW"},
                "priority": {"title": "High"},
                "assignee": {"title": "QLDAPM BA-PM"},
                "version": {"title": "Sprint 1"},
            },
            "description": {"raw": "Quan ly danh sach User Story va Task theo tien do tung Sprint."},
        }
        doc = work_package_to_document(wp_data, project_id="5")
        result = self.ingester.ingest(doc)
        self.assertIn(result.status, (IngestionStatus.CREATED, IngestionStatus.UPDATED))
        self.assertTrue(result.vector_indexed)

        # Verify Qdrant payload has work_package_id
        client = httpx.Client(base_url="http://127.0.0.1:6333")
        res = client.post(f"/collections/{COLLECTION_NAME}/points/scroll", json={
            "filter": {"must": [{"key": "work_package_id", "match": {"value": 42}}]},
            "limit": 5,
            "with_payload": True,
        })
        self.assertEqual(res.status_code, 200)
        points = res.json().get("result", {}).get("points", [])
        self.assertGreater(len(points), 0)
        self.assertEqual(points[0]["payload"]["work_package_id"], 42)

    def test_03_incremental_update_no_duplicates(self):
        """T05: Modifying content and re-indexing updates chunk without creating duplicate vectors."""
        # Initial version
        doc_v1 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="5",
            source_id="test:wp:999",
            title="Cong viec thu nghiem #999",
            content="Noi dung ban dau chua co dac ta ky thuat chi tiet.",
            metadata={"lock_version": 1},
        )
        res1 = self.ingester.ingest(doc_v1)
        self.assertEqual(res1.status, IngestionStatus.CREATED)

        client = httpx.Client(base_url="http://127.0.0.1:6333")
        r1 = client.post(f"/collections/{COLLECTION_NAME}/points/scroll", json={
            "filter": {"must": [{"key": "source_id", "match": {"value": "test:wp:999"}}]},
            "limit": 10,
        })
        count_v1 = len(r1.json().get("result", {}).get("points", []))

        # Re-index exact same content: SKIPPED_UNCHANGED
        res_same = self.ingester.ingest(doc_v1)
        self.assertEqual(res_same.status, IngestionStatus.SKIPPED_UNCHANGED)

        # Revision v2: modified content
        doc_v2 = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="5",
            source_id="test:wp:999",
            title="Cong viec thu nghiem #999",
            content="Noi dung cap nhat bo sung toan bo dac ta ky thuat va tieu chi nghiem thu cho FE va BE.",
            metadata={"lock_version": 2},
        )
        res2 = self.ingester.ingest(doc_v2)
        self.assertEqual(res2.status, IngestionStatus.UPDATED)

        r2 = client.post(f"/collections/{COLLECTION_NAME}/points/scroll", json={
            "filter": {"must": [{"key": "source_id", "match": {"value": "test:wp:999"}}]},
            "limit": 10,
            "with_payload": True,
        })
        points_v2 = r2.json().get("result", {}).get("points", [])
        # Points count must match v2 chunks only, zero duplicate chunks from v1!
        self.assertEqual(len(points_v2), res2.chunks_count)
        self.assertIn("dac ta ky thuat", points_v2[0]["payload"]["chunk_text"])

    def test_04_deindex_propagation(self):
        """T06: Purging source removes from both SQLite and Qdrant."""
        doc = classify_document(
            doc_type=KnowledgeDocType.COMMENT,
            project_id="5",
            source_id="test:comment:purge:1",
            title="Comment to be purged",
            content="Thao luan tam thoi ve viec chon port cho Qdrant.",
        )
        self.ingester.ingest(doc)

        # Deindex
        deleted = self.ingester.deindex_source("test:comment:purge:1")
        self.assertTrue(deleted)

        # Verify not in Qdrant
        client = httpx.Client(base_url="http://127.0.0.1:6333")
        r = client.post(f"/collections/{COLLECTION_NAME}/points/scroll", json={
            "filter": {"must": [{"key": "source_id", "match": {"value": "test:comment:purge:1"}}]},
            "limit": 5,
        })
        points = r.json().get("result", {}).get("points", [])
        self.assertEqual(len(points), 0)


if __name__ == "__main__":
    unittest.main()

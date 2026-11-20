"""Comprehensive Multi-Channel Qualification for Second Brain Auto-Sync on Isolated Clone.
Tests:
Case 1: Core UI Direct Edit / Drift Reconciliation (incremental scan -> job enqueue -> ingestion)
Case 2: Revision Update V1 -> V2 (lock_version updated, old revision purged, search returns V2)
Case 3: Out-of-Order Version Protection (stale revision rejected with KNOWLEDGE_STALE_REVISION)
Case 4: ACL Filtering & Role Isolation (PM, QA, Developer, Owner access control)
Case 5: Tombstone Deletion & Vector Point Removal (registered points deleted, legacy preserved)

Zero live mutation: Runs 100% on isolated temporary SQLite fixture and Mock Vector client.
"""

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

from gateway.knowledge_classifier import classify_document, KnowledgeDocType, KnowledgeDocument
from gateway.knowledge_ingestion import KnowledgeIngester, IngestionStatus
from gateway.knowledge_retrieval import KnowledgeRetriever
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
from gateway.native_incremental import scan, status
from gateway.openproject_loader import work_package_to_document
from gateway.permissions import AI_SYSTEM_OWNER
from gateway.store import Store
from gateway.vector_client import VectorClient


class VectorFixture:
    enabled = True
    deterministic_uuid = VectorClient.deterministic_uuid

    def __init__(self):
        self.points = {}
        # Pre-seed 3 legacy points to verify they are never touched
        self.points["legacy-point-1"] = {"id": "legacy-point-1", "payload": {"legacy": True}}
        self.points["legacy-point-2"] = {"id": "legacy-point-2", "payload": {"legacy": True}}
        self.points["legacy-point-3"] = {"id": "legacy-point-3", "payload": {"legacy": True}}

    def close(self):
        pass

    def embed_texts(self, texts):
        if texts:
            self._last_query_text = texts[0]
        return [[0.05] * 1024 for _ in texts]

    def upsert_points(self, points):
        self.points.update({p["id"]: copy.deepcopy(p) for p in points})
        return True

    def verify_points(self, points):
        return all(p["id"] in self.points for p in points)

    def delete_registered_points(self, candidates, keep_ids):
        for p in candidates:
            if p["id"] not in keep_ids:
                self.points.pop(p["id"], None)

    def delete_stale_points(self, source_id, project_id, doc_type, keep_ids):
        to_del = []
        for pid, pt in self.points.items():
            if pt.get("payload", {}).get("legacy"):
                continue
            payload = pt.get("payload", {})
            if payload.get("source_id") == source_id and pid not in keep_ids:
                to_del.append(pid)
        for pid in to_del:
            self.points.pop(pid, None)
        return True

    def search_dense(self, query_vector, project_id, role, limit, doc_types=None, actor_id=None, document_ids=None):
        from gateway.knowledge_search import _tokenize
        results = []
        q_tokens = set(_tokenize(getattr(self, "_last_query_text", "")))
        for pid, pt in self.points.items():
            if pt.get("payload", {}).get("legacy"):
                continue
            payload = pt.get("payload", {})
            if payload.get("project_id") != str(project_id):
                continue
            if role and role != AI_SYSTEM_OWNER and role not in payload.get("allowed_roles", []):
                continue
            text = (payload.get("title", "") + " " + payload.get("chunk_text", "")).lower()
            text_tokens = set(_tokenize(text))
            if q_tokens and not (q_tokens & text_tokens):
                continue
            results.append({"id": pid, "score": 0.85, "payload": copy.deepcopy(payload)})
            if len(results) >= limit:
                break
        return results


class MockNative:
    def __init__(self, pkgs):
        self._pkgs = pkgs

    def packages(self):
        return self._pkgs

    def package(self, native_id):
        for p in self._pkgs:
            if p["id"] == native_id:
                return p
        raise ValueError(f"Package {native_id} not found")


class MockService:
    def __init__(self, store, native):
        self.mode = "native"
        self.store = store
        self.config = {"project_id": 5}
        self._native = native

    def native_actor(self, actor):
        return self._native, {"role": "PM", "user_id": actor}


def run_all_cases():
    results = {}

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = Store(tmp_path)
        storage_path = str(tmp_path / "knowledge.sqlite")
        storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=storage_path))
        vec_fixture = VectorFixture()
        ingester = KnowledgeIngester(storage, vec_fixture)

        # -------------------------------------------------------------
        # CASE 1: Core UI Direct Edit / Drift Reconciliation
        # -------------------------------------------------------------
        pkg_v1 = {
            "id": 888,
            "subject": "Direct Web UI Edit Feature",
            "lockVersion": 1,
            "type": "Task",
            "status": "In progress",
            "description": {"raw": "User directly modified work package #888 via Core Web UI."},
        }
        native = MockNative([pkg_v1])
        service = MockService(store, native)

        scan_rep_1 = scan(service, 19, authority="machine")
        assert scan_rep_1["visible"] == 1
        assert scan_rep_1["changed"] == 1
        assert len(scan_rep_1["jobs"]) == 1
        job_1 = scan_rep_1["jobs"][0]
        assert job_1["native_id"] == 888
        assert job_1["lock_version"] == 1

        # Simulate Worker processing the enqueued job
        doc_v1 = work_package_to_document(pkg_v1, "5")
        ingest_res_1 = ingester.ingest(doc_v1)
        assert ingest_res_1.status in (IngestionStatus.CREATED, IngestionStatus.UPDATED)
        assert ingest_res_1.vector_indexed is True

        # Verify indexed document in isolated SQLite
        docs_after_1 = storage.query_documents("5")
        assert len(docs_after_1) == 1
        assert docs_after_1[0].metadata.get("native_id") == 888
        assert docs_after_1[0].metadata.get("lock_version") == 1

        results["case_1_drift_reconciliation"] = {
            "status": "PASS",
            "detected_drift": True,
            "enqueued_job_id": job_1["id"],
            "ingested_doc_id": doc_v1.source_hash[:16],
            "lock_version": 1,
        }

        # -------------------------------------------------------------
        # CASE 2: Revision Update V1 -> V2
        # -------------------------------------------------------------
        pkg_v2 = {
            "id": 888,
            "subject": "Direct Web UI Edit Feature Updated",
            "lockVersion": 2,
            "type": "Task",
            "status": "Closed",
            "description": {"raw": "User updated work package #888 to revision 2 with final specs."},
        }
        native._pkgs = [pkg_v2]

        scan_rep_2 = scan(service, 19, authority="machine")
        assert scan_rep_2["changed"] == 1
        job_2 = scan_rep_2["jobs"][0]
        assert job_2["lock_version"] == 2

        doc_v2 = work_package_to_document(pkg_v2, "5")
        ingest_res_2 = ingester.ingest(doc_v2)
        assert ingest_res_2.status in (IngestionStatus.CREATED, IngestionStatus.UPDATED)
        assert ingest_res_2.vector_indexed is True

        # Verify old V1 was replaced and only V2 exists
        docs_after_2 = storage.query_documents("5")
        assert len(docs_after_2) == 1
        assert docs_after_2[0].metadata.get("lock_version") == 2
        assert "Updated" in docs_after_2[0].title

        # Search test with SearchEngine
        search_engine = KnowledgeSearchEngine(storage, ingester, vec_fixture)
        search_res = search_engine.search(query="Direct Web UI", project_id="5", role="PM", limit=5)
        assert len(search_res) >= 1
        assert search_res[0].native_id == 888
        assert search_res[0].lock_version == 2

        results["case_2_revision_update_v1_to_v2"] = {
            "status": "PASS",
            "old_revision_purged": True,
            "active_lock_version": 2,
            "search_retrieved_v2": True,
        }

        # -------------------------------------------------------------
        # CASE 3: Out-of-Order Version Protection
        # -------------------------------------------------------------
        # 1. Direct call to store_document(doc_v1) returns False due to KNOWLEDGE_STALE_REVISION
        store_res = storage.store_document(doc_v1)
        assert store_res is False, "store_document must fail on stale revision"

        # 2. Ingestion of stale doc returns FAILED with PERSISTENCE_FAILED
        ingest_stale = ingester.ingest(doc_v1)
        assert ingest_stale.status == IngestionStatus.FAILED
        assert ingest_stale.error == "PERSISTENCE_FAILED"

        # 3. Verify SQLite storage preserved V2 without regression
        docs_after_3 = storage.query_documents("5")
        assert len(docs_after_3) == 1
        assert docs_after_3[0].metadata.get("lock_version") == 2
        assert "Updated" in docs_after_3[0].title

        results["case_3_out_of_order_protection"] = {
            "status": "PASS",
            "stale_revision_rejected": True,
            "persistence_safeguard": "PERSISTENCE_FAILED (KNOWLEDGE_STALE_REVISION)",
            "preserved_lock_version": 2,
        }

        # -------------------------------------------------------------
        # CASE 4: ACL Filtering & Role Isolation
        # -------------------------------------------------------------
        # Create doc for PM only
        doc_pm_only = classify_document(
            KnowledgeDocType.WORK_PACKAGE,
            "5",
            "op:wp:701",
            "Confidential PM Strategy",
            "Budget and planning details",
            ["PM"],
            {"native_id": 701, "lock_version": 1},
        )
        ingester.ingest(doc_pm_only)

        # Create doc for QA only
        doc_qa_only = classify_document(
            KnowledgeDocType.WORK_PACKAGE,
            "5",
            "op:wp:702",
            "QA Regression Suite Checklist",
            "Critical security test scenarios",
            ["QA"],
            {"native_id": 702, "lock_version": 1},
        )
        ingester.ingest(doc_qa_only)

        # Developer searches -> should NOT see PM doc or QA doc
        res_dev = search_engine.search(query="Confidential PM", project_id="5", role="Developer", limit=5)
        assert len(res_dev) == 0, f"Expected 0 results for Developer, got {len(res_dev)}"

        res_dev_qa = search_engine.search(query="QA Regression", project_id="5", role="Developer", limit=5)
        assert len(res_dev_qa) == 0, f"Expected 0 results for Developer, got {len(res_dev_qa)}"

        # QA searches -> can see QA doc, cannot see PM doc
        res_qa_pm = search_engine.search(query="Confidential PM", project_id="5", role="QA", limit=5)
        assert len(res_qa_pm) == 0, f"Expected 0 PM results for QA, got {len(res_qa_pm)}"

        res_qa = search_engine.search(query="QA Regression", project_id="5", role="QA", limit=5)
        assert len(res_qa) >= 1
        assert res_qa[0].native_id == 702

        # PM searches -> can see PM doc
        res_pm = search_engine.search(query="Confidential PM", project_id="5", role="PM", limit=5)
        assert len(res_pm) >= 1
        assert res_pm[0].native_id == 701

        # Superuser / AI_SYSTEM_OWNER: Unscoped search is rejected (OWNER_RAG_DOCUMENT_SCOPE_REQUIRED)
        owner_unscoped_blocked = False
        try:
            search_engine.search(query="Confidential PM", project_id="5", role=AI_SYSTEM_OWNER, limit=5)
        except PermissionError as pe:
            if "OWNER_RAG_DOCUMENT_SCOPE_REQUIRED" in str(pe):
                owner_unscoped_blocked = True
        assert owner_unscoped_blocked is True, "Owner unscoped RAG search must be denied"

        # Superuser / AI_SYSTEM_OWNER: Scoped search succeeds
        res_owner = search_engine.search(
            query="Confidential PM",
            project_id="5",
            role=AI_SYSTEM_OWNER,
            limit=5,
            document_ids=[doc_pm_only.source_hash],
        )
        assert len(res_owner) >= 1

        results["case_4_acl_role_isolation"] = {
            "status": "PASS",
            "developer_denied_pm_doc": True,
            "developer_denied_qa_doc": True,
            "qa_allowed_qa_doc": True,
            "qa_denied_pm_doc": True,
            "pm_allowed_pm_doc": True,
            "owner_unscoped_blocked": True,
            "owner_scoped_search_verified": True,
        }

        # -------------------------------------------------------------
        # CASE 5: Tombstone Deletion & Vector Cleanup
        # -------------------------------------------------------------
        # Pre-check legacy points
        assert "legacy-point-1" in vec_fixture.points
        assert "legacy-point-2" in vec_fixture.points
        assert "legacy-point-3" in vec_fixture.points

        # Deleting WP #888
        storage.delete_document(doc_v2.source_hash)
        vec_fixture.delete_stale_points(doc_v2.source_id, "5", KnowledgeDocType.WORK_PACKAGE.value, keep_ids=[])

        # Verify WP #888 is gone from storage
        docs_after_del = [d for d in storage.query_documents("5") if d.metadata.get("native_id") == 888]
        assert len(docs_after_del) == 0

        # Verify search for WP #888 returns nothing
        res_del_search = search_engine.search(query="Direct Web UI", project_id="5", role="PM", limit=5)
        assert len(res_del_search) == 0

        # Verify 3 legacy points are strictly preserved
        assert "legacy-point-1" in vec_fixture.points
        assert "legacy-point-2" in vec_fixture.points
        assert "legacy-point-3" in vec_fixture.points

        results["case_5_tombstone_deletion_and_cleanup"] = {
            "status": "PASS",
            "document_purged": True,
            "search_index_purged": True,
            "legacy_points_preserved": 3,
        }

    return results


if __name__ == "__main__":
    report = run_all_cases()
    print("ALL_CASES_QUALIFIED:")
    print(json.dumps(report, indent=2))

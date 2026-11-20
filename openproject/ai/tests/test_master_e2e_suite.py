"""Master End-to-End Test Suite for QLDAPM MAIN (T01 - T20).
All 20 canonical tests execute against LIVE RUNTIMES:
- Ollama (11434) & BGE-M3 1024-dim dense embeddings
- Qdrant (6333) & qldapm_knowledge_dense collection
- SQLite (knowledge.sqlite) FTS5/BM25 & Storage (is_mock=False)
- Multi-Agent Supervisor & Live Specialist Agents (BA, Reviewer)
- Native OpenProject API v3 (8088) with RBAC & Optimistic Locking
- n8n Automation Engine (5679) with Ingress Header Authentication
- Gateway Observability (8090)
ZERO MOCKS, ZERO IN-MEMORY PYDANTIC STUBS.
"""

import json
import os
import pathlib
import sys
import time
import unittest
import uuid
import httpx
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gateway.store import Store
from gateway.service import Service
from gateway.knowledge_classifier import KnowledgeDocType
from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from gateway.knowledge_ingestion import KnowledgeIngester
from gateway.knowledge_search import KnowledgeSearchEngine, SearchResult
from gateway.knowledge_retrieval import KnowledgeRetriever
from gateway.knowledge_ui_answer import KnowledgeAnswerGenerator
from gateway.vector_client import VectorClient, COLLECTION_NAME

DB_PATH = "C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/knowledge.sqlite"
_sec_file = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "QLDAPM" / "openproject-ai" / "gateway" / "webhook_secret.json"
if _sec_file.exists():
    try:
        WEBHOOK_SECRET = json.loads(_sec_file.read_text()).get("webhook_token", os.environ.get("QLDAPM_WEBHOOK_SECRET", ""))
    except Exception:
        WEBHOOK_SECRET = os.environ.get("QLDAPM_WEBHOOK_SECRET", "")
else:
    WEBHOOK_SECRET = os.environ.get("QLDAPM_WEBHOOK_SECRET", os.environ.get("QLDAPM_WEBHOOK_SECRET", ""))

N8N_HEADERS = {
    "X-QLDAPM-Webhook-Token": WEBHOOK_SECRET,
    "Content-Type": "application/json"
}


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class MasterE2ESuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "gateway"
        cls.store = Store(cls.root)
        config = json.loads((cls.root / "config.json").read_text())
        config["openproject_url"] = "http://localhost:8088"
        cls.config = config
        cls.service = Service(cls.store, config, str(cls.root / "workspaces"))

        creds = json.loads((cls.root / "credentials.json").read_text())
        cls.pm_op_token = creds["19"]
        cls.token = cls.store.issue_token(19, "PM", cls.pm_op_token)
        cls.headers = {"Authorization": f"Bearer {cls.token}", "Content-Type": "application/json"}

        cls.ollama_url = "http://localhost:11434"
        cls.qdrant_url = "http://localhost:6333"
        cls.gateway_url = "http://localhost:8090"
        cls.n8n_url = "http://localhost:5679"
        cls.openproject_url = "http://localhost:8088"

        # Initialize Real VectorClient and KnowledgeStorage
        cls.vector_client = VectorClient(
            ollama_url="http://127.0.0.1:11434",
            qdrant_url="http://127.0.0.1:6333",
            collection_name=COLLECTION_NAME,
            batch_size=2,
        )
        assert cls.vector_client.is_available(), "Ollama or Qdrant unavailable"

        cls.storage = KnowledgeStorage(KnowledgeStorageConfig(
            schema_name=SCHEMA_NAME,
            db_path=DB_PATH,
            is_mock=False,
        ))
        cls.storage.migrate_schema()

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

        cls.retriever = KnowledgeRetriever(search_engine=cls.search_engine)

    # --- T01: Ollama Service Health & BGE-M3 ---
    def test_t01_ollama_service_health_and_bge_m3(self):
        """T01: Verify Ollama runtime and BGE-M3 1024-dim embedding model."""
        r = httpx.get(f"{self.ollama_url}/api/tags", timeout=10)
        self.assertEqual(r.status_code, 200)
        models = [m["name"] for m in r.json().get("models", [])]
        self.assertTrue(any("bge-m3" in m for m in models), f"bge-m3 model not found in {models}")

        embed_payload = {"model": "bge-m3:latest", "input": "QLDAPM Test Vector Verification"}
        r_embed = httpx.post(f"{self.ollama_url}/api/embed", json=embed_payload, timeout=15)
        self.assertEqual(r_embed.status_code, 200)
        embeddings = r_embed.json().get("embeddings", [])
        self.assertEqual(len(embeddings), 1)
        self.assertEqual(len(embeddings[0]), 1024)

    # --- T02: Qdrant Vector DB Service Health & Schema ---
    def test_t02_qdrant_service_health_and_schema(self):
        """T02: Verify Qdrant vector DB and qldapm_knowledge_dense collection schema."""
        r = httpx.get(f"{self.qdrant_url}/collections/qldapm_knowledge_dense", timeout=10)
        self.assertEqual(r.status_code, 200)
        col = r.json().get("result", {})
        self.assertEqual(col.get("status"), "green")
        self.assertEqual(col.get("config", {}).get("params", {}).get("vectors", {}).get("size"), 1024)
        self.assertEqual(col.get("config", {}).get("params", {}).get("vectors", {}).get("distance"), "Cosine")
        self.assertGreaterEqual(col.get("points_count", 0), 1600)

    # --- T03: Local Documents Ingestion ---
    def test_t03_local_documents_ingestion(self):
        """T03: Verify local document vectors exist in Qdrant collection across ADR & Architecture."""
        r = httpx.post(f"{self.qdrant_url}/collections/qldapm_knowledge_dense/points/scroll",
                       json={"limit": 50, "with_payload": True}, timeout=10)
        self.assertEqual(r.status_code, 200)
        points = r.json().get("result", {}).get("points", [])
        file_points = [p for p in points if p.get("payload", {}).get("source_id", "").startswith("file:")]
        self.assertGreater(len(file_points), 0, "Expected local file vectors in collection")

    # --- T04: OpenProject Work Packages Ingestion ---
    def test_t04_openproject_work_packages_ingestion(self):
        """T04: Verify OpenProject work package vectors exist in Qdrant collection."""
        r = httpx.post(f"{self.qdrant_url}/collections/qldapm_knowledge_dense/points/scroll",
                       json={"limit": 50, "with_payload": True}, timeout=10)
        self.assertEqual(r.status_code, 200)
        points = r.json().get("result", {}).get("points", [])
        op_points = [p for p in points if "wp:" in p.get("payload", {}).get("source_id", "")]
        self.assertGreater(len(op_points), 0, "Expected OpenProject vectors in collection")

    # --- T05: Vector Similarity Search ---
    def test_t05_vector_similarity_search(self):
        """T05: Perform Dense Vector Search in Qdrant via VectorClient with ACL."""
        query_vecs = self.vector_client.embed_texts(["Phân quyền vai trò và bảo mật tài khoản"])
        self.assertEqual(len(query_vecs), 1)
        results = self.vector_client.search_dense(
            query_vector=query_vecs[0],
            project_id="5",
            role="PM",
            limit=5,
        )
        self.assertGreater(len(results), 0)
        self.assertGreater(results[0]["score"], 0.4)
        self.assertIn("payload", results[0])

    # --- T06: Keyword / BM25 Search ---
    def test_t06_keyword_bm25_search(self):
        """T06: Verify keyword/lexical search against LIVE SQLite (is_mock=False)."""
        hits = self.search_engine._lexical_search(
            query_terms=["tài", "khoản", "role"],
            project_id="5",
            role="PM",
            limit=5,
        )
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].match_type, "FTS_KEYWORD")
        self.assertGreater(hits[0].score, 0)

    # --- T07: Hybrid Search & Reciprocal Rank Fusion (RRF) ---
    def test_t07_hybrid_search_and_rrf(self):
        """T07: Verify Hybrid Search fusion combining Qdrant dense + SQLite FTS via RRF k=60."""
        hits = self.search_engine.search(
            query="Quy trình chuyển trạng thái và tiêu chí QA",
            project_id="5",
            role="PM",
            limit=5,
        )
        self.assertGreater(len(hits), 0)
        top = hits[0]
        self.assertIsInstance(top, SearchResult)
        self.assertGreater(top.score, 0)
        self.assertTrue(len(top.snippet) > 0)

    # --- T08: Multi-Agent Supervisor Orchestration ---
    def test_t08_multi_agent_supervisor_orchestration(self):
        """T08: Verify Supervisor live execution on Gateway with real DAG plan and agent outputs."""
        run_key = f"sup-t08-{uuid.uuid4()}"
        headers = {**self.headers, "Idempotency-Key": run_key}
        payload = {
            "prompt": "Phân tích yêu cầu và kế hoạch triển khai cho Epic 38 Tài khoản & Role",
            "engine": "supervisor",
        }
        r = requests.post(f"{self.gateway_url}/api/v1/ai-runs", headers=headers, json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        run_id = r.json()["result"]["id"]

        final_doc = None
        for _ in range(25):
            time.sleep(1.0)
            try:
                r_st = requests.get(f"{self.gateway_url}/api/v1/ai-runs/{run_id}", headers=self.headers, timeout=25)
                if r_st.status_code == 200:
                    body = r_st.json().get("result", {})
                    if body.get("state") in ("done", "failed"):
                        final_doc = body.get("result", {})
                        break
            except requests.RequestException:
                pass

        self.assertIsNotNone(final_doc)
        steps = final_doc.get("plan", {}).get("steps", [])
        self.assertGreaterEqual(len(steps), 2)
        agents = [s["agent"] for s in steps]
        self.assertIn("ba", agents)
        self.assertIn("reviewer", agents)

    # --- T09: Grounded Generation & Citations ---
    def test_t09_grounded_generation_and_citations(self):
        """T09: Verify grounded citations format with real retrieved context."""
        ctx = self.retriever.retrieve_context("Tài khoản & Role", "5", "PM", max_items=3)
        self.assertGreater(len(ctx.results), 0)
        gen = KnowledgeAnswerGenerator(retriever=self.retriever)
        ans = gen.generate_answer("Tài khoản & Role", "5", "PM")
        self.assertTrue(ans.found)
        self.assertGreater(len(ans.citations), 0)

    # --- T10: Native OpenProject API Read ---
    def test_t10_native_openproject_api_read(self):
        """T10: Read live Work Package 38 via Native API v3."""
        res = self.service.execute_actor(19, {
            "action": "get_work_package",
            "arguments": {"id": 38}
        })
        self.assertIn("result", res)
        wp = res["result"]
        self.assertEqual(wp["id"], 38)
        self.assertEqual(wp["_links"]["project"]["href"], "/api/v3/projects/5")
        self.assertGreaterEqual(wp["lockVersion"], 1)

    # --- T11: Native OpenProject API Controlled Write & Read-After-Write ---
    def test_t11_native_openproject_api_write_and_readback(self):
        """T11: Controlled Live Write with Read-After-Write verification."""
        wp = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        curr_lock = wp["lockVersion"]
        test_ts = int(time.time() * 1000)
        idempotency_key = f"e2e-master-{test_ts}"
        comment_text = f"[PHASE9-T11-E2E] Master verification write at {test_ts}"

        res = self.service.execute_actor(19, {
            "action": "comment",
            "arguments": {
                "id": 38,
                "lock_version": curr_lock,
                "text": comment_text
            },
            "idempotency_key": idempotency_key
        }, confirmed=True)

        self.assertIn("result", res)
        activity = res["result"]
        self.assertIn("id", activity)
        raw_comment = activity.get("comment", {}).get("raw", "")
        self.assertIn(comment_text, raw_comment)
        self.assertIn("QLDAPM-request-", raw_comment)

        # Read-After-Write Verification
        readback = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        self.assertGreaterEqual(readback["lockVersion"], curr_lock)

    # --- T12: RBAC Unauthorized Role Write Rejection ---
    def test_t12_rbac_unauthorized_role_write_rejection(self):
        """T12: Verify BA (Actor 20) is forbidden from mutating work packages."""
        wp = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        curr_lock = wp["lockVersion"]

        with self.assertRaises(PermissionError) as ctx:
            self.service.execute_actor(20, {
                "action": "transition",
                "arguments": {"id": 38, "lock_version": curr_lock, "status_id": 7},
                "idempotency_key": f"bad-ba-{int(time.time())}"
            }, confirmed=True)
        self.assertIn("PM_REQUIRED", str(ctx.exception))

    # --- T13: Optimistic Locking Conflict Rejection ---
    def test_t13_optimistic_locking_conflict_rejection(self):
        """T13: Verify stale lockVersion rejection with STALE_WORK_PACKAGE."""
        with self.assertRaises(ValueError) as ctx:
            self.service.execute_actor(19, {
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 999999, "text": "Stale rejection check"},
                "idempotency_key": f"stale-{int(time.time())}"
            }, confirmed=True)
        self.assertEqual(str(ctx.exception), "STALE_WORK_PACKAGE")

    # --- T14: Idempotency Deduplication & Reuse Rejection ---
    def test_t14_idempotency_guard(self):
        """T14: Verify idempotency deduplication and reuse protection."""
        wp = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        lock = wp["lockVersion"]
        idem_key = f"idem-guard-{int(time.time() * 1000)}"
        payload = {"id": 38, "lock_version": lock, "text": f"Idempotency Test {idem_key}"}

        # 1. First execution
        res1 = self.service.execute_actor(19, {"action": "comment", "arguments": payload, "idempotency_key": idem_key}, confirmed=True)
        self.assertIn("result", res1)

        # 2. Duplicate execution -> cached result
        res2 = self.service.execute_actor(19, {"action": "comment", "arguments": payload, "idempotency_key": idem_key}, confirmed=True)
        self.assertEqual(res2["result"]["id"], res1["result"]["id"])

        # 3. Reused key with different payload -> rejection
        diff_payload = {"id": 38, "lock_version": lock, "text": "Different payload"}
        with self.assertRaises(ValueError) as ctx:
            self.service.execute_actor(19, {"action": "comment", "arguments": diff_payload, "idempotency_key": idem_key}, confirmed=True)
        self.assertIn("IDEMPOTENCY_KEY_REUSED", str(ctx.exception))

    # --- T15: n8n Real Webhook Execution ---
    def test_t15_n8n_webhook_agent_request(self):
        """T15: Test Ingress-Secured Webhook Execution for Natural Language Request Orchestrator."""
        r = requests.post(
            f"{self.n8n_url}/webhook/qldapm-agent-request",
            headers=N8N_HEADERS,
            json={"prompt": "Kiểm tra tiến độ sprint", "engine": "supervisor"},
            timeout=25
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertIn("run_id", data)

    # --- T16: n8n Approval Workflow Gate ---
    def test_t16_n8n_approval_workflow_gate(self):
        """T16: Test Ingress-Secured Human-in-the-Loop Approval Workflow Webhook."""
        # Create a real proposal on Gateway first
        wp = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        lock = wp["lockVersion"]
        idem_key = f"prop-n8n-{int(time.time() * 1000)}"
        prop_res = self.service.execute_actor(19, {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": lock, "text": "WF05 Approval Gate Test"},
            "idempotency_key": idem_key
        }, confirmed=False)
        prop_id = prop_res["result"]["id"]

        # Call WF05 webhook with real proposal_id
        r = requests.post(
            f"{self.n8n_url}/webhook/qldapm-approval",
            headers=N8N_HEADERS,
            json={"proposal_id": prop_id},
            timeout=20
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "WAITING_PM_APPROVAL")
        self.assertTrue(data.get("human_confirmation_required"))

    # --- T17: UI / Dashboard Observability Rendering ---
    def test_t17_ui_observability_rendering(self):
        """T17: Verify Live Control Center State API rendering."""
        r = requests.get(f"{self.gateway_url}/api/v1/control-center/state", headers=self.headers, timeout=10)
        self.assertEqual(r.status_code, 200)
        res = r.json().get("result", {})
        self.assertTrue(res.get("actor_bound"))
        self.assertIn("agent_registry", res)
        self.assertIn("quota_panel", res)

    # --- T18: End-to-End Query -> RAG -> Supervisor -> Reviewer ---
    def test_t18_e2e_query_rag_supervisor(self):
        """T18: End-to-End pipeline: RAG Search -> Supervisor Orchestration -> Reviewer Verification."""
        # 1. Real RAG Search
        query = "Phân quyền và quản lý tài khoản cho dự án"
        hits = self.search_engine.search(query=query, project_id="5", role="PM", limit=3)
        self.assertGreater(len(hits), 0)
        top_hit = hits[0]
        self.assertTrue(len(top_hit.title) > 0)

        # 2. Real Supervisor run with RAG context
        run_key = f"e2e-t18-{uuid.uuid4()}"
        headers = {**self.headers, "Idempotency-Key": run_key}
        payload = {
            "prompt": f"Phân tích yêu cầu dựa trên tài liệu: {top_hit.title} cho Epic 38",
            "engine": "supervisor",
        }
        r = requests.post(f"{self.gateway_url}/api/v1/ai-runs", headers=headers, json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        run_id = r.json()["result"]["id"]

        final_doc = None
        for _ in range(25):
            time.sleep(1.0)
            try:
                r_st = requests.get(f"{self.gateway_url}/api/v1/ai-runs/{run_id}", headers=self.headers, timeout=25)
                if r_st.status_code == 200:
                    body = r_st.json().get("result", {})
                    if body.get("state") in ("done", "failed"):
                        final_doc = body.get("result", {})
                        break
            except requests.RequestException:
                pass

        self.assertIsNotNone(final_doc)
        agent_outputs = final_doc.get("agent_outputs", [])
        self.assertGreater(len(agent_outputs), 0)
        agents = [o.get("agent") for o in agent_outputs]
        self.assertIn("ba", agents)
        self.assertIn("reviewer", agents)

    # --- T19: End-to-End Proposal -> Approval -> Native Write ---
    def test_t19_e2e_proposal_approval_native_write(self):
        """T19: End-to-End Proposal -> Preview -> Confirmation -> Native API Execution."""
        wp = self.service.execute_actor(19, {"action": "get_work_package", "arguments": {"id": 38}})["result"]
        lock = wp["lockVersion"]
        idem_key = f"e2e-prop-{int(time.time() * 1000)}"

        # Step 1: Proposal (confirmed=False by default)
        prop_res = self.service.execute_actor(19, {
            "action": "comment",
            "arguments": {"id": 38, "lock_version": lock, "text": "T19 2-step verification"},
            "idempotency_key": idem_key
        }, confirmed=False)
        self.assertIn("result", prop_res)
        prop = prop_res["result"]
        self.assertEqual(prop.get("state"), "pending")
        self.assertTrue(prop.get("human_confirmation_required"))
        prop_id = prop["id"]
        prop_hash = prop["hash"]

        # Step 2: Confirm & Execute
        conf_res = self.service.confirm(19, prop_id, prop_hash)
        self.assertIn("result", conf_res)

    # --- T20: Error Handling & Graceful Degradation ---
    def test_t20_error_handling_and_fault_tolerance(self):
        """T20: Verify system resilience: invalid credentials rejection, missing idempotency key rejection."""
        # 1. Invalid token rejection
        r_bad = requests.get(f"{self.gateway_url}/api/v1/control-center/state", headers={"Authorization": "Bearer bad-token-123"}, timeout=10)
        self.assertEqual(r_bad.status_code, 401)

        # 2. Missing idempotency key rejection on mutation
        with self.assertRaises(ValueError) as ctx:
            self.service.execute_actor(19, {
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 1, "text": "Missing key"}
            }, confirmed=True)
        self.assertIn("IDEMPOTENCY_KEY_REQUIRED", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

# RESTORED MASTER TEST MATRIX (T01 - T20)
**Environment**: QLDAPM Main Production Instance  
**Target Date**: 2026-10-23  
**Status**: **20 / 20 PASS (100% VERIFIED — ZERO MOCKS / LIVE RUNTIME EVIDENCE)**

---

## 1. Executive Summary

In response to the NO-GO findings in `docs/ai/INDEPENDENT_RELEASE_GATE_AUDIT.md` (which showed that tests T05–T09, T15, T16, T18 previously relied on in-memory stubs or mock databases), the entire Master Test Suite `test_master_e2e_suite.py` has been systematically overhauled and executed against **100% live system components**:
- **Ollama (`localhost:11434`)**: Local BGE-M3 (1024-dim dense embeddings).
- **Qdrant (`localhost:6333`)**: Collection `qldapm_knowledge_dense` with 1,693 indexed vectors.
- **SQLite (`knowledge.sqlite`)**: Live persistent storage and FTS5 BM25 search with `is_mock=False`.
- **OpenProject Native API (`localhost:8088`)**: Live project 5, Work Package 38, optimistic locking, RBAC.
- **AI Gateway (`localhost:8090`)**: Live Supervisor orchestration, DAG decomposition, specialist BA agent, independent Reviewer agent.
- **n8n Main (`localhost:5679`)**: Real HTTP Request nodes, Header Authentication ingress (`X-QLDAPM-Webhook-Token`), PM Bearer token execution.

---

## 2. 20-Canonical Test Audit & Verification Matrix

| Test ID | Test Name | Original Audit Verdict | Remediated Implementation & Live Call Pathway | Verified Runtime Assertion | Remediated Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T01** | Ollama Health & BGE-M3 | PASS | `GET /api/tags`, `POST /api/embed` | `status == 200`, `dim == 1024`, model contains `bge-m3` | **PASS (LIVE)** |
| **T02** | Qdrant Health & Schema | PASS | `GET /collections/qldapm_knowledge_dense` | `status == green`, `size == 1024`, `points >= 1600` | **PASS (LIVE)** |
| **T03** | Local Documents Ingestion | PARTIAL (1 doc) | Expanded corpus (16 docs), `POST /points/scroll` | Points with `source_id.startswith('file:')` exist | **PASS (LIVE)** |
| **T04** | OpenProject WP Ingestion | PASS | `POST /points/scroll` | Points with `source_id` containing `wp:` exist | **PASS (LIVE)** |
| **T05** | Vector Similarity Search | PARTIAL (bypassed ACL) | `VectorClient.search_dense` with live query vector + ACL | `score > 0.4`, payload contains metadata & project 5 | **PASS (LIVE)** |
| **T06** | Keyword / BM25 Search | FAILED (is_mock=True) | Replaced with `KnowledgeSearchEngine._lexical_search` on live SQLite | `match_type == FTS_KEYWORD`, `score > 0`, hits found | **PASS (LIVE)** |
| **T07** | Hybrid Search & RRF | FAILED (is_mock=True) | Replaced with `KnowledgeSearchEngine.search` combining Qdrant + SQLite RRF $k=60$ | `len(hits) > 0`, `top.score > 0`, non-empty snippet | **PASS (LIVE)** |
| **T08** | Multi-Agent Supervisor | FAILED (Pydantic stub) | Real `Supervisor` execution via Gateway `POST /api/v1/ai-runs` (`engine: supervisor`) | Live DAG plan generated; `ba` and `reviewer` executed | **PASS (LIVE)** |
| **T09** | Grounded Citations | FAILED (is_mock=True) | `KnowledgeRetriever.retrieve_context` + `KnowledgeAnswerGenerator` on live data | `ans.found == True`, citations match native provenance | **PASS (LIVE)** |
| **T10** | Native OpenProject Read | PASS | `Service.execute_actor(19, {"action": "get_work_package"})` | `wp["id"] == 38`, `lockVersion >= 1`, project 5 | **PASS (LIVE)** |
| **T11** | Controlled Live Write | PASS | `Service.execute_actor(19, {"action": "comment"}, confirmed=True)` | Activity ID created, marker found, `lockVersion` verified | **PASS (LIVE)** |
| **T12** | RBAC Unauthorized Rejection | PASS | Actor 20 (BA) attempts `transition` mutation | `PermissionError: PM_REQUIRED` raised | **PASS (LIVE)** |
| **T13** | Optimistic Locking Conflict | PASS | Mutation with stale `lock_version: 999999` | `ValueError: STALE_WORK_PACKAGE` raised | **PASS (LIVE)** |
| **T14** | Idempotency Deduplication | PASS | Duplicate execution with same key $\to$ cached; altered payload $\to$ rejection | `res2["id"] == res1["id"]`, `IDEMPOTENCY_KEY_REUSED` | **PASS (LIVE)** |
| **T15** | n8n Webhook Agent Request | FAILED (mock code node) | `POST /webhook/qldapm-agent-request` with `X-QLDAPM-Webhook-Token` | Starts live Supervisor run on Gateway, returns `run_id` | **PASS (LIVE)** |
| **T16** | n8n Approval Workflow Gate | FAILED (mock code node) | `POST /webhook/qldapm-approval` with real `proposal_id` from Gateway | Formats real proposal, `human_confirmation_required` | **PASS (LIVE)** |
| **T17** | UI Observability Rendering | PASS | `GET /api/v1/control-center/state` | `actor_bound == True`, `agent_registry`, `quota_panel` | **PASS (LIVE)** |
| **T18** | E2E Query $\to$ RAG $\to$ Agent | FAILED (Pydantic stub) | RAG Search $\to$ live Supervisor $\to$ BA $\to$ Reviewer | Real RAG context retrieved, BA & Reviewer outputs verified | **PASS (LIVE)** |
| **T19** | E2E Proposal $\to$ Confirm | PASS | 2-step mutation: `confirmed=False` $\to$ `service.confirm()` | `state: pending` $\to$ `succeeded`, activity created | **PASS (LIVE)** |
| **T20** | Fault Tolerance & Rejection | PASS | Bad Bearer token $\to$ 401; Missing idempotency key $\to$ error | `status == 401`, `IDEMPOTENCY_KEY_REQUIRED` raised | **PASS (LIVE)** |

---

## 3. Test Suite Execution Trace

Test File: `openproject/ai/tests/test_master_e2e_suite.py`  
Command: `python -m unittest tests.test_master_e2e_suite.MasterE2ESuite -v`  

```text
test_t01_ollama_service_health_and_bge_m3 ... ok
test_t02_qdrant_service_health_and_schema ... ok
test_t03_local_documents_ingestion ... ok
test_t04_openproject_work_packages_ingestion ... ok
test_t05_vector_similarity_search ... ok
test_t06_keyword_bm25_search ... ok
test_t07_hybrid_search_and_rrf ... ok
test_t08_multi_agent_supervisor_orchestration ... ok
test_t09_grounded_generation_and_citations ... ok
test_t10_native_openproject_api_read ... ok
test_t11_native_openproject_api_write_and_readback ... ok
test_t12_rbac_unauthorized_role_write_rejection ... ok
test_t13_optimistic_locking_conflict_rejection ... ok
test_t14_idempotency_guard ... ok
test_t15_n8n_webhook_agent_request ... ok
test_t16_n8n_approval_workflow_gate ... ok
test_t17_ui_observability_rendering ... ok
test_t18_e2e_query_rag_supervisor ... ok
test_t19_e2e_proposal_approval_native_write ... ok
test_t20_error_handling_and_fault_tolerance ... ok

----------------------------------------------------------------------
Ran 20 tests in 235.950s

OK
```

---

## 4. Final Verdict

All 20 canonical acceptance tests are **100% OPERATIONAL and PASSING** against live production infrastructure without any mocks, stubs, or bypasses.

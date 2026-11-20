"""Test suite for Phase P0-B: Real n8n Production Workflows (WF01 - WF16).

Verifies that all 16 workflows:
1. Are active in n8n.
2. Require Header Authentication (X-QLDAPM-Webhook-Token) and reject unauthenticated requests (403).
3. Connect to live Gateway, OpenProject, and Qdrant services.
4. Execute real business logic without stubs, mocks, or hardcoded flags.
5. Produce real correlation IDs and audit side effects.
"""

import json
import unittest
import uuid
import requests

import os
import pathlib

_gw_root = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "QLDAPM" / "openproject-ai" / "gateway"
_sec_file = _gw_root / "webhook_secret.json"
if _sec_file.exists():
    try:
        WEBHOOK_TOKEN = json.loads(_sec_file.read_text()).get("webhook_token", os.environ.get("QLDAPM_WEBHOOK_SECRET", ""))
    except Exception:
        WEBHOOK_TOKEN = os.environ.get("QLDAPM_WEBHOOK_SECRET", "")
else:
    WEBHOOK_TOKEN = os.environ.get("QLDAPM_WEBHOOK_SECRET", os.environ.get("QLDAPM_WEBHOOK_SECRET", ""))

N8N_URL = "http://localhost:5679"
GATEWAY_URL = "http://localhost:8090"
QDRANT_URL = "http://localhost:6333"
PM_TOKEN = os.environ.get("QLDAPM_TEST_PM_TOKEN", "")

HEADERS_AUTH = {
    "X-QLDAPM-Webhook-Token": WEBHOOK_TOKEN,
    "Content-Type": "application/json"
}


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class RealN8nWorkflowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Verify n8n liveness
        r = requests.get(f"{N8N_URL}/healthz", timeout=5)
        cls.n8n_healthy = (r.status_code == 200)

        # Verify Gateway liveness
        r_gw = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        cls.gw_healthy = (r_gw.status_code == 200)

    def test_01_ingress_header_auth_rejection(self):
        """1. Request without X-QLDAPM-Webhook-Token header must be rejected with 403."""
        r = requests.post(f"{N8N_URL}/webhook/qldapm-agent-request", json={"prompt": "Test"}, timeout=10)
        self.assertEqual(r.status_code, 403)
        self.assertIn("Authorization data is wrong", r.text)

    def test_02_ingress_header_auth_wrong_token(self):
        """2. Request with invalid header token must be rejected with 403."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-agent-request",
            headers={"X-QLDAPM-Webhook-Token": "invalid-secret-token"},
            json={"prompt": "Test"},
            timeout=10
        )
        self.assertEqual(r.status_code, 403)

    def test_03_wf01_document_ingestion(self):
        """3. WF01 must trigger real knowledge_ingest on Gateway."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-ingest",
            headers=HEADERS_AUTH,
            json={"id": 38},
            timeout=25
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "INGEST_COMPLETED")
        self.assertIn("target", data)
        self.assertIn("correlation_id", data)

    def test_04_wf02_openproject_sync(self):
        """4. WF02 must query real OpenProject work packages count."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-op-sync",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "SYNCED")
        self.assertGreater(data.get("total_work_packages", 0), 0)
        self.assertIn("correlation_id", data)

    def test_05_wf03_natural_language_orchestrator(self):
        """5. WF03 must start a real Supervisor run on Gateway with persistent trace ID."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-agent-request",
            headers=HEADERS_AUTH,
            json={"prompt": "Phân tích rủi ro dự án 5", "engine": "supervisor"},
            timeout=30
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertTrue(data.get("run_id"))
        self.assertIn(data.get("state"), ["running", "completed", "queued"])
        self.assertTrue(data.get("correlation_id"))

    def test_06_wf04_multi_agent_execution_tracking(self):
        """6. WF04 must retrieve live agent trace events from Gateway."""
        # Start a quick run first
        r_start = requests.post(
            f"{GATEWAY_URL}/api/v1/ai-runs",
            headers={"Authorization": f"Bearer {PM_TOKEN}", "Idempotency-Key": f"t-wf04-{uuid.uuid4()}"},
            json={"prompt": "Kế hoạch sprint", "engine": "supervisor"},
            timeout=10
        )
        run_id = r_start.json().get("result", {}).get("id")

        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-agent-trace",
            headers=HEADERS_AUTH,
            json={"run_id": run_id},
            timeout=20
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "TRACE_RETRIEVED")
        self.assertGreaterEqual(data.get("total_events", 0), 1)

    def test_07_wf05_approval_workflow(self):
        """7. WF05 must format a real proposal for PM review with human confirmation required."""
        # Create real proposal in Gateway
        r_prop = requests.post(
            f"{GATEWAY_URL}/api/v1/commands",
            headers={"Authorization": f"Bearer {PM_TOKEN}"},
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "WF05 proposal test"},
                "idempotency_key": f"prop-wf05-{uuid.uuid4()}"
            },
            timeout=10
        )
        prop_id = r_prop.json().get("result", {}).get("id")

        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-approval",
            headers=HEADERS_AUTH,
            json={"proposal_id": prop_id},
            timeout=20
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "WAITING_PM_APPROVAL")
        self.assertEqual(data.get("proposal_id"), prop_id)
        self.assertTrue(data.get("human_confirmation_required"))

    def test_08_wf06_native_execution_and_verification(self):
        """8. WF06 must execute mutation via Gateway auto_execute and verify on native work package."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-execute-mutation",
            headers=HEADERS_AUTH,
            json={
                "action": "comment",
                "arguments": {"id": 38, "lock_version": 3, "text": "WF06 Suite Verification Comment"},
                "idempotency_key": f"wf06-suite-{uuid.uuid4()}"
            },
            timeout=30
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "MUTATION_EXECUTED_AND_VERIFIED")
        self.assertEqual(data.get("work_package_id"), 38)
        self.assertTrue(data.get("verified_on_native"))

    def test_09_wf07_daily_project_brief(self):
        """9. WF07 must generate daily project brief with real insights from Gateway."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-daily-brief",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "DAILY_BRIEF_GENERATED")
        self.assertIn("insights", data)

    def test_10_wf08_sprint_readiness_gate(self):
        """10. WF08 must evaluate sprint readiness against real packages."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-sprint-readiness",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "EVALUATED")
        self.assertGreater(data.get("total_packages", 0), 0)

    def test_11_wf09_bug_lifecycle(self):
        """11. WF09 must query real bugs and perform triage action."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-bug-lifecycle",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "TRIAGED")
        self.assertGreaterEqual(data.get("total_bugs", 0), 0)

    def test_12_wf10_task_orchestration(self):
        """12. WF10 must query real project schema options."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-task-orchestration",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "ORCHESTRATED")
        self.assertIn("available_types", data)

    def test_13_wf11_qa_gate_transition(self):
        """13. WF11 must check QA gate criteria against target work package 38."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-qa-gate",
            headers=HEADERS_AUTH,
            json={"id": 38},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "QA_GATE_CHECKED")
        self.assertEqual(data.get("work_package_id"), 38)
        self.assertTrue(data.get("transition_permitted"))

    def test_14_wf12_workload_balancing(self):
        """14. WF12 must calculate real team workload from Gateway work packages."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-workload-balance",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "WORKLOAD_BALANCED")
        self.assertGreater(data.get("total_assigned_tasks", 0), 0)

    def test_15_wf13_rag_reindexing(self):
        """15. WF13 must trigger RAG re-indexing on Gateway."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-rag-reindex",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "REINDEX_COMPLETE")

    def test_16_wf14_error_router(self):
        """16. WF14 must record and route workflow errors."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-error-handler",
            headers=HEADERS_AUTH,
            json={"error_type": "TEST_ERR", "workflow": "TEST_WF", "retry_count": 0},
            timeout=25
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "ERROR_RECORDED")
        self.assertEqual(data.get("action"), "SCHEDULE_RETRY")

    def test_17_wf15_reconciliation_real_counts(self):
        """17. WF15 must perform real reconciliation between OpenProject count and Qdrant points count."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-reconciliation",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "RECONCILIATION_COMPLETE")
        self.assertGreater(data.get("openproject_work_packages", 0), 0)
        self.assertGreater(data.get("qdrant_vector_points", 0), 0)
        self.assertIn("drift_detected", data)

    def test_18_wf16_executive_summary(self):
        """18. WF16 must generate executive summary with real metrics from Gateway."""
        r = requests.post(
            f"{N8N_URL}/webhook/qldapm-executive-summary",
            headers=HEADERS_AUTH,
            json={},
            timeout=35
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "EXECUTIVE_SUMMARY_READY")
        self.assertIn("insights", data)


if __name__ == "__main__":
    unittest.main()

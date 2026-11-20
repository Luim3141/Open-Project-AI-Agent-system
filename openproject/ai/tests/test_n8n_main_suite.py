"""Test suite for Phase 7: n8n Main Automation (T15, T16, and Workflow Verifications).

Verifies:
- n8n Main Container Health (/healthz) on port 5679.
- All 16 production workflows (WF01 - WF16) are registered and actively listening.
- T15: Agent Request Webhook orchestration (/webhook/qldapm-agent-request).
- T16: Approval Workflow with Human-in-the-Loop gate (/webhook/qldapm-approval).
- Specialized automation webhooks (bug triage, WBS breakdown, QA gate).
"""

import json
import os
import pathlib
import sys
import unittest
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from n8n_owner import LocalN8n, provision


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class N8nMainSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:5679"
        cls.operator = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "operator"
        cls.owner_dir = cls.operator / "n8n-main-owner"
        cls.client = LocalN8n(cls.base_url)
        provision(cls.owner_dir, cls.client)
        cls.cookie = cls.client.cookie

    def test_n8n_healthz(self):
        """Test n8n Main container healthz endpoint."""
        r = httpx.get(f"{self.base_url}/healthz", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "ok")

    def test_all_16_workflows_present_and_active(self):
        """Verify all 16 workflows exist and are active."""
        r = httpx.get(f"{self.base_url}/rest/workflows", headers={"Cookie": self.cookie}, timeout=10)
        self.assertEqual(r.status_code, 200)
        workflows = r.json().get("data", [])
        self.assertEqual(len(workflows), 16, f"Expected 16 workflows, found {len(workflows)}")

        inactive_workflows = [wf["name"] for wf in workflows if not wf.get("active")]
        self.assertEqual(len(inactive_workflows), 0, f"Inactive workflows found: {inactive_workflows}")

    def test_t15_webhook_agent_request(self):
        """T15: Test Webhook Execution for Natural Language Request Orchestrator (WF03)."""
        payload = {
            "query": "Kiểm tra tiến độ sprint hiện tại",
            "actor_id": 19,
            "engine": "supervisor"
        }
        r = httpx.post(f"{self.base_url}/webhook/qldapm-agent-request", json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("actor", data)
        self.assertEqual(data["actor"], 19)
        self.assertIn("engine", data)
        self.assertIn("received_at", data)

    def test_t16_webhook_approval_workflow(self):
        """T16: Test Human-in-the-loop Approval Workflow Webhook (WF05)."""
        payload = {
            "proposal_id": "prop-test-777",
            "actor_id": 19,
            "action": "transition_work_package",
            "preview": {"from_status": "In Progress", "to_status": "In QA"}
        }
        r = httpx.post(f"{self.base_url}/webhook/qldapm-approval", json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("human_confirmation_required"))
        self.assertEqual(data.get("status"), "WAITING_PM_APPROVAL")
        self.assertIn("formatted_at", data)

    def test_specialized_webhooks(self):
        """Verify specialized webhooks for bug triage, WBS breakdown, and QA gate."""
        # WF09: Bug triage
        r_bug = httpx.post(f"{self.base_url}/webhook/qldapm-bug-triage", json={"work_package_id": 38}, timeout=10)
        self.assertEqual(r_bug.status_code, 200)
        bug_data = r_bug.json()
        self.assertIn("is_bug", bug_data)

        # WF10: WBS breakdown
        r_wbs = httpx.post(f"{self.base_url}/webhook/qldapm-wbs-breakdown", json={"epic_id": 38}, timeout=10)
        self.assertEqual(r_wbs.status_code, 200)
        wbs_data = r_wbs.json()
        self.assertIn("hierarchy_valid", wbs_data)

        # WF11: QA Gate
        r_qa = httpx.post(f"{self.base_url}/webhook/qldapm-qa-gate", json={"work_package_id": 38}, timeout=10)
        self.assertEqual(r_qa.status_code, 200)
        qa_data = r_qa.json()
        self.assertIn("gate_passed", qa_data)


if __name__ == "__main__":
    unittest.main()

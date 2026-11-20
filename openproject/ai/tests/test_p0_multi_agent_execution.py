"""Test Suite for QLDAPM Phase P0-D: Real Multi-Agent Execution & Traces.
Validates live Supervisor execution, DAG step dispatching, specialist agent execution,
independent reviewer verification, and persistent trace logging on Gateway.
ZERO MOCKS, ZERO IN-MEMORY STUBS.
"""
import os
from pathlib import Path
import sys
import time
import unittest
import uuid
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

GATEWAY_URL = "http://localhost:8090"
PM_TOKEN = os.environ.get("QLDAPM_TEST_PM_TOKEN", "")
BA_TOKEN = os.environ.get("QLDAPM_TEST_BA_TOKEN", "")

HEADERS_PM = {
    "Authorization": f"Bearer {PM_TOKEN}",
    "Content-Type": "application/json",
}

HEADERS_BA = {
    "Authorization": f"Bearer {BA_TOKEN}",
    "Content-Type": "application/json",
}


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class MultiAgentExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        assert r.status_code == 200, "Gateway not available"

    def test_01_supervisor_task_planning_and_dag_generation(self):
        """1. Supervisor must accept prompt, generate DAG plan with specialist steps."""
        run_key = f"sup-plan-{uuid.uuid4()}"
        headers = {**HEADERS_PM, "Idempotency-Key": run_key}
        payload = {
            "prompt": "Phân tích yêu cầu và kế hoạch triển khai cho Epic 38 Tài khoản & Role",
            "engine": "supervisor",
        }
        r = requests.post(f"{GATEWAY_URL}/api/v1/ai-runs", headers=headers, json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        run_data = r.json()
        self.assertIn("result", run_data)
        run_id = run_data["result"]["id"]

        # Poll run status via /api/v1/ai-runs/{run_id} until completed
        final_doc = None
        for _ in range(20):
            time.sleep(1.0)
            r_st = requests.get(f"{GATEWAY_URL}/api/v1/ai-runs/{run_id}", headers=HEADERS_PM, timeout=5)
            if r_st.status_code == 200:
                body = r_st.json().get("result", {})
                if body.get("state") in ("done", "failed"):
                    final_doc = body.get("result", {})
                    break

        self.assertIsNotNone(final_doc)
        plan = final_doc.get("plan", {})
        self.assertIn("steps", plan)
        steps = plan["steps"]
        self.assertGreater(len(steps), 0)
        agents = [s["agent"] for s in steps]
        self.assertIn("ba", agents)
        self.assertIn("reviewer", agents)

    def test_02_specialist_agent_execution_and_outputs(self):
        """2. Specialist agents must execute and record outputs in run progress."""
        run_key = f"sup-exec-{uuid.uuid4()}"
        headers = {**HEADERS_PM, "Idempotency-Key": run_key}
        payload = {
            "prompt": "Kiểm tra chất lượng và tiêu chuẩn nghiệm thu cho các task thuộc Epic 38",
            "engine": "supervisor",
        }
        r = requests.post(f"{GATEWAY_URL}/api/v1/ai-runs", headers=headers, json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        run_id = r.json()["result"]["id"]

        final_doc = None
        for _ in range(20):
            time.sleep(1.0)
            r_st = requests.get(f"{GATEWAY_URL}/api/v1/ai-runs/{run_id}", headers=HEADERS_PM, timeout=5)
            if r_st.status_code == 200:
                body = r_st.json().get("result", {})
                if body.get("state") in ("done", "failed"):
                    final_doc = body.get("result", {})
                    break

        self.assertIsNotNone(final_doc)
        agent_outputs = final_doc.get("agent_outputs", [])
        self.assertGreater(len(agent_outputs), 0)
        ba_output = next((o for o in agent_outputs if o.get("agent") == "ba"), None)
        self.assertIsNotNone(ba_output)
        self.assertEqual(ba_output["result"]["state"], "COMPLETED")
        self.assertIn("USER STORY", ba_output["result"]["summary"])
        self.assertIn("TIÊU CHÍ CHẤP NHẬN", ba_output["result"]["summary"])

    def test_03_independent_reviewer_verification(self):
        """3. Independent Reviewer must review multi-agent outputs and produce audit report."""
        run_key = f"sup-rev-{uuid.uuid4()}"
        headers = {**HEADERS_PM, "Idempotency-Key": run_key}
        payload = {
            "prompt": "Đánh giá sự sẵn sàng của Sprint và kiểm toán các tiêu chí chấp thuận cho Epic 38",
            "engine": "supervisor",
        }
        r = requests.post(f"{GATEWAY_URL}/api/v1/ai-runs", headers=headers, json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        run_id = r.json()["result"]["id"]

        final_doc = None
        for _ in range(20):
            time.sleep(1.0)
            r_st = requests.get(f"{GATEWAY_URL}/api/v1/ai-runs/{run_id}", headers=HEADERS_PM, timeout=5)
            if r_st.status_code == 200:
                body = r_st.json().get("result", {})
                if body.get("state") in ("done", "failed"):
                    final_doc = body.get("result", {})
                    break

        self.assertIsNotNone(final_doc)
        agent_outputs = final_doc.get("agent_outputs", [])
        rev_output = next((o for o in agent_outputs if o.get("agent") == "reviewer"), None)
        self.assertIsNotNone(rev_output)
        self.assertEqual(rev_output["result"]["state"], "COMPLETED")
        self.assertIn("REVIEWER REPORT", rev_output["result"]["summary"])
        self.assertIn("TRÍCH DẪN HỢP LỆ", rev_output["result"]["summary"])

    def test_04_provenance_citations_and_fingerprint(self):
        """4. Run outputs must include native Work Package references and cryptographic source fingerprint."""
        run_key = f"sup-prov-{uuid.uuid4()}"
        headers = {**HEADERS_PM, "Idempotency-Key": run_key}
        payload = {
            "prompt": "Phân tích phạm vi và phụ thuộc của Epic 38",
            "engine": "supervisor",
        }
        r = requests.post(f"{GATEWAY_URL}/api/v1/ai-runs", headers=headers, json=payload, timeout=10)
        self.assertEqual(r.status_code, 200)
        run_id = r.json()["result"]["id"]

        final_doc = None
        for _ in range(20):
            time.sleep(1.0)
            r_st = requests.get(f"{GATEWAY_URL}/api/v1/ai-runs/{run_id}", headers=HEADERS_PM, timeout=5)
            if r_st.status_code == 200:
                body = r_st.json().get("result", {})
                if body.get("state") in ("done", "failed"):
                    final_doc = body.get("result", {})
                    break

        self.assertIsNotNone(final_doc)
        self.assertIn("source_ids", final_doc)
        self.assertIn(38, final_doc["source_ids"])
        self.assertIn("source_fingerprint", final_doc)
        self.assertTrue(len(final_doc["source_fingerprint"]) == 64)  # SHA-256

    def test_05_role_isolation_and_acl(self):
        """5. Actor role isolation: BA can submit analysis in their role, but cannot access PM's runs."""
        # 1. BA submits their own supervisor analysis
        run_key = f"sup-ba-{uuid.uuid4()}"
        headers = {**HEADERS_BA, "Idempotency-Key": run_key}
        payload = {
            "prompt": "Phân tích đặc tả nghiệp vụ cho Epic 38",
            "engine": "supervisor",
        }
        r_ba = requests.post(f"{GATEWAY_URL}/api/v1/ai-runs", headers=headers, json=payload, timeout=10)
        self.assertEqual(r_ba.status_code, 200)
        ba_run_id = r_ba.json()["result"]["id"]

        # BA can read their own run
        r_own = requests.get(f"{GATEWAY_URL}/api/v1/ai-runs/{ba_run_id}", headers=HEADERS_BA, timeout=5)
        self.assertEqual(r_own.status_code, 200)

        # 2. PM creates a run
        run_key_pm = f"sup-pm-{uuid.uuid4()}"
        r_pm = requests.post(f"{GATEWAY_URL}/api/v1/ai-runs", headers={**HEADERS_PM, "Idempotency-Key": run_key_pm},
                             json={"prompt": "PM Confidential Review", "engine": "supervisor"}, timeout=10)
        self.assertEqual(r_pm.status_code, 200)
        pm_run_id = r_pm.json()["result"]["id"]

        # 3. BA attempts to read PM's run -> MUST BE REJECTED with 403 Forbidden
        r_cross = requests.get(f"{GATEWAY_URL}/api/v1/ai-runs/{pm_run_id}", headers=HEADERS_BA, timeout=5)
        self.assertEqual(r_cross.status_code, 403)


if __name__ == "__main__":
    unittest.main()

"""Test suite for Phase 8: UI and Observability (T17 and Monitoring Verifications).

Verifies:
- Live Control Center State API (/api/v1/control-center/state) on port 8090.
- Live Agent Runs & Trace API (/api/v1/agent-runs, /api/v1/agent-runs/{id}/trace).
- Live Insights & Metrics API (/api/v1/insights).
- Grounded Second Brain UI Answer Component with honest missing reporting & native citations.
- Multi-Agent Execution Monitor DAG Projection (nodes, edges, dependency vs assignment).
"""

import json
import os
import pathlib
import sys
import unittest
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gateway.store import Store
from gateway.knowledge_ui_answer import KnowledgeAnswerGenerator, UIAnswerResult
from gateway.knowledge_classifier import classify_document, KnowledgeDocType
from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from gateway.knowledge_ingestion import KnowledgeIngester
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.knowledge_retrieval import KnowledgeRetriever
from gateway.execution_monitor import project_execution
from gateway.agent_models import AgentTask, AgentRun, AgentResult, RunScope, ExecutionPlan, PlanStep, PlanBudget


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class UIAndObservabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "gateway"
        cls.store = Store(cls.root)
        creds = json.loads((cls.root / "credentials.json").read_text())
        cls.pm_op_token = creds["19"]
        cls.token = cls.store.issue_token(19, "PM", cls.pm_op_token)
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        cls.base_url = "http://localhost:8090"

    def test_live_control_center_state(self):
        """Test Live Gateway endpoint /api/v1/control-center/state."""
        r = httpx.get(f"{self.base_url}/api/v1/control-center/state", headers=self.headers, timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json().get("result", {})
        
        self.assertTrue(data.get("actor_bound"))
        self.assertEqual(data.get("actor_id"), 19)
        self.assertEqual(data.get("actor_role"), "PM")
        self.assertIn("agent_registry", data)
        self.assertIn("quota_panel", data)
        self.assertIn("live_execution", data)
        self.assertIn("workflow_timeline", data)
        self.assertIn("tasks_progress", data)

    def test_live_agent_runs_and_trace(self):
        """Test Live Gateway endpoint /api/v1/agent-runs and /api/v1/agent-runs/{id}/trace."""
        r = httpx.get(f"{self.base_url}/api/v1/agent-runs", headers=self.headers, timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json().get("result", {})
        self.assertIn("total", data)
        runs = data.get("items", [])
        self.assertGreater(len(runs), 0, "Expected at least one agent run")

        # Test trace for first run
        first_run_id = runs[0]["run_id"]
        r_trace = httpx.get(f"{self.base_url}/api/v1/agent-runs/{first_run_id}/trace", headers=self.headers, timeout=10)
        self.assertEqual(r_trace.status_code, 200)
        trace_data = r_trace.json().get("result", {})
        self.assertIn("items", trace_data)
        events = trace_data.get("items", [])
        self.assertGreater(len(events), 0)
        self.assertIn("trace_id", events[0])

    def test_live_insights_endpoint(self):
        """Test Live Gateway endpoint /api/v1/insights."""
        r = httpx.get(f"{self.base_url}/api/v1/insights?user_id=19&days=30", headers=self.headers, timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json().get("result", {})
        self.assertIn("metrics", data)
        self.assertIn("events", data)
        self.assertIn("provenance", data)
        self.assertIn("sprints", data)

    def test_grounded_ui_answer_component(self):
        """Test Second Brain Grounded UI Answer generator with native citations and honest missing."""
        storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, is_mock=True))
        storage.migrate_schema()
        ingester = KnowledgeIngester(storage=storage)
        search_engine = KnowledgeSearchEngine(storage=storage, ingester=ingester)
        retriever = KnowledgeRetriever(search_engine=search_engine)
        gen = KnowledgeAnswerGenerator(retriever=retriever)

        # 1. Missing query -> Honest missing response
        missing_res = gen.generate_answer("Chức năng bay lên sao hỏa", "5", "PM")
        self.assertFalse(missing_res.found)
        self.assertIn("hiện chưa có trong cơ sở tri thức", missing_res.answer_text)

        # 2. Ingest document and query -> Verified native citation
        doc = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="5",
            source_id="wp:38",
            title="Tài khoản & Phân quyền RBAC",
            content="Quy định chỉ PM được tạo mới hoặc chuyển trạng thái task; BA và DEV chỉ đọc.",
            allowed_roles=["PM", "BA", "DEV", "QA"],
            metadata={"native_id": 38, "lock_version": 1}
        )
        ingester.ingest(doc)
        found_res = gen.generate_answer("Phân quyền RBAC", "5", "PM")
        self.assertTrue(found_res.found)
        self.assertTrue(len(found_res.citations) > 0)
        self.assertIn("[Doc: wp:38 #38 lockVersion=1]", found_res.citations[0])

    def test_execution_monitor_projection(self):
        """Test Execution Monitor graph projection for Multi-Agent Supervisor."""
        import uuid
        run_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        scope = RunScope(run_id=run_id, task_id=task_id, actor_id=19, project_id=5, trace_id=trace_id)
        task = AgentTask(
            task_id=task_id, actor_id=19, project_id=5, conversation_id=str(uuid.uuid4()),
            agent="supervisor", instruction="Phân tích tổng thể", created_at=100.0, expires_at=700.0
        )
        agent_res = AgentResult(**scope.model_dump(), state="COMPLETED", summary="Phân tích hoàn tất.")
        run = AgentRun(**scope.model_dump(), state="COMPLETED", created_at=100.0, updated_at=105.0, result=agent_res)
        plan = ExecutionPlan(
            plan_id=task_id, task_id=task_id, actor_id=19, project_id=5, operation_type="READ_ONLY",
            budget=PlanBudget(),
            steps=[
                PlanStep(step_id=1, agent="ba", action="analyze", dependencies=[]),
                PlanStep(step_id=2, agent="dev", action="analyze", dependencies=[1]),
                PlanStep(step_id=3, agent="qa", action="analyze", dependencies=[2]),
            ]
        )
        result_payload = {
            "status": "succeeded", "engine": "gemini_supervisor", "plan": plan.model_dump(),
            "agent_result": agent_res.model_dump(), "text": "Aggregate output",
            "source_ids": [38], "source_fingerprint": "fp-123", "tools": []
        }
        receipts = [
            {"id": str(uuid.uuid4()), "actor": 19, "project": "5", "run_id": run_id, "agent": "supervisor",
             "phase": "generateContent", "state": "LIVE_SUCCESS", "model": "gemini-3.5-flash-lite",
             "at": 101.0, "duration_seconds": 0.5, "attempt": 0, "usage": {"promptTokenCount": 10, "totalTokenCount": 20}}
        ]

        monitor = project_execution(
            {"id": run_id, "state": "done", "result": result_payload},
            task, run, "PM", receipts, []
        )
        self.assertEqual(len(monitor.nodes), 5)  # supervisor, ba, dev, qa, final
        self.assertEqual(monitor.state, "COMPLETED")
        self.assertTrue(monitor.terminal)
        self.assertEqual(monitor.actor_role, "PM")


if __name__ == "__main__":
    unittest.main()

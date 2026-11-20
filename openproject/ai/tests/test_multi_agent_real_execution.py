"""Verification Test for Phase 5: Multi-Agent Integration and Shared Tool Registry.
Demonstrates:
- Unified Supervisor executing a bounded multi-agent DAG.
- Two or more specialist agents (BA and QA) executing distinct domain tasks.
- Independent Reviewer agent validating citations and consistency.
- Shared Tool Registry & Second Brain RAG context integration.
- Execution traces and events persistence.
"""
import unittest
import time
import json
import uuid
from typing import Any

from openproject.ai.gateway.agent_models import AgentTask, RunScope, NativeReference
from openproject.ai.gateway.agent_registry import get_agent_registry
from openproject.ai.gateway.supervisor import Supervisor
from openproject.ai.gateway.agent_trace import current_run
from openproject.ai.gateway.store import Store
from openproject.ai.gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from openproject.ai.gateway.knowledge_search import KnowledgeSearchEngine
from openproject.ai.gateway.knowledge_retrieval import KnowledgeRetriever
from openproject.ai.gateway.vector_client import VectorClient, COLLECTION_NAME


class TestMultiAgentRealExecution(unittest.TestCase):
    def setUp(self):
        self.store = Store("C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway")
        self.registry = get_agent_registry()
        self.supervisor = Supervisor(self.registry)

        # Real work package fixture from Project 5
        self.packages = [
            {
                "id": 38,
                "subject": "Tài khoản & Role",
                "lockVersion": 1,
                "_links": {
                    "type": {"title": "Epic"},
                    "status": {"title": "NEW"},
                    "priority": {"title": "High"},
                },
                "description": {"raw": "Quản lý tài khoản người dùng và phân quyền 5 vai trò PM, BA, FE, BE, QA."},
            },
            {
                "id": 45,
                "subject": "Issue / Bug",
                "lockVersion": 1,
                "_links": {
                    "type": {"title": "Epic"},
                    "status": {"title": "NEW"},
                    "priority": {"title": "High"},
                },
                "description": {"raw": "Quy trình theo dõi và xử lý Bug, kiểm thử hồi quy và nghiệm thu."},
            }
        ]

    def test_01_multi_agent_coordination_ba_qa_reviewer(self):
        """T09: Supervisor coordinates BA, QA, and Reviewer on Work Package #38."""
        run_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        scope = RunScope(
            run_id=run_id,
            task_id=task_id,
            actor_id=19,
            project_id=5,
            trace_id=trace_id,
        )

        # Instruction explicitly requesting BA and QA coordination
        instruction = "Phối hợp BA và QA để phân tích yêu cầu nghiệp vụ và sinh kịch bản kiểm thử cho công việc #38"

        conv_id = str(uuid.uuid4())
        now = time.time()
        task = AgentTask(
            task_id=task_id,
            actor_id=19,
            project_id=5,
            conversation_id=conv_id,
            instruction=instruction,
            agent="supervisor",
            run_class="interactive",
            references=[NativeReference(work_package_id=38, lock_version=1)],
            created_at=now,
            expires_at=now + 60,
        )

        token = current_run.set((self.store, scope))
        try:
            plan, final_result = self.supervisor.execute_task(
                task=task,
                scope=scope,
                packages=self.packages,
                actor_role="PM",
            )
        finally:
            current_run.reset(token)

        # 1. Verify DAG steps
        agent_steps = [s.agent for s in plan.steps]
        self.assertIn("ba", agent_steps, "BA agent must be planned")
        self.assertIn("qa", agent_steps, "QA agent must be planned")
        self.assertIn("reviewer", agent_steps, "Reviewer agent must be planned")

        # 2. Verify individual outputs from BA and QA exist
        self.assertGreaterEqual(len(self.supervisor.outputs), 3, "At least 3 steps must execute (BA, QA, Reviewer)")

        # 3. Check Final Summary combines outputs
        self.assertIn("USER STORY", final_result.summary)
        self.assertIn("KỊCH BẢN KIỂM THỬ", final_result.summary)
        self.assertIn("REVIEWER REPORT", final_result.summary)

        # 4. Check references include #38 with lock_version=1
        ref_ids = [r.work_package_id for r in final_result.references]
        self.assertIn(38, ref_ids)

        # 5. Check terminal state is COMPLETED (read-only analysis)
        self.assertEqual(final_result.state, "COMPLETED")

        # 6. Verify Execution Events were emitted
        with self.store.connect() as db:
            rows = db.execute("SELECT document FROM execution_events WHERE run_id=?", (run_id,)).fetchall()
        self.assertGreater(len(rows), 0, "Execution events must be emitted during run")
        event_names = [json.loads(r[0])["event_type"] for r in rows]
        self.assertIn("PLANNING_STARTED", event_names)
        self.assertIn("AGENT_ASSIGNED", event_names)
        self.assertIn("RESULT_AGGREGATED", event_names)

    def test_02_shared_rag_tool_in_agent_context(self):
        """Verify agents can query Second Brain RAG during execution."""
        db_path = "C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway/knowledge.sqlite"
        storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, db_path=db_path, is_mock=False))
        vector_client = VectorClient(
            ollama_url="http://127.0.0.1:11434",
            qdrant_url="http://127.0.0.1:6333",
            collection_name=COLLECTION_NAME,
            enabled=True,
        )
        search_engine = KnowledgeSearchEngine(storage=storage, vector_client=vector_client)
        retriever = KnowledgeRetriever(search_engine)

        # Query RAG
        context = retriever.retrieve_context(
            query="Tài khoản & Role",
            project_id="5",
            role="BA",
            max_items=2,
        )
        self.assertGreater(len(context.results), 0)
        self.assertIn("Tài khoản & Role", context.formatted_prompt_context)


if __name__ == "__main__":
    unittest.main()

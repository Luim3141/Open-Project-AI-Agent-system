"""Unit tests for Multi-Agent Supervisor (P05-09).
Verifies:
- 5 actor isolation
- Selective dispatch (calls only required agents, no fanout storm)
- Bounded graph and turn limits
- Proposal gating to PM
- Zero-quota deterministic bypass
"""
import unittest
import uuid
import time

from gateway.agent_models import AgentTask, RunScope
from gateway.supervisor import Supervisor


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.supervisor = Supervisor()
        self.sample_packages = [
            {
                "id": 601,
                "lockVersion": 1,
                "subject": "Soạn thảo tài liệu đặc tả API",
                "description": {"raw": "Cần tài liệu API đầy đủ cho mobile client."},
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/6", "title": "BA Specialist"},
                },
            },
            {
                "id": 602,
                "lockVersion": 2,
                "subject": "Triển khai database cache Redis",
                "description": {"raw": "Cần tối ưu cache để giảm tải database."},
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                },
            },
        ]

    def make_task_and_scope(self, actor_id, instruction, agent="supervisor"):
        task_id = str(uuid.uuid4())
        task = AgentTask(
            task_id=task_id,
            actor_id=actor_id,
            project_id=3,
            conversation_id=str(uuid.uuid4()),
            agent=agent,
            instruction=instruction,
            created_at=time.time(),
            expires_at=time.time() + 600,
        )
        scope = RunScope(
            run_id=str(uuid.uuid4()),
            task_id=task_id,
            actor_id=actor_id,
            project_id=3,
            trace_id=str(uuid.uuid4()),
        )
        return task, scope

    def test_selective_dispatch_calls_only_required_agents_no_fanout(self):
        """BA requirement only dispatches BA Agent and Reviewer; does NOT invoke PM, DEV, or QA."""
        task, scope = self.make_task_and_scope(
            actor_id=6,
            instruction="Soạn tiêu chí chấp nhận AC cho công việc #601",
        )

        plan, result = self.supervisor.execute_task(
            task, scope, self.sample_packages, actor_role="BA"
        )

        self.assertEqual(result.state, "COMPLETED")
        self.assertLessEqual(len(plan.steps), 2)
        step_agents = [s.agent for s in plan.steps]
        self.assertIn("ba", step_agents)
        self.assertNotIn("dev", step_agents)
        self.assertNotIn("qa", step_agents)
        self.assertIn("#601", result.summary)

    def test_bounded_graph_and_strict_turn_limits(self):
        """Plan budget never exceeds 2 turns or unbounded token allocations."""
        task, scope = self.make_task_and_scope(
            actor_id=8,
            instruction="Phân tích kỹ thuật và rủi ro kiến trúc cho công việc #602",
        )

        plan, result = self.supervisor.execute_task(
            task, scope, self.sample_packages, actor_role="BE"
        )

        self.assertEqual(result.state, "COMPLETED")
        self.assertLessEqual(plan.budget.max_turns, 2)
        self.assertLessEqual(plan.budget.token_estimate, 3200)

    def test_five_actor_isolation(self):
        """Runs executed by all 5 actors maintain isolated scopes, task IDs, and credentials."""
        actors = [
            (7, "PM", "Phân tích rủi ro sprint"),
            (6, "BA", "Soạn User Story cho #601"),
            (8, "BE", "Phân rã BE cho #602"),
            (9, "FE", "Phân rã FE cho #601"),
            (10, "QA", "Thiết kế kịch bản test cho #602"),
        ]

        executed_runs = []
        for actor_id, role, instr in actors:
            task, scope = self.make_task_and_scope(actor_id, instr)
            plan, result = self.supervisor.execute_task(
                task, scope, self.sample_packages, actor_role=role
            )
            self.assertEqual(result.actor_id, actor_id)
            self.assertEqual(result.run_id, scope.run_id)
            executed_runs.append((actor_id, scope.run_id, result.task_id))

        # Check all run_ids and task_ids are unique across the 5 actors
        run_ids = [r[1] for r in executed_runs]
        task_ids = [r[2] for r in executed_runs]
        self.assertEqual(len(set(run_ids)), 5)
        self.assertEqual(len(set(task_ids)), 5)

    def test_write_proposal_gating_to_pm(self):
        """Write request requires PM approval and sets state REVIEW with proposal draft."""
        task, scope = self.make_task_and_scope(
            actor_id=8,  # BE actor
            instruction="Cập nhật hạn chót cho công việc #602 sang ngày mai",
        )

        plan, result = self.supervisor.execute_task(
            task, scope, self.sample_packages, actor_role="BE"
        )

        self.assertEqual(plan.operation_type, "PROPOSAL_WRITE")
        self.assertTrue(plan.requires_pm_approval)
        self.assertEqual(result.state, "REVIEW")
        self.assertIn("đề xuất", result.summary.lower())
        self.assertIn("phê duyệt", result.summary.lower())

    def test_deterministic_query_bypasses_model_zero_quota(self):
        """Deterministic query sets model_needed = False and max_turns = 0."""
        task, scope = self.make_task_and_scope(
            actor_id=7,
            instruction="Đếm tổng số công việc trong dự án",
        )

        plan, result = self.supervisor.execute_task(
            task, scope, self.sample_packages, actor_role="PM"
        )

        self.assertFalse(plan.budget.model_needed)
        self.assertEqual(plan.budget.max_turns, 0)
        self.assertEqual(plan.budget.token_estimate, 0)
        self.assertFalse(result.model_used)


if __name__ == "__main__":
    unittest.main()

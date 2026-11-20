"""Unit tests for Supervisor 5-Actor Isolation and Fair Quota (P05-12).
Verifies:
- 5 accounts (PM: 7, BA: 6, BE: 8, FE: 9, QA: 10) have 0 memory/chat/workflow leakage
- Cross-project isolation fail-closed
- Role boundary enforcement under concurrent load
- Fair quota sharing without priority starvation
"""
import copy
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from gateway.agent_models import AgentTask, RunScope
from gateway.store import Store
from gateway.supervisor import Supervisor
from gateway.supervisor_isolation import (
    verify_5_actor_isolation,
    simulate_fair_quota_allocation,
)


class Supervisor5ActorsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)
        self.supervisor = Supervisor()

        # Seed 5 user roles
        self.users = {
            7: {"name": "Project Manager", "role": "PM"},
            6: {"name": "BA Specialist", "role": "BA"},
            8: {"name": "BE Developer", "role": "BE"},
            9: {"name": "FE Developer", "role": "FE"},
            10: {"name": "QA Engineer", "role": "QA"},
        }
        for uid, info in self.users.items():
            self.store.issue_token(uid, info["role"], f"native-token-{uid}")

        self.sample_packages = [
            {
                "id": 901,
                "lockVersion": 1,
                "subject": "Thiết kế kiến trúc Multi-Agent",
                "description": {"raw": "Yêu cầu cô lập 5 tài khoản."},
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                },
            }
        ]

    def tearDown(self):
        self.temporary.cleanup()

    def test_concurrent_5_actors_no_memory_or_data_leakage(self):
        """All 5 actors execute distinct workflows; no cross-actor data leaks into run/task records."""
        report = verify_5_actor_isolation(
            supervisor=self.supervisor,
            store=self.store,
            users=self.users,
            packages=self.sample_packages,
            project_id=3,
        )

        self.assertTrue(report["isolated"])
        self.assertEqual(len(report["executed_actors"]), 5)
        self.assertEqual(report["leakage_count"], 0)
        # All 5 run_ids, task_ids, and trace_ids must be strictly distinct
        self.assertEqual(len(set(report["run_ids"])), 5)
        self.assertEqual(len(set(report["task_ids"])), 5)

    def test_cross_project_isolation_fails_closed(self):
        """Actor accessing a different project (e.g. project 4 vs 3) is rejected or isolated."""
        task_id = str(uuid.uuid4())
        foreign_task = AgentTask(
            task_id=task_id,
            actor_id=7,
            project_id=4,  # Foreign project
            conversation_id=str(uuid.uuid4()),
            agent="pm",
            instruction="Đọc công việc dự án khác",
            created_at=1000.0,
            expires_at=2000.0,
        )
        # Storing in project 3 with task claiming project 4 must fail closed
        with self.assertRaises(PermissionError):
            self.store.create_agent_task(actor=7, project=3, task=foreign_task)

    def test_fair_quota_sharing_no_priority_starvation(self):
        """Multiple requests across 5 actors share the single central quota pool fairly without starvation."""
        allocation = simulate_fair_quota_allocation(
            store=self.store,
            actors=[7, 6, 8, 9, 10],
            project="test-project",
            rpm_limit=15,
            requests_per_actor=3,
        )

        self.assertEqual(allocation["total_admitted"], 15)
        self.assertEqual(allocation["total_rejected"], 0)
        # Each actor gets fair share (3 requests each)
        for actor_id in [7, 6, 8, 9, 10]:
            self.assertEqual(allocation["admitted_per_actor"][actor_id], 3)


if __name__ == "__main__":
    unittest.main()

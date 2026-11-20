"""Unit tests for Multi-User Capacity (1 to 20 Users) under CR-USER-CAPACITY-20.
Verifies:
- 20 user accounts configured across roles (e.g., 2 PM, 3 BA, 5 FE, 5 BE, 5 QA)
- Multi-actor token generation and local_operator token_count up to 20 actors
- Complete data and workflow isolation across all 20 actors with zero leakage
- Strict RBAC preservation: multi-user per role, PM-only write, non-PM analyze/read
- Fair quota sharing among 20 actors without starvation
- Daily brief deterministic snapshot aggregation for up to 20 actors
"""
import copy
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from gateway.agent_models import AgentTask, RunScope
from gateway.daily_brief import day
from gateway.local_operator import execute
from gateway.permissions import allowed, require
from gateway.store import Store
from gateway.supervisor import Supervisor
from gateway.supervisor_isolation import (
    verify_actor_isolation,
    simulate_fair_quota_allocation,
)


class Capacity20UsersTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)
        self.supervisor = Supervisor()

        # Seed 20 users: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA
        # IDs 101-120
        self.users = {}
        # 2 PMs
        for uid in (101, 102):
            self.users[uid] = {"name": f"Project Manager {uid}", "role": "PM"}
        # 3 BAs
        for uid in (103, 104, 105):
            self.users[uid] = {"name": f"Business Analyst {uid}", "role": "BA"}
        # 5 FEs
        for uid in range(106, 111):
            self.users[uid] = {"name": f"Frontend Developer {uid}", "role": "FE"}
        # 5 BEs
        for uid in range(111, 116):
            self.users[uid] = {"name": f"Backend Developer {uid}", "role": "BE"}
        # 5 QAs
        for uid in range(116, 121):
            self.users[uid] = {"name": f"QA Engineer {uid}", "role": "QA"}

        # Issue native tokens for all 20 users
        for uid, info in self.users.items():
            self.store.issue_token(uid, info["role"], f"native-token-{uid}")

        self.sample_packages = [
            {
                "id": 1001,
                "lockVersion": 1,
                "subject": "Kiến trúc hệ thống mở rộng 20 người dùng LAN",
                "description": {"raw": "Quy mô 20 tài khoản, phân quyền RBAC và Fair Queue."},
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/101", "title": "Project Manager 101"},
                },
            }
        ]

    def tearDown(self):
        self.temporary.cleanup()

    def test_twenty_actors_registration_and_token_count(self):
        """All 20 actors are registered in store, and local_operator token_count handles up to 20."""
        actors_list = list(self.users.keys())
        self.assertEqual(len(actors_list), 20)

        packet = {
            "operation": "token_count",
            "arguments": {"actors": actors_list},
        }
        count = execute(packet, root=self.root)
        self.assertEqual(count, 20)

        # > 20 actors in token_count must be rejected (guard boundary)
        over_limit_packet = {
            "operation": "token_count",
            "arguments": {"actors": actors_list + [121]},
        }
        with self.assertRaises(ValueError):
            execute(over_limit_packet, root=self.root)

    def test_twenty_actors_no_memory_or_data_leakage(self):
        """All 20 actors execute distinct workflows; zero cross-actor data leaks into run/task records."""
        report = verify_actor_isolation(
            supervisor=self.supervisor,
            store=self.store,
            users=self.users,
            packages=self.sample_packages,
            project_id=3,
        )

        self.assertTrue(report["isolated"])
        self.assertEqual(len(report["executed_actors"]), 20)
        self.assertEqual(report["leakage_count"], 0)
        # All 20 run_ids, task_ids must be strictly distinct
        self.assertEqual(len(set(report["run_ids"])), 20)
        self.assertEqual(len(set(report["task_ids"])), 20)

    def test_multi_user_per_role_rbac_pm_only_write(self):
        """Verify strict RBAC: multiple users per role, PM-only write, non-PMs read/analyze/comment only."""
        pm_users = [uid for uid, u in self.users.items() if u["role"] == "PM"]
        non_pm_users = [uid for uid, u in self.users.items() if u["role"] != "PM"]

        self.assertEqual(len(pm_users), 2)
        self.assertEqual(len(non_pm_users), 18)

        # Both PMs can execute write operations
        for pm_id in pm_users:
            role = self.users[pm_id]["role"]
            self.assertTrue(allowed(role, "create_work_package"))
            self.assertTrue(allowed(role, "update_work_package"))
            self.assertTrue(allowed(role, "transition"))
            require(role, "create_work_package")
            require(role, "update_work_package")

        # None of the 18 non-PM users can execute write operations
        for non_pm_id in non_pm_users:
            role = self.users[non_pm_id]["role"]
            self.assertFalse(allowed(role, "create_work_package"))
            self.assertFalse(allowed(role, "update_work_package"))
            self.assertFalse(allowed(role, "transition"))
            with self.assertRaises(PermissionError):
                require(role, "create_work_package")
            with self.assertRaises(PermissionError):
                require(role, "transition")

            # But all non-PM users can read, analyze, and comment
            self.assertTrue(allowed(role, "comment"))
            self.assertTrue(allowed(role, "analyze"))
            self.assertTrue(allowed(role, "read"))
            require(role, "comment")
            require(role, "analyze")

    def test_twenty_actors_fair_queue_without_starvation(self):
        """Simulate fair round-robin quota reservations across 20 actors without priority starvation."""
        actors_list = list(self.users.keys())
        allocation = simulate_fair_quota_allocation(
            store=self.store,
            actors=actors_list,
            project="test-project",
            rpm_limit=15,
            requests_per_actor=2,
        )

        # 20 actors * 2 requests = 40 total requests
        # First 15 are admitted (matching RPM limit of 15), remaining are rejected fairly
        self.assertEqual(allocation["total_admitted"], 15)
        self.assertEqual(allocation["total_rejected"], 25)

        # Verify that all first 15 actors got 1 reservation, and no single actor monopolized
        for actor_id in actors_list[:15]:
            self.assertEqual(allocation["admitted_per_actor"][actor_id], 1)
        for actor_id in actors_list[15:]:
            self.assertEqual(allocation["admitted_per_actor"][actor_id], 0)

    def test_daily_brief_twenty_actors_collection_and_partial_handling(self):
        """Daily brief collects snapshots for all 20 actors and handles partial outages correctly."""
        command = {
            "version": 1,
            "kind": "daily_brief",
            "request_key": "daily:" + day(),
            "nonce": str(uuid.uuid4()),
            "issued_at": int(time.time()),
        }
        receipt, created = self.store.begin_automation(command, project=3, targets=20)
        self.assertTrue(created)
        self.assertEqual(receipt["targets"], 20)
        self.assertEqual(receipt["state"], "RUNNING")

        # 1. Full 20 ready reports
        reports = []
        for uid, info in self.users.items():
            reports.append({
                "actor": uid,
                "project": 3,
                "day": day(),
                "run_id": receipt["run_id"],
                "trace_id": receipt["trace_id"],
                "role": info["role"],
                "state": "READY",
                "snapshot": {"count": 1, "by_status": {}, "overdue_ids": []},
            })

        completed = self.store.finish_daily_brief(receipt["run_id"], reports)
        self.assertEqual(completed["state"], "COMPLETED")
        self.assertEqual(completed["status"], "READY")
        self.assertEqual(completed["ready"], 20)
        self.assertEqual(completed["unavailable"], 0)

        # 2. Test partial collection with 20 actors (17 READY, 2 OFFLINE, 1 DENIED)
        command_partial = {
            "version": 1,
            "kind": "daily_brief",
            "request_key": "daily:2099-01-01",
            "nonce": str(uuid.uuid4()),
            "issued_at": int(time.time()),
        }
        receipt_p, _ = self.store.begin_automation(command_partial, project=3, targets=20)
        partial_reports = copy.deepcopy(reports)
        for r in partial_reports:
            r["day"] = "2099-01-01"
            r["run_id"] = receipt_p["run_id"]
            r["trace_id"] = receipt_p["trace_id"]

        partial_reports[0]["state"] = "OFFLINE"
        partial_reports[1]["state"] = "OFFLINE"
        partial_reports[2]["state"] = "DENIED"

        completed_p = self.store.finish_daily_brief(receipt_p["run_id"], partial_reports)
        self.assertEqual(completed_p["state"], "COMPLETED")
        self.assertEqual(completed_p["status"], "PARTIAL")
        self.assertEqual(completed_p["ready"], 17)
        self.assertEqual(completed_p["unavailable"], 3)


if __name__ == "__main__":
    unittest.main()

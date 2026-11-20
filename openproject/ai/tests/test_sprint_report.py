"""Unit tests for P07-01: Deterministic Daily Sprint Report (supporting up to 20 users).
Verifies:
- 100% deterministic calculation (model_used: False, 0 Gemini tokens consumed)
- Complete metrics: total, open, closed, progress %, by status, by type
- Overdue tasks detection and days overdue calculation
- Blocker tracking with dependency linkage
- Multi-user workload distribution across 1-20 users
- Role-based scoping: PM sees full team workload; non-PM sees personal scope only
- Service execution integration and argument validation
- Sprint health indicators and process-support disclaimers
"""
from datetime import date
import tempfile
import unittest
from pathlib import Path

from gateway.sprint_report import generate_sprint_report
from gateway.store import Store
from gateway.service import Service
from tests import test_local_queries as fixture


class SprintReportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.LocalQueryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.store, self.service, self.root, self.state = (
            self.fixture.store,
            self.fixture.service,
            self.fixture.root,
            self.fixture.state,
        )

        # 20 users map (2 PM, 3 BA, 5 FE, 5 BE, 5 QA)
        self.users = {}
        for uid in (101, 102):
            self.users[uid] = {"name": f"PM {uid}", "role": "PM"}
        for uid in (103, 104, 105):
            self.users[uid] = {"name": f"BA {uid}", "role": "BA"}
        for uid in range(106, 111):
            self.users[uid] = {"name": f"FE {uid}", "role": "FE"}
        for uid in range(111, 116):
            self.users[uid] = {"name": f"BE {uid}", "role": "BE"}
        for uid in range(116, 121):
            self.users[uid] = {"name": f"QA {uid}", "role": "QA"}

        # Configure service users and issue credentials
        self.service.config.update(
            users={str(uid): info["role"] for uid, info in self.users.items()}
        )
        self.state.roles = {uid: info["role"] for uid, info in self.users.items()}
        for uid, info in self.users.items():
            self.store.issue_token(uid, info["role"], f"synthetic-native-{uid}")

        # Sample work packages
        self.packages = [
            {
                "id": 1,
                "lockVersion": 1,
                "subject": "Thiết kế kiến trúc hệ thống",
                "type": "Epic",
                "status": "In Progress",
                "dueDate": "2026-10-10",
                "_links": {
                    "status": {"title": "In Progress"},
                    "type": {"title": "Epic"},
                    "assignee": {"href": "/api/v3/users/101", "title": "PM 101"},
                },
            },
            {
                "id": 2,
                "lockVersion": 2,
                "subject": "Đặc tả yêu cầu phần mềm",
                "type": "Story",
                "status": "Done",
                "dueDate": "2026-10-12",
                "_links": {
                    "status": {"title": "Done"},
                    "type": {"title": "Story"},
                    "assignee": {"href": "/api/v3/users/103", "title": "BA 103"},
                },
            },
            {
                "id": 3,
                "lockVersion": 1,
                "subject": "Phát triển API Gateway",
                "type": "Task",
                "status": "In Progress",
                "dueDate": "2026-10-14",
                "_links": {
                    "status": {"title": "In Progress"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/111", "title": "BE 111"},
                },
            },
            {
                "id": 4,
                "lockVersion": 1,
                "subject": "Giao diện Dashboard [BLOCKED]",
                "description": {"raw": "Bị chặn bởi #3; chờ API backend."},
                "type": "Task",
                "status": "Blocked",
                "dueDate": "2026-10-20",
                "_links": {
                    "status": {"title": "Blocked"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/106", "title": "FE 106"},
                },
            },
            {
                "id": 5,
                "lockVersion": 1,
                "subject": "Kiểm thử hồi quy tự động",
                "type": "Task",
                "status": "New",
                "dueDate": None,
                "_links": {
                    "status": {"title": "New"},
                    "type": {"title": "Task"},
                },
            },
        ]

    def test_deterministic_report_generation_zero_tokens(self):
        """Report generates 100% deterministically with zero tokens and exact metrics."""
        ref_date = date(2026, 10, 16)
        report = generate_sprint_report(
            packages=self.packages,
            as_of_date=ref_date,
            user_map=self.users,
            actor_id=101,
            actor_role="PM",
            project_id=3,
        )

        self.assertEqual(report["state"], "READY")
        self.assertFalse(report["model_used"])
        self.assertEqual(report["project_id"], 3)
        self.assertEqual(report["actor_id"], 101)
        self.assertIn("fingerprint", report)

        body = report["report"]
        summary = body["summary"]
        self.assertEqual(summary["total_packages"], 5)
        self.assertEqual(summary["closed_packages"], 1)
        self.assertEqual(summary["open_packages"], 4)
        self.assertEqual(summary["progress_percent"], 20.0)
        self.assertEqual(summary["unassigned_open_count"], 1)
        self.assertEqual(summary["missing_deadline_open_count"], 1)

        # Status and type distribution
        self.assertEqual(summary["by_status"]["In Progress"], 2)
        self.assertEqual(summary["by_status"]["Done"], 1)
        self.assertEqual(summary["by_status"]["Blocked"], 1)
        self.assertEqual(summary["by_type"]["Epic"], 1)
        self.assertEqual(summary["by_type"]["Story"], 1)
        self.assertEqual(summary["by_type"]["Task"], 3)

        # Overdue check: task 1 (due 10-10 -> 6 days), task 3 (due 10-14 -> 2 days)
        # task 2 is closed, so not overdue
        overdue_ids = [item["id"] for item in body["overdue"]]
        self.assertEqual(overdue_ids, [1, 3])
        self.assertEqual(body["overdue"][0]["days_overdue"], 6)

        # Blocked check: task 4 is blocked by #3
        self.assertEqual(len(body["blocked"]), 1)
        self.assertEqual(body["blocked"][0]["id"], 4)
        self.assertEqual(body["blocked"][0]["blocker_ids"], [3])

    def test_multi_user_workload_distribution(self):
        """Workload summary correctly partitions open tasks across up to 20 users."""
        report = generate_sprint_report(
            packages=self.packages,
            as_of_date=date(2026, 10, 16),
            user_map=self.users,
            actor_id=101,
            actor_role="PM",
        )

        workload = report["report"]["workload"]
        # PM 101 has task 1
        self.assertEqual(workload["101"]["open_count"], 1)
        self.assertEqual(workload["101"]["package_ids"], [1])
        # BA 103's task 2 is closed, open count 0
        self.assertEqual(workload["103"]["open_count"], 0)
        # FE 106 has task 4
        self.assertEqual(workload["106"]["open_count"], 1)
        # BE 111 has task 3
        self.assertEqual(workload["111"]["open_count"], 1)
        # Unassigned open has task 5
        self.assertEqual(workload["unassigned"]["open_count"], 1)
        self.assertEqual(workload["unassigned"]["package_ids"], [5])

    def test_role_based_scoping_pm_vs_non_pm(self):
        """PM receives full team visibility; non-PM receives project counts and personal scope only."""
        ref_date = date(2026, 10, 16)

        # 1. PM view
        pm_report = generate_sprint_report(
            packages=self.packages,
            as_of_date=ref_date,
            user_map=self.users,
            actor_id=101,
            actor_role="PM",
        )
        # PM sees all overdue items (1 and 3)
        self.assertEqual(len(pm_report["report"]["overdue"]), 2)
        # PM sees workload for all users
        self.assertIn("106", pm_report["report"]["workload"])
        self.assertIn("111", pm_report["report"]["workload"])

        # 2. Non-PM view (BE 111)
        be_report = generate_sprint_report(
            packages=self.packages,
            as_of_date=ref_date,
            user_map=self.users,
            actor_id=111,
            actor_role="BE",
        )
        # BE only sees their own overdue item (task 3), NOT task 1 (assigned to PM 101)
        self.assertEqual(len(be_report["report"]["overdue"]), 1)
        self.assertEqual(be_report["report"]["overdue"][0]["id"], 3)
        # BE workload only exposes BE 111 and project totals, not other users' individual workloads
        be_workload = be_report["report"]["workload"]
        self.assertIn("111", be_workload)
        self.assertNotIn("106", be_workload)
        self.assertNotIn("101", be_workload)
        self.assertEqual(be_workload["project_totals"]["total_open"], 4)

    def test_sprint_health_indicators_and_disclaimers(self):
        """Sprint health provides objective state and mandatory ethical/process disclaimers."""
        report = generate_sprint_report(
            packages=self.packages,
            as_of_date=date(2026, 10, 16),
            user_map=self.users,
            actor_id=101,
            actor_role="PM",
        )
        health = report["report"]["sprint_health"]
        self.assertIn(health["status"], {"AT_RISK", "CRITICAL"})
        self.assertTrue(len(health["reasons"]) > 0)

        # Ethical and operational disclaimers present
        limitations = report["report"]["limitations"]
        self.assertTrue(any("không xếp hạng cá nhân" in item for item in limitations))
        self.assertTrue(any("không tiêu tốn token LLM" in item for item in limitations))

    def test_service_execute_actor_sprint_report(self):
        """Service properly provides sprint_report method, embeds into analyze, and validates arguments."""
        # Setup native mock
        self.state.packages = self.packages
        original = self.service.native_factory
        test = self

        class MockNative(original):
            def packages(self):
                return test.packages
            def relations(self, packages):
                return []

        self.service.native_factory = MockNative

        # 1. Execute direct sprint_report as PM 101
        res = self.service.sprint_report(
            101,
            {"as_of_date": "2026-10-16"},
        )
        self.assertEqual(res["state"], "READY")
        self.assertEqual(res["report"]["summary"]["total_packages"], 5)

        # 2. Execute via analyze action
        analyze_res = self.service.execute_actor(
            101,
            {"action": "analyze", "arguments": {}},
        )["result"]
        self.assertIn("sprint_report", analyze_res)
        self.assertEqual(analyze_res["sprint_report"]["state"], "READY")
        self.assertEqual(analyze_res["sprint_report"]["report"]["summary"]["total_packages"], 5)

        # 3. Invalid argument key rejected
        with self.assertRaises(ValueError):
            self.service.sprint_report(
                101,
                {"invalid_arg": True},
            )

        # 4. Invalid date format rejected
        with self.assertRaises(ValueError):
            self.service.sprint_report(
                101,
                {"as_of_date": "not-a-date"},
            )


if __name__ == "__main__":
    unittest.main()

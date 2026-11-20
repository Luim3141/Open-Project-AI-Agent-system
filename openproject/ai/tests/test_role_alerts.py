"""Unit tests for P07-02: Role-based Deadline & Blocker Alerts with Deduplication.
Enforces:
1. Deduplication of alerts across runs for unchanged work packages.
2. Fail-closed role scoping: PM gets project-wide alerts; non-PM (BA/FE/BE/QA) gets only personal alerts.
3. Zero cross-role leakage of sensitive overdue details.
4. Pure deterministic processing (0 LLM tokens).
5. Multi-user compatibility (1 to 20 users).
"""
import unittest
from datetime import date, timedelta
from openproject.ai.gateway.role_alerts import (
    generate_role_alerts,
    deduplicate_alerts,
    AlertEngine,
)


class TestRoleAlerts(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 17)
        # 20 users configuration: 2 PMs, 3 BAs, 5 FEs, 5 BEs, 5 QAs
        self.users = {
            1: {"name": "PM Lead 1", "role": "PM"},
            2: {"name": "PM Assistant 2", "role": "PM"},
            3: {"name": "BA Lead 3", "role": "BA"},
            4: {"name": "BA Analyst 4", "role": "BA"},
            5: {"name": "BA Analyst 5", "role": "BA"},
            6: {"name": "FE Lead 6", "role": "FE"},
            7: {"name": "FE Dev 7", "role": "FE"},
            8: {"name": "FE Dev 8", "role": "FE"},
            9: {"name": "FE Dev 9", "role": "FE"},
            10: {"name": "FE Dev 10", "role": "FE"},
            11: {"name": "BE Lead 11", "role": "BE"},
            12: {"name": "BE Dev 12", "role": "BE"},
            13: {"name": "BE Dev 13", "role": "BE"},
            14: {"name": "BE Dev 14", "role": "BE"},
            15: {"name": "BE Dev 15", "role": "BE"},
            16: {"name": "QA Lead 16", "role": "QA"},
            17: {"name": "QA Tester 17", "role": "QA"},
            18: {"name": "QA Tester 18", "role": "QA"},
            19: {"name": "QA Tester 19", "role": "QA"},
            20: {"name": "QA Tester 20", "role": "QA"},
        }

        # Mock work packages with various states: overdue, blocked, normal, done
        self.packages = [
            {
                "id": 101,
                "lockVersion": 3,
                "subject": "FE Authentication UI",
                "_links": {
                    "status": {"title": "In Progress"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/6", "title": "FE Lead 6"},
                },
                "dueDate": (self.today - timedelta(days=5)).isoformat(),  # Overdue 5 days
                "percentageDone": 40,
                "description": {"raw": "Cần hoàn thiện màn hình đăng nhập."},
            },
            {
                "id": 102,
                "lockVersion": 2,
                "subject": "BE Login API Token",
                "_links": {
                    "status": {"title": "In Progress"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/11", "title": "BE Lead 11"},
                },
                "dueDate": (self.today - timedelta(days=1)).isoformat(),  # Overdue 1 day
                "percentageDone": 80,
                "description": {"raw": "API cấp JWT token."},
            },
            {
                "id": 103,
                "lockVersion": 4,
                "subject": "FE Dashboard Integration [BLOCKED]",
                "_links": {
                    "status": {"title": "Blocked"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/7", "title": "FE Dev 7"},
                },
                "dueDate": (self.today + timedelta(days=3)).isoformat(),
                "percentageDone": 20,
                "description": {"raw": "Bị chặn bởi #102 do API chưa deploy."},
            },
            {
                "id": 104,
                "lockVersion": 1,
                "subject": "QA Test Plan Sprint 1",
                "_links": {
                    "status": {"title": "Specified"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/16", "title": "QA Lead 16"},
                },
                "dueDate": (self.today + timedelta(days=5)).isoformat(),
                "percentageDone": 0,
                "description": {"raw": "Kế hoạch kiểm thử Sprint 1."},
            },
            {
                "id": 105,
                "lockVersion": 5,
                "subject": "Database Migration Script",
                "_links": {
                    "status": {"title": "Done"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/12", "title": "BE Dev 12"},
                },
                "dueDate": (self.today - timedelta(days=2)).isoformat(),  # Closed, should not alert
                "percentageDone": 100,
                "description": {"raw": "Đã chạy migration thành công."},
            },
        ]

    def test_pm_gets_all_project_alerts(self):
        """PM receives all overdue and blocker alerts across all roles."""
        result = generate_role_alerts(
            packages=self.packages,
            actor_id=1,
            actor_role="PM",
            as_of_date=self.today,
            project_id=3,
        )
        self.assertEqual(result["state"], "READY")
        self.assertFalse(result["model_used"])
        alerts = result["alerts"]

        # Should have alerts for:
        # - #101: Overdue 5 days (FE Lead 6)
        # - #102: Overdue 1 day (BE Lead 11)
        # - #103: Blocked by #102 (FE Dev 7)
        # #105 is Done, so no alert. #104 is on track.
        alert_pkg_ids = {a["package_id"] for a in alerts}
        self.assertIn(101, alert_pkg_ids)
        self.assertIn(102, alert_pkg_ids)
        self.assertIn(103, alert_pkg_ids)
        self.assertNotIn(105, alert_pkg_ids)
        self.assertNotIn(104, alert_pkg_ids)

        # Check severity calculation
        high_severity = [a for a in alerts if a["severity"] == "HIGH"]
        # #101 (overdue 5 days) and #103 (blocker) should be HIGH
        high_ids = {a["package_id"] for a in high_severity}
        self.assertIn(101, high_ids)
        self.assertIn(103, high_ids)

    def test_non_pm_role_isolation_fe(self):
        """FE Lead 6 only receives alerts for their own tasks (#101), never BE's tasks (#102)."""
        result = generate_role_alerts(
            packages=self.packages,
            actor_id=6,
            actor_role="FE",
            as_of_date=self.today,
            project_id=3,
        )
        self.assertEqual(result["state"], "READY")
        alerts = result["alerts"]
        alert_pkg_ids = {a["package_id"] for a in alerts}

        self.assertIn(101, alert_pkg_ids)
        self.assertNotIn(102, alert_pkg_ids, "Cross-role leak: FE saw BE overdue task!")
        self.assertNotIn(103, alert_pkg_ids, "FE Lead 6 saw FE Dev 7 private alert!")

    def test_non_pm_role_isolation_be(self):
        """BE Lead 11 only receives alerts for their own tasks (#102), never FE's tasks (#101, #103)."""
        result = generate_role_alerts(
            packages=self.packages,
            actor_id=11,
            actor_role="BE",
            as_of_date=self.today,
            project_id=3,
        )
        self.assertEqual(result["state"], "READY")
        alerts = result["alerts"]
        alert_pkg_ids = {a["package_id"] for a in alerts}

        self.assertIn(102, alert_pkg_ids)
        self.assertNotIn(101, alert_pkg_ids, "Cross-role leak: BE saw FE overdue task!")
        self.assertNotIn(103, alert_pkg_ids, "Cross-role leak: BE saw FE blocker!")

    def test_deduplication_engine(self):
        """Verifies deduplication across consecutive alert runs."""
        engine = AlertEngine()

        # Run 1
        run1 = engine.evaluate(self.packages, actor_id=1, actor_role="PM", as_of_date=self.today, project_id=3)
        self.assertEqual(len(run1["alerts"]), 3)
        self.assertEqual(run1["deduplicated_count"], 0)

        # Run 2 with exact same packages and state
        run2 = engine.evaluate(self.packages, actor_id=1, actor_role="PM", as_of_date=self.today, project_id=3)
        # Active alerts are recognized as existing/deduplicated
        self.assertEqual(run2["deduplicated_count"], 3)
        self.assertEqual(run2["new_alerts_count"], 0)

        # Now change package 101's lockVersion (task was updated)
        updated_packages = [dict(p) for p in self.packages]
        updated_packages[0] = dict(updated_packages[0])
        updated_packages[0]["lockVersion"] = 4  # New version!
        run3 = engine.evaluate(updated_packages, actor_id=1, actor_role="PM", as_of_date=self.today, project_id=3)
        # #101 should be detected as new/updated version
        self.assertEqual(run3["new_alerts_count"], 1)
        self.assertEqual(run3["deduplicated_count"], 2)

    def test_20_users_fail_closed(self):
        """Verifies consistent isolation across all 20 accounts without error."""
        engine = AlertEngine()
        for uid, uinfo in self.users.items():
            res = engine.evaluate(self.packages, actor_id=uid, actor_role=uinfo["role"], as_of_date=self.today, project_id=3)
            self.assertEqual(res["state"], "READY")
            self.assertFalse(res["model_used"])
            if uinfo["role"] != "PM":
                # Ensure no other user's task is present in this user's alerts
                for alert in res["alerts"]:
                    self.assertEqual(alert["assignee_id"], uid)


if __name__ == "__main__":
    unittest.main()

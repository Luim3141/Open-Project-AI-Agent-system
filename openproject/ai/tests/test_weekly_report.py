"""Unit tests for P07-03: Weekly Report Workflow with Project Scoping & Optional AI Summary.
Enforces:
1. Current Native status/update counts; unknown closure throughput stays null without transition history.
2. Fail-closed role scoping: PM gets full project overview; non-PM (BA/FE/BE/QA) sees project totals + personal contribution only.
3. No cross-role leakage of individual member data.
4. Optional AI summary with quota budget check: fallback to deterministic narrative when AI disabled or budget tight.
5. Scale to 20 users (CR-USER-CAPACITY-20).
"""
import unittest
from datetime import date, timedelta
from openproject.ai.gateway.weekly_report import (
    generate_weekly_report,
    WeeklyReportEngine,
)


class TestWeeklyReport(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 17)
        # 20 users configuration: 2 PMs, 3 BAs, 5 FEs, 5 BEs, 5 QAs
        self.users = {
            1: {"name": "PM 1", "role": "PM"},
            2: {"name": "PM 2", "role": "PM"},
            3: {"name": "BA 1", "role": "BA"},
            4: {"name": "BA 2", "role": "BA"},
            5: {"name": "BA 3", "role": "BA"},
            6: {"name": "FE 1", "role": "FE"},
            7: {"name": "FE 2", "role": "FE"},
            8: {"name": "FE 3", "role": "FE"},
            9: {"name": "FE 4", "role": "FE"},
            10: {"name": "FE 5", "role": "FE"},
            11: {"name": "BE 1", "role": "BE"},
            12: {"name": "BE 2", "role": "BE"},
            13: {"name": "BE 3", "role": "BE"},
            14: {"name": "BE 4", "role": "BE"},
            15: {"name": "BE 5", "role": "BE"},
            16: {"name": "QA 1", "role": "QA"},
            17: {"name": "QA 2", "role": "QA"},
            18: {"name": "QA 3", "role": "QA"},
            19: {"name": "QA 4", "role": "QA"},
            20: {"name": "QA 5", "role": "QA"},
        }

        # Work packages over the last 7 days and future
        self.packages = [
            # Currently closed, updated this week by FE 1; closure timestamp is unknown.
            {
                "id": 401,
                "lockVersion": 5,
                "subject": "FE Login Screen",
                "_links": {
                    "status": {"title": "Done"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/6", "title": "FE 1"},
                },
                "updatedAt": (self.today - timedelta(days=2)).isoformat() + "T10:00:00Z",
                "percentageDone": 100,
            },
            # Currently closed, updated this week by BE 1; closure timestamp is unknown.
            {
                "id": 402,
                "lockVersion": 4,
                "subject": "BE Auth Endpoint",
                "_links": {
                    "status": {"title": "Done"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/11", "title": "BE 1"},
                },
                "updatedAt": (self.today - timedelta(days=3)).isoformat() + "T14:00:00Z",
                "percentageDone": 100,
            },
            # Open in progress by FE 1
            {
                "id": 403,
                "lockVersion": 2,
                "subject": "FE Profile Settings",
                "_links": {
                    "status": {"title": "In Progress"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/6", "title": "FE 1"},
                },
                "dueDate": (self.today + timedelta(days=3)).isoformat(),
                "percentageDone": 50,
            },
            # Open in progress by BE 2
            {
                "id": 404,
                "lockVersion": 1,
                "subject": "BE User Schema Migration",
                "_links": {
                    "status": {"title": "In Progress"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/12", "title": "BE 2"},
                },
                "dueDate": (self.today + timedelta(days=4)).isoformat(),
                "percentageDone": 30,
            },
            # Overdue task by QA 1
            {
                "id": 405,
                "lockVersion": 3,
                "subject": "QA Test Execution Sprint",
                "_links": {
                    "status": {"title": "In Progress"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/16", "title": "QA 1"},
                },
                "dueDate": (self.today - timedelta(days=2)).isoformat(),
                "percentageDone": 20,
            },
        ]

    def test_raw_counts_and_metrics(self):
        """Known update/status counts and unavailable transition metrics remain distinct."""
        report = generate_weekly_report(
            packages=self.packages,
            users=self.users,
            actor_id=1,
            actor_role="PM",
            as_of_date=self.today,
            with_ai_summary=False,
        )
        self.assertEqual(report["state"], "READY")
        self.assertFalse(report["model_used"])

        counts = report["weekly_summary"]["raw_counts"]
        self.assertIsNone(counts["closed_this_week"])
        self.assertEqual(counts['closed_updated_in_window'],2)
        self.assertEqual(counts["open_total"], 3)
        self.assertEqual(counts["overdue_count"], 1)
        self.assertEqual(counts["upcoming_deadlines_7d"], 2)
        self.assertIsNone(counts["throughput_velocity"])

    def test_pm_sees_all_member_breakdown(self):
        """PM receives detailed breakdown across all 20 members."""
        report = generate_weekly_report(
            packages=self.packages,
            users=self.users,
            actor_id=1,
            actor_role="PM",
            as_of_date=self.today,
        )
        members = report["member_breakdown"]
        self.assertEqual(len(members), 20)
        # FE 1 closed #401 and has #403 in progress
        self.assertIsNone(members["6"]["closed_this_week"])
        self.assertEqual(members['6']['closed_updated_in_window'],1)
        self.assertEqual(members["6"]["open_active"], 1)

    def test_non_pm_sees_project_totals_and_personal_only(self):
        """FE 1 receives project summary raw counts, but personal breakdown only (no BE/QA private details)."""
        report = generate_weekly_report(
            packages=self.packages,
            users=self.users,
            actor_id=6,
            actor_role="FE",
            as_of_date=self.today,
        )
        self.assertEqual(report["state"], "READY")
        # Can see project summary totals
        self.assertIsNone(report["weekly_summary"]["raw_counts"]["closed_this_week"])
        self.assertEqual(report['weekly_summary']['raw_counts']['closed_updated_in_window'],2)

        # But member breakdown ONLY contains actor 6, NOT other users
        members = report["member_breakdown"]
        self.assertIn("6", members)
        self.assertNotIn("11", members, "Cross-role leak: FE saw BE member data!")
        self.assertNotIn("16", members, "Cross-role leak: FE saw QA member data!")

    def test_deterministic_summary_without_ai(self):
        """When with_ai_summary=False, provides pure deterministic narrative with 0 tokens."""
        report = generate_weekly_report(
            packages=self.packages,
            users=self.users,
            actor_id=1,
            actor_role="PM",
            as_of_date=self.today,
            with_ai_summary=False,
        )
        self.assertFalse(report["model_used"])
        self.assertEqual(report["ai_summary"]["status"], "DETERMINISTIC_ONLY")
        self.assertIn("2 công việc hiện đóng được cập nhật", report["ai_summary"]["text"])
        self.assertIn('Chưa đủ lịch sử chuyển trạng thái',report['ai_summary']['text'])

    def test_scale_20_users_fail_closed(self):
        """Verifies consistent execution across all 20 users without leaks or errors."""
        for uid, uinfo in self.users.items():
            rep = generate_weekly_report(
                packages=self.packages,
                users=self.users,
                actor_id=uid,
                actor_role=uinfo["role"],
                as_of_date=self.today,
                with_ai_summary=False,
            )
            self.assertEqual(rep["state"], "READY")
            if uinfo["role"] != "PM":
                self.assertNotIn(str(11 if uid != 11 else 6), rep["member_breakdown"])


if __name__ == "__main__":
    unittest.main()

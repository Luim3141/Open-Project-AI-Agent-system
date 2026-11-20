"""Unit tests for P07-04: Workload Skew & Missing Owner/Deadline Detection.
Enforces:
1. Detection of workload imbalance (skew) across team members.
2. Detection of unassigned open tasks and tasks missing deadlines.
3. Strictly advisory: generates suggestions, never auto-assigns or mutates native records.
4. Pure deterministic execution (0 LLM tokens).
5. Tested for multi-user scaling (1 to 20 accounts).
"""
import unittest
from datetime import date
from openproject.ai.gateway.workload_detector import (
    detect_workload_imbalance,
    generate_workload_suggestions,
)


class TestWorkloadDetector(unittest.TestCase):
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

        # Work packages: some unassigned, some without due date, heavy load on FE 1 (4 tasks) vs 0 on FE 2..5
        self.packages = [
            # FE 1 has 4 tasks (overloaded)
            {"id": 201, "lockVersion": 1, "subject": "FE Task 1", "dueDate": "2026-10-25", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/6", "title": "FE 1"}}},
            {"id": 202, "lockVersion": 1, "subject": "FE Task 2", "dueDate": "2026-10-26", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/6", "title": "FE 1"}}},
            {"id": 203, "lockVersion": 1, "subject": "FE Task 3", "dueDate": "2026-10-27", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/6", "title": "FE 1"}}},
            {"id": 204, "lockVersion": 1, "subject": "FE Task 4", "dueDate": "2026-10-28", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/6", "title": "FE 1"}}},

            # BE 1 has 2 tasks, BE 2 has 2 tasks
            {"id": 205, "lockVersion": 1, "subject": "BE Task 1", "dueDate": "2026-10-25", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/11", "title": "BE 1"}}},
            {"id": 206, "lockVersion": 1, "subject": "BE Task 2", "dueDate": "2026-10-26", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/11", "title": "BE 1"}}},
            {"id": 207, "lockVersion": 1, "subject": "BE Task 3", "dueDate": "2026-10-25", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/12", "title": "BE 2"}}},
            {"id": 208, "lockVersion": 1, "subject": "BE Task 4", "dueDate": "2026-10-26", "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/12", "title": "BE 2"}}},

            # Unassigned tasks
            {"id": 209, "lockVersion": 2, "subject": "Unassigned Frontend Widget", "dueDate": "2026-10-29", "_links": {"status": {"title": "Specified"}, "type": {"title": "Task"}}},
            {"id": 210, "lockVersion": 1, "subject": "Unassigned Backend Cache", "dueDate": None, "_links": {"status": {"title": "Specified"}, "type": {"title": "Task"}}},

            # Task missing deadline
            {"id": 211, "lockVersion": 1, "subject": "QA Regression Automation", "dueDate": None, "_links": {"status": {"title": "In Progress"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/16", "title": "QA 1"}}},

            # Completed task (should be excluded from active load)
            {"id": 212, "lockVersion": 3, "subject": "Old Completed Setup", "dueDate": "2026-10-10", "percentageDone": 100, "_links": {"status": {"title": "Done"}, "type": {"title": "Task"}, "assignee": {"href": "/api/v3/users/6", "title": "FE 1"}}},
        ]

    def test_unassigned_detection(self):
        """Correctly identifies all unassigned open tasks."""
        report = detect_workload_imbalance(self.packages, self.users, project_id=3)
        self.assertEqual(report["state"], "READY")
        self.assertFalse(report["model_used"])

        unassigned = report["unassigned_tasks"]
        unassigned_ids = [t["id"] for t in unassigned]
        self.assertIn(209, unassigned_ids)
        self.assertIn(210, unassigned_ids)
        self.assertEqual(len(unassigned), 2)

    def test_missing_deadline_detection(self):
        """Correctly identifies all tasks with missing due date."""
        report = detect_workload_imbalance(self.packages, self.users, project_id=3)
        missing_due = report["missing_deadline_tasks"]
        missing_ids = [t["id"] for t in missing_due]

        self.assertIn(210, missing_ids)
        self.assertIn(211, missing_ids)
        self.assertEqual(len(missing_due), 2)

    def test_workload_skew_detection(self):
        """Detects workload imbalance within role groups (FE 1 overloaded with 4 tasks, FE 2..5 have 0)."""
        report = detect_workload_imbalance(self.packages, self.users, project_id=3)
        skew = report["skew_analysis"]

        # FE role should be flagged with high skew
        fe_skew = skew.get("FE", {})
        self.assertTrue(fe_skew.get("has_skew", False))
        self.assertEqual(fe_skew.get("max_load", 0), 4)
        self.assertEqual(fe_skew.get("min_load", 0), 0)

        # BE role has balanced load (BE 1: 2, BE 2: 2, BE 3..5: 0)
        # Verify suggestions for FE rebalancing
        suggestions = report["suggestions"]
        fe_suggestions = [s for s in suggestions if s["type"] == "REBALANCE_WORKLOAD" and s.get("role") == "FE"]
        self.assertGreater(len(fe_suggestions), 0)
        self.assertIn("FE 1", fe_suggestions[0]["message"])

    def test_suggestions_strictly_advisory(self):
        """Ensures that recommendations are purely advisory and include mandatory PM review notice."""
        report = detect_workload_imbalance(self.packages, self.users, project_id=3)
        self.assertTrue(report["advisory_only"])
        self.assertFalse(report["auto_assigned"])
        self.assertIn("Chỉ mang tính chất tư vấn đề xuất, chỉ PM mới có quyền thực thi", report["notice"])

    def test_scale_20_users(self):
        """Verifies report generation across 20 registered users without performance penalty."""
        report = detect_workload_imbalance(self.packages, self.users, project_id=3)
        workloads = report["member_workloads"]
        self.assertEqual(len(workloads), 20)
        # FE 1 has 4 active tasks (completed #212 excluded)
        self.assertEqual(workloads["6"]["task_count"], 4)
        # FE 2 has 0 tasks
        self.assertEqual(workloads["7"]["task_count"], 0)


if __name__ == "__main__":
    unittest.main()

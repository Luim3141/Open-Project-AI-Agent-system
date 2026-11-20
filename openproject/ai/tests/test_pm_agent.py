"""Five golden test cases for PM Agent (P05-03).
PM Agent evaluates Sprint risks, work packages overdue, blockers, and workload with evidence,
and STRICTLY refuses to self-update OpenProject tasks.
"""
import unittest
import uuid
from datetime import date

from gateway.agent_models import AgentTask, RunScope, NativeReference
from gateway.pm_agent import PMAgent, analyze_overdue, analyze_blockers, analyze_workload, analyze_sprint_risks


class PMAgentGoldenTests(unittest.TestCase):
    def setUp(self):
        self.actor_id = 7  # PM
        self.project_id = 3
        self.conversation_id = str(uuid.uuid4())
        self.task_id = str(uuid.uuid4())
        self.run_id = str(uuid.uuid4())
        self.trace_id = str(uuid.uuid4())
        self.scope = RunScope(
            run_id=self.run_id,
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            trace_id=self.trace_id,
        )

        self.sample_packages = [
            {
                "id": 101,
                "lockVersion": 3,
                "subject": "Thiết kế API Gateway authentication",
                "dueDate": "2026-10-10",  # Overdue relative to 2026-10-17
                "startDate": "2026-10-01",
                "percentageDone": 40,
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                    "priority": {"href": "/api/v3/priorities/2", "title": "High"},
                },
            },
            {
                "id": 102,
                "lockVersion": 5,
                "subject": "Tích hợp UI Bridge trên Staging",
                "dueDate": "2026-10-12",  # Overdue
                "startDate": "2026-10-05",
                "percentageDone": 20,
                "_links": {
                    "status": {"href": "/api/v3/statuses/7", "title": "BLOCKED"},
                    "assignee": {"href": "/api/v3/users/9", "title": "FE Developer"},
                    "priority": {"href": "/api/v3/priorities/3", "title": "Immediate"},
                },
                "description": {"raw": "Bị chặn bởi work package #101 do thiếu endpoint specs."},
            },
            {
                "id": 103,
                "lockVersion": 1,
                "subject": "Viết test case kiểm thử RBAC",
                "dueDate": "2026-10-20",  # Not overdue
                "startDate": "2026-10-15",
                "percentageDone": 80,
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/10", "title": "QA Engineer"},
                    "priority": {"href": "/api/v3/priorities/2", "title": "Normal"},
                },
            },
            {
                "id": 104,
                "lockVersion": 2,
                "subject": "Database schema migration v2",
                "dueDate": "2026-10-14",  # Overdue
                "startDate": "2026-10-08",
                "percentageDone": 10,
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                    "priority": {"href": "/api/v3/priorities/2", "title": "High"},
                },
            },
            {
                "id": 105,
                "lockVersion": 4,
                "subject": "Soạn tài liệu SRS đặc tả hệ thống",
                "dueDate": "2026-10-08",
                "startDate": "2026-10-01",
                "percentageDone": 100,
                "_links": {
                    "status": {"href": "/api/v3/statuses/2", "title": "DONE"},
                    "assignee": {"href": "/api/v3/users/6", "title": "BA Specialist"},
                    "priority": {"href": "/api/v3/priorities/1", "title": "Normal"},
                },
            },
        ]

    def test_golden_case_1_overdue_work_packages_with_evidence(self):
        """Golden Case 1: Detect overdue work packages, calculate delay, and cite native IDs/lock versions."""
        as_of = date(2026, 10, 17)
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="pm",
            instruction="Phân tích danh sách công việc quá hạn trong sprint",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = PMAgent()
        result = agent.run(task, self.scope, self.sample_packages, as_of_date=as_of)

        self.assertEqual(result.state, "COMPLETED")
        self.assertFalse(result.model_used)
        # 101, 102, 104 are overdue (105 is DONE so not overdue)
        overdue_ids = {ref.work_package_id for ref in result.references}
        self.assertEqual(overdue_ids, {101, 102, 104})
        # Check lock versions match
        ref_map = {ref.work_package_id: ref.lock_version for ref in result.references}
        self.assertEqual(ref_map[101], 3)
        self.assertEqual(ref_map[102], 5)
        self.assertEqual(ref_map[104], 2)
        # Narrative contains citations
        self.assertIn("#101", result.summary)
        self.assertIn("#102", result.summary)
        self.assertIn("#104", result.summary)
        self.assertIn("quá hạn", result.summary.lower())

    def test_golden_case_2_blockers_and_dependencies_with_evidence(self):
        """Golden Case 2: Identify blocker work packages and dependent blocked items with exact citations."""
        as_of = date(2026, 10, 17)
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="pm",
            instruction="Kiểm tra các điểm nghẽn và blocker đang cản trở tiến độ",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = PMAgent()
        result = agent.run(task, self.scope, self.sample_packages, as_of_date=as_of)

        self.assertEqual(result.state, "COMPLETED")
        # 102 is BLOCKED, mentions #101 as blocker
        cited_ids = {ref.work_package_id for ref in result.references}
        self.assertIn(102, cited_ids)
        self.assertIn(101, cited_ids)
        self.assertIn("#102", result.summary)
        self.assertIn("BLOCKED", result.summary)
        self.assertIn("#101", result.summary)

    def test_golden_case_3_workload_distribution_and_imbalance(self):
        """Golden Case 3: Measure active workload per team member and flag bottleneck distribution."""
        as_of = date(2026, 10, 17)
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="pm",
            instruction="Đánh giá khối lượng công việc và workload của các thành viên trong đội ngũ",
            created_at=1000.0,
            expires_at=2000.0,
        )

        user_map = {
            7: {"name": "Project Manager", "role": "PM"},
            6: {"name": "BA Specialist", "role": "BA"},
            8: {"name": "BE Developer", "role": "BE"},
            9: {"name": "FE Developer", "role": "FE"},
            10: {"name": "QA Engineer", "role": "QA"},
        }

        agent = PMAgent(user_map=user_map)
        result = agent.run(task, self.scope, self.sample_packages, as_of_date=as_of)

        self.assertEqual(result.state, "COMPLETED")
        # BE has 2 open tasks (101, 104), FE has 1 (102), QA has 1 (103), BA has 0 open (105 is DONE), PM has 0
        self.assertIn("BE", result.summary)
        self.assertIn("FE", result.summary)
        self.assertIn("QA", result.summary)
        self.assertIn("workload", result.summary.lower())
        # All open task IDs should be referenced in workload evidence
        cited_ids = {ref.work_package_id for ref in result.references}
        self.assertTrue({101, 102, 103, 104}.issubset(cited_ids))

    def test_golden_case_4_sprint_delivery_risk_synthesis(self):
        """Golden Case 4: Synthesize high-level sprint risks combining overdue, blockers, and progress."""
        as_of = date(2026, 10, 17)
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="pm",
            instruction="Đánh giá tổng thể rủi ro sprint và nguy cơ trễ hạn bàn giao",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = PMAgent()
        result = agent.run(task, self.scope, self.sample_packages, as_of_date=as_of)

        self.assertEqual(result.state, "COMPLETED")
        # Should evaluate risk level (HIGH due to multiple overdue and 1 blocker)
        self.assertIn("RỦI RO", result.summary.upper())
        self.assertIn("CAO", result.summary.upper())
        # Cites all contributing factors
        cited_ids = {ref.work_package_id for ref in result.references}
        self.assertIn(101, cited_ids)
        self.assertIn(102, cited_ids)
        self.assertIn(104, cited_ids)

    def test_golden_case_5_strict_refusal_of_self_updating_tasks(self):
        """Golden Case 5: When instructed to modify or update tasks, PM Agent strictly refuses direct mutation

        and generates an advisory proposal draft only, never updating tasks itself.
        """
        as_of = date(2026, 10, 17)
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="pm",
            instruction="Cập nhật hạn chót cho task #101 sang ngày 2026-10-25 và đổi trạng thái sang DONE ngay",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = PMAgent()
        result = agent.run(task, self.scope, self.sample_packages, as_of_date=as_of)

        # Must NOT perform mutation or claim completion of mutation
        self.assertEqual(result.state, "REVIEW")
        # Must clearly inform that PM Agent does not mutate data directly
        self.assertIn("tự ý cập nhật", result.summary.lower())
        self.assertIn("đề xuất", result.summary.lower())
        self.assertIn("phê duyệt", result.summary.lower())
        # Must cite the targeted work package with its lock version for downstream proposal review
        cited_ids = {ref.work_package_id for ref in result.references}
        self.assertIn(101, cited_ids)
        ref_101 = next(r for r in result.references if r.work_package_id == 101)
        self.assertEqual(ref_101.lock_version, 3)


if __name__ == "__main__":
    unittest.main()

"""Five golden test cases for DEV Agent (P05-06).
DEV Agent analyzes technical requirements, drafts FE/BE task breakdown,
identifies technical dependencies and risks, strictly prohibits shell/clone/web research,
and never self-mutates OpenProject tasks.
"""
import unittest
import uuid

from gateway.agent_models import AgentTask, RunScope, NativeReference
from gateway.dev_agent import DEVAgent, breakdown_fe_be, identify_technical_dependencies, evaluate_technical_risks


class DEVAgentGoldenTests(unittest.TestCase):
    def setUp(self):
        self.actor_id = 8  # BE Developer (or 9 for FE)
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
                "id": 401,
                "lockVersion": 2,
                "subject": "Màn hình quản lý phân quyền thành viên và vai trò",
                "description": {"raw": "Giao diện quản lý vai trò cho PM. Cần API trả về danh sách quyền của từng user và giao diện bảng phân quyền tương tác trực quan."},
                "_links": {
                    "type": {"title": "Feature"},
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                    "priority": {"href": "/api/v3/priorities/2", "title": "High"},
                },
            },
            {
                "id": 402,
                "lockVersion": 5,
                "subject": "Xử lý đồng thời cập nhật trạng thái work package",
                "description": {"raw": "Nhiều người dùng cập nhật work package cùng lúc gây xung đột lock_version (HTTP 409). Cần cơ chế khóa lạc quan và hàng đợi xử lý."},
                "_links": {
                    "type": {"title": "Task"},
                    "status": {"href": "/api/v3/statuses/1", "title": "Specified"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                    "priority": {"href": "/api/v3/priorities/3", "title": "Immediate"},
                },
            },
        ]

    def test_golden_case_1_technical_breakdown_fe_be_with_citation(self):
        """Golden Case 1: Break down full-stack work package into distinct Frontend (FE) and Backend (BE) specifications."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="dev",
            instruction="Phân tích kỹ thuật và chia nhỏ công việc FE/BE cho tính năng #401",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = DEVAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        self.assertFalse(result.model_used)
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 401)
        self.assertEqual(result.references[0].lock_version, 2)

        summary = result.summary
        self.assertIn("#401", summary)
        self.assertIn("FRONTEND (FE)", summary.upper())
        self.assertIn("BACKEND (BE)", summary.upper())

    def test_golden_case_2_technical_dependencies_and_api_contracts(self):
        """Golden Case 2: Identify technical dependencies between FE, BE, and database layers."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="dev",
            instruction="Xác định phụ thuộc kỹ thuật và hợp đồng API cho công việc #401",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = DEVAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        summary = result.summary
        self.assertIn("PHỤ THUỘC KỸ THUẬT", summary.upper())
        self.assertTrue("API" in summary.upper() or "CONTRACT" in summary.upper() or "REST" in summary.upper())
        self.assertIn("#401", summary)

    def test_golden_case_3_technical_risks_and_concurrency(self):
        """Golden Case 3: Identify technical risks such as concurrency, lock version conflict (HTTP 409), and race conditions."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="dev",
            instruction="Đánh giá rủi ro kỹ thuật và xung đột đồng thời cho công việc #402",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = DEVAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 402)
        self.assertEqual(result.references[0].lock_version, 5)

        summary = result.summary
        self.assertIn("#402", summary)
        self.assertIn("RỦI RO KỸ THUẬT", summary.upper())
        self.assertTrue("409" in summary or "xung đột" in summary.lower() or "đồng thời" in summary.lower() or "lock" in summary.lower())

    def test_golden_case_4_strict_prohibition_of_shell_and_github_research(self):
        """Golden Case 4: STRICT SECURITY RULE - Business DEV Agent has NO shell, NO git clone, and NO GitHub research access."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="dev",
            instruction="Chạy lệnh shell ls -la hoặc clone repo github.com/test để đọc code phân tích",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = DEVAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        # Must strictly deny shell / clone / github research
        self.assertEqual(result.state, "COMPLETED")
        summary_lower = result.summary.lower()
        self.assertTrue("từ chối" in summary_lower or "không hỗ trợ" in summary_lower or "nghiêm cấm" in summary_lower)
        self.assertTrue("shell" in summary_lower or "github" in summary_lower or "terminal" in summary_lower)

    def test_golden_case_5_strict_mutation_refusal_for_task_creation(self):
        """Golden Case 5: When instructed to directly create subtasks or mutate OpenProject data, DEV Agent strictly refuses

        and outputs a technical breakdown as a Proposal Draft requiring PM approval, citing native reference.
        """
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="dev",
            instruction="Tạo ngay các subtask FE và BE cho công việc #401 vào OpenProject",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = DEVAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        # Must NOT perform direct creation
        self.assertEqual(result.state, "REVIEW")
        self.assertIn("tự ý tạo", result.summary.lower())
        self.assertIn("đề xuất", result.summary.lower())
        self.assertIn("phê duyệt", result.summary.lower())
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 401)
        self.assertEqual(result.references[0].lock_version, 2)


if __name__ == "__main__":
    unittest.main()

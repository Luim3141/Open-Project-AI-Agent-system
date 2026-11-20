"""Five golden test cases for BA Agent (P05-04).
BA Agent drafts User Stories, Acceptance Criteria (AC), analyzes ambiguity,
drafts business dependencies with native citations, and STRICTLY does not self-write to OpenProject.
"""
import unittest
import uuid

from gateway.agent_models import AgentTask, RunScope, NativeReference
from gateway.ba_agent import BAAgent, draft_user_story, draft_acceptance_criteria, detect_ambiguity, draft_dependencies


class BAAgentGoldenTests(unittest.TestCase):
    def setUp(self):
        self.actor_id = 6  # BA Specialist
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
                "id": 201,
                "lockVersion": 2,
                "subject": "Tính năng đăng nhập 2 lớp (2FA)",
                "description": {"raw": "Cần làm tính năng đăng nhập 2 lớp thật nhanh, giao diện đẹp và hệ thống tự hiểu khi nào cần mã OTP."},
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/6", "title": "BA Specialist"},
                    "priority": {"href": "/api/v3/priorities/2", "title": "High"},
                },
            },
            {
                "id": 202,
                "lockVersion": 4,
                "subject": "Xem lịch sử giao dịch cá nhân",
                "description": {"raw": "Người dùng xem lịch sử các giao dịch đã thực hiện trong 30 ngày gần nhất."},
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/9", "title": "FE Developer"},
                    "priority": {"href": "/api/v3/priorities/1", "title": "Normal"},
                },
            },
            {
                "id": 203,
                "lockVersion": 1,
                "subject": "Xuất báo cáo tài chính dạng Excel",
                "description": {"raw": "Yêu cầu người dùng phải đăng nhập thành công và có quyền kế toán mới được xuất báo cáo."},
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "Specified"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                    "priority": {"href": "/api/v3/priorities/2", "title": "High"},
                },
            },
        ]

    def test_golden_case_1_user_story_decomposition_with_native_citation(self):
        """Golden Case 1: Standardize informal requirement into formal User Story format with native citation."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="ba",
            instruction="Soạn thảo User Story chuẩn cho công việc #201",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = BAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        self.assertFalse(result.model_used)
        # Must cite #201 with lock_version 2
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 201)
        self.assertEqual(result.references[0].lock_version, 2)
        # Content format: As a / I want / So that (Là / Tôi muốn / Để)
        summary = result.summary
        self.assertIn("#201", summary)
        self.assertIn("Là ", summary)
        self.assertIn("Tôi muốn ", summary)
        self.assertIn("Để ", summary)

    def test_golden_case_2_acceptance_criteria_drafting(self):
        """Golden Case 2: Draft structured, testable Acceptance Criteria (Given-When-Then or criteria list)."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="ba",
            instruction="Soạn tiêu chí chấp nhận (AC) cho công việc #202",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = BAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 202)
        self.assertEqual(result.references[0].lock_version, 4)
        summary = result.summary
        self.assertIn("#202", summary)
        self.assertIn("TIÊU CHÍ CHẤP NHẬN", summary.upper())
        # AC contains testable conditions
        self.assertTrue("AC" in summary or "Given" in summary or "Điều kiện" in summary)

    def test_golden_case_3_ambiguity_detection_and_flagging(self):
        """Golden Case 3: Detect vague phrases (e.g. 'thật nhanh', 'giao diện đẹp', 'tự hiểu') and flag clarifications."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="ba",
            instruction="Kiểm tra mức độ mơ hồ và làm rõ yêu cầu cho công việc #201",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = BAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        self.assertIn("#201", result.summary)
        summary_lower = result.summary.lower()
        self.assertIn("mơ hồ", summary_lower)
        # Should flag vague phrases
        self.assertTrue("nhanh" in summary_lower or "đẹp" in summary_lower or "tự hiểu" in summary_lower)
        # Should provide clarifying questions
        self.assertIn("câu hỏi làm rõ", summary_lower)

    def test_golden_case_4_business_dependency_drafting(self):
        """Golden Case 4: Analyze business flow dependencies (e.g. Export #203 depends on Auth #201) with citations."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="ba",
            instruction="Phân tích phụ thuộc nghiệp vụ giữa các tính năng trong dự án",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = BAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        cited_ids = {r.work_package_id for r in result.references}
        self.assertIn(203, cited_ids)
        self.assertIn(201, cited_ids)
        self.assertIn("PHỤ THUỘC", result.summary.upper())
        self.assertIn("#203", result.summary)
        self.assertIn("#201", result.summary)

    def test_golden_case_5_strict_no_self_write_mutation_refusal(self):
        """Golden Case 5: When instructed to write or update task directly, BA Agent strictly refuses direct write

        and produces an advisory Proposal Draft requiring PM approval, citing native reference.
        """
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="ba",
            instruction="Cập nhật tiêu chí chấp nhận AC này vào mô tả công việc #202 ngay lập tức",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = BAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        # Must NOT perform direct write
        self.assertEqual(result.state, "REVIEW")
        self.assertIn("tự ý ghi", result.summary.lower())
        self.assertIn("đề xuất", result.summary.lower())
        self.assertIn("phê duyệt", result.summary.lower())
        # Must cite the work package with lock_version 4
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 202)
        self.assertEqual(result.references[0].lock_version, 4)


if __name__ == "__main__":
    unittest.main()

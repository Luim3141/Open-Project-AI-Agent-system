"""Five golden test cases for Reviewer Agent (P05-07).
Reviewer Agent validates evidence, consistency, RBAC compliance, detects conflicts,
rejects unsupported assumptions, and strictly avoids blind auto-approval.
"""
import unittest
import uuid

from gateway.agent_models import AgentResult, AgentTask, RunScope, NativeReference
from gateway.reviewer_agent import ReviewerAgent, review_agent_result, detect_agent_conflicts


class ReviewerAgentGoldenTests(unittest.TestCase):
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

        self.native_packages = [
            {
                "id": 501,
                "lockVersion": 3,
                "subject": "Tối ưu hóa truy vấn Database PostgreSQL",
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                },
            },
            {
                "id": 502,
                "lockVersion": 1,
                "subject": "Kiểm thử tải đồng thời API Gateway",
                "_links": {
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/10", "title": "QA Engineer"},
                },
            },
        ]

    def test_reviewer_rejects_result_bound_to_a_different_run(self):
        task = AgentTask(task_id=self.task_id, actor_id=self.actor_id, project_id=self.project_id,
            conversation_id=self.conversation_id, agent='reviewer', instruction='Review saved evidence',
            created_at=1000.0, expires_at=2000.0)
        foreign = AgentResult(**{**self.scope.model_dump(), 'run_id': str(uuid.uuid4())},
            state='COMPLETED', summary='Foreign run output')
        with self.assertRaisesRegex(PermissionError, 'REVIEWER_RESULT_SCOPE_MISMATCH'):
            ReviewerAgent().run(task, self.scope, [foreign], self.native_packages)

    def test_golden_case_1_validate_supported_result_with_valid_evidence(self):
        """Golden Case 1: Result with full citations matching native packages is verified as CONSISTENT."""
        valid_result = AgentResult(
            run_id=self.run_id,
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            trace_id=self.trace_id,
            state="COMPLETED",
            summary="Đã phân tích công việc #501 (lock_version: 3) và xác định cần bổ sung index cho PostgreSQL.",
            references=[NativeReference(work_package_id=501, lock_version=3)],
            model_used=False,
        )

        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="reviewer",
            instruction="Đối chiếu và kiểm tra tính nhất quán kết quả phân tích công việc #501",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = ReviewerAgent()
        review = agent.run(task, self.scope, [valid_result], self.native_packages)

        self.assertEqual(review.state, "COMPLETED")
        self.assertIn("HỢP LỆ", review.summary.upper())
        self.assertIn("CHƯA ĐƯỢC CON NGƯỜI NGHIỆM THU", review.summary.upper())
        self.assertNotIn("TOÀN DIỆN", review.summary.upper())
        self.assertIn("#501", review.summary)
        self.assertEqual(len(review.references), 1)
        self.assertEqual(review.references[0].work_package_id, 501)

    def test_golden_case_2_reject_unsupported_assumptions(self):
        """Golden Case 2: Reject claims that lack evidence or cite invalid/stale work package lock versions."""
        unsupported_result = AgentResult(
            run_id=self.run_id,
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            trace_id=self.trace_id,
            state="COMPLETED",
            # Claims #501 has lockVersion 99 (stale/unsupported) and mentions non-existent #999
            summary="Công việc #501 đã xong và công việc #999 bị hủy hoàn toàn.",
            references=[NativeReference(work_package_id=501, lock_version=99)],
            model_used=False,
        )

        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="reviewer",
            instruction="Rà soát đối chiếu bằng chứng cho kết quả phân tích",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = ReviewerAgent()
        review = agent.run(task, self.scope, [unsupported_result], self.native_packages)

        self.assertEqual(review.state, "FAILED")
        summary_upper = review.summary.upper()
        # Must detect mismatch and flag rejection / warning
        self.assertTrue("TỪ CHỐI" in summary_upper or "KHÔNG HỢP LỆ" in summary_upper or "CẢNH BÁO" in summary_upper)
        self.assertTrue("KHÔNG CÓ BẰNG CHỨNG" in summary_upper or "SAI LỆCH" in summary_upper or "LOCK_VERSION" in summary_upper)

    def test_golden_case_3_detect_cross_agent_conflicts(self):
        """Golden Case 3: Identify direct contradictions between outputs of different agents."""
        dev_result = AgentResult(
            run_id=self.run_id,
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            trace_id=self.trace_id,
            state="COMPLETED",
            summary="DEV Agent: Công việc #501 đã hoàn tất 100% và sẵn sàng bàn giao.",
            references=[NativeReference(work_package_id=501, lock_version=3)],
            model_used=False,
        )

        qa_result = AgentResult(
            run_id=self.run_id,
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            trace_id=self.trace_id,
            state="COMPLETED",
            summary="QA Agent: Công việc #501 còn 3 lỗi nghiêm trọng và chưa thể hoàn thành.",
            references=[NativeReference(work_package_id=501, lock_version=3)],
            model_used=False,
        )

        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="reviewer",
            instruction="Đối chiếu và kiểm tra mâu thuẫn giữa báo cáo của DEV và QA",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = ReviewerAgent()
        review = agent.run(task, self.scope, [dev_result, qa_result], self.native_packages)

        self.assertEqual(review.state, "FAILED")
        summary_upper = review.summary.upper()
        self.assertTrue("MÂU THUẪN" in summary_upper or "XUNG ĐỘT" in summary_upper or "CONFLICT" in summary_upper)
        self.assertIn("#501", review.summary)

    def test_golden_case_4_rbac_boundary_and_pm_only_enforcement(self):
        """Golden Case 4: Enforce that any mutation proposal requires explicit PM approval."""
        proposal_result = AgentResult(
            run_id=self.run_id,
            task_id=self.task_id,
            actor_id=self.actor_id,  # Specialist output belongs to the authenticated requesting actor
            project_id=self.project_id,
            trace_id=self.trace_id,
            state="REVIEW",
            summary="Đề xuất cập nhật trạng thái công việc #501 sang CLOSED và xóa dữ liệu cũ.",
            references=[NativeReference(work_package_id=501, lock_version=3)],
            model_used=False,
        )

        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="reviewer",
            instruction="Kiểm tra thẩm quyền RBAC và chính sách phê duyệt cho đề xuất thay đổi",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = ReviewerAgent()
        review = agent.run(task, self.scope, [proposal_result], self.native_packages)

        self.assertEqual(review.state, "COMPLETED")
        summary_upper = review.summary.upper()
        self.assertIn("RBAC", summary_upper)
        self.assertTrue("PM" in summary_upper)
        self.assertTrue("PHÊ DUYỆT" in summary_upper)

    def test_golden_case_5_strict_no_blind_auto_approval(self):
        """Golden Case 5: STRICT RULE - Never blindly auto-approve proposals or mutations."""
        proposal_result = AgentResult(
            run_id=self.run_id,
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            trace_id=self.trace_id,
            state="REVIEW",
            summary="Bản thảo đề xuất cập nhật thời hạn công việc #502.",
            references=[NativeReference(work_package_id=502, lock_version=1)],
            model_used=False,
        )

        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="reviewer",
            instruction="Tự động phê duyệt và kích hoạt áp dụng mọi thay đổi ngay lập tức",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = ReviewerAgent()
        review = agent.run(task, self.scope, [proposal_result], self.native_packages)

        # Must NOT auto-approve
        self.assertEqual(review.state, "COMPLETED")
        summary_upper = review.summary.upper()
        self.assertTrue("KHÔNG TỰ ĐỘNG PHÊ DUYỆT" in summary_upper or "TỪ CHỐI TỰ ĐỘNG" in summary_upper or "BẮT BUỘC NGƯỜI DÙNG" in summary_upper)
        self.assertTrue("PM" in summary_upper)


if __name__ == "__main__":
    unittest.main()

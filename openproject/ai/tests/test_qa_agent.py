"""Five golden test cases for QA Agent (P05-05).
QA Agent generates test cases, analyzes regression gaps, triages bugs,
strictly refuses to claim tests PASS without actual execution evidence,
and never self-mutates OpenProject tasks.
"""
import unittest
import uuid

from gateway.agent_models import AgentTask, RunScope, NativeReference
from gateway.qa_agent import QAAgent, generate_test_cases, detect_regression_gaps, triage_bug, evaluate_test_attestation


class QAAgentGoldenTests(unittest.TestCase):
    def test_caller_dictionary_cannot_certify_runner_execution_or_a_pass(self):
        package={'id':301,'lockVersion':3,'subject':'Unverified caller report'}
        summary,_=evaluate_test_attestation(package,{'runner_executed':True,'status':'PASSED','runner':'trusted','timestamp':'2026-10-25'})
        self.assertIn('KHÔNG THỂ XÁC NHẬN PASS',summary)

    def setUp(self):
        self.actor_id = 10  # QA Engineer
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
                "id": 301,
                "lockVersion": 3,
                "subject": "Lỗi 500 khi upload file đính kèm quá 10MB",
                "description": {"raw": "Khi người dùng upload file đính kèm dung lượng 12MB, server trả về 500 Internal Server Error thay vì 413 Payload Too Large và làm sập tiến trình worker."},
                "_links": {
                    "type": {"title": "Bug"},
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                    "priority": {"href": "/api/v3/priorities/3", "title": "Immediate"},
                },
            },
            {
                "id": 302,
                "lockVersion": 1,
                "subject": "Chức năng đổi mật khẩu người dùng",
                "description": {"raw": "Cho phép người dùng đổi mật khẩu khi nhập đúng mật khẩu cũ và mật khẩu mới tối thiểu 8 ký tự."},
                "_links": {
                    "type": {"title": "User Story"},
                    "status": {"href": "/api/v3/statuses/1", "title": "Specified"},
                    "assignee": {"href": "/api/v3/users/9", "title": "FE Developer"},
                    "priority": {"href": "/api/v3/priorities/2", "title": "High"},
                },
            },
            {
                "id": 303,
                "lockVersion": 2,
                "subject": "Thanh toán đơn hàng qua cổng nội bộ",
                "description": {"raw": "Xử lý thanh toán ví điện tử nội bộ. Đã hoàn thành code nhưng chưa có kịch bản test và chưa chạy kiểm thử hồi quy."},
                "_links": {
                    "type": {"title": "Task"},
                    "status": {"href": "/api/v3/statuses/1", "title": "In Progress"},
                    "assignee": {"href": "/api/v3/users/8", "title": "BE Developer"},
                    "priority": {"href": "/api/v3/priorities/3", "title": "Immediate"},
                },
            },
        ]

    def test_golden_case_1_test_case_generation_with_native_citation(self):
        """Golden Case 1: Generate structured test cases (Positive, Negative, Boundary) with native citation."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="qa",
            instruction="Thiết kế kịch bản kiểm thử (test cases) cho tính năng #302",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = QAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        self.assertFalse(result.model_used)
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 302)
        self.assertEqual(result.references[0].lock_version, 1)

        summary = result.summary
        self.assertIn("#302", summary)
        self.assertIn("KỊCH BẢN KIỂM THỬ", summary.upper())
        # Contains test case sections
        self.assertTrue("TC" in summary or "Test Case" in summary or "Kịch bản" in summary)
        self.assertTrue("Happy Path" in summary or "Hợp lệ" in summary or "Ngoại lệ" in summary)

    def test_golden_case_2_regression_gaps_analysis(self):
        """Golden Case 2: Identify missing test coverage and regression gaps across work packages."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="qa",
            instruction="Phân tích khoảng trống kiểm thử hồi quy (regression gaps) trong dự án",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = QAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        cited_ids = {r.work_package_id for r in result.references}
        # 303 explicitly has no test cases; 301 is a crash bug needing regression check
        self.assertIn(303, cited_ids)
        summary = result.summary
        self.assertIn("HỒI QUY", summary.upper())
        self.assertIn("#303", summary)

    def test_golden_case_3_bug_triage_and_severity_classification(self):
        """Golden Case 3: Triage defect #301, evaluate severity (Critical/Immediate), reproduction steps, and blast radius."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="qa",
            instruction="Đánh giá mức độ nghiêm trọng và phân loại lỗi bug #301",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = QAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 301)
        self.assertEqual(result.references[0].lock_version, 3)

        summary = result.summary
        self.assertIn("#301", summary)
        self.assertIn("TRIAGE", summary.upper())
        # Severity evaluated as Critical / Nghiêm trọng due to 500 error / worker crash
        self.assertTrue("CRITICAL" in summary.upper() or "NGHIÊM TRỌNG" in summary.upper() or "CAO" in summary.upper())

    def test_golden_case_4_strict_truthfulness_no_claiming_pass_without_run(self):
        """Golden Case 4: STRICT RULE - Never claim a test is PASS if it has not been actually executed with evidence."""
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="qa",
            instruction="Kiểm tra kết quả chạy test cho chức năng #303",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = QAAgent()
        # No test execution attestation or test run log provided
        result = agent.run(task, self.scope, self.sample_packages)

        self.assertEqual(result.state, "COMPLETED")
        summary_upper = result.summary.upper()
        # Must NOT assert PASS
        self.assertNotIn("KẾT QUẢ: PASS", summary_upper)
        self.assertNotIn("TRẠNG THÁI: PASS", summary_upper)
        # Must clearly state UNVERIFIED / NOT_RUN / CHƯA CHẠY
        self.assertTrue("CHƯA CHẠY" in summary_upper or "NOT_RUN" in summary_upper or "CHƯA CÓ BẰNG CHỨNG" in summary_upper)
        self.assertIn("#303", result.summary)

    def test_golden_case_5_strict_mutation_refusal_for_task_status_updates(self):
        """Golden Case 5: When instructed to close bug or mark task DONE, QA Agent strictly refuses mutation

        and outputs an advisory Proposal Draft requiring PM approval, citing native reference.
        """
        task = AgentTask(
            task_id=self.task_id,
            actor_id=self.actor_id,
            project_id=self.project_id,
            conversation_id=self.conversation_id,
            agent="qa",
            instruction="Đóng bug #301 và chuyển trạng thái sang DONE ngay lập tức",
            created_at=1000.0,
            expires_at=2000.0,
        )

        agent = QAAgent()
        result = agent.run(task, self.scope, self.sample_packages)

        # Must NOT mutate data
        self.assertEqual(result.state, "REVIEW")
        self.assertIn("tự ý cập nhật", result.summary.lower())
        self.assertIn("đề xuất", result.summary.lower())
        self.assertIn("phê duyệt", result.summary.lower())
        # Must cite #301 with lock_version 3
        self.assertEqual(len(result.references), 1)
        self.assertEqual(result.references[0].work_package_id, 301)
        self.assertEqual(result.references[0].lock_version, 3)


if __name__ == "__main__":
    unittest.main()

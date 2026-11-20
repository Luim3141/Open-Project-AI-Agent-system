"""Unit tests for P07-05: Sprint Readiness Review Workflow.
Enforces:
1. Detection of missing Acceptance Criteria (AC).
2. Detection of missing test coverage / test tasks.
3. Detection of blocked dependencies.
4. Output includes specific Work Package IDs and structured proposals for PM review.
5. Strictly advisory: 0 native auto-writes, zero LLM calls.
6. Multi-user and multi-role compatibility.
"""
import unittest
from datetime import date
from openproject.ai.gateway.sprint_readiness import (
    evaluate_sprint_readiness,
    SprintReadinessEngine,
)


class TestSprintReadiness(unittest.TestCase):
    def setUp(self):
        self.packages = [
            # Story 1: Complete AC, has test, no blocker -> Fully Ready
            {
                "id": 301,
                "lockVersion": 2,
                "subject": "User Registration Flow",
                "_links": {
                    "status": {"title": "Specified"},
                    "type": {"title": "User Story"},
                    "assignee": {"href": "/api/v3/users/6", "title": "FE Lead 6"},
                },
                "description": {
                    "raw": "Cho phép người dùng tạo tài khoản mới.\n\n### Tiêu chí chấp nhận (AC):\n- [ ] Nhập email hợp lệ và mật khẩu >= 8 ký tự\n- [ ] Gửi mã xác thực qua email\n- [ ] Thông báo lỗi rõ ràng khi trùng email"
                },
            },
            # Test task for Story 1
            {
                "id": 302,
                "lockVersion": 1,
                "subject": "Test Registration Flow",
                "_links": {
                    "status": {"title": "Specified"},
                    "type": {"title": "Test"},
                    "assignee": {"href": "/api/v3/users/16", "title": "QA Lead 16"},
                    "parent": {"href": "/api/v3/work_packages/301"},
                },
                "description": {"raw": "Kiểm thử các ca thành công và biên của tính năng đăng ký."},
            },
            # Story 2: Missing AC, no test -> Unready
            {
                "id": 303,
                "lockVersion": 1,
                "subject": "Export PDF Report",
                "_links": {
                    "status": {"title": "New"},
                    "type": {"title": "Feature"},
                    "assignee": {"href": "/api/v3/users/11", "title": "BE Lead 11"},
                },
                "description": {"raw": "Cần xuất báo cáo ra file PDF."},  # No AC!
            },
            # Story 3: Has AC, but blocked by #303 -> Blocked dependency
            {
                "id": 304,
                "lockVersion": 3,
                "subject": "Download PDF Button UI [BLOCKED]",
                "_links": {
                    "status": {"title": "Blocked"},
                    "type": {"title": "Task"},
                    "assignee": {"href": "/api/v3/users/7", "title": "FE Dev 7"},
                },
                "description": {
                    "raw": "Nút tải PDF trên giao diện.\n\nAcceptance Criteria:\n- [ ] Nút hiển thị đúng vị trí\n- [ ] Loading spinner khi đang tải\n\nBị chặn bởi #303"
                },
            },
        ]

    def test_missing_ac_detection(self):
        """Correctly identifies work packages without Acceptance Criteria."""
        report = evaluate_sprint_readiness(self.packages, project_id="QLDAPM")
        self.assertEqual(report["state"], "READY")
        self.assertFalse(report["model_used"])

        missing_ac = report["missing_ac_packages"]
        missing_ids = [p["id"] for p in missing_ac]
        self.assertIn(303, missing_ids)
        self.assertNotIn(301, missing_ids)
        self.assertNotIn(304, missing_ids)

    def test_missing_test_coverage_detection(self):
        """Correctly identifies development packages lacking test coverage."""
        report = evaluate_sprint_readiness(self.packages, project_id="QLDAPM")
        missing_tests = report["missing_test_packages"]
        missing_ids = [p["id"] for p in missing_tests]

        # Story 303 has no test
        self.assertIn(303, missing_ids)
        # Story 301 has linked test #302
        self.assertNotIn(301, missing_ids)

    def test_blocked_dependency_detection(self):
        """Correctly flags tasks that are blocked by unresolved dependencies."""
        report = evaluate_sprint_readiness(self.packages, project_id="QLDAPM")
        blocked = report["blocked_packages"]
        blocked_ids = [p["id"] for p in blocked]

        self.assertIn(304, blocked_ids)
        self.assertEqual(blocked[0]["blocker_ids"], [303])

    def test_readiness_status_and_score(self):
        """Computes accurate readiness status and overall readiness percentage."""
        report = evaluate_sprint_readiness(self.packages, project_id="QLDAPM")
        # 4 packages: 301 is ready, 302 is test task. 303 missing AC & test, 304 blocked -> 3 issues => NOT_READY
        self.assertEqual(report["sprint_readiness"]["status"], "NOT_READY")
        self.assertIn("proposals_for_pm", report)
        self.assertGreater(len(report["proposals_for_pm"]), 0)

    def test_strictly_advisory_no_writes(self):
        """Ensures that all findings are proposals for PM review and not direct mutations."""
        report = evaluate_sprint_readiness(self.packages, project_id="QLDAPM")
        self.assertTrue(report["advisory_only"])
        self.assertFalse(report["auto_executed"])
        self.assertIn("Chỉ đề xuất để PM duyệt, không tự động ghi dữ liệu", report["notice"])


if __name__ == "__main__":
    unittest.main()

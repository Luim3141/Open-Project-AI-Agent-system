import unittest
from openproject.ai.gateway.decision_memory import (
    DecisionMemory,
    DecisionType,
    DecisionRecord,
    SecurityValidationError,
)

class TestDecisionMemory(unittest.TestCase):
    def setUp(self):
        self.decision_mem = DecisionMemory()

    def test_record_scope_change(self):
        rec = self.decision_mem.record_decision(
            project_id="QAG3",
            actor_id=7,  # PM
            decision_type=DecisionType.SCOPE_CHANGE,
            summary="Thêm trường xác thực 2 lớp TOTP vào User Story Đăng nhập",
            reason="Yêu cầu bảo mật tăng cường từ khách hàng nội bộ",
            native_id=101,
            lock_version=2,
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        )
        self.assertTrue(rec.decision_id)
        self.assertEqual(rec.decision_type, DecisionType.SCOPE_CHANGE)
        self.assertEqual(rec.provenance_hash, rec.compute_hash())

    def test_record_status_gate_transition(self):
        rec = self.decision_mem.record_decision(
            project_id="QAG3",
            actor_id=10,  # QA
            decision_type=DecisionType.STATUS_GATE,
            summary="Chuyển Work Package 102 sang Ready for QA",
            reason="Toàn bộ unit test backend đạt 100% pass với biên bản test runner xác thực",
            native_id=102,
            lock_version=4,
            allowed_roles=["PM", "BE", "QA"],
        )
        self.assertEqual(rec.decision_type, DecisionType.STATUS_GATE)
        self.assertEqual(rec.native_id, 102)

    def test_record_sprint_risk(self):
        rec = self.decision_mem.record_decision(
            project_id="QAG3",
            actor_id=7,  # PM
            decision_type=DecisionType.SPRINT_RISK,
            summary="Nguy cơ chậm tiến độ do thiếu nhân sự FE",
            reason="FE bị ốm 2 ngày, điều chỉnh buffer Sprint và phân bổ lại task",
            native_id=901,
            lock_version=1,
            allowed_roles=["PM"],
        )
        self.assertEqual(rec.decision_type, DecisionType.SPRINT_RISK)

    def test_reject_external_crawl_and_github(self):
        with self.assertRaises(SecurityValidationError):
            self.decision_mem.record_decision(
                project_id="QAG3",
                actor_id=7,
                decision_type=DecisionType.SCOPE_CHANGE,
                summary="Thay đổi theo repo github.com/external/demo",
                reason="Xem tài liệu tại https://example.com/spec",
                native_id=101,
                lock_version=1,
            )

    def test_query_decision_history_with_acl(self):
        # 1. PM-only decision
        self.decision_mem.record_decision(
            project_id="QAG3",
            actor_id=7,
            decision_type=DecisionType.SPRINT_RISK,
            summary="Báo cáo rủi ro nội bộ PM",
            reason="Kế hoạch dự phòng nhân sự",
            native_id=902,
            lock_version=1,
            allowed_roles=["PM"],
        )
        # 2. General decision
        self.decision_mem.record_decision(
            project_id="QAG3",
            actor_id=6,  # BA
            decision_type=DecisionType.SCOPE_CHANGE,
            summary="Cập nhật AC cho thanh toán",
            reason="Khách hàng yêu cầu hỗ trợ mã QR",
            native_id=105,
            lock_version=3,
            allowed_roles=["PM", "BA", "FE", "BE", "QA"],
        )

        # Query as FE: should only see general decision, not PM confidential
        fe_decisions = self.decision_mem.query_decisions(project_id="QAG3", role="FE")
        self.assertEqual(len(fe_decisions), 1)
        self.assertEqual(fe_decisions[0].native_id, 105)

        # Query as PM: sees both
        pm_decisions = self.decision_mem.query_decisions(project_id="QAG3", role="PM")
        self.assertEqual(len(pm_decisions), 2)

        # Query cross-project: DEMO gets 0 decisions
        demo_decisions = self.decision_mem.query_decisions(project_id="DEMO", role="PM")
        self.assertEqual(len(demo_decisions), 0)

if __name__ == '__main__':
    unittest.main()

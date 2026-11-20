"""Unit tests for P07-06: Requirement Change -> QA Draft & Scoped Notification Workflow.
Enforces:
1. Event handling for requirement/work package changes.
2. Generates QA test draft without auto-transitioning or changing roles.
3. Built-in idempotency (repeated events return identical draft without duplicate processing).
4. Strict RBAC: event payload cannot escalate privileges or mutate status.
5. Role-appropriate notifications (QA + assigned dev + PM notice).
"""
import unittest
from datetime import date
from openproject.ai.gateway.qa_change_workflow import (
    process_requirement_change,
    QAChangeWorkflowEngine,
)


class TestQAChangeWorkflow(unittest.TestCase):
    def setUp(self):
        self.package = {
            "id": 501,
            "lockVersion": 4,
            "subject": "User Profile Email Update",
            "_links": {
                "status": {"title": "In Progress"},
                "type": {"title": "Feature"},
                "assignee": {"href": "/api/v3/users/11", "title": "BE Lead 11"},
            },
            "description": {
                "raw": "Cho phép người dùng đổi địa chỉ email liên kết và yêu cầu xác thực OTP."
            },
        }
        self.users = {
            1: {"name": "PM 1", "role": "PM"},
            11: {"name": "BE Lead 11", "role": "BE"},
            16: {"name": "QA Lead 16", "role": "QA"},
        }

    def test_qa_draft_generation_on_requirement_change(self):
        """Generates QA test scenario draft when requirement changes."""
        event = {
            "event_type": "REQUIREMENT_UPDATED",
            "package_id": 501,
            "lock_version": 4,
            "changed_fields": ["description", "subject"],
            "actor_id": 1,
            "package": self.package,
        }
        result = process_requirement_change(event, users=self.users)
        self.assertEqual(result["state"], "READY")
        self.assertFalse(result["model_used"])
        self.assertTrue(result["is_draft"])

        # Check QA draft content
        draft = result["qa_draft"]
        self.assertEqual(draft["target_package_id"], 501)
        self.assertEqual(draft["lock_version"], 4)
        self.assertIn("KỊCH BẢN KIỂM THỬ ĐỀ XUẤT", draft["test_plan_text"])
        self.assertIn("OTP", draft["test_plan_text"])

    def test_built_in_idempotency(self):
        """Identical events return cached result without duplicate processing."""
        engine = QAChangeWorkflowEngine()
        event = {
            "event_type": "REQUIREMENT_UPDATED",
            "package_id": 501,
            "lock_version": 4,
            "changed_fields": ["description"],
            "actor_id": 1,
            "package": self.package,
        }
        res1 = engine.handle_event(event, users=self.users)
        self.assertFalse(res1["idempotent_replay"])

        # Replay same event
        res2 = engine.handle_event(event, users=self.users)
        self.assertTrue(res2["idempotent_replay"])
        self.assertEqual(res1["event_fingerprint"], res2["event_fingerprint"])

    def test_no_privilege_escalation_or_auto_transition(self):
        """Event payload attempting status transition or role escalation is ignored/refused."""
        engine = QAChangeWorkflowEngine()
        malicious_event = {
            "event_type": "REQUIREMENT_UPDATED",
            "package_id": 501,
            "lock_version": 4,
            "changed_fields": ["description"],
            "actor_id": 11,  # BE
            "package": self.package,
            # Malicious attempt to change status to DONE or escalate role to PM
            "requested_status": "DONE",
            "requested_role": "PM",
            "auto_transition": True,
        }
        res = engine.handle_event(malicious_event, users=self.users)
        self.assertEqual(res["state"], "READY")
        # Ensure status did not change and no transition occurred
        self.assertFalse(res["auto_transitioned"])
        self.assertEqual(res["current_status"], "In Progress")
        self.assertNotIn("DONE", res.get("status_mutation", ""))

    def test_role_appropriate_notifications(self):
        """Notifications are correctly routed to QA, assigned dev, and PM."""
        event = {
            "event_type": "REQUIREMENT_UPDATED",
            "package_id": 501,
            "lock_version": 4,
            "changed_fields": ["description"],
            "actor_id": 1,
            "package": self.package,
        }
        res = process_requirement_change(event, users=self.users)
        notifications = res["notifications"]

        recipients = {n["recipient_id"] for n in notifications}
        # QA Lead (16), BE Lead (11), PM (1) should receive appropriate notices
        self.assertIn(16, recipients)
        self.assertIn(11, recipients)
        self.assertIn(1, recipients)

        # QA notice mentions reviewing test cases
        qa_notices = [n for n in notifications if n["recipient_id"] == 16]
        self.assertIn("Rà soát kịch bản kiểm thử", qa_notices[0]["message"])


if __name__ == "__main__":
    unittest.main()

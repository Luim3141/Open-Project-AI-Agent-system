"""Unit tests for P07-07: Workflow Pause Controller on Host Offline, Permission Denied, Quota Exhausted.
Enforces:
1. Halts workflow execution when host is offline, permissions are missing, or AI quota is exhausted.
2. Prevents retry storm via exponential backoff / pause windows.
3. Prevents notification spam (debounce window for outage alerts).
4. Auto-resumes cleanly upon verified successful connection.
5. Zero LLM tokens.
"""
import unittest
import time
from openproject.ai.gateway.workflow_pause import (
    WorkflowPauseController,
    PauseReason,
)


class TestWorkflowPause(unittest.TestCase):
    def setUp(self):
        self.controller = WorkflowPauseController(notification_debounce_seconds=1800)

    def test_normal_execution_allowed(self):
        """When in normal running state, executions proceed without delay."""
        allowed, reason = self.controller.should_execute("daily_sprint_report")
        self.assertTrue(allowed)
        self.assertEqual(reason, "RUNNING")

    def test_host_offline_pauses_and_prevents_retry_storm(self):
        """Host offline triggers pause with exponential backoff, preventing retry storms."""
        # 1st failure
        res1 = self.controller.record_failure("daily_sprint_report", PauseReason.HOST_OFFLINE, "Connection refused")
        self.assertEqual(res1["state"], "PAUSED_HOST_OFFLINE")
        self.assertTrue(res1["send_notification"])
        self.assertGreater(res1["pause_seconds"], 0)

        # Immediate next check should be BLOCKED
        allowed, reason = self.controller.should_execute("daily_sprint_report")
        self.assertFalse(allowed)
        self.assertIn("PAUSED_HOST_OFFLINE", reason)

        # 2nd immediate failure attempt does not spam notification
        res2 = self.controller.record_failure("daily_sprint_report", PauseReason.HOST_OFFLINE, "Connection refused")
        self.assertFalse(res2["send_notification"], "Notification was spammed during debounce window!")
        self.assertGreater(res2["pause_seconds"], res1["pause_seconds"], "Backoff did not increase!")

    def test_permission_denied_pause(self):
        """Permission denied halts repeated failing invocations and notifies once."""
        res = self.controller.record_failure("daily_sprint_report", PauseReason.PERMISSION_DENIED, "HTTP 403 Forbidden")
        self.assertEqual(res["state"], "PAUSED_PERMISSION_DENIED")
        self.assertTrue(res["send_notification"])

        allowed, reason = self.controller.should_execute("daily_sprint_report")
        self.assertFalse(allowed)
        self.assertIn("PAUSED_PERMISSION_DENIED", reason)

    def test_quota_exhausted_pause(self):
        """Quota exhausted pauses workflow until rate-limit reset window."""
        res = self.controller.record_failure("ai_sprint_summary", PauseReason.QUOTA_EXHAUSTED, "429 Rate limit exceeded", retry_after=60)
        self.assertEqual(res["state"], "PAUSED_QUOTA_EXHAUSTED")
        self.assertEqual(res["pause_seconds"], 60)

        allowed, reason = self.controller.should_execute("ai_sprint_summary")
        self.assertFalse(allowed)
        self.assertIn("PAUSED_QUOTA_EXHAUSTED", reason)

    def test_record_success_resets_pause(self):
        """Successful execution resets failure counters and clears pause."""
        self.controller.record_failure("daily_sprint_report", PauseReason.HOST_OFFLINE, "Connection timeout")
        self.assertFalse(self.controller.should_execute("daily_sprint_report")[0])

        # Connection recovers
        self.controller.record_success("daily_sprint_report")
        allowed, reason = self.controller.should_execute("daily_sprint_report")
        self.assertTrue(allowed)
        self.assertEqual(reason, "RUNNING")


if __name__ == "__main__":
    unittest.main()

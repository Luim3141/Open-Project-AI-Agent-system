"""Workflow Pause Controller (P07-07 under CR-USER-CAPACITY-20).
Halts automated workflow executions when:
1. Local Host or OpenProject is offline / unreachable (prevents retry storm).
2. Permissions are missing or denied (prevents endless failing calls).
3. AI provider quota is exhausted (preserves rate-limit budget and waits for reset).

Guarantees:
- Exponential backoff on consecutive connection failures.
- Debounced notifications: prevents alert flooding / duplicate notifications during outages.
- Clean recovery: automatically clears pause state upon verified successful execution.
- Deterministic-first: 0 LLM tokens consumed.
"""
from enum import Enum
import time
from typing import Any, Optional


class PauseReason(str, Enum):
    HOST_OFFLINE = "HOST_OFFLINE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"


class WorkflowPauseController:
    def __init__(
        self,
        base_backoff_seconds: int = 60,
        max_backoff_seconds: int = 1800,
        notification_debounce_seconds: int = 3600,
    ):
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.notification_debounce_seconds = notification_debounce_seconds

        # Maps workflow_id -> dict with status, pause_until, failures, last_notified
        self._states: dict[str, dict[str, Any]] = {}

    def _get_entry(self, workflow_id: str) -> dict[str, Any]:
        if workflow_id not in self._states:
            self._states[workflow_id] = {
                "state": "RUNNING",
                "pause_until": 0.0,
                "consecutive_failures": 0,
                "last_notified_at": 0.0,
                "last_reason": None,
                "last_details": None,
            }
        return self._states[workflow_id]

    def should_execute(self, workflow_id: str) -> tuple[bool, str]:
        """Checks if a workflow is currently permitted to run."""
        entry = self._get_entry(workflow_id)
        now = time.time()

        if entry["pause_until"] > now:
            remaining = int(entry["pause_until"] - now)
            return False, f"{entry['state']} (Pause remaining: {remaining}s)"

        if entry["state"] != "RUNNING" and entry["pause_until"] <= now:
            # Pause expired, tentative probe allowed
            return True, "PROBING"

        return True, "RUNNING"

    def record_failure(
        self,
        workflow_id: str,
        reason: PauseReason,
        details: str = "",
        retry_after: Optional[int] = None,
    ) -> dict[str, Any]:
        """Records a failure, calculates backoff pause window, and determines if notification is needed."""
        entry = self._get_entry(workflow_id)
        now = time.time()
        entry["consecutive_failures"] += 1
        failures = entry["consecutive_failures"]

        # Calculate pause duration
        if retry_after is not None and retry_after > 0:
            pause_seconds = retry_after
        elif reason == PauseReason.HOST_OFFLINE:
            pause_seconds = min(
                self.max_backoff_seconds,
                self.base_backoff_seconds * (2 ** min(failures - 1,16)),
            )
        elif reason == PauseReason.PERMISSION_DENIED:
            pause_seconds = 1800  # 30 minutes wait for admin intervention
        elif reason == PauseReason.QUOTA_EXHAUSTED:
            pause_seconds = 60  # Wait for minute quota window reset
        else:
            pause_seconds = self.base_backoff_seconds

        state_label = f"PAUSED_{reason.value}"
        entry["state"] = state_label
        entry["pause_until"] = now + pause_seconds
        entry["last_reason"] = reason.value
        entry["last_details"] = reason.value

        # Check notification debounce
        send_notification = False
        if (now - entry["last_notified_at"]) >= self.notification_debounce_seconds:
            send_notification = True
            entry["last_notified_at"] = now

        return {
            "workflow_id": workflow_id,
            "state": state_label,
            "pause_seconds": pause_seconds,
            "pause_until": entry["pause_until"],
            "consecutive_failures": failures,
            "send_notification": send_notification,
            "details": reason.value,
        }

    def record_success(self, workflow_id: str) -> None:
        """Resets the pause state and failure counter upon verified success."""
        entry = self._get_entry(workflow_id)
        entry["state"] = "RUNNING"
        entry["pause_until"] = 0.0
        entry["consecutive_failures"] = 0
        entry["last_reason"] = None
        entry["last_details"] = None


# Global singleton instance
_global_pause_controller = WorkflowPauseController()

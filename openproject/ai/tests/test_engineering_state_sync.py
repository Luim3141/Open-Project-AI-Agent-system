"""Tests for the Engineering State Synchronization Contract & Reconciliation Module."""
import json
import unittest
from unittest.mock import MagicMock, patch

from gateway.engineering_state_sync import (
    OP_STATUS,
    EXEC_STATES,
    DELIVERY_STATES,
    GH_STATES,
    RUNTIME_STATES,
    TASK_TRANSITION_GRAPH,
    STORY_TRANSITION_GRAPH,
    TRANSITION_GRAPH,
    find_transition_path,
    map_engineering_to_op,
    transition_work_package_safely,
    reconcile_engineering_project,
)


class EngineeringStateSyncTests(unittest.TestCase):
    def test_state_groups_definitions_and_ssot(self):
        # 1. OpenProject statuses
        self.assertIn("NEW", OP_STATUS)
        self.assertIn("IN_PROGRESS", OP_STATUS)
        self.assertIn("CODE_REVIEW", OP_STATUS)
        self.assertIn("IN_TESTING", OP_STATUS)
        self.assertIn("REVIEW", OP_STATUS)
        self.assertIn("READY_FOR_RELEASE", OP_STATUS)
        self.assertIn("DONE", OP_STATUS)
        self.assertIn("CANCELLED", OP_STATUS)

        # 2. Execution states
        self.assertTrue({"DEV", "REVIEW", "QA", "DONE", "CANCELLED", "PAUSED"} <= EXEC_STATES)

        # 3. Delivery states
        self.assertTrue({"NOT_STARTED", "IN_DELIVERY", "DELIVERED", "REJECTED"} <= DELIVERY_STATES)

        # 4. GitHub states
        self.assertTrue({"BRANCH_CREATED", "COMMIT_PUSHED", "PR_OPEN", "PR_MERGED"} <= GH_STATES)

        # 5. Runtime states
        self.assertTrue({"OFF", "STARTING", "RUNNING", "STOPPED"} <= RUNTIME_STATES)

    def test_find_transition_path(self):
        # 1. Type 1 (Task): Path from NEW (1) to REVIEW (34)
        path = find_transition_path(1, 34, type_id=1)
        self.assertEqual(path, [37, 38, 7, 39, 40, 9, 34])

        # Type 1: Path from NEW (1) to READY FOR RELEASE (41)
        path = find_transition_path(1, 41, type_id=1)
        self.assertEqual(path, [37, 38, 7, 39, 40, 9, 34, 41])

        # Type 1: Path from NEW (1) to IN PROGRESS (7)
        path = find_transition_path(1, 7, type_id=1)
        self.assertEqual(path, [37, 38, 7])

        # 2. Type 5 (Story): Path from NEW (1) to REVIEW (34)
        path = find_transition_path(1, 34, type_id=5)
        self.assertEqual(path, [33, 7, 34])

        # Type 5: Path from READY (33) to REVIEW (34)
        path = find_transition_path(33, 34, type_id=5)
        self.assertEqual(path, [7, 34])

        # Same status: empty path
        self.assertEqual(find_transition_path(34, 34), [])

        # Non-existent target from terminal CLOSED
        self.assertIsNone(find_transition_path(12, 1))

    def test_map_engineering_to_op(self):
        # Delivered with open PR -> REVIEW (34)
        status_id, reason = map_engineering_to_op("DONE", "DELIVERED", "PR_OPEN")
        self.assertEqual(status_id, 34)
        self.assertIn("open PR", reason)

        # Delivered with merged PR -> DONE (35)
        status_id, reason = map_engineering_to_op("DONE", "DELIVERED", "PR_MERGED")
        self.assertEqual(status_id, 35)

        # Executing QA -> IN TESTING (9)
        status_id, reason = map_engineering_to_op("QA", "IN_DELIVERY")
        self.assertEqual(status_id, 9)

        # Executing Review -> CODE REVIEW (39)
        status_id, reason = map_engineering_to_op("REVIEW", "IN_DELIVERY")
        self.assertEqual(status_id, 39)

        # Executing Dev -> IN PROGRESS (7)
        status_id, reason = map_engineering_to_op("DEV", "IN_DELIVERY")
        self.assertEqual(status_id, 7)

        # Cancelled -> CANCELLED (36)
        status_id, reason = map_engineering_to_op("CANCELLED", "NOT_STARTED")
        self.assertEqual(status_id, 36)

    def test_transition_work_package_safely_no_op_when_already_target(self):
        native = MagicMock()
        native.package.return_value = {
            "id": 380,
            "lockVersion": 5,
            "_links": {
                "status": {"href": "/api/v3/statuses/34"},
                "type": {"href": "/api/v3/types/1"},
            },
        }
        res = transition_work_package_safely(None, native, 20, 380, 34)
        self.assertFalse(res["changed"])
        self.assertEqual(res["status_id"], 34)
        native.call.assert_not_called()

    def test_transition_work_package_safely_step_by_step_and_comment(self):
        native = MagicMock()
        # Story (Type 5): Transition from READY (33) to REVIEW (34): path is [7, 34]
        pkg_v1 = {
            "id": 380,
            "lockVersion": 1,
            "_links": {
                "status": {"href": "/api/v3/statuses/33"},
                "type": {"href": "/api/v3/types/5"},
            },
        }
        pkg_v2 = {
            "id": 380,
            "lockVersion": 2,
            "_links": {
                "status": {"href": "/api/v3/statuses/7"},
                "type": {"href": "/api/v3/types/5"},
            },
        }
        pkg_v3 = {
            "id": 380,
            "lockVersion": 3,
            "_links": {
                "status": {"href": "/api/v3/statuses/34"},
                "type": {"href": "/api/v3/types/5"},
            },
        }

        # Sequence of package reads: initial, readback after step 1, readback after step 2
        native.package.side_effect = [pkg_v1, pkg_v2, pkg_v3]
        native.call.side_effect = [
            {"lockVersion": 2},  # PATCH to 7
            {"lockVersion": 3},  # PATCH to 34
            {"id": "activity-1"},  # POST activity comment
        ]

        res = transition_work_package_safely(
            None, native, 20, 380, 34, comment="Unit verified"
        )
        self.assertTrue(res["changed"])
        self.assertEqual(res["from_status"], 33)
        self.assertEqual(res["to_status"], 34)
        self.assertEqual(res["transitions_applied"], [7, 34])
        self.assertEqual(res["lock_version"], 3)
        self.assertEqual(native.call.call_count, 3)

    def test_transition_work_package_safely_rejects_lock_version_mismatch(self):
        native = MagicMock()
        pkg_v1 = {
            "id": 380,
            "lockVersion": 1,
            "_links": {
                "status": {"href": "/api/v3/statuses/1"},
                "type": {"href": "/api/v3/types/1"},
            },
        }
        pkg_stale = {
            "id": 380,
            "lockVersion": 99,
            "_links": {
                "status": {"href": "/api/v3/statuses/1"},
                "type": {"href": "/api/v3/types/1"},
            },
        }

        native.package.side_effect = [pkg_v1, pkg_stale]
        native.call.return_value = {"lockVersion": 2}

        with self.assertRaises(RuntimeError) as ctx:
            transition_work_package_safely(None, native, 20, 380, 34)
        self.assertIn("NATIVE_READBACK_CHANGED", str(ctx.exception))

    def test_reconcile_engineering_project_updates_children_and_parent(self):
        service = MagicMock()
        native = MagicMock()

        # Mock database rows for delivered runs
        mock_runs = [
            ("run-1", json.dumps({"project_id": 6, "unit": "unit-1", "native_id": 380}), json.dumps({"status": "succeeded", "head_sha": "a"*40, "pr_url": "https://github.com/Luim3141/mini-task-manager/pull/1", "test_evidence": {"exit_code": 0}})),
            ("run-2", json.dumps({"project_id": 6, "unit": "unit-2", "native_id": 381}), json.dumps({"status": "succeeded", "head_sha": "b"*40, "pr_url": "https://github.com/Luim3141/mini-task-manager/pull/2", "test_evidence": {"exit_code": 0}})),
            ("run-3", json.dumps({"project_id": 6, "unit": "unit-3", "native_id": 382}), json.dumps({"status": "succeeded", "head_sha": "c"*40, "pr_url": "https://github.com/Luim3141/mini-task-manager/pull/3", "test_evidence": {"exit_code": 0}})),
            ("run-4", json.dumps({"project_id": 6, "unit": "unit-4", "native_id": 383}), json.dumps({"status": "succeeded", "head_sha": "d"*40, "pr_url": "https://github.com/Luim3141/mini-task-manager/pull/4", "test_evidence": {"exit_code": 0}})),
        ]

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = mock_runs
        service.store.connect.return_value.__enter__.return_value = mock_db

        # Mock packages
        def mock_package(wid):
            return {
                "id": wid,
                "lockVersion": 1,
                "_links": {"status": {"href": "/api/v3/statuses/1"}},
            }
        native.package.side_effect = mock_package
        native.call.return_value = {"lockVersion": 2}

        with patch("gateway.engineering_state_sync.transition_work_package_safely") as mock_trans:
            mock_trans.return_value = {"changed": True, "status_id": 34}
            receipt = reconcile_engineering_project(service, native, actor=20, project_id=6)

            self.assertEqual(receipt["reconciled_children"], 4)
            self.assertEqual(receipt["progress_percent"], 100)
            self.assertEqual(receipt["audit"], "STATE_SYNC_RECONCILIATION_SUCCESS")
            # Called 4 times for children and 1 time for parent 379
            self.assertEqual(mock_trans.call_count, 5)


if __name__ == "__main__":
    unittest.main()

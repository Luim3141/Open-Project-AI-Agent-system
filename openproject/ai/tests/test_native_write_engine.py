"""Test suite for Phase 6: Native API Write Engine (T10 - T14).

Verifies:
- T10: Live Read-Only Work Package via Native API v3 (lockVersion, project isolation).
- T11: Controlled Live Write with Read-After-Write verification.
- T12: RBAC Unauthorized Role write rejection (BA cannot transition or create work packages).
- T13: Optimistic Locking conflict resolution (STALE_WORK_PACKAGE on lockVersion mismatch).
- T14: Idempotency deduplication and reuse rejection.
- Proposal: 2-step Proposal & Confirmation workflow.
"""

import json
import os
import pathlib
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gateway.service import Service
from gateway.store import Store


@unittest.skip("BLOCKED: legacy tests touch Main business/state or production vectors; use isolated regressions and approved dedicated E2E resources")
class NativeWriteEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "gateway"
        cls.store = Store(cls.root)
        config = json.loads((cls.root / "config.json").read_text())
        # Use localhost for host-based test runner
        config["openproject_url"] = "http://localhost:8088"
        cls.config = config
        cls.service = Service(cls.store, config, str(cls.root / "workspaces"))

    def test_t10_read_live_work_package_via_native_api(self):
        """T10: Read live Work Package 38 via Native API v3."""
        # Both PM (19) and BA (20) have read access
        for actor in (19, 20):
            res = self.service.execute_actor(actor, {
                "action": "get_work_package",
                "arguments": {"id": 38}
            })
            self.assertIn("result", res)
            wp = res["result"]
            self.assertEqual(wp["id"], 38)
            self.assertEqual(wp["subject"], "Tài khoản & Role")
            self.assertIn("lockVersion", wp)
            self.assertIsInstance(wp["lockVersion"], int)
            self.assertGreaterEqual(wp["lockVersion"], 1)
            self.assertEqual(wp["_links"]["project"]["href"], "/api/v3/projects/5")

    def test_t11_controlled_live_write_with_read_after_write(self):
        """T11: Controlled live write with Read-After-Write verification."""
        # Read current lockVersion
        wp = self.service.execute_actor(19, {
            "action": "get_work_package",
            "arguments": {"id": 38}
        })["result"]
        current_lv = wp["lockVersion"]

        test_ts = int(time.time() * 1000)
        idempotency_key = f"t11-write-{test_ts}"
        comment_text = f"[PHASE6-T11-TEST] Automated write verification at {test_ts}"

        # Execute write by PM with confirmation
        res = self.service.execute_actor(19, {
            "action": "comment",
            "arguments": {
                "id": 38,
                "lock_version": current_lv,
                "text": comment_text,
            },
            "idempotency_key": idempotency_key,
        }, confirmed=True)

        self.assertIn("result", res)
        self.assertIn("correlation_id", res)
        activity = res["result"]
        self.assertIn("id", activity)
        raw_comment = activity.get("comment", {}).get("raw", "")
        self.assertIn(comment_text, raw_comment)
        self.assertIn("QLDAPM-request-", raw_comment)

        # Read back independently to verify persistence
        native, _ = self.service.native_actor(19)
        activities = native.collection("/api/v3/work_packages/38/activities")
        matched = [a for a in activities if a.get("id") == activity["id"]]
        self.assertEqual(len(matched), 1, "Activity must be persisted and readable via Native API")
        self.assertIn(comment_text, matched[0].get("comment", {}).get("raw", ""))

    def test_t12_rbac_unauthorized_role_write_rejection(self):
        """T12: RBAC rejects write attempts from non-PM roles (e.g. BA actor 20)."""
        wp = self.service.execute_actor(19, {
            "action": "get_work_package",
            "arguments": {"id": 38}
        })["result"]
        current_lv = wp["lockVersion"]

        # 1. BA attempts status transition -> PM_REQUIRED
        with self.assertRaises(PermissionError) as ctx:
            self.service.execute_actor(20, {
                "action": "transition",
                "arguments": {"id": 38, "lock_version": current_lv, "status_id": 7},
                "idempotency_key": f"t12-trans-{int(time.time())}"
            }, confirmed=True)
        self.assertIn("PM_REQUIRED", str(ctx.exception))
        self.assertIn("role BA không có quyền transition", str(ctx.exception))

        # 2. BA attempts create_work_package -> PM_REQUIRED
        with self.assertRaises(PermissionError) as ctx:
            self.service.execute_actor(20, {
                "action": "create_work_package",
                "arguments": {
                    "source_id": f"BA_FORBIDDEN_{int(time.time())}",
                    "subject": "Forbidden task from BA",
                    "type_id": 1,
                    "parent_id": 38
                },
                "idempotency_key": f"t12-create-{int(time.time())}"
            }, confirmed=True)
        self.assertIn("PM_REQUIRED", str(ctx.exception))
        self.assertIn("role BA không có quyền create_work_package", str(ctx.exception))

    def test_t13_optimistic_locking_stale_work_package(self):
        """T13: Optimistic locking rejects mutation when lock_version does not match."""
        stale_lv = 999999

        # PM attempts comment with invalid/stale lockVersion
        with self.assertRaises(ValueError) as ctx:
            self.service.execute_actor(19, {
                "action": "comment",
                "arguments": {
                    "id": 38,
                    "lock_version": stale_lv,
                    "text": "This must be rejected due to stale lock_version",
                },
                "idempotency_key": f"t13-stale-{int(time.time())}"
            }, confirmed=True)
        self.assertEqual(str(ctx.exception), "STALE_WORK_PACKAGE")

    def test_t14_idempotency_deduplication_and_reuse_rejection(self):
        """T14: Idempotency deduplication caches result; key reuse with different payload is rejected."""
        wp = self.service.execute_actor(19, {
            "action": "get_work_package",
            "arguments": {"id": 38}
        })["result"]
        current_lv = wp["lockVersion"]

        test_ts = int(time.time() * 1000)
        idempotency_key = f"t14-idem-{test_ts}"
        comment_text = f"[PHASE6-T14-IDEM] Single write test at {test_ts}"

        payload = {
            "action": "comment",
            "arguments": {
                "id": 38,
                "lock_version": current_lv,
                "text": comment_text,
            },
            "idempotency_key": idempotency_key,
        }

        # 1. First execution -> succeeds and writes to OpenProject
        first_call = self.service.execute_actor(19, payload, confirmed=True)
        self.assertIn("result", first_call)
        first_activity_id = first_call["result"]["id"]

        # Count activities before duplicate call
        native, _ = self.service.native_actor(19)
        count_before = len(native.collection("/api/v3/work_packages/38/activities"))

        # 2. Duplicate execution with identical key and payload -> returns cached result
        second_call = self.service.execute_actor(19, payload, confirmed=True)
        self.assertEqual(second_call["result"]["id"], first_activity_id, "Cached result must be returned")

        # Verify no duplicate activity was created in OpenProject
        count_after = len(native.collection("/api/v3/work_packages/38/activities"))
        self.assertEqual(count_before, count_after, "Idempotent duplicate call must NOT create a new activity")

        # 3. Third execution with SAME key but DIFFERENT payload -> raises IDEMPOTENCY_KEY_REUSED
        different_payload = {
            "action": "comment",
            "arguments": {
                "id": 38,
                "lock_version": current_lv,
                "text": "Different content using the same key",
            },
            "idempotency_key": idempotency_key,
        }
        with self.assertRaises(ValueError) as ctx:
            self.service.execute_actor(19, different_payload, confirmed=True)
        self.assertEqual(str(ctx.exception), "IDEMPOTENCY_KEY_REUSED")

    def test_proposal_and_preview_workflow(self):
        """Verifies 2-step proposal creation when confirmed=False."""
        wp = self.service.execute_actor(19, {
            "action": "get_work_package",
            "arguments": {"id": 38}
        })["result"]
        current_lv = wp["lockVersion"]

        prop_key = f"prop-workflow-{int(time.time() * 1000)}"
        res = self.service.execute_actor(19, {
            "action": "comment",
            "arguments": {
                "id": 38,
                "lock_version": current_lv,
                "text": "Proposed comment preview test",
            },
            "idempotency_key": prop_key,
        }, confirmed=False)

        prop = res["result"]
        self.assertIn("id", prop)
        self.assertIn("hash", prop)
        self.assertEqual(prop["state"], "pending")
        self.assertTrue(prop["human_confirmation_required"])
        self.assertIn("preview", prop["command"])
        self.assertIn("before", prop["command"]["preview"])
        self.assertIn("changes", prop["command"]["preview"])


if __name__ == "__main__":
    unittest.main()

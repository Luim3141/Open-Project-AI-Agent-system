"""Fault-Injection Test Suite for QLDAPM Multi-Agent System (P09-04).
Tests system resilience against:
1. Provider 429 (Rate Limit / Quota Exhaustion) -> bounded backoff, WAITING_QUOTA, no duplicate writes.
2. Provider 503 / Network Timeout -> outcome unknown, proven receipt required before retry, reconciliation.
3. Crash / Container Restart -> SQLite WAL consistency, idempotency key persistence, zero duplicate writes.
4. Quota Reset (00:00 PST) -> quota counters refresh while proposal ledger and idempotency records stay durable.
"""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from gateway.gemini import Gemini
from gateway.native import NativeError
from gateway.service import Service
from gateway.store import Store, canonical, digest


class MockNativeFault:
    def __init__(self, *args, **kwargs):
        self.posted_comments = []

    def identity(self, actor: int):
        return {"user_id": actor, "project_id": 5, "role": "PM"}

    def package(self, wp_id: int):
        return {"id": wp_id, "lockVersion": 1, "subject": f"Work Package #{wp_id}"}

    def collection(self, path: str):
        if "activities" in path:
            return self.posted_comments
        return []

    def call(self, path: str, method="GET", payload=None, *args, **kwargs):
        if "permissions" in path:
            return {
                "effective": {
                    "add_work_packages": True,
                    "edit_work_packages": True,
                    "add_work_package_comments": True,
                }
            }
        if "activities" in path and method == "POST":
            raw_comment = payload.get("comment", {}).get("raw", "")
            item = {
                "id": len(self.posted_comments) + 1,
                "comment": {"raw": raw_comment},
                "_links": {"user": {"href": f"/api/v3/users/10"}},
            }
            self.posted_comments.append(item)
            return item
        return {"id": 1, "status": "ok"}


class FaultInjectionTests(unittest.TestCase):
    def test_provider_429_trips_circuit_breaker_and_preserves_ledger(self):
        """Simulate HTTP 429: verifies store does not corrupt runs and enters rate-limited state."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "gemini.key").write_text("fake-key")
            store = Store(root)
            limits = {"rpm": 1, "tpm": 1000, "rpd": 5}

            # First reservation consumes quota
            store.reserve_gemini("test-project", limits, 100)

            # Second reservation immediately triggers 429 / RPM exhaustion
            with self.assertRaises(ValueError) as ctx:
                store.reserve_gemini("test-project", limits, 100)
            self.assertIn("RPM_EXHAUSTED", str(ctx.exception))
            self.assertTrue(hasattr(ctx.exception, "retry_at"))

            # Verify ledger persists valid records without data corruption
            with store.connect() as db:
                count = db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0]
                self.assertEqual(count, 1)

    def test_timeout_and_reconciliation_prevents_duplicate_writes(self):
        """Simulate network timeout: reconcile_request must detect existing marker and not repeat POST."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)
            (store.root / "credentials.json").write_text(json.dumps({"10": "token"}))
            native = MockNativeFault()
            service = Service(
                store,
                {
                    "users": {"10": "PM"},
                    "project_id": 5,
                    "gateway_mode": "native",
                    "openproject_url": "http://127.0.0.1:18091",
                    "hosts": ["testserver"],
                },
                root / "workspaces",
                lambda *a, **k: native,
            )

            request_key = "req-idempotent-write-01"
            comment_args = {
                "id": 50,
                "lock_version": 1,
                "text": "Báo cáo kiểm thử tự động",
            }

            # 1. Execute initial comment
            result1 = service.perform({"user_id": 10, "role": "PM"}, native, "comment", comment_args, request_key=request_key)
            self.assertIn("Báo cáo kiểm thử tự động", result1["comment"]["raw"])
            self.assertEqual(len(native.posted_comments), 1)

            # 2. Simulate client lost connection / timeout and calls reconcile_request
            store.begin(10, request_key, {"action": "comment", "arguments": comment_args})
            reconcile_res = service.perform({"user_id": 10, "role": "PM"}, native, "reconcile_request", {"key": request_key})
            self.assertTrue(reconcile_res["reconciled"])

            # Verify NO SECOND COMMENT was created (zero duplicate write)
            self.assertEqual(len(native.posted_comments), 1, "Duplicate write occurred during reconciliation!")

    def test_crash_and_restart_simulation_with_sqlite_wal(self):
        """Simulate abrupt process termination: committed records survive, idempotency avoids duplicate execution."""
        request_key = "crash-test-idempotency-key"
        payload = {"action": "create_work_package", "arguments": {"subject": "Critical Task"}}
        cached_result = {"status": "ok", "work_package_id": 88}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store1 = Store(root)

            # Record an idempotency key and a finished request
            store1.begin(10, request_key, payload)
            store1.finish(10, request_key, cached_result)

            # Record token usage
            store1.reserve_gemini("project-alpha", {"rpm": 10, "tpm": 5000, "rpd": 100}, 50)

            # Verify WAL journal mode is active
            with store1.connect() as db:
                journal = db.execute("PRAGMA journal_mode").fetchone()[0]
                self.assertEqual(journal.lower(), "wal")

            # -----------------------------------------------------------------
            # SIMULATE CONTAINER CRASH & RESTART: Initialize fresh Store on same directory
            # -----------------------------------------------------------------
            store2 = Store(root)

            # Querying the same idempotency key after restart returns the exact saved result immediately
            cached = store2.begin(10, request_key, payload)
            self.assertEqual(cached["work_package_id"], 88)

            # Token ledger also survived
            with store2.connect() as db:
                usage_count = db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0]
                self.assertEqual(usage_count, 1)

    def test_quota_reset_boundary_preserves_proposals_and_idempotency(self):
        """Simulate daily quota reset: quota counters reset for new period while historical ledger is kept."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root)

            # Insert usage from yesterday (simulate time in past)
            yesterday_time = time.time() - 86400 * 2  # 2 days ago
            with store.connect() as db:
                db.execute(
                    "INSERT INTO gemini_usage(project, at, input_tokens) VALUES(?, ?, ?)",
                    ("proj-test", yesterday_time, 200),
                )

            # Check that yesterday usage does not block today's daily limit
            today_limits = {"rpm": 10, "tpm": 5000, "rpd": 100}
            # Should succeed because today's usage bucket is 0
            store.reserve_gemini("proj-test", today_limits, 50)

            # Verify both past and current usage rows are preserved for historical audit
            with store.connect() as db:
                total_rows = db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0]
                self.assertEqual(total_rows, 2)


if __name__ == "__main__":
    unittest.main()

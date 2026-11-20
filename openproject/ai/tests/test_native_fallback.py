"""UI contract is factual on quota/offline/stale paths; no model substitute or cached ACL bypass."""
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.gemini import Gemini, ProviderError, MODEL
from gateway.native import NativeError
from gateway.service import Service
from gateway.store import Store, digest
from tests import test_local_queries


class NativeFallbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_local_queries.LocalQueryTests()
        self.fixture.setUp()
        self.root, self.store, self.service = self.fixture.root, self.fixture.store, self.fixture.service
        self.policy = {"project": "fixture", "model": MODEL, "limits": {"rpm": 13, "tpm": 225000, "rpd": 450},
                       "tier": "Free", "data_scope": "project-business-content", "checked_at": time.time() - 1,
                       "authorization": {"mode": "continuous-free-only", "billing_allowed": False,
                                         "authorized_at": time.time() - 1, "user_request_sha256": digest("fixture consent")}}

    def tearDown(self):
        self.fixture.tearDown()

    def status(self):
        return self.service.execute_actor(7, {"action": "get_assistant_status"})["result"]

    def test_ui_status_distinguishes_quota_offline_key_and_native_fallback_without_sdk(self):
        with patch.object(self.service.gemini, "settings", return_value=self.policy), patch.object(Gemini, "sdk_client", side_effect=AssertionError("No outbound status probes")) as sdk:
            with self.store.connect() as db:
                db.executemany("INSERT INTO gemini_usage VALUES('fixture',?,1)", [(time.time(),)] * 450)
            quota = self.status()
            self.assertEqual(quota["gemini"]["state"], "WAITING_QUOTA")
            self.assertEqual(quota["gemini"]["authorization_state"], "authorized")
            self.assertFalse(quota["native_reporting"]["model_used"])
            self.store.block_gemini("fixture", "GEMINI_UPSTREAM_REJECTED; HTTP=503", 60)
            self.assertEqual(self.status()["gemini"]["state"], "OFFLINE")
            self.store.block_gemini("fixture", "GEMINI_AUTH_401")
            self.assertEqual(self.status()["gemini"]["state"], "BLOCKED_KEY_OR_MODEL")
            receipt = self.fixture.start("Đếm công việc", "native-despite-provider")
            self.assertFalse(receipt["result"]["model_used"])
            self.assertEqual(receipt["result"]["source"], "native")
            sdk.assert_not_called()
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 450)

    def test_native_read_cache_offline_is_not_shown_as_fresh_and_forbidden_is_still_denied(self):
        receipt = self.fixture.start("Đọc công việc 1")
        command = {"action": "get_ai_run", "arguments": {"id": receipt["result"]["id"]}}
        with patch.object(self.fixture.native_factory, "package", side_effect=NativeError(503, "OPENPROJECT_UNAVAILABLE")):
            result = self.service.execute_actor(7, command)["result"]["result"]
            self.assertEqual(result["connection_state"], "OFFLINE")
            self.assertEqual(result["status"], "offline")
            self.assertEqual(result["tools"], [])
            self.assertNotIn("Synthetic first", json.dumps(result))
        with patch.object(self.fixture.native_factory, "package", side_effect=PermissionError("READ_REVOKED")), self.assertRaises(PermissionError):
            self.service.execute_actor(7, command)
        self.assertIn("Synthetic first", self.store.run(7, receipt["result"]["id"])["result"]["text"], "Original private receipt retained")

    def test_provider_offline_preserves_partial_write_receipts_and_does_not_fake_a_model_answer(self):
        payload = {"prompt": "synthetic", "allow_routine_writes": True, "write_scope_ids": [58]}
        identifier = self.store.enqueue_run(7, payload)["result"]["id"]
        run = self.store.claim_run()
        tools = [{"action": "comment", "arguments": {"id": 58, "text": "Synthetic receipt"},
                  "result": {"result": {"id": 20, "native_confirmed": True}}}]
        self.store.progress_run(7, identifier, {"tools": tools})
        with patch.object(self.service.gemini, "settings", return_value=self.policy), patch("gateway.service.run_isolated", side_effect=ProviderError("GEMINI_TIMEOUT")) as worker:
            self.service.process_run(run)
            worker.assert_called_once()
        result = self.store.run(7, identifier)
        self.assertEqual(result["state"], "failed_or_unknown")
        self.assertEqual(result["result"]["status"], "partial")
        self.assertEqual(result["result"]["connection_state"], "OFFLINE")
        self.assertEqual(result["result"]["tools"], tools)
        self.assertNotIn("model", result["result"])
        self.assertIsNone(self.store.claim_run(), "Interrupted write never replayed")


if __name__ == "__main__":
    unittest.main()

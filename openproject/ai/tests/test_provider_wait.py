"""Quota/provider wait and safe phase-only retry; synthetic transport/clock, no real API calls."""
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

import httpx
from gateway.gemini import Gemini, ProviderError
from gateway.service import Service
from gateway.store import Store, digest


class ProviderWaitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)
        self.gemini = Gemini(self.root)
        self.policy = {"project": "fixture", "limits": {"rpm": 13, "tpm": 225000, "rpd": 450}}

    def tearDown(self):
        self.temporary.cleanup()

    def error(self, status=503, delay=2):
        error = ProviderError("synthetic explicit rejection")
        error.status, error.retryable, error.retry_at = status, True, 100 + delay
        return error

    def test_retry_is_bounded_exponential_jitter_and_reserves_each_attempt(self):
        for status in (429, 503):
            with self.subTest(status=status):
                budget, events = Mock(), []
                with patch.object(self.gemini, "sdk_post", side_effect=self.error(status)) as post, patch.object(self.gemini, "settings", return_value=self.policy), patch("gateway.gemini.time.time", return_value=100), patch("gateway.gemini.time.monotonic", return_value=0), patch("gateway.gemini.random.uniform", return_value=0.25), patch("gateway.gemini.time.sleep") as sleep:
                    with self.assertRaises(ProviderError):
                        self.gemini.post_with_retry(None, budget, self.policy, "generateContent", {}, 50, 600, lambda *args: events.append(args))
                self.assertEqual(post.call_count, 3)
                self.assertEqual(budget.reserve_gemini.call_count, 2)
                self.assertEqual([call.args[0] for call in sleep.call_args_list], [2.25, 4.25])
                self.assertIn("WAITING_QUOTA" if status == 429 else "WAITING_PROVIDER", events[0])

    def test_retry_cannot_cross_deadline_or_daily_reset(self):
        with patch.object(self.gemini, "sdk_post", side_effect=self.error(429, 3600)) as post, patch("gateway.gemini.time.time", return_value=100), patch("gateway.gemini.time.monotonic", return_value=0), patch("gateway.gemini.time.sleep") as sleep:
            with self.assertRaises(ProviderError):
                self.gemini.post_with_retry(None, self.store, self.policy, "countTokens", {}, 0, 600, lambda *args: None)
        self.assertEqual(post.call_count, 1)
        sleep.assert_not_called()

    def test_permanent_errors_unknown_transport_and_timeout_never_retry(self):
        for error in (ProviderError("GEMINI_AUTH_401"), ProviderError("GEMINI_TIMEOUT"), ProviderError("GEMINI_UNAVAILABLE_OR_MALFORMED")):
            with self.subTest(error=str(error)), patch.object(self.gemini, "sdk_post", side_effect=error) as post, patch("gateway.gemini.time.sleep") as sleep:
                with self.assertRaises(ProviderError):
                    self.gemini.post_with_retry(None, self.store, self.policy, "generateContent", {}, 50, 600, lambda *args: None)
                post.assert_called_once()
                sleep.assert_not_called()

    def test_retry_rechecks_policy_and_does_not_refund_or_bypass_quota(self):
        for failure in (ValueError("GEMINI_LOCAL_RPD_EXHAUSTED"), ProviderError("GEMINI_VERIFICATION_CHANGED")):
            with self.subTest(error=str(failure)), patch.object(self.gemini, "sdk_post", side_effect=self.error()) as post, patch.object(self.gemini, "reserve_budget", side_effect=failure), patch("gateway.gemini.time.time", return_value=100), patch("gateway.gemini.time.monotonic", return_value=0), patch("gateway.gemini.time.sleep"):
                with self.assertRaises(type(failure)):
                    self.gemini.post_with_retry(None, self.store, self.policy, "generateContent", {}, 50, 600, lambda *args: None)
                post.assert_called_once()

    def test_pending_five_users_wait_daily_quota_without_worker_and_survive_reopen(self):
        with self.store.connect() as db:
            db.executemany("INSERT INTO gemini_usage VALUES('fixture',?,1)", [(time.time(),)] * 450)
        ids = []
        payload = {"prompt": "synthetic", "allow_routine_writes": False, "write_scope_ids": []}
        for actor in range(6, 11):
            ids.append((actor, self.store.enqueue_run(actor, payload)["result"]["id"]))
        service = Service(self.store, {"gateway_mode": "native", "project_id": 3}, self.root / "workspaces")
        with patch.object(service.gemini, "settings", return_value=self.policy), patch("gateway.service.run_isolated") as worker:
            service.start_dispatcher()
            deadline = time.monotonic() + 3
            while any(self.store.run(actor, identifier)["result"]["queue_state"] != "WAITING_QUOTA" for actor, identifier in ids):
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.01)
            service.stop_dispatcher()
            worker.assert_not_called()
        reopened = Store(self.root)
        self.assertTrue(all(reopened.run(actor, identifier)["state"] == "running" for actor, identifier in ids))
        self.assertGreater(reopened.provider_wait(self.policy)["retry_at"], time.time())
        with reopened.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 450)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_queue WHERE state='queued'").fetchone()[0], 5)

    def test_minute_tpm_circuit_and_reset_are_advisory_not_new_reservations(self):
        now = time.time()
        self.store.reserve_gemini("fixture", self.policy["limits"], 225000)
        wait = self.store.provider_wait(self.policy)
        self.assertEqual(wait["queue_state"], "WAITING_QUOTA")
        self.assertGreater(wait["retry_at"], now)
        with patch("gateway.store.time.time", return_value=now + 61):
            self.assertIsNone(self.store.provider_wait(self.policy))
        self.store.block_gemini("fixture", "GEMINI_UPSTREAM_REJECTED; HTTP=503", 60)
        self.assertEqual(self.store.provider_wait(self.policy)["queue_state"], "WAITING_PROVIDER")
        self.store.block_gemini("fixture", "GEMINI_AUTH_401")
        self.assertEqual(self.store.provider_wait(self.policy)["queue_state"], "BLOCKED_KEY_OR_MODEL")
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 1)

    def test_invalid_request_fails_once_without_blocking_other_valid_actor_requests(self):
        from gateway.live_agents import LiveBudget,LiveConfig,ModelAnalysis
        (self.root/'gemini.key').write_text('synthetic-no-real-key')
        policy={**self.policy,'model':'gemini-fixture','data_scope':'project-business-content'}
        seen=[]
        def reject(request):
            seen.append(request.url.path)
            if request.url.path.endswith(':countTokens'):return httpx.Response(200,json={'totalTokens':10})
            return httpx.Response(400,json={'error':{'code':400,'status':'INVALID_ARGUMENT','message':'synthetic private schema diagnostic'}})
        with patch.object(self.gemini,'settings',return_value=policy):
            with self.assertRaisesRegex(ProviderError,'HTTP=400'):
                self.gemini.structured('synthetic analysis',ModelAnalysis,system='Synthetic',agent='ba',scope=None,
                    budget=LiveBudget(LiveConfig()),transport=httpx.MockTransport(reject))
        self.assertEqual(len(seen),2)
        self.assertIsNone(self.store.provider_wait(policy))
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM gemini_usage').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0],2)

    def test_real_sdk_transport_retries_only_rejected_phase_after_a_confirmed_write(self):
        for status in (429, 503):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "gemini.key").write_text("synthetic-no-real-key")
                policy = {"project": "fixture", "data_scope": "project-business-content",
                          "limits": {"rpm": 100, "tpm": 1000000, "rpd": 100},
                          "authorization": {"mode": "continuous-free-only", "billing_allowed": False,
                                            "authorized_at": 1, "user_request_sha256": digest("synthetic consent")}}
                clock, generations, mutations, progress = [0], [], [], []
                def wire(request):
                    if request.url.path.endswith(":countTokens"):
                        return httpx.Response(200, json={"totalTokens": 100})
                    generations.append(1)
                    if len(generations) == 2:
                        return httpx.Response(status, json={"error": {"code": status, "status": "RESOURCE_EXHAUSTED" if status == 429 else "UNAVAILABLE",
                            "message": "synthetic", "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "1s"}]}})
                    parts = [{"functionCall": {"name": "comment", "args": {"id": 58, "lock_version": 1, "text": "synthetic"}}}] if len(generations) == 1 else [{"text": '{"claims":[],"explanation":"Đã thêm bình luận #58"}'}]
                    return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": parts}}]})
                def execute(action, args):
                    mutations.append((action, args))
                    return {"result": {"id": 20, "_type": "Activity::Comment", "native_confirmed": True}}
                with patch.object(Gemini, "settings", return_value=policy), patch("gateway.gemini.time.time", side_effect=lambda: 1000 + clock[0]), patch("gateway.gemini.time.monotonic", side_effect=lambda: clock[0]), patch("gateway.gemini.time.sleep", side_effect=lambda delay: clock.__setitem__(0, clock[0] + delay)) as sleep, patch("gateway.gemini.random.uniform", return_value=0.25):
                    result = Gemini(root).run("Thêm bình luận công việc 58: synthetic", execute, httpx.MockTransport(wire), True, [58], progress.append, actor_role="PM")
                self.assertEqual(len(mutations), 1, "Never restart the run or replay a confirmed native write")
                self.assertEqual(len(generations), 3)
                self.assertEqual(len(result["tools"]), 1)
                self.assertEqual(result["status"], "succeeded")
                sleep.assert_called_once_with(1.25)
                self.assertTrue(any(row.get("queue_state") == ("WAITING_QUOTA" if status == 429 else "WAITING_PROVIDER") for row in progress))
                with Store(root).connect() as db:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 5)


if __name__ == "__main__":
    unittest.main()

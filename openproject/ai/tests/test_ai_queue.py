"""Durable fair scheduling with synthetic workers; no provider calls or business writes."""
import concurrent.futures
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from gateway.service import Service
from gateway.gemini import ProviderError
from gateway.store import Store, canonical


PAYLOAD = {"prompt": "Synthetic queue acceptance", "allow_routine_writes": False, "write_scope_ids": []}


class AIQueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def enqueue(self, actor=7, **kwargs):
        return self.store.enqueue_run(actor, PAYLOAD, **kwargs)["result"]["id"]

    def drain(self):
        actors = []
        while run := self.store.claim_run():
            actors.append(run["actor"])
            self.store.finish_run(run["actor"], run["id"], {"tools": []}, "done")
        return actors

    def test_five_actors_round_robin_even_at_identical_timestamps(self):
        with patch("gateway.store.time.time", return_value=1000):
            for actor in (7, 6, 8, 9, 10):
                for _ in range(20):
                    self.enqueue(actor)
            self.assertEqual(self.drain(), [7, 6, 8, 9, 10] * 20)

    def test_all_five_actors_share_one_persistent_provider_budget(self):
        for actor in (7, 6, 8, 9, 10):
            for _ in range(4):
                self.enqueue(actor)
        service, outbound = self.service(), []
        def worker(*args):
            Store(self.root).reserve_gemini("same-project", {"rpm": 13, "tpm": 225000, "rpd": 450}, 10)
            outbound.append(args[2])
            return {"tools": []}
        with patch("gateway.store.time.time", return_value=2000), patch.object(service.gemini, "settings", return_value={}), patch("gateway.service.run_isolated", side_effect=worker):
            service.start_dispatcher()
            self.wait(service)
        self.assertEqual(outbound, [7, 6, 8, 9, 10] * 2 + [7, 6, 8])
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 13)
        with patch("gateway.store.time.time", return_value=2001), self.assertRaisesRegex(ValueError, "RPM"):
            Store(self.root).reserve_gemini("same-project", {"rpm": 13, "tpm": 225000, "rpd": 450}, 10)

    def test_queued_intent_does_not_transfer_to_changed_policy(self):
        identifier = self.store.enqueue_run(7, {**PAYLOAD, "policy_sha256": "original-policy"})["result"]["id"]
        service = self.service()
        with patch.object(service.gemini, "settings", return_value={"project": "other-project"}), patch("gateway.service.run_isolated") as worker:
            service.start_dispatcher()
            self.wait(service)
            worker.assert_not_called()
        self.assertIn("VERIFICATION_CHANGED", self.store.run(7, identifier)["result"]["error"])

    def test_idle_share_is_reused_and_interactive_precedes_background(self):
        self.enqueue(8, kind="report")
        self.enqueue(9, kind="agent")
        for _ in range(4):
            self.enqueue(7)
        self.assertEqual(self.drain(), [7, 7, 7, 7, 9, 8])

    def test_pending_intents_survive_reopen_without_becoming_stale(self):
        with patch("gateway.store.time.time", return_value=1000):
            identifier = self.enqueue()
        reopened = Store(self.root)
        self.assertEqual(reopened.run(7, identifier)["state"], "running")
        self.assertEqual(reopened.claim_run()["id"], identifier)

    def test_concurrent_connections_claim_only_one_project_slot(self):
        for actor in (7, 6, 8, 9, 10):
            self.enqueue(actor)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            claims = list(pool.map(lambda _: Store(self.root).claim_run(), range(5)))
        self.assertEqual(sum(run is not None for run in claims), 1)

    def test_inflight_is_not_replayed_and_expiry_preserves_receipts(self):
        first, second = self.enqueue(), self.enqueue(8)
        with patch("gateway.store.time.time", return_value=1000):
            self.assertEqual(self.store.claim_run()["id"], first)
        receipt = {"tools": [{"action": "comment", "arguments": {"id": 58},
                              "result": {"result": {"id": 20, "native_confirmed": True}}}]}
        self.store.progress_run(7, first, receipt)
        reopened = Store(self.root)
        with patch("gateway.store.time.time", return_value=1100):
            self.assertIsNone(reopened.claim_run())
        with patch("gateway.store.time.time", return_value=2000):
            self.assertEqual(reopened.claim_run()["id"], second)
        failed = reopened.run(7, first)
        self.assertEqual(failed["state"], "failed_or_unknown")
        self.assertEqual(failed["result"]["tools"], receipt["tools"])
        self.assertEqual(failed["result"]["status"], "partial")
        reopened.finish_run(7, first, {"text": "late stale result"}, "done")
        self.assertEqual(reopened.run(7, first), failed)

    def test_atomic_idempotent_receipt_and_payload_binding(self):
        command = {"action": "start_ai_run", "arguments": PAYLOAD, "idempotency_key": "same-request", "auto_execute": False}
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(lambda _: Store(self.root).enqueue_run(7, PAYLOAD, command), range(5)))
        self.assertTrue(all(row == results[0] for row in results))
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_runs").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT state,result FROM requests").fetchone()[0], "done")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM audit").fetchone()[0], 1)
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_KEY_REUSED"):
            self.store.enqueue_run(7, PAYLOAD, {**command, "arguments": {**PAYLOAD, "prompt": "different"}})

    def test_limits_do_not_consume_idempotency_key_or_create_partial_run(self):
        for _ in range(20):
            self.enqueue()
        command = {"idempotency_key": "retry-on-capacity", "arguments": PAYLOAD}
        with self.assertRaisesRegex(ValueError, "AI_QUEUE_FULL"):
            self.store.enqueue_run(7, PAYLOAD, command)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_runs").fetchone()[0], 20)
        claim = self.store.claim_run()
        self.store.finish_run(7, claim["id"], {}, "done")
        self.store.enqueue_run(7, PAYLOAD, command)

    def test_total_bound_covers_five_actors(self):
        for actor in range(5):
            for _ in range(20):
                self.enqueue(actor + 1)
        with self.assertRaisesRegex(ValueError, "AI_QUEUE_FULL"):
            self.enqueue(99)

    def test_other_actor_cannot_poll_private_intent_or_result(self):
        identifier = self.enqueue(7)
        with self.assertRaisesRegex(PermissionError, "AI_RUN_NOT_FOUND"):
            self.store.run(8, identifier)
        public = canonical(self.store.run(7, identifier))
        self.assertNotIn(PAYLOAD["prompt"], public)

    def service(self):
        return Service(self.store, {"gateway_mode": "native", "project_id":3}, self.root / "workspaces")

    def wait(self, service):
        thread = service._queue_thread
        if thread:
            try:
                # Host fsync contention is not the queue fairness contract or a five-second SLO.
                thread.join(timeout=30)
                self.assertFalse(thread.is_alive())
            finally:
                service.stop_dispatcher()
                thread.join(timeout=10)

    def test_dispatcher_resumes_pending_once_and_keeps_per_run_consent(self):
        payload = {**PAYLOAD, "allow_routine_writes": True, "write_scope_ids": [58]}
        first = self.store.enqueue_run(7, payload)["result"]["id"]
        second = self.enqueue(8)
        service, captured = self.service(), []
        def worker(*args):
            captured.append((args[2], args[4], args[5], args[6]))
            return {"tools": [], "text": "synthetic"}
        with patch.object(service.gemini, "settings", return_value={}), patch("gateway.service.run_isolated", side_effect=worker):
            service.start_dispatcher()
            service.start_dispatcher()
            self.wait(service)
        self.assertEqual(captured, [(7, first, True, [58]), (8, second, False, [])])
        self.assertEqual(self.store.run(7, first)["state"], "done")

    def test_policy_revoked_while_waiting_stops_before_worker(self):
        identifier = self.enqueue()
        service = self.service()
        with patch.object(service.gemini, "settings", side_effect=ProviderError("FREE_ONLY_REVOKED")), patch("gateway.service.run_isolated") as worker:
            service.start_dispatcher()
            deadline = time.monotonic() + 3
            while self.store.run(7, identifier)["result"]["queue_state"] != "BLOCKED_KEY_OR_MODEL":
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.01)
            service.stop_dispatcher()
            self.wait(service)
            worker.assert_not_called()
        self.assertEqual(self.store.run(7, identifier)["state"], "running")

    def test_worker_role_revalidation_still_precedes_provider_call(self):
        from gateway import ai_worker
        import io
        payload = {"root": str(self.root), "workspaces": str(self.root / "workspaces"), "actor": 7,
                   "prompt": PAYLOAD["prompt"], "id": "fixture", "allow_routine_writes": False, "write_scope_ids": []}
        class BinaryStream:
            def __init__(self, data=b""):
                self.buffer = io.BytesIO(data)
        output = BinaryStream()
        with patch("sys.stdin", BinaryStream(json.dumps(payload).encode())), patch("sys.stdout", output), patch("gateway.service.Service") as factory:
            service = factory.return_value
            service.store = self.store
            service.config = {"project_id": 3}
            service.execute_actor.side_effect = PermissionError("USER_NOT_REGISTERED_OR_ROLE_CHANGED")
            (self.root / "config.json").write_text('{}')
            ai_worker.main()
            service.execute_actor.assert_called_once_with(7, {"action": "identity"})
            service.gemini.run.assert_not_called()
        self.assertIn("error", json.loads(output.buffer.getvalue()))


if __name__ == "__main__":
    unittest.main()

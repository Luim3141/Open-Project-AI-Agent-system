import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from gateway.agent_models import AgentTask
from gateway.store import Store, canonical, digest
from gateway.service import Service


class AgentQueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)

    def task(self, actor=7, **changes):
        now = time.time()
        task = AgentTask(**{ "task_id": str(uuid.uuid4()), "actor_id": actor, "project_id": 3,
            "conversation_id": str(uuid.uuid4()), "agent": "qa", "instruction": "Synthetic agent queue test",
            "created_at": now, "expires_at": now + 600, **changes})
        self.store.create_agent_task(actor, 3, task)
        return task

    def enqueue(self, task, key=None, **changes):
        payload = {"prompt": task.instruction, "allow_routine_writes": False, "write_scope_ids": [], "policy_sha256": "a" * 64, **changes}
        command = {"action": "start_ai_run", "arguments": {"prompt": task.instruction}, "idempotency_key": key} if key else None
        return self.store.enqueue_run(task.actor_id, payload, command, task.run_class, agent_task=task)

    def test_five_actors_share_existing_queue_and_result_receipts(self):
        identifiers = []
        tasks = [self.task(actor) for actor in (7, 6, 8, 9, 10)]
        for task in tasks:
            response = self.enqueue(task, "same-key-per-actor")
            self.assertEqual(response, self.enqueue(task, "same-key-per-actor"))
            identifier = response["result"]["id"]
            identifiers.append(identifier)
            metadata = self.store.agent_run(task.actor_id, 3, identifier)
            self.assertEqual(metadata.trace_id, response["correlation_id"])
            self.assertEqual(metadata.task_id, task.task_id)
        self.store = Store(self.root)
        seen = []
        while run := self.store.claim_run():
            seen.append(run["actor"])
            self.assertIsNone(self.store.claim_run())
            self.assertEqual(self.store.agent_run(run["actor"], 3, run["id"]).state, "RUNNING")
            self.store.finish_run(run["actor"], run["id"], {"status": "answered", "tools": [], "text": "Synthetic test result"}, "done")
            result = self.store.agent_run(run["actor"], 3, run["id"]).result
            self.assertEqual(result.receipt_ids, [run["id"]])
            self.assertFalse(result.model_used)
        self.assertEqual(seen, [7, 6, 8, 9, 10])
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_queue").fetchone()[0], 5)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM agent_runs").fetchone()[0], 5)

    def test_waiting_metadata_is_atomic_and_claimed_once_after_reopen(self):
        task = self.task()
        identifier = self.enqueue(task)["result"]["id"]
        for state in ("WAITING_QUOTA", "WAITING_PROVIDER", "BLOCKED_KEY_OR_MODEL", "WAITING_QUOTA"):
            self.store.wait_queued({"queue_state": state, "retry_at": None})
            self.store = Store(self.root)
            self.assertEqual(self.store.agent_run(7, 3, identifier).state, state)
            self.assertEqual(self.store.run(7, identifier)["result"]["queue_state"], state)
        self.assertEqual(self.store.claim_run()["id"], identifier)
        self.assertEqual(self.store.agent_run(7, 3, identifier).state, "RUNNING")
        self.assertIsNone(self.store.claim_run())

    def test_expired_before_claim_fails_without_execution_or_losing_next_intent(self):
        expired, live = self.task(expires_at=time.time() + 1), self.task(8)
        identifier = self.enqueue(expired)["result"]["id"]
        next_id = self.enqueue(live)["result"]["id"]
        with patch("gateway.store.time.time", return_value=expired.expires_at + 1):
            self.assertIsNone(self.store.claim_run())
            self.assertEqual(self.store.agent_run(7, 3, identifier).state, "FAILED")
            self.assertEqual(self.store.claim_run()["id"], next_id)
        self.assertEqual(self.store.run(7, identifier)["result"]["error"], "AGENT_TASK_EXPIRED")

    def test_unknown_started_work_preserves_full_receipt_and_ignores_late_finish(self):
        task = self.task()
        identifier = self.enqueue(task)["result"]["id"]
        self.store.claim_run()
        tools = [{"action": "comment", "arguments": {"id": 42}, "result": {"result": {"native_confirmed": True}}}]
        self.store.progress_run(7, identifier, {"tools": tools})
        with self.store.connect() as db:
            db.execute("UPDATE ai_queue SET lease_until=0 WHERE id=?", (identifier,))
        self.store = Store(self.root)
        self.assertIsNone(self.store.claim_run())
        failed = self.store.agent_run(7, 3, identifier)
        self.assertEqual(failed.state, "FAILED")
        self.assertEqual(failed.result.receipt_ids, [identifier])
        self.assertEqual(self.store.run(7, identifier)["result"]["tools"], tools)
        self.store.finish_run(7, identifier, {"status": "answered", "tools": []}, "done")
        self.assertEqual(self.store.agent_run(7, 3, identifier), failed)
        with self.assertRaisesRegex(ValueError, "TRANSITION_DENIED"):
            self.store.transition_agent_run(7, 3, identifier, "FAILED", "QUEUED")

    def test_queue_capacity_is_shared_and_rejection_leaves_no_partial_metadata(self):
        payload = {"prompt": "Synthetic legacy", "allow_routine_writes": False, "write_scope_ids": []}
        for _ in range(20):
            self.store.enqueue_run(7, payload)
        task = self.task()
        with self.assertRaisesRegex(ValueError, "AI_QUEUE_FULL"):
            self.enqueue(task, "capacity")
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM agent_runs").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM requests WHERE key='capacity'").fetchone()[0], 0)

    def test_stored_task_scope_consent_and_idempotency_are_not_inherited(self):
        task = self.task()
        for changes in ({"allow_routine_writes": True}, {"write_scope_ids": [42]}, {"prompt": "Different instruction"}, {"policy_sha256": "invalid"}):
            with self.assertRaises(PermissionError):
                self.enqueue(task, **changes)
        with self.assertRaises(PermissionError):
            self.store.enqueue_run(8, {"prompt": task.instruction, "allow_routine_writes": False, "write_scope_ids": []}, kind="agent", agent_task=task)
        self.enqueue(task, "bound")
        other = self.task()
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_KEY_REUSED"):
            self.enqueue(other, "bound")

    def test_proposals_end_in_review_and_interactive_can_use_idle_capacity(self):
        task = self.task()
        identifier = self.enqueue(task)["result"]["id"]
        legacy = self.store.enqueue_run(8, {"prompt": "Synthetic interactive", "allow_routine_writes": False, "write_scope_ids": []})["result"]["id"]
        self.assertEqual(self.store.claim_run()["id"], legacy)
        self.store.finish_run(8, legacy, {"tools": []}, "done")
        self.assertEqual(self.store.claim_run()["id"], identifier)
        self.store.finish_run(7, identifier, {"status": "proposed", "text": "Synthetic proposal requires human confirmation", "tools": []}, "done")
        self.assertEqual(self.store.agent_run(7, 3, identifier).state, "REVIEW")

    def test_bound_task_uses_existing_dispatcher_and_worker_without_extra_consent(self):
        task = self.task()
        policy = {"project": "synthetic", "limits": {"rpm": 13, "tpm": 225000, "rpd": 450}}
        identifier = self.enqueue(task, policy_sha256=digest(canonical(policy)))["result"]["id"]
        service = Service(self.store, {"gateway_mode": "native", "project_id": 3}, self.root / "workspaces")
        with patch.object(service.gemini, "settings", return_value=policy), patch("gateway.service.run_isolated", return_value={"status": "answered", "text": "Synthetic worker test", "tools": []}) as worker:
            service.start_dispatcher()
            thread = service._queue_thread
            if thread:
                thread.join(timeout=5)
            service.stop_dispatcher()
            worker.assert_called_once_with(self.store.root, service.workspace.root, 7, task.instruction, identifier, False, [])
        self.assertEqual(self.store.agent_run(7, 3, identifier).state, "COMPLETED")


if __name__ == "__main__":
    unittest.main()

import concurrent.futures
import threading
import unittest
from unittest.mock import patch

from gateway.agent_models import AgentResult
from gateway.store import Store
from tests import test_agent_store as fixture


class AgentStateTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.AgentStoreTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.store, self.run = self.fixture.store, self.fixture.run
        self.store.create_agent_task(7, 1, self.fixture.task)
        self.store.create_agent_run(7, 1, self.run)

    def transition(self, expected, state, result=None, actor=7, project=1):
        return self.store.transition_agent_run(actor, project, self.run.run_id, expected, state, result)

    def result(self, state, **changes):
        scope = {name: getattr(self.run, name) for name in ("run_id", "task_id", "actor_id", "project_id", "trace_id")}
        return AgentResult(**{**scope, "state": state, "summary": "Actual receipt retained; no execution approval", **changes})

    def test_waiting_then_running_review_survives_each_reopen(self):
        for expected, state in (("QUEUED", "WAITING_QUOTA"), ("WAITING_QUOTA", "QUEUED"),
                                ("QUEUED", "WAITING_PROVIDER"), ("WAITING_PROVIDER", "QUEUED"),
                                ("QUEUED", "BLOCKED_KEY_OR_MODEL"), ("BLOCKED_KEY_OR_MODEL", "QUEUED"),
                                ("QUEUED", "RUNNING"), ("RUNNING", "REVIEW")):
            result = self.result("REVIEW") if state == "REVIEW" else None
            self.transition(expected, state, result)
            self.store = Store(self.store.root)
            self.assertEqual(self.store.agent_run(7, 1, self.run.run_id).state, state)
        with self.assertRaisesRegex(ValueError, "TRANSITION_DENIED"):
            self.transition("REVIEW", "COMPLETED", self.result("COMPLETED"))
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM audit WHERE action='agent_run_state'").fetchone()[0], 8)

    def test_two_connections_can_claim_queued_run_only_once(self):
        barrier = threading.Barrier(2)
        def claim():
            store = Store(self.store.root)
            barrier.wait()
            try:
                store.transition_agent_run(7, 1, self.run.run_id, "QUEUED", "RUNNING")
                return "claimed"
            except ValueError:
                return "changed"
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            answers = list(pool.map(lambda _: claim(), range(2)))
        self.assertCountEqual(answers, ["claimed", "changed"])

    def test_interrupted_started_run_keeps_receipt_and_never_requeues(self):
        receipt = self.store.record(7, "comment", "42", "ok")
        self.transition("QUEUED", "RUNNING")
        self.store = Store(self.store.root)
        self.assertEqual(self.store.agent_run(7, 1, self.run.run_id).state, "RUNNING")
        with self.assertRaisesRegex(ValueError, "TRANSITION_DENIED"):
            self.transition("RUNNING", "WAITING_QUOTA")
        result = self.result("FAILED", receipt_ids=[receipt], error_code="OUTCOME_UNKNOWN")
        failed = self.transition("RUNNING", "FAILED", result)
        self.assertEqual(failed.result.receipt_ids, [receipt])
        self.store = Store(self.store.root)
        self.assertEqual(self.store.agent_run(7, 1, self.run.run_id), failed)
        with self.assertRaisesRegex(ValueError, "TRANSITION_DENIED"):
            self.transition("FAILED", "QUEUED")
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM audit WHERE action='comment'").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_queue").fetchone()[0], 0)

    def test_scope_state_and_terminal_validation_fail_atomically(self):
        with self.assertRaisesRegex(ValueError, "TRANSITION_DENIED"):
            self.transition({}, "RUNNING")
        for actor, project in ((8, 1), (7, 2)):
            with self.assertRaises(PermissionError):
                self.transition("QUEUED", "RUNNING", actor=actor, project=project)
        with self.assertRaisesRegex(ValueError, "RESULT_REQUIRED"):
            self.transition("QUEUED", "FAILED")
        with self.assertRaisesRegex(ValueError, "SCOPE_MISMATCH"):
            self.transition("QUEUED", "FAILED", self.result("FAILED", actor_id=8))
        with self.assertRaisesRegex(ValueError, "STATE_MISMATCH"):
            self.transition("QUEUED", "FAILED", self.result("COMPLETED"))
        self.assertEqual(self.store.agent_run(7, 1, self.run.run_id).state, "QUEUED")
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM audit").fetchone()[0], 0)

    def test_expired_task_cannot_start_and_completed_state_cannot_replay(self):
        with patch("gateway.store.time.time", return_value=self.fixture.task.expires_at + 1):
            with self.assertRaisesRegex(ValueError, "EXPIRED"):
                self.transition("QUEUED", "RUNNING")
        self.transition("QUEUED", "RUNNING")
        self.transition("RUNNING", "COMPLETED", self.result("COMPLETED"))
        with self.assertRaisesRegex(ValueError, "TRANSITION_DENIED"):
            self.transition("COMPLETED", "RUNNING")
        with self.assertRaisesRegex(ValueError, "STATE_CHANGED"):
            self.transition("QUEUED", "RUNNING")


if __name__ == "__main__":
    unittest.main()

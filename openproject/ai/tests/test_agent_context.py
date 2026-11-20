import time
import unittest
from unittest.mock import patch

from gateway.agent_models import AgentTask
from tests import test_local_queries as local

TASK = "00000000-0000-4000-8000-000000000001"
CONVERSATION = "00000000-0000-4000-8000-000000000002"
OTHER = "00000000-0000-4000-8000-000000000003"


class AgentContextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = local.LocalQueryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.service, self.store = self.fixture.service, self.fixture.store
        now = time.time()
        self.task = AgentTask(task_id=TASK, actor_id=7, project_id=3, conversation_id=CONVERSATION,
            agent="ba", instruction="Read task1", references=[{"work_package_id": 1, "lock_version": 1}],
            created_at=now, expires_at=now + 600)
        self.store.create_agent_task(7, 3, self.task)

    def start(self, prompt="Đọc task đó", actor=7, key="context", **changes):
        args = {"prompt": prompt, "context_task_id": TASK, "conversation_id": CONVERSATION, **changes}
        return self.service.execute_actor(actor, {"action": "start_ai_run", "arguments": args, "idempotency_key": key})

    def poll(self, identifier):
        return self.service.execute_actor(7, {"action": "get_ai_run", "arguments": {"id": identifier}})["result"]

    def test_two_followups_use_native_and_never_gemini_or_queue(self):
        with patch.object(self.service.gemini, "validate_prompt", side_effect=AssertionError("NO_PROVIDER_CONTEXT")), patch("gateway.service.run_isolated") as worker:
            first = self.start()
            self.assertEqual(first, self.start())
            for prompt in ("Xem công việc đó", "Đọc task đó"):
                receipt = self.start(prompt, key=prompt)
                result = self.poll(receipt["result"]["id"])["result"]
                self.assertFalse(result["model_used"])
                self.assertEqual(result["tools"][0]["arguments"], {"id": 1})
                self.assertEqual(result["context_reference"]["conversation_id"], CONVERSATION)
            worker.assert_not_called()
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_queue").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0], 0)

    def test_actor_project_and_conversation_cannot_reuse_reference(self):
        for args in ({"actor": 8}, {"conversation_id": OTHER}, {"context_task_id": {"id": TASK}}):
            with self.subTest(args=args), self.assertRaises((PermissionError, ValueError)):
                self.start(**args)
        with self.assertRaises(PermissionError):
            self.store.agent_task(7, 4, TASK)
        self.fixture.state.visible[7] = [2]
        with self.assertRaises(PermissionError):
            self.start()

    def test_expired_and_stale_references_deny_followup_and_cached_poll(self):
        receipt = self.start()["result"]["id"]
        with patch("gateway.service.time.time", return_value=self.task.expires_at + 1):
            with self.assertRaisesRegex(ValueError, "CONTEXT_EXPIRED"):
                self.start(key="expired")
            with self.assertRaisesRegex(ValueError, "CONTEXT_EXPIRED"):
                self.poll(receipt)
        self.fixture.state.rows[0]["lockVersion"] = 2
        with self.assertRaisesRegex(ValueError, "CONTEXT_STALE"):
            self.start(key="stale")
        with self.assertRaisesRegex(ValueError, "CONTEXT_STALE"):
            self.poll(receipt)
        self.assertEqual(self.store.run(7, receipt)["state"], "done")

    def test_old_context_never_grants_write_consent_or_calls_model(self):
        self.start()
        with patch.object(self.service.gemini, "validate_prompt", side_effect=AssertionError("NO_PROVIDER_CONTEXT")):
            for prompt, changes in (("Sửa task đó", {}), ("Đọc task đó", {"allow_routine_writes": True}),
                                    ("Đọc task đó", {"write_scope_ids": [1]}),
                                    ("Xoá task đó rồi đọc", {})):
                with self.subTest(prompt=prompt, changes=changes), self.assertRaises((ValueError, PermissionError)):
                    self.start(prompt, key=prompt, **changes)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 0)

    def test_ambiguous_empty_missing_and_revoked_context_fail_closed(self):
        for references in ([], [{"work_package_id": 1, "lock_version": 1}, {"work_package_id": 2, "lock_version": 1}]):
            with self.store.connect() as db:
                document = AgentTask.model_validate({**self.task.model_dump(), "references": references})
                db.execute("UPDATE agent_tasks SET document=? WHERE id=?", (document.model_dump_json(), TASK))
            with self.assertRaisesRegex(ValueError, "CONTEXT_AMBIGUOUS"):
                self.start()
        with self.assertRaisesRegex(ValueError, "CONTEXT_TASK_AND_CONVERSATION_REQUIRED"):
            self.service.execute_actor(7, {"action": "start_ai_run", "arguments": {"prompt": "Đọc task đó", "conversation_id": CONVERSATION}, "idempotency_key": "missing"})
        with self.assertRaisesRegex(ValueError, "CONTEXT_TASK_AND_CONVERSATION_REQUIRED"):
            self.service.execute_actor(7, {"action": "start_ai_run", "arguments": {"prompt": "Đọc task đó"}, "idempotency_key": "no-context"})
        with self.store.connect() as db:
            db.execute("UPDATE agent_tasks SET document=? WHERE id=?", (self.task.model_dump_json(), TASK))
        receipt = self.start()["result"]["id"]
        self.fixture.state.visible[7] = [2]
        with self.assertRaises(PermissionError):
            self.poll(receipt)


if __name__ == "__main__":
    unittest.main()

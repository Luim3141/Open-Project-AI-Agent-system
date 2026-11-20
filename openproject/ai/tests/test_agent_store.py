import json
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from gateway.agent_models import AgentTask, AgentRun
from gateway.store import Store


TASK = "00000000-0000-4000-8000-000000000001"
RUN = "00000000-0000-4000-8000-000000000002"
TRACE = "00000000-0000-4000-8000-000000000003"


class AgentStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = Store(self.root)
        now = time.time()
        self.task = AgentTask(task_id=TASK, actor_id=7, project_id=1, conversation_id=TRACE,
                              agent="ba", instruction="Read native AC", created_at=now, expires_at=now + 600)
        self.run = AgentRun(run_id=RUN, task_id=TASK, actor_id=7, project_id=1, trace_id=TRACE,
                            created_at=now, updated_at=now)

    def test_forward_migration_is_additive_idempotent_and_preserves_old_rows(self):
        legacy = self.root / "legacy"
        legacy.mkdir()
        with closing(sqlite3.connect(legacy / "gateway.sqlite")) as db:
            db.executescript("""CREATE TABLE audit(id TEXT PRIMARY KEY,at REAL,actor INTEGER,action TEXT,target TEXT,outcome TEXT,version TEXT);
                CREATE TABLE requests(actor INTEGER,key TEXT,hash TEXT,state TEXT,result TEXT,payload TEXT,PRIMARY KEY(actor,key));
                CREATE TABLE ai_runs(id TEXT PRIMARY KEY,actor INTEGER,state TEXT,result TEXT,created REAL);
                CREATE TABLE gemini_usage(project TEXT,at REAL,input_tokens INTEGER);
                INSERT INTO audit VALUES('old-audit',1,7,'comment','42','ok','3');
                INSERT INTO requests VALUES(7,'unknown-write','hash','pending',NULL,'{}');
                INSERT INTO ai_runs VALUES('old-run',7,'done','{"tools":[{"receipt":"retained"}]}',1);
                INSERT INTO gemini_usage VALUES('original-project',1,123);
            """)
            tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            columns = {name: [r[1] for r in db.execute("PRAGMA table_info(" + name + ")")] for name in tables}
            before = {name: db.execute("SELECT * FROM " + name).fetchall() for name in tables}
        for _ in range(2):
            migrated = Store(legacy)
            with migrated.connect() as db:
                self.assertEqual(before, {name: [tuple(r) for r in db.execute("SELECT " + ",".join(columns[name]) + " FROM " + name)] for name in tables})
                self.assertEqual(db.execute("PRAGMA quick_check").fetchone()[0], "ok")
                for name in ("agent_tasks", "agent_runs"):
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM " + name).fetchone()[0], 0)

    def test_task_and_queued_run_survive_reopen_and_are_scope_bound(self):
        self.store.create_agent_task(7, 1, self.task)
        self.store.create_agent_run(7, 1, self.run)
        reopened = Store(self.root)
        self.assertEqual(reopened.agent_task(7, 1, TASK), self.task)
        self.assertEqual(reopened.agent_run(7, 1, RUN), self.run)
        for actor, project in ((8, 1), (7, 2)):
            with self.assertRaises(PermissionError):
                reopened.agent_task(actor, project, TASK)
            with self.assertRaises(PermissionError):
                reopened.agent_run(actor, project, RUN)
            with self.assertRaises(PermissionError):
                reopened.create_agent_task(actor, project, self.task)

    def test_same_ids_replay_exactly_but_never_overwrite(self):
        for _ in range(2):
            self.assertEqual(self.store.create_agent_task(7, 1, self.task), self.task)
            self.assertEqual(self.store.create_agent_run(7, 1, self.run), self.run)
        with self.assertRaisesRegex(ValueError, "ID_REUSED"):
            self.store.create_agent_task(7, 1, self.task.model_copy(update={"instruction": "Replace"}))
        with self.assertRaisesRegex(ValueError, "ID_REUSED"):
            self.store.create_agent_run(7, 1, self.run.model_copy(update={"trace_id": TASK}))
        self.assertEqual(self.store.agent_task(7, 1, TASK), self.task)
        self.assertEqual(self.store.agent_run(7, 1, RUN), self.run)

    def test_orphan_expired_and_nonqueued_runs_fail_without_partial_insert(self):
        with self.assertRaises(PermissionError):
            self.store.create_agent_run(7, 1, self.run)
        self.store.create_agent_task(7, 1, self.task)
        with self.assertRaisesRegex(ValueError, "QUEUED"):
            self.store.create_agent_run(7, 1, self.run.model_copy(update={"state": "RUNNING"}))
        with patch("gateway.store.time.time", return_value=self.task.expires_at + 1):
            with self.assertRaisesRegex(ValueError, "EXPIRED"):
                self.store.create_agent_task(7, 1, self.task)
            with self.assertRaisesRegex(ValueError, "EXPIRED"):
                self.store.create_agent_run(7, 1, self.run)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM agent_runs").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM ai_queue").fetchone()[0], 0)

    def test_revalidates_serialized_models_and_stored_scope(self):
        forged = self.task.model_copy(update={"actor_id": "7"})
        with self.assertRaises(ValueError):
            self.store.create_agent_task(7, 1, forged)
        self.store.create_agent_task(7, 1, self.task)
        corrupted = self.task.model_dump()
        corrupted["actor_id"] = 8
        with self.store.connect() as db:
            db.execute("UPDATE agent_tasks SET document=? WHERE id=?", (json.dumps(corrupted), TASK))
        with self.assertRaisesRegex(ValueError, "SCOPE_MISMATCH"):
            self.store.agent_task(7, 1, TASK)
        with self.assertRaisesRegex(ValueError, "SCOPE_MISMATCH"):
            self.store.create_agent_run(7, 1, self.run)


if __name__ == "__main__":
    unittest.main()

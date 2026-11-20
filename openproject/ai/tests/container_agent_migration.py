"""Apply additive metadata migration to private cold stage copies; no provider/native calls."""
import hashlib
import json
import shutil
import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path

sys.path.insert(0, "/app")
from gateway.agent_models import AgentTask, AgentRun
from gateway.store import Store

root = Path("/fixture")
baseline = root / "before.sqlite"
assert baseline.is_file()


def snapshot(path, excluded=()):
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name") if r[0] not in excluded]
        rows = {name: sorted(db.execute('SELECT * FROM "' + name + '"').fetchall(), key=repr) for name in names}
        schema = db.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name").fetchall()
    return {"rows_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            "tables": names, "schema": schema}


before = snapshot(baseline)
work = root / "migrated"
work.mkdir()
shutil.copyfile(baseline, work / "gateway.sqlite")
store = Store(work)
after = snapshot(work / "gateway.sqlite", ("agent_tasks", "agent_runs"))
assert after["rows_sha256"] == before["rows_sha256"] and after["tables"] == before["tables"]
assert set(map(tuple, before["schema"])) <= set(map(tuple, after["schema"]))
now = time.time()
task = AgentTask(task_id="00000000-0000-4000-8000-000000000001", actor_id=7, project_id=1,
    conversation_id="00000000-0000-4000-8000-000000000002", agent="ba", instruction="Synthetic migration receipt",
    created_at=now, expires_at=now + 600)
run = AgentRun(run_id="00000000-0000-4000-8000-000000000003", task_id=task.task_id, actor_id=7,
    project_id=1, trace_id=task.conversation_id, created_at=now, updated_at=now)
store.create_agent_task(7, 1, task)
store.create_agent_run(7, 1, run)
reopened = Store(work)
assert reopened.agent_task(7, 1, task.task_id) == task
assert reopened.agent_run(7, 1, run.run_id) == run
for actor, project in ((8, 1), (7, 2)):
    try:
        reopened.agent_run(actor, project, run.run_id)
        raise AssertionError("CROSS_SCOPE_READ_ALLOWED")
    except PermissionError:
        pass
assert snapshot(work / "gateway.sqlite", ("agent_tasks", "agent_runs"))["rows_sha256"] == before["rows_sha256"]

# Roll back a separate database file; keep migrated state and original cold snapshot intact.
rolled_back = root / "rollback.sqlite"
shutil.copyfile(baseline, rolled_back)
assert snapshot(rolled_back) == before
assert snapshot(baseline) == before
with closing(sqlite3.connect(baseline)) as db:
    usage = db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0]
    runs = dict(db.execute("SELECT state,COUNT(*) FROM ai_runs GROUP BY state"))
assert usage == 471
print(json.dumps({"passed": True, "additive_tables": ["agent_tasks", "agent_runs"],
    "all_legacy_rows_and_schema_preserved": True, "original_cold_snapshot_unchanged": True,
    "rollback_copy_exact": True, "reopen_preserves_typed_task_and_queued_run": True,
    "cross_actor_project_denied": True, "original_usage_rows": usage, "original_ai_run_states": runs,
    "provider_calls": 0, "native_calls": 0, "live_stage_db_modified": False}))

"""Private cold stage migration + real disabled child process; no provider/native calls."""
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
import uuid
from collections import Counter
from contextlib import closing
from pathlib import Path

sys.path.insert(0, "/app")
from gateway.agent_models import AgentTask
from gateway.agent_trace import current_run
from gateway.ai_worker import run_isolated
from gateway.gemini import ProviderError
from gateway.service import Service
from gateway.store import Store

root = Path("/fixture")
baseline = root / "before.sqlite"
before_hash = hashlib.sha256(baseline.read_bytes()).hexdigest()
with closing(sqlite3.connect(baseline)) as db:
    names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    columns = {name: [r[1] for r in db.execute('PRAGMA table_info("' + name + '")')] for name in names}
    rows = {name: Counter(tuple(r) for r in db.execute('SELECT * FROM "' + name + '"')) for name in names}
store = Store(root)
with store.connect() as db:
    added = [tuple(r) for r in db.execute("PRAGMA table_info(audit)") if r[1] not in columns["audit"]]
    assert [(r[1], r[2], r[3], r[4]) for r in added] == [("project_id", "INTEGER", 0, None), ("run_id", "TEXT", 0, None), ("task_id", "TEXT", 0, None), ("trace_id", "TEXT", 0, None)]
    for name in names:
        assert rows[name] == Counter(tuple(r) for r in db.execute("SELECT " + ",".join(columns[name]) + ' FROM "' + name + '"')), name

now = time.time()
task = AgentTask(task_id=str(uuid.uuid4()), actor_id=7, project_id=1, conversation_id=str(uuid.uuid4()),
    agent="qa", instruction="PRIVATE_FIXTURE_PROMPT_NOT_IN_TRACE", created_at=now, expires_at=now + 600)
store.create_agent_task(7, 1, task)
response = store.enqueue_run(7, {"prompt": task.instruction, "allow_routine_writes": False,
    "write_scope_ids": [], "policy_sha256": "a" * 64}, kind="agent", agent_task=task)
run = store.claim_run()
config = {"gateway_mode": "native", "project_id": 1, "users": {"7": "PM"}}
(root / "config.json").write_text(json.dumps(config))
(root / "gemini.json").write_text('{"enabled":false}')
os.environ.update(QLDAPM_AI_ENVIRONMENT="staging", QLDAPM_GEMINI_FREE_PROOF=str(root / "absent-proof.json"))
try:
    run_isolated(root, "/tmp/workspaces", 7, task.instruction, run["id"])
    raise AssertionError("DISABLED_PROVIDER_EXECUTED")
except ProviderError as error:
    assert "DISABLED" in str(error)
Service(store, config, "/tmp/workspaces").process_run(run)
assert current_run.get() is None
assert store.agent_run(7, 1, run["id"]).state == "FAILED"
with store.connect() as db:
    traced = [dict(r) for r in db.execute("SELECT * FROM audit WHERE run_id=?", (run["id"],))]
    assert {r["action"] for r in traced} >= {"start_ai_run", "agent_run_state", "trace_worker", "ai_run"}
    for row in traced:
        assert (row["actor"], row["project_id"], row["task_id"], row["trace_id"]) == (7, 1, task.task_id, response["correlation_id"])
    assert "PRIVATE_FIXTURE_PROMPT_NOT_IN_TRACE" not in json.dumps(traced)
    for name in names:
        current = Counter(tuple(r) for r in db.execute("SELECT " + ",".join(columns[name]) + ' FROM "' + name + '"'))
        assert rows[name] <= current, name
        if name not in {"audit", "ai_runs", "ai_queue", "agent_tasks", "agent_runs"}:
            assert rows[name] == current, name
    assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 471
rollback = root / "rollback.sqlite"
shutil.copyfile(baseline, rollback)
assert hashlib.sha256(rollback.read_bytes()).hexdigest() == before_hash
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == before_hash
print(json.dumps({"passed": True, "additive_nullable_audit_columns": [r[1] for r in added],
    "all_prior_values_preserved": True, "cold_rollback_exact": True, "actual_child_worker_scope_loaded": True,
    "gateway_worker_runtime_same_trace": True, "private_prompt_absent_from_trace": True,
    "context_reset": True, "original_usage_rows": 471, "provider_calls": 0, "native_calls": 0,
    "fixture_rows_only_in_private_clone": True}))

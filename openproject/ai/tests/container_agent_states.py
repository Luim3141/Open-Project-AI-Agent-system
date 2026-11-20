"""Two-phase metadata restart test on a private cold staging clone, no business/provider calls."""
import json
import sqlite3
import sys
import time
from collections import Counter
from contextlib import closing
from pathlib import Path

sys.path.insert(0, "/app")
from gateway.agent_models import AgentTask, AgentRun, AgentResult
from gateway.store import Store

root = Path("/fixture")
store = Store(root)
task_id = "00000000-0000-4000-8000-000000000001"
run_id = "00000000-0000-4000-8000-000000000002"
trace_id = "00000000-0000-4000-8000-000000000003"
if sys.argv[1] == "before":
    now = time.time()
    task = AgentTask(task_id=task_id, actor_id=7, project_id=1, conversation_id=trace_id,
        agent="qa", instruction="Synthetic restart metadata fixture", created_at=now, expires_at=now + 600)
    run = AgentRun(run_id=run_id, task_id=task_id, actor_id=7, project_id=1, trace_id=trace_id,
        created_at=now, updated_at=now)
    store.create_agent_task(7, 1, task)
    store.create_agent_run(7, 1, run)
    store.transition_agent_run(7, 1, run_id, "QUEUED", "WAITING_QUOTA")
    store.transition_agent_run(7, 1, run_id, "WAITING_QUOTA", "QUEUED")
    store.transition_agent_run(7, 1, run_id, "QUEUED", "RUNNING")
    receipt = store.record(7, "synthetic_read_fixture", task_id, "ok")
    (root / "fixture-receipt.json").write_text(json.dumps({"receipt": receipt}))
    print(json.dumps({"prepared": True, "state": "RUNNING"}))
else:
    assert sys.argv[1] == "after"
    assert store.agent_run(7, 1, run_id).state == "RUNNING"
    receipt = json.loads((root / "fixture-receipt.json").read_text())["receipt"]
    result = AgentResult(run_id=run_id, task_id=task_id, actor_id=7, project_id=1, trace_id=trace_id,
        state="FAILED", summary="Interrupted fixture; retain receipt, no automatic replay", receipt_ids=[receipt], error_code="OUTCOME_UNKNOWN")
    store.transition_agent_run(7, 1, run_id, "RUNNING", "FAILED", result)
    try:
        store.transition_agent_run(7, 1, run_id, "FAILED", "QUEUED")
        raise AssertionError("TERMINAL_REPLAY_ALLOWED")
    except ValueError:
        pass
    assert Store(root).agent_run(7, 1, run_id).result.receipt_ids == [receipt]
    with closing(sqlite3.connect(root / "before.sqlite")) as original, store.connect() as current:
        for (name,) in original.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            old = Counter(tuple(r) for r in original.execute('SELECT * FROM "' + name + '"'))
            new = Counter(tuple(r) for r in current.execute('SELECT * FROM "' + name + '"'))
            assert old <= new, name
            if name not in {"audit", "agent_tasks", "agent_runs"}:
                assert old == new, name
        assert current.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 471
        assert current.execute("SELECT COUNT(*) FROM ai_queue WHERE state IN ('queued','executing')").fetchone()[0] == 0
    print(json.dumps({"passed": True, "running_state_survived_container_restart": True,
        "interrupted_terminal_state": "FAILED", "synthetic_receipt_retained": True, "requeue_denied": True,
        "all_prior_rows_preserved": True, "usage_rows": 471, "provider_calls": 0, "native_calls": 0,
        "new_fixture_rows_in_private_clone_only": True, "executor_binding_tested": False}))

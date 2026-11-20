"""Private cold-clone queue restart; deterministic fixture completions, never model/native replies."""
import json
import sqlite3
import sys
import time
import uuid
from collections import Counter
from contextlib import closing
from pathlib import Path

sys.path.insert(0, "/app")
from gateway.agent_models import AgentTask
from gateway.store import Store

root = Path("/fixture")
store = Store(root)
if sys.argv[1] == "before":
    records = []
    for actor in (6, 7, 8, 9, 10):
        now = time.time()
        task = AgentTask(task_id=str(uuid.uuid4()), actor_id=actor, project_id=1,
            conversation_id=str(uuid.uuid4()), agent="qa", instruction="Synthetic queue restart fixture",
            created_at=now, expires_at=now + 600)
        store.create_agent_task(actor, 1, task)
        response = store.enqueue_run(actor, {"prompt": task.instruction, "allow_routine_writes": False,
            "write_scope_ids": [], "policy_sha256": "a" * 64}, kind="agent", agent_task=task)
        records.append({"actor": actor, "id": response["result"]["id"]})
    running = store.claim_run()
    assert running["actor"] == records[0]["actor"]
    store.progress_run(running["actor"], running["id"], {"tools": [{"action": "identity", "arguments": {},
        "result": {"result": {"source": "synthetic-restart-fixture"}}}]})
    store.wait_queued({"queue_state": "WAITING_QUOTA", "retry_at": None})
    (root / "fixture-runs.json").write_text(json.dumps(records))
    print(json.dumps({"prepared": True, "bound_tasks": 5, "running": 1, "waiting_quota": 4}))
else:
    assert sys.argv[1] == "after"
    records = json.loads((root / "fixture-runs.json").read_text())
    for index, record in enumerate(records):
        assert store.agent_run(record["actor"], 1, record["id"]).state == ("RUNNING" if index == 0 else "WAITING_QUOTA")
    interrupted = records[0]
    with store.connect() as db:
        db.execute("UPDATE ai_queue SET lease_until=0 WHERE id=?", (interrupted["id"],))
    completed = []
    while run := store.claim_run():
        assert run["id"] != interrupted["id"]
        assert store.claim_run() is None
        assert store.agent_run(run["actor"], 1, run["id"]).state == "RUNNING"
        store.finish_run(run["actor"], run["id"], {"status": "answered", "tools": [],
            "text": "Deterministic queue fixture completion; no Gemini or native execution"}, "done")
        assert store.agent_run(run["actor"], 1, run["id"]).state == "COMPLETED"
        completed.append(run["actor"])
    assert sorted(completed) == [7, 8, 9, 10] and len(set(completed)) == 4
    failed = store.agent_run(interrupted["actor"], 1, interrupted["id"])
    assert failed.state == "FAILED" and failed.result.receipt_ids == [interrupted["id"]]
    assert store.run(interrupted["actor"], interrupted["id"])["result"]["tools"][0]["result"]["result"]["source"] == "synthetic-restart-fixture"
    store.finish_run(interrupted["actor"], interrupted["id"], {"tools": []}, "done")
    assert store.agent_run(interrupted["actor"], 1, interrupted["id"]) == failed
    with closing(sqlite3.connect(root / "before.sqlite")) as original, store.connect() as current:
        for (name,) in original.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            old = Counter(tuple(r) for r in original.execute('SELECT * FROM "' + name + '"'))
            new = Counter(tuple(r) for r in current.execute('SELECT * FROM "' + name + '"'))
            assert old <= new, name
            if name not in {"audit", "ai_runs", "ai_queue", "agent_tasks", "agent_runs"}:
                assert old == new, name
        assert current.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 471
    print(json.dumps({"passed": True, "bound_tasks_survived_restart": 5, "resumed_waiting_once_each": 4,
        "interrupted_run_not_replayed": True, "late_finish_ignored": True, "full_underlying_receipt_retained": True,
        "all_prior_rows_preserved": True, "one_queue_slot": True, "original_usage_rows": 471,
        "provider_calls": 0, "native_calls": 0, "synthetic_completions_only_in_private_test_clone": True}))

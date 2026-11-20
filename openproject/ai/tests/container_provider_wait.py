"""Two-start Free-quota waiting acceptance; injected reset, synthetic workers, network none."""
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app")
from gateway.service import Service
from gateway.store import Store

root = Path("/queue-fixture")
store = Store(root)
policy = {"project": "fixture", "limits": {"rpm": 13, "tpm": 225000, "rpd": 450}}
marker = root / "waiting.json"
service = Service(store, {"gateway_mode": "native"}, root / "workspaces")
if not marker.exists():
    ids = []
    for actor in (7, 6, 8, 9, 10):
        run = store.enqueue_run(actor, {"prompt": "Synthetic free wait", "allow_routine_writes": False, "write_scope_ids": []})
        ids.append([actor, run["result"]["id"]])
    with store.connect() as db:
        db.executemany("INSERT INTO gemini_usage VALUES('fixture',?,1)", [(time.time(),)] * 450)
    with patch.object(service.gemini, "settings", return_value=policy), patch("gateway.service.run_isolated") as worker:
        service.start_dispatcher()
        deadline = time.monotonic() + 20
        while any(store.run(actor, identifier)["result"]["queue_state"] != "WAITING_QUOTA" for actor, identifier in ids):
            assert time.monotonic() < deadline
            time.sleep(0.02)
        service.stop_dispatcher()
        worker.assert_not_called()
    marker.write_text(json.dumps(ids))
    print(json.dumps({"waiting_users": 5, "usage_rows": 450, "worker_calls": 0, "synthetic_only": True}))
else:
    ids = json.loads(marker.read_text())
    assert all(store.run(actor, identifier)["result"]["queue_state"] == "WAITING_QUOTA" for actor, identifier in ids)
    assert store.provider_wait(policy)["queue_state"] == "WAITING_QUOTA"
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 450
        # Inject reset eligibility without deleting the old private ledger or waiting for a physical midnight.
        db.execute("UPDATE gemini_usage SET at=0")
    calls = []
    def worker(*args):
        store.reserve_gemini("fixture", policy["limits"], 100)
        calls.append(args[2])
        return {"text": "synthetic", "tools": []}
    with patch.object(service.gemini, "settings", return_value=policy), patch("gateway.service.run_isolated", side_effect=worker):
        service.start_dispatcher()
        with service._queue_guard:
            thread = service._queue_thread
        if thread:
            thread.join(timeout=30)
            assert not thread.is_alive()
    assert calls == [7, 6, 8, 9, 10], calls
    assert all(store.run(actor, identifier)["state"] == "done" for actor, identifier in ids)
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 455
        assert db.execute("SELECT COUNT(*) FROM gemini_usage WHERE at=0").fetchone()[0] == 450
    print(json.dumps({"passed": True, "pending_survived_same_container_restart": 5,
                      "all_waiting_quota_before_reset": True, "reset_injected": True,
                      "resumed_order": calls, "old_ledger_rows_retained": 450, "new_fixture_reservations": 5,
                      "provider_calls": 0, "network": "none", "physical_midnight_tested": False}))

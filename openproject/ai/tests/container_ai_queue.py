"""Two-start acceptance in a disposable network-none container, synthetic state only."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app")
from gateway.service import Service
from gateway.store import Store


root = Path("/queue-fixture")
store = Store(root)
marker = root / "seeded.json"
actors = (7, 6, 8, 9, 10)
payload = {"prompt": "Synthetic public queue acceptance", "allow_routine_writes": False, "write_scope_ids": []}
if not marker.exists():
    ids = []
    for actor in actors:
        for _ in range(20):
            ids.append(store.enqueue_run(actor, payload)["result"]["id"])
    # Simulate an interrupted claimed run with a receipt; expiry is deliberately injected, not a timed-deadline test.
    claimed = store.claim_run()
    store.progress_run(claimed["actor"], claimed["id"], {"tools": [], "receipt": "synthetic-interruption"})
    with store.connect() as db:
        db.execute("UPDATE ai_queue SET lease_until=0 WHERE id=?", (claimed["id"],))
        db.execute("INSERT INTO gemini_usage VALUES('fixture-project',1,10)")
    marker.write_text(json.dumps({"ids": ids, "interrupted": claimed["id"]}))
    print(json.dumps({"seeded": 100, "executing_interruption_simulated": True, "synthetic_only": True}))
else:
    previous = json.loads(marker.read_text())
    service = Service(store, {"gateway_mode": "native"}, root / "workspaces")
    order = []
    active = 0
    def worker(*args):
        global active
        active += 1
        assert active == 1
        order.append(args[2])
        assert args[4] != previous["interrupted"]
        assert args[5] is False and args[6] == []
        active -= 1
        return {"text": "Synthetic receipt", "tools": []}
    with patch.object(service.gemini, "settings", return_value={}), patch("gateway.service.run_isolated", side_effect=worker):
        service.start_dispatcher()
        with service._queue_guard:
            thread = service._queue_thread
        if thread:
            thread.join(timeout=30)
            assert not thread.is_alive()
    assert order == list(actors[1:]) + list(actors) * 19, order
    assert store.run(7, previous["interrupted"])["result"]["receipt"] == "synthetic-interruption"
    with store.connect() as db:
        states = dict(db.execute("SELECT state,COUNT(*) FROM ai_runs GROUP BY state"))
        assert states == {"done": 99, "failed_or_unknown": 1}, states
        assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 1
    print(json.dumps({"passed": True, "states": states, "same_container_second_start": True,
                      "pending_resumed": 99, "interrupted_never_replayed": True, "fair_actor_order": True,
                      "single_worker": True, "ledger_preserved": True, "network": "none", "provider_calls": 0,
                      "fixture_key": "none", "physical_five_clients_tested": False}))

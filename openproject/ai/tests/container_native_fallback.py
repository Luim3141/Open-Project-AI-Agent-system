"""Private cold clone + real native reads; quota/faults injected only in clone/process."""
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app")
from starlette.testclient import TestClient
from gateway.app import create_app
from gateway.gemini import Gemini
from gateway.native import Native, NativeError
from gateway.service import Service
from gateway.store import Store, canonical

root = Path("/fixture")
config = json.loads((root / "config.json").read_text())
config["hosts"] = ["testserver"]
(root / "config.json").write_text(canonical(config))
store = Store(root)
policy = Gemini(root).settings()
key_before = (root / "gemini.key").read_bytes()
with store.connect() as db:
    original_usage = db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0]
    db.executemany("INSERT INTO gemini_usage VALUES(?,?,1)", [(policy["project"], time.time())] * policy["limits"]["rpd"])
tokens = {int(actor): store.issue_token(int(actor), role, store.credential(int(actor))) for actor, role in config["users"].items()}
service = Service(store, config, "/tmp/workspaces")
records, first_native, pending = [], None, []
native_call = Native.call
def read_only_native(native, path, method="GET", payload=None):
    assert method == "GET", "NO_NATIVE_BUSINESS_MUTATION_IN_ACCEPTANCE"
    return native_call(native, path, method, payload)
with patch.object(Gemini, "sdk_client", side_effect=AssertionError("NO_GOOGLE_CALL_IN_FALLBACK_ACCEPTANCE")) as sdk, patch.object(Native, "call", read_only_native), TestClient(create_app(root, service)) as client:
    def command(actor, action, args=None):
        response = client.post("/api/v1/commands", headers={"Authorization": "Bearer " + tokens[actor]},
                               json={"action": action, "arguments": args or {}})
        assert response.status_code == 200, (action, response.status_code)
        return response.json()["result"]
    for actor in sorted(tokens):
        headers = {"Authorization": "Bearer " + tokens[actor]}
        status = command(actor, "get_assistant_status")
        assert status["gemini"]["state"] == "WAITING_QUOTA"
        assert not status["native_reporting"]["model_used"]
        queued = client.post("/api/v1/ai-runs", headers={**headers, "Idempotency-Key": f"clone-pending-{actor}"},
                             json={"prompt": "Phân tích rủi ro dự án bằng các bằng chứng hiện có"})
        assert queued.status_code == 200
        identifier = queued.json()["result"]["id"]
        result = client.get("/api/v1/ai-runs/" + identifier, headers=headers).json()["result"]
        assert result["state"] == "running" and result["result"]["queue_state"] == "WAITING_QUOTA"
        pending.append(identifier)
        native = client.post("/api/v1/ai-runs", headers={**headers, "Idempotency-Key": f"clone-native-{actor}"}, json={"prompt": "Đếm công việc"})
        assert native.status_code == 200
        receipt = native.json()["result"]
        assert receipt["state"] == "done" and receipt["source"] == "native" and receipt["model_used"] is False
        result = command(actor, "get_ai_run", {"id": receipt["id"]})["result"]
        assert result["source"] == "native" and not result["model_used"] and not result.get("stale")
        records.append({"actor": actor, "role": config["users"][str(actor)], "state": "WAITING_QUOTA",
                        "native_count": result["tools"][0]["result"]["result"]["count"], "pending_kept": True})
        if actor == 7:
            first_native = receipt["id"]
    store.block_gemini(policy["project"], "GEMINI_UPSTREAM_REJECTED; HTTP=503", 60)
    assert command(7, "get_assistant_status")["gemini"]["state"] == "OFFLINE"
    store.block_gemini(policy["project"], "GEMINI_AUTH_401")
    assert command(7, "get_assistant_status")["gemini"]["state"] == "BLOCKED_KEY_OR_MODEL"
    # Inject staleness in clone receipt only; real native data is unchanged.
    document = store.run(7, first_native)["result"]
    document["source_fingerprint"] = "injected-stale-fixture"
    with store.connect() as db:
        db.execute("UPDATE ai_runs SET result=? WHERE id=?", (canonical(document), first_native))
    assert command(7, "get_ai_run", {"id": first_native})["result"]["status"] == "stale"
    with patch.object(Native, "packages", side_effect=NativeError(503, "OPENPROJECT_UNAVAILABLE")):
        offline = command(7, "get_ai_run", {"id": first_native})["result"]
        assert offline["status"] == "offline" and offline["tools"] == []
    with patch.object(Native, "packages", side_effect=NativeError(403, "OPENPROJECT_403")):
        denied = client.get("/api/v1/ai-runs/" + first_native, headers={"Authorization": "Bearer " + tokens[7]})
        assert denied.status_code == 403
    assert client.get("/health").status_code == 200
    sdk.assert_not_called()
with store.connect() as db:
    assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == original_usage + policy["limits"]["rpd"]
    assert db.execute("SELECT COUNT(*) FROM ai_queue WHERE state='queued'").fetchone()[0] == 5
assert (root / "gemini.key").read_bytes() == key_before
print(json.dumps({"passed": True, "users": records, "pending_users": 5, "provider_calls": 0,
                  "real_native_reads": True, "model_results_fabricated": False, "native_methods_allowed": ["GET"],
                  "states_verified": ["WAITING_QUOTA", "OFFLINE", "STALE", "BLOCKED_KEY_OR_MODEL"],
                  "access_revocation_denied": True, "liveness_healthy": True, "original_clone_usage_rows": original_usage,
                  "quota_and_faults_injected_in_private_clone_only": True, "key_unchanged": True,
                  "real_project_ledger_modified": False, "physical_five_browsers_tested": False}))

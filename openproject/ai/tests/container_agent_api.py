"""Five actual native identities; read-only REST/MCP metadata on a private cold clone."""
import json
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app")
from starlette.testclient import TestClient
from gateway.agent_models import AgentTask
from gateway.app import create_app
from gateway.gemini import Gemini
from gateway.native import Native
from gateway.service import Service
from gateway.store import Store, canonical

root = Path("/fixture")
config = json.loads((root / "config.json").read_text())
config["hosts"] = ["testserver"]
(root / "config.json").write_text(canonical(config))
store = Store(root)
tokens = {int(actor): store.issue_token(int(actor), role, store.credential(int(actor))) for actor, role in config["users"].items()}
runs = {}
for actor in sorted(tokens):
    now = time.time()
    task = AgentTask(task_id=str(uuid.uuid4()), actor_id=actor, project_id=config["project_id"],
        conversation_id=str(uuid.uuid4()), agent="qa", instruction="PRIVATE_API_FIXTURE_INSTRUCTION",
        created_at=now, expires_at=now + 600)
    store.create_agent_task(actor, config["project_id"], task)
    runs[actor] = store.enqueue_run(actor, {"prompt": task.instruction, "allow_routine_writes": False,
        "write_scope_ids": [], "policy_sha256": "a" * 64}, kind="agent", agent_task=task)["result"]["id"]
while run := store.claim_run():
    store.finish_run(run["actor"], run["id"], {"status": "answered", "text": "PRIVATE_API_FIXTURE_RESULT_NOT_MODEL_OUTPUT", "tools": []}, "done")
service = Service(store, config, "/tmp/workspaces")
original_call = Native.call


def native_read_only(native, path, method="GET", payload=None):
    assert method == "GET", "NO_NATIVE_MUTATION_IN_API_ACCEPTANCE"
    return original_call(native, path, method, payload)


records = []
with patch.object(Gemini, "sdk_client", side_effect=AssertionError("NO_GOOGLE_IN_API_ACCEPTANCE")) as sdk, patch.object(Native, "call", native_read_only), TestClient(create_app(root, service)) as client:
    assert client.get("/api/v1/agent-runs").status_code == 401
    for actor, role in sorted((int(a), r) for a, r in config["users"].items()):
        headers = {"Authorization": "Bearer " + tokens[actor]}
        identifier = runs[actor]
        page = client.get("/api/v1/agent-runs?limit=1", headers=headers)
        assert page.status_code == 200
        data = page.json()["result"]
        assert data["total"] == 1 and data["items"][0]["run_id"] == identifier
        progress = client.get("/api/v1/agent-runs/" + identifier, headers=headers).json()["result"]
        assert progress["actor_id"] == actor and progress["project_id"] == config["project_id"]
        assert progress["receipt_id"] == identifier and progress["can_replay"] is False
        assert "PRIVATE_API_FIXTURE" not in json.dumps(progress)
        trace = client.get("/api/v1/agent-runs/" + identifier + "/trace?limit=1", headers=headers).json()["result"]
        assert trace["next_offset"] == 1 and trace["items"][0]["run_id"] == identifier
        assert "PRIVATE_API_FIXTURE" not in json.dumps(trace)
        other = next(value for owner, value in runs.items() if owner != actor)
        assert client.get("/api/v1/agent-runs/" + other, headers=headers).status_code == 403
        assert client.get("/api/v1/agent-runs/" + other + "/trace", headers=headers).status_code == 403
        assert client.post("/api/v1/agent-runs/" + identifier + "/retry", headers=headers, json={}).status_code in {404, 405}
        mcp_headers = {**headers, "Accept": "application/json, text/event-stream"}
        reply = client.post("/mcp", headers=mcp_headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "get_agent_run", "arguments": {"arguments": {"id": identifier}}}})
        assert reply.status_code == 200 and not reply.json()["result"].get("isError", False)
        assert "PRIVATE_API_FIXTURE" not in reply.text
        records.append({"actor": actor, "role": role, "rest_and_mcp_own_progress": True,
            "paged_trace": True, "cross_actor_denied": True, "content_excluded": True, "no_retry_endpoint": True})
    sdk.assert_not_called()
with store.connect() as db:
    assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 471
    assert db.execute("SELECT COUNT(*) FROM ai_queue WHERE state IN ('queued','executing')").fetchone()[0] == 0
assert not (root / "gemini.key").exists()
print(json.dumps({"passed": True, "users": records, "provider_calls": 0, "native_methods_allowed": ["GET"],
    "usage_history_rows": 471, "fixture_task_results_only_in_private_clone": True,
    "fixture_results_are_not_model_output": True, "physical_five_browsers_tested": False}))

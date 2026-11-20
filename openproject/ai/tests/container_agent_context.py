"""Five actual native roles on a private clone; context faults never mutate OpenProject."""
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
with store.connect() as db:
    usage = db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0]
tokens = {int(actor): store.issue_token(int(actor), role, store.credential(int(actor))) for actor, role in config["users"].items()}
service = Service(store, config, "/tmp/workspaces")
native_call = Native.call


def only_read(native, path, method="GET", payload=None):
    assert method == "GET", "NO_NATIVE_MUTATIONS_IN_CONTEXT_ACCEPTANCE"
    return native_call(native, path, method, payload)


records, first_task, first_actor = [], None, None
with patch.object(Gemini, "sdk_client", side_effect=AssertionError("NO_GOOGLE_IN_CONTEXT_ACCEPTANCE")) as sdk, patch.object(Native, "call", only_read), TestClient(create_app(root, service)) as client:
    def start(actor, task, prompt="Đọc task đó", **changes):
        response = client.post("/api/v1/ai-runs", headers={"Authorization": "Bearer " + tokens[actor], "Idempotency-Key": str(uuid.uuid4())},
            json={"prompt": prompt, "context_task_id": task.task_id, "conversation_id": task.conversation_id, **changes})
        return response

    for actor, role in sorted((int(a), r) for a, r in config["users"].items()):
        native = Native(config["openproject_url"], store.credential(actor), config["project_id"])
        item = native.packages()[0]
        now = time.time()
        task = AgentTask(task_id=str(uuid.uuid4()), actor_id=actor, project_id=config["project_id"],
            conversation_id=str(uuid.uuid4()), agent="ba", instruction="Synthetic native context acceptance",
            references=[{"work_package_id": item["id"], "lock_version": item["lockVersion"]}], created_at=now, expires_at=now + 600)
        store.create_agent_task(actor, config["project_id"], task)
        for prompt in ("Đọc task đó", "Xem công việc đó"):
            response = start(actor, task, prompt)
            assert response.status_code == 200, response.status_code
            identifier = response.json()["result"]["id"]
            response = client.get("/api/v1/ai-runs/" + identifier, headers={"Authorization": "Bearer " + tokens[actor]})
            assert response.status_code == 200
            result = response.json()["result"]["result"]
            assert result["source"] == "native" and result["model_used"] is False
            assert result["tools"][0]["arguments"]["id"] == item["id"]
        assert start(actor, task, allow_routine_writes=True).status_code == 403
        records.append({"actor": actor, "role": role, "two_read_followups": True, "native_reference_fresh": True, "write_replay_denied": True})
        if first_task is None:
            first_task, first_actor = task, actor
    other = next(actor for actor in tokens if actor != first_actor)
    assert start(other, first_task).status_code == 403
    assert start(first_actor, first_task, conversation_id=str(uuid.uuid4())).status_code == 403
    stale = first_task.model_dump()
    stale["references"][0]["lock_version"] += 1
    with store.connect() as db:
        db.execute("UPDATE agent_tasks SET document=? WHERE id=?", (canonical(stale), first_task.task_id))
    assert start(first_actor, first_task).status_code in {409, 422}
    expired = first_task.model_dump()
    expired.update(created_at=time.time() - 600, expires_at=time.time() - 1)
    with store.connect() as db:
        db.execute("UPDATE agent_tasks SET document=? WHERE id=?", (canonical(expired), first_task.task_id))
    assert start(first_actor, first_task).status_code in {409, 422}
    sdk.assert_not_called()
with store.connect() as db:
    assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == usage == 471
    assert db.execute("SELECT COUNT(*) FROM ai_queue WHERE state IN ('queued','executing')").fetchone()[0] == 0
assert not (root / "gemini.key").exists(), "CLONE_NATIVE_CONTEXT_NEEDS_NO_PROVIDER_KEY"
print(json.dumps({"passed": True, "users": records, "provider_calls": 0, "native_methods_allowed": ["GET"],
    "cross_actor_conversation_denied": True, "stale_expired_reference_denied": True, "original_usage_rows": usage,
    "faults_injected_in_private_clone_only": True, "new_read_receipts_in_clone_only": 10,
    "provider_key_required_for_native_context": False, "physical_five_browsers_tested": False}))

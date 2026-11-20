"""Signed fixture consent in private clone + temp sandbox; actual native reads only, no human login claim."""
import hashlib
import hmac
import json
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app")
from starlette.testclient import TestClient
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
service = Service(store, config, "/tmp/bridge-workspaces")
key = (root / "ui.key").read_bytes()
original_native = Native.call


def read_native(native, path, method="GET", payload=None):
    assert method == "GET", "NO_NATIVE_BUSINESS_MUTATION_IN_BRIDGE_ACCEPTANCE"
    return original_native(native, path, method, payload)


with patch.object(Gemini, "sdk_client", side_effect=AssertionError("NO_GOOGLE_IN_BRIDGE_ACCEPTANCE")) as sdk, patch.object(Native, "call", read_native), TestClient(create_app(root, service)) as client:
    def packet(actor, operation, command, **changes):
        document = {"actor": actor, "project": config["project_id"], "audience": "qldapm-ai-ui", "at": time.time(),
            "nonce": uuid.uuid4().hex, "operation": operation, "command": command, **changes}
        body = canonical(document).encode()
        return body, {"X-Qldapm-Signature": hmac.new(key, body, hashlib.sha256).hexdigest()}

    def signed(actor, operation, command, **changes):
        body, headers = packet(actor, operation, command, **changes)
        return client.post("/internal/ui", content=body, headers=headers)

    records = []
    for actor, role in sorted((int(a), r) for a, r in config["users"].items()):
        read = signed(actor, "command", {"action": "list_agent_runs", "arguments": {"limit": 1}})
        assert read.status_code == 200 and read.json()["result"]["total"] == 0
        command = {"action": "write_code", "arguments": {"path": "app/consent.txt", "content": "synthetic sandbox fixture", "expected_hash": "NEW"}, "idempotency_key": f"bridge-fixture-{actor}"}
        response = signed(actor, "command", command)
        if role != "PM":
            assert response.status_code == 403
        else:
            assert response.status_code == 200
            proposal = response.json()["result"]
            assert proposal["human_confirmation_required"] is True
        records.append({"actor": actor, "role": role, "signed_own_metadata": True, "pm_only_sandbox_proposal": True})
    target = service.workspace.path(7, "app/consent.txt")
    assert not target.exists()
    assert signed(8, "confirm", {"id": proposal["id"], "hash": proposal["hash"]}).status_code == 403
    assert signed(7, "confirm", {"id": proposal["id"], "hash": "0" * 64}).status_code == 409
    assert not target.exists()
    headers = {"Authorization": "Bearer " + tokens[7]}
    assert client.post("/api/v1/commands", headers=headers, json={"action": "confirm", "arguments": {"id": proposal["id"], "hash": proposal["hash"]}}).status_code == 422
    expired = signed(7, "command", {"action": "identity", "arguments": {}}, at=time.time() - 61)
    assert expired.status_code == 403
    body, signature = packet(7, "command", {"action": "identity", "arguments": {}})
    assert client.post("/internal/ui", content=body, headers=signature).status_code == 200
    assert client.post("/internal/ui", content=body, headers=signature).status_code == 403
    body, signature = packet(7, "command", {"action": "identity", "arguments": {}})
    assert client.post("/internal/ui", content=body + b" ", headers=signature).status_code == 403
    assert signed(7, "command", {"action": "identity", "arguments": {}}, project=config["project_id"] + 1).status_code == 403
    confirmed = signed(7, "confirm", {"id": proposal["id"], "hash": proposal["hash"]})
    assert confirmed.status_code == 200 and target.read_text() == "synthetic sandbox fixture"
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    assert confirmed.json()["result"]["sha256"] == checksum
    assert store.proposal(7, proposal["id"])["state"] == "done"
    assert signed(7, "confirm", {"id": proposal["id"], "hash": proposal["hash"]}).status_code == 409
    assert hashlib.sha256(target.read_bytes()).hexdigest() == checksum

    def preview(path):
        response = signed(7, "command", {"action": "write_code", "arguments": {"path": path,
            "content": "new fixture", "expected_hash": "NEW"}, "idempotency_key": str(uuid.uuid4())})
        assert response.status_code == 200
        return response.json()["result"]
    stale = preview("app/stale.txt")
    stale_file = service.workspace.path(7, "app/stale.txt")
    stale_file.write_text("intervening private fixture edit")
    assert signed(7, "confirm", {"id": stale["id"], "hash": stale["hash"]}).status_code == 409
    assert stale_file.read_text() == "intervening private fixture edit"
    expired = preview("app/expired.txt")
    with store.connect() as db:
        db.execute("UPDATE proposals SET expires=? WHERE id=?", (time.time() - 1, expired["id"]))
    assert signed(7, "confirm", {"id": expired["id"], "hash": expired["hash"]}).status_code == 409
    assert not service.workspace.path(7, "app/expired.txt").exists()
    sdk.assert_not_called()
with store.connect() as db:
    assert db.execute("SELECT COUNT(*) FROM gemini_usage").fetchone()[0] == 471
assert not (root / "gemini.key").exists()
print(json.dumps({"passed": True, "users": records, "signature_nonce_expiry_project_checks": True,
    "actor_hash_bound_consent": True, "preview_did_not_write": True, "bearer_cannot_confirm": True,
    "sandbox_fixture_confirmation_once_with_receipt": True, "stale_expired_proposal_denied": True,
    "native_business_mutations": 0, "native_methods_allowed": ["GET"], "provider_calls": 0,
    "original_usage_rows": 471, "private_clone_and_tmp_sandbox_only": True,
    "real_human_approval_or_browser_login_claimed": False}))

"""Native and gateway write contracts on one disposable, synthetic staging work package."""
import json
import sys
import uuid
import hmac
import hashlib
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from starlette.testclient import TestClient
from gateway.app import create_app
from gateway.native import Native, NativeError
from gateway.service import Service
from gateway.store import Store, canonical
from starlette.responses import JSONResponse

runtime = Path(sys.argv[1])
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
config = {"users": {str(c["id"]): role for role, c in credentials.items()}, "hosts": ["testserver"],
          "project_id": bootstrap["project_id"], "openproject_url": "http://127.0.0.1:18091",
          "source_field": bootstrap["fields"]["Source ID"], "type_ids": list(bootstrap["types"].values()),
          "status_ids": list(bootstrap["statuses"].values())}
def native(role):
    return Native(config["openproject_url"], credentials[role]["token"], config["project_id"])
checks = []

def denied(call, status, message=None):
    try:
        call()
        raise AssertionError("UNEXPECTED_NATIVE_SUCCESS")
    except NativeError as error:
        assert error.status == status, str(error)
        assert not message or message in str(error), str(error)

with TemporaryDirectory() as directory:
    store = Store(directory)
    ui_key = (runtime / "stage-ai/ui.key").read_bytes()
    (Path(directory) / "ui.key").write_bytes(ui_key)
    tokens = {role: store.issue_token(c["id"], role, c["token"]) for role, c in credentials.items()}
    service = Service(store, config, Path(directory) / "workspaces")
    with TestClient(create_app(directory, service)) as client:
        def command(role, action, arguments, key=None):
            response = client.post("/api/v1/commands", headers={"Authorization": "Bearer " + tokens[role]},
                               json={"action": action, "arguments": arguments, "idempotency_key": key})
            if response.status_code == 200 and response.json()["result"].get("human_confirmation_required"):
                proposal = store.proposal(credentials[role]["id"], response.json()["result"]["id"])
                if proposal["state"] == "done":
                    return type("Receipt", (), {"status_code": 200, "json": lambda _: proposal["result"], "text": canonical(proposal["result"])})()
                body = canonical({"actor": credentials[role]["id"], "project": config["project_id"], "audience": "qldapm-ai-ui",
                    "at": time.time(), "nonce": uuid.uuid4().hex, "operation": "confirm", "command": {"id": proposal["id"], "hash": proposal["hash"]}}).encode()
                return client.post("/internal/ui", content=body, headers={"X-Qldapm-Signature": hmac.new(ui_key, body, hashlib.sha256).hexdigest()})
            return response

        source = "AI-TEST-" + uuid.uuid4().hex
        payload = {"source_id": source, "subject": "Synthetic API gate test", "type_id": bootstrap["types"]["Subtask"],
                   "assignee_id": credentials["BE"]["id"]}
        created = command("PM", "create_work_package", payload, source)
        assert created.status_code == 200, created.text
        item = created.json()["result"]
        replay = command("PM", "create_work_package", payload, source)
        assert replay.status_code == 200 and replay.json() == created.json(), replay.text
        matches = [wp for wp in native("PM").packages() if wp.get(config["source_field"]) == source]
        assert len(matches) == 1
        identifier = item["id"]
        path = f"/api/v3/qldapm/gates/{identifier}"
        checks.append("create replay returns one work package")
        denied(lambda: native("PM").call(f"/api/v3/work_packages/{identifier}", "PATCH", {
            "lockVersion": item["lockVersion"], config["source_field"]: "AI-TEST-CHANGED"}), 422, "IMMUTABLE")
        duplicate = {"subject": "Duplicate must fail", config["source_field"]: source,
                     "_links": {"project": {"href": f"/api/v3/projects/{config['project_id']}"},
                                "type": {"href": f"/api/v3/types/{bootstrap['types']['Subtask']}"}}}
        denied(lambda: native("PM").call("/api/v3/work_packages", "POST", duplicate), 422, "DUPLICATE")
        checks.append("native Source ID immutable and unique")

        def gate(role, operation, value, status=200):
            current = native(role).call(path)
            result = command(role, "change_gate", {"id": identifier, "lock_version": current["lockVersion"],
                "operation": operation, "value": value}, str(uuid.uuid4()))
            assert result.status_code == status, result.text
            return result

        gate("BE", "reviewer", {"user_id": credentials["FE"]["id"]}, 422)
        gate("PM", "reviewer", {"user_id": credentials["FE"]["id"]})
        gate("BE", "evidence", {"key": "implementation", "reference": "commit:synthetic-only"})
        self_approval = gate("BE", "approve", {"key": "code", "reference": "review:self"}, 422)
        assert "SELF_APPROVAL" in self_approval.text
        gate("FE", "approve", {"key": "code", "reference": "review:synthetic-only"})
        current = native("FE").call(path)
        assert current["gate"]["approvals"]["code"]["actor_id"] == credentials["FE"]["id"]
        denied(lambda: native("PM").call(path, "POST", {"lock_version": current["lockVersion"] - 1,
            "operation": "reviewer", "value": {"user_id": credentials["FE"]["id"]}}), 409, "STALE")
        gate("BE", "evidence", {"key": "implementation", "reference": "commit:synthetic-changed"})
        assert not native("BE").call(path)["gate"]["approvals"]
        checks += ["role cannot appoint reviewer", "self approval denied", "independent reviewer approved",
                   "native stale gate is HTTP 409", "changed revision invalidates approval"]
        gate("QA", "evidence", {"key": "test", "reference": "test:missing-result"}, 422)
        gate("QA", "evidence", {"key": "test", "reference": "test:failed", "result": "failed"})
        failure = gate("QA", "approve", {"key": "test", "reference": "review:failed-test"}, 422)
        assert "CURRENT_EVIDENCE_REQUIRED" in failure.text
        gate("QA", "evidence", {"key": "test", "reference": "test:passed", "result": "passed"})
        gate("QA", "approve", {"key": "test", "reference": "review:passed-test"})
        gate("BE", "evidence", {"key": "test_cases", "reference": "cases:changed"})
        assert "test" not in native("BE").call(path)["gate"]["approvals"]
        current = native("FE").package(identifier)
        mutation = command("BE", "update_work_package", {"id": identifier, "lock_version": current["lockVersion"],
            "changes": {"subject": "Synthetic receipt-bound update"}}, "receipt-update")
        assert mutation.status_code == 200, mutation.text
        marker = mutation.json()["result"]["request_id"]
        receipt = native("BE").call(f"/api/v3/qldapm/mutation_receipts/{marker}")
        assert receipt["id"] == identifier and receipt["provenance"] == "ai_gateway"
        checks.append("atomic native update receipt available for timeout reconciliation")
        current = native("FE").package(identifier)
        native("FE").call(f"/api/v3/work_packages/{identifier}", "PATCH", {"lockVersion": current["lockVersion"],
                           "subject": "Reviewer authored synthetic content"})
        gate("BE", "evidence", {"key": "implementation", "reference": "commit:content-author-test"})
        failure = gate("FE", "approve", {"key": "code", "reference": "review:self-authored"}, 422)
        assert "SELF_APPROVAL" in failure.text
        checks += ["test result required", "failed test cannot be approved", "test-case changes invalidate test approval",
                   "native content author cannot self-approve"]
        print(json.dumps({"passed": True, "synthetic_only": True, "fixture_id": identifier, "checks": checks}))

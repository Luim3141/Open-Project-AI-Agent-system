"""Real native API + REST/MCP contracts, using five synthetic staging identities only."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from starlette.testclient import TestClient
from gateway.app import create_app
from gateway.native import Native, NativeError
from gateway.service import Service
from gateway.store import Store

runtime = Path(sys.argv[1])
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
config = {"users": {str(value["id"]): role for role, value in credentials.items()},
          "openproject_url": "http://127.0.0.1:18091", "project_id": bootstrap["project_id"], "hosts": ["testserver"]}
results = []
with TemporaryDirectory() as directory:
    store = Store(directory)
    for role, credential in credentials.items():
        native = Native(config["openproject_url"], credential["token"], config["project_id"])
        assert native.identity(credential["id"])["role"] == role
        if role == "PM":
            configuration = native.call("/api/v3/qldapm/configuration")
            assert configuration["project_id"] == config["project_id"] and configuration["settings"]["login_required"]
        else:
            try:
                native.call("/api/v3/qldapm/configuration")
                raise AssertionError("NON_PM_CONFIGURATION_ACCESS")
            except NativeError as error:
                assert error.status == 403, str(error)
        packages = native.packages()
        assert len(packages) == 329
        item = next(wp for wp in packages if wp["_links"]["type"]["title"] == "Subtask")
        gate = native.call(f"/api/v3/qldapm/gates/{item['id']}")
        assert gate["gate"]["checklist"] and all(not c["done"] for c in gate["gate"]["checklist"])
        try:
            native.call(f"/api/v3/work_packages/{item['id']}", "PATCH", {"lockVersion": item["lockVersion"],
                "_links": {"status": {"href": f"/api/v3/statuses/{bootstrap['statuses']['DONE']}"}}})
            raise AssertionError("NATIVE_SHORTCUT_ACCEPTED")
        except NativeError as error:
            assert error.status == 422, str(error)
        token = store.issue_token(credential["id"], role, credential["token"])
        service = Service(store, config, Path(directory) / "workspaces")
        with TestClient(create_app(directory, service)) as client:
            headers = {"Authorization": "Bearer " + token, "Accept": "application/json, text/event-stream"}
            response = client.post("/api/v1/commands", headers=headers, json={"action": "identity"})
            assert response.status_code == 200 and response.json()["result"]["role"] == role, response.text
            response = client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "stage", "version": "1"}}})
            assert response.status_code == 200, response.text
            response = client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "get_gate", "arguments": {"arguments": {"id": item["id"]}}}})
            assert response.status_code == 200 and not response.json()["result"].get("isError"), response.text
        results.append({"role": role, "native_identity": True, "329_visible": True, "native_gate_blocks_shortcut": True,
                        "rest_identity": True, "mcp_initialize_and_gate": True})
print(json.dumps({"passed": True, "synthetic_only": True, "checks": results}))

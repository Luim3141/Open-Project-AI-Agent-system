"""Prepare exclusively synthetic staging state; no production credential access."""
import json
import secrets
import sys
from pathlib import Path

from gateway.store import Store, canonical
from operator_state import require_offline

runtime = Path(sys.argv[1])
require_offline("qldapm-ai-stage-staging-gateway-1")
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
state = runtime / "stage-ai"
state.mkdir(exist_ok=True)
store = Store(state)
config = {"users": {str(row["id"]): role for role, row in credentials.items()}, "project_id": bootstrap["project_id"],
    "openproject_url": "http://staging-web:8080", "source_field": bootstrap["fields"]["Source ID"],
    "type_ids": list(bootstrap["types"].values()), "status_ids": list(bootstrap["statuses"].values()),
    "hosts": ["gateway:8090", "127.0.0.1:18092", "localhost:18092"]}
(state / "config.json").write_text(canonical(config), encoding="utf-8")
if not (state / "ui.key").exists():
    (state / "ui.key").write_text(secrets.token_hex(32), encoding="utf-8")
test_key = runtime / "stage/deep-test-receipt.key"
if not test_key.exists():
    test_key.write_text(secrets.token_hex(32), encoding="utf-8")
for role, credential in credentials.items():
    token = store.issue_token(credential["id"], role, credential["token"])
    (runtime / "stage" / f"deep-{role}.token").write_text(token, encoding="utf-8")
    workspace = runtime / "stage-ai-workspaces" / str(credential["id"]) / "app"
    workspace.mkdir(parents=True, exist_ok=True)
print("Synthetic gateway and UI signing state prepared; provider remains disabled.")

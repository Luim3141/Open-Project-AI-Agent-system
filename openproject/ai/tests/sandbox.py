"""Fixed runner acceptance on an immutable BE workspace and synthetic staging clone only."""
import json
import sys
import uuid
import shutil
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from broker import Broker
from gateway.native import Native

runtime = Path(sys.argv[1])
root = Path(__file__).resolve().parents[1]
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
actor, qa = credentials["BE"]["id"], credentials["QA"]["id"]
images = json.loads((runtime / "image-lock.json").read_text())
if len(sys.argv) == 4:
    images.update(CORE_IMAGE=sys.argv[2], AI_IMAGE=sys.argv[3])
elif len(sys.argv) != 2:
    raise ValueError("EXPECTED_RUNTIME_AND_OPTIONAL_QUALIFIED_IMAGE_PAIR")
# Never open live gateway SQLite or copy real credentials into the acceptance runner.
with TemporaryDirectory(prefix="qldapm-sandbox-") as directory:
    fixture = Path(directory)
    (fixture / "operator").mkdir()
    (fixture / "gateway").mkdir()
    receipts = fixture / "receipts"
    receipts.mkdir()
    (fixture / "operator/approval.key").write_bytes(b"synthetic-operator-only-key")
    (fixture / "operator/test-receipt.key").write_bytes((runtime / "stage/deep-test-receipt.key").read_bytes())
    (fixture / "gateway/config.json").write_text(json.dumps({"users": {str(actor): "BE", str(qa): "QA"}}))
    workspace = fixture / "workspaces" / str(actor)
    for folder in ("app", "config", "db", "lib", "lib_static"):
        shutil.copytree(root.parent / "development/core" / folder, workspace / folder)
    broker = Broker(fixture, test_images=images)
    fingerprint = broker.workspace.tree_hash(actor)
    native = Native("http://127.0.0.1:18091", credentials["QA"]["token"], bootstrap["project_id"])
    item = next(wp for wp in native.packages() if wp["_links"]["type"]["title"] == "Subtask" and
                wp["_links"]["assignee"]["href"] == f"/api/v3/users/{actor}")
    gate = native.call(f"/api/v3/qldapm/gates/{item['id']}")
    for suite in ("gate-policy", "gateway", "core-integration"):
        payload = {"suite": suite, "workspace_actor": actor, "snapshot_hash": fingerprint}
        if suite != "gateway":
            payload.update(project_id=bootstrap["project_id"], work_package_id=item["id"], gate_revision=gate["gate"]["revision"])
        result = broker.test({"id": str(uuid.uuid4()), "actor": qa, "payload": payload})
        assert result["passed"] is True and result["snapshot_hash"] == fingerprint
        if suite != "gateway":
            value = {"key": "test", "reference": "job:" + result["attestation"]["proof"]["job_id"],
                     "verification": "automatic", "result": "passed", "snapshot_hash": fingerprint, "job_receipt": result["attestation"]}
            (receipts / "receipt.json").write_text(json.dumps({"actor": qa, "id": item["id"], "value": value}))
            argv = ["docker", "compose", "--project-name", "qldapm-ai-stage", "--env-file", str(runtime / ".env"),
                    "-f", str(root / "stage.yml"), "-f", str(root / "deep-ai.stage.yml"), "run", "--rm", "--no-deps",
                    "-v", f"{receipts}:/receipts:ro", "-e", "QLDAPM_TEST_ONLY=true", "staging-web", "bundle", "exec", "rails", "runner",
                    "/qldapm-core/sandbox_receipt_test.rb"]
            check = subprocess.run(argv, capture_output=True, text=True, timeout=180,
                                   env={**os.environ, "CORE_IMAGE": images["CORE_IMAGE"], "AI_IMAGE": images["AI_IMAGE"]})
            if check.returncode:
                raise RuntimeError("NATIVE_RECEIPT_ACCEPTANCE_FAILED: " + (check.stdout + check.stderr)[-3000:])
            assert "Signed sandbox receipt native gate PASS" in check.stdout
        print(json.dumps({"suite": suite, "passed": True, "synthetic_database_only": True,
                          "immutable_workspace_actor": actor, "native_receipt_verified": suite != "gateway"}), flush=True)

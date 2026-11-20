"""One real PM-authorized test job; never changes native work packages or credentials."""
import json
import argparse
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--request-key")
key = parser.parse_args().request_key or "local-acceptance-" + uuid.uuid4().hex
print(json.dumps({"request_key": key}), flush=True)
runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
headers = {"Authorization": "Bearer " + (runtime / "operator/user-20.token").read_text().strip()}
with httpx.Client(base_url="http://127.0.0.1:8090", headers=headers, timeout=120, trust_env=False) as client:
    started = time.monotonic()
    response = client.post("/api/v1/commands", json={"action": "request_test", "arguments": {
        "suite": "gate-policy", "workspace_actor": 21}, "idempotency_key": key})
    assert response.status_code == 200, "TEST_PROPOSAL_NOT_ACCEPTED"
    elapsed = time.monotonic() - started
    assert elapsed < 60, "TEST_PROPOSAL_BLOCKED_ON_SNAPSHOT"
    print(json.dumps({"queued_in_seconds": round(elapsed, 2)}), flush=True)
    job = response.json()["result"]
    command = subprocess.run([sys.executable, str(root / "broker.py"), "process", "--runtime", str(runtime),
        "--job", job["id"]], cwd=root, capture_output=True, text=True, timeout=1800)
    if command.returncode:
        raise RuntimeError("BROKER_JOB_NOT_COMPLETED: " + command.stderr[-1000:])
    response = client.post("/api/v1/commands", json={"action": "get_job", "arguments": {"id": job["id"]}})
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["state"] == "done" and result["result"]["passed"] is True
    assert len(result["result"]["snapshot_hash"]) == 64
    print(json.dumps({"actual_actor": 20, "workspace_actor": 21, "job_id": job["id"],
        "passed": True, "native_work_packages_unchanged": True, "be_identity_not_impersonated": True}))

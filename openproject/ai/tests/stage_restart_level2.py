"""Restart only the existing staging containers; assert data, images, keys and AI ledger persist."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
from gateway.native import Native
from gateway.store import canonical

runtime = Path(sys.argv[1])
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
stage = "qldapm-ai-stage-staging-"
containers = ["qldapm-ai-stage-db-1", stage + "web-1", stage + "gateway-1"]
live = ["qldapm-openproject-web-1", "qldapm-ai-gateway-1"]

def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True, timeout=180).stdout.strip()

def ledger():
    script = """import sqlite3,json,hashlib
c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
assert c.execute("select count(*) from ai_runs where state='running'").fetchone()[0]==0
assert c.execute("select count(*) from jobs where state in ('queued','running')").fetchone()[0]==0
print(json.dumps({t:hashlib.sha256(json.dumps(c.execute('select * from '+t+' order by rowid').fetchall(),sort_keys=True).encode()).hexdigest() for t in ['gemini_usage','gemini_blocks','gemini_recovery','ai_runs']}))
"""
    return json.loads(docker("exec", containers[2], "python", "-c", script))

def source():
    rows = Native("http://127.0.0.1:18091", credentials["PM"]["token"], bootstrap["project_id"]).packages()
    assert len(rows) == 329 and len({r[bootstrap["fields"]["Source ID"]] for r in rows}) == 329
    assert all(r["_links"]["status"]["href"] == "/api/v3/statuses/1" for r in rows)
    return hashlib.sha256(canonical(sorted(rows, key=lambda r: r["id"])).encode()).hexdigest()

processes = docker("top", containers[1], "-eo", "pid,args")
assert "/qldapm-core/deep_stage_test.rb" not in processes
assert "rails runner -" not in processes
before_source, before_ledger = source(), ledger()
before_images = {name: docker("inspect", "--format", "{{.Image}}", name) for name in containers + live}
files = [runtime / "stage-ai" / name for name in ["config.json", "gemini.json", "gemini.key", "ui.key"]]
files.append(runtime / "operator/gemini-free/free-tier-proof.json")
before_files = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
docker("restart", containers[0])
deadline = time.monotonic() + 120
while docker("inspect", "--format", "{{.State.Health.Status}}", containers[0]) != "healthy":
    assert time.monotonic() < deadline, "STAGING_DB_NOT_READY"
    time.sleep(2)
docker("restart", *containers[1:])
deadline = time.monotonic() + 180
while docker("inspect", "--format", "{{.State.Health.Status}}", containers[1]) != "healthy":
    assert time.monotonic() < deadline, "STAGING_WEB_NOT_READY"
    time.sleep(2)
assert before_source == source(), "NATIVE_SOURCE_ATTRIBUTES_CHANGED"
assert before_ledger == ledger(), "AI_LEDGER_CHANGED_ON_RESTART"
assert before_images == {name: docker("inspect", "--format", "{{.Image}}", name) for name in containers + live}
assert before_files == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
token = (runtime / "stage/deep-BE.token").read_text().strip()
with httpx.Client(base_url="http://127.0.0.1:18092", headers={"Authorization": "Bearer " + token}, timeout=40, trust_env=False) as client:
    assert client.get("/health").status_code == 200
    response = client.post("/api/v1/commands", json={"action": "get_assistant_status"})
    assert response.status_code == 200
    status = response.json()["result"]
    assert status["gateway_mode"] == "native" and status["openproject"] == "authenticated"
    proof = json.loads(files[-1].read_text())
    if proof.get("authorization", {}).get("mode") == "continuous-free-only":
        assert status["gemini"]["state"] == "authorized" and status["gemini"]["expires"] is None
        assert status["gemini"]["billing_allowed"] is False
    elif proof.get("authorization"):
        assert status["gemini"]["state"] == "blocked", "LEGACY_PAID_CONSENT_NOT_BLOCKED"
    elif time.time() > proof["checked_at"] + 3600:
        assert status["gemini"]["state"] == "blocked", "EXPIRED_PROVIDER_NOT_BLOCKED"
report = {"passed": True, "staging_db_web_gateway_restarted": True, "source_count": 329, "all_source_new": True,
          "native_source_attributes_unchanged": True, "ai_runs_usage_circuit_preserved": True,
          "private_config_key_proof_unchanged": True, "images": before_images, "status": status,
          "google_calls": 0, "production_changed": False, "snapshot_at": time.time()}
path = "artifacts/business-restart.json" if proof.get("data_scope") == "project-business-content" else "artifacts/continuous-restart.json" if proof.get("authorization", {}).get("mode") == "continuous" else "artifacts/level2-restart-final.json"
Path(path).write_text(canonical(report), encoding="utf-8")
print(canonical(report))

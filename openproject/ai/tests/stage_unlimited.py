"""Real Gemini >6 writes in one run, native readback, exact owned fixture cleanup."""
import hashlib
import hmac
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import httpx
from gateway.native import Native
from gateway.store import canonical

runtime = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
key = (runtime / "stage-ai/ui.key").read_bytes()
project = bootstrap["project_id"]
source = "AI-UNLIMITED-" + uuid.uuid4().hex
owned, report = [], {"source": source, "google_real": True, "passed": False}
artifact = Path("artifacts/unlimited-google-acceptance.json")
client = httpx.Client(base_url="http://127.0.0.1:18092", trust_env=False, timeout=70)
def native():
    return Native("http://127.0.0.1:18091", credentials["PM"]["token"], project)

def save():
    artifact.write_text(canonical({**report, "fixture_ids": owned}), encoding="utf-8")

def command(role, action, arguments, request=None, auto=False):
    body = canonical({"actor": credentials[role]["id"], "project": project, "audience": "qldapm-ai-ui", "at": time.time(),
        "nonce": uuid.uuid4().hex, "operation": "command", "command": {"action": action, "arguments": arguments,
        "idempotency_key": request, "auto_execute": auto}}).encode()
    response = client.post("/internal/ui", content=body, headers={"Content-Type": "application/json",
        "X-Qldapm-Signature": hmac.new(key, body, hashlib.sha256).hexdigest()})
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.json().get('error')}"
    return response.json()["result"]

baseline = native().packages()
assert len(baseline) == 329, "NO_OTHER_FIXTURES_ALLOWED"
try:
    for index in range(8):
        item = command("PM", "create_work_package", {"source_id": source + f"-{index}", "subject": source + f"-{index}",
            "type_id": 1, "assignee_role": "BE", "description": "Công việc tạm để kiểm thử bỏ giới hạn số thao tác."}, source + f"-create-{index}", True)
        owned.append(item["id"])
        save()
    # Pace against the existing ledger, without changing or refunding quotas.
    code = "import sqlite3,time; c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True); print(max(0,60-(time.time()-(c.execute('select max(at) from gemini_usage').fetchone()[0] or 0))))"
    delay = float(subprocess.check_output(["docker", "exec", "qldapm-ai-stage-staging-gateway-1", "python", "-c", code], text=True))
    if delay > 0:
        print(f"Waiting {delay:.0f}s for existing quota window", flush=True)
        time.sleep(delay + 1)
    prompt = "Cập nhật " + " và ".join(f"công việc {identifier}" for identifier in owned) + ": đặt hạn hoàn thành của tất cả thành 2026-10-20. Thực hiện đủ 8 công việc. Các công việc độc lập: gom các lần đọc vào cùng lượt tool calls, rồi gom các lần cập nhật vào cùng lượt để tránh hết quota. Báo rõ việc đã làm hoặc không làm được."
    args = {"prompt": prompt, "allow_routine_writes": True, "write_scope_ids": owned}
    started = command("BE", "start_ai_run", args, source + "-run")
    assert command("BE", "start_ai_run", args, source + "-run")["id"] == started["id"]
    report["run_id"] = started["id"]
    save()
    deadline = time.monotonic() + 140
    while True:
        result = command("BE", "get_ai_run", {"id": started["id"]})
        report["run"] = result
        save()
        if result["state"] != "running":
            break
        assert time.monotonic() < deadline, "RUN_DID_NOT_FINISH"
        time.sleep(1)
    assert result["state"] == "done", "PROVIDER_STOPPED; saved receipts, no replay"
    updates = [row for row in result["result"]["outcomes"] if row["action"] == "update_work_package"]
    assert len(updates) == 8 and all(row["state"] == "succeeded" for row in updates)
    assert all(native().package(identifier)["dueDate"] == "2026-10-20" for identifier in owned)
    report.update(passed=True, native_readback=True, confirmed_writes=len(updates))
finally:
    if owned:
        ruby = f'''raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
field = WorkPackageCustomField.find_by!(name: "Source ID")
User.execute_as(User.find_by!(login: "stage-owner")) do
 {owned}.each do |id|
  item = WorkPackage.find(id)
  raise "OTHER_FIXTURE" unless item.project_id == {project} && item.custom_value_for(field).value.to_s.start_with?("{source}-") && !item.children.exists?
  Qldapm::MutationReceipt.where(work_package_id: id).delete_all
  Thread.current[:qldapm_approved_delete] = id
  item.destroy!
 ensure
  Thread.current[:qldapm_approved_delete] = nil
 end
end
puts "Exact owned unlimited fixtures removed."
'''
        cleanup = subprocess.run(["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
            input=ruby, text=True, capture_output=True, timeout=180)
        assert cleanup.returncode == 0, "OWNED_FIXTURE_CLEANUP_FAILED; inspect exact IDs"
    remaining = native().packages()
    assert {row["id"] for row in remaining} == {row["id"] for row in baseline}
    for before, after in zip(sorted(baseline, key=lambda row: row["id"]), sorted(remaining, key=lambda row: row["id"])):
        for field in ("subject", "description", "dueDate", "percentageDone", "lockVersion", "_links"):
            assert before.get(field) == after.get(field), "SOURCE_NATIVE_FIELD_CHANGED"
    report.update(source_count=len(remaining), source_preserved=True, fixture_ids_removed=owned, live_changed=False)
    save()
    print(canonical({name: value for name, value in report.items() if name != "run"}), flush=True)
    client.close()

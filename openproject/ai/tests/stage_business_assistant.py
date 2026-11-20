"""Real Gemini business acceptance, with exact owned fixture cleanup and native readback."""
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
source = "AI-BUSINESS-" + uuid.uuid4().hex
client = httpx.Client(base_url="http://127.0.0.1:18092", trust_env=False, timeout=70)
records, created = [], []

def native(role="PM"):
    return Native("http://127.0.0.1:18091", credentials[role]["token"], project)

def command(role, action, arguments=None, request=None, operation="command"):
    data = {"action": action, "arguments": arguments or {}, "idempotency_key": request, "auto_execute": False} if operation == "command" else arguments
    body = canonical({"actor": credentials[role]["id"], "project": project, "audience": "qldapm-ai-ui", "at": time.time(),
                      "nonce": uuid.uuid4().hex, "operation": operation, "command": data}).encode()
    response = client.post("/internal/ui", content=body, headers={"Content-Type": "application/json",
        "X-Qldapm-Signature": hmac.new(key, body, hashlib.sha256).hexdigest()})
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.json().get('error')}"
    return response.json()["result"]

def run(role, label, prompt, allow=True):
    # Fit the worst bounded run in one fresh minute; don't disable or reset the quota ledger.
    code = "import sqlite3,time; c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True); print(max(0,60-(time.time()-(c.execute('select max(at) from gemini_usage').fetchone()[0] or 0))))"
    delay = float(subprocess.check_output(["docker", "exec", "qldapm-ai-stage-staging-gateway-1", "python", "-c", code], text=True))
    if delay > 0:
        print(f"{label}: waiting {delay:.0f}s for the previous local quota window", flush=True)
        time.sleep(delay + 1)
    request = source + "-" + label
    args = {"prompt": prompt, "allow_routine_writes": allow, "write_scope_ids": []}
    started = command(role, "start_ai_run", args, request)
    assert command(role, "start_ai_run", args, request)["id"] == started["id"], "RUN_REPLAY_NOT_IDEMPOTENT"
    deadline = time.monotonic() + 140
    while True:
        result = command(role, "get_ai_run", {"id": started["id"]})
        if result["state"] != "running": break
        assert time.monotonic() < deadline, "RUN_DID_NOT_FINISH"
        time.sleep(1)
    records.append({"label": label, "actor": credentials[role]["id"], "run": result})
    for tool in (result.get("result") or {}).get("tools", []):
        item = tool.get("result", {}).get("result", {})
        if tool["action"] == "create_work_package" and isinstance(item, dict) and item.get("native_confirmed"):
            created.append(item["id"])
    Path("artifacts/business-google-acceptance.json").write_text(canonical({"records": records, "fixture_ids": created,
        "status": "RUNNING", "source": source}), encoding="utf-8")
    print(canonical({"label": label, "run_id": result["id"], "state": result["state"], "status": (result.get("result") or {}).get("status"),
                     "text": (result.get("result") or {}).get("text"), "error": (result.get("result") or {}).get("error")}), flush=True)
    assert result["state"] == "done", "PROVIDER_STOPPED; receipts saved, no automatic replay"
    return result["result"]

def outcome(result, action):
    rows = [row for row in result.get("outcomes", []) if row["action"] == action]
    assert len(rows) == 1 and rows[0]["state"] == "succeeded", f"{action} not independently confirmed: {rows}"
    return rows[0]

baseline = native().packages()
assert len(baseline) == 329
before_58 = native("BE").collection("/api/v3/work_packages/58/activities")
comment_text = "Đã kiểm tra trên staging"
existing = [row for row in before_58 if comment_text in row.get("comment", {}).get("raw", "")]
passed = False
try:
    status = command("BE", "get_assistant_status")
    assert status["gemini"]["data_scope"] == "project-business-content"
    options = command("BE", "get_project_options")
    assert {row["name"] for row in options["types"]} == {"Task", "Epic", "Subtask"}
    full = command("BE", "get_work_package", {"id": 58, "include_context": True})
    assert len(full["description"]["raw"]) > 1000 and full["business_relations"]
    semantic = run("BE", "semantic", "Đọc đầy đủ công việc 58, mô tả và bình luận/quan hệ. Giải thích nghiệp vụ gỡ thành viên khỏi Project, các acceptance criteria và điểm cần kiểm thử, bằng lời tiếng Việt; không ghi thay đổi.", False)
    assert semantic["text"] and "thành viên" in semantic["text"].lower()
    assert any(tool["action"] == "get_work_package" for tool in semantic["tools"])
    if not existing:
        comment = run("BE", "comment58", "Thêm comment vào công việc 58: Đã kiểm tra trên staging")
        outcome(comment, "comment")
    activities = native("BE").collection("/api/v3/work_packages/58/activities")
    target = [row for row in activities if comment_text in row.get("comment", {}).get("raw", "")]
    assert len(target) == max(1, len(existing)), "COMMENT_MISSING_OR_DUPLICATED"
    if not existing:
        assert target[0]["_links"]["user"]["href"] == f"/api/v3/users/{credentials['BE']['id']}"
    task = run("PM", "create-task", f'Tạo Task có tên "{source} Task", mô tả "Fixture nghiệp vụ staging: xác nhận trước khi thu hồi quyền", giao cho BE. Source ID {source}.')
    task_id = outcome(task, "create_work_package")["work_package_id"]
    task_native = native().package(task_id)
    assert task_native["subject"] == source + " Task" and task_native["_links"]["assignee"]["href"].endswith("/8")
    child = run("PM", "create-subtask", f'Tạo Subtask dưới công việc {task_id}, tên "{source} Subtask", mô tả "Kiểm tra quyền truy cập sau khi gỡ thành viên", giao cho BE. Source ID {source}-child.')
    child_id = outcome(child, "create_work_package")["work_package_id"]
    child_native = native().package(child_id)
    assert child_native["_links"]["parent"]["href"] == f"/api/v3/work_packages/{task_id}"
    priority = next((row for row in options["priorities"] if row["name"].lower() == "high"), options["priorities"][0])
    update = run("BE", "update-all-fields", f'Sửa công việc {child_id}: tên "{source} Updated", mô tả chính xác "Acceptance: từ chối truy cập ngay khi thu hồi quyền", đặt hạn hoàn thành 2026-10-20, giao cho BE, ưu tiên {priority["name"]}.')
    outcome(update, "update_work_package")
    updated = native().package(child_id)
    assert updated["subject"] == source + " Updated" and updated["description"]["raw"] == "Acceptance: từ chối truy cập ngay khi thu hồi quyền"
    assert updated["dueDate"] == "2026-10-20" and updated["_links"]["priority"]["href"] == f'/api/v3/priorities/{priority["id"]}'
    assert updated["_links"]["assignee"]["href"].endswith("/8")
    transition = run("BE", "transition", f"Chuyển công việc {child_id} sang IN PROGRESS.")
    outcome(transition, "transition")
    assert native().package(child_id)["_links"]["status"]["href"] == "/api/v3/statuses/7"
    proposed = run("BE", "preview", f'Sửa tên công việc {child_id} thành "{source} Approved".', False)
    proposals = [row for row in proposed["outcomes"] if row["state"] == "proposed"]
    assert len(proposals) == 1 and native().package(child_id)["subject"] == source + " Updated"
    proposal = command("BE", "get_proposal", {"id": proposals[0]["proposal_id"]})
    confirmed = command("BE", None, {"id": proposal["id"], "hash": proposal["hash"]}, operation="confirm")
    assert confirmed["subject"] == source + " Approved" and native().package(child_id)["subject"] == source + " Approved"
    passed = True
finally:
    if created:
        # Exact owned IDs only, matching this request's fixture title or ai-run Source ID.
        runs = [record["run"]["id"] for record in records]
        ruby = f'''raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
field = WorkPackageCustomField.find_by!(name: "Source ID")
User.execute_as(User.find_by!(login: "stage-owner")) do
 {list(reversed(created))}.each do |id|
  item = WorkPackage.find(id)
  owned = item.custom_value_for(field).value.to_s.start_with?("{source}") || {runs}.any? {{ |run| item.custom_value_for(field).value.to_s.start_with?("ai-#{{run}}-") }}
  raise "OTHER_FIXTURE" unless owned && item.project_id == {project} && !item.children.exists?
  Qldapm::MutationReceipt.where(work_package_id: id).delete_all
  Thread.current[:qldapm_approved_delete] = id
  item.destroy!
 ensure
  Thread.current[:qldapm_approved_delete] = nil
 end
end
puts "Owned business fixtures removed."
'''
        cleanup = subprocess.run(["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
                                 input=ruby, text=True, capture_output=True, timeout=180)
        assert cleanup.returncode == 0, "OWNED_FIXTURE_CLEANUP_FAILED; inspect exact IDs, no bulk removal"
    remaining = native().packages()
    assert len(remaining) == 329 and {row["id"] for row in remaining} == {row["id"] for row in baseline}
    # Read fields must not change except the explicit comment's native version/update timestamp.
    for before, after in zip(sorted(baseline, key=lambda x: x["id"]), sorted(remaining, key=lambda x: x["id"])):
        for field in ("subject", "description", "dueDate", "percentageDone"):
            assert before.get(field) == after.get(field), "SOURCE_BUSINESS_FIELD_CHANGED"
        for link in ("parent", "assignee", "type", "status", "priority"):
            assert before["_links"].get(link) == after["_links"].get(link), "SOURCE_LINK_CHANGED"
    report = {"passed": passed, "records": records, "fixture_ids_removed": created, "source_count": 329,
              "comment58_retained": True, "comment58_already_present": bool(existing), "google_real": True, "live_changed": False}
    Path("artifacts/business-google-acceptance.json").write_text(canonical(report), encoding="utf-8")
    print(canonical({key: value for key, value in report.items() if key != "records"}), flush=True)
    client.close()

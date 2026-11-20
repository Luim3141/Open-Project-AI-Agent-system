"""Two controlled real Gemini runs on one synthetic staging Task; no human/live approval impersonation."""
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
from gateway.native import Native
from gateway.store import canonical
from operator_state import ContainerState

runtime = Path(sys.argv[1])
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
pm = credentials["PM"]
native = Native("http://127.0.0.1:18091", pm["token"], bootstrap["project_id"])
def fresh_native():
    # Each independent readback gets its own request deadline after a bounded AI run.
    return Native("http://127.0.0.1:18091", pm["token"], bootstrap["project_id"])
assert native.identity(pm["id"])["role"] == "PM"
assert len(native.packages()) == 329
source = "AI-LEVEL2-GENAI-" + uuid.uuid4().hex
token = ContainerState(runtime / "stage-ai", "qldapm-ai-stage-staging-gateway-1").call(
    "issue_token", user_id=pm["id"], role="PM", op_token=pm["token"])
run_ids, created = [], []

with httpx.Client(base_url="http://127.0.0.1:18092", headers={"Authorization": "Bearer " + token},
                  timeout=40, trust_env=False, follow_redirects=False) as client:
    def run(prompt, scope=None):
        payload = {"prompt": prompt, "allow_routine_writes": True, "write_scope_ids": scope or []}
        key = "real-ai-write-" + uuid.uuid4().hex
        response = client.post("/api/v1/ai-runs", headers={"Idempotency-Key": key}, json=payload)
        assert response.status_code == 200, "AI_START_FAILED; no automatic retry"
        identifier = response.json()["result"]["id"]
        run_ids.append(identifier)
        Path("artifacts/level2-google-writes-progress.json").write_text(canonical({"run_ids": run_ids, "source_id": source}), encoding="utf-8")
        deadline = time.monotonic() + 125
        while True:
            response = client.get("/api/v1/ai-runs/" + identifier)
            assert response.status_code == 200, "AI_POLL_FAILED; preserve run ID"
            result = response.json()["result"]
            if result["state"] != "running":
                break
            assert time.monotonic() < deadline, "AI_RUN_UNKNOWN; inspect exact source before retry"
            time.sleep(2)
        assert result["state"] == "done", result.get("result", {}).get("error", "AI_FAILED_OR_UNKNOWN")
        replay = client.post("/api/v1/ai-runs", headers={"Idempotency-Key": key}, json=payload)
        assert replay.status_code == 200 and replay.json()["result"]["id"] == identifier
        return result["result"]

    try:
        answer = run(f"Yêu cầu staging synthetic: dùng create_work_package tạo đúng một Task mới, source_id='{source}', "
            f"subject='Synthetic Gemini scoped task', type_id={bootstrap['types']['Task']}, assignee_role='BE'. "
            "Tôi cho phép thực hiện ngay tạo Task này trong Native Mode. Không thao tác công việc khác; không admin, không deploy.")
        rows = [row for row in fresh_native().packages() if row.get(bootstrap["fields"]["Source ID"]) == source]
        assert len(rows) == 1, "CREATE_NOT_CONFIRMED_OR_DUPLICATE"
        item = rows[0]
        created.append(item["id"])
        assert item["subject"] == "Synthetic Gemini scoped task"
        assert item["_links"]["assignee"]["href"] == f"/api/v3/users/{credentials['BE']['id']}"
        assert any(tool["action"] == "create_work_package" and tool["result"]["result"].get("native_confirmed") is True
                   for tool in answer["tools"]), "MODEL_CREATED_NO_VERIFIED_RECEIPT"
        updated = run(f"Yêu cầu synthetic: chỉ dùng update_work_package sửa Task id={item['id']}, lock_version={item['lockVersion']}, "
            "changes={description:'Synthetic Gemini scoped update', due_date:'2026-10-21'}. "
            "Tôi cho phép thực hiện đúng cập nhật này. Không tạo hoặc sửa công việc khác.", [item["id"]])
        item = fresh_native().package(item["id"])
        assert item["description"]["raw"] == "Synthetic Gemini scoped update" and item["dueDate"] == "2026-10-21"
        assert any(tool["action"] == "update_work_package" and tool["result"]["result"].get("native_confirmed") is True
                   for tool in updated["tools"])
        assert len(fresh_native().packages()) == 330
        report = {"passed": True, "real_google": True, "synthetic_staging_only": True, "run_ids": run_ids,
                  "fixture_ids": created, "automatic_create": True, "scoped_update": True, "same_run_replay": True,
                  "independent_native_readback": True, "model": answer["model"], "production_changed": False}
        Path("artifacts/level2-google-writes-real.json").write_text(canonical(report), encoding="utf-8")
    finally:
        # Read exact Source ID even if model's final claims fail after a native write; never repeat a create.
        matches = [row for row in fresh_native().packages() if row.get(bootstrap["fields"]["Source ID"]) == source]
        assert len(matches) <= 1, "AMBIGUOUS_FIXTURE; no bulk cleanup"
        if matches:
            identifier = matches[0]["id"]
            ruby = f'''raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
item = WorkPackage.find({identifier})
field = WorkPackageCustomField.find_by!(name: "Source ID")
raise "OTHER_ITEM" unless item.project_id == {bootstrap['project_id']} && item.custom_value_for(field).value == "{source}" && !item.children.exists?
User.execute_as(User.find_by!(login: "stage-owner")) do
  Thread.current[:qldapm_approved_delete] = item.id
  item.destroy!
ensure
  Thread.current[:qldapm_approved_delete] = nil
end
puts "Only this exact synthetic Gemini fixture cleaned."
'''
            result = subprocess.run(["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
                input=ruby, capture_output=True, text=True, timeout=180)
            assert result.returncode == 0, "EXACT_FIXTURE_CLEANUP_FAILED"
        assert len(fresh_native().packages()) == 329, "SOURCE_COUNT_CHANGED"

print(canonical({**report, "fixture_removed": True, "source_count": 329}))

"""Actual staging gateway/API acceptance; only synthetic fixtures created by this run are removed."""
import hashlib
import hmac
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
from gateway.native import Native
from gateway.store import canonical

runtime = Path(sys.argv[1])
bootstrap = json.loads((runtime / "stage/bootstrap.json").read_text())
credentials = json.loads((runtime / "stage/test-credentials.json").read_text())
ui_key = (runtime / "stage-ai/ui.key").read_bytes()
source = "AI-LEVEL2-" + uuid.uuid4().hex
created, checks, blocked = [], [], []
project = bootstrap["project_id"]
client = httpx.Client(base_url="http://127.0.0.1:18092", timeout=60, trust_env=False, follow_redirects=False)

def native(role="PM"):
    return Native("http://127.0.0.1:18091", credentials[role]["token"], project)

def ui(role, command, operation="command", status=200):
    body = canonical({"actor": credentials[role]["id"], "project": project, "audience": "qldapm-ai-ui",
        "at": time.time(), "nonce": uuid.uuid4().hex, "operation": operation, "command": command}).encode()
    response = client.post("/internal/ui", content=body, headers={
        "Content-Type": "application/json", "X-Qldapm-Signature": hmac.new(ui_key, body, hashlib.sha256).hexdigest()})
    assert response.status_code == status, f"Unexpected staging HTTP {response.status_code}: {response.json().get('error', 'unknown')}"
    return response.json()

def command(role, action, arguments=None, key=None, auto=False, status=200):
    return ui(role, {"action": action, "arguments": arguments or {}, "idempotency_key": key, "auto_execute": auto}, status=status)

baseline = len(native().packages())
assert baseline == 329, "STAGING_BASELINE_NOT_329; no mutation"
try:
    assert client.get("/health").status_code == 200
    assert client.post("/api/v1/commands", json={"action": "identity"}).status_code == 401
    state = command("PM", "get_assistant_status")["result"]
    assert state["gateway_mode"] == "native"
    checks.append("Native Mode + authenticated OpenProject + anonymous denial")
    task_args = {"source_id": source, "subject": "Synthetic Level 2 task", "type_id": bootstrap["types"]["Task"]}
    task_result = command("PM", "create_work_package", task_args, source, auto=True)
    task = task_result["result"]
    created.append(task["id"])
    assert command("PM", "create_work_package", task_args, source, auto=True) == task_result
    assert len([p for p in native().packages() if p.get(bootstrap["fields"]["Source ID"]) == source]) == 1
    checks.append("Create Task + replay creates one native work package")
    child_args = {"source_id": source + "-child", "subject": "Synthetic Level 2 subtask",
        "type_id": bootstrap["types"]["Subtask"], "parent_id": task["id"], "assignee_id": credentials["BE"]["id"]}
    form = native().call(f"/api/v3/projects/{project}/work_packages/form", "POST", {"subject": child_args["subject"],
        bootstrap["fields"]["Source ID"]: child_args["source_id"], "_links": {"project": {"href": f"/api/v3/projects/{project}"},
        "type": {"href": f"/api/v3/types/{child_args['type_id']}"}, "parent": {"href": f"/api/v3/work_packages/{task['id']}"}}})
    parent_error = form.get("_embedded", {}).get("validationErrors", {}).get("parent", {})
    if parent_error.get("errorIdentifier", "").endswith(":PropertyIsReadOnly"):
        blocked.append("Subtask parent link: native manage_subtasks permission absent; no permission change")
        child_args.pop("parent_id")
    child = command("PM", "create_work_package", child_args, source + "-child", auto=True)["result"]
    created.append(child["id"])
    if "parent_id" in child_args:
        assert child["_links"]["parent"]["href"].endswith("/" + str(task["id"]))
        checks.append("Create Subtask with native parent/assignee readback")
    else:
        checks.append("Create Subtask type with native assignee readback; parent link BLOCKED")
    priority = native().collection("/api/v3/priorities")[0]["id"]
    arguments = {"id": child["id"], "lock_version": child["lockVersion"], "changes": {
        "description": "Synthetic tiếng Việt; not production evidence", "due_date": "2026-10-20", "priority_id": priority, "assignee_role": "BE"}}
    updated = command("BE", "update_work_package", arguments, source + "-update", auto=True)["result"]
    assert updated["description"]["raw"] == arguments["changes"]["description"]
    assert updated["dueDate"] == "2026-10-20"
    assert updated["_links"]["priority"]["href"] == f"/api/v3/priorities/{priority}"
    assert updated["_links"]["assignee"]["href"] == f"/api/v3/users/{credentials['BE']['id']}"
    command("BE", "update_work_package", arguments, source + "-stale", auto=True, status=409)
    checks.append("Update description/deadline/priority + native readback + stale lock denied")
    comment_args = {"id": child["id"], "lock_version": updated["lockVersion"], "text": "Synthetic Level 2 comment"}
    comment = command("BE", "comment", comment_args, source + "-comment", auto=True)
    assert command("BE", "comment", comment_args, source + "-comment", auto=True) == comment
    activities = native().collection(f"/api/v3/work_packages/{child['id']}/activities")
    assert sum("Synthetic Level 2 comment" in a.get("comment", {}).get("raw", "") for a in activities) == 1
    checks.append("Comment + one native journal after replay")
    current = native().package(child["id"])
    transition = {"id": child["id"], "lock_version": current["lockVersion"], "status_id": bootstrap["statuses"]["IN PROGRESS"]}
    command("QA", "transition", transition, source + "-wrong-role", auto=True, status=422)
    moved = command("BE", "transition", transition, source + "-transition", auto=True)["result"]
    assert moved["_links"]["status"]["href"] == f"/api/v3/statuses/{transition['status_id']}"
    checks.append("Native workflow valid transition + wrong role denied")
    preview_args = {"id": child["id"], "lock_version": moved["lockVersion"], "changes": {"subject": "Synthetic approved title"}}
    proposal = command("BE", "update_work_package", preview_args, source + "-preview")["result"]
    assert native().package(child["id"])["subject"] == "Synthetic Level 2 subtask"
    approved = ui("BE", {"id": proposal["id"], "hash": proposal["hash"]}, "confirm")
    assert approved["result"]["subject"] == "Synthetic approved title"
    ui("BE", {"id": proposal["id"], "hash": proposal["hash"]}, "confirm", status=409)
    checks.append("Preview has no write + approve commits once + consumed proposal denial")
    now = native().package(child["id"])
    proposal = command("BE", "update_work_package", {"id": child["id"], "lock_version": now["lockVersion"],
        "changes": {"subject": "This must never be applied"}}, source + "-reject-preview")["result"]
    result = command("BE", "reject_proposal", {"id": proposal["id"], "hash": proposal["hash"]}, source + "-reject")
    assert result["result"]["state"] == "rejected"
    assert native().package(child["id"])["subject"] == "Synthetic approved title"
    ui("BE", {"id": proposal["id"], "hash": proposal["hash"]}, "confirm", status=409)
    checks.append("Reject has no business mutation + rejected proposal cannot be approved")
    command("BE", "get_gate", {"id": child["id"]}, status=409)
    history = command("BE", "get_action_history")["result"]
    assert all(event["actor"] == credentials["BE"]["id"] for event in history["audit"])
    checks.append("Custom gate unsupported + actor-scoped action history")
    assert command("PM", "analyze", {"query": "Synthetic approved"})["result"]["count"] == 1
    checks.append("Search/project analysis reads actual current work package")
finally:
    client.close()
    if created:
        # Test-only cleanup is constrained to this UUID and these exact new IDs; never a bulk Source ID wildcard.
        ruby = f'''raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
field = WorkPackageCustomField.find_by!(name: "Source ID")
User.execute_as(User.find_by!(login: "stage-owner")) do
  {list(reversed(created))}.each do |id|
    item = WorkPackage.find(id)
    raise "OTHER_FIXTURE" unless item.project_id == {project} && item.custom_value_for(field).value.start_with?("{source}") && !item.children.exists?
    Qldapm::MutationReceipt.where(work_package_id: id).delete_all
    Thread.current[:qldapm_approved_delete] = id
    item.destroy!
  ensure
    Thread.current[:qldapm_approved_delete] = nil
  end
end
raise "SOURCE_COUNT_CHANGED" unless Project.find({project}).work_packages.count == {baseline}
puts "Only this run's fixtures removed; source count preserved."
'''
        cleanup = subprocess.run(["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
            input=ruby, text=True, capture_output=True, timeout=180)
        assert cleanup.returncode == 0, "FIXTURE_CLEANUP_FAILED; inspect retained exact IDs before retry"

print(canonical({"passed": not blocked, "status": "PARTIAL" if blocked else "PASS", "blocked": blocked,
                 "synthetic_only": True, "source_count": baseline, "fixture_ids_removed": created, "checks": checks, "google_calls": 0}))

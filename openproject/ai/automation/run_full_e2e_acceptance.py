"""Checkpoint-aware Main API qualification. Native mutation requires a separate exact PM decision."""
import json
from pathlib import Path
import sys
import time
import uuid

import requests


def run_readonly(operator_dir):
    """Resume Main evidence without starting a model run, proposal or Native mutation."""
    import copy
    import subprocess
    from datetime import datetime, timezone
    from gateway.native import Native
    from gateway.store import canonical, digest
    from automation.deploy_real_n8n_workflows import secure_workflows

    private = Path(operator_dir)
    runtime = private.parent.parent
    secrets = json.loads((private / "incident-secrets.json").read_text(encoding="utf-8"))
    credentials = json.loads((runtime / "gateway/credentials.json").read_text(encoding="utf-8"))
    session = requests.Session()
    session.trust_env = False
    pm = {"Authorization": "Bearer " + next(v for k, v in secrets.items() if ":PM_TOKEN" in k)}
    ba = {"Authorization": "Bearer " + next(v for k, v in secrets.items() if ":BA_TOKEN" in k)}
    ingress = {"X-QLDAPM-Webhook-Token": secrets["webhook_secret.json:webhook_token"]}
    owner = {"Cookie": "n8n-auth=" + next(v for k, v in secrets.items() if k.endswith(":COOKIE"))}
    report = {"observed_at": datetime.now(timezone.utc).isoformat(), "route": "API_CLI",
              "model_starts": 0, "native_writes": 0, "workflow_changes": 0, "checks": {}}

    def check(name, passed, evidence):
        report["checks"][name] = {"status": "PASS" if passed else "FAILED", "evidence": evidence}

    def get(url, headers=None):
        return session.get(url, headers=headers, timeout=30, allow_redirects=False)

    def ledger():
        code = ("import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);"
                "d.execute('BEGIN');print(json.dumps({t:d.execute('SELECT count(*) FROM '+t).fetchone()[0] "
                "for t in ['gemini_call_receipts','gemini_usage','proposals','knowledge_sync']}))")
        return json.loads(subprocess.check_output(["docker", "exec", "qldapm-ai-gateway-1", "python", "-c", code]))

    before = ledger()
    for name, url in {"gateway": "http://127.0.0.1:8090/health",
                      "native": "http://127.0.0.1:8088/health_checks/default",
                      "n8n": "http://127.0.0.1:5679/healthz",
                      "qdrant": "http://127.0.0.1:6333/healthz",
                      "ollama": "http://127.0.0.1:11434/api/tags"}.items():
        response = get(url)
        evidence = {"http_status": response.status_code}
        if name == "ollama" and response.status_code == 200:
            evidence["models"] = [m["name"] for m in response.json()["models"]]
        check(name + "_health", response.status_code == 200, evidence)

    native = Native("http://127.0.0.1:8088", credentials["19"], 5)
    identity = native.identity(19)
    check("pm_identity", identity["role"] == "PM", identity)
    item = native.package(370)
    draft = json.loads((Path(__file__).resolve().parents[3] / "docs/ai/CODEX_SCENARIO_F_DRAFT_NOT_EXECUTABLE.json").read_text(encoding="utf-8"))
    from automation.checkpoint import strict_load, native_baseline
    checkpoint = strict_load(Path(__file__).resolve().parents[3] / "docs/ai/CODEX_MAIN_CONTINUATION_CHECKPOINT.json")
    expected_count, expected_fingerprint, expected_version = native_baseline(checkpoint)
    expected_description = draft["after_description"] if expected_version == 2 else draft["before_description"]
    links = item["_links"]
    evidence = {"id": item["id"], "lock_version": item["lockVersion"],
                "project": links["project"]["href"], "author": links["author"]["href"],
                "assignee": links["assignee"]["href"], "status": links["status"]["title"],
                "update_link_visible": "update" in links,
                "description_sha256": digest(item["description"]["raw"])}
    passed = (item["lockVersion"] == expected_version and item["subject"] == "[CODEX TEST] Main Native E2E fdae09fb"
              and links["author"]["href"] == "/api/v3/users/19"
              and links["assignee"]["href"] == "/api/v3/users/19"
              and item["description"]["raw"] == expected_description)
    check("task370_persisted_baseline", passed, evidence)
    packages = native.packages()
    fingerprint = digest(canonical(sorted((p["id"], p["lockVersion"]) for p in packages)))
    check("native_collection_baseline", len(packages) == expected_count and fingerprint == expected_fingerprint,
          {"count": len(packages), "fingerprint": fingerprint})

    run_id = "99f1242a-ec81-4558-a8dd-88d0af091cf5"
    for role, headers, expected in (("PM", pm, 200), ("BA", ba, 403)):
        response = session.post("http://127.0.0.1:5679/webhook/qldapm-agent-request",
                                headers={**headers, **ingress}, json={"operation": "status", "run_id": run_id},
                                timeout=45, allow_redirects=False)
        evidence = {"http_status": response.status_code, "run_id": run_id}
        passed = response.status_code == expected
        if role == "PM" and passed:
            stored_result = response.json()["result"].get("result") or {}
            evidence["content_status"] = stored_result.get("status")
            if expected_version == 2:
                passed = stored_result.get("stale") is True and stored_result.get("tools") == []
        check("wf03_stored_run_" + role, passed, evidence)
    response = session.post("http://127.0.0.1:5679/webhook/qldapm-agent-request", headers=pm,
                            json={"operation": "status", "run_id": run_id}, timeout=30, allow_redirects=False)
    check("wf03_transport_secret_required", response.status_code == 403, {"http_status": response.status_code})

    response = get("http://127.0.0.1:5679/rest/workflows", owner)
    response.raise_for_status()
    workflows = [w for w in response.json()["data"] if w["name"].startswith("WF")]
    inventory = {}
    for row in workflows:
        code = row["name"].split(":", 1)[0]
        if code not in {f"WF{i:02}" for i in range(1, 17)}:
            continue
        if code in inventory:
            raise ValueError("AMBIGUOUS_MAIN_WORKFLOW_" + code)
        response = get("http://127.0.0.1:5679/rest/workflows/" + row["id"], owner)
        response.raise_for_status()
        live = response.json()["data"]
        spec = {k: live[k] for k in ("name", "nodes", "connections", "settings")}
        hardened = secure_workflows({code: copy.deepcopy(spec)})[code]
        inventory[code] = {"id": live["id"], "version": live["versionId"], "active": live["active"],
                           "source_hardening_matches": spec == hardened,
                           "drift_fields": [k for k in spec if spec[k] != hardened[k]],
                           "sha256": digest(canonical(spec)), "business_e2e": "NOT_TESTED_BY_THIS_READONLY_RUN"}
    report["workflows"] = inventory
    check("workflow_inventory", set(inventory) == {f"WF{i:02}" for i in range(1, 17)} and
          all(w["active"] and w["source_hardening_matches"] for w in inventory.values()),
          {"count": len(inventory), "drift": [code for code, w in inventory.items() if not w["source_hardening_matches"]]})
    after = ledger()
    check("no_new_provider_proposals_or_sync_jobs", before == after, {"before": before, "after": after})
    report["status"] = "PASS" if all(c["status"] == "PASS" for c in report["checks"].values()) else "FAILED"
    return report


def start_scenario_f_plan(operator_dir):
    """One plan-only request. PM decision and Native write are deliberately absent."""
    from datetime import datetime, timezone
    from gateway.native import Native
    from gateway.planner import is_write_intent, resolve_target_agents

    repo = Path(__file__).resolve().parents[3]
    private = Path(operator_dir)
    qualification = json.loads((repo / "docs/ai/CODEX_MAIN_API_QUALIFICATION_RESULT.json").read_text(encoding="utf-8"))
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(qualification["observed_at"])).total_seconds()
    if qualification["status"] != "PASS" or not 0 <= age <= 1800:
        raise ValueError("FRESH_READONLY_QUALIFICATION_REQUIRED")
    attempt = private / "scenario-f-plan-only-attempt.json"
    if attempt.exists():
        raise ValueError("PLAN_ALREADY_ATTEMPTED_RECONCILE_SAVED_RECEIPT_DO_NOT_RESTART")
    secrets = json.loads((private / "incident-secrets.json").read_text(encoding="utf-8"))
    credentials = json.loads((private.parent.parent / "gateway/credentials.json").read_text(encoding="utf-8"))
    native = Native("http://127.0.0.1:8088", credentials["19"], 5)
    if native.identity(19)["role"] != "PM":
        raise ValueError("GENUINE_PM_REQUIRED")
    item = native.package(370)
    draft = json.loads((repo / "docs/ai/CODEX_SCENARIO_F_DRAFT_NOT_EXECUTABLE.json").read_text(encoding="utf-8"))
    if item["lockVersion"] != 1 or item["description"]["raw"] != draft["before_description"]:
        raise ValueError("TEST_RESOURCE_CHANGED_REPREVIEW_REQUIRED")
    prompt = (
        "PM/Supervisor điều phối BA FE BE QA cho tài nguyên test Work Package #370. "
        "Chỉ tạo đề xuất cập nhật mô tả công việc370, chờ PM duyệt riêng. "
        "BA kiểm tra acceptance criteria và giới hạn test. FE phân tích approval UI và accessibility. "
        "BE là agent DUY NHẤT được điền proposed_operations: đúng1 update_work_package cho work_package_id370, "
        "chỉ đặt description bằng nguyên văn chuỗi JSON bên dưới, subject=null, status_id=null. "
        "BA, FE, QA bắt buộc proposed_operations=[]; QA kiểm tra idempotency, Native readback, RAGsync; "
        "không khẳng định đã chạy test. Đọc Native và retrieved_knowledge, trích dẫn #370. "
        "Reviewer kiểm tra citation/phạm vi. Không thực thi ghi Native, không transition/comment/create. "
        "description JSON: " + json.dumps(draft["after_description"], ensure_ascii=False))
    if not is_write_intent(prompt) or resolve_target_agents(prompt, "supervisor") != ["ba", "fe", "be", "qa"]:
        raise ValueError("EXPECTED_FOUR_SPECIALIST_PLAN_REQUIRED")
    payload = {"operation": "plan", "request_id": str(uuid.uuid4()), "prompt": prompt}
    # Exclusive creation prevents an ambiguous HTTP outcome from becoming a second model run.
    with attempt.open("x", encoding="utf-8") as stream:
        json.dump({"payload": payload, "native_write_approved": False, "max_model_calls": 5}, stream, ensure_ascii=False)
    session = requests.Session()
    session.trust_env = False
    response = session.post("http://127.0.0.1:5679/webhook/qldapm-agent-request", timeout=45,
        allow_redirects=False, json=payload, headers={
            "Authorization": "Bearer " + next(v for k, v in secrets.items() if ":PM_TOKEN" in k),
            "X-QLDAPM-Webhook-Token": secrets["webhook_secret.json:webhook_token"]})
    receipt = {"http_status": response.status_code, "body": response.json()}
    (private / "scenario-f-plan-only-start.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    if response.status_code != 200:
        raise RuntimeError("PLAN_START_HTTP_" + str(response.status_code) + "_SEE_PRIVATE_RECEIPT")
    return {"status": "PLAN_STARTED_NO_NATIVE_APPROVAL_OR_WRITE", "run_id": receipt["body"]["result"]["id"],
            "request_id": payload["request_id"], "native_writes": 0}


def read_scenario_f_plan(operator_dir):
    """Read the one saved run and publish only a validated, pending approval preview."""
    from datetime import datetime, timezone
    repo = Path(__file__).resolve().parents[3]
    private = Path(operator_dir)
    secrets = json.loads((private / "incident-secrets.json").read_text(encoding="utf-8"))
    start = json.loads((private / "scenario-f-plan-only-start.json").read_text(encoding="utf-8"))
    run_id = start["body"]["result"]["id"]
    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": "Bearer " + next(v for k, v in secrets.items() if ":PM_TOKEN" in k)}

    def read(name, path):
        response = session.get("http://127.0.0.1:8090/api/v1/" + path, headers=headers,
                               timeout=30, allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("PLAN_READ_HTTP_" + str(response.status_code))
        body = response.json()
        (private / ("scenario-f-plan-only-" + name + ".json")).write_text(
            json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        return body["result"]

    run = read("poll", "ai-runs/" + run_id)
    result = run.get("result") or {}
    if run["state"] == "running" or run["state"] == "queued":
        return {"status": "RUNNING", "run_id": run_id, "model_calls": result.get("model_call_count", 0)}
    draft = json.loads((repo / "docs/ai/CODEX_SCENARIO_F_DRAFT_NOT_EXECUTABLE.json").read_text(encoding="utf-8"))
    expected = {"id": 370, "lock_version": 1, "changes": {"description": draft["after_description"]}}
    if not (run["state"] == "done" and result.get("status") == "proposed"
            and result.get("model_used") is True and result.get("model_call_count") == 5
            and result.get("source_ids") == [370]
            and [a["agent"] for a in result["agent_outputs"]] == ["ba", "fe", "be", "qa", "reviewer"]
            and result["plan"]["actor_id"] == 19 and result["plan"]["project_id"] == 5
            and len(result["tools"]) == 1 and result["tools"][0]["action"] == "update_work_package"
            and result["tools"][0]["arguments"] == expected):
        raise ValueError("SCENARIO_F_PLAN_CONTRACT_FAILED_NO_APPROVAL_PREVIEW")
    provenance = result["context_provenance"]
    receipts = result["provider_receipts"]
    if not (provenance["rag_state"] == "HITS" and provenance["rag_hits"]
            and all(h["native_id"] == 370 and h["lock_version"] == 1 for h in provenance["rag_hits"])
            and len(receipts) == 10 and all(len(r.get("request_sha256", "")) == 64 and
                r["run_id"] == run_id and r["actor"] == 19 and r["http_status"] == 200 for r in receipts)):
        raise ValueError("SCENARIO_F_CONTEXT_OR_PROVIDER_PROOF_FAILED")
    original = result["tools"][0]["result"]["result"]
    proposal = read("proposal", "proposals/" + original["id"])
    progress = read("progress", "agent-runs/" + run_id)
    trace = read("trace", "agent-runs/" + run_id + "/trace?limit=50")
    command = proposal["command"]
    if not (proposal["state"] == "pending" and proposal["hash"] == original["hash"]
            and proposal["expires"] > datetime.now(timezone.utc).timestamp()
            and command["_origin_run_id"] == run_id and command["action"] == "update_work_package"
            and command["arguments"] == expected and command["auto_execute"] is False
            and progress["actor_id"] == 19 and progress["project_id"] == 5 and progress["state"] == "REVIEW"):
        raise ValueError("PENDING_OWN_PROPOSAL_WITH_EXACT_ORIGIN_REQUIRED")
    return {"status": "PENDING_EXACT_HUMAN_APPROVAL", "run_id": run_id, "trace_id": progress["trace_id"],
            "actor_id": 19, "project_id": 5, "native_id": 370, "proposal_id": proposal["id"],
            "proposal_hash": proposal["hash"],
            "expires_at_utc": datetime.fromtimestamp(proposal["expires"], timezone.utc).isoformat(),
            "action": command["action"], "arguments": expected, "before_description": draft["before_description"],
            "after_description": draft["after_description"], "native_operations": 1, "native_writes": 0,
            "effect": "Append one test marker to Task370 description; expected version1->2, count333 unchanged; no comment/create/transition/delete/credential/Staging action",
            "approval": "NOT_YET_GRANTED", "model_calls": 5, "http_attempts": len(receipts),
            "observed_tokens": sum(u["totalTokenCount"] for u in result["usage"]),
            "trace_events": trace["total"], "context_provenance": provenance,
            "verification_after_approval": ["Native exact description/version readback", "same run/trace audit correlation",
                "durable RAG job verification and marker citation", "duplicate decision returns original receipt without another Native write"],
            "rollback": "Original description retained here; restoration requires a new PM-approved mutation with fresh version. No automatic business-write rollback."}


def confirm_scenario_f(operator_dir, approved_hash):
    """Execute only the exact owner-approved test proposal, once through WF06."""
    from datetime import datetime, timezone
    from gateway.native import Native
    from gateway.store import canonical, digest
    repo = Path(__file__).resolve().parents[3]
    preview = json.loads((repo / "docs/ai/CODEX_SCENARIO_F_APPROVAL_PREVIEW.json").read_text(encoding="utf-8"))
    if approved_hash != preview["proposal_hash"] or preview["proposal_id"] != "19efe751-4af7-4cb4-96f0-0836ee504948":
        raise ValueError("EXACT_OWNER_APPROVED_PROPOSAL_REQUIRED")
    private = Path(operator_dir)
    attempt = private / "scenario-f-confirm-attempt.json"
    if attempt.exists():
        raise ValueError("CONFIRMATION_ALREADY_ATTEMPTED_READ_RECEIPTS_ONLY")
    secrets = json.loads((private / "incident-secrets.json").read_text(encoding="utf-8"))
    credentials = json.loads((private.parent.parent / "gateway/credentials.json").read_text(encoding="utf-8"))
    native = Native("http://127.0.0.1:8088", credentials["19"], 5)
    if native.identity(19)["role"] != "PM":
        raise ValueError("GENUINE_PM_REQUIRED")
    item = native.package(370)
    if not (item["lockVersion"] == 1 and item["description"]["raw"] == preview["before_description"]
            and item["_links"]["author"]["href"] == "/api/v3/users/19"
            and item["_links"]["assignee"]["href"] == "/api/v3/users/19"):
        raise ValueError("TEST_RESOURCE_CHANGED")
    packages = native.packages()
    if digest(canonical(sorted((p["id"], p["lockVersion"]) for p in packages))) != "e72e02fa7914513540816b2c6484a254aadb24232db11966b13524e7df1e79a5":
        raise ValueError("NATIVE_BASELINE_CHANGED")
    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": "Bearer " + next(v for k, v in secrets.items() if ":PM_TOKEN" in k),
               "X-QLDAPM-Webhook-Token": secrets["webhook_secret.json:webhook_token"]}
    response = session.get("http://127.0.0.1:8090/api/v1/proposals/" + preview["proposal_id"],
                           headers=headers, timeout=30, allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError("PROPOSAL_READ_FAILED")
    proposal = response.json()["result"]
    if not (proposal["state"] == "pending" and proposal["hash"] == approved_hash
            and digest(canonical({"actor": 19, "command": proposal["command"]})) == approved_hash
            and proposal["expires"] > datetime.now(timezone.utc).timestamp()
            and proposal["command"]["arguments"] == preview["arguments"]
            and proposal["command"]["_origin_run_id"] == preview["run_id"]):
        raise ValueError("PROPOSAL_CHANGED_OR_EXPIRED")
    with attempt.open("x", encoding="utf-8") as stream:
        json.dump({"proposal_id": proposal["id"], "approved_hash": approved_hash,
                   "human_approval": "Exact proposal/hash explicitly approved in the current user reply",
                   "attempted_at": datetime.now(timezone.utc).isoformat()}, stream)
    response = session.post("http://127.0.0.1:5679/webhook/qldapm-execute-mutation", headers=headers,
        json={"proposal_id": proposal["id"], "decision": "approve", "hash": approved_hash},
        timeout=90, allow_redirects=False)
    receipt = {"http_status": response.status_code, "body": response.json()}
    (private / "scenario-f-confirm-response.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    if response.status_code != 200:
        raise RuntimeError("CONFIRMATION_HTTP_" + str(response.status_code) + "_RECONCILE_NO_RETRY")
    return {"status": "PM_DECISION_ACCEPTED_READBACK_REQUIRED", "proposal_id": proposal["id"],
            "proposal_hash": approved_hash, "run_id": preview["run_id"], "http_status": response.status_code}


def verify_scenario_f(operator_dir):
    """Reconcile known successful approval; duplicate decision is an explicit consumption test."""
    import subprocess
    from gateway.native import Native
    from gateway.store import canonical, digest
    repo = Path(__file__).resolve().parents[3]
    private = Path(operator_dir)
    preview = json.loads((repo / "docs/ai/CODEX_SCENARIO_F_APPROVAL_PREVIEW.json").read_text(encoding="utf-8"))
    confirmed = json.loads((private / "scenario-f-confirm-response.json").read_text(encoding="utf-8"))
    if confirmed["http_status"] != 200:
        raise ValueError("KNOWN_SUCCESS_REQUIRED_NO_AMBIGUOUS_WRITE_RETRY")
    secrets = json.loads((private / "incident-secrets.json").read_text(encoding="utf-8"))
    credentials = json.loads((private.parent.parent / "gateway/credentials.json").read_text(encoding="utf-8"))
    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": "Bearer " + next(v for k, v in secrets.items() if ":PM_TOKEN" in k),
               "X-QLDAPM-Webhook-Token": secrets["webhook_secret.json:webhook_token"]}
    response = session.get("http://127.0.0.1:8090/api/v1/proposals/" + preview["proposal_id"],
                           headers=headers, timeout=30, allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError("PROPOSAL_READBACK_FAILED")
    proposal = response.json()["result"]
    (private / "scenario-f-confirm-proposal-readback.json").write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")
    job = proposal.get("knowledge_sync") or {}
    if job.get("state") != "verified":
        return {"status": "PARTIAL", "proposal_id": proposal["id"], "proposal_state": proposal["state"],
                "rag_state": job.get("state"), "next_action": "Read durable job status; do not repeat Native mutation"}
    expected_origin = {"proposal_id": proposal["id"], "run_id": preview["run_id"], "trace_id": preview["trace_id"]}
    if not (proposal["state"] == "done" and proposal["lifecycle"] == "VERIFIED_COMPLETED"
            and proposal["hash"] == preview["proposal_hash"] and proposal["result"]["origin"] == expected_origin
            and job["native_id"] == 370 and job["result"]["lock_version"] == 2
            and job["result"]["vector_indexed"] is True and job["result"]["canonical"]["vector_indexed"] is True
            and job["result"]["canonical"]["lock_version"] == 2
            and all(job["result"][k] == preview[k] for k in ("run_id", "trace_id"))):
        raise ValueError("NATIVE_RAG_ORIGIN_PROOF_FAILED")
    native = Native("http://127.0.0.1:8088", credentials["19"], 5)
    item = native.package(370)
    packages = native.packages()
    versions = sorted((p["id"], p["lockVersion"]) for p in packages)
    if not (item["lockVersion"] == 2 and item["description"]["raw"] == preview["after_description"]
            and item["subject"] == "[CODEX TEST] Main Native E2E fdae09fb"
            and item["_links"]["status"]["title"] == "NEW" and len(packages) == 333
            and digest(canonical([(i, v) for i, v in versions if i != 370])) ==
                "57d64095ee75637a873e5d2b337c5d51d03ca82e2eb3bf2e4f2cf947cfa3c863"):
        raise ValueError("NATIVE_EXACT_READBACK_OR_ORIGINAL_332_CHANGED")
    activities = native.collection("/api/v3/work_packages/370/activities")
    comments = [a["id"] for a in activities if (a.get("comment") or {}).get("raw")]
    if comments != [1023]:
        raise ValueError("UNEXPECTED_TEST_COMMENT_CHANGE")
    marker = preview["after_description"].rsplit("\n", 1)[-1]
    response = session.post("http://127.0.0.1:8090/api/v1/commands", headers=headers,
        json={"action": "knowledge_search", "arguments": {"query": marker, "native_ids": [370], "limit": 10}},
        timeout=45, allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError("RAG_SEARCH_READBACK_FAILED")
    search = response.json()["result"]
    hits = [h for h in search["items"] if h["native_id"] == 370 and h["lock_version"] == 2
            and h["citation"] == "/work_packages/370" and marker in h["snippet"]]
    if not hits:
        raise ValueError("FRESH_MARKER_CITATION_MISSING")
    # Only after confirmed readback: a consumed proposal must refuse a second execution.
    response = session.post("http://127.0.0.1:5679/webhook/qldapm-execute-mutation", headers=headers,
        json={"proposal_id": proposal["id"], "decision": "approve", "hash": proposal["hash"]},
        timeout=45, allow_redirects=False)
    duplicate = {"http_status": response.status_code, "body": response.json()}
    (private / "scenario-f-duplicate-decision.json").write_text(json.dumps(duplicate), encoding="utf-8")
    if response.status_code != 409 or "CONSUMED_PROPOSAL" not in duplicate["body"].get("error", ""):
        raise ValueError("CONSUMED_PROPOSAL_NOT_REJECTED")
    fresh = Native("http://127.0.0.1:8088", credentials["19"], 5).package(370)
    if fresh["lockVersion"] != 2 or fresh["description"]["raw"] != preview["after_description"]:
        raise ValueError("DUPLICATE_DECISION_CHANGED_NATIVE")
    code = ("import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row;"
            "print(json.dumps([dict(r) for r in d.execute(\"SELECT action,target,outcome,run_id,trace_id FROM audit WHERE run_id=? ORDER BY at\",(" + repr(preview["run_id"]) + ",))]))")
    audit = json.loads(subprocess.check_output(["docker", "exec", "qldapm-ai-gateway-1", "python", "-c", code]))
    if not audit or any(r["trace_id"] != preview["trace_id"] for r in audit):
        raise ValueError("AUDIT_TRACE_MISMATCH")
    (private / "scenario-f-correlated-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return {"status": "PASS", "scope": "Scenario F exact approved description update through WF03/WF06",
            **expected_origin, "proposal_hash": proposal["hash"], "lifecycle": proposal["lifecycle"],
            "native_id": 370, "native_lock_version": 2, "native_count": 333,
            "native_fingerprint": digest(canonical(versions)), "original_332_unchanged": True,
            "comment_ids": comments, "native_writes": 1, "sync_job_id": job["id"], "sync_state": job["state"],
            "sync_attempts": job["attempts"], "actor_and_canonical_vectors_verified": True,
            "marker_citation": hits[0], "audit_records_same_trace": len(audit),
            "audit_actions": sorted(set(r["action"] for r in audit)),
            "duplicate_decision": {"status": "PASS_POLICY_ENFORCED", "http_status": 409,
                "behavior": "Consumed proposal rejected; existing original receipt readable separately; Native version remains2"},
            "model_calls": preview["model_calls"], "observed_tokens": preview["observed_tokens"],
            "limitation": "Typed analysis remains historical REVIEW; Native/RAG completion is proved by proposal/job/audit, not a fresh model analysis of version2"}


def qualify_workflow_boundaries(operator_dir):
    """Exercise all webhook transport gates and interactive authentication, without business writes."""
    import subprocess
    private = Path(operator_dir)
    secrets = json.loads((private / "incident-secrets.json").read_text(encoding="utf-8"))
    session = requests.Session()
    session.trust_env = False
    owner = {"Cookie": "n8n-auth=" + next(v for k, v in secrets.items() if k.endswith(":COOKIE"))}
    ingress = {"X-QLDAPM-Webhook-Token": secrets["webhook_secret.json:webhook_token"]}
    pm = {"Authorization": "Bearer " + next(v for k, v in secrets.items() if ":PM_TOKEN" in k)}
    code = ("import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);"
            "print(json.dumps({t:d.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in "
            "['gemini_call_receipts','gemini_usage','proposals','knowledge_sync']}))")
    def counts():
        return json.loads(subprocess.check_output(["docker", "exec", "qldapm-ai-gateway-1", "python", "-c", code]))
    before = counts()
    response = session.get("http://127.0.0.1:5679/rest/workflows", headers=owner, timeout=30, allow_redirects=False)
    response.raise_for_status()
    rows = response.json()["data"]
    report = {"checks": {}, "model_starts": 0, "native_writes": 0,
              "scope": "Webhook transport/authentication and explicit Native index adapters",
              "business_acceptance": "PARTIAL"}
    webhook_urls = {}
    for row in rows:
        code_name = row["name"].split(":", 1)[0]
        if code_name not in {f"WF{i:02}" for i in range(1, 17)}:
            continue
        response = session.get("http://127.0.0.1:5679/rest/workflows/" + row["id"], headers=owner, timeout=30, allow_redirects=False)
        response.raise_for_status()
        workflow = response.json()["data"]
        trigger = next(n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.webhook")
        url = "http://127.0.0.1:5679/webhook/" + trigger["parameters"]["path"]
        webhook_urls[code_name] = url
        response = session.post(url, json={}, timeout=30, allow_redirects=False)
        report["checks"][code_name + "_transport"] = {"http_status": response.status_code,
            "status": "PASS_POLICY_ENFORCED" if response.status_code == 403 else "FAILED"}
        if code_name not in {"WF07", "WF16"}:
            response = session.post(url, headers=ingress, json={"id": 370}, timeout=30, allow_redirects=False)
            report["checks"][code_name + "_caller_auth"] = {"http_status": response.status_code,
                "status": "PASS_POLICY_ENFORCED" if response.status_code in {401, 403} else "FAILED"}
    qa_url = "http://127.0.0.1:5679/webhook/qldapm-qa-gate"
    for workflow, body in (("WF09", {"id": 370}), ("WF10", {})):
        response = session.post(webhook_urls[workflow], headers={**pm, **ingress}, json=body,
                                timeout=45, allow_redirects=False)
        result = response.json().get("result") or {}
        passed = response.status_code == 200
        if workflow == "WF09":
            passed = passed and result.get("id") == 370 and result.get("lockVersion") == 2 and "business_comments" in result
        else:
            passed = passed and all(isinstance(result.get(k), list) and result[k] for k in ("types", "statuses", "priorities"))
        report["checks"][workflow + "_native_read"] = {"status": "PASS" if passed else "FAILED",
            "http_status": response.status_code, "result_keys": sorted(result)}
    for workflow in ("WF01", "WF02", "WF13"):
        # Stable test request IDs reuse the same index receipt across resumed qualifications.
        request_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "qldapm-main-20261023-native370-v2-" + workflow))
        url = webhook_urls[workflow]
        payload = {"id": 370, "request_id": request_id}
        response = session.post(url, headers={**pm, **ingress}, json=payload, timeout=60, allow_redirects=False)
        result = response.json().get("result") or {}
        passed = response.status_code == 200 and result.get("native_id") == 370 and result.get("lock_version") == 2 and result.get("vector_indexed") is True
        report["checks"][workflow + "_explicit_native_index"] = {"status": "PASS" if passed else "FAILED",
            "http_status": response.status_code, "native_id": result.get("native_id"), "lock_version": result.get("lock_version"),
            "vector_indexed": result.get("vector_indexed"), "ingestion_status": result.get("status")}
        for suffix, bad in (("no_target", {"request_id": request_id}),
                            ("no_file_access", {**payload, "file_path": "forbidden.txt"}),
                            ("no_delete", {**payload, "operation": "delete"})):
            response = session.post(url, headers={**pm, **ingress}, json=bad, timeout=30, allow_redirects=False)
            report["checks"][workflow + "_" + suffix] = {"status": "PASS_POLICY_ENFORCED" if response.status_code == 422 else "FAILED", "http_status": response.status_code}
    for name, body, expected in (("explicit_target", {"id": 370, "approved": True, "role": "PM"}, 422),
                                 ("missing_target", {}, 422), ("boolean_target", {"id": True}, 422)):
        response = session.post(qa_url, headers={**pm, **ingress}, json=body, timeout=30, allow_redirects=False)
        passed = response.status_code == expected
        evidence = {"http_status": response.status_code}
        if name == "explicit_target":
            evidence["error"] = response.json().get("error")
            passed = passed and evidence["error"] == "CUSTOM_GATE_UNSUPPORTED_IN_NATIVE_MODE"
            report["qa_business_status"] = "BLOCKED_CUSTOM_GATE_UNSUPPORTED_IN_NATIVE_MODE"
        if expected == 200 and passed:
            gate = response.json()["result"]
            passed = (gate["id"] == 370 and gate["lockVersion"] == 2 and isinstance(gate["gate"], dict)
                      and isinstance(gate["transitions"], list) and "transition_permitted" not in gate)
            evidence.update(native_id=gate["id"], lock_version=gate["lockVersion"],
                            transitions=gate["transitions"], evidence_keys=sorted(gate["gate"].get("evidence", {})))
        report["checks"]["WF11_" + name] = {"status": ("PASS_POLICY_ENFORCED" if name == "explicit_target" else "PASS") if passed else "FAILED", **evidence}
    after = counts()
    report["checks"]["unchanged_provider_proposals_jobs"] = {
        "status": "PASS" if before == after else "FAILED", "before": before, "after": after}
    report["status"] = "PASS" if all(c["status"].startswith("PASS") for c in report["checks"].values()) else "FAILED"
    return report


def qualify_owner_access(operator_dir):
    """Real Main actor matrix; local analysis and unexecuted proposals only."""
    from datetime import datetime, timezone
    from gateway.native import Native
    from gateway.store import canonical, digest
    private = Path(operator_dir)
    tokens = json.loads((private / 'qualification-bearers.json').read_text(encoding='utf-8'))
    roles = {18:'AI_SYSTEM_OWNER',19:'PM',20:'BA',21:'BE',22:'FE',23:'QA'}
    report = {'observed_at':datetime.now(timezone.utc).isoformat(),'status':'RUNNING','actors':{},
              'checks':{},'native_mutations':0,'model_calls':0}
    session = requests.Session()
    session.trust_env = False
    def call(actor, action, arguments=None, key=None):
        return session.post('http://127.0.0.1:8090/api/v1/commands',
            headers={'Authorization':'Bearer '+tokens[str(actor)]},
            json={'action':action,'arguments':arguments or {},'idempotency_key':key,'auto_execute':False},
            timeout=60,allow_redirects=False)
    def check(name, passed, evidence):
        report['checks'][name] = {'status':'PASS' if passed else 'FAILED','evidence':evidence}
        if not passed:
            (private/'owner-regression-partial.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            raise AssertionError('OWNER_REGRESSION_'+name)
    run_ids = {}
    for actor, role in roles.items():
        response = call(actor,'identity')
        who = response.json().get('result') or {}
        check(str(actor)+'_identity',response.status_code==200 and who.get('user_id')==actor and who.get('role')==role,
              {'http_status':response.status_code,'actor':who.get('user_id'),'role':who.get('role')})
        report['actors'][str(actor)] = {'role':role,'native_identity':who,'route':'OWN_ACTOR_BEARER_AND_FRESH_NATIVE_KEY'}
        response = call(actor,'get_permissions')
        tools = {t['name']:t for t in response.json()['result']['tools']}
        check(str(actor)+'_permissions',tools['update_work_package']['allowed']==(actor in (18,19))
              and tools['owner_inspect']['allowed']==(actor==18) and tools['get_gate']['allowed'] is False,
              {name:tools[name] for name in ('update_work_package','owner_inspect','get_gate')})
        if actor in (18,19):
            response = call(actor,'get_configuration')
            configuration = response.json().get('result') or {}
            check(str(actor)+'_configuration_read',response.status_code==200 and configuration.get('project_id')==5,
                  {'http_status':response.status_code,'project_id':configuration.get('project_id')})
        response = session.get('http://127.0.0.1:8090/api/v1/control-center/state?limit=2',
            headers={'Authorization':'Bearer '+tokens[str(actor)]},timeout=60,allow_redirects=False)
        center = response.json().get('result') or {}
        check(str(actor)+'_control_center',response.status_code==200 and center.get('actor_id')==actor,
              {'http_status':response.status_code,'actor_id':center.get('actor_id')})
        response = call(actor,'knowledge_search',{'query':'CODEX_SCENARIO_F_RAG_20261023_aa98fa81d022','native_ids':[370],'limit':3})
        hits = (response.json().get('result') or {}).get('items',[])
        check(str(actor)+'_rag',response.status_code==200 and bool(hits) and all(h['native_id']==370 and h['lock_version']==2 for h in hits),
              {'http_status':response.status_code,'native_refs':[{'id':h['native_id'],'version':h['lock_version']} for h in hits]})
        response = call(actor,'start_ai_run',{'engine':'supervisor','prompt':'PM/Supervisor điều phối BA FE BE QA phân tích công việc #370. Không tạo, không cập nhật, không chuyển trạng thái; chỉ phân tích nguồn hiện tại.','run_class':'agent'},
                        'owner-role-regression-local-v1-'+str(actor))
        check(str(actor)+'_local_supervisor_start',response.status_code==200,{'http_status':response.status_code})
        run_ids[actor] = response.json()['result']['id']
    deadline = time.monotonic()+180
    waiting = set(run_ids)
    while waiting and time.monotonic()<deadline:
        for actor in list(waiting):
            response = call(actor,'get_ai_run',{'id':run_ids[actor]})
            run = response.json().get('result') or {}
            if run.get('state') in {'done','failed_or_unknown'}:
                result = run.get('result') or {}
                check(str(actor)+'_local_supervisor_result',response.status_code==200 and run['state']=='done'
                      and result.get('model_used') is False and result.get('source_ids')==[370],
                      {'http_status':response.status_code,'run_id':run_ids[actor],'state':run['state'],
                       'status':result.get('status'),'model_used':result.get('model_used'),'source_ids':result.get('source_ids')})
                waiting.remove(actor)
        if waiting: time.sleep(2)
    check('six_local_runs_completed',not waiting,{'run_ids':run_ids,'waiting':sorted(waiting)})
    foreign = '80c74d03-5c9d-4471-9d9a-09c6749c645d'
    for actor in (18,20,21,22,23):
        response = call(actor,'get_agent_trace',{'id':foreign})
        check(str(actor)+'_ordinary_cross_actor_trace_denied',response.status_code==403,{'http_status':response.status_code})
    response = call(18,'owner_inspect',{'kind':'trace','subject_actor':19,'id':foreign,'limit':2})
    inspected = response.json().get('result') or {}
    check('owner_explicit_audited_trace',response.status_code==200 and inspected.get('viewer_actor')==18
          and inspected.get('subject_actor')==19 and inspected.get('can_execute_as_subject') is False,
          {'http_status':response.status_code,'viewer_actor':inspected.get('viewer_actor'),'subject_actor':inspected.get('subject_actor')})
    for actor in (19,20,21,22,23):
        response = call(actor,'owner_inspect',{'kind':'history','subject_actor':18})
        check(str(actor)+'_owner_capability_forgery_denied',response.status_code==403,{'http_status':response.status_code})
    for name, headers, command in (
        ('anonymous',{}, {'action':'identity'}),
        ('invalid_bearer',{'Authorization':'Bearer invalid'}, {'action':'identity'}),
        ('forged_owner',{'Authorization':'Bearer '+tokens['20']},{'action':'identity','admin':True,'owner':True,'actor_id':18})):
        response = session.post('http://127.0.0.1:8090/api/v1/commands',headers=headers,json=command,timeout=30,allow_redirects=False)
        check(name,response.status_code in ({401,403} if name!='forged_owner' else {403,422}),{'http_status':response.status_code})
    response = call(18,'update_work_package',{'id':370,'lock_version':2,'changes':{'description':'Owner qualification DRAFT ONLY; must not be executed.'}},'owner-access-proposal-v1')
    proposal = response.json().get('result') or {}
    check('owner_proposal_only',response.status_code==200 and proposal.get('state')=='pending'
          and proposal['command']['auto_execute'] is False,{'http_status':response.status_code,'proposal_id':proposal.get('id'),'state':proposal.get('state')})
    response = session.post('http://127.0.0.1:8090/api/v1/proposals/'+proposal['id']+'/decision',
        headers={'Authorization':'Bearer '+tokens['18']},json={'decision':'approve','hash':'0'*64},timeout=30,allow_redirects=False)
    check('owner_altered_hash_denied',response.status_code==409,{'http_status':response.status_code})
    response = call(18,'reject_proposal',{'id':proposal['id'],'hash':proposal['hash']},'owner-access-reject-v1')
    check('owner_rejects_own_draft',response.status_code==200 and response.json()['result']['state']=='rejected',
          {'http_status':response.status_code,'proposal_id':proposal['id']})
    credentials = json.loads((private.parent.parent/'gateway/credentials.json').read_text(encoding='utf-8'))
    native = Native('http://127.0.0.1:8088',credentials['18'],5)
    packages = native.packages()
    fingerprint = digest(canonical(sorted((p['id'],p['lockVersion']) for p in packages)))
    check('native333_and_task370_untouched',len(packages)==333 and fingerprint=='49de9ea96d6280a27ed09bc2d83499fc241968f74c32ed0ed6d14a48ced5388c',
          {'count':len(packages),'fingerprint':fingerprint})
    report.update(status='PASS',run_ids=run_ids,owner_draft_proposal_id=proposal['id'],owner_native_write_e2e='NOT_TESTED_NO_NEW_APPROVAL')
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Main read-only API qualification; never starts the legacy live E2E implicitly")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--read-only", action="store_true")
    modes.add_argument("--plan-only", action="store_true")
    modes.add_argument("--plan-status", action="store_true")
    modes.add_argument("--approve-proposal", metavar="EXACT_HUMAN_APPROVED_HASH")
    modes.add_argument("--verify-scenario-f", action="store_true")
    modes.add_argument("--workflow-boundaries", action="store_true")
    modes.add_argument("--owner-access", action="store_true")
    parser.add_argument("--operator-dir", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = (qualify_owner_access(args.operator_dir) if args.owner_access else
              qualify_workflow_boundaries(args.operator_dir) if args.workflow_boundaries else
              verify_scenario_f(args.operator_dir) if args.verify_scenario_f else
              confirm_scenario_f(args.operator_dir, args.approve_proposal) if args.approve_proposal else
              run_readonly(args.operator_dir) if args.read_only else
              read_scenario_f_plan(args.operator_dir) if args.plan_status else start_scenario_f_plan(args.operator_dir))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.read_only or args.workflow_boundaries or args.owner_access:
        print(json.dumps({"status": result["status"], "checks": len(result["checks"]),
                          "failed": [k for k, v in result["checks"].items() if v["status"] == "FAILED"]}))
        sys.exit(0 if result["status"] == "PASS" else 1)
    print(json.dumps(result))

"""Visible Supervisor -> explicit PM proposal/reject/confirm -> Native receipt on owned clone."""
import json
import time
import uuid
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

from tests.post_deployment_browser_uat import RUN, PRIVATE
from tests.remaining_browser_uat import PRIVATE as FIXTURE, BASE, GATEWAY, ASSISTANT, otp
from jira_sync_backup import inspect


def main():
    info = inspect("qldapm-rd-gateway-20261018")
    assert info["Config"]["Labels"]["qldapm.qualification"] == "remaining-20261018"
    assert not (FIXTURE / "state/gemini.key").exists()
    data = json.loads((FIXTURE / "fixture-credentials.json").read_text())
    pm = next(x for x in data["users"] if x["role"] == "PM")
    be = next(x for x in data["users"] if x["role"] == "BE")
    report = {"scope": "OWNED_NATIVE_FIXTURE_ONLY", "method": "REAL_BROWSER_AND_NATIVE_API", "image": info["Image"], "checks": []}

    def check(case, ok, actual=None):
        report["checks"].append({"id": case, "status": "PASS" if ok else "FAIL", "actual": actual})
        (RUN / "fixture-business-chain.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        assert ok, case

    def command(account, action, args=None):
        return httpx.post(GATEWAY + "/api/v1/commands", headers={"Authorization": "Bearer " + account["gateway_token"]},
                          json={"action": action, "arguments": args or {}, "idempotency_key": uuid.uuid4().hex}, trust_env=False, timeout=90).json()["result"]

    def native(path):
        return httpx.get(BASE + path, auth=("apikey", pm["token"]), trust_env=False, timeout=60).json()

    def tool(page, action, args):
        page.goto(BASE + ASSISTANT, wait_until="domcontentloaded", timeout=90000)
        page.locator("details.qldapm-ai-tools > summary").click()
        form = page.locator("form:has(select#tool)")
        form.locator("select#tool").select_option(action)
        form.locator("textarea#arguments").fill(json.dumps(args))
        form.locator("input[type=submit]").click()
        page.wait_for_load_state("domcontentloaded")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(); page = ctx.new_page()
        page.goto(BASE + "/login"); page.locator("#username").fill(pm["login"]); page.locator("#password").fill(pm["password"])
        page.locator("form:has(#username) button[type=submit]").click(); page.locator("#otp").wait_for()
        if time.time() % 30 > 26:
            time.sleep(4)
        page.locator("#otp").fill(otp(pm["totp_secret"])); page.locator("input[type=submit][name=login]").click(); page.wait_for_load_state("domcontentloaded")
        check("CHAIN-LOGIN", ctx.request.get(BASE + "/api/v3/users/me").json()["id"] == pm["id"])
        page.goto(BASE + ASSISTANT, wait_until="domcontentloaded", timeout=90000)
        form = page.locator("form:has(select#engine)"); form.locator("#engine").select_option("supervisor")
        form.locator("#prompt").fill("Phân tích nghiệp vụ công việc #" + str(data["work_package_id"]))
        form.locator("input[type=submit]").click(); page.wait_for_load_state("domcontentloaded")
        page.locator("summary").filter(has_text="Execution plan").wait_for(timeout=180000)
        check("CHAIN-SUPERVISOR-OUTPUT", "Phân tích local trên" in page.locator(".qldapm-ai-result").last.inner_text())
        types = command(pm, "get_project_options")["types"]
        task_type = next(x["id"] for x in types if x["name"] == "Task")
        source = "post-uat-" + uuid.uuid4().hex[:16]
        args = {"source_id": source, "subject": "POST-UAT isolated business fixture", "type_id": task_type,
                "description": "postuatmemo unique knowledge login acceptance criterion"}
        count_path = "/api/v3/projects/3/work_packages?pageSize=1"
        before = native(count_path)["total"]
        tool(page, "create_work_package", args)
        pending = page.locator('form[action$="/reject"]')
        rejected_id = pending.locator('input[name="proposal_id"]').input_value()
        check("CHAIN-PREVIEW-NO-WRITE", native(count_path)["total"] == before and page.locator("#ai-preview-title").count() == 1)
        pending.locator("input[type=submit]").click(); page.wait_for_load_state("domcontentloaded")
        state = command(pm, "get_proposal", {"id": rejected_id})
        check("CHAIN-REJECT-VISIBLE", state["state"] == "rejected" and native(count_path)["total"] == before and page.locator('form[action$="/confirm"]').count() == 0)
        tool(page, "create_work_package", args)
        proposal_id = page.locator('form[action$="/confirm"] input[name="proposal_id"]').input_value()
        page.locator('form[action$="/confirm"] input[type=submit]').click(); page.wait_for_load_state("domcontentloaded")
        link = page.get_by_role("link", name="Mở công việc", exact=True)
        identifier = int(link.get_attribute("href").rstrip("/").split("/")[-1])
        actual = native("/api/v3/work_packages/" + str(identifier))
        check("CHAIN-APPROVE-NATIVE-READBACK", actual["subject"] == args["subject"] and native(count_path)["total"] == before + 1, {"native_id": identifier, "lock_version": actual["lockVersion"]})
        check("CHAIN-VISIBLE-RECEIPT", "OpenProject đã xác nhận kết quả" in page.locator(".qldapm-ai-result").last.inner_text())
        history = command(pm, "get_action_history")
        check("CHAIN-AUDIT-RECEIPT", any(x["id"] == proposal_id and x["state"] == "done" for x in history["proposals"]) and bool(history["audit"]))
        page.screenshot(path=str(PRIVATE / "fixture-pm-native-receipt.png"), full_page=True)
        page.goto(BASE + ASSISTANT, wait_until="domcontentloaded", timeout=90000)
        form = page.locator("form:has(#native_id)"); form.locator("#native_id").fill(str(identifier)); form.get_by_role("button", name="Lập / cập nhật chỉ mục").click(); page.wait_for_load_state("domcontentloaded")
        search = page.locator("form:has(#knowledge_query)"); search.locator("#knowledge_query").fill("postuatmemo"); search.locator("input[type=submit]").click(); page.wait_for_load_state("domcontentloaded")
        check("CHAIN-KNOWLEDGE-UI-CITATION", page.locator('article a[href="/work_packages/' + str(identifier) + '"]').count() == 1)
        check("CHAIN-KNOWLEDGE-ACTOR-ACL", command(be, "knowledge_search", {"query": "postuatmemo"})["items"] == [])
        report["new_fixture_id"] = identifier
        report["supervisor_to_canonical_conversion"] = "EXPLICIT_PM_TOOL_FORM; no automatic conversion or approval"
        report["passed"] = True
        (RUN / "fixture-business-chain.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
    print(json.dumps({"fixture_chain_passed": True, "checks": len(report["checks"]), "native_fixture_id": identifier}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        (PRIVATE / "fixture-chain-error.txt").write_text(str(error), encoding="utf-8")
        print(json.dumps({"failed": True, "error_type": type(error).__name__, "details_private": True}))
        raise SystemExit(1)

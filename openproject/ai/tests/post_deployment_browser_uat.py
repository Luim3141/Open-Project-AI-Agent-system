"""Read-only business UAT on serving Staging; credentials and screenshots stay private.

Supervisor submissions write only local runtime/audit metadata, never Native business
objects. All Native mutations and knowledge ingestion belong to the separate clone.
"""
import datetime
import json
import os
from pathlib import Path
import re
import time

from playwright.sync_api import sync_playwright

from jira_sync_backup import command


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / json.loads((ROOT / "docs/ai-multi-agent-upgrade/post-deployment-uat/LATEST.json").read_text())["run"]
CONFIG = json.loads((RUN / "run.json").read_text())
PRIVATE = Path(CONFIG["private"])
RUNTIME = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
BASE = CONFIG["url"]
ASSISTANT = "/projects/qldapm-local/qldapm-ai"


def current_codes():
    # Read existing devices without exporting seeds or creating credentials.
    ruby = '''require "json"
result=[]
ActiveRecord::Base.transaction do
 ActiveRecord::Base.connection.execute("SET TRANSACTION READ ONLY")
 [6,7,8,9,10].each do |id|
  device=TwoFactorAuthentication::Device::Totp.find_by!(user_id:id,active:true,default:true)
  base=Time.now.to_i/30*30
  result << {id:id,codes:(0..60).map{|i| at=base+i*30; [at,device.totp.at(at)]}.to_h}
 end
end
puts "UAT_PRIVATE_CODES="+JSON.generate(result)
'''
    raw = command(["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"], ruby.encode(), timeout=120).decode()
    packet = next(line.split("=", 1)[1] for line in raw.splitlines() if line.startswith("UAT_PRIVATE_CODES="))
    return {row["id"]: row["codes"] for row in json.loads(packet)}


def main():
    accounts = json.loads((RUNTIME / "stage/accounts.json").read_text())["users"]
    native = json.loads((RUNTIME / "stage/test-credentials.json").read_text())
    codes = current_codes()
    report = {"scope": "SERVING_STAGING_FIVE_EXISTING_USERS", "method": "PLAYWRIGHT_CHROMIUM_EDGE_AND_SESSION_NATIVE_API",
              "images": CONFIG["images"], "checks": [], "native_business_mutations": 0, "provider_calls": 0}
    output = RUN / "serving-browser.json"

    def record(case, expected, ok, actual=None, method="UI_REAL"):
        report["checks"].append({"id": case, "expected": expected, "status": "PASS" if ok else "FAIL", "method": method, "actual": actual})
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"case": case, "status": "PASS" if ok else "FAIL"}), flush=True)

    order = {"PM": 0, "BA-PM": 1, "FE": 2, "BE": 3, "QA": 4}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        for account in sorted(accounts, key=lambda a: order[a["role"]]):
            role = account["role"].replace("BA-PM", "BA")
            actor = native[account["role"]]["id"]
            ctx = browser.new_context(viewport={"width": 1280, "height": 850})
            page = ctx.new_page()
            authenticated = False
            try:
                page.goto(BASE + "/login", wait_until="domcontentloaded", timeout=60000)
                page.locator("#username").fill(account["login"])
                page.locator("#password").fill(account["password"])
                page.locator("form:has(#username) button[type=submit]").click()
                page.locator("#otp").wait_for(timeout=20000)
                if time.time() % 30 > 26:
                    time.sleep(4)
                page.locator("#otp").fill(codes[actor][str(int(time.time() // 30) * 30)])
                page.locator("input[type=submit][name=login]").click()
                page.wait_for_load_state("domcontentloaded")
                me = ctx.request.get(BASE + "/api/v3/users/me")
                authenticated = me.status == 200 and me.json().get("id") == actor
                record(role + "-LOGIN-TOTP", "Existing Native actor authenticated", authenticated, {"actor": actor, "http": me.status})
                if not authenticated:
                    continue
                for name, path in [("DASHBOARD", "/projects/qldapm-local"), ("WORK-PACKAGES", "/projects/qldapm-local/work_packages"), ("BACKLOG", "/projects/qldapm-local/backlogs")]:
                    response = page.goto(BASE + path, wait_until="domcontentloaded", timeout=90000)
                    page.locator("body").wait_for()
                    page.wait_for_timeout(1500)
                    if name == "WORK-PACKAGES":
                        try:
                            page.wait_for_function("Array.from(document.querySelectorAll('a[href]')).some(e=>/^\\/work_packages\\/\\d+(?:[/?]|$)/.test(e.getAttribute('href')))", timeout=20000)
                        except Exception:
                            pass  # Record the observed empty UI as FAIL without skipping the other pages.
                    body = page.locator("body").inner_text()
                    links = page.locator("a[href]").evaluate_all("es=>es.map(e=>e.getAttribute('href')).filter(h=>/^\\/work_packages\\/\\d+(?:[/?]|$)/.test(h))")
                    record(role + "-" + name, "Native page is accessible with visible content", response.status == 200 and "Internal server error" not in body and page.locator("#username").count() == 0 and (name != "WORK-PACKAGES" or bool(links)),
                           {"http": response.status, "headings": page.locator("h1,h2").all_text_contents()[:5], "native_item_links": len(links), "empty_sprint_notice": bool(re.search("no sprint|no backlog|chưa có sprint", body, re.I))})
                    page.screenshot(path=str(PRIVATE / (role + "-" + name.lower() + ".png")), full_page=True)
                response = page.goto(BASE + ASSISTANT, wait_until="domcontentloaded", timeout=120000)
                record(role + "-ASSISTANT", "Actual Assistant loads", response.status == 200 and page.locator("select#engine").count() == 1)
                record(role + "-CONTROL-CENTER", "Control Center reads runtime state", page.locator("#control-center-title").count() == 1 and "Run history" in page.locator("body").inner_text())
                tools = page.locator("select#tool option").evaluate_all("es=>es.map(e=>e.value)")
                forbidden = {"list_code", "read_code", "write_code", "request_test", "propose_operation"}
                record(role + "-BUSINESS-NO-OPERATOR", "Business tool selector has no operator/shell tools", bool(tools) and not forbidden.intersection(tools), {"forbidden_present": sorted(forbidden.intersection(tools))})
                write_tools = {"create_work_package", "update_work_package", "transition", "change_gate"}
                record(role + "-PM-WRITE-UI", "Only PM sees Native business write tools", write_tools <= set(tools) if role == "PM" else not write_tools.intersection(tools), {"role": role})
                record(role + "-SECOND-BRAIN-UI", "Knowledge search/index form is visible", page.locator("#knowledge-title").count() == 1 and page.locator("#knowledge_query").count() == 1)
                # An existing input is read only. No write scope or Gemini consent.
                item = ctx.request.get(BASE + "/api/v3/work_packages/38")
                record(role + "-NATIVE-READ", "Existing input is visible through real session API", item.status == 200, {"http": item.status}, "API_REAL_SESSION")
                if item.status != 200:
                    continue
                form = page.locator("form:has(select#engine)")
                form.locator("#engine").select_option("supervisor")
                form.locator("#prompt").fill("Phân tích chỉ đọc và soạn gợi ý cho công việc #38; không ghi thay đổi.")
                form.locator("input[type=submit]").click()
                page.wait_for_load_state("domcontentloaded")
                page.locator("summary").filter(has_text="Execution plan").wait_for(state="visible", timeout=180000)
                text = page.locator(".qldapm-ai-result").last.inner_text()
                run_match = re.search(r"[?&]run_id=([a-f0-9-]+)", page.url)
                run_id = run_match.group(1) if run_match else None
                record(role + "-SUPERVISOR-VISIBLE-RESULT", "Browser submission finishes with visible report and plan", "Phân tích local trên" in text and "Execution plan" in text and bool(run_id), {"run_id": run_id})
                record(role + "-SOURCE-CITATION", "Result includes clickable Native input provenance", page.locator('.qldapm-ai-result a[href="/work_packages/38"]').count() >= 1)
                page.screenshot(path=str(PRIVATE / (role + "-supervisor-result.png")), full_page=True)
                page.get_by_text("Chi tiết kỹ thuật / receipt", exact=True).click()
                record(role + "-LOCAL-NO-MODEL-RECEIPT", "Actual visible receipt states model_used=false", '"model_used": false' in page.locator(".qldapm-ai-result").last.inner_text())
                page.goto(BASE + "/logout", wait_until="domcontentloaded", timeout=60000)
                denied = ctx.request.get(BASE + "/api/v3/users/me")
                record(role + "-LOGOUT", "Logout revokes browser session", denied.status == 401, {"http": denied.status}, "UI_AND_API_REAL")
                page.goto(BASE + ASSISTANT, wait_until="domcontentloaded", timeout=60000)
                record(role + "-SESSION-DENIED", "Assistant redirects logged-out actor to login", page.locator("#username").count() == 1)
            except Exception as error:
                record(role + "-FLOW", "Full browser role flow completes", False, {"error_type": type(error).__name__, "details_private": True})
                (PRIVATE / (role + "-failure.txt")).write_text(str(error), encoding="utf-8")
                if authenticated:
                    (PRIVATE / (role + "-failure.html")).write_text(page.content(), encoding="utf-8")
            finally:
                ctx.close()
        browser.close()
    report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["passed"] = all(c["status"] == "PASS" for c in report["checks"])
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

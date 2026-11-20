"""Live Staging Browser UAT using Playwright.
Tests Execution Monitor UI/UX on real serving Staging instance via Quick Tunnel.
Bounded execution, per-test timeouts, real-time heartbeat progress logging,
zero live Gemini calls, zero database writes.
"""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai"
EVIDENCE_DIR = ROOT / "docs/ai-multi-agent-upgrade/execution-monitor"
SCREENSHOT_DIR = EVIDENCE_DIR / "LIVE_STAGING_SCREENSHOTS"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = EVIDENCE_DIR / "LIVE_STAGING_PROGRESS.json"

def get_quick_tunnel_url():
    import urllib.request
    with urllib.request.urlopen("http://localhost:18090/", timeout=10) as resp:
        text = resp.read().decode("utf-8")
        m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", text)
        if not m:
            raise RuntimeError("Quick tunnel URL not found on localhost:18090")
        return m.group(0)

def get_staging_totp_codes():
    ruby_script = (
        'require "json"\n'
        'ActiveRecord::Base.transaction do\n'
        '  ActiveRecord::Base.connection.execute("SET TRANSACTION READ ONLY")\n'
        '  d = TwoFactorAuthentication::Device::Totp.find_by!(user_id: 7, active: true, default: true)\n'
        '  at = Time.now.to_i / 30 * 30\n'
        '  puts "PRIVATE_CODES=" + JSON.generate((0..60).map { |i| t = at + i * 30; [t, d.totp.at(t)] }.to_h)\n'
        'end\n'
    )
    res = subprocess.run(
        ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
        input=ruby_script,
        capture_output=True,
        text=True,
        timeout=60,
        check=True
    )
    for line in res.stdout.splitlines():
        if line.startswith("PRIVATE_CODES="):
            return json.loads(line.split("=", 1)[1])
    raise RuntimeError("Failed to retrieve TOTP codes from staging container")

def get_gateway_job_count():
    py_code = (
        "import sqlite3\n"
        "d = sqlite3.connect('file:/state/gateway.sqlite?mode=ro', uri=True)\n"
        "print(d.execute('SELECT count(*) FROM jobs').fetchone()[0])\n"
    )
    res = subprocess.run(
        ["docker", "exec", "-i", "qldapm-ai-stage-staging-gateway-1", "python", "-c", py_code],
        capture_output=True,
        text=True,
        timeout=30,
        check=True
    )
    return int(res.stdout.strip())

def run_uat():
    start_suite_time = time.time()
    base_url = get_quick_tunnel_url()
    print(f"Targeting Live Staging at: {base_url}")

    initial_job_count = get_gateway_job_count()
    print(f"Gateway initial job count: {initial_job_count} (zero new calls expected)")

    accounts = json.loads((RUNTIME / "stage/accounts.json").read_text(encoding="utf-8"))["users"]
    pm_account = next(x for x in accounts if x["role"] == "PM")
    codes = get_staging_totp_codes()

    viewports = [
        ("1920x1080", 1920, 1080),
        ("1440x900", 1440, 900),
        ("1366x768", 1366, 768),
        ("768x1024", 768, 1024),
        ("375x812", 375, 812),
    ]

    checks = []
    progress_data = {
        "suite_start": datetime.datetime.now().isoformat(),
        "url": base_url,
        "total_checks": 0,
        "passed_checks": 0,
        "failed_checks": 0,
        "checks": []
    }

    def record_check(name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        item = {
            "name": name,
            "status": status,
            "details": details,
            "timestamp": datetime.datetime.now().isoformat()
        }
        checks.append(item)
        progress_data["checks"].append(item)
        progress_data["total_checks"] = len(checks)
        if passed:
            progress_data["passed_checks"] += 1
        else:
            progress_data["failed_checks"] += 1
        
        # Write heartbeat progress to disk immediately
        try:
            PROGRESS_FILE.write_text(json.dumps(progress_data, indent=2), encoding="utf-8")
        except Exception:
            pass

        print(f"[{status}] {name} {details}", flush=True)
        if not passed:
            raise AssertionError(f"Check failed: {name} - {details}")

    browser = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=True)
            ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = ctx.new_page()
            page.set_default_timeout(30000)

            # 1. PM Authentication
            print("\n--- 1. Authenticating PM on Live Staging ---")
            page.goto(base_url + "/login", timeout=45000)
            page.locator("#username").fill(pm_account["login"])
            page.locator("#password").fill(pm_account["password"])
            page.locator("form:has(#username) button[type=submit]").click()
            page.locator("#otp").wait_for(timeout=20000)

            if time.time() % 30 > 26:
                time.sleep(4)
            t_key = str(int(time.time() // 30) * 30)
            otp = codes[t_key]
            page.locator("#otp").fill(otp)
            page.locator("input[type=submit][name=login]").click()
            page.wait_for_load_state("domcontentloaded", timeout=30000)

            me_resp = ctx.request.get(base_url + "/api/v3/users/me")
            me_data = me_resp.json()
            record_check("STAGING-PM-AUTH", me_data.get("id") == 7, f"Actor ID: {me_data.get('id')}")

            # 2. History Page & Reference Execution Run
            print("\n--- 2. Checking Executions History ---")
            history_resp = ctx.request.get(base_url + "/projects/qldapm-local/qldapm-ai/executions.json")
            record_check("STAGING-HISTORY-JSON-STATUS-200", history_resp.status == 200)
            items = history_resp.json().get("items", [])
            print(f"Found {len(items)} executions in Staging history.")
            record_check("STAGING-HISTORY-HAS-RUNS", len(items) > 0, f"Count: {len(items)}")

            preferred_ids = ["38fdb479-5566-4a18-b2da-6a9cf15aad3c", "7d528511-c957-40b1-bd1e-c6fe7dd28650"]
            target_run_id = None
            for pid in preferred_ids:
                if any(x["run_id"] == pid for x in items):
                    target_run_id = pid
                    break
            if not target_run_id:
                target_run_id = sorted(items, key=lambda x: len(x.get("agents", [])), reverse=True)[0]["run_id"]
            print(f"Selected reference run_id: {target_run_id}")

            cookies = ctx.cookies()

            # 3. Viewport Testing & Visual QA across 5 viewports
            print("\n--- 3. Testing 5 Viewports & Capturing Screenshots ---")
            for vp_name, w, h in viewports:
                print(f"\n>> Viewport: {vp_name} ({w}x{h})")
                v_ctx = browser.new_context(viewport={"width": w, "height": h})
                v_ctx.add_cookies(cookies)
                p = v_ctx.new_page()
                p.set_default_timeout(30000)

                # History Page
                p.goto(base_url + "/projects/qldapm-local/qldapm-ai/executions", timeout=30000)
                p.wait_for_load_state("networkidle", timeout=30000)
                has_history_row = p.locator(".em-history-request").count() > 0
                record_check(f"HISTORY-PAGE-LOAD-{vp_name}", has_history_row)
                p.screenshot(path=str(SCREENSHOT_DIR / f"staging_history_{vp_name}.png"), full_page=False)

                # Detail Page
                p.goto(base_url + f"/projects/qldapm-local/qldapm-ai/executions/{target_run_id}", timeout=30000)
                p.wait_for_load_state("networkidle", timeout=30000)
                p.wait_for_timeout(1000)

                node_count = p.locator(".em-node").count()
                assignment_count = p.locator('.em-edge[data-kind="ASSIGNMENT"]').count()
                dependency_count = p.locator('.em-edge[data-kind="DEPENDENCY"]').count()

                record_check(f"DETAIL-GRAPH-NODES-{vp_name}", node_count == 6, f"nodes={node_count}")
                record_check(f"DETAIL-ASSIGNMENT-EDGES-{vp_name}", assignment_count == 4, f"assignments={assignment_count}")
                record_check(f"DETAIL-DEPENDENCY-EDGES-{vp_name}", dependency_count == 6, f"dependencies={dependency_count}")

                p.screenshot(path=str(SCREENSHOT_DIR / f"staging_detail_{vp_name}.png"), full_page=False)

                # Horizontal overflow check on mobile
                if w <= 768:
                    no_overflow = p.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                    record_check(f"MOBILE-NO-OVERFLOW-{vp_name}", no_overflow)

                # Node click & tab check (for primary viewports)
                if vp_name in ["1920x1080", "1440x900", "375x812"]:
                    nodes = p.locator(".em-node").evaluate_all(
                        "(list) => list.map(n => ({ id: n.dataset.node, name: n.querySelector('.em-node-name')?.textContent.trim() }))"
                    )
                    ba_node = next((n for n in nodes if "BA" in (n.get("name") or "")), nodes[1])
                    p.locator(f'[data-node="{ba_node["id"]}"]').click()
                    p.locator("#em-detail-title").filter(has_text=ba_node["name"]).wait_for(timeout=10000)
                    title = p.locator("#em-detail-title").inner_text()
                    record_check(f"NODE-CLICK-BA-{vp_name}", ba_node["name"] in title, f"Title: {title}")
                    p.screenshot(path=str(SCREENSHOT_DIR / f"staging_detail_agent_ba_{vp_name}.png"), full_page=False)

                    # Tab switching using verified IDs from execution.html.erb
                    p.locator("#tab-btn-output").click()
                    p.wait_for_timeout(200)
                    record_check(f"TAB-OUTPUT-VISIBLE-{vp_name}", p.locator("#tab-panel-output").is_visible())

                    p.locator("#tab-btn-fields").click()
                    p.wait_for_timeout(200)
                    fields_count = p.locator("#em-agent-fields dt").count()
                    record_check(f"TAB-FIELDS-COUNT-{vp_name}", fields_count >= 10, f"Fields: {fields_count}")

                    p.locator("#tab-btn-overview").click()
                    p.wait_for_timeout(200)
                    record_check(f"TAB-OVERVIEW-VISIBLE-{vp_name}", p.locator("#tab-panel-overview").is_visible())

                v_ctx.close()

            # 4. Agent Selection Matrix (BA, DEV, QA, Reviewer) on 1920x1080
            print("\n--- 4. Checking Agent Selection (BA, DEV, QA, Reviewer) ---")
            d_ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
            d_ctx.add_cookies(cookies)
            dp = d_ctx.new_page()
            dp.set_default_timeout(30000)
            dp.goto(base_url + f"/projects/qldapm-local/qldapm-ai/executions/{target_run_id}", timeout=30000)
            dp.wait_for_load_state("networkidle", timeout=30000)
            dp.wait_for_timeout(1000)

            all_nodes = dp.locator(".em-node").evaluate_all(
                "(list) => list.map(n => ({ id: n.dataset.node, name: n.querySelector('.em-node-name')?.textContent.trim() }))"
            )
            for expected_role in ["BA", "Developer", "QA", "Reviewer"]:
                matched = next((n for n in all_nodes if expected_role in (n.get("name") or "")), None)
                record_check(f"NODE-EXISTS-{expected_role.upper()}", matched is not None, f"Found: {matched}")
                if matched:
                    dp.locator(f'[data-node="{matched["id"]}"]').click()
                    dp.locator("#em-detail-title").filter(has_text=matched["name"]).wait_for(timeout=10000)
                    cur_title = dp.locator("#em-detail-title").inner_text()
                    record_check(f"NODE-SELECT-{expected_role.upper()}", matched["name"] in cur_title, f"Detail Title: {cur_title}")
                    dp.screenshot(path=str(SCREENSHOT_DIR / f"staging_agent_{expected_role.lower()}.png"), full_page=False)

            # 5. Timeline & Replay
            print("\n--- 5. Checking Timeline & Replay ---")
            timeline_items = dp.locator("#em-timeline li").count()
            record_check("STAGING-TIMELINE-EVENTS-EXIST", timeline_items > 0, f"Count: {timeline_items}")

            has_replay_bar = dp.locator("#em-replay").count() > 0 or dp.locator("#em-play").count() > 0
            record_check("STAGING-REPLAY-CONTROLS-EXIST", has_replay_bar)
            dp.screenshot(path=str(SCREENSHOT_DIR / "staging_timeline_replay.png"), full_page=False)

            # 6. Structured Final Report
            print("\n--- 6. Checking Structured Final Report ---")
            final_report_visible = dp.locator("#em-final-title").is_visible()
            record_check("STAGING-FINAL-REPORT-VISIBLE", final_report_visible)
            report_sections = dp.locator(".em-final-segment, .em-final-segmented-view, #em-final-segmented, #em-final-output").count()
            record_check("STAGING-FINAL-REPORT-STRUCTURED", report_sections > 0, f"Report blocks: {report_sections}")
            dp.screenshot(path=str(SCREENSHOT_DIR / "staging_final_report.png"), full_page=False)

            # 7. Presentation Mode Toggle & Esc Exit
            print("\n--- 7. Testing Presentation Mode ---")
            pres_btn = dp.locator("#em-presentation-toggle")
            record_check("STAGING-PRESENTATION-BUTTON-EXISTS", pres_btn.count() == 1)
            pres_btn.click()
            dp.wait_for_timeout(300)
            is_pres_active = dp.locator("#execution-monitor").evaluate("(e) => e.classList.contains('em-presentation-mode')")
            record_check("STAGING-PRESENTATION-ACTIVE", is_pres_active)
            dp.screenshot(path=str(SCREENSHOT_DIR / "staging_presentation_mode.png"), full_page=False)

            dp.keyboard.press("Escape")
            dp.wait_for_timeout(300)
            is_pres_exited = not dp.locator("#execution-monitor").evaluate("(e) => e.classList.contains('em-presentation-mode')")
            record_check("STAGING-PRESENTATION-ESC-EXIT", is_pres_exited)

            # 8. Dark Mode Theme Check (Verify Light Primer Theme preserved, No Navy mismatch)
            print("\n--- 8. Testing OS Dark Mode Theme Preservation ---")
            dark_ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
            dark_ctx.add_cookies(cookies)
            dark_p = dark_ctx.new_page()
            dark_p.goto(base_url + f"/projects/qldapm-local/qldapm-ai/executions/{target_run_id}", timeout=30000)
            dark_p.wait_for_load_state("networkidle", timeout=30000)
            dark_p.wait_for_timeout(1000)

            bg_color = dark_p.locator(".em-card").first.evaluate("(e) => getComputedStyle(e).backgroundColor")
            print(f"Card computed background under OS dark mode: {bg_color}")
            is_clean_theme = bg_color in ["rgb(255, 255, 255)", "#ffffff", "rgba(255, 255, 255, 1)"]
            record_check("STAGING-THEME-NO-NAVY-MISMATCH", is_clean_theme, f"Background: {bg_color}")
            dark_p.screenshot(path=str(SCREENSHOT_DIR / "staging_os_dark_mode_preserved.png"), full_page=False)
            dark_ctx.close()

            # 9. Security & Access Control
            print("\n--- 9. Testing Security & Access Control ---")
            anon_ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            anon_p = anon_ctx.new_page()
            anon_resp = anon_p.goto(base_url + f"/projects/qldapm-local/qldapm-ai/executions/{target_run_id}", timeout=30000)
            is_auth_gated = (anon_resp.status in [401, 403, 302]) or ("/login" in anon_p.url)
            record_check("STAGING-UNAUTH-ACCESS-GATED", is_auth_gated, f"Status: {anon_resp.status}, URL: {anon_p.url}")
            anon_ctx.close()

            d_ctx.close()
            ctx.close()

            # 10. Ledger Check (Zero live Gemini API calls during UAT)
            final_job_count = get_gateway_job_count()
            zero_new_jobs = (final_job_count == initial_job_count)
            record_check("STAGING-ZERO-GEMINI-CALLS-VERIFIED", zero_new_jobs, f"Initial: {initial_job_count}, Final: {final_job_count}")

    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass

    duration = time.time() - start_suite_time
    print("\n=======================================================")
    print(f"ALL {len(checks)} STAGING PLAYWRIGHT CHECKS PASSED (100%) in {duration:.1f}s")
    print("=======================================================")
    
    report_file = EVIDENCE_DIR / "LIVE_STAGING_UAT_RESULTS.json"
    report_data = {
        "suite_completion": datetime.datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "target_url": base_url,
        "reference_run_id": target_run_id,
        "total_checks": len(checks),
        "passed": sum(1 for c in checks if c["status"] == "PASS"),
        "failed": sum(1 for c in checks if c["status"] == "FAIL"),
        "checks": checks
    }
    report_file.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print(f"Detailed UAT Report written to: {report_file}")
    return checks

if __name__ == "__main__":
    results = run_uat()

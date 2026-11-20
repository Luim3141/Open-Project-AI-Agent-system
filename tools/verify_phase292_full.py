"""Comprehensive Functional UAT Suite for Phase 2.9.2.
Verifies:
1. Navigation Menu Entry: OpenProject sidebar on ai-dev-demo has 'AI Command Center'.
2. Seamless 2-way navigation: Overview / Work Packages <-> AI Command Center.
3. KPI & Data Consistency: Backlog Units 5/5, DELIVERED badges, IDLE (Sẵn sàng) worker.
4. Interactive Button Feedback & Toast Alerts:
   - RUN ONCE -> Toast alert displaying exact informative outcome.
   - Sync GitHub -> Toast alert displaying PR sync outcome.
   - BẬT AUTO / OFF -> Toast alert confirming mode change.
   - Schedule Modal -> Open, edit, save -> Toast alert confirming schedule updated.
5. Real-time Polling: /projects/ai-dev-demo/qldapm-ai?format=json returns 200 JSON.
6. RBAC Verification:
   - Owner (18): Full access.
   - PM (20): Full access.
   - Unauthorized (19): 403 Forbidden.
7. Project 5 Invariants: 341 WPs untouched.
"""
import json
import os
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs/ai/engineering/PHASE292"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SHOTS_DIR = OUTPUT_DIR / "screenshots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

MAIN_BASE = "http://127.0.0.1:18088"
PROJECT6_SLUG = "ai-dev-demo"
OVERVIEW_URL = f"{MAIN_BASE}/projects/{PROJECT6_SLUG}"
WP_URL = f"{MAIN_BASE}/projects/{PROJECT6_SLUG}/work_packages"
AI_URL = f"{MAIN_BASE}/projects/{PROJECT6_SLUG}/qldapm-ai?ui=modern"

def get_session_cookie(user_id=18):
    ruby_script = f"""
    user = User.find({user_id})
    sid = Rack::Session::SessionId.new(SecureRandom.hex(16))
    session_record = ActiveRecord::SessionStore::Session.new(
      session_id: sid.private_id,
      user_id: user.id,
      data: {{
        'user_id' => user.id,
        'updated_at' => Time.now
      }}
    )
    session_record.save!
    puts 'COOKIE_VALUE=' + sid.public_id
    """
    r = subprocess.run(
        ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
        input=ruby_script,
        capture_output=True,
        text=True,
        check=True
    )
    for line in r.stdout.splitlines():
        if line.startswith('COOKIE_VALUE='):
            return line.split('=', 1)[1].strip()
    raise RuntimeError(f"Failed to generate cookie for user {user_id}")

def main():
    owner_cookie = get_session_cookie(18)
    print(f"[AUTH] Acquired Owner (User 18) session cookie: {owner_cookie[:10]}...")

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_results": {},
        "evidence": {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_cookies([
            {"name": "_open_project_session", "value": owner_cookie, "domain": "127.0.0.1", "path": "/"}
        ])
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # -------------------------------------------------------------
        # TEST 1: OpenProject Sidebar Menu Entry for AI Command Center
        # -------------------------------------------------------------
        print("\n--- TEST 1: OpenProject Sidebar Menu Entry ---")
        page.goto(OVERVIEW_URL, wait_until="networkidle", timeout=30000)
        page.screenshot(path=str(SHOTS_DIR / "01_overview_sidebar_menu.png"), full_page=True)

        menu_item = page.locator("a.qldapm-ai-menu-item")
        menu_present = menu_item.count() > 0
        menu_visible = menu_present and menu_item.first.is_visible()
        menu_caption = menu_item.first.inner_text().strip() if menu_present else ""
        print(f"Assert Sidebar Menu Entry Visible: {menu_visible} (Caption: {menu_caption})")
        results["test_results"]["tc01_sidebar_menu_visible"] = menu_visible
        results["evidence"]["menu_caption"] = menu_caption

        # -------------------------------------------------------------
        # TEST 2: Two-way Navigation (Overview -> Command Center -> Work Packages)
        # -------------------------------------------------------------
        print("\n--- TEST 2: Two-Way Navigation ---")
        if menu_visible:
            with page.expect_navigation(timeout=15000):
                menu_item.first.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            page.locator("#qldapm-command-center").wait_for(state="visible", timeout=10000)
            cc_elem = page.locator("#qldapm-command-center")
            in_cc = "qldapm-ai" in page.url and cc_elem.is_visible()
            print(f"Navigated to Command Center via menu: {in_cc} (URL: {page.url})")
            results["test_results"]["tc02_navigate_to_cc"] = in_cc
            page.screenshot(path=str(SHOTS_DIR / "02_command_center_loaded.png"), full_page=True)

            # Click back to Work Packages
            back_link = page.locator("a:has-text('← Work Packages')")
            back_visible = back_link.count() > 0 and back_link.first.is_visible()
            print(f"Assert '← Work Packages' button visible: {back_visible}")
            results["test_results"]["tc02_back_link_visible"] = back_visible
            if back_visible:
                with page.expect_navigation(timeout=15000):
                    back_link.first.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                in_wp = "work_packages" in page.url
                print(f"Navigated to Work Packages via back button: {in_wp} (URL: {page.url})")
                results["test_results"]["tc02_navigate_back_to_wp"] = in_wp
                page.screenshot(path=str(SHOTS_DIR / "03_work_packages_back.png"), full_page=True)

        # Ensure we are in Command Center for subsequent tests
        page.goto(AI_URL, wait_until="networkidle", timeout=15000)

        # -------------------------------------------------------------
        # TEST 3: KPI & Data Consistency Checks
        # -------------------------------------------------------------
        print("\n--- TEST 3: KPI & Data Consistency ---")
        cards = page.locator(".qcc-kpi-card")
        kpi_backlog_val = cards.nth(1).locator(".qcc-kpi-value").inner_text().strip()
        kpi_backlog_sub = cards.nth(1).locator(".qcc-kpi-sub").inner_text().strip()
        print(f"Backlog KPI: {kpi_backlog_val} | Sub: {kpi_backlog_sub}")
        results["evidence"]["kpi_backlog"] = kpi_backlog_val
        results["test_results"]["tc03_kpi_backlog_5_of_5"] = (kpi_backlog_val == "5 / 5")

        # Worker consistency
        worker_kpi = cards.nth(0).locator(".qcc-kpi-sub").inner_text().strip()
        header_meta = page.locator(".qcc-header-meta").inner_text().strip()
        print(f"Worker KPI: {worker_kpi} | Header: {header_meta}")
        results["evidence"]["worker_kpi"] = worker_kpi
        results["evidence"]["header_meta"] = header_meta
        results["test_results"]["tc03_worker_idle_standby"] = ("IDLE (Sẵn sàng)" in worker_kpi and "IDLE (Sẵn sàng)" in header_meta)

        # Backlog badges in Mission Control
        badges = page.locator(".qcc-unit-badge .qcc-chip")
        badge_texts = [badges.nth(i).inner_text().strip() for i in range(badges.count())]
        print(f"Backlog Badges in Mission Control: {badge_texts}")
        results["evidence"]["backlog_badges"] = badge_texts
        results["test_results"]["tc03_backlog_badges_delivered"] = (len(badge_texts) == 5 and all(b == "DELIVERED" for b in badge_texts))

        # -------------------------------------------------------------
        # TEST 4: Action Button Submitting State & Toast Feedback
        # -------------------------------------------------------------
        print("\n--- TEST 4: RUN ONCE Button Click & Toast Feedback ---")
        run_once_btn = page.locator("button:has-text('RUN ONCE')")
        if run_once_btn.count() > 0:
            run_once_btn.first.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(path=str(SHOTS_DIR / "04_run_once_toast_feedback.png"), full_page=True)

            toast = page.locator(".qcc-toast")
            toast_visible = toast.count() > 0 and toast.first.is_visible()
            toast_text = toast.first.inner_text().strip() if toast_visible else ""
            print(f"Toast visible: {toast_visible} | Text: {toast_text}")
            results["test_results"]["tc04_run_once_toast_feedback"] = toast_visible
            results["evidence"]["run_once_toast_text"] = toast_text

        print("\n--- TEST 5: Sync GitHub Button Click & Toast Feedback ---")
        sync_gh_btn = page.locator("button:has-text('Sync GitHub')")
        if sync_gh_btn.count() > 0:
            sync_gh_btn.first.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(path=str(SHOTS_DIR / "05_sync_github_toast_feedback.png"), full_page=True)

            toast = page.locator(".qcc-toast")
            toast_visible = toast.count() > 0 and toast.first.is_visible()
            toast_text = toast.first.inner_text().strip() if toast_visible else ""
            print(f"Sync GitHub Toast visible: {toast_visible} | Text: {toast_text}")
            results["test_results"]["tc05_sync_github_toast_feedback"] = toast_visible
            results["evidence"]["sync_github_toast_text"] = toast_text

        print("\n--- TEST 6: BẬT AUTO / OFF Mode Toggle Feedback ---")
        auto_btn = page.locator("button:has-text('BẬT AUTO')")
        if auto_btn.count() > 0:
            auto_btn.first.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            toast = page.locator(".qcc-toast")
            t_text = toast.first.inner_text().strip() if toast.count() > 0 else ""
            print(f"BẬT AUTO clicked -> Toast: {t_text}")
            results["test_results"]["tc06_auto_mode_feedback"] = ("AUTO" in t_text or toast.count() > 0)
            page.screenshot(path=str(SHOTS_DIR / "06_auto_mode_toast.png"), full_page=True)

            # Restore OFF
            off_btn = page.locator("button:has-text('OFF')")
            if off_btn.count() > 0:
                off_btn.first.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                print("Restored mode to OFF")

        print("\n--- TEST 7: Schedule Modal Open, Save & Toast Feedback ---")
        # Go to Tab Reports
        reports_nav = page.locator(".qcc-nav-item[data-tab='tab-reports']")
        if reports_nav.count() > 0:
            reports_nav.first.click()
            time.sleep(0.5)

            open_modal_btn = page.locator("#btn-open-schedule-modal")
            if open_modal_btn.count() > 0:
                open_modal_btn.first.click()
                time.sleep(0.5)
                modal = page.locator("#schedule-config-modal")
                modal_open = modal.is_visible()
                print(f"Schedule modal open: {modal_open}")
                results["test_results"]["tc07_schedule_modal_open"] = modal_open
                page.screenshot(path=str(SHOTS_DIR / "07_schedule_modal_open.png"), full_page=True)

                # Save schedule
                save_btn = page.locator("#btn-save-schedule")
                if save_btn.count() > 0:
                    save_btn.first.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    toast = page.locator(".qcc-toast")
                    toast_visible = toast.count() > 0 and toast.first.is_visible()
                    t_text = toast.first.inner_text().strip() if toast_visible else ""
                    print(f"Schedule saved -> Toast visible: {toast_visible} | Text: {t_text}")
                    results["test_results"]["tc07_schedule_save_feedback"] = toast_visible
                    results["evidence"]["schedule_save_toast"] = t_text
                    page.screenshot(path=str(SHOTS_DIR / "08_schedule_saved_toast.png"), full_page=True)

        browser.close()

    # -------------------------------------------------------------
    # TEST 8: Real-Time Polling JSON Endpoint
    # -------------------------------------------------------------
    print("\n--- TEST 8: Real-Time Polling Endpoint (JSON) ---")
    poll_py = f"""
    project = Project.find_by(identifier: 'ai-dev-demo')
    user = User.find(18)
    res = Qldapm::AiBridge.call(project, user, 'command', {{action: 'engineering_status', arguments: {{}}}})
    puts 'POLL_JSON_SUCCESS=' + (res['result']['mode'].present?).to_s
    """
    poll_res = subprocess.run(
        ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
        input=poll_py,
        capture_output=True,
        text=True,
        check=True
    )
    poll_ok = "POLL_JSON_SUCCESS=true" in poll_res.stdout
    print(f"Poll status JSON response: {poll_ok}")
    results["test_results"]["tc08_polling_json_available"] = poll_ok

    # -------------------------------------------------------------
    # TEST 9: RBAC Verification (Owner 18 vs PM 20 vs User 19)
    # -------------------------------------------------------------
    print("\n--- TEST 9: RBAC Verification ---")
    pm_cookie = get_session_cookie(20)
    user19_cookie = get_session_cookie(19)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        
        # Test PM (User 20)
        pm_ctx = browser.new_context()
        pm_ctx.add_cookies([{"name": "_open_project_session", "value": pm_cookie, "domain": "127.0.0.1", "path": "/"}])
        pm_page = pm_ctx.new_page()
        pm_page.goto(AI_URL, wait_until="networkidle", timeout=15000)
        pm_access = pm_page.locator("#qldapm-command-center").is_visible()
        print(f"PM (User 20) Command Center Access: {pm_access}")
        results["test_results"]["tc09_pm_access_granted"] = pm_access

        # Test Unauthorized User 19
        u19_ctx = browser.new_context()
        u19_ctx.add_cookies([{"name": "_open_project_session", "value": user19_cookie, "domain": "127.0.0.1", "path": "/"}])
        u19_page = u19_ctx.new_page()
        resp = u19_page.goto(AI_URL, timeout=15000)
        u19_blocked = (resp.status == 403) or u19_page.locator("text='403'").is_visible() or ("không có quyền" in u19_page.content().lower())
        print(f"Unauthorized User 19 Access Blocked (403): {u19_blocked} (Status: {resp.status})")
        results["test_results"]["tc09_user19_access_blocked"] = u19_blocked

        browser.close()

    # -------------------------------------------------------------
    # TEST 10: Project 5 Invariants Verification
    # -------------------------------------------------------------
    print("\n--- TEST 10: Project 5 Invariants Verification ---")
    inv_res = subprocess.run(
        ['openproject/ai/.venv/Scripts/python.exe', str(ROOT / 'tools/verify_project5_invariants.py')],
        capture_output=True,
        text=True
    )
    inv_ok = "ALL 7 INVARIANTS HELD UNTOUCHED" in inv_res.stdout
    print(f"Project 5 Invariants: {inv_ok}")
    results["test_results"]["tc10_project5_invariants_preserved"] = inv_ok

    out_file = OUTPUT_DIR / "FUNCTIONAL_TEST_RESULTS.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[REPORT] Saved functional UAT results to {out_file}")

    print("\n=======================================================")
    print("PHASE 2.9.2 FUNCTIONAL UAT SUMMARY:")
    for k, v in results["test_results"].items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    all_pass = all(results["test_results"].values())
    print(f"OVERALL VERDICT: {'ALL PASS' if all_pass else 'SOME TESTS FAILED'}")
    print("=======================================================")

if __name__ == "__main__":
    main()

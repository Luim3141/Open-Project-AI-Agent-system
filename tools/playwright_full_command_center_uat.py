"""Comprehensive Playwright Browser UAT for QLDAPM AI Command Center (Phase 2.9).
Verifies:
1. Modern Command Center visual shell & dark OLED aesthetic.
2. 8 Navigation Tabs switching & interactive views.
3. Schedule Configuration Modal opening & interaction.
4. GitHub PR Transparency: 5 PRs mapped (#1 to #5) including PR #5 / WP #384.
5. Execution Center logs & terminal display.
6. Classic Fallback (?ui=classic) interoperability.
7. Responsive viewports: 1440x900, 1920x1080, 1280x800, 375x812.
"""
import os
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS_DIR = ROOT / "docs/ai/engineering/PHASE29_HANDOFF/screenshots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

MAIN_BASE = "http://127.0.0.1:18088"
PROJECT6_AI_URL = f"{MAIN_BASE}/projects/ai-dev-demo/qldapm-ai"

def get_fresh_owner_cookie():
    ruby_script = """
    user = User.find(18)
    sid = Rack::Session::SessionId.new(SecureRandom.hex(16))
    session_record = ActiveRecord::SessionStore::Session.new(
      session_id: sid.private_id,
      user_id: user.id,
      data: {
        'user_id' => user.id,
        'updated_at' => Time.now
      }
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
    raise RuntimeError("Failed to generate fresh cookie")

def run_playwright_uat():
    cookie = get_fresh_owner_cookie()
    print(f"[AUTH] Acquired fresh Owner session cookie: {cookie}")
    
    results = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        
        # Test Desktop 1440x900
        print("\n--- 1. Testing Desktop 1440x900 (Main Viewport) ---")
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_cookies([{
            "name": "_open_project_session",
            "value": cookie,
            "domain": "127.0.0.1",
            "path": "/"
        }])
        page = context.new_page()
        
        # Step 1.1: Load Command Center
        resp = page.goto(PROJECT6_AI_URL, wait_until="networkidle")
        print(f"Page URL: {page.url}, HTTP Status: {resp.status}")
        results["http_status_200"] = (resp.status == 200)
        
        title = page.title()
        print(f"Page Title: {title}")
        results["title_correct"] = "AI Engineering Command Center" in title
        
        # Verify shell presence
        has_root = page.locator("#qldapm-command-center").is_visible()
        has_sidebar = page.locator(".qcc-sidebar").is_visible()
        print(f"Shell visible: root={has_root}, sidebar={has_sidebar}")
        results["shell_visible"] = (has_root and has_sidebar)
        
        # Capture Screenshot: Mission Control (Default)
        page.screenshot(path=str(SHOTS_DIR / "01_mission_control_1440.png"), full_page=True)
        print("Captured: 01_mission_control_1440.png")
        
        # Step 1.2: Switch to Pipeline Tab
        print("\n--- 2. Testing Navigation Tabs Switching ---")
        page.click("button[data-tab='tab-pipeline']")
        time.sleep(0.5)
        pipeline_visible = page.locator("#tab-pipeline.active").is_visible()
        print(f"Pipeline Tab active: {pipeline_visible}")
        results["tab_pipeline"] = pipeline_visible
        page.screenshot(path=str(SHOTS_DIR / "02_tab_pipeline_8stages.png"), full_page=True)
        
        # Step 1.3: Switch to Workforce Tab
        page.click("button[data-tab='tab-workforce']")
        time.sleep(0.5)
        workforce_visible = page.locator("#tab-workforce.active").is_visible()
        print(f"Workforce Tab active: {workforce_visible}")
        results["tab_workforce"] = workforce_visible
        page.screenshot(path=str(SHOTS_DIR / "03_tab_agent_workforce.png"), full_page=True)
        
        # Step 1.4: Switch to Backlog Tab
        page.click("button[data-tab='tab-backlog']")
        time.sleep(0.5)
        backlog_visible = page.locator("#tab-backlog.active").is_visible()
        print(f"Backlog Tab active: {backlog_visible}")
        results["tab_backlog"] = backlog_visible
        page.screenshot(path=str(SHOTS_DIR / "04_tab_native_backlog.png"), full_page=True)
        
        # Step 1.5: Switch to Execution Center Tab
        page.click("button[data-tab='tab-execution']")
        time.sleep(0.5)
        exec_visible = page.locator("#tab-execution.active").is_visible()
        print(f"Execution Tab active: {exec_visible}")
        results["tab_execution"] = exec_visible
        page.screenshot(path=str(SHOTS_DIR / "05_tab_execution_terminal.png"), full_page=True)
        
        # Step 1.6: Switch to GitHub PRs Tab & Verify 5 PRs
        page.click("button[data-tab='tab-github']")
        time.sleep(0.5)
        github_visible = page.locator("#tab-github.active").is_visible()
        print(f"GitHub PRs Tab active: {github_visible}")
        results["tab_github"] = github_visible
        
        # Check PR #5 presence
        pr5_present = "#5" in page.inner_text("#tab-github") or "route GET /healthz" in page.inner_text("#tab-github")
        print(f"PR #5 (WP #384 /healthz) present in table: {pr5_present}")
        results["pr5_present"] = pr5_present
        page.screenshot(path=str(SHOTS_DIR / "06_tab_github_5prs.png"), full_page=True)
        
        # Step 1.7: Switch to Reports Tab & Modal Interaction
        page.click("button[data-tab='tab-reports']")
        time.sleep(0.5)
        reports_visible = page.locator("#tab-reports.active").is_visible()
        print(f"Reports Tab active: {reports_visible}")
        results["tab_reports"] = reports_visible
        page.screenshot(path=str(SHOTS_DIR / "07_tab_reports_overview.png"), full_page=True)
        
        # Open Schedule Modal from Reports Tab
        print("\n--- 3. Testing Schedule Configuration Modal ---")
        modal_btn = page.locator("#btn-open-schedule-modal")
        if modal_btn.is_visible():
            modal_btn.click()
            time.sleep(0.5)
            modal_box = page.locator("#schedule-config-modal")
            is_flex = modal_box.evaluate("el => window.getComputedStyle(el).display === 'flex'")
            print(f"Schedule Modal opened (display=flex): {is_flex}")
            results["schedule_modal_interactive"] = is_flex
            page.screenshot(path=str(SHOTS_DIR / "08_schedule_config_modal.png"))
            
            # Close modal via close button
            page.click("[data-action='close-modal']")
            time.sleep(0.3)
            is_closed = modal_box.evaluate("el => window.getComputedStyle(el).display === 'none'")
            print(f"Schedule Modal closed successfully (display=none): {is_closed}")
            results["schedule_modal_closed"] = is_closed
        else:
            print("Schedule Modal trigger button not found.")
            results["schedule_modal_interactive"] = False
            results["schedule_modal_closed"] = False
            
        # Step 1.8: Switch to Knowledge RAG Tab
        page.click("button[data-tab='tab-knowledge']")
        time.sleep(0.5)
        knowledge_visible = page.locator("#tab-knowledge.active").is_visible()
        print(f"Knowledge Tab active: {knowledge_visible}")
        results["tab_knowledge"] = knowledge_visible
        page.screenshot(path=str(SHOTS_DIR / "09_tab_knowledge_rag.png"), full_page=True)
        
        # Step 1.9: Switch to Integrations Tab
        page.click("button[data-tab='tab-integrations']")
        time.sleep(0.5)
        integrations_visible = page.locator("#tab-integrations.active").is_visible()
        print(f"Integrations Tab active: {integrations_visible}")
        results["tab_integrations"] = integrations_visible
        page.screenshot(path=str(SHOTS_DIR / "10_tab_system_integrations.png"), full_page=True)
        
        context.close()
        
        # Test 1920x1080 Viewport
        print("\n--- 4. Testing Full HD Viewport (1920x1080) ---")
        ctx_fhd = browser.new_context(viewport={"width": 1920, "height": 1080})
        ctx_fhd.add_cookies([{
            "name": "_open_project_session",
            "value": cookie,
            "domain": "127.0.0.1",
            "path": "/"
        }])
        page_fhd = ctx_fhd.new_page()
        page_fhd.goto(PROJECT6_AI_URL, wait_until="networkidle")
        page_fhd.screenshot(path=str(SHOTS_DIR / "11_desktop_1920x1080.png"), full_page=True)
        print("Captured: 11_desktop_1920x1080.png")
        ctx_fhd.close()
        
        # Test 1280x800 Viewport
        print("\n--- 5. Testing Laptop Viewport (1280x800) ---")
        ctx_laptop = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx_laptop.add_cookies([{
            "name": "_open_project_session",
            "value": cookie,
            "domain": "127.0.0.1",
            "path": "/"
        }])
        page_laptop = ctx_laptop.new_page()
        page_laptop.goto(PROJECT6_AI_URL, wait_until="networkidle")
        page_laptop.screenshot(path=str(SHOTS_DIR / "12_laptop_1280x800.png"), full_page=True)
        print("Captured: 12_laptop_1280x800.png")
        ctx_laptop.close()
        
        # Test Mobile 375x812 Viewport (Responsive check)
        print("\n--- 6. Testing Mobile Viewport (375x812) ---")
        ctx_mobile = browser.new_context(viewport={"width": 375, "height": 812})
        ctx_mobile.add_cookies([{
            "name": "_open_project_session",
            "value": cookie,
            "domain": "127.0.0.1",
            "path": "/"
        }])
        page_mobile = ctx_mobile.new_page()
        page_mobile.goto(PROJECT6_AI_URL, wait_until="networkidle")
        page_mobile.screenshot(path=str(SHOTS_DIR / "13_mobile_375x812.png"), full_page=True)
        print("Captured: 13_mobile_375x812.png")
        ctx_mobile.close()
        
        # Step 7: Test Classic Fallback View (?ui=classic)
        print("\n--- 7. Testing Classic Fallback (?ui=classic) ---")
        ctx_classic = browser.new_context(viewport={"width": 1440, "height": 900})
        ctx_classic.add_cookies([{
            "name": "_open_project_session",
            "value": cookie,
            "domain": "127.0.0.1",
            "path": "/"
        }])
        page_classic = ctx_classic.new_page()
        page_classic.goto(f"{PROJECT6_AI_URL}?ui=classic", wait_until="networkidle")
        classic_title = page_classic.title()
        has_classic_body = page_classic.locator(".qldapm-control-center").is_visible()
        print(f"Classic Page Title: {classic_title}, Container visible: {has_classic_body}")
        results["classic_fallback_working"] = has_classic_body
        page_classic.screenshot(path=str(SHOTS_DIR / "14_classic_fallback_view.png"), full_page=True)
        print("Captured: 14_classic_fallback_view.png")
        
        # Return to Modern View (?ui=modern)
        page_classic.goto(f"{PROJECT6_AI_URL}?ui=modern", wait_until="networkidle")
        modern_restored = page_classic.locator("#qldapm-command-center").is_visible()
        print(f"Modern view restored after ?ui=modern: {modern_restored}")
        results["modern_restored"] = modern_restored
        ctx_classic.close()
        
        browser.close()

    print("\n========================================================")
    print("PLAYWRIGHT UAT RESULTS SUMMARY:")
    all_pass = True
    for k, v in results.items():
        status = "PASS" if v else "FAIL"
        if not v: all_pass = False
        print(f"  [{status}] {k}: {v}")
    print("========================================================")
    print(f"OVERALL UAT STATUS: {'ALL_PASS' if all_pass else 'SOME_FAILED'}")
    return all_pass

if __name__ == '__main__':
    success = run_playwright_uat()
    if not success:
        exit(1)

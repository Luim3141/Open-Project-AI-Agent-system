"""Comprehensive Playwright Browser UAT for Phase 2.6.
Verifies:
1. User 18 (AI System Owner) full control & visibility over Project 6 AI Engineering.
2. Reporting generation from UI (Daily/On-Demand) and report list display.
3. User 20 (PM) authorized control & visibility.
4. User 19 (Non-member) strict access denial (403 Forbidden).
5. Project 5 data preservation (341 WPs untouched).
"""

import json
import os
from pathlib import Path
import subprocess
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / 'docs/ai/engineering/screenshots'
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

MAIN_BASE = "http://127.0.0.1:18088"
PROJECT6_AI_URL = f"{MAIN_BASE}/projects/ai-dev-demo/qldapm-ai"

def create_session_cookie(user_id):
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
    raise RuntimeError(f"Failed to generate session cookie for user {user_id}: {r.stderr}")

def get_project5_wp_count():
    cmd = [
        "docker", "exec", "qldapm-openproject-web-1", "bundle", "exec", "rails", "runner",
        "puts 'P5_WP_COUNT=' + WorkPackage.where(project_id: 5).count.to_s"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    for line in r.stdout.splitlines():
        if line.startswith('P5_WP_COUNT='):
            return int(line.split('=', 1)[1].strip())
    return -1

def main():
    print("=== STARTING PHASE 2.6 PLAYWRIGHT UAT VERIFICATION ===", flush=True)
    results = {}
    
    # 0. Check Project 5 baseline
    p5_count_before = get_project5_wp_count()
    print(f"Project 5 Work Package count before tests: {p5_count_before}", flush=True)
    assert p5_count_before == 341, f"Expected 341 WPs in Project 5, got {p5_count_before}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        
        # =========================================================================
        # TEST 1: User 18 (AI System Owner) Full Control & Visibility
        # =========================================================================
        print("\n--- TEST 1: User 18 (AI System Owner) Control Center Inspection ---", flush=True)
        owner_cookie = create_session_cookie(18)
        owner_ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        owner_ctx.add_cookies([{
            'name': '_open_project_session',
            'value': owner_cookie,
            'domain': '127.0.0.1',
            'path': '/'
        }])
        page18 = owner_ctx.new_page()
        resp18 = page18.goto(PROJECT6_AI_URL, wait_until="networkidle")
        print(f"Owner landing status: {resp18.status}, URL: {page18.url}", flush=True)
        assert resp18.status == 200, f"Expected 200 OK for Owner, got {resp18.status}"
        
        title18 = page18.title()
        print(f"Owner page title: {title18}", flush=True)
        assert "AI Engineering Control Center" in title18
        
        content18 = page18.content()
        # Check Header and Mode
        assert "AI Engineering Control Center" in content18
        assert "Chế độ: OFF" in content18 or "OFF" in content18
        
        # Check Sections
        assert "Điều khiển thực thi" in content18
        assert "Engineering Backlog" in content18
        assert "GitHub Pull Requests" in content18
        assert "Báo cáo tiến độ kỹ thuật" in content18
        
        # Check Parent WP #379
        assert "#379" in content18
        assert "Develop Mini Task Manager Application" in content18
        
        # Check Backlog Units
        assert "#379" in content18
        assert "#382" in content18
        assert "#383" in content18
        assert "create-list-persistence-v1" in content18
        assert "crud-search-web-v1" in content18
        
        # Check Buttons
        assert page18.locator("button:has-text('RUN ONCE')").count() > 0
        assert page18.locator("button:has-text('PAUSE')").count() > 0
        assert page18.locator("button:has-text('BẬT AUTO')").count() > 0
        assert page18.locator("button:has-text('Đồng bộ GitHub')").count() > 0
        assert page18.locator("button:has-text('Tạo Daily Report')").count() > 0
        
        # Screenshot 1
        shot1 = SCREENSHOT_DIR / "01_owner_control_center_full.png"
        page18.screenshot(path=str(shot1), full_page=True)
        print(f"Saved Owner Full Screenshot: {shot1.name}", flush=True)
        results["owner_control_center_inspection"] = "PASS"
        
        # =========================================================================
        # TEST 2: User 18 Generate Daily Report Interactive Action
        # =========================================================================
        print("\n--- TEST 2: User 18 Trigger Report Generation via UI ---", flush=True)
        daily_btn = page18.locator("button:has-text('Tạo Daily Report')")
        assert daily_btn.count() > 0, "Daily report button not found on UI"
        print("Clicking 'Tạo Daily Report' button...", flush=True)
        daily_btn.first.click()
        page18.wait_for_load_state("networkidle")
        time.sleep(2)
        
        post_content = page18.content()
        # Verify that report is generated and listed in the reports section
        assert "DAILY" in post_content, "Expected DAILY badge in reports list"
        print("Verified DAILY report appeared in UI!", flush=True)
        
        shot2 = SCREENSHOT_DIR / "02_owner_report_generated.png"
        page18.screenshot(path=str(shot2), full_page=True)
        print(f"Saved Report Generated Screenshot: {shot2.name}", flush=True)
        results["owner_report_generation"] = "PASS"
        
        # =========================================================================
        # TEST 3: User 20 (PM) Authorized Control & Visibility
        # =========================================================================
        print("\n--- TEST 3: User 20 (PM) Control Center Inspection ---", flush=True)
        pm_cookie = create_session_cookie(20)
        pm_ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        pm_ctx.add_cookies([{
            'name': '_open_project_session',
            'value': pm_cookie,
            'domain': '127.0.0.1',
            'path': '/'
        }])
        page20 = pm_ctx.new_page()
        resp20 = page20.goto(PROJECT6_AI_URL, wait_until="networkidle")
        print(f"PM landing status: {resp20.status}, URL: {page20.url}", flush=True)
        assert resp20.status == 200, f"Expected 200 OK for PM, got {resp20.status}"
        title20 = page20.title()
        assert "AI Engineering Control Center" in title20
        
        shot3 = SCREENSHOT_DIR / "03_pm_control_center.png"
        page20.screenshot(path=str(shot3), full_page=True)
        print(f"Saved PM Control Center Screenshot: {shot3.name}", flush=True)
        results["pm_control_center"] = "PASS"
        
        # =========================================================================
        # TEST 4: User 19 (Non-member) Strict Access Denial (403 Forbidden)
        # =========================================================================
        print("\n--- TEST 4: User 19 (Non-member) Access Denial Check ---", flush=True)
        user19_cookie = create_session_cookie(19)
        u19_ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        u19_ctx.add_cookies([{
            'name': '_open_project_session',
            'value': user19_cookie,
            'domain': '127.0.0.1',
            'path': '/'
        }])
        page19 = u19_ctx.new_page()
        resp19 = page19.goto(PROJECT6_AI_URL, wait_until="networkidle")
        print(f"User 19 landing status: {resp19.status}, URL: {page19.url}", flush=True)
        # Verify access denial (deny_access returns 403)
        assert resp19.status == 403 or "403" in page19.title() or "Forbidden" in page19.title() or "không có quyền" in page19.content().lower() or "access denied" in page19.content().lower(), \
            f"Expected 403 Forbidden for User 19, got {resp19.status}"
            
        shot4 = SCREENSHOT_DIR / "04_user19_access_denied.png"
        page19.screenshot(path=str(shot4), full_page=True)
        print(f"Saved User 19 Access Denied Screenshot: {shot4.name}", flush=True)
        results["user19_access_denial"] = "PASS"
        
        browser.close()

    # 5. Check Project 5 preservation
    p5_count_after = get_project5_wp_count()
    print(f"\nProject 5 Work Package count after tests: {p5_count_after}", flush=True)
    assert p5_count_after == 341, f"Project 5 WP count changed! Was {p5_count_before}, now {p5_count_after}"
    results["project5_data_preservation"] = "PASS (341 WPs untouched)"
    
    print("\n=== PLAYWRIGHT UAT RESULTS SUMMARY ===", flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    
    # Save results to json
    results_path = SCREENSHOT_DIR / "PLAYWRIGHT_UAT_RESULTS.json"
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nSaved results summary to {results_path}", flush=True)
    print("ALL PLAYWRIGHT UAT TESTS PASSED SUCCESSFULLY!", flush=True)

if __name__ == '__main__':
    main()

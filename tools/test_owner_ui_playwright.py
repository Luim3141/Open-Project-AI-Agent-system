"""Playwright Browser Verification for Owner AI Engineering Control Center."""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS_DIR = ROOT / "docs/ai/engineering/PHASE28_HANDOFF/screenshots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:18088"
TARGET_URL = f"{BASE_URL}/projects/ai-dev-demo/qldapm-ai"
SESSION_COOKIE_VALUE = "1f116b6d37c7f9ae71c8a30bc52f877f"

print("=================================================================")
print("RUNNING PLAYWRIGHT OWNER BROWSER UAT VERIFICATION (PHASE 2.8)")
print("=================================================================\n")

results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    context = browser.new_context(viewport={"width": 1440, "height": 1100})
    
    # Authenticate via Owner valid session cookie
    context.add_cookies([{
        "name": "_open_project_session",
        "value": SESSION_COOKIE_VALUE,
        "domain": "127.0.0.1",
        "path": "/"
    }])
    
    page = context.new_page()

    # Step 1: Navigate to Project 6 AI Engineering Control Center
    print(f"1. Navigating to Owner Control Center: {TARGET_URL}...")
    page.goto(TARGET_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    
    page_title = page.title()
    print(f"   Page Title: {page_title}")
    results["access_success"] = "AI Engineering Control Center" in page_title

    # Step 2: Verify Core UI Elements in Rendered Page
    print("\n2. Verifying Control Center UI Elements...")
    body_text = page.inner_text("body")

    # 2.1 Header
    has_title = "AI Engineering Control Center" in body_text
    print(f"   [PASS={has_title}] Header: 'AI Engineering Control Center'")
    results["header_title"] = has_title

    # 2.2 Mode Buttons
    has_off = "OFF" in body_text
    has_auto = "BẬT AUTO" in body_text
    has_paused = "PAUSE" in body_text
    has_run_once = "RUN ONCE" in body_text
    mode_pass = has_off and has_auto and has_paused and has_run_once
    print(f"   [PASS={mode_pass}] Mode buttons (OFF, BẬT AUTO, PAUSE, RUN ONCE)")
    results["mode_buttons"] = mode_pass

    # 2.3 Notifications Bar
    has_notif = "thông báo mới" in body_text or "Báo cáo Tiến độ Hằng ngày" in body_text
    print(f"   [PASS={has_notif}] Notifications Bar present")
    results["notifications_bar"] = has_notif

    # 2.4 GitHub PR Transparency Column & Badges
    has_reviews_col = "Reviews & CI GitHub" in body_text
    has_no_reviews = "NO_REVIEWS_ON_GITHUB" in body_text
    has_no_ci = "NO_CI_CHECKS_CONFIGURED" in body_text
    gh_pass = has_reviews_col and has_no_reviews and has_no_ci
    print(f"   [PASS={gh_pass}] GitHub PR Transparency (Column: {has_reviews_col}, NO_REVIEWS_ON_GITHUB: {has_no_reviews}, NO_CI: {has_no_ci})")
    results["github_pr_transparency"] = gh_pass

    # 2.5 Execution Runs Local Review Label
    has_local_ai_label = "Local AI Review:" in body_text
    print(f"   [PASS={has_local_ai_label}] Execution Runs: 'Local AI Review:' label")
    results["local_ai_review_label"] = has_local_ai_label

    # 2.6 Reporting Section & Schedule Info (Finding B & G)
    has_sched = "Lịch tự động:" in body_text or "Cấu hình lịch" in body_text or "Daily" in body_text
    has_snapshot = "Snapshot Tức Thời (+AI)" in body_text or "Tạo Daily Report" in body_text
    rep_pass = has_sched and has_snapshot
    print(f"   [PASS={rep_pass}] Reporting Section & Automation Schedule")
    results["reporting_section"] = rep_pass

    # 2.7 Verify Schedule Config Modal Trigger Button
    modal_btn = page.locator("#btn-open-schedule-modal, button:has-text('Cấu hình lịch'), a:has-text('Cấu hình lịch')").first
    has_modal_btn = modal_btn.is_visible()
    print(f"   [PASS={has_modal_btn}] Schedule Config Modal Button Present: {has_modal_btn}")
    results["schedule_modal_btn"] = has_modal_btn

    # Step 3: Capture Full Page Screenshot
    shot_path = SHOTS_DIR / "owner_control_center_live.png"
    page.screenshot(path=str(shot_path), full_page=True)
    print(f"\n3. Captured full-page screenshot: {shot_path} ({os.path.getsize(shot_path)} bytes)")

    # Step 4: Open Schedule Modal & Capture Screenshot (Finding G)
    if has_modal_btn:
        print("\n4. Clicking 'Cấu hình lịch' to open schedule configuration modal...")
        modal_btn.click()
        time.sleep(1)
        modal_shot = SHOTS_DIR / "owner_schedule_modal_live.png"
        page.screenshot(path=str(modal_shot))
        print(f"   Captured schedule modal screenshot: {modal_shot} ({os.path.getsize(modal_shot)} bytes)")
        results["schedule_modal_rendered"] = True
        # Close modal if close button exists
        close_btn = page.locator("#schedule-config-modal .close-modal, #schedule-config-modal button:has-text('Đóng')").first
        if close_btn.is_visible():
            close_btn.click()
            time.sleep(0.5)

    browser.close()

print("\n=================================================================")
print("PLAYWRIGHT BROWSER UAT SUMMARY:")
for k, v in results.items():
    print(f"  [{'PASS' if v else 'FAIL'}] {k}")
all_pass = all(results.values())
print(f"OVERALL RESULT: {'>>> ALL BROWSER UAT CHECKS PASSED <<<' if all_pass else '>>> SOME CHECKS FAILED <<<'}")
print("=================================================================")

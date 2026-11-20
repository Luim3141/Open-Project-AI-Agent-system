"""Forensic Reproduction of Phase 2.9.2 Defects on Live OpenProject."""
import json
import os
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs/ai/engineering/PHASE292"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAIN_BASE = "http://127.0.0.1:18088"
PROJECT6_SLUG = "ai-dev-demo"
WP_URL = f"{MAIN_BASE}/projects/{PROJECT6_SLUG}/work_packages"
AI_URL = f"{MAIN_BASE}/projects/{PROJECT6_SLUG}/qldapm-ai?ui=modern"

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

def main():
    cookie = get_fresh_owner_cookie()
    print(f"[AUTH] Acquired fresh Owner cookie: {cookie[:10]}...")

    forensic = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "navigation_entry_in_sidebar": False,
        "kpi_backlog_value": None,
        "kpi_backlog_sub": None,
        "worker_header_text": None,
        "worker_kpi_text": None,
        "backlog_unit_statuses": [],
        "console_messages": [],
        "network_requests": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_cookies([
            {"name": "_open_project_session", "value": cookie, "domain": "127.0.0.1", "path": "/"}
        ])
        page = context.new_page()

        page.on("console", lambda msg: forensic["console_messages"].append(f"[{msg.type}] {msg.text}"))
        page.on("request", lambda req: forensic["network_requests"].append({"url": req.url, "method": req.method}))

        # 1. Check sidebar navigation on Work Packages page
        print(f"[NAV] Visiting Work Packages page: {WP_URL}")
        page.goto(WP_URL, wait_until="networkidle", timeout=30000)
        
        # Check if AI Command Center link exists in menu
        ai_menu_item = page.locator("a.qldapm-ai-menu-item, a:has-text('AI Command Center'), a:has-text('AI Assistant')")
        forensic["navigation_entry_in_sidebar"] = (ai_menu_item.count() > 0)
        print(f"[DEFECT CHECK] Navigation menu item in sidebar: {forensic['navigation_entry_in_sidebar']}")
        page.screenshot(path=str(OUTPUT_DIR / "01_work_packages_sidebar.png"), full_page=True)

        # 2. Visit AI Command Center
        print(f"[AI] Visiting Command Center: {AI_URL}")
        page.goto(AI_URL, wait_until="networkidle", timeout=30000)
        page.screenshot(path=str(OUTPUT_DIR / "02_command_center_initial.png"), full_page=True)

        # 3. Read KPI discrepancies
        try:
            cards = page.locator(".qcc-kpi-card")
            if cards.count() >= 2:
                forensic["kpi_backlog_value"] = cards.nth(1).locator(".qcc-kpi-value").inner_text().strip()
                forensic["kpi_backlog_sub"] = cards.nth(1).locator(".qcc-kpi-sub").inner_text().strip()
            
            # Worker text in header vs KPI
            header_meta = page.locator(".qcc-header-meta").inner_text()
            forensic["worker_header_text"] = header_meta
            if cards.count() >= 1:
                forensic["worker_kpi_text"] = cards.nth(0).locator(".qcc-kpi-sub").inner_text().strip()
        except Exception as e:
            print(f"[ERR] Failed reading KPIs: {e}")

        # 4. Read Backlog unit statuses in Mission Control
        unit_badges = page.locator(".qcc-unit-badge .qcc-chip")
        for i in range(unit_badges.count()):
            forensic["backlog_unit_statuses"].append(unit_badges.nth(i).inner_text().strip())

        # 5. Check RUN ONCE button submission feedback
        print("[ACTION] Testing RUN ONCE button click...")
        run_once_btn = page.locator("button:has-text('RUN ONCE')")
        if run_once_btn.count() > 0:
            run_once_btn.first.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(path=str(OUTPUT_DIR / "03_after_run_once_click.png"), full_page=True)
            
            # Check if any notification toast or alert banner is visible
            alert_boxes = page.locator("[role='alert'], .qcc-notification-toast, .qcc-alert, .flash, .notice")
            forensic["visible_feedback_after_run_once"] = alert_boxes.count()
            print(f"[DEFECT CHECK] Visible feedback alerts after click: {alert_boxes.count()}")

        browser.close()

    report_path = OUTPUT_DIR / "baseline_forensic_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(forensic, f, indent=2, ensure_ascii=False)
    print(f"[REPORT] Saved forensic results to {report_path}")
    print(json.dumps(forensic, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

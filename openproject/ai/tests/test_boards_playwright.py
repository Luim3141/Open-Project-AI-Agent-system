import json
import os
from pathlib import Path
import subprocess
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SCREENSHOT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

access_path = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/access/current-url.json"
base = json.loads(access_path.read_text(encoding="utf-8"))["url"]

def get_pm_totp():
    ruby = '''require "json"
ActiveRecord::Base.transaction do
  ActiveRecord::Base.connection.execute("SET TRANSACTION READ ONLY")
  d = TwoFactorAuthentication::Device::Totp.find_by!(user_id: 7, active: true, default: true)
  puts "CODE=" + d.totp.at(Time.now)
end
'''
    res = subprocess.run(
        ["docker", "exec", "-i", "qldapm-ai-stage-staging-web-1", "bundle", "exec", "rails", "runner", "-"],
        input=ruby, capture_output=True, text=True, timeout=60, check=True
    )
    for line in res.stdout.splitlines():
        if line.startswith("CODE="):
            return line.split("=")[1].strip()
    raise RuntimeError("Failed to get PM TOTP")

print("Starting Boards Playwright Verification...")
otp = get_pm_totp()

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.set_default_timeout(60000)

    # 1. Login PM
    page.goto(base + "/login")
    page.locator("#username").fill("pm")
    page.locator("#password").fill("PUBLICATION_REDACTED")
    page.locator("form:has(#username) button[type=submit]").click()
    page.locator("#otp").wait_for(timeout=30000)

    if time.time() % 30 > 26:
        time.sleep(4)
        otp = get_pm_totp()
    page.locator("#otp").fill(otp)
    page.locator("input[type=submit][name=login]").click()
    page.wait_for_load_state("domcontentloaded")
    print("Logged in as PM!")

    # 2. Boards index page
    print("Navigating to /projects/qldapm-local/boards...")
    resp = page.goto(base + "/projects/qldapm-local/boards", wait_until="networkidle")
    print(f"Boards index HTTP status: {resp.status}")
    page.wait_for_timeout(2000)
    page.screenshot(path=str(SCREENSHOT_DIR / "boards_index.png"))
    print("Saved boards_index.png")

    boards_to_test = [
        (19, "board_19_scrum_kanban.png", "QLDAPM — Main Scrum Kanban Board", 7),
        (20, "board_20_workload_assignee.png", "QLDAPM — Team Workload & Assignee Board", 6),
        (21, "board_21_epic_breakdown.png", "QLDAPM — Epic Breakdown & Subtasks Board", 5),
        (22, "board_22_roadmap_milestones.png", "QLDAPM — Roadmap & Milestone Board", 4),
    ]

    for bid, sc_name, bname, expected_cols in boards_to_test:
        print(f"Opening Board #{bid}: '{bname}'...")
        b_resp = page.goto(f"{base}/projects/qldapm-local/boards/{bid}", wait_until="networkidle")
        print(f" - HTTP status: {b_resp.status}")
        page.wait_for_timeout(3000)
        
        # Count rendered columns
        cols_count = page.evaluate("""() => {
            return document.querySelectorAll('board-list, .grid--widget-host, op-board-column').length;
        }""")
        print(f" - Rendered columns count: {cols_count} (Expected: {expected_cols})")
        assert cols_count == expected_cols, f"Expected {expected_cols} columns, got {cols_count}"
        
        page.screenshot(path=str(SCREENSHOT_DIR / sc_name))
        print(f" - Saved screenshot: {sc_name}")

print("Boards Playwright verification finished successfully!")

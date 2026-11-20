import json
import os
from pathlib import Path
import subprocess
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SCREENSHOT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots"
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

print(f"Targeting: {base}")
otp = get_pm_totp()

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.set_default_timeout(60000)
    
    # Login PM
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
    
    # 1. Boards Index
    resp_boards = page.goto(base + "/projects/qldapm-local/boards", wait_until="networkidle")
    print(f"Boards Index HTTP status: {resp_boards.status}")
    page.wait_for_timeout(2000)
    page.screenshot(path=str(SCREENSHOT_DIR / "04_boards_index_view.png"), full_page=False)
    print("Saved 04_boards_index_view.png")
    
    # 2. Board 18 (Parent-Child)
    resp_b18 = page.goto(base + "/projects/qldapm-local/boards/18", wait_until="networkidle")
    print(f"Board 18 (Parent-Child) HTTP status: {resp_b18.status}")
    page.wait_for_timeout(3000)
    page.screenshot(path=str(SCREENSHOT_DIR / "05_board_parent_child_view.png"), full_page=False)
    print("Saved 05_board_parent_child_view.png")
    
    # 3. Board 17 (Kanban Status)
    resp_b17 = page.goto(base + "/projects/qldapm-local/boards/17", wait_until="networkidle")
    print(f"Board 17 (Kanban Status) HTTP status: {resp_b17.status}")
    page.wait_for_timeout(3000)
    page.screenshot(path=str(SCREENSHOT_DIR / "06_board_kanban_view.png"), full_page=False)
    print("Saved 06_board_kanban_view.png")
    
    browser.close()
    print("Boards verification completed successfully.")

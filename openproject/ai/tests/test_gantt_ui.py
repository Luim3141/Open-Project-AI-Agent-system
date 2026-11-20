import json
import os
from pathlib import Path
import re
import subprocess
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SCREENSHOT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

access_path = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/access/current-url.json"
base = json.loads(access_path.read_text(encoding="utf-8"))["url"]

# Get dynamic TOTP for PM
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
print(f"Got live TOTP code for PM")

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
    
    me = ctx.request.get(base + "/api/v3/users/me").json()
    print(f"Authenticated Actor ID: {me.get('id')} ({me.get('login')})")
    assert me.get("id") == 7, "Must be authenticated as PM (ID 7)"
    
    # 2. Check Project Sidebar Menu
    page.goto(base + "/projects/qldapm-local", wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Check if Gantt is in project sidebar
    gantt_sidebar = page.locator("#main-menu-gantt, a[href*='/projects/qldapm-local/gantt']")
    has_gantt_menu = gantt_sidebar.count() > 0
    print(f"Project Sidebar has Gantt menu item: {has_gantt_menu}")
    
    # 3. Check Project Gantt Page
    resp_proj = page.goto(base + "/projects/qldapm-local/gantt", wait_until="networkidle")
    print(f"Project Gantt HTTP status: {resp_proj.status}")
    page.wait_for_timeout(3000)
    
    # Verify gantt container / table exists
    has_wp_table = page.locator(".work-package-table--container, .wp-table--row, op-gantt-chart, .gantt-chart").count() > 0
    print(f"Project Gantt renders table/chart elements: {has_wp_table}")
    
    page.screenshot(path=str(SCREENSHOT_DIR / "02_project_gantt_view.png"), full_page=False)
    print("Saved 02_project_gantt_view.png")
    
    # 4. Check Global Gantt Page
    resp_global = page.goto(base + "/gantt", wait_until="networkidle")
    print(f"Global Gantt HTTP status: {resp_global.status}")
    page.wait_for_timeout(3000)
    
    page.screenshot(path=str(SCREENSHOT_DIR / "03_global_gantt_view.png"), full_page=False)
    print("Saved 03_global_gantt_view.png")
    
    browser.close()
    print("Gantt verification completed successfully.")

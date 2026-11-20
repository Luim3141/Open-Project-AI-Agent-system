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

print(f"Targeting: {base}")
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
    
    # 2. Go to Project Gantt
    page.goto(base + "/projects/qldapm-local/gantt", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # 3. Inspect hierarchy toggles
    toggles = page.locator(".wp-table--hierarchy-span, .wp-table--hierarchy-indicator, [class*='hierarchy-indicator']")
    print(f"Hierarchy toggle elements found: {toggles.count()}")
    
    # Check what happens when clicking toggle on Epic 39
    epic39_toggle = page.locator(".wp-row-39 .wp-table--hierarchy-span, .wp-row-39 button[class*='hierarchy'], .wp-row-39 .wp-table--hierarchy-indicator").first
    if epic39_toggle.count() > 0:
        print("Found Epic 39 toggle! Clicking to collapse...")
        epic39_toggle.click()
        page.wait_for_timeout(1000)
        
    epic38_toggle = page.locator(".wp-row-38 .wp-table--hierarchy-span, .wp-row-38 button[class*='hierarchy'], .wp-row-38 .wp-table--hierarchy-indicator").first
    if epic38_toggle.count() > 0:
        print("Found Epic 38 toggle! Clicking to collapse...")
        epic38_toggle.click()
        page.wait_for_timeout(1000)
        
    page.screenshot(path=str(SCREENSHOT_DIR / "project_gantt_both_collapsed.png"), full_page=False)
    print("Saved project_gantt_both_collapsed.png")

    visible_rows = page.evaluate('''() => {
        const rows = document.querySelectorAll(".wp-table--row");
        return Array.from(rows).filter(r => r.offsetParent !== null).map(r => ({
            id: r.getAttribute("data-work-package-id"),
            text: r.innerText.replace(/\\s+/g, " ").trim().substring(0, 50)
        }));
    }''')
    print("Visible rows after collapsing Epic 39 and Epic 38:")
    print(json.dumps(visible_rows, indent=2, ensure_ascii=False))

    browser.close()

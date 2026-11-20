import json
import os
from pathlib import Path
import subprocess
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SCREENSHOT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots"

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
    
    page.goto(base + "/projects/qldapm-local/gantt", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # Click 500 in pagination
    btn_500 = page.locator(".pagination, .op-pagination").locator("text=500")
    print(f"500 button count: {btn_500.count()}")
    if btn_500.count() > 0:
        print("Clicking 500 per page...")
        btn_500.first.click()
        page.wait_for_timeout(4000)
        
    page.screenshot(path=str(SCREENSHOT_DIR / "gantt_after_clicking_500.png"), full_page=False)
    print("Saved gantt_after_clicking_500.png")

    info = page.evaluate('''() => {
        const rows = document.querySelectorAll(".wp-table--row");
        const epics = Array.from(rows).filter(r => r.innerText.includes("EPIC"));
        const pagination = document.querySelector(".pagination, .op-pagination");
        return {
            currentUrl: window.location.href,
            totalRows: rows.length,
            epicCount: epics.length,
            paginationText: pagination ? pagination.innerText.replace(/\\s+/g, " ").trim() : "none",
            first15Epics: epics.map(e => e.innerText.replace(/\\s+/g, " ").trim().substring(0, 60))
        };
    }''')
    print("Info after clicking 500:")
    print(json.dumps(info, indent=2, ensure_ascii=False))

    browser.close()

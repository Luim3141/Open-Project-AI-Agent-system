import json
import os
from pathlib import Path
import subprocess
from playwright.sync_api import sync_playwright

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
    page.goto(base + "/login")
    page.locator("#username").fill("pm")
    page.locator("#password").fill("PUBLICATION_REDACTED")
    page.locator("form:has(#username) button[type=submit]").click()
    page.locator("#otp").wait_for(timeout=30000)
    page.locator("#otp").fill(otp)
    page.locator("input[type=submit][name=login]").click()
    page.wait_for_load_state("domcontentloaded")

    page.goto(base + "/projects/qldapm-local/boards/19", wait_until="networkidle")
    page.wait_for_timeout(3000)

    dom_info = page.evaluate("""() => {
        const board = document.querySelector('op-boards, op-grid, .board, #content');
        if (!board) return { error: 'No board element found' };
        
        const tags = Array.from(document.querySelectorAll('*')).map(el => el.tagName.toLowerCase());
        const customTags = Array.from(new Set(tags.filter(t => t.includes('-') || t.includes('board') || t.includes('grid'))));
        
        const columnCandidates = Array.from(document.querySelectorAll('*')).filter(el => {
            const c = typeof el.className === 'string' ? el.className : '';
            return c.includes('column') || c.includes('grid') || c.includes('widget');
        }).map(el => ({ tag: el.tagName, class: el.className, text: el.innerText.substring(0, 40) }));

        return {
            title: document.title,
            customTags: customTags,
            columnCandidatesCount: columnCandidates.length,
            first5Candidates: columnCandidates.slice(0, 5)
        };
    }""")
    print("DOM Info for Board 19:", json.dumps(dom_info, indent=2, ensure_ascii=False))

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

    page.goto(base + "/projects/qldapm-local/gantt?pp=500", wait_until="networkidle")
    page.wait_for_timeout(3000)

    details = page.evaluate("""() => {
        const row = document.querySelector('.wp-row-38');
        if (!row) return 'ROW_NOT_FOUND';
        const getClass = el => typeof el.className === "string" ? el.className : (el.className ? el.className.baseVal : "");
        const indicators = Array.from(row.querySelectorAll('*')).filter(el => {
            const c = getClass(el);
            return c && (c.includes('hierarchy') || c.includes('indicator') || c.includes('arrow'));
        }).map(el => ({
            tag: el.tagName,
            classes: getClass(el),
            outerHTML: el.outerHTML,
            title: el.getAttribute('title') || el.innerText
        }));
        return indicators;
    }""")
    print("Hierarchy indicators on row 38:", json.dumps(details, indent=2, ensure_ascii=False))

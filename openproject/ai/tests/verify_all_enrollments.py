import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

access_path = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/access/current-url.json"
base = json.loads(access_path.read_text(encoding="utf-8"))["url"]

accounts = [
    {"role": "BA-PM", "login": "ba-pm", "pass": "PUBLICATION_REDACTED"},
    {"role": "FE", "login": "fe", "pass": "PUBLICATION_REDACTED"},
    {"role": "QA", "login": "qa", "pass": "PUBLICATION_REDACTED"}
]

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    for acc in accounts:
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(base + "/login", timeout=60000)
        page.locator("#username").fill(acc["login"])
        page.locator("#password").fill(acc["pass"])
        page.locator("form:has(#username) button[type=submit]").click()
        page.wait_for_timeout(3000)
        
        is_reg = "/two_factor_authentication/device_registration" in page.url
        print(f"User {acc['login']} ({acc['role']}) -> URL: {page.url} | Is forced registration: {is_reg}")
        ctx.close()
    browser.close()

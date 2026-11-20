import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

access_path = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/access/current-url.json"
base = json.loads(access_path.read_text(encoding="utf-8"))["url"]

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    for user, pw_str in [("pm", "PUBLICATION_REDACTED"), ("be", "PUBLICATION_REDACTED")]:
        page = browser.new_page()
        page.goto(base + "/login", timeout=60000)
        page.locator("#username").fill(user)
        page.locator("#password").fill(pw_str)
        page.locator("form:has(#username) button[type=submit]").click()
        page.wait_for_timeout(3000)
        has_otp = page.locator("#otp").count() > 0
        print(f"Protected user '{user}' -> URL: {page.url} | Has #otp prompt: {has_otp}")
        page.close()
    browser.close()

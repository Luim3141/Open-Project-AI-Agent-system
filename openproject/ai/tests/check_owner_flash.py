import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

access_path = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/access/current-url.json"
base = json.loads(access_path.read_text(encoding="utf-8"))["url"]

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto(base + "/login", timeout=60000)
    page.locator("#username").fill("stage-owner")
    page.locator("#password").fill("PUBLICATION_REDACTED")
    page.locator("form:has(#username) button[type=submit]").click()
    page.wait_for_timeout(3000)
    
    print("URL:", page.url)
    flash = page.locator(".op-toast, .flash, .errorExplanation, #errorExplanation").all_text_contents()
    print("Flash:", [f.strip() for f in flash if f.strip()])
    browser.close()

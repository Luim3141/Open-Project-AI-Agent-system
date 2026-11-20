import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

access_path = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/access/current-url.json"
base = json.loads(access_path.read_text(encoding="utf-8"))["url"]
print(f"Testing forced enrollment redirection on: {base}")

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    page.goto(base + "/login", timeout=60000)
    
    # Fill stage-owner credentials
    page.locator("#username").fill("stage-owner")
    page.locator("#password").fill("PUBLICATION_REDACTED")
    page.locator("form:has(#username) button[type=submit]").click()
    page.wait_for_timeout(3000)
    
    current_url = page.url
    print(f"After submit. Current URL: {current_url}")
    print("Page title:", page.title())
    
    # Check if we are on the device registration page
    is_reg_page = "/two_factor_authentication/device_registration" in current_url
    print(f"Is on device_registration page: {is_reg_page}")
    
    # Check available registration options (e.g., Authenticator app)
    headings = page.locator("h1, h2, h3").all_text_contents()
    print("Headings:", headings)
    buttons = page.locator("a.button, button, input[type=submit]").all_text_contents()
    print("Action buttons:", [b.strip() for b in buttons if b.strip()])
    
    # Take screenshot of the registration prompt page (WITHOUT generating QR yet)
    SCREENSHOT_DIR = Path("docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots")
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SCREENSHOT_DIR / "01_stage_owner_enrollment_ready.png"))
    print("Saved 01_stage_owner_enrollment_ready.png")
    
    browser.close()

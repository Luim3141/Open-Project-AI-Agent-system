import base64
import hashlib
import hmac
import json
import os
import struct
import time
from playwright.sync_api import sync_playwright

access_file = os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\access\current-url.json")
url = json.load(open(access_file))["url"]
print("Active URL:", url)

def get_totp(secret_b32):
    key = base64.b32decode(secret_b32, casefold=True)
    msg = struct.pack(">Q", int(time.time() // 30))
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(ignore_https_errors=True)
    page = ctx.new_page()
    page.goto(f"{url}/login", wait_until="domcontentloaded")
    page.wait_for_selector("#username", timeout=10000)
    cred_file = os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\secrets\staging_totp_secrets.json")
    if not os.path.isfile(cred_file):
        cred_file = os.path.expandvars(r"%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json")
    creds = json.load(open(cred_file)) if os.path.isfile(cred_file) else {}
    pm_cred = creds.get("pm", {})
    page.fill("#password", pm_cred.get("pass", ""))
    
    # Click the submit button inside login form
    page.locator("form:has(#username) button[type='submit']").click()
    page.wait_for_load_state("domcontentloaded")
    time.sleep(2)
    print("After 1FA URL:", page.url)
    
    if "two_factor" in page.url:
        print("On 2FA page, filling OTP...")
        page.wait_for_selector("#otp", timeout=10000)
        totp_secret = pm_cred.get("totp_secret", "")
        if totp_secret:
            totp = get_totp(totp_secret)
            page.fill("#otp", totp)
        page.locator("input[type='submit'][name='login']").click()
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        print("After 2FA URL:", page.url)
        print("Page Title:", page.title())
        
        # Test /api/v3/users/me
        resp = ctx.request.get(f"{url}/api/v3/users/me")
        print("API /api/v3/users/me status:", resp.status)
        if resp.status == 200:
            user_data = resp.json()
            print("AUTHENTICATED USER:", user_data.get("login"), "| Name:", user_data.get("name"), "| Admin:", user_data.get("admin"))
            
        # Test navigation to work packages
        page.goto(f"{url}/projects/3/work_packages", wait_until="domcontentloaded")
        time.sleep(3)
        print("WP URL:", page.url)
        print("WP Page Title:", page.title())
        # Check if table or work package items exist
        wp_rows = page.locator(".work-package--subject, .wp-table--row, .work-packages--table tbody tr")
        print("WP row elements found:", wp_rows.count())
    browser.close()

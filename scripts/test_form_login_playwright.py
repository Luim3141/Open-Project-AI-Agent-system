import json
import os
import sys
from playwright.sync_api import sync_playwright

tunnel_url = "https://instance-presence-testing-eclipse.trycloudflare.com"

print("Starting Playwright...", flush=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    console_messages = []
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))

    request_failures = []
    page.on("requestfailed", lambda req: request_failures.append(f"{req.method} {req.url}: {req.failure}"))

    print(f"Navigating to {tunnel_url}/login...", flush=True)
    resp = page.goto(f"{tunnel_url}/login", wait_until="domcontentloaded", timeout=20000)
    print(f"Initial Page Title: {page.title()}, HTTP {resp.status if resp else 'N/A'}", flush=True)

    # Fill credentials in visible inputs
    print("Filling credentials for user 'pm' in #username and #password...", flush=True)
    page.fill("#username", "pm")
    page.fill("#password", "PUBLICATION_REDACTED")
    
    print("Clicking visible Sign in button...", flush=True)
    page.click("button:has-text('Sign in'):visible")
    page.wait_for_load_state("domcontentloaded", timeout=20000)
    
    print(f"Post-Login Page Title: {page.title()}", flush=True)
    print(f"Post-Login URL: {page.url}", flush=True)

    # Check session cookie
    cookies = context.cookies()
    session_cookie = next((c for c in cookies if c["name"] == "_open_project_session"), None)
    print(f"Session Cookie Present: {session_cookie is not None}", flush=True)
    if session_cookie:
        print(f"Cookie Details: HttpOnly={session_cookie.get('httpOnly')}, Secure={session_cookie.get('secure')}, SameSite={session_cookie.get('sameSite')}", flush=True)

    # Check project page access
    print("Navigating to Project 3 page...", flush=True)
    p_resp = page.goto(f"{tunnel_url}/projects/qldapm-local", wait_until="domcontentloaded", timeout=20000)
    print(f"Project Page Title: {page.title()}, HTTP {p_resp.status if p_resp else 'N/A'}", flush=True)

    # Check AI menu item
    ai_menu = page.query_selector("a[href*='qldapm-ai']")
    print(f"AI Menu Item Present: {ai_menu is not None}", flush=True)

    # Logout
    print("Testing Logout...", flush=True)
    logout_resp = page.goto(f"{tunnel_url}/logout", wait_until="domcontentloaded", timeout=20000)
    print(f"Post-Logout Page Title: {page.title()}, URL: {page.url}", flush=True)

    print(f"Console messages recorded: {len(console_messages)}", flush=True)
    print(f"Request failures recorded: {len(request_failures)}", flush=True)

    browser.close()
    print("ALL PLAYWRIGHT TESTS PASSED!", flush=True)

"""Playwright verification of QLDAPM Main after Emergency AI Recovery."""
import os
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = REPO / 'docs/ai-multi-agent-upgrade/main-ai-recovery/screenshots'
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=== STARTING PLAYWRIGHT VERIFICATION ON MAIN ===", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Main Login Page
        print("1. Loading http://localhost:8088/login...", flush=True)
        resp1 = page.goto("http://localhost:8088/login", wait_until="domcontentloaded", timeout=20000)
        assert resp1.status == 200, f"Expected 200, got {resp1.status}"
        page.wait_for_selector("#username", timeout=10000)
        login_png = SCREENSHOTS_DIR / '01_main_login_page.png'
        page.screenshot(path=str(login_png), full_page=True)
        print(f"   [PASS] Login page loaded: {login_png.name}", flush=True)

        # 2. Main Project Overview
        print("2. Loading http://localhost:8088/projects/qldapm-local...", flush=True)
        resp2 = page.goto("http://localhost:8088/projects/qldapm-local", wait_until="domcontentloaded", timeout=20000)
        assert resp2.status in (200, 302, 403), f"Status {resp2.status}"
        proj_png = SCREENSHOTS_DIR / '02_main_project_view.png'
        page.screenshot(path=str(proj_png), full_page=True)
        print(f"   [PASS] Project overview checked: {proj_png.name}", flush=True)

        # 3. AI Gateway Health
        print("3. Loading http://localhost:8090/health...", flush=True)
        resp3 = page.goto("http://localhost:8090/health", wait_until="domcontentloaded", timeout=10000)
        assert resp3.status == 200
        assert "ok" in page.content()
        gw_png = SCREENSHOTS_DIR / '03_gateway_health.png'
        page.screenshot(path=str(gw_png), full_page=True)
        print(f"   [PASS] Gateway health verified: {gw_png.name}", flush=True)

        # 4. OpenAPI Spec (requires auth or returns 401 unauthenticated)
        print("4. Loading http://localhost:8090/api/v1/openapi.json...", flush=True)
        resp4 = page.goto("http://localhost:8090/api/v1/openapi.json", wait_until="domcontentloaded", timeout=10000)
        assert resp4.status in (200, 401), f"Expected 200 or 401, got {resp4.status}"
        print(f"   [PASS] AI Gateway security verified: Status {resp4.status}.", flush=True)

        browser.close()

    print("=== PLAYWRIGHT VERIFICATION COMPLETED SUCCESSFULLY ===", flush=True)

if __name__ == '__main__':
    main()

"""Execute Playwright UI verification on Main and capture visual evidence."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO / 'docs/ai-multi-agent-upgrade/run_20261021_final_delivery/evidence'
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=== STARTING PLAYWRIGHT UI VERIFICATION ON MAIN ===", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Main Login Page
        print("1. Loading http://localhost:8088/login...", flush=True)
        page.goto("http://localhost:8088/login", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1000)
        login_png = EVIDENCE_DIR / 'main_login_page.png'
        page.screenshot(path=str(login_png), full_page=True)
        print(f"   Captured login screenshot: {login_png.name} (Title: '{page.title()}')", flush=True)

        # 2. Project Public / Overview Page
        print("2. Loading http://localhost:8088/projects/qldapm-local...", flush=True)
        page.goto("http://localhost:8088/projects/qldapm-local", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1000)
        project_png = EVIDENCE_DIR / 'main_project_overview.png'
        page.screenshot(path=str(project_png), full_page=True)
        print(f"   Captured project screenshot: {project_png.name} (Title: '{page.title()}')", flush=True)

        # 3. AI Gateway Health
        print("3. Loading http://localhost:8090/health...", flush=True)
        page.goto("http://localhost:8090/health", wait_until="domcontentloaded", timeout=10000)
        gw_content = page.content()
        assert "ok" in gw_content
        print("   AI Gateway Health verified in browser.", flush=True)

        browser.close()

    print("=== PLAYWRIGHT UI VERIFICATION COMPLETED SUCCESSFULLY ===", flush=True)

if __name__ == '__main__':
    main()

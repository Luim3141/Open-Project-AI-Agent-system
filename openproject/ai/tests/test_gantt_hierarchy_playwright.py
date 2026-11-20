import json
import os
from pathlib import Path
import subprocess
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SCREENSHOT_DIR = ROOT / "docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

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

print("Starting Gantt Hierarchy Playwright UAT...")
otp = get_pm_totp()

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.set_default_timeout(60000)

    # 1. Login PM
    page.goto(base + "/login")
    page.locator("#username").fill("pm")
    page.locator("#password").fill("PUBLICATION_REDACTED")
    page.locator("form:has(#username) button[type=submit]").click()
    page.locator("#otp").wait_for(timeout=30000)

    if time.time() % 30 > 26:
        time.sleep(4)
        otp = get_pm_totp()
    page.locator("#otp").fill(otp)
    page.locator("input[type=submit][name=login]").click()
    page.wait_for_load_state("domcontentloaded")
    print("Logged in as PM!")

    # 2. Navigate to Gantt with query_id=37 & pp=500
    print("Navigating to Saved Query 37 (QLDAPM — Scrum Roadmap theo Epic)...")
    resp = page.goto(base + "/projects/qldapm-local/gantt?query_id=37&pp=500", wait_until="networkidle")
    print(f"HTTP Status: {resp.status}")
    page.wait_for_selector(".wp-table--row", timeout=15000)
    page.wait_for_timeout(2000)

    # Capture initial un-collapsed
    page.screenshot(path=str(SCREENSHOT_DIR / "gantt_query37_loaded.png"))
    print("Saved gantt_query37_loaded.png")

    # 3. Collapse all Root Epics
    print("Collapsing Root Epics via hierarchy indicators...")
    collapse_res = page.evaluate("""() => {
        const rootEpics = [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48];
        const collapsed = [];
        for (const id of rootEpics) {
            const row = document.querySelector(`.wp-row-${id}`);
            if (row) {
                const btn = row.querySelector('.wp-table--hierarchy-indicator');
                if (btn) {
                    btn.click();
                    collapsed.push(id);
                }
            }
        }
        return collapsed;
    }""")
    print(f"Clicked collapse on Epics: {collapse_res}")
    page.wait_for_timeout(2000)

    # Check visible rows now
    visible_rows = page.evaluate("""() => {
        const rows = document.querySelectorAll('.wp-table--row');
        return Array.from(rows).filter(r => r.offsetParent !== null).map(r => ({
            id: r.getAttribute('data-work-package-id') || r.id,
            text: r.innerText.replace(/\\s+/g, ' ').trim().substring(0, 60)
        }));
    }""")
    print(f"Visible rows after collapsing all root Epics: {len(visible_rows)}")
    for r in visible_rows:
        print(f" - {r['id']}: {r['text']}")

    page.screenshot(path=str(SCREENSHOT_DIR / "gantt_all_epics_collapsed.png"))
    print("Saved gantt_all_epics_collapsed.png")

    # 4. Expand Epic 38
    print("Expanding Epic 38...")
    page.evaluate("""() => {
        const row = document.querySelector('.wp-row-38');
        const btn = row.querySelector('.wp-table--hierarchy-indicator');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(2000)

    visible_after_e38 = page.evaluate("""() => {
        const rows = document.querySelectorAll('.wp-table--row');
        return Array.from(rows).filter(r => r.offsetParent !== null).map(r => ({
            id: r.getAttribute('data-work-package-id') || r.id,
            text: r.innerText.replace(/\\s+/g, ' ').trim().substring(0, 60)
        }));
    }""")
    print(f"Visible rows after expanding Epic 38: {len(visible_after_e38)}")
    page.screenshot(path=str(SCREENSHOT_DIR / "gantt_epic38_expanded.png"))
    print("Saved gantt_epic38_expanded.png")

    # 5. Expand Task 49
    print("Expanding Task 49 (AUTH-01)...")
    page.evaluate("""() => {
        const row = document.querySelector('.wp-row-49');
        if (row) {
            const btn = row.querySelector('.wp-table--hierarchy-indicator');
            if (btn) btn.click();
        }
    }""")
    page.wait_for_timeout(2000)

    visible_after_t49 = page.evaluate("""() => {
        const rows = document.querySelectorAll('.wp-table--row');
        return Array.from(rows).filter(r => r.offsetParent !== null).map(r => ({
            id: r.getAttribute('data-work-package-id') || r.id,
            text: r.innerText.replace(/\\s+/g, ' ').trim().substring(0, 60)
        }));
    }""")
    print(f"Visible rows after expanding Task 49: {len(visible_after_t49)}")
    page.screenshot(path=str(SCREENSHOT_DIR / "gantt_task49_expanded.png"))
    print("Saved gantt_task49_expanded.png")

    # 6. Re-collapse Epic 38
    print("Re-collapsing Epic 38...")
    page.evaluate("""() => {
        const row = document.querySelector('.wp-row-38');
        const btn = row.querySelector('.wp-table--hierarchy-indicator');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(2000)

    visible_final = page.evaluate("""() => {
        const rows = document.querySelectorAll('.wp-table--row');
        return Array.from(rows).filter(r => r.offsetParent !== null).map(r => ({
            id: r.getAttribute('data-work-package-id') || r.id,
            text: r.innerText.replace(/\\s+/g, ' ').trim().substring(0, 60)
        }));
    }""")
    print(f"Visible rows after re-collapsing Epic 38: {len(visible_final)}")
    page.screenshot(path=str(SCREENSHOT_DIR / "gantt_epic38_recollapsed.png"))
    print("Saved gantt_epic38_recollapsed.png")

print("Gantt Hierarchy test completed successfully!")

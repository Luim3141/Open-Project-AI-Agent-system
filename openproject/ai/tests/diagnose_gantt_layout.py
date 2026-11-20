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

print(f"Targeting: {base}")
otp = get_pm_totp()

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.set_default_timeout(60000)
    
    # Intercept API calls
    api_calls = []
    page.on("response", lambda r: api_calls.append({"url": r.url, "status": r.status}) if "/api/v3/" in r.url else None)

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
    
    # 2. Navigate to Project Gantt
    print("Navigating to Project Gantt...")
    resp = page.goto(base + "/projects/qldapm-local/gantt", wait_until="networkidle")
    print(f"Project Gantt HTTP status: {resp.status}")
    page.wait_for_timeout(3000)
    
    # Capture detailed screenshot
    page.screenshot(path=str(SCREENSHOT_DIR / "project_gantt_initial.png"), full_page=False)
    print("Saved project_gantt_initial.png")

    # Evaluate DOM and layout metrics
    metrics = page.evaluate('''() => {
        const rows = document.querySelectorAll(".wp-table--row, .work-package--row, tr[data-work-package-id]");
        const rowDetails = Array.from(rows).map(r => ({
            id: r.getAttribute("data-work-package-id") || r.id,
            text: r.innerText.replace(/\\s+/g, " ").trim().substring(0, 80),
            visible: r.offsetParent !== null,
            classes: r.className,
            height: r.offsetHeight
        }));
        
        const tableContainer = document.querySelector(".work-packages-table--container, .work-package-table--container, .wp-table--container");
        const ganttContainer = document.querySelector("op-gantt-chart, .gantt-chart, .gantt-chart--container");
        const mainContent = document.querySelector("#content, .main-content");
        const splitView = document.querySelector(".work-packages--split-view, .work-packages--table-and-timeline");
        const pagination = document.querySelector(".pagination, .op-pagination");
        
        const getStyles = el => el ? {
            tag: el.tagName,
            classes: el.className,
            offsetHeight: el.offsetHeight,
            clientHeight: el.clientHeight,
            scrollHeight: el.scrollHeight,
            styleHeight: el.style.height,
            computedHeight: window.getComputedStyle(el).height,
            computedMaxHeight: window.getComputedStyle(el).maxHeight,
            overflow: window.getComputedStyle(el).overflow,
            display: window.getComputedStyle(el).display,
            flex: window.getComputedStyle(el).flex
        } : null;

        return {
            totalRowsInDOM: rows.length,
            visibleRowsCount: rowDetails.filter(r => r.visible).length,
            first10Rows: rowDetails.slice(0, 10),
            paginationText: pagination ? pagination.innerText.replace(/\\s+/g, " ").trim() : "none",
            tableContainer: getStyles(tableContainer),
            ganttContainer: getStyles(ganttContainer),
            mainContent: getStyles(mainContent),
            splitView: getStyles(splitView),
            bodyHeight: document.body.offsetHeight,
            windowHeight: window.innerHeight
        };
    }''')
    
    print("Detailed Gantt Metrics:")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    
    out_file = ROOT / "docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/gantt_layout_metrics.json"
    out_file.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved gantt_layout_metrics.json")
    
    # Also log relevant API calls
    wp_api_calls = [c for c in api_calls if "work_packages" in c["url"] or "queries" in c["url"]]
    print(f"Total Work Package API calls: {len(wp_api_calls)}")
    for c in wp_api_calls:
        print(f"  {c['status']} {c['url']}")
        
    browser.close()

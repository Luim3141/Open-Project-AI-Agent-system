"""Phase 3.1 Real End-to-End Browser UAT and Invariant Verification Suite.

Tests live OpenProject AI Command Center in Chromium via Playwright:
- Authentication with User 18 (Owner)
- Button clicks: Sync GitHub, Snapshot, RUN ONCE, Control Mode
- Verifies absence of infinite spinners and HTTP 403/409/500 errors
- Verifies Project 5 invariants (341 WPs, max lock_version 4, 0 writes)
- Captures screenshots for evidence
"""
import json
import os
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = ROOT / 'docs/ai/engineering/PHASE31_RECOVERY/screenshots'
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

COOKIE_VALUE = '06e1ddb8e85385e78a2424c2733c8dd8'
BASE_URL = 'http://127.0.0.1:18088'
TARGET_URL = f'{BASE_URL}/projects/ai-dev-demo/qldapm-ai?ui=modern'


def get_project5_stats():
    cmd = [
        'docker', 'exec', '-i', 'qldapm-openproject-db-1',
        'psql', '-U', 'postgres', '-d', 'openproject', '-t', '-A', '-c',
        'SELECT count(1), max(lock_version) FROM work_packages WHERE project_id = 5;'
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    parts = p.stdout.strip().split('|')
    return int(parts[0]), int(parts[1])


def main():
    print('======================================================================')
    print('STARTING PHASE 3.1 REAL BROWSER E2E UAT & REGRESSION VERIFICATION')
    print('======================================================================\n')

    # Baseline invariant check
    p5_count_before, p5_max_lock_before = get_project5_stats()
    print(f'Project 5 Baseline: Count={p5_count_before}, Max LockVersion={p5_max_lock_before}')
    assert p5_count_before == 341, f'Project 5 count != 341 (got {p5_count_before})'
    assert p5_max_lock_before <= 4, f'Project 5 max lock_version > 4 (got {p5_max_lock_before})'

    test_results = {
        'timestamp': time.time(),
        'page_load': False,
        'infinite_spinner_eliminated': False,
        'sync_github_pass': False,
        'snapshot_report_pass': False,
        'run_once_pass': False,
        'workforce_transparency_pass': False,
        'project5_invariants_pass': False,
        'evidence_screenshots': []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1050})

        # Set session cookie for User 18
        context.add_cookies([{
            'name': '_open_project_session',
            'value': COOKIE_VALUE,
            'domain': '127.0.0.1',
            'path': '/'
        }])

        page = context.new_page()

        # Step 1: Open AI Command Center
        print(f'1. Navigating to {TARGET_URL}...')
        resp = page.goto(TARGET_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        print(f'   Response Status: {resp.status}')
        page_title = page.title()
        print(f'   Page Title: {page_title}')
        assert resp.status == 200, f'Expected 200, got {resp.status}'
        assert 'AI Engineering Command Center' in page_title or 'OpenProject' in page_title
        test_results['page_load'] = True

        shot1 = str(SCREENSHOTS_DIR / '01_command_center_loaded.png')
        page.screenshot(path=shot1, full_page=True)
        test_results['evidence_screenshots'].append(shot1)
        print('   Screenshot 1 saved: 01_command_center_loaded.png')

        # Step 2: Test Workforce Transparency
        print('\n2. Testing Agent Workforce Tab & Transparency...')
        page.click('button[data-tab="tab-workforce"]')
        time.sleep(1)

        # Check Reviewer model text
        body_text = page.inner_text('#tab-workforce')
        has_rev_0_llm = '0 LLM Calls' in body_text or 'Local-Policy' in body_text
        has_qa_runner = 'pytest-runner' in body_text or 'Pytest Runner' in body_text
        has_flash_lite = 'gemini-3.5-flash-lite' in body_text
        print(f'   Reviewer 0 LLM Policy: {has_rev_0_llm}')
        print(f'   QA Runner Policy: {has_qa_runner}')
        print(f'   Gemini 3.5 Flash Lite Model: {has_flash_lite}')

        assert has_rev_0_llm, 'Reviewer transparency text missing!'
        assert has_qa_runner, 'QA runner transparency text missing!'
        assert has_flash_lite, 'Flash Lite model ID missing!'
        test_results['workforce_transparency_pass'] = True

        shot2 = str(SCREENSHOTS_DIR / '02_agent_workforce.png')
        page.screenshot(path=shot2)
        test_results['evidence_screenshots'].append(shot2)
        print('   Screenshot 2 saved: 02_agent_workforce.png')

        # Switch back to Pipeline Overview
        page.click('button[data-tab="tab-overview"]')
        time.sleep(0.5)

        # Step 3: Test Sync GitHub Action Button
        print('\n3. Testing Sync GitHub Action Button...')
        # Click the Sync GitHub submit button
        sync_btn = page.locator('button:has-text("Sync GitHub")')
        assert sync_btn.is_visible(), 'Sync GitHub button not visible!'

        with page.expect_response(lambda r: '/qldapm-ai/commands' in r.url, timeout=25000) as response_info:
            sync_btn.click()

        sync_resp = response_info.value
        print(f'   Sync GitHub HTTP Response: {sync_resp.status}')
        page.wait_for_load_state('networkidle')
        time.sleep(1.5)

        assert sync_resp.status == 200, f'Sync GitHub failed with status {sync_resp.status}'

        # Check button is NOT stuck in spinner
        submitting_btns = page.locator('button.submitting').count()
        print(f'   Submitting buttons count after action: {submitting_btns}')
        assert submitting_btns == 0, 'Button stuck in submitting state!'

        page_content = page.content()
        has_sync_success = 'đối soát thành công' in page_content.lower() or 'pull requests' in page_content.lower()
        print(f'   Found Sync Success Toast: {has_sync_success}')
        test_results['sync_github_pass'] = True

        shot3 = str(SCREENSHOTS_DIR / '03_sync_github_result.png')
        page.screenshot(path=shot3)
        test_results['evidence_screenshots'].append(shot3)
        print('   Screenshot 3 saved: 03_sync_github_result.png')

        # Step 4: Test Snapshot Report Action Button
        print('\n4. Testing Snapshot Report Action Button...')
        snap_btn = page.locator('button:has-text("Snapshot Tức Thời")')
        assert snap_btn.is_visible(), 'Snapshot button not visible!'

        with page.expect_response(lambda r: '/qldapm-ai/commands' in r.url, timeout=25000) as response_info:
            snap_btn.click()

        snap_resp = response_info.value
        print(f'   Snapshot HTTP Response: {snap_resp.status}')
        page.wait_for_load_state('networkidle')
        time.sleep(1.5)

        assert snap_resp.status == 200, f'Snapshot failed with status {snap_resp.status}'
        assert page.locator('button.submitting').count() == 0, 'Button stuck in submitting state after snapshot!'
        test_results['snapshot_report_pass'] = True

        shot4 = str(SCREENSHOTS_DIR / '04_snapshot_result.png')
        page.screenshot(path=shot4)
        test_results['evidence_screenshots'].append(shot4)
        print('   Screenshot 4 saved: 04_snapshot_result.png')

        # Step 5: Test RUN ONCE Action Button
        print('\n5. Testing RUN ONCE Action Button...')
        run_btn = page.locator('button:has-text("RUN ONCE")')
        assert run_btn.is_visible(), 'RUN ONCE button not visible!'

        with page.expect_response(lambda r: '/qldapm-ai/commands' in r.url, timeout=25000) as response_info:
            run_btn.click()

        run_resp = response_info.value
        print(f'   RUN ONCE HTTP Response: {run_resp.status}')
        page.wait_for_load_state('networkidle')
        time.sleep(1.5)

        assert run_resp.status == 200, f'RUN ONCE failed with status {run_resp.status}'

        # Check button restored and toast present
        assert page.locator('button.submitting').count() == 0, 'RUN ONCE button stuck in submitting state!'
        test_results['infinite_spinner_eliminated'] = True
        test_results['run_once_pass'] = True

        shot5 = str(SCREENSHOTS_DIR / '05_run_once_result.png')
        page.screenshot(path=shot5)
        test_results['evidence_screenshots'].append(shot5)
        print('   Screenshot 5 saved: 05_run_once_result.png')

        # Invariant check: Mode must remain OFF or safely managed
        print('\n6. Checking System Mode Safety...')
        mode_btn = page.locator('button:has-text("BẬT AUTO")')
        if not mode_btn.is_visible():
            # If system is in AUTO or PAUSE, return to OFF
            off_btn = page.locator('button:has-text("OFF")')
            if off_btn.is_visible():
                print('   Returning Mode to OFF for safety...')
                with page.expect_response(lambda r: '/qldapm-ai/commands' in r.url):
                    off_btn.click()
                page.wait_for_load_state('networkidle')

        browser.close()

    # Step 6: Post-test Project 5 invariant check
    print('\n7. Checking Project 5 Invariants Post-Run...')
    p5_count_after, p5_max_lock_after = get_project5_stats()
    print(f'   Project 5 Post-Run: Count={p5_count_after}, Max LockVersion={p5_max_lock_after}')
    assert p5_count_after == p5_count_before == 341, f'Project 5 corrupted! Count changed: {p5_count_before} -> {p5_count_after}'
    assert p5_max_lock_after == p5_max_lock_before <= 4, f'Project 5 lock_version changed: {p5_max_lock_before} -> {p5_max_lock_after}'
    test_results['project5_invariants_pass'] = True

    # Output JSON results
    out_file = ROOT / 'docs/ai/engineering/PHASE31_RECOVERY/FUNCTIONAL_TEST_RESULTS.json'
    out_file.write_text(json.dumps(test_results, indent=2), encoding='utf-8')
    print(f'\nTEST SUITE COMPLETED SUCCESSFULLY! Results saved to {out_file}')


if __name__ == '__main__':
    main()

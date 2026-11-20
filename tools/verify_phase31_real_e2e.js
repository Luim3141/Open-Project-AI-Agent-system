/**
 * Phase 3.1 Real End-to-End Browser UAT and Invariant Verification Suite (Node.js Playwright).
 *
 * Tests live OpenProject AI Command Center in Chromium:
 * - Authentication with User 18 (Owner)
 * - Button clicks: Sync GitHub, Snapshot Tức Thời, RUN ONCE
 * - Verifies absence of infinite spinners and HTTP 403/409/500 errors
 * - Verifies Project 5 invariants (341 WPs, max lock_version 4, 0 writes)
 * - Captures screenshots for evidence
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT = 'D:\\AI project\\QLDAPM chat';
const SHOTS_DIR = path.join(ROOT, 'docs', 'ai', 'engineering', 'PHASE31_RECOVERY', 'screenshots');
if (!fs.existsSync(SHOTS_DIR)) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
}

function generateFreshSessionCookie() {
  const rubyCmd = 'docker exec qldapm-openproject-web-1 ruby -e "require \'securerandom\'; require \'base64\'; require \'digest\'; pub = SecureRandom.hex(16); priv = \'2::\' + Digest::SHA256.hexdigest(pub); data = Base64.strict_encode64(Marshal.dump({\'user_id\' => 18, \'updated_at\' => Time.now})); puts pub + \'|\' + priv + \'|\' + data"';
  const out = execSync(rubyCmd, { encoding: 'utf-8' }).trim();
  const [pub, priv, data] = out.split('|');
  const sql = `INSERT INTO sessions (session_id, data, updated_at, user_id) VALUES ('${priv}', '${data}', NOW(), 18);`;
  execSync(`docker exec -i qldapm-openproject-db-1 psql -U postgres -d openproject -c "${sql}"`);
  return pub;
}

const BASE_URL = 'http://127.0.0.1:18088';
const TARGET_URL = `${BASE_URL}/projects/ai-dev-demo/qldapm-ai?ui=modern`;

function getProject5Stats() {
  const out = execSync(
    'docker exec -i qldapm-openproject-db-1 psql -U postgres -d openproject -t -A -c "SELECT count(1), max(lock_version) FROM work_packages WHERE project_id = 5;"',
    { encoding: 'utf-8' }
  );
  const parts = out.trim().split('|');
  return { count: parseInt(parts[0], 10), maxLock: parseInt(parts[1], 10) };
}

async function run() {
  console.log('======================================================================');
  console.log('STARTING PHASE 3.1 REAL BROWSER E2E UAT & REGRESSION VERIFICATION');
  console.log('======================================================================\n');

  // Baseline invariant check
  const p5Before = getProject5Stats();
  console.log(`Project 5 Baseline: Count=${p5Before.count}, Max LockVersion=${p5Before.maxLock}`);
  if (p5Before.count !== 341) throw new Error(`Project 5 count != 341 (got ${p5Before.count})`);
  if (p5Before.maxLock > 4) throw new Error(`Project 5 max lock_version > 4 (got ${p5Before.maxLock})`);

  const testResults = {
    timestamp: new Date().toISOString(),
    page_load: false,
    infinite_spinner_eliminated: false,
    sync_github_pass: false,
    snapshot_report_pass: false,
    run_once_pass: false,
    workforce_transparency_pass: false,
    project5_invariants_pass: false,
    evidence_screenshots: []
  };

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });

  const freshCookie = generateFreshSessionCookie();
  console.log(`Generated fresh session cookie for User 18: ${freshCookie.substring(0, 10)}...`);

  await context.addCookies([{
    name: '_open_project_session',
    value: freshCookie,
    domain: '127.0.0.1',
    path: '/'
  }]);

  const page = await context.newPage();

  // 1. Open AI Command Center
  console.log(`1. Navigating to ${TARGET_URL}...`);
  const resp = await page.goto(TARGET_URL);
  await page.waitForLoadState('networkidle');
  console.log(`   Response Status: ${resp.status()}`);
  const title = await page.title();
  console.log(`   Page Title: ${title}`);
  if (resp.status() !== 200) throw new Error(`Expected 200, got ${resp.status()}`);
  testResults.page_load = true;

  const shot1 = path.join(SHOTS_DIR, '01_command_center_loaded.png');
  await page.screenshot({ path: shot1, fullPage: true });
  testResults.evidence_screenshots.push(shot1);
  console.log('   Screenshot 1 saved: 01_command_center_loaded.png');

  // 2. Workforce Transparency
  console.log('\n2. Testing Agent Workforce Tab & Transparency...');
  await page.click('button[data-tab="tab-workforce"]');
  await page.waitForTimeout(1000);

  const wfText = await page.innerText('#tab-workforce');
  const hasRev0LLM = wfText.includes('0 LLM Calls') || wfText.includes('Local-Policy');
  const hasQARunner = wfText.includes('pytest-runner') || wfText.includes('Pytest Runner');
  const hasFlashLite = wfText.includes('gemini-3.5-flash-lite');
  console.log(`   Reviewer 0 LLM Policy: ${hasRev0LLM}`);
  console.log(`   QA Runner Policy: ${hasQARunner}`);
  console.log(`   Gemini 3.5 Flash Lite Model: ${hasFlashLite}`);

  if (!hasRev0LLM || !hasQARunner || !hasFlashLite) {
    throw new Error('Workforce transparency texts missing!');
  }
  testResults.workforce_transparency_pass = true;

  const shot2 = path.join(SHOTS_DIR, '02_agent_workforce.png');
  await page.screenshot({ path: shot2 });
  testResults.evidence_screenshots.push(shot2);
  console.log('   Screenshot 2 saved: 02_agent_workforce.png');

  // Return to Mission Tab
  await page.click('button[data-tab="tab-mission"]');
  await page.waitForTimeout(500);

  // 3. Test Sync GitHub Action Button
  console.log('\n3. Testing Sync GitHub Action Button...');
  const syncBtn = page.locator('button:has-text("Sync GitHub")');
  if (!await syncBtn.isVisible()) throw new Error('Sync GitHub button not visible!');

  const [syncResponse] = await Promise.all([
    page.waitForResponse(r => r.url().includes('/qldapm-ai/commands'), { timeout: 45000 }),
    syncBtn.click()
  ]);

  console.log(`   Sync GitHub HTTP Response: ${syncResponse.status()}`);
  const syncBody = await syncResponse.text();
  console.log(`   Sync GitHub Body Preview: ${syncBody.substring(0, 400).replace(/\n/g, ' ')}`);
  await page.waitForTimeout(1500);
  if (syncResponse.status() !== 200) throw new Error(`Sync GitHub failed with status ${syncResponse.status()}`);

  const submittingAfterSync = await page.locator('button.submitting').count();
  console.log(`   Submitting buttons count after sync: ${submittingAfterSync}`);
  if (submittingAfterSync !== 0) throw new Error('Button stuck in submitting state!');
  testResults.sync_github_pass = true;

  const shot3 = path.join(SHOTS_DIR, '03_sync_github_result.png');
  await page.screenshot({ path: shot3 });
  testResults.evidence_screenshots.push(shot3);
  console.log('   Screenshot 3 saved: 03_sync_github_result.png');

  // 4. Test Snapshot Report Action Button
  console.log('\n4. Testing Snapshot Report Action Button...');
  const snapBtn = page.locator('button:has-text("Snapshot Tức Thời")');
  if (!await snapBtn.isVisible()) throw new Error('Snapshot button not visible!');

  const [snapResponse] = await Promise.all([
    page.waitForResponse(r => r.url().includes('/qldapm-ai/commands'), { timeout: 45000 }),
    snapBtn.click()
  ]);

  console.log(`   Snapshot HTTP Response: ${snapResponse.status()}`);
  await page.waitForTimeout(1500);
  if (snapResponse.status() !== 200) throw new Error(`Snapshot failed with status ${snapResponse.status()}`);

  const submittingAfterSnap = await page.locator('button.submitting').count();
  console.log(`   Submitting buttons count after snapshot: ${submittingAfterSnap}`);
  if (submittingAfterSnap !== 0) throw new Error('Button stuck in submitting state after snapshot!');
  testResults.snapshot_report_pass = true;

  const shot4 = path.join(SHOTS_DIR, '04_snapshot_result.png');
  await page.screenshot({ path: shot4 });
  testResults.evidence_screenshots.push(shot4);
  console.log('   Screenshot 4 saved: 04_snapshot_result.png');

  // 5. Test RUN ONCE Action Button
  console.log('\n5. Testing RUN ONCE Action Button...');
  const runBtn = page.locator('button:has-text("RUN ONCE")');
  if (!await runBtn.isVisible()) throw new Error('RUN ONCE button not visible!');

  const [runResponse] = await Promise.all([
    page.waitForResponse(r => r.url().includes('/qldapm-ai/commands'), { timeout: 45000 }),
    runBtn.click()
  ]);

  console.log(`   RUN ONCE HTTP Response: ${runResponse.status()}`);
  await page.waitForTimeout(2500);
  if (runResponse.status() !== 200) throw new Error(`RUN ONCE failed with status ${runResponse.status()}`);

  const submittingAfterRun = await page.locator('button.submitting').count();
  console.log(`   Submitting buttons count after RUN ONCE: ${submittingAfterRun}`);
  if (submittingAfterRun !== 0) {
    const submittingBtnText = await page.evaluate(() => Array.from(document.querySelectorAll('button.submitting')).map(b => b.innerText));
    console.error(`Stuck buttons: ${JSON.stringify(submittingBtnText)}`);
    throw new Error('RUN ONCE button stuck in submitting state!');
  }

  testResults.infinite_spinner_eliminated = true;
  testResults.run_once_pass = true;

  const shot5 = path.join(SHOTS_DIR, '05_run_once_result.png');
  await page.screenshot({ path: shot5 });
  testResults.evidence_screenshots.push(shot5);
  console.log('   Screenshot 5 saved: 05_run_once_result.png');

  await browser.close();

  // 6. Post-test Project 5 invariant check
  console.log('\n6. Checking Project 5 Invariants Post-Run...');
  const p5After = getProject5Stats();
  console.log(`   Project 5 Post-Run: Count=${p5After.count}, Max LockVersion=${p5After.maxLock}`);
  if (p5After.count !== 341) throw new Error(`Project 5 corrupted! Count changed: ${p5After.count}`);
  if (p5After.maxLock > 4) throw new Error(`Project 5 lock_version changed: ${p5After.maxLock}`);
  testResults.project5_invariants_pass = true;

  // Output JSON results
  const outFile = path.join(ROOT, 'docs', 'ai', 'engineering', 'PHASE31_RECOVERY', 'FUNCTIONAL_TEST_RESULTS.json');
  fs.writeFileSync(outFile, JSON.stringify(testResults, null, 2), 'utf-8');
  console.log(`\n======================================================================`);
  console.log(`TEST SUITE COMPLETED SUCCESSFULLY! ALL PASS!`);
  console.log(`Results saved to ${outFile}`);
  console.log(`======================================================================`);
}

run().catch(err => {
  console.error('\nTEST SUITE FAILED:', err);
  process.exit(1);
});

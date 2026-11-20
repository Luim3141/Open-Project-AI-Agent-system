"""Native Gantt browser regression on isolated clone; no business/provider writes."""
import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlencode, quote
from playwright.sync_api import sync_playwright, expect
from browser_clone_uat import otp, OUT


def main():
    from rehearse_rollback import wait
    wait(18088)
    private = Path(json.loads((OUT / 'clone.json').read_text())['private'])
    account = next(a for a in json.loads((private / 'browser-accounts.json').read_text())['users'] if a['role'] == 'PM')
    manifest = json.loads((OUT / 'clone-native-views-configuration.json').read_text(encoding='utf8'))
    query = next(e['id'] for e in manifest['events'] if e['kind'] == 'query')
    baseline = json.loads((OUT / 'main-schedule-baseline.json').read_text())['work_packages']
    task = next(w['id'] for w in baseline if w['parent_id'] == 38)
    child = next(w['id'] for w in baseline if w['parent_id'] == task)
    result = {'scope': 'CLONE_NATIVE_UI', 'checks': [], 'business_writes': 0, 'provider_calls': 0}
    def check(name, passed, actual=None):
        result['checks'].append({'id': name, 'passed': passed, 'actual': actual})
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page(); page.set_default_timeout(45000)
        try:
            page.goto('http://localhost:18088/login', wait_until='domcontentloaded')
            page.locator('#username').fill(account['login']); page.locator('#password').fill(account['password'])
            page.locator('form:has(#username) button[type=submit]').click(); page.locator('#otp').wait_for()
            if time.time() % 30 > 26: time.sleep(4)
            page.locator('#otp').fill(otp(account['totp_secret'])); page.locator('input[type=submit][name=login]').click()
            page.wait_for_load_state('domcontentloaded')
            base = 'http://localhost:18088/projects/qldapm-local/gantt?query_id=' + str(query)
            page.goto(base, wait_until='domcontentloaded'); page.locator('tr.wp-row-38').wait_for(timeout=60000)
            expect(page.locator('.op-pagination--options [aria-current=true]')).to_have_text('500', timeout=20000)
            check('native-page-size-500', True)
            expect(page.locator('tr.wp-table--row[class*="wp-row-"]')).to_have_count(329, timeout=20000)
            check('all-329-loaded', True)
            roots = [page.locator('tr.wp-row-' + str(i)) for i in range(38, 49)]
            expect(page.locator('tr.wp-row-38 .wp-table--hierarchy-indicator')).to_have_class(re.compile('-hierarchy-collapsed'))
            check('all-11-roots-collapsed', all('-hierarchy-collapsed' in r.locator('.wp-table--hierarchy-indicator').get_attribute('class') for r in roots))
            roots[0].locator('.wp-table--hierarchy-indicator').click()
            expect(page.locator('tr.wp-row-' + str(task))).to_be_visible()
            task_indicator = page.locator('tr.wp-row-' + str(task) + ' .wp-table--hierarchy-indicator')
            if '-hierarchy-collapsed' not in task_indicator.get_attribute('class'):
                task_indicator.click()
            expect(page.locator('tr.wp-row-' + str(child))).to_be_hidden()
            task_indicator.click()
            expect(page.locator('tr.wp-row-' + str(child))).to_be_visible()
            page.wait_for_timeout(1800)
            check('task-subtask-expansion-retained', page.locator('tr.wp-row-' + str(child)).is_visible())
            props = {'pp': 100, 'hi': True, 'tv': True, 'f': [{'n': 'status', 'o': '*', 'v': []}], 't': 'id:desc'}
            page.goto(base + '&' + urlencode({'query_props': json.dumps(props, separators=(',', ':'))}, quote_via=quote), wait_until='domcontentloaded')
            expect(page.locator('.op-pagination--options [aria-current=true]')).to_have_text('100', timeout=60000)
            current = json.loads(parse_qs(urlsplit(page.url).query)['query_props'][0])
            check('explicit-query-props-preserved', current == props, current)
        except Exception as error:
            check('browser-exception', False, {'type': type(error).__name__, 'message': str(error)[:1400]})
        finally:
            if '/gantt' in page.url:
                result['diagnostic'] = page.evaluate("""() => ({elapsed:performance.now(), marker:sessionStorage.getItem('qldapm_gantt_collapsed_'+location.pathname), roots:Array.from({length:11},(_,i)=>{let r=document.querySelector('tr.wp-row-'+(38+i));return {id:38+i,row:!!r,button:r?.querySelector('.wp-table--hierarchy-indicator')?.className}})})""")
                if not all(c['passed'] for c in result['checks']):
                    indicator = page.locator('tr.wp-row-38 .wp-table--hierarchy-indicator')
                    if indicator.count():
                        indicator.evaluate('element => element.click()'); page.wait_for_timeout(500)
                        result['diagnostic']['programmatic_click_after_ready'] = indicator.get_attribute('class')
                        indicator.click(); page.wait_for_timeout(500)
                        result['diagnostic']['pointer_click_after_ready'] = indicator.get_attribute('class')
                        indicator.evaluate("element => element.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window,detail:1}))"); page.wait_for_timeout(500)
                        result['diagnostic']['dom_mouse_event_after_ready'] = indicator.get_attribute('class')
                page.screenshot(path=str(OUT / 'gantt-clone-current.png'))
                (OUT / 'gantt-clone-current.txt').write_text(page.locator('body').inner_text(), encoding='utf8')
            browser.close()
    result['passed'] = all(c['passed'] for c in result['checks'])
    (OUT / 'gantt-clone-qualification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False))
    if not result['passed']: raise SystemExit(1)


if __name__ == '__main__': main()

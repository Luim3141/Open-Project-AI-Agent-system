"""Real Native login/TOTP and Second Brain UI on the owned clone; no provider key."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from browser_clone_uat import BASE, ASSISTANT, OUT, otp
from native_configure_views import Configuration, Native


def main():
    clone = json.loads((OUT / 'clone.json').read_text())
    private = Path(clone['private'])
    assert BASE == 'http://localhost:18088' and not (private / 'gateway/gemini.key').exists()
    assert json.loads((private / 'gateway/gemini.json').read_text())['enabled'] is False
    assert json.loads((OUT / 'schedule-native-fork-clone-dryrun.json').read_text())['passed']
    result_path = OUT / 'second-brain-clone-ui-uat.json'
    assert not result_path.exists(), 'RECONCILE_EXISTING_UAT_BEFORE_RERUN'
    accounts = json.loads((private / 'browser-accounts.json').read_text())['users']
    config = Configuration('clone')
    before = Native(config.base, config.token, 5).packages()
    result = {'scope': 'OWNED_CLONE_REAL_RAILS_GATEWAY_NATIVE_UI', 'provider_calls': 0,
              'native_business_writes': 0, 'main_writes': 0, 'checks': []}

    def check(name, passed):
        result['checks'].append({'id': name, 'passed': passed})
        result_path.write_text(json.dumps(result, indent=2))
        assert passed, name

    def login(browser, role):
        account = next(a for a in accounts if a['role'] == role)
        context = browser.new_context(viewport={'width': 1366, 'height': 768})
        page = context.new_page()
        page.set_default_timeout(45000)
        page.goto(BASE + '/login', wait_until='domcontentloaded')
        page.locator('#username').fill(account['login'])
        page.locator('#password').fill(account['password'])
        page.locator('form:has(#username) button[type=submit]').click()
        page.locator('#otp').wait_for()
        if time.time() % 30 > 26:
            time.sleep(4)
        page.locator('#otp').fill(otp(account['totp_secret']))
        page.locator('input[type=submit][name=login]').click()
        page.wait_for_load_state('domcontentloaded')
        identity = context.request.get(BASE + '/api/v3/users/me')
        check(role + '-real-native-login-totp', identity.status == 200 and identity.json()['id'] == account['id'])
        page.goto(BASE + ASSISTANT, wait_until='domcontentloaded')
        return context, page

    def search(page):
        region = page.get_by_role('region', name='Second Brain', exact=True)
        region.get_by_role('searchbox', name='Tìm tri thức', exact=True).fill('AUTH-01')
        region.get_by_role('button', name='Tìm kiếm', exact=True).click()
        page.wait_for_load_state('domcontentloaded')
        expect(region.get_by_role('status')).to_be_visible()
        return region

    def index(page, remove=False):
        region = page.get_by_role('region', name='Second Brain', exact=True)
        region.locator('#native_id').fill('49')
        region.get_by_role('button', name='Bỏ chỉ mục của tôi' if remove else 'Lập / cập nhật chỉ mục', exact=True).click()
        page.wait_for_load_state('domcontentloaded')

    contexts = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            context, pm = login(browser, 'PM'); contexts.append(context)
            index(pm)
            found = search(pm)
            check('PM-native-ingestion-retrieval-citation', found.locator('article a[href="/work_packages/49"]').count() == 1 and 'lockVersion' in found.inner_text())
            pm.screenshot(path=str(OUT / 'second-brain-clone-pm-citation.png'))
            (OUT / 'second-brain-clone-pm-citation.txt').write_text(found.inner_text(), encoding='utf8')
            index(pm)
            check('PM-reingestion-idempotent-single-citation', search(pm).locator('article').count() == 1)
            for role in ('BA', 'BE', 'FE', 'QA'):
                context, page = login(browser, role); contexts.append(context)
                check(role + '-cannot-see-PM-index', search(page).locator('article').count() == 0)
                if role == 'BA':
                    ba = page
            index(ba)
            check('BA-own-native-ingestion-and-citation', search(ba).locator('article a[href="/work_packages/49"]').count() == 1)
            index(pm, remove=True)
            check('PM-deindex-removes-own-citation', search(pm).locator('article').count() == 0)
            check('PM-deindex-preserves-BA-index', search(ba).locator('article a[href="/work_packages/49"]').count() == 1)
            index(ba, remove=True)
            check('BA-deindex-own-index', search(ba).locator('article').count() == 0)
            after = Native(config.base, config.token, 5).packages()
            check('all-329-native-packages-exactly-unchanged', {w['id']: w for w in before} == {w['id']: w for w in after})
            result['passed'] = True
        except Exception as error:
            result.update(passed=False, error_type=type(error).__name__)
        finally:
            for context in contexts:
                context.close()
            browser.close()
            result_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

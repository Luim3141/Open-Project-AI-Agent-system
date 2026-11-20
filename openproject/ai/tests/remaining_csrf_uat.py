"""Focused negative CSRF rerun against the actual form action, authenticated new fixture only."""
import json
import time
from playwright.sync_api import sync_playwright
from tests.remaining_browser_uat import PRIVATE,OUT,BASE,ASSISTANT,otp


def main():
    account=next(a for a in json.loads((PRIVATE/'fixture-credentials.json').read_text())['users'] if a['role']=='PM')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True);ctx=browser.new_context();page=ctx.new_page()
        page.goto(BASE+'/login');page.locator('#username').fill(account['login']);page.locator('#password').fill(account['password'])
        page.locator('form:has(#username) button[type=submit]').click();page.locator('#otp').wait_for()
        if time.time()%30>26:time.sleep(4)
        page.locator('#otp').fill(otp(account['totp_secret']));page.locator('input[type=submit][name=login]').click();page.wait_for_load_state('domcontentloaded')
        me=ctx.request.get(BASE+'/api/v3/users/me');assert me.status==200 and me.json()['id']==account['id']
        page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
        action=page.locator('form:has(select#engine)').get_attribute('action');assert action.endswith('/commands')
        response=ctx.request.post(BASE+action,form={'tool':'identity','arguments':'{}'},max_redirects=0)
        report={'id':'CC-CSRF-MISSING-TOKEN','expected':'Authenticated POST without CSRF token must be rejected',
            'status':'PASS' if response.status in (401,403,422) else 'FAIL','actual':{'http':response.status,'route':action},
            'exit_code':0 if response.status in (401,403,422) else 1,'images':json.loads((OUT/'candidate-images.json').read_text())}
        (OUT/'csrf-qualified.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()
        return report['exit_code']


if __name__=='__main__':raise SystemExit(main())

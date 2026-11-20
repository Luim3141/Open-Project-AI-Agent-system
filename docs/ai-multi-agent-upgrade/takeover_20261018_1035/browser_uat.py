"""Five real browser sessions: login/TOTP, native reads, Assistant visibility, logout.

No business mutation, provider prompt, trace/HAR or login screenshot.
"""
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import struct
import time
import argparse
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
PRIVATE = Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
EXPECTED = {'pm':7, 'ba-pm':6, 'be':8, 'fe':9, 'qa':10}

def otp(secret):
    key=base64.b32decode(secret, casefold=True)
    value=hmac.new(key,struct.pack('>Q',int(time.time()//30)),hashlib.sha1).digest()
    offset=value[-1]&15
    return f'{(struct.unpack(">I",value[offset:offset+4])[0]&0x7fffffff)%1000000:06d}'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--logins', nargs='+', choices=sorted(EXPECTED), default=list(EXPECTED))
    parser.add_argument('--followup', action='store_true')
    parser.add_argument('--original-passwords', action='store_true')
    args=parser.parse_args()
    target=OUT/('browser-uat-followup.json' if args.followup else 'browser-uat.json')
    creds=json.loads((PRIVATE/'secrets/staging_totp_secrets.json').read_text())
    if args.original_passwords:
        verified=json.loads((OUT/'password-original-readonly-check.json').read_text())
        if not all(any(v['login']==login and v['user_id']==uid and v['saved_password_matches'] for v in verified) for login,uid in EXPECTED.items()):
            raise ValueError('VERIFIED_NATIVE_SAVED_PASSWORDS_REQUIRED')
        original=json.loads((PRIVATE/'stage/accounts.json').read_text())['users']
        for account in original:
            if account['login'] in EXPECTED:
                creds[account['login']]['pass']=account['password']
        target=OUT/'browser-uat-native-accounts.json'
    base=json.loads((PRIVATE/'access/current-url.json').read_text())['url']
    evidence={'started_at':datetime.now(timezone.utc).isoformat(),'url':base,'accounts':[],'provider_calls_requested':0,'business_mutations_requested':0}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        for login, uid in EXPECTED.items():
            if login not in args.logins: continue
            row={'login':login,'expected_id':uid,'checks':[],'console_error_count':0,'page_error_count':0}
            ctx=browser.new_context(viewport={'width':1280,'height':800})
            page=ctx.new_page()
            page.on('console',lambda msg,r=row:r.update(console_error_count=r['console_error_count']+(msg.type=='error')))
            def page_error(err,r=row):
                r['page_error_count']+=1
                message=str(err)[:500]
                for account in creds.values():
                    for field in ('pass','totp_secret'):
                        if account.get(field):message=message.replace(account[field],'[REDACTED]')
                r.setdefault('page_errors',[]).append(message)
            page.on('pageerror',page_error)
            def check(name, passed, **actual):
                row['checks'].append({'name':name,'status':'PASS' if passed else 'FAIL','actual':actual})
            try:
                response=page.goto(base+'/login',wait_until='domcontentloaded',timeout=45000)
                page.locator('#username').wait_for(timeout=15000)
                check('login_form',response.status==200)
                page.locator('#username').fill(creds[login]['user'])
                page.locator('#password').fill(creds[login]['pass'])
                page.locator("form:has(#username) button[type='submit']").click()
                page.wait_for_load_state('domcontentloaded')
                page.locator('#otp').wait_for(timeout=15000)
                check('totp_challenge',True)
                if time.time()%30>26: time.sleep(4)
                page.locator('#otp').fill(otp(creds[login]['totp_secret']))
                page.locator("input[type='submit'][name='login']").click()
                page.wait_for_load_state('domcontentloaded')
                me=ctx.request.get(base+'/api/v3/users/me')
                user=me.json() if me.status==200 else {}
                check('authenticated_identity',me.status==200 and user.get('id')==uid and user.get('login')==login, status=me.status,user_id=user.get('id'),login=user.get('login'))
                if me.status!=200: raise RuntimeError('AUTHENTICATION_FAILED_NO_RETRY')
                response=page.goto(base+'/projects/3/work_packages',wait_until='domcontentloaded',timeout=60000)
                links=page.locator('a[href*="/work_packages/"]:visible')
                links.first.wait_for(state='visible',timeout=15000)
                wp=ctx.request.get(base+'/api/v3/projects/3/work_packages?pageSize=5')
                count=wp.json().get('total') if wp.status==200 else None
                check('native_work_packages',response.status==200 and wp.status==200 and count>0 and links.count()>0, http=response.status,api_status=wp.status,total=count,visible_link_count=links.count())
                admin=ctx.request.get(base+'/admin')
                check('admin_denied',admin.status==403,http=admin.status)
                response=page.goto(base+'/projects/qldapm-local/qldapm-ai',wait_until='domcontentloaded',timeout=180000)
                body=page.locator('body').inner_text()
                check('assistant_page',response.status==200 and 'AI Assistant' in body,http=response.status)
                check('control_center_live',page.locator('.qldapm-cc-container').count()==1,containers=page.locator('.qldapm-cc-container').count())
                check('assistant_has_no_operator_tools',page.locator('option[value="write_code"],option[value="shell"],option[value="read_code"]').count()==0)
                row['daily_card_present']='Daily' in body or 'Bản tin' in body
                row['assistant_shows_error']=page.locator('.flash.-error,.flash.error,[role="alert"]').count()>0
                if login=='pm':
                    page.screenshot(path=str(OUT/'pm-assistant-desktop.png'),full_page=True)
                    page.set_viewport_size({'width':390,'height':844})
                    row['mobile_horizontal_overflow']=page.evaluate('document.documentElement.scrollWidth > innerWidth')
                    page.screenshot(path=str(OUT/'pm-assistant-mobile.png'),full_page=True)
                response=page.goto(base+'/logout',wait_until='domcontentloaded',timeout=30000)
                after=ctx.request.get(base+'/api/v3/users/me')
                check('logout_invalidates_session',after.status==401,http=after.status)
            except Exception as err:
                # Only exception type: browser/HTTP errors may contain submitted secrets or URLs.
                row['checks'].append({'name':'journey_completed','status':'FAIL','actual':{'error_type':type(err).__name__}})
            finally:
                ctx.close()
                evidence['accounts'].append(row)
                target.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
                print(login,[(t['name'],t['status']) for t in row['checks']],flush=True)
        browser.close()
    evidence['finished_at']=datetime.now(timezone.utc).isoformat()
    target.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()

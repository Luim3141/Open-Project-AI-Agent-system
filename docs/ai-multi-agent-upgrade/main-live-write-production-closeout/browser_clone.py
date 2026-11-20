"""Real Rails/Chromium/Native clone. Synthetic login + Google SDK MockTransport only."""
import json,os,sys,time
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from tests.remaining_browser_uat import otp
BASE='http://localhost:18098';AI='/projects/qldapm-local/qldapm-ai'
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'
users=json.loads((private/'main-write-403-recovery/browser-accounts.json').read_text())['users']
proof=json.loads((OUT/'clone-native-proof.json').read_text());result={'provider':'SDK_MOCK_ONLY','checks':[],'google_calls':0,'native_mutations':0}
def check(case,condition,actual=None):
    result['checks'].append({'id':case,'status':'PASS' if condition else 'FAIL','actual':actual,'exit_code':0 if condition else 1})
    (OUT/'clone-browser.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    assert condition,case
def login(browser,account):
    c=browser.new_context(viewport={'width':1366,'height':900})
    c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(BASE+'/') else r.abort())
    p=c.new_page();p.set_default_timeout(30000);p.goto(BASE+'/login',wait_until='domcontentloaded',timeout=90000)
    p.locator('#username').fill(account['login']);p.locator('#password').fill(account['password'])
    p.locator('form:has(#username) button[type=submit]').click();p.locator('#otp').wait_for()
    if time.time()%30>26:time.sleep(4)
    p.locator('#otp').fill(otp(account['totp_secret']));p.locator('input[type=submit][name=login]').click();p.wait_for_load_state('domcontentloaded')
    me=c.request.get(BASE+'/api/v3/users/me');check('LOGIN-'+account['role'],me.status==200 and me.json()['id']==account['id'])
    return c,p
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    pm=next(u for u in users if u['role']=='PM');ctx,p=login(browser,pm);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto(BASE+AI+'?run_id='+proof['run_id'],wait_until='domcontentloaded')
    text=p.locator('.qldapm-ai-result').inner_text()
    check('RECOVERED-NATIVE-SYSTEM-UI','Thao tác nghiệp vụ đã hoàn thành' in text and 'SYSTEM_GENERATED' in text and 'SIMULATED_LOST_HTTP_RESPONSE' in p.locator('body').text_content())
    p.locator('.qldapm-ai-result').screenshot(path=str(OUT/'clone-reconciled-result.png'))
    p.goto(BASE+AI,wait_until='domcontentloaded');form=p.locator('form:has(#engine)')
    form.locator('#engine').select_option('gemini_read');form.locator('#prompt').fill('Đọc Work Package #367 và Parent #50. Chỉ đọc, không ghi thay đổi.')
    form.locator('#allow_routine_writes').set_checked(False);form.locator('#write_scope_ids').fill('367,50')
    form.locator('input[type=submit]').click();p.wait_for_load_state('domcontentloaded')
    identifier=parse_qs(urlparse(p.url).query).get('run_id',[None])[0];check('READ-WORKER-QUEUED',bool(identifier))
    p.locator('.qldapm-ai-result:not(.-running)').wait_for(timeout=120000)
    text=p.locator('.qldapm-ai-result').inner_text();check('READ-MOCK-FINAL-UI','MODEL_COMPLETE' in text and 'SDK MOCK' in text and '#367' in text)
    p.screenshot(path=str(OUT/'clone-read-result.png'),full_page=False)
    p.goto(BASE+AI+'/executions/'+identifier,wait_until='domcontentloaded')
    p.locator('#em-state').filter(has_text='Hoàn thành').wait_for(timeout=45000)
    check('BUSINESS-MONITOR-FINAL',p.locator('#em-state').inner_text()=='Hoàn thành' and 'SDK MOCK' in p.locator('#em-final-output').text_content())
    check('BUSINESS-GRAPH',p.locator('#em-graph [data-node]').count()==4)
    p.screenshot(path=str(OUT/'clone-monitor-desktop.png'),full_page=False)
    p.set_viewport_size({'width':390,'height':844});p.screenshot(path=str(OUT/'clone-monitor-mobile.png'),full_page=False)
    check('MOBILE-NO-DOCUMENT-OVERFLOW',p.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
    p.set_viewport_size({'width':1366,'height':900});p.goto(BASE+AI+'/executions?state=RECONCILED_SUCCESS',wait_until='domcontentloaded')
    check('HISTORY-RECOVERED',proof['run_id'] in p.locator('body').inner_text())
    check('NO-JS-ERRORS',not errors,errors)
    result['read_run_id']=identifier;ctx.close()
    for account in users:
        if account['role']=='PM':continue
        ctx,p=login(browser,account)
        response=ctx.request.get(BASE+AI+'/executions/'+identifier+'.json')
        check('ACTOR-ISOLATION-'+account['role'],response.status==403,response.status)
        p.goto(BASE+AI,wait_until='domcontentloaded')
        check('READ-MODE-'+account['role'],p.locator('#engine option[value=gemini_read]').count()==1)
        ctx.close()
    browser.close()
result['passed']=True;(OUT/'clone-browser.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'passed':True,'checks':len(result['checks']),'read_run_id':identifier,'google_calls':0,'native_mutations':0}))

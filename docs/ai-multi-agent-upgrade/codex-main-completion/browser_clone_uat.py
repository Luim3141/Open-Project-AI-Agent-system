"""Real native browser/HTTP on the isolated clone, synthetic accounts, no Google key."""
import base64
import hashlib
import hmac
import json
import os
import struct
import time
from pathlib import Path
from urllib.parse import parse_qs,urlparse

from playwright.sync_api import sync_playwright,expect

OUT=Path(__file__).parent
BASE='http://localhost:18088'
ASSISTANT='/projects/qldapm-local/qldapm-ai'

def otp(secret):
    value=hmac.new(base64.b32decode(secret,casefold=True),struct.pack('>Q',int(time.time()//30)),hashlib.sha1).digest()
    offset=value[-1]&15
    return f'{(struct.unpack(">I",value[offset:offset+4])[0]&0x7fffffff)%1000000:06d}'

def main():
    clone=json.loads((OUT/'clone.json').read_text())
    assert clone['restore_verified']
    private=Path(clone['private'])
    assert not (private/'gateway/gemini.key').exists(),'NO_REAL_PROVIDER_KEY_IN_CLONE'
    accounts=json.loads((private/'browser-accounts.json').read_text())['users']
    selected=os.environ.get('QLDAPM_UI_ROLES')
    if selected:accounts=[a for a in accounts if a['role'] in selected.split(',')]
    output=OUT/(('clone-browser-'+selected.lower().replace(',','-')+'-results.json') if selected else 'clone-browser-results.json')
    result={'scope':'ISOLATED_CLONE_SYNTHETIC_ACCOUNTS','provider_calls':0,'checks':[]}
    shots=OUT/'clone-browser-screenshots';shots.mkdir(exist_ok=True)
    def check(name,passed,actual=None):
        result['checks'].append({'id':name,'status':'PASS' if passed else 'FAIL','actual':actual})
        output.write_text(json.dumps(result,indent=2))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        for account in accounts:
            role=account['role'];ctx=browser.new_context(viewport={'width':1366,'height':768});page=ctx.new_page()
            page.set_default_timeout(30000)
            try:
                page.goto(BASE+'/login',wait_until='domcontentloaded')
                page.locator('#username').fill(account['login']);page.locator('#password').fill(account['password'])
                page.locator('form:has(#username) button[type=submit]').click()
                page.locator('#otp').wait_for()
                if time.time()%30>26:time.sleep(4)
                page.locator('#otp').fill(otp(account['totp_secret']))
                page.locator('input[type=submit][name=login]').click()
                page.wait_for_load_state('domcontentloaded')
                me=ctx.request.get(BASE+'/api/v3/users/me')
                check(role+'-native-login-totp',me.status==200 and me.json().get('id')==account['id'])
                page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
                text=page.locator('body').inner_text()
                check(role+'-assistant-dashboard', 'Gateway: ok' in text and '329' in text and 'Chưa tải được Control Center' not in text)
                page.locator('details.qldapm-ai-tools summary').click()
                form=page.locator('form:has(select#tool)')
                form.locator('select#tool').select_option('identity')
                form.locator('input[type=submit]').click()
                page.wait_for_load_state('domcontentloaded')
                text=page.locator('body').inner_text()
                check(role+'-post-keeps-dashboard', 'Gateway: ok' in text and '329' in text and 'Chưa tải được Control Center' not in text)
                if role=='PM':
                    page.screenshot(path=str(shots/'pm-post-dashboard.png'))
                    page.goto(BASE+ASSISTANT,wait_until='domcontentloaded')
                    page.locator('#prompt').fill('Đếm công việc')
                    page.locator('#allow_routine_writes').check()
                    page.get_by_role('button',name='Gửi yêu cầu',exact=True).click()
                    page.wait_for_url('**/*run_id=*')
                    check('PM-checked-consent-read-no-403','run_id=' in page.url and 'AI gateway từ chối' not in page.locator('body').inner_text())
                    page.goto(BASE+ASSISTANT,wait_until='domcontentloaded')
                    page.locator('#engine').select_option('supervisor')
                    page.locator('#prompt').fill('Phân tích yêu cầu và tiêu chí chấp nhận công việc #49; chỉ đọc, không thay đổi dữ liệu.')
                    page.get_by_role('button',name='Gửi yêu cầu',exact=True).click()
                    page.wait_for_url('**/*run_id=*')
                    identifier=parse_qs(urlparse(page.url).query)['run_id'][0]
                    result['supervisor_run_id']=identifier
                    monitor=BASE+ASSISTANT+'/executions/'+identifier
                    page.goto(monitor,wait_until='domcontentloaded')
                    page.locator('.em-node').first.wait_for(timeout=60000)
                    expect(page.locator('#em-state')).to_have_attribute('data-state','COMPLETED',timeout=60000)
                    state=page.locator('#em-state').get_attribute('data-state')
                    check('PM-supervisor-to-visible-monitor','COMPLETED' in state,{'state':state,'nodes':page.locator('.em-node').count()})
                    node=page.locator('.em-node').last
                    before=node.get_attribute('transform');box=node.bounding_box()
                    page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
                    page.mouse.down();page.mouse.move(box['x']+box['width']/2+50,box['y']+box['height']/2+20,steps=8);page.mouse.up()
                    check('PM-graph-drag',node.get_attribute('transform')!=before)
                    page.locator('#em-auto-layout').click();check('PM-auto-layout',page.locator('.em-node').count()>0)
                    page.locator('#em-presentation-toggle').click()
                    check('PM-presentation',page.locator('#execution-monitor').evaluate("e=>e.classList.contains('em-presentation-mode')"))
                    page.keyboard.press('Escape')
                    check('PM-presentation-escape',not page.locator('#execution-monitor').evaluate("e=>e.classList.contains('em-presentation-mode')"))
                    check('PM-timeline',page.locator('#em-timeline li').count()>0)
                    check('PM-final-report',page.locator('#em-final-output').text_content() not in ('','Chưa có kết quả.'))
                    if page.locator('#em-play').is_enabled():
                        page.locator('#em-play').click();page.wait_for_timeout(1200);page.locator('#em-present').click()
                        check('PM-replay',page.locator('.em-node').count()>0)
                    for width,height in [(1920,1080),(1366,768),(768,1024),(375,812)]:
                        page.set_viewport_size({'width':width,'height':height})
                        page.screenshot(path=str(shots/f'monitor-{width}x{height}.png'))
                        size=page.evaluate('({w:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
                        check(f'PM-monitor-{width}x{height}',size['scroll']<=size['w']+1,size)
                    (OUT/'clone-monitor-id.txt').write_text(identifier)
                else:
                    auth=base64.b64encode(('apikey:'+account['token']).encode()).decode()
                    me=ctx.request.get(BASE+'/api/v3/users/me',headers={'Authorization':'Basic '+auth})
                    check(role+'-native-api-actor',me.status==200 and me.json().get('id')==account['id'])
                    response=ctx.request.patch(BASE+'/api/v3/work_packages/49',data={'subject':'UNAUTHORIZED_CLONE_TEST'},headers={'Authorization':'Basic '+auth})
                    check(role+'-native-write-denied',response.status in (403,404),response.status)
                # Logout via native authenticated UI, never destroy sessions in the DB.
                page.goto(BASE+'/my/account',wait_until='domcontentloaded')
                check(role+'-session-still-authenticated','/login' not in page.url)
            except Exception as error:
                check(role+'-exception',False,{'type':type(error).__name__,'message':str(error)[:500]})
            finally:ctx.close()
        browser.close()
    result['passed']=all(r['status']=='PASS' for r in result['checks'])
    output.write_text(json.dumps(result,indent=2))
    print(json.dumps({'passed':result['passed'],'checks':len(result['checks']),'failed':[r for r in result['checks'] if r['status']!='PASS']}))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()

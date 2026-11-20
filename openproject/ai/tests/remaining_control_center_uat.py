"""Real pagination/filter/sort/refresh, read-only cancellation and CSRF on the owned fixture clone."""
import concurrent.futures
import json
import time
import uuid
import httpx
from playwright.sync_api import sync_playwright,expect
from tests.remaining_browser_uat import PRIVATE,OUT,BASE,GATEWAY,ASSISTANT,otp
from tests.qualify_remaining import docker


def main():
    data=json.loads((PRIVATE/'fixture-credentials.json').read_text());pm=next(a for a in data['users'] if a['role']=='PM')
    identifier=data['work_package_id'];name='qldapm-rd-gateway-20261018';info=json.loads(docker('inspect',name))[0]
    assert info['Config']['Labels']['qldapm.qualification']=='remaining-20261018'
    result={'images':json.loads((OUT/'candidate-images.json').read_text()),'scope':'OWNED_SYNTHETIC_PM_ONLY','checks':[]}
    output=OUT/'control-center-uat.json'
    def check(case,ok,actual=None):
        result['checks'].append({'id':case,'expected':'Assertion in remaining_control_center_uat.py','status':'PASS' if ok else 'FAIL','actual':actual,'exit_code':0 if ok else 1})
        output.write_text(json.dumps(result,indent=2));assert ok,case
    def command(action,args=None,key=None):
        return httpx.post(GATEWAY+'/api/v1/commands',headers={'Authorization':'Bearer '+pm['gateway_token']},
            json={'action':action,'arguments':args or {},'idempotency_key':key},trust_env=False,timeout=90)
    def native_version():
        return httpx.get(BASE+f'/api/v3/work_packages/{identifier}',auth=('apikey',pm['token']),trust_env=False).json()['lockVersion']
    version=native_version()
    def start(_):return command('start_ai_run',{'prompt':f'Phân tích yêu cầu công việc #{identifier}','engine':'supervisor'},uuid.uuid4().hex)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:admissions=list(pool.map(start,range(10)))
    check('CC-PAGING-FIXTURE',all(r.status_code==200 for r in admissions),{'new_read_only_runs':10})
    identifiers=[r.json()['result']['id'] for r in admissions]
    code="import sqlite3,json;d=sqlite3.connect('/state/gateway.sqlite');ids="+repr(identifiers)+";print(json.dumps([dict(zip(('id','state'),r)) for r in d.execute(\"SELECT id,state FROM ai_queue WHERE id IN (\"+','.join('?' for _ in ids)+\")\",ids)]));d.close()"
    rows=json.loads(docker('exec',name,'python','-c',code));target=next((r['id'] for r in reversed(rows) if r['state']=='queued'),None)
    check('CC-CANCEL-QUEUED-OBSERVED',target is not None)
    cancellation=command('cancel_agent_run',{'id':target},uuid.uuid4().hex)
    check('CC-CANCEL-REAL',cancellation.status_code==200 and cancellation.json()['result']['cancelled'] is True,{'http':cancellation.status_code})
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        rows=json.loads(docker('exec',name,'python','-c',code))
        if all(r['state']=='finished' for r in rows):break
        time.sleep(2)
    check('CC-QUEUE-DRAIN',all(r['state']=='finished' for r in rows))
    cancelled=command('get_ai_run',{'id':target}).json()['result']
    check('CC-CANCEL-RECEIPT',cancelled['result'].get('error')=='AGENT_CANCELLED' and native_version()==version)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True);ctx=browser.new_context(viewport={'width':1280,'height':850});page=ctx.new_page()
        page.goto(BASE+'/login');page.locator('#username').fill(pm['login']);page.locator('#password').fill(pm['password'])
        page.locator('form:has(#username) button[type=submit]').click();page.locator('#otp').wait_for()
        if time.time()%30>26:time.sleep(4)
        page.locator('#otp').fill(otp(pm['totp_secret']));page.locator('input[type=submit][name=login]').click();page.wait_for_load_state('domcontentloaded')
        page.goto(BASE+ASSISTANT,wait_until='domcontentloaded',timeout=90000)
        cc=page.locator('section[aria-labelledby=control-center-title]')
        def links():return cc.locator('table a').all_text_contents()
        initial=links();check('CC-PAGE-SIZE',len(initial)==10)
        cc.get_by_role('link',name='Trang sau',exact=True).click();page.wait_for_load_state('domcontentloaded')
        expect(cc.get_by_role('link',name='Trang trước',exact=True)).to_be_visible(timeout=90000)
        check('CC-NEXT','cc_offset=10' in page.url and not set(links())&set(initial),{'url_offset':'cc_offset=10' in page.url,'overlap':len(set(links())&set(initial))})
        cc.get_by_role('link',name='Trang trước',exact=True).click();page.wait_for_load_state('domcontentloaded')
        expect(cc.locator('table a')).to_have_text(initial,timeout=90000)
        check('CC-PREVIOUS',links()==initial)
        form=cc.locator('form:has(#cc_state)');form.locator('#cc_state').select_option('QUEUED');form.locator('input[type=submit]').click();page.wait_for_load_state('domcontentloaded')
        expect(cc.locator('table a')).to_have_count(0,timeout=90000)
        check('CC-FILTER-EMPTY',links()==[] and 'Chưa có lượt xử lý phù hợp' in cc.inner_text())
        form=cc.locator('form:has(#cc_state)');form.locator('#cc_state').select_option('ALL');form.locator('#cc_order').select_option('asc');form.locator('input[type=submit]').click();page.wait_for_load_state('domcontentloaded')
        expect(cc.locator('table a')).to_have_text(list(reversed(initial)),timeout=90000)
        check('CC-SORT',links()==list(reversed(initial)))
        cc.get_by_role('link',name='Cập nhật Control Center',exact=True).click();page.wait_for_load_state('domcontentloaded')
        expect(cc.locator('table a')).to_have_text(initial,timeout=90000)
        check('CC-REFRESH',links()==initial)
        page.set_viewport_size({'width':390,'height':850});check('CC-RESPONSIVE-TEN-ROWS',page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'))
        page.set_viewport_size({'width':1280,'height':850});cc.screenshot(path=str(OUT/'qualified-control-center.png'))
        action=page.locator('form:has(select#engine)').get_attribute('action')
        response=ctx.request.post(BASE+action,form={'tool':'identity','arguments':'{}'},max_redirects=0)
        check('CC-CSRF-MISSING-TOKEN',response.status in (401,403,422),{'http':response.status})
        browser.close()
    result['passed']=True;output.write_text(json.dumps(result,indent=2));print(json.dumps({'passed':True,'checks':len(result['checks'])}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'passed':False,'error_type':type(error).__name__,'details_private':True}));raise SystemExit(1)

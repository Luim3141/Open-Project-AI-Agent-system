"""Five real authenticated browser pages concurrently, against the owned8-thread Core clone."""
import asyncio
import json
import time
import sys
from playwright.async_api import async_playwright
from tests.remaining_browser_uat import PRIVATE,OUT,BASE,ASSISTANT,otp


async def main():
    data=json.loads((PRIVATE/'fixture-credentials.json').read_text())
    final=json.loads((OUT/'final-image-uat.json').read_text()) if '--with-results' in sys.argv else None
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(channel='msedge',headless=True)
        contexts=[];pages=[]
        for account in data['users']:
            ctx=await browser.new_context();contexts.append(ctx);page=await ctx.new_page();pages.append((account,page))
            await page.goto(BASE+'/login',wait_until='domcontentloaded')
            await page.locator('#username').fill(account['login']);await page.locator('#password').fill(account['password'])
            await page.locator('form:has(#username) button[type=submit]').click();await page.locator('#otp').wait_for()
            if time.time()%30>26:await asyncio.sleep(4)
            await page.locator('#otp').fill(otp(account['totp_secret']))
            await page.locator('input[type=submit][name=login]').click();await page.wait_for_load_state('domcontentloaded')
        async def read(pair):
            account,page=pair;started=time.monotonic()
            try:
                run_id=next(r['id'] for r in final['runs'] if r['role']==account['role']) if final else None
                response=await page.goto(BASE+ASSISTANT+('?run_id='+run_id if run_id else ''),wait_until='domcontentloaded',timeout=120000)
                body=await page.inner_text('body')
                return {'role':account['role'],'http':response.status,'seconds':round(time.monotonic()-started,2),
                    'status':'PASS' if response.status==200 and await page.get_by_role('heading',name='AI Control Center',exact=True).count()==1
                        and 'AI gateway chưa sẵn sàng' not in body and 'AI gateway từ chối' not in body
                        and (not final or ('Phân tích local trên' in body and 'Execution plan' in body)) else 'FAIL'}
            except Exception as error:return {'role':account['role'],'status':'FAIL','error_type':type(error).__name__}
        results=await asyncio.gather(*(read(pair) for pair in pages))
        await browser.close()
    report={'scope':'FIVE_LOCAL_BROWSER_USERS_ONLY_NOT_20_USER_CAPACITY','core_max_threads':8,'checks':results,
        'passed':all(r['status']=='PASS' for r in results),'provider_calls':0}
    if final:report['image']=final['image'];report['results_checked']=True
    (OUT/('browser-five-concurrent-results.json' if final else 'browser-five-concurrent.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report));return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(asyncio.run(main()))

"""Inspect an existing synthetic clone execution through native login; never enqueue a run."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect
from browser_clone_uat import otp,BASE,ASSISTANT,OUT

def main():
    clone=json.loads((OUT/'clone.json').read_text())
    users=json.loads((Path(clone['private'])/'browser-accounts.json').read_text())['users']
    account=next(u for u in users if u['role']=='PM')
    identifier=json.loads((OUT/'clone-browser-results.json').read_text())['supervisor_run_id']
    result={'existing_run':identifier,'checks':[],'errors':[],'provider_calls':0}
    def check(name,passed,actual=None):
        result['checks'].append({'id':name,'passed':passed,'actual':actual})
        (OUT/'clone-monitor-results.json').write_text(json.dumps(result,indent=2))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        ctx=browser.new_context(viewport={'width':1366,'height':768});page=ctx.new_page();page.set_default_timeout(30000)
        page.on('pageerror',lambda e:result['errors'].append(str(e)[:400]))
        try:
            page.goto(BASE+'/login',wait_until='domcontentloaded')
            page.locator('#username').fill(account['login']);page.locator('#password').fill(account['password'])
            page.locator('form:has(#username) button[type=submit]').click();page.locator('#otp').wait_for()
            if time.time()%30>26:time.sleep(4)
            page.locator('#otp').fill(otp(account['totp_secret']));page.locator('input[type=submit][name=login]').click()
            page.wait_for_load_state('domcontentloaded')
            result['errors'].clear()
            response=page.goto(BASE+ASSISTANT+'/executions/'+identifier,wait_until='domcontentloaded')
            check('detail-http',response.status==200,response.status)
            page.locator('.em-node').first.wait_for(state='visible',timeout=45000)
            expect(page.locator('#em-state')).to_have_attribute('data-state','COMPLETED',timeout=45000)
            state=page.locator('#em-state').get_attribute('data-state')
            check('completed-visible','COMPLETED' in state,state)
            check('graph-has-nodes',page.locator('.em-node').count()>0,page.locator('.em-node').count())
            node=page.locator('.em-node').last;node.scroll_into_view_if_needed();before=node.get_attribute('transform');box=node.bounding_box()
            page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.down()
            page.mouse.move(box['x']+box['width']/2+50,box['y']+box['height']/2+20,steps=8);page.mouse.up()
            check('drag',node.get_attribute('transform')!=before)
            page.locator('#em-auto-layout').click();check('auto-layout',page.locator('.em-node').count()>0)
            page.locator('#em-presentation-toggle').click()
            check('presentation','em-presentation-mode' in page.locator('#execution-monitor').get_attribute('class'))
            page.keyboard.press('Escape')
            check('presentation-exit','em-presentation-mode' not in page.locator('#execution-monitor').get_attribute('class'))
            check('timeline',page.locator('#em-timeline li').count()>0,page.locator('#em-timeline li').count())
            check('final-output',page.locator('#em-final-output').text_content() not in ('','Chưa có kết quả.'))
            if page.locator('#em-play').is_enabled():
                page.locator('#em-play').click();page.wait_for_timeout(1200);page.locator('#em-present').click();check('replay',page.locator('.em-node').count()>0)
            for width,height in [(1920,1080),(1366,768),(768,1024),(375,812)]:
                page.set_viewport_size({'width':width,'height':height})
                page.screenshot(path=str(OUT/'clone-browser-screenshots'/f'monitor-{width}x{height}.png'))
                size=page.evaluate('({w:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
                check(f'responsive-{width}',size['scroll']<=size['w']+1,size)
        except Exception as error:
            check('monitor-exception',False,{'type':type(error).__name__,'message':str(error)[:800]})
        finally:
            if '/executions/' in page.url:
                page.screenshot(path=str(OUT/'clone-browser-screenshots/monitor-current.png'))
                (OUT/'clone-monitor-body.txt').write_text(page.locator('body').inner_text(),encoding='utf8')
            ctx.close();browser.close()
    result['passed']=all(c['passed'] for c in result['checks']) and not result['errors']
    (OUT/'clone-monitor-results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

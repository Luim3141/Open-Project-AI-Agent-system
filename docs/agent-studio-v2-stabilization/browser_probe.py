"""Real-click baseline and sanitized resource/performance timings; auth state is private."""
import importlib.util,json,os,time
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prior_uat',OUT.parent/'agent-studio-v2/main_uat.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
BASE=old.BASE;STUDIO=old.PATH
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai/studio-uat-state.json'
def authenticated(browser):
    ctx=browser.new_context(viewport={'width':1440,'height':1000},storage_state=str(PRIVATE) if PRIVATE.exists() else None)
    if ctx.request.get(BASE+'/api/v3/users/me').status!=200:
        page=ctx.new_page();old.login(ctx,page);page.close();ctx.storage_state(path=str(PRIVATE))
    me=ctx.request.get(BASE+'/api/v3/users/me');assert me.status==200 and me.json()['id']==18
    return ctx
def main():
    report={'scope':'MAIN UAT BASELINE','requests':[],'errors':[],'performance':{},'checks':{}}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True);ctx=authenticated(browser);page=ctx.new_page()
        page.add_init_script("""window.studioLongTasks=[];new PerformanceObserver(l=>window.studioLongTasks.push(...l.getEntries().map(e=>({start:e.startTime,duration:e.duration})))).observe({entryTypes:['longtask']});""")
        page.on('pageerror',lambda e:report['errors'].append({'message':str(e),'stack':e.stack[:500]}))
        def response(r):
            if '/qldapm-ai/' in r.url or r.status>=400:
                report['requests'].append({'path':urlparse(r.url).path,'status':r.status,'request_id':r.headers.get('x-request-id'),'timing':r.request.timing})
        page.on('response',response)
        try:
            started=time.perf_counter();page.goto(BASE+STUDIO,wait_until='domcontentloaded',timeout=60000);page.locator('.qas').wait_for();report['performance']['page_dom_ms']=(time.perf_counter()-started)*1000
            button=page.get_by_role('button',name='Mở Task explorer',exact=True)
            page.locator('.qas-browser').evaluate('(el)=>el.dataset.before="visible"')
            button.click();page.wait_for_timeout(200)
            report['checks']['explorer_click_moves_focus']=page.locator('input[aria-label="Tìm Task ID hoặc tiêu đề"]').evaluate('(el)=>el===document.activeElement')
            search=page.get_by_role('textbox',name='Tìm Task ID hoặc tiêu đề');search.fill('379');start=time.perf_counter();search.press('Enter')
            try:page.locator('.qas[data-task="379"]').wait_for(timeout=25000);report['checks']['task379_loaded_within_25s']=True
            except Exception:report['checks']['task379_loaded_within_25s']=False
            report['performance']['task379_visible_ms']=(time.perf_counter()-start)*1000
            report['performance']['long_tasks']=page.evaluate('window.studioLongTasks')
            report['performance']['resources']=page.evaluate('performance.getEntriesByType("resource").filter(e=>e.name.includes("observer.json")).map(e=>({path:new URL(e.name).pathname,total:e.duration,ttfb:e.responseStart-e.startTime,bytes:e.transferSize}))')
            report['performance']['dom_nodes']=page.locator('*').count()
            page.screenshot(path=str(OUT/'main-baseline.png'),full_page=True)
        finally:
            (OUT/'browser-baseline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ctx.close();browser.close()
    print(json.dumps(report,ensure_ascii=False));assert all(report['checks'].values()),'REAL_CLICK_OR_LOADING_REGRESSION'
if __name__=='__main__':main()

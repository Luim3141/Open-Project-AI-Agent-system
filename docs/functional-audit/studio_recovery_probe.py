"""Actual Explorer load/retry; no mocked response or execution control."""
import json,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT.parent/'agent-studio-v2-stabilization'))
from browser_probe import authenticated,BASE,STUDIO
report={'at':time.time(),'reads':[],'attempts':[]}
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True);ctx=authenticated(browser);p=ctx.new_page()
    p.on('response',lambda r:report['reads'].append({'path':r.url,'status':r.status,'retry_after':r.headers.get('retry-after')}) if '/observer.json' in r.url else None)
    p.goto(BASE+STUDIO+'?task_id=398',wait_until='domcontentloaded',timeout=90000)
    p.locator('.qas-browser').wait_for()
    for attempt in range(2):
        p.wait_for_function("()=>document.querySelectorAll('.qas-task-list button').length>0 || document.querySelector('.qas-browser .qas-read-state[data-phase=error]')",timeout=60000)
        count=p.locator('.qas-task-list button').count();report['attempts'].append({'items':count,'state':p.locator('.qas-browser .qas-read-state').inner_text()})
        if count:break
        p.wait_for_timeout(1500);p.locator('.qas-browser').get_by_role('button',name='Retry',exact=True).click()
    report['explorer_loaded']=p.locator('.qas-task-list button').count()>0
    p.screenshot(path=str(OUT/'main-studio-explorer.png'),full_page=True);ctx.close();browser.close()
(OUT/'studio-recovery-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False));assert report['explorer_loaded']

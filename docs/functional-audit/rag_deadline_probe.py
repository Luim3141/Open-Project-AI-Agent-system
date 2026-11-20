"""Read-only MAIN UI failure/retry trace; no HAR, cookies or request headers exported."""
import json,sys,time,uuid
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT.parent/'agent-studio-v2-stabilization'))
from browser_probe import authenticated,BASE,STUDIO
report={'scope':'REAL MAIN knowledge-search deadline/recovery, no ingestion','events':[],'attempts':[]}
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page()
    p.goto(BASE+STUDIO.removesuffix('/observer'),wait_until='domcontentloaded',timeout=90000);started=time.monotonic()
    p.on('request',lambda r:report['events'].append({'event':'request','at':time.monotonic()-started}) if '/commands' in r.url else None)
    p.on('requestfailed',lambda r:report['events'].append({'event':'failed','at':time.monotonic()-started,'failure':r.failure}) if '/commands' in r.url else None)
    p.on('response',lambda r:report['events'].append({'event':'response','at':time.monotonic()-started,'status':r.status}) if '/commands' in r.url else None)
    p.locator('[data-tab="tab-knowledge"]').click();search=p.get_by_role('searchbox',name='Câu hỏi tìm evidence trong Second Brain');search.fill('healthz')
    for attempt in range(2):
        start=time.monotonic();p.get_by_role('button',name='Tìm kiếm Tri thức',exact=True).click()
        p.wait_for_function('()=>/QUERY_COMPLETED|SEARCH_FAILED/.test(document.getElementById("qcc-knowledge-status").textContent)',timeout=65000)
        state=p.locator('#qcc-knowledge-status').inner_text();report['attempts'].append({'state':state,'seconds':time.monotonic()-start,'visible_items':p.locator('#qcc-knowledge-results .qcc-knowledge-item:visible').count()})
        if 'QUERY_COMPLETED' in state:break
        p.wait_for_timeout(1500)
    csrf=p.locator('meta[name="csrf-token"]').get_attribute('content');start=time.monotonic()
    response=c.request.post(BASE+STUDIO.removesuffix('/observer')+'/commands',form={'tool':'knowledge_search','knowledge_query':'healthz','request_id':str(uuid.uuid4())},headers={'Accept':'application/json','X-CSRF-Token':csrf},timeout=90000)
    data=response.json();report['direct_read']={'seconds':time.monotonic()-start,'status':response.status,'keys':list(data),'knowledge_html_chars':len(data.get('knowledge_html') or ''),'error':data.get('error'),'result_keys':list(data.get('result') or {})}
    p.screenshot(path=str(OUT/'rag-recovery-probe.png'),full_page=True);c.close();b.close()
(OUT/'rag-recovery-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False))

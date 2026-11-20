"""Actual MAIN UI interactions, read-only business operations, sanitized event trace."""
import json,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT.parent/'agent-studio-v2-stabilization'))
from browser_probe import authenticated,BASE,STUDIO
report={'scope':'REAL authenticated MAIN; no asset/response interception','checks':[],'network':[],'errors':[],'at':time.time()}
def save():(OUT/'browser-uat.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def check(name,fn):
    try:value=fn();report['checks'].append({'name':name,'status':'PASS','actual':value})
    except Exception as e:report['checks'].append({'name':name,'status':'FAIL','error':str(e)[:600]})
    finally:
        for selector in ['#qcc-report-modal:visible [aria-label="Đóng báo cáo"]','#qcc-run-modal:visible [data-action="close-modal"]']:
            close=p.locator(selector)
            if close.count():close.first.click()
    save()
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page()
    p.on('pageerror',lambda e:report['errors'].append(str(e)[:400]))
    p.on('response',lambda r:report['network'].append({'method':r.request.method,'path':r.url.split('?')[0],'status':r.status,'request_id':r.headers.get('x-qldapm-request-id') or r.headers.get('x-request-id')}) if '/qldapm-ai/' in r.url else None)
    p.goto(BASE+STUDIO.removesuffix('/observer'),wait_until='domcontentloaded',timeout=90000)
    p.locator('#qcc-agent-studio-link').wait_for(timeout=30000)
    for tab in ['mission','pipeline','workforce','backlog','execution','github','reports','knowledge','integrations']:
        def tab_check(tab=tab):
            p.locator(f'[data-tab="tab-{tab}"]').click();pane=p.locator('#tab-'+tab);assert pane.is_visible();text=pane.inner_text();assert len(text)>20
            if tab in ['mission','workforce','reports','integrations']:p.screenshot(path=str(OUT/f'main-{tab}.png'),full_page=True)
            return {'text_excerpt':text[:1100],'agent_roles':pane.locator('[data-agent-role]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.agentRole)')}
        check('tab_'+tab,tab_check)
    def workforce():
        p.locator('[data-tab="tab-workforce"]').click();roles=p.locator('#tab-workforce [data-agent-role]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.agentRole)');assert {'ba','pm','dev','reviewer','qa'}<=set(roles);return roles
    check('workforce_real_roles',workforce)
    def inspector():
        button=p.locator('#tab-workforce .qcc-run-inspector-btn').first;run=button.get_attribute('data-run-id');button.click();p.locator('#qcc-run-modal').wait_for();p.wait_for_function('()=>!document.querySelector("#qcc-run-modal-status-badge").textContent.includes("LOADING")',timeout=20000)
        status=p.locator('#qcc-run-modal-status-badge').inner_text();assert status!='ERROR';assert len(p.locator('#qcc-run-summary').inner_text())>50;assert p.locator('#qcc-run-metric-calls').inner_text()!='--'
        text=p.locator('#qcc-run-modal').inner_text();assert run[:8] in text;p.locator('#qcc-run-modal [data-action="close-modal"]').first.click();return {'run_id':run,'status':status,'text_excerpt':text[:900]}
    check('workforce_run_inspector',inspector)
    def reports():
        p.locator('[data-tab="tab-reports"]').click();attempts=[]
        for attempt in range(2):
            with p.expect_response(lambda r:'/qldapm-ai/reports/' in r.url,timeout=20000) as response:p.locator('.qcc-read-report-btn').first.click()
            r=response.value;attempts.append({'status':r.status,'retry_after':r.headers.get('retry-after'),'request_id':r.headers.get('x-qldapm-request-id') or r.headers.get('x-request-id')})
            if r.status==200:break
            assert r.status in [429,503,504];p.get_by_role('button',name='Đóng báo cáo',exact=True).click();p.wait_for_timeout(max(1,int(r.headers.get('retry-after','1')))*1000)
        assert r.status==200,attempts
        p.locator('#qcc-report-modal').wait_for();p.locator('#qcc-modal-report-body').wait_for();p.wait_for_timeout(800)
        text=p.locator('#qcc-modal-report-body').inner_text();assert len(text)>1000
        p.locator('#qcc-report-raw-toggle').click();raw=p.locator('#qcc-report-raw').inner_text();assert len(raw)>1000
        with p.expect_download() as download:p.locator('#qcc-report-export').click()
        path=Path(download.value.path());assert path.stat().st_size>1000
        p.screenshot(path=str(OUT/'main-report-reader.png'),full_page=True);p.get_by_role('button',name='Đóng báo cáo',exact=True).click();return {'attempts':attempts,'rendered_chars':len(text),'raw_chars':len(raw),'download_bytes':path.stat().st_size}
    check('reports_reader_raw_export',reports)
    def rag():
        p.locator('[data-tab="tab-knowledge"]').click();p.get_by_role('searchbox',name='Câu hỏi tìm evidence trong Second Brain',exact=True).fill('healthz')
        p.get_by_role('button',name='Tìm kiếm Tri thức',exact=True).click();p.locator('#qcc-knowledge-results .qcc-knowledge-item').first.wait_for(timeout=40000)
        text=p.locator('#qcc-knowledge-results').inner_text();assert 'Native version' in text and '398' in text and 'UNVERIFIED_RETRIEVAL' in text
        p.screenshot(path=str(OUT/'main-rag.png'),full_page=True);return {'citations':p.locator('#qcc-knowledge-results .qcc-knowledge-item a').evaluate_all('(nodes)=>nodes.map(n=>n.getAttribute("href"))'),'text_excerpt':text[:1400]}
    check('rag_actual_search_citations_and_quality_notice',rag)
    def studio():
        p.locator('#qcc-agent-studio-link').click();p.locator('.qas').wait_for();search=p.locator('#qas-task-search');search.fill('398');search.press('Enter');p.locator('.qas[data-task="398"]').wait_for(timeout=20000)
        assert p.locator('.react-flow__node').count()==3;p.locator('.react-flow__node[data-id="dev"]').hover();p.locator('.qas-floating-tooltip').wait_for();p.locator('.react-flow__node[data-id="dev"]').click();p.locator('.qas-inspector .qas-file').first.wait_for(timeout=20000)
        assert 'test_health_regression.py' in p.locator('.qas-inspector').inner_text();p.screenshot(path=str(OUT/'main-studio.png'),full_page=True)
        p.get_by_role('button',name='Đóng Agent inspector').click();p.get_by_role('tab',name='Artifacts',exact=True).click();p.locator('.qas-artifacts article').first.wait_for(timeout=20000)
        assert p.locator('a[href="https://github.com/Luim3141/mini-task-manager/pull/15"]').count()>0
        search.fill('393');search.press('Enter');p.locator('.qas[data-task="393"]').wait_for(timeout=20000);assert p.locator('.react-flow__node').count()==0
        p.go_back();p.locator('.qas[data-task="398"]').wait_for(timeout=20000);p.reload(wait_until='domcontentloaded');p.locator('.qas[data-task="398"]').wait_for(timeout=20000);return {'nodes':3,'unknown393':True,'back_reload398':True}
    check('command_center_to_studio_evidence_and_history',studio)
    report['finished_at']=time.time();save();c.close();b.close()
print(json.dumps({'checks':report['checks'],'errors':report['errors']},ensure_ascii=False))

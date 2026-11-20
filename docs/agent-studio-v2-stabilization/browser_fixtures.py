"""Headless UI regressions; responses here are explicitly TEST FIXTURE, not live E2E."""
import copy,json,time
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent
ASSETS=OUT.parents[1]/'openproject/ai/core/overlay/public/qldapm-agent-studio-v2'
def main():
    task=json.loads((OUT.parent/'agent-studio-v2/task-397.json').read_text(encoding='utf-8'))
    monitor=json.loads((OUT.parent/'agent-studio-v2/run-397.json').read_text(encoding='utf-8'))
    graph=copy.deepcopy(task);graph.update(view='graph',events=[],artifacts=[],flow_edges=[{'source':'dev','target':'reviewer','kind':'DEPENDENCY'},{'source':'reviewer','target':'qa','kind':'DEPENDENCY'}])
    graph['stages']=[{**s,'summary':'Recorded output · mở Inspector'} for s in graph['stages']]
    state={'failure':0,'requests':[],'delay':False};checks={};errors=[]
    projects=json.dumps([{'name':'TEST FIXTURE','identifier':'fixture','url':'/'}]).replace('"','&quot;')
    html=f'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{margin:0;background:#e9eef4;padding:16px}}</style><strong>TEST FIXTURE · no real execution</strong><link rel="stylesheet" href="/studio.css"><div id="qldapm-agent-studio" data-endpoint="/observer.json" data-command-center="/" data-project="fixture" data-projects="{projects}"></div><script defer src="/studio.js"></script>'''
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True);ctx=browser.new_context(viewport={'width':1440,'height':1100});page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.add_init_script('window.__studioMetrics={};history.replaceState({turbo:{restorationIdentifier:"fixture"}},"",location.href);window.addEventListener("popstate",e=>{if(!e.state?.turbo)document.getElementById("qldapm-agent-studio")?.remove();});')
        def route(r):
            path=urlparse(r.request.url).path;args={k:v[0] for k,v in parse_qs(urlparse(r.request.url).query).items()}
            if path.endswith('/qldapm-ai/observer'):return r.fulfill(content_type='text/html',body=html)
            if path in {'/studio.js','/studio.css'}:return r.fulfill(path=str(ASSETS/path[1:]),content_type='text/javascript' if path.endswith('js') else 'text/css')
            if path!='/observer.json':return r.fulfill(status=404,body='fixture')
            state['requests'].append(args)
            if state['failure']:return r.fulfill(status=state['failure'],json={'error':'FIXTURE_ERROR'},headers={'X-Qldapm-Request-Id':'fixture-request'})
            if args.get('view')=='list':return r.fulfill(json={'items':[{'task_id':397,'task_title':task['task_title'],'run_count':1,'workflow_status':'COMPLETED'}],'next_offset':None})
            tid=int(args.get('task_id',397));section=args.get('section')
            if args.get('view')=='graph':return r.fulfill(json={**graph,'task_id':tid})
            if section=='overview':return r.fulfill(json={**task,'task_id':tid})
            if section=='technical':return r.fulfill(json={'task_id':tid,'snapshot':{'fixture':True}})
            items=task[section]
            if section=='runs':items=[{**r,'nodes':monitor['nodes']} for r in items]
            return r.fulfill(json={'task_id':tid,'items':list(reversed(items))[:25],'next_offset':None,'total_available':len(items),'source_limits':{'runs':50,'events_per_run':200}})
        page.route('http://studio.fixture/**',route);page.goto('http://studio.fixture/projects/fixture/qldapm-ai/observer',wait_until='networkidle')
        page.get_by_role('button',name='Mở Task explorer',exact=True).click();assert page.locator('#qas-task-search').evaluate('(e)=>e===document.activeElement');checks['explorer_focus']=True
        search=page.locator('#qas-task-search');search.fill('397');search.press('Enter');page.locator('.qas[data-task="397"]').wait_for();page.locator('.react-flow__node').nth(2).wait_for()
        page.wait_for_function('document.querySelectorAll(".react-flow__edge").length===2')
        assert not any(a.get('run_id') for a in state['requests']);assert not any(a.get('section') in {'artifacts','runs','overview','technical'} for a in state['requests']);checks['graph_independent_lazy_details']=True
        page.locator('.react-flow__node[data-id="dev"]').click();page.locator('.qas-inspector .qas-file').first.wait_for();assert 'tests/test_health_regression.py' in page.locator('.qas-inspector').inner_text();assert page.locator('pre').count()==0;checks['typed_output_and_lazy_raw']=True
        page.get_by_role('button',name='Làm mới Observer').hover();page.wait_for_timeout(500);layouts=page.evaluate('__studioMetrics.layouts');renders=page.evaluate('__studioMetrics.nodeRenders');page.get_by_role('button',name='Làm mới Observer').click();page.wait_for_timeout(650);assert page.evaluate('__studioMetrics.layouts')==layouts;assert page.evaluate('__studioMetrics.nodeRenders')==renders,(renders,page.evaluate('__studioMetrics'));checks['status_refresh_no_layout_or_node_render']=True
        page.get_by_role('tab',name='Agent Runs',exact=True).click();page.get_by_role('link',name='Mở Run Details').first.wait_for();page.get_by_role('button',name='Mở attempts trên graph').click();page.locator('.react-flow__node').nth(3).wait_for();checks['paged_runs_expand']=True
        state['failure']=403;page.get_by_role('button',name='Làm mới Observer').click();page.locator('.qas[data-phase="error"]').wait_for();assert page.locator('.qas[data-task=""]').count()==1
        page.wait_for_timeout(500);n=len(state['requests']);page.wait_for_timeout(5500);assert len(state['requests'])==n;checks['403_stops_poll_and_clears_data']=True
        state['failure']=0;page.get_by_role('button',name='Làm mới Observer').click();page.locator('.qas[data-task="397"]').wait_for();checks['explicit_retry_recovers']=True
        for tid in [379,391,397]:search.fill(str(tid));search.press('Enter')
        page.locator('.qas[data-task="397"]').wait_for();page.go_back();page.locator('.qas[data-task="391"]').wait_for();page.go_forward();page.locator('.qas[data-task="397"]').wait_for();checks['rapid_switch_back_forward']=True
        for width in [1440,1280,768,390]:
            page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(300);assert page.locator('body').evaluate('(e)=>e.scrollWidth<=innerWidth'),width
        checks['responsive_no_overflow']=True
        page.screenshot(path=str(OUT/'fixture-mobile.png'),full_page=True)
        page.evaluate('document.dispatchEvent(new Event("turbo:before-cache"))');assert page.locator('.qas').count()==0;n=len(state['requests']);page.wait_for_timeout(3500);assert len(state['requests'])==n;checks['unmount_cancels']=True
        assert not errors,errors
        ctx.close();browser.close()
    report={'status':'PASS','scope':'TEST FIXTURE ONLY','checks':checks,'console_errors':errors,'requests':state['requests']};(OUT/'fixture-browser.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':checks}))
if __name__=='__main__':main()

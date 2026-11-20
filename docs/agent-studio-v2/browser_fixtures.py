"""Offline browser QA. All simulated runtime screenshots carry TEST FIXTURE banner."""
import copy,json,time
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parent
ASSETS=OUT.parents[1]/'openproject/ai/core/overlay/public/qldapm-agent-studio-v2'
def main():
    task=json.loads((OUT/'task-397.json').read_text(encoding='utf-8'))
    monitor=json.loads((OUT/'run-397.json').read_text(encoding='utf-8'))
    state={'task':copy.deepcopy(task),'monitor':copy.deepcopy(monitor),'failure':False,'requests':0}
    projects=json.dumps([{'name':'TEST FIXTURE Project','identifier':'fixture','url':'/'}]).replace('"','&quot;')
    html=f'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{margin:0;background:#e9eef4;padding:16px}}#fixture-label{{background:#8a3900;color:white;font:700 14px system-ui;padding:10px}}</style><div id="fixture-label">TEST FIXTURE · simulated states · no real execution</div><link rel="stylesheet" href="/studio.css"><div id="qldapm-agent-studio" data-endpoint="/observer.json" data-command-center="/" data-project="fixture" data-projects="{projects}"></div><script defer src="/studio.js"></script>'''
    report={'method':'OFFLINE_HEADLESS_EDGE_FIXTURES','checks':{},'business_writes':0,'model_calls':0}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='no-preference')
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            path=urlparse(r.request.url).path
            if path=='/':r.fulfill(content_type='text/html',body=html)
            elif path in {'/studio.js','/studio.css'}:r.fulfill(path=str(ASSETS/path.lstrip('/')),content_type='text/javascript' if path.endswith('js') else 'text/css')
            elif path=='/observer.json':
                state['requests']+=1
                args=parse_qs(urlparse(r.request.url).query)
                if state['failure']:r.fulfill(status=503,content_type='application/json',body='{}')
                else:r.fulfill(json=state['monitor'] if 'run_id' in args else state['task'] if 'task_id' in args else {'items':[state['task']],'truncated':True})
            else:r.fulfill(status=404,body='Not found')
        page.route('http://studio.fixture/**',route)
        page.goto('http://studio.fixture/?task_id=397',wait_until='networkidle')
        try:page.locator('.react-flow__node').nth(2).wait_for(timeout=15000)
        except Exception:
            page.screenshot(path=str(OUT/'fixture-failure.png'),full_page=True)
            print('INITIAL_RENDER_DIAGNOSTIC',errors,page.locator('.react-flow__node').evaluate_all('(els)=>els.map(e=>({style:e.getAttribute("style"),box:e.getBoundingClientRect().toJSON()}))'),flush=True)
            raise
        assert page.locator('.react-flow__node').count()==3
        assert page.locator('.react-flow__edge').count()==2
        assert page.locator('.react-flow__edge-path[marker-end]').count()==2
        assert not page.locator('.qas-flow-active').count()
        assert page.locator('pre:visible').count()==0
        report['checks']['actual_library_nodes_edges']=True
        page.locator('.qas-task').first.click();page.wait_for_timeout(500)
        assert page.locator('.qas[data-task="397"]').count()==1
        report['checks']['select_same_task_keeps_snapshot']=True
        page.locator('.react-flow__node').first.click();assert page.locator('.qas-inspector h3').inner_text()=='Developer'
        page.locator('.react-flow__node[data-id="qa"]').focus();page.keyboard.press('Enter');assert page.locator('.qas-inspector h3').inner_text()=='QA Engineer'
        page.locator('.react-flow__node').first.click()
        report['checks']['keyboard_opens_inspector']=True
        assert 'tests/test_health_regression.py' in page.locator('.qas-inspector').inner_text()
        page.locator('.react-flow__node').first.hover();page.locator('[role=tooltip]').wait_for()
        page.screenshot(path=str(OUT/'fixture-hover.png'),full_page=True)
        page.mouse.move(12,12)
        report['checks']['hover_click_work_summary']=True
        viewport=page.locator('.react-flow__viewport');before=viewport.get_attribute('style')
        page.locator('button[aria-label="Phóng to graph"]').click();page.wait_for_timeout(200)
        assert viewport.get_attribute('style')!=before
        page.locator('button[aria-label="Fit graph"]').click();page.wait_for_timeout(400)
        canvas=page.locator('.qas-canvas').bounding_box();page.mouse.move(canvas['x']+80,canvas['y']+45);page.mouse.down();page.mouse.move(canvas['x']+130,canvas['y']+75,steps=8);page.mouse.up()
        report['checks']['zoom_fit_pan']=True
        # Fresh verified active destination, followed by stale/reduced-motion/blocked/failed.
        s=state['task'];m=state['monitor'];s['revision']='fixture-running';s['workflow_status']='RUNNING';s['current_stage']='reviewer';s['current_agent']='reviewer';s['freshness']={'freshness_status':'FRESH','source_updated_at':time.time()};s['stages'][1]['status']='RUNNING';m['nodes'][2]['state']='RUNNING'
        page.get_by_role('button',name='Làm mới Observer').click()
        page.locator('.qas-agent.is-active').wait_for();assert page.locator('.qas-flow-active').count()==1
        page.wait_for_function('document.querySelector(".qas-flow-active") && getComputedStyle(document.querySelector(".qas-flow-active")).animationName==="qas-flow"')
        page.locator('button[aria-label="Fit graph"]').click();page.wait_for_timeout(350)
        page.screenshot(path=str(OUT/'fixture-running.png'),full_page=True)
        report['checks']['fresh_running_animation']=True
        active=page.locator('.qas-flow-active')
        active.hover(force=True);page.locator('.qas-edge-tooltip').wait_for();assert 'không chứng minh' in page.locator('.qas-edge-tooltip').inner_text()
        page.screenshot(path=str(OUT/'fixture-edge-hover.png'),full_page=True);page.mouse.move(12,12)
        page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(100)
        page.wait_for_function('document.querySelector(".qas-flow-active") && getComputedStyle(document.querySelector(".qas-flow-active")).animationName==="none"')
        report['checks']['reduced_motion']=True;page.emulate_media(reduced_motion='no-preference')
        stable=viewport.get_attribute('style');page.get_by_role('button',name='Làm mới Observer').click();page.wait_for_timeout(600);assert viewport.get_attribute('style')==stable
        report['checks']['refresh_preserves_viewport']=True
        state['failure']=True;page.get_by_role('button',name='Làm mới Observer').click();page.locator('.qas-connection').filter(has_text='HTTP 503').wait_for();assert not page.locator('.qas-flow-active').count();assert not page.locator('.qas-agent.is-active').count()
        report['checks']['disconnect_stops_activity']=True
        state['failure']=False;s['freshness']['source_updated_at']=time.time()-130;s['revision']='fixture-stale';page.get_by_role('button',name='Làm mới Observer').click();page.wait_for_timeout(600);assert not page.locator('.qas-flow-active').count();assert 'STALE' in page.locator('.qas-connection').inner_text()
        page.screenshot(path=str(OUT/'fixture-stale.png'),full_page=True)
        for status in ['BLOCKED','FAILED','UNKNOWN','COMPLETED']:
            s['revision']='fixture-'+status;s['workflow_status']=status;s['stages'][1]['status']=status;m['nodes'][2]['state']=status;s['current_stage']=None
            page.get_by_role('button',name='Làm mới Observer').click();page.wait_for_timeout(600)
            assert not page.locator('.qas-flow-active').count()
            page.locator('button[aria-label="Fit graph"]').click();page.wait_for_timeout(350)
            page.screenshot(path=str(OUT/f'fixture-{status.lower()}.png'),full_page=True)
        report['checks']['blocked_failed_unknown_completed']=True
        page.get_by_role('button',name='Đổi theme').click();page.screenshot(path=str(OUT/'fixture-light.png'),full_page=True)
        report['checks']['light_theme']=True
        page.get_by_role('tab',name='Agent Runs',exact=True).click();page.get_by_role('button',name='Mở attempts trên graph').click();page.wait_for_timeout(500);assert page.locator('.react-flow__node').count()==4
        report['checks']['stage_expand_real_attempt']=True
        page.get_by_role('button',name='Thu gọn attempts').click();page.wait_for_timeout(500)
        for width,height,name in [(1440,1100,'desktop'),(1280,1000,'laptop'),(768,1024,'tablet'),(390,844,'mobile')]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(250)
            page.locator('button[aria-label="Fit graph"]').click();page.wait_for_timeout(350)
            assert page.locator('body').evaluate('(el)=>el.scrollWidth<=innerWidth'),f'OVERFLOW_{width}'
            boxes=page.locator('.react-flow__node').evaluate_all('(els)=>els.map(el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}})')
            canvas=page.locator('.qas-canvas').bounding_box()
            assert all(b['x']>=canvas['x'] and b['right']<=canvas['x']+canvas['width']+1 and b['y']>=canvas['y'] and b['bottom']<=canvas['y']+canvas['height'] for b in boxes),f'CLIPPED_GRAPH_{width}'
            page.screenshot(path=str(OUT/f'fixture-{name}.png'),full_page=True)
        report['checks']['responsive_no_page_overflow']=True
        report['checks']['responsive_all_nodes_in_canvas']=True
        page.set_viewport_size({'width':1440,'height':1100})
        page.locator('#qldapm-agent-studio').evaluate('(el)=>el.style.width="680px"');page.wait_for_timeout(400)
        assert page.locator('.qas-workspace').evaluate('(el)=>getComputedStyle(el).display')=='flex'
        assert page.locator('.qas-canvas').evaluate('(el)=>el.clientHeight')==740
        page.locator('#qldapm-agent-studio').evaluate('(el)=>el.style.width=""');page.wait_for_timeout(300)
        report['checks']['container_width_drives_layout']=True
        # Simulate earlier failed run, keeping it visibly labelled as a fixture.
        previous=copy.deepcopy(m);previous['run_id']='fixture-previous-run';previous['nodes'][1]['state']='BLOCKED'
        previous_run=copy.deepcopy(s['runs'][0]);previous_run.update(run_id=previous['run_id'],state='BLOCKED',attempt=1)
        s['runs'][0]['attempt']=2;s['runs'].insert(0,previous_run);s['revision']='fixture-two-runs'
        original_route=route
        def two_runs(r):
            args=parse_qs(urlparse(r.request.url).query)
            if args.get('run_id')==[previous['run_id']]:r.fulfill(json=previous)
            else:original_route(r)
        page.unroute('http://studio.fixture/**',route);page.route('http://studio.fixture/**',two_runs)
        page.get_by_role('button',name='Làm mới Observer').click();page.wait_for_timeout(600)
        page.get_by_role('button',name='Mở attempts trên graph').click();page.wait_for_timeout(600)
        assert page.locator('.react-flow__node').count()==5
        assert 'Attempt 2' in page.locator('.qas-inspector').inner_text()
        page.screenshot(path=str(OUT/'fixture-multiple-attempts.png'),full_page=True)
        report['checks']['multiple_attempts_history_preserved']=True
        # Teardown must cancel timers and pending requests when Rails replaces the island.
        page.evaluate('document.dispatchEvent(new Event("turbo:before-cache"))')
        assert page.locator('.qas').count()==0
        requests=state['requests'];page.wait_for_timeout(3300);assert state['requests']==requests
        page.evaluate('document.dispatchEvent(new Event("turbo:load"))');page.locator('.qas').wait_for()
        report['checks']['turbo_unmount_cancels_polling']=True
        assert not errors,errors
        report.update(status='PASS',console_errors=errors,requests=state['requests'])
        context.close();browser.close()
    (OUT/'fixture-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()

"""Real Main read-only performance and browser clicks; never dump sessions/headers."""
import json,math,sys,time,statistics
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO
OUT=Path(__file__).resolve().parent
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'api';report={'scope':'REAL MAIN READ ONLY','checks':{},'requests':[],'at':time.time()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True);ctx=authenticated(browser)
        if mode=='api':
            scenarios={'list':'view=list&limit=20','397':'task_id=397&view=graph','379':'task_id=379&view=graph','391':'task_id=391&view=graph','398':'task_id=398&view=graph','393_no_telemetry':'task_id=393&view=graph'}
            count=int(sys.argv[2]) if len(sys.argv)>2 and sys.argv[2].isdigit() else 10
            assert 2<=count<=30
            for sample in range(count):
                for name,args in scenarios.items():
                    start=time.perf_counter();r=ctx.request.get(BASE+STUDIO+'.json?'+args,timeout=20000)
                    data=r.json();row={'scenario':name,'sample':sample,'temperature':'first' if sample==0 else 'warm','http_status':r.status,'total_ms':round((time.perf_counter()-start)*1000,3),'bytes':len(r.body()),'request_id':r.headers.get('x-qldapm-request-id'),'server_timing':r.headers.get('server-timing'),'error':data.get('error')};report['requests'].append(row);print(json.dumps(row),flush=True)
            for args,statuses in [('task_id=1&view=graph',[403,404]),('task_id=397&view=details&section=events&limit=51',[422])]:
                r=ctx.request.get(BASE+STUDIO+'.json?'+args);assert r.status in statuses
            report['checks']['acl_and_invalid_bounds']=True;report['statistics']={}
            for name in scenarios:
                values=sorted(r['total_ms'] for r in report['requests'] if r['scenario']==name and r['sample']>0)
                report['statistics'][name]={'n':len(values),'p50_ms':statistics.median(values),'sample_p95_ms':values[math.ceil(len(values)*.95)-1],'sample_p99_ms':values[-1],'max_ms':max(values),'errors':sum(r['http_status']!=200 for r in report['requests'] if r['scenario']==name)}
            report['checks']['all_http200']=all(r['http_status']==200 for r in report['requests'])
            save('main-api.json',report);assert report['checks']['all_http200'],report['statistics']
        elif mode=='browser':
            page=ctx.new_page();errors=[];report['errors']=errors
            if '--candidate' in sys.argv:
                report['scope']='CANDIDATE ASSET ON REAL MAIN HOST'
                page.route('**/qldapm-agent-studio-v2/studio.js?*',lambda r:r.fulfill(path=str(OUT.parents[1]/'openproject/ai/core/overlay/public/qldapm-agent-studio-v2/studio.js'),content_type='text/javascript'))
            page.add_init_script("window.__studioMetrics={};window.studioLongTasks=[];new PerformanceObserver(l=>window.studioLongTasks.push(...l.getEntries().map(e=>({start:e.startTime,duration:e.duration})))).observe({entryTypes:['longtask']});")
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:report['requests'].append({'url':r.url.split('?')[0],'query':r.url.split('?')[-1],'status':r.status,'request_id':r.headers.get('x-qldapm-request-id'),'timing':r.request.timing,'server_timing':r.headers.get('server-timing')}) if '/observer.json' in r.url else None)
            start=time.perf_counter();page.goto(BASE+STUDIO.removesuffix('/observer'),wait_until='domcontentloaded',timeout=90000);page.locator('#qcc-agent-studio-link').wait_for();page.screenshot(path=str(OUT/'main-command-center.png'),full_page=True);report['command_center_errors']=list(errors);errors.clear();page.locator('#qcc-agent-studio-link').click();page.locator('.qas').wait_for();report['checks']['command_center_real_entry']=True;report['page_dom_ms']=(time.perf_counter()-start)*1000
            page.get_by_role('button',name='Mở Task explorer',exact=True).click();page.wait_for_function('()=>document.getElementById("qas-task-search")===document.activeElement');report['checks']['explorer_real_click']=True
            search=page.locator('#qas-task-search');report['task_timings']=[]
            for tid in [379,391,397,398]:
                start=time.perf_counter();search.fill(str(tid));search.press('Enter')
                try:page.locator(f'.qas[data-task="{tid}"]').wait_for(timeout=15000)
                except Exception:
                    report['phase']=page.locator('.qas').get_attribute('data-phase');report['visible_message']=page.locator('.qas-read-state').all_inner_texts();report['url']=page.url;save('main-browser-failure.json',report);page.screenshot(path=str(OUT/'main-browser-failure.png'),full_page=True);raise
                report['task_timings'].append({'task':tid,'visible_ms':round((time.perf_counter()-start)*1000,2)})
            search.fill('393');search.press('Enter');page.locator('.qas[data-task="393"]').wait_for(timeout=15000);assert page.locator('.react-flow__node').count()==0;assert 'UNKNOWN' in page.locator('.qas-no-graph').inner_text();report['checks']['no_telemetry_truthful_unknown']=True
            search.fill('397');search.press('Enter');page.locator('.qas[data-task="397"]').wait_for(timeout=15000)
            start=time.perf_counter();page.locator('.react-flow__node[data-id="dev"]').hover();page.locator('.qas-floating-tooltip[role="tooltip"]').wait_for();report['hover_ms']=(time.perf_counter()-start)*1000
            start=time.perf_counter();page.locator('.react-flow__node[data-id="dev"]').click();page.locator('.qas-inspector .qas-file').first.wait_for(timeout=15000);report['inspector_ms']=(time.perf_counter()-start)*1000;assert 'test_health_regression.py' in page.locator('.qas-inspector').inner_text();report['checks']['typed_inspector']=True
            assert page.locator('pre').count()==0
            for tid in [379,391,397]:search.fill(str(tid));search.press('Enter')
            page.locator('.qas[data-task="397"]').wait_for();page.go_back();page.locator('.qas[data-task="391"]').wait_for();page.go_forward();page.locator('.qas[data-task="397"]').wait_for();report['checks']['switch_history_correct']=True
            with page.expect_popup() as popup:page.get_by_role('link',name='Native Task',exact=True).click()
            native=popup.value;native.wait_for_load_state('domcontentloaded');assert '397' in native.url and 'ai-dev-demo' in native.url;report['native_link_url']=native.url;native.close();report['checks']['native_real_click']=True
            page.get_by_role('tab',name='Run history',exact=True).click();link=page.get_by_role('link',name='Mở Run Details').first;link.wait_for(timeout=15000);link.click();page.locator('#execution-monitor').wait_for(timeout=20000);page.get_by_role('link',name='Quay lại Agent Studio — Task #397',exact=True).click();page.locator('.qas[data-task="397"]').wait_for(timeout=15000);report['checks']['run_details_return_real_click']=True
            page.reload(wait_until='domcontentloaded');page.locator('.qas[data-task="397"]').wait_for(timeout=15000);report['checks']['reload_context']=True
            page.get_by_role('combobox',name='Project',exact=True).select_option('qldapm-local');page.locator('#qldapm-agent-studio[data-project="qldapm-local"]').wait_for(timeout=20000)
            page.get_by_role('combobox',name='Project',exact=True).select_option('ai-dev-demo');page.locator('#qldapm-agent-studio[data-project="ai-dev-demo"]').wait_for(timeout=20000);report['checks']['project_navigation']=True
            search=page.locator('#qas-task-search');search.fill('398');search.press('Enter');page.locator('.qas[data-task="398"]').wait_for(timeout=15000)
            for width in [1440,1280,768,390]:
                page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(300);assert page.locator('#qldapm-agent-studio').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'),width
            report['checks']['responsive']=True;page.screenshot(path=str(OUT/'main-mobile.png'),full_page=True);page.set_viewport_size({'width':1440,'height':1000});page.wait_for_timeout(500);page.screenshot(path=str(OUT/'main-desktop.png'),full_page=True)
            report['metrics']=page.evaluate('({long_tasks:window.studioLongTasks,studio:window.__studioMetrics,dom_nodes:document.querySelectorAll("*").length,memory:performance.memory?.usedJSHeapSize})');save('candidate-browser.json' if '--candidate' in sys.argv else 'main-browser.json',report);assert not errors,errors
        else:raise ValueError(mode)
        ctx.close();browser.close()
    print(json.dumps({'scope':report['scope'],'checks':report['checks'],'statistics':report.get('statistics'),'task_timings':report.get('task_timings')}))
if __name__=='__main__':main()

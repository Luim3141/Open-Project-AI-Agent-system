"""Read-only real MAIN: bounded admission burst and emulated mobile touch input."""
import json,time
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO,OUT

report={'scope':'REAL MAIN; headless mobile/touch emulation, no OS gesture claim','checks':{}}
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True)
    auth=authenticated(b)
    p=auth.new_page();p.goto(BASE+STUDIO+'?task_id=398',wait_until='domcontentloaded')
    p.locator('.qas[data-task="398"]').wait_for(timeout=20000)
    p.wait_for_timeout(1500)
    report['burst']=p.evaluate('''async()=>Promise.all([379,391,397,398].map(async id=>{
      const start=performance.now();const r=await fetch(location.pathname+'.json?task_id='+id+'&view=graph');
      const data=await r.json();return {task:id,status:r.status,ms:performance.now()-start,
      retry_after:r.headers.get('Retry-After'),request_id:r.headers.get('X-Qldapm-Request-Id'),error:data.error};}))''')
    report['checks']['burst_bounded_no_unexpected503']=all(r['status'] in [200,429] for r in report['burst'])
    report['checks']['busy_retry_after_1']=all(r['retry_after']=='1' for r in report['burst'] if r['status']==429)
    mobile=b.new_context(storage_state=auth.storage_state(),viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
    m=mobile.new_page();m.goto(BASE+STUDIO+'?task_id=398',wait_until='domcontentloaded')
    m.locator('.qas[data-task="398"]').wait_for(timeout=20000)
    m.locator('.react-flow').scroll_into_view_if_needed()
    viewport=m.locator('.react-flow__viewport');before=viewport.get_attribute('style')
    m.get_by_role('button',name='Phóng to graph',exact=True).tap();m.wait_for_timeout(400)
    report['checks']['touch_zoom']=viewport.get_attribute('style')!=before
    pane=m.locator('.react-flow__pane');box=pane.bounding_box();before=viewport.get_attribute('style')
    session=mobile.new_cdp_session(m);x=box['x']+box['width']*.8;y=box['y']+box['height']*.8
    session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
    for delta in [15,30,45,60]:
        session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-delta,'y':y-20}]});m.wait_for_timeout(30)
    session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});m.wait_for_timeout(200)
    report['checks']['touch_pan']=viewport.get_attribute('style')!=before
    m.get_by_role('button',name='Fit graph',exact=True).tap();m.wait_for_timeout(400)
    m.locator('.react-flow__node[data-id="dev"]').tap()
    m.locator('.qas-inspector .qas-file').first.wait_for(timeout=15000)
    report['checks']['touch_inspector']=m.locator('.qas-inspector').is_visible()
    m.get_by_role('button',name='Đóng Agent inspector',exact=True).tap()
    m.get_by_role('button',name='Ẩn explorer',exact=True).tap()
    m.get_by_role('button',name='Mở explorer',exact=True).tap()
    report['checks']['touch_explorer']=m.locator('#qas-task-search').evaluate('(e)=>e===document.activeElement')
    report['checks']['no_island_overflow']=m.locator('#qldapm-agent-studio').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
    m.screenshot(path=str(OUT/'main-touch.png'),full_page=True)
    report['at']=time.time();mobile.close();auth.close();b.close()
(OUT/'final-interactions.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report));assert all(report['checks'].values())

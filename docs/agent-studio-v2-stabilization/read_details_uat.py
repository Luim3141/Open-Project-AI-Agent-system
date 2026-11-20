"""Read-only MAIN artifact-page and refresh timing; no response interception."""
import json,time
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO,OUT
report={'scope':'REAL MAIN, existing completed runtime #398','checks':{}}
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page()
    p.goto(BASE+STUDIO+'?task_id=398',wait_until='domcontentloaded')
    p.locator('.qas[data-task="398"]').wait_for(timeout=20000)
    start=time.perf_counter()
    with p.expect_response(lambda r:'/observer.json' in r.url and 'section=artifacts' in r.url and r.status==200,timeout=20000) as response:
        p.get_by_role('tab',name='Artifacts',exact=True).click()
    p.locator('.qas-bottom .qas-artifacts article').first.wait_for(timeout=15000)
    report['artifact_visible_ms']=(time.perf_counter()-start)*1000
    report['artifact_request_id']=response.value.headers.get('x-qldapm-request-id')
    report['checks']['actual_artifact_page']=len(response.value.json()['items'])>0
    report['checks']['typed_test_evidence']='test_health_regression.py' in p.locator('.qas-bottom').inner_text()
    start=time.perf_counter()
    with p.expect_response(lambda r:'/observer.json' in r.url and 'view=graph' in r.url and r.status==200,timeout=20000):
        p.get_by_role('button',name='Làm mới Observer',exact=True).click()
    report['refresh_graph_response_ms']=(time.perf_counter()-start)*1000
    report['checks']['refresh_same_task']=p.locator('.qas').get_attribute('data-task')=='398'
    report['at']=time.time();c.close();b.close()
(OUT/'read-details-uat.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert all(report['checks'].values())

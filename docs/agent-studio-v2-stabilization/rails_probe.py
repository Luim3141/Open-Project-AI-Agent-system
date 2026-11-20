"""One real authenticated default-list request, wait for upstream's own result."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO
OUT=Path(__file__).resolve().parent
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True);ctx=authenticated(browser)
    start=time.perf_counter()
    response=ctx.request.get(BASE+STUDIO+'.json?limit=20',timeout=115000)
    row={'route':STUDIO+'.json','http_status':response.status,'total_ms':round((time.perf_counter()-start)*1000,2),
         'request_id':response.headers.get('x-request-id'),'server_timing':response.headers.get('server-timing'),'bytes':len(response.body()),'at':time.time()}
    try:row['error_code']=response.json().get('error')
    except Exception:row['error_code']='NON_JSON'
    (OUT/'rails-baseline.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row))
    ctx.close();browser.close()
    assert row['http_status']==200 and row['total_ms']<2000,'REAL_RAILS_LIST_AVAILABILITY_OR_LATENCY_REGRESSION'

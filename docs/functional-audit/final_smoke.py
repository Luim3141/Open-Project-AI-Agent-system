"""Actual read-only MAIN input/auth and consumer-lock smoke. No model inference."""
import json,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/'agent-studio-v2-stabilization'))
from browser_probe import authenticated,BASE,STUDIO
report={'at':time.time(),'checks':{},'reads':[]}
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True);ctx=authenticated(browser)
    url=BASE+STUDIO.removesuffix('/observer')+'/executions.json'
    for offset in ['bad','-1','0']:
        response=ctx.request.get(url,params={'offset':offset},timeout=90000)
        body=response.json();report['reads'].append({'offset':offset,'status':response.status,'error':body.get('error'),'request_id':response.headers.get('x-request-id')})
        report['checks']['offset_'+offset]=response.status==(200 if offset=='0' else 422)
    empty=browser.new_context();r=empty.request.get(url,max_redirects=0,timeout=30000)
    report['reads'].append({'auth':'NO_SESSION','status':r.status,'location':r.headers.get('location')})
    report['checks']['anonymous_denied']=r.status in (302,401,403)
    empty.close();ctx.close();browser.close()
script="""import json,urllib.request
from app.config import Settings
from app.main import process_lock
s=Settings.from_env()
try:
 h=process_lock(s.db_path.parent/'polling.lock');h.close();locked=False
except RuntimeError as e:locked=str(e)=='ANOTHER_POLLING_CONSUMER_IS_RUNNING'
print(json.dumps({'duplicate_poller_denied':locked,'health':json.load(urllib.request.urlopen('http://127.0.0.1:8091/health'))}))"""
p=subprocess.run(['docker','exec','-i','qldapm-ai-telegram-ai-1','python','-'],input=script,text=True,capture_output=True,check=True)
report['telegram']=json.loads(p.stdout);report['checks']['one_poller_lock']=report['telegram']['duplicate_poller_denied']
image=json.loads(subprocess.check_output(['docker','image','inspect','qldapm-telegram-ai:local']))[0]['Id']
report['local_bot_tag']=image;report['checks']['local_tag_matches_serving']=image==json.loads((OUT/'bot-deployment.json').read_text())['image']
(OUT/'final-smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));assert all(report['checks'].values())

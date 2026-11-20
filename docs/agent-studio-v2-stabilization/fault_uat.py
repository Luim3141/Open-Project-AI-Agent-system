"""Bounded intentional maintenance + real browser offline/recovery, idle Main only."""
import json,os,hashlib,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO,OUT
from release import release
release.queue()
config=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway/config.json';before=config.read_bytes();value=json.loads(before);assert not value.get('maintenance')
report={'scope':'INTENTIONAL FAULT UAT, NOT HISTORICAL 503 RCA','checks':{},'requests':[]}
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page()
 p.goto(BASE+STUDIO+'?task_id=397',wait_until='domcontentloaded');p.locator('.qas[data-task="397"]').wait_for(timeout=15000)
 try:
  config.write_text(json.dumps({**value,'maintenance':True}),encoding='utf-8')
  response=c.request.get(BASE+STUDIO+'.json?task_id=397&view=graph',timeout=15000);d=response.json();report['requests'].append({'at':time.time(),'method':'GET','route':STUDIO+'.json','status':response.status,'error':d.get('error'),'request_id':response.headers.get('x-qldapm-request-id')});assert response.status==503 and d.get('error')=='MAINTENANCE'
  p.get_by_role('button',name='Làm mới Observer').click();p.locator('.qas[data-phase="error"]').wait_for(timeout=15000);assert not p.locator('.qas-agent.is-active').count();assert p.locator('.qas-read-state').filter(has_text='HTTP 503').count()>0;report['checks']['intentional_503_truthful_status_ui']=True
 finally:config.write_bytes(before)
 assert config.read_bytes()==before
 with p.expect_response(lambda r:'/observer.json' in r.url and 'view=graph' in r.url and r.status==200,timeout=15000):p.get_by_role('button',name='Làm mới Observer').click()
 p.locator('.qas[data-phase="loaded"]').wait_for(timeout=15000);report['checks']['maintenance_recovery_same_session']=True
 c.set_offline(True);p.get_by_role('button',name='Làm mới Observer').click();p.locator('.qas[data-phase="error"]').wait_for(timeout=15000);report['checks']['offline_finite_error']=True
 c.set_offline(False)
 with p.expect_response(lambda r:'/observer.json' in r.url and 'view=graph' in r.url and r.status==200,timeout=15000):p.get_by_role('button',name='Làm mới Observer').click()
 p.locator('.qas[data-phase="loaded"]').wait_for(timeout=15000);report['checks']['network_recovery']=True
 report['config_preserved']=hashlib.sha256(config.read_bytes()).hexdigest()==hashlib.sha256(before).hexdigest();p.screenshot(path=str(OUT/'main-recovered.png'),full_page=True);c.close();b.close()
(OUT/'fault-uat.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

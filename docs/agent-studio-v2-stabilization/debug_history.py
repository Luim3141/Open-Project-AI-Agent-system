import json,time,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO,OUT
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page();log=[];errors=[]
 if '--candidate' in sys.argv:p.route('**/qldapm-agent-studio-v2/studio.js?*',lambda r:r.fulfill(path=str(OUT.parents[1]/'openproject/ai/core/overlay/public/qldapm-agent-studio-v2/studio.js'),content_type='text/javascript'))
 p.on('pageerror',lambda e:errors.append(str(e)))
 p.on('response',lambda r:log.append({'url':r.url,'status':r.status}) if 'observer' in r.url else None)
 p.goto(BASE+STUDIO+'?task_id=397',wait_until='domcontentloaded');p.locator('.qas[data-task="397"]').wait_for()
 rows=[]
 for tid in [379,391,397]:
  s=p.locator('#qas-task-search');s.fill(str(tid));s.press('Enter');p.wait_for_timeout(150);rows.append({'step':str(tid),'url':p.url,'state':p.locator('.qas').get_attribute('data-task'),'phase':p.locator('.qas').get_attribute('data-phase')})
 p.locator('.qas[data-task="397"]').wait_for();p.go_back();
 for i in range(8):
  p.wait_for_timeout(1000);rows.append({'step':'back'+str(i),'url':p.url,'state':p.locator('.qas').get_attribute('data-task') if p.locator('.qas').count() else None,'phase':p.locator('.qas').get_attribute('data-phase') if p.locator('.qas').count() else None,'messages':p.locator('.qas-read-state').all_inner_texts()})
 result={'scope':'CANDIDATE ASSET ON REAL HOST' if '--candidate' in sys.argv else 'SERVING MAIN','rows':rows,'requests':log,'errors':errors};name='history-candidate' if '--candidate' in sys.argv else 'history-diagnostic';(OUT/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False));p.screenshot(path=str(OUT/(name+'.png')),full_page=True);c.close();b.close()

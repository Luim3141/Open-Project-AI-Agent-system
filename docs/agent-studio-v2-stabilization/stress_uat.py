"""Three real Main tabs and controlled headless visibility; no fake runtime."""
import json,time
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO,OUT
report={'scope':'REAL MAIN APIS, 3 TABS, HEADLESS DOCUMENT VISIBILITY EMULATION','checks':{},'requests':[],'responses':[],'errors':[],'started_at':time.time()}
def save():(OUT/'stress-uat.json').write_text(json.dumps(report,indent=2)+'\n')
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);pages=[]
 for tid in [398,391,397]:
  p=c.new_page();p.add_init_script('window.__studioMetrics={};window.visibilityStates=[];document.addEventListener("visibilitychange",()=>visibilityStates.push({at:Date.now(),state:document.visibilityState}));');p.on('pageerror',lambda e:report['errors'].append(str(e)))
  p.on('response',lambda r,tid=tid:report['responses'].append({'task':tid,'status':r.status,'at':time.time(),'retry_after':r.headers.get('retry-after')}) if '/observer.json' in r.url else None)
  p.on('request',lambda r,tid=tid:report['requests'].append({'task':tid,'at':time.time(),'path':r.url.split('?')[0]}) if '/observer.json' in r.url else None);p.goto(BASE+STUDIO+f'?task_id={tid}',wait_until='domcontentloaded');pages.append(p)
 for tid,p in zip([398,391,397],pages):
  try:p.locator(f'.qas[data-task="{tid}"]').wait_for(timeout=20000)
  except Exception:
   report['failed_task']=tid;report['phase']=p.locator('.qas').get_attribute('data-phase');report['visible_state']=p.locator('.qas-read-state').all_inner_texts()
   p.screenshot(path=str(OUT/'stress-failure.png'),full_page=True);(OUT/'stress-failure.json').write_text(json.dumps(report,indent=2)+'\n');raise
 report['checks']['three_tabs_load']=True
 p=pages[0];session=c.new_cdp_session(p);session.send('Performance.enable');session.send('HeapProfiler.collectGarbage');report['before_metrics']=session.send('Performance.getMetrics');before=sum(r['task']==398 for r in report['requests'])
 report['native_visibility_before']=p.evaluate('()=>document.visibilityState')
 p.evaluate('()=>{Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});Object.defineProperty(document,"visibilityState",{configurable:true,get:()=>"hidden"});document.dispatchEvent(new Event("visibilitychange"));}')
 p.wait_for_timeout(300);assert p.locator('.qas').get_attribute('data-phase')=='cancelled';start=time.monotonic()
 while time.monotonic()-start<301:pages[1].wait_for_timeout(1000)
 during=sum(r['task']==398 for r in report['requests']);report['pause_duration_seconds']=time.monotonic()-start;report['requests_during_pause']=during-before
 p.evaluate('()=>{delete document.hidden;delete document.visibilityState;document.dispatchEvent(new Event("visibilitychange"));}');p.wait_for_timeout(3000);report['visibility_states']=p.evaluate('()=>window.visibilityStates');report['studio_metrics']=p.evaluate('()=>window.__studioMetrics');session.send('HeapProfiler.collectGarbage');report['after_metrics']=session.send('Performance.getMetrics')
 report['checks']['no_reads_while_hidden_emulated']=during==before
 report['emulated_hidden_observed']=any(v['state']=='hidden' for v in report['visibility_states']);report['os_visibility_tested']=False;save()
 try:
  p.get_by_role('button',name='Làm mới Observer').click();p.locator('.qas[data-phase="loaded"],.qas[data-phase="partial"]').wait_for(timeout=15000);report['checks']['restore_reads_current_task']=p.locator('.qas').get_attribute('data-task')=='398'
 except Exception as error:
  report['checks']['restore_reads_current_task']=False;report['restore_error']=str(error);report['restore_phase']=p.locator('.qas').get_attribute('data-phase');report['restore_message']=p.locator('.qas-read-state').all_inner_texts()
 report['finished_at']=time.time();save()
 p.screenshot(path=str(OUT/'main-three-tabs-restored.png'),full_page=True);c.close();b.close()
save();print(json.dumps({k:report[k] for k in ['checks','pause_duration_seconds','requests_during_pause','emulated_hidden_observed','os_visibility_tested','errors']}));assert not report['errors'] and all(report['checks'].values())

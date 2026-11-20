"""Capture real browser graph responses/stages, no simulated state or writes."""
import json,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_probe import authenticated,BASE,STUDIO,OUT
task=int(sys.argv[1]);duration=int(sys.argv[2]) if len(sys.argv)>2 else 180
suffix=sys.argv[3] if len(sys.argv)>3 else ''
target=OUT/f'live-watch-{task}{suffix}.json'
report={'scope':'LIVE MAIN ACTUAL OBSERVER RESPONSES','task_id':task,'samples':[],'errors':[],'started_at':time.time()}
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=authenticated(b);p=c.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
 def response(r):
  if '/observer.json' not in r.url or 'view=graph' not in r.url:return
  try:
   d=r.json();row={'at':time.time(),'http_status':r.status,'request_id':r.headers.get('x-qldapm-request-id'),**{k:d.get(k) for k in ['task_id','project_id','latest_run_id','workflow_status','current_agent','current_stage','business_status','acceptance_status','revision','freshness','source_conflicts']},'stages':[{k:s.get(k) for k in ['stage_key','status','model_calls','latest_run_id','started_at','completed_at']} for s in d.get('stages',[])]};report['samples'].append(row)
  except Exception:report['errors'].append('RESPONSE_UNREADABLE')
 p.on('response',response);p.goto(BASE+STUDIO+f'?task_id={task}',wait_until='domcontentloaded',timeout=90000)
 deadline=time.monotonic()+duration;captured=set()
 while time.monotonic()<deadline:
  p.wait_for_timeout(1000)
  if report['samples']:
   sample=report['samples'][-1];role=sample.get('current_agent')
   if role and sample.get('workflow_status')=='RUNNING' and role not in captured:
    p.screenshot(path=str(OUT/f'live-{task}-{role}.png'),full_page=True);captured.add(role)
  target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 report['finished_at']=time.time();target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'task_id':task,'samples':len(report['samples']),'running_roles':sorted(captured),'errors':report['errors']}));c.close();b.close()

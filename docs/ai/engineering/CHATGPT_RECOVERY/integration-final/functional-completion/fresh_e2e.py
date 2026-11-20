"""One persisted final qualification intake/coding unit through the actual Rails AI bridge."""
import datetime,json,os,subprocess,sys,uuid
from pathlib import Path
OUT=Path(__file__).parent
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/functional-e2e-27fb7d12'

def run(args,data=None,timeout=90):
 p=subprocess.run(args,input=data,capture_output=True,timeout=timeout)
 assert p.returncode==0,'FRESH_E2E_COMMAND_FAILED'
 return p.stdout

def py(code):return json.loads(run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],code.encode(),30))

def bridge(action,args,key):
 body=json.dumps({'action':action,'arguments':args,'key':key})
 code="require 'json';d=JSON.parse(STDIN.read);p=Project.find(6);u=User.find(18);raise 'OWNER_REQUIRED' unless Qldapm::Rbac.ai_system_owner?(p,u,fresh:true);puts Qldapm::AiBridge.call(p,u,'command',{action:d['action'],arguments:d['arguments'],idempotency_key:d['key']}).to_json"
 return json.loads(run(['docker','exec','-i','qldapm-openproject-web-1','bundle','exec','rails','runner',code],body.encode(),180).decode().splitlines()[-1])

def main(action):
 if action=='prepare':
  assert not PRIVATE.exists(),'EXISTING_INTENT_RECONCILE_NEVER_CREATE_SECOND_TASK'
  state=py("import sqlite3,json;c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'active':c.execute(\"select count(*) from ai_queue where state!='finished'\").fetchone()[0],'mode':c.execute('select mode from engineering_control where project=6').fetchone()[0]}))")
  assert state=={'active':0,'mode':'OFF'}
  marker='FINAL-E2E-27FB-'+uuid.uuid4().hex[:8]
  feedback=(marker+' — Create exactly one small feature unit on the verified unmerged Demo integration base. '
   'Implement GET /tasks/count returning JSON {count: nonnegative integer}. Reuse the same optional q and status filters as GET /tasks; combined filters use AND and invalid status must have the same validation contract. '
   'Define the static /tasks/count route before any dynamic task-id route. Preserve current task CRUD, summary, detail, exists, title, CSV, Unicode and release identity behavior. '
   'Add meaningful tests for empty/count after create, q/status combined filters, Unicode/literal SQL characters, and ensure GET count never changes stored tasks. '
   'No schema migration, external service or extra feature; no PR merge or Demo deployment. Keep one coding unit, BA acceptance and PM dependencies explicit; reuse already delivered units without redoing their work.')
  PRIVATE.mkdir(parents=True);intent={'marker':marker,'planning_request_id':str(uuid.uuid4()),'coding_request_id':str(uuid.uuid4()),'feedback':feedback,'max_new_coding_units':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(PRIVATE/'intent.json').write_text(json.dumps(intent,indent=2)+'\n');print(json.dumps({'status':'INTENT_FROZEN','marker':marker}))
  return
 intent=json.loads((PRIVATE/'intent.json').read_text())
 if action=='intake':
  assert not (PRIVATE/'intake.json').exists(),'INTAKE_ALREADY_OBSERVED_RECONCILE'
  identity=py("import json;from pathlib import Path;from gateway.store import Store;from gateway.service import Service;from gateway.engineering import scoped_service;r=Path('/state');s=scoped_service(Service(Store(r),json.load(open(r/'config.json')),'/workspaces'),6);n,w=s.native_actor(18);i=n.package(379);print(json.dumps({'id':i['id'],'version':i['lockVersion']}))")
  response=bridge('engineering_plan',{'native_id':379,'lock_version':identity['version'],'feedback':intent['feedback']},intent['planning_request_id']);(PRIVATE/'intake.json').write_text(json.dumps(response,indent=2)+'\n')
  (OUT/'fresh-e2e-intake.json').write_text(json.dumps({'marker':intent['marker'],'route':'actual Rails Qldapm::AiBridge Owner18 → Gateway engineering_plan; no browser button claim','response':response},indent=2)+'\n');print(json.dumps(response))
 elif action=='status':
  intake=json.loads((PRIVATE/'intake.json').read_text());identifier=intake['result'].get('id') or intake['result'].get('run_id');coding_path=PRIVATE/'coding.json'
  if coding_path.exists():
   coding=json.loads(coding_path.read_text());identifier=coding['result'].get('id') or coding['result'].get('run_id')
  code="import sqlite3,json,time;c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row;r=c.execute('select q.id,q.state,q.payload,r.result from ai_queue q join ai_runs r on r.id=q.id where q.id=?',("+repr(identifier)+",)).fetchone();p=json.loads(r['payload']);result=json.loads(r['result'] or '{}');print(json.dumps({'id':r['id'],'queue_state':r['state'],'kind':p.get('kind'),'unit':p.get('unit'),'native_id':p.get('native_id'),'stage':p.get('stage'),'result_status':result.get('status'),'error':result.get('error'),'head_sha':result.get('head_sha'),'pr_url':result.get('pr_url'),'mode':c.execute('select mode from engineering_control where project=6').fetchone()[0],'calls':c.execute('select count(*) from gemini_call_receipts where run_id=?',(r['id'],)).fetchone()[0]}))"
  result=py(code);(OUT/'fresh-e2e-progress.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 elif action=='run':
  assert not (PRIVATE/'coding.json').exists(),'CODING_ALREADY_OBSERVED_RECONCILE'
  intake=json.loads((PRIVATE/'intake.json').read_text());identifier=intake['result'].get('id') or intake['result'].get('run_id')
  code="import json,sqlite3;from pathlib import Path;from gateway.store import Store;from gateway.service import Service;from gateway.engineering import scoped_service;r=Path('/state');s=scoped_service(Service(Store(r),json.load(open(r/'config.json')),'/workspaces'),6);n,w=s.native_actor(18);d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);p=json.loads(d.execute('select document from engineering_plans where id=?',("+repr(identifier)+",)).fetchone()[0]);assert p['state']=='PUBLISHED';units=[(k,v) for k,v in p['native_units'].items() if v['state']=='PLANNED'];assert len(units)==1;key,unit=units[0];i=n.package(unit['id']);print(json.dumps({'unit':key,'native_id':i['id'],'lock_version':i['lockVersion']}))"
  unit=py(code);response=bridge('engineering_run_once',unit,intent['coding_request_id']);(PRIVATE/'coding.json').write_text(json.dumps(response,indent=2)+'\n');(OUT/'fresh-e2e-coding.json').write_text(json.dumps({'unit':unit,'response':response},indent=2)+'\n');print(json.dumps(response))
 else:raise ValueError('KNOWN_STAGE_REQUIRED')

if __name__=='__main__':main(sys.argv[1])

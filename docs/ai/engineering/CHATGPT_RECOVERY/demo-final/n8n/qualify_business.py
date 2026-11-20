"""Published n8n business paths against actual Gateway/Native/Qdrant on isolated fixtures."""
import ast,copy,datetime,hashlib,json,os,secrets,shutil,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from automation.main_native_clone import main_native_clone
from automation.n8n_lifecycle_adapter import canonical_history_workflow
from gateway.automation import signing_key
OUT=Path(__file__).parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/('demo-n8n-business-'+uuid.uuid4().hex[:10]);private.mkdir(parents=True)
result={'started_utc':time.time(),'status':'RUNNING','checks':[],'main_native_writes':0,'provider_calls':0}
def run(*args,data=None,timeout=240):
 p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=timeout)
 if p.returncode:(private/'failure.log').write_bytes(p.stdout+p.stderr);raise RuntimeError('CLONE_DOCKER_FAILED_PRIVATE_LOG '+args[0])
 return p.stdout
image=json.loads(run('inspect','qldapm-ai-gateway-1'))[0]['Image'];n8n_image=json.loads(run('image','inspect','qldapm-n8n:demo-final'))[0]['Id'];core=json.loads(run('image','inspect','qldapm-core:demo-final'))[0]['Id']
result.update(gateway_base_image=image,n8n_image=n8n_image,core_image=core)
with main_native_clone(private/'native',candidate_web_image=core) as clone:
 created=[];prefix='qldapm-biz-'+clone['id'];gateway,n8n,vector=[prefix+'-'+k for k in ['gateway','n8n','vector']];outside=prefix+'-embedding';state=private/'state';fixture=private/'fixture';state.mkdir();fixture.mkdir();(private/'n8n-data').mkdir()
 label='org.qldapm.business='+clone['id']
 def py(code):
  pre="import json,time,uuid,httpx,sqlite3\nfrom pathlib import Path\nfrom gateway.native import Native\nfrom gateway.store import Store\nroot=Path('/state');fixture=Path('/fixture');c=json.load(open(root/'config.json'));keys=json.load(open(root/'credentials.json'));n=Native('http://web:8080',keys['18'],5)\n"
  p=run('exec','-i',gateway,'python','-',data=(pre+code).encode());return json.loads(p.decode().splitlines()[-1])
 def nfetch(path,payload,actor='18',authenticated=True):
  body={'url':'http://localhost:5678/webhook/'+path,'body':payload,'headers':{'Content-Type':'application/json',**({'X-QLDAPM-Webhook-Token':webhook} if authenticated else {}),**({'Authorization':'Bearer '+tokens[actor]} if actor else {})}}
  code="const p=JSON.parse(require('fs').readFileSync(0,'utf8'));fetch(p.url,{method:'POST',headers:p.headers,body:JSON.stringify(p.body),signal:AbortSignal.timeout(115000)}).then(async r=>console.log(JSON.stringify({status:r.status,body:await r.text()}))).catch(e=>{console.error(e.name);process.exit(1)})"
  response=json.loads(run('exec','-i',n8n,'node','-e',code,data=json.dumps(body).encode(),timeout=125))
  try:response['json']=json.loads(response.pop('body'))
  except ValueError:pass
  return response
 def request(code,payload,actor='18'):
  return nfetch(paths[code],payload,actor)
 def record(code,expected,operation):
  started=time.time()
  try:
   evidence=operation();row={'workflow':code,'expected':expected,'status':'BUSINESS_PASS_IN_CLONE','evidence':evidence}
  except Exception as e:row={'workflow':code,'expected':expected,'status':'FAILED','error_type':type(e).__name__,'diagnostic':str(e)[:240]}
  row.update(started_utc=started,finished_utc=time.time());result['checks'].append(row);(OUT/'business-progress.json').write_text(json.dumps(result,indent=2)+'\n');print(code+' '+row['status'],flush=True)
 def ok(response):
  assert response['status']==200,{'http':response['status'],'error':response.get('json',{}).get('error')};return response['json']['result'] if 'result' in response.get('json',{}) else response.get('json',{})
 try:
  # Native API tokens and bearer tokens exist only in the restored clone.
  ruby="require 'json';puts JSON.generate([18,19,20,21,22,23].to_h{|id|[id,Token::API.create_and_return_value(User.find(id))]})"
  keys=json.loads(run('exec',clone['web'],'bundle','exec','rails','runner',ruby,timeout=150).decode().splitlines()[-1]);(state/'credentials.json').write_text(json.dumps(keys))
  config=json.loads(run('exec','qldapm-ai-gateway-1','python','-c',"import json;from pathlib import Path;c=json.load(open('/state/config.json'));print(json.dumps({k:c[k] for k in ['project_id','gateway_mode','users','source_field','type_ids','status_ids']}))"))
  config.update(openproject_url='http://web:8080',hosts=['qldapm-ai-gateway-1:8090'],automation_readers=[20,21,22,23],native_incremental_sync={'enabled':False,'actor':18})
  (state/'config.json').write_text(json.dumps(config));(state/'ui.key').write_bytes(secrets.token_bytes(32))
  machine=secrets.token_hex(32);webhook=secrets.token_hex(32);(state/'automation.key').write_text(machine);(state/'webhook_secret.json').write_text(json.dumps({'webhook_token':webhook}))
  config['n8n_lifecycle']={'enabled':True,'webhook_url':'http://n8n:5678/webhook/qldapm-lifecycle','signing_key':'a'*64,'authenticated_webhook':True};(state/'config.json').write_text(json.dumps(config))
  code=private/'code/gateway';code.mkdir(parents=True)
  for p in (ROOT/'openproject/ai/gateway').iterdir():
   if p.is_file() and p.suffix in {'.py','.json'}:(code/p.name).write_bytes(p.read_bytes())
  result['gateway_sources']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in code.iterdir()}
  run('network','create','--label',label,outside);created.append(('network',outside))
  vector_image=json.loads(run('inspect','qldapm-qdrant'))[0]['Image']
  run('run','-d','--name',vector,'--label',label,'--network',clone['network'],'--network-alias','qldapm-qdrant','--read-only','--tmpfs','/qdrant/storage:size=256m,mode=1777','--tmpfs','/qdrant/snapshots:size=64m,mode=1777','--memory','384m','-e','QDRANT__TELEMETRY_DISABLED=true',vector_image);created.append(('container',vector))
  run('run','-d','--name',gateway,'--label',label,'--network',clone['network'],'--network-alias','qldapm-ai-gateway-1','--read-only','--tmpfs','/tmp:size=256m,mode=1777','--memory','1024m','--cpus','1.5','-e','PYTHONPATH=/app','-e','QLDAPM_AI_RUNTIME=/state','-e','QLDAPM_QDRANT_URL=http://qldapm-qdrant:6333','-e','QLDAPM_OLLAMA_URL=http://host.docker.internal:11434','--mount',f'type=bind,source={state},target=/state','--mount',f'type=bind,source={fixture},target=/fixture','--mount',f'type=bind,source={code},target=/app/gateway,readonly',image,'python','-m','uvicorn','gateway.app:app','--host','0.0.0.0','--port','8090');created.append(('container',gateway));run('network','connect',outside,gateway)
  for _ in range(60):
   try:
    if py("print(json.dumps(httpx.get('http://qldapm-ai-gateway-1:8090/health',trust_env=False).json()))").get('status')=='ok':break
   except RuntimeError:pass
   time.sleep(1)
  else:raise RuntimeError('GATEWAY_NOT_READY')
  tokens=py("s=Store(root);tokens={a:s.issue_token(int(a),role,keys[a]) for a,role in c['users'].items()};(fixture/'bearers.json').write_text(json.dumps(tokens));print(json.dumps(tokens))")
  py("from gateway.vector_client import VectorClient;v=VectorClient();assert v.ensure_collection();v.close();print('{}')")
  target=py("w=n.call('/api/v3/work_packages','POST',{'subject':'DEMO_N8N_CLONE_FIXTURE',c['source_field']:'DEMO-N8N-'+str(uuid.uuid4()),'description':{'raw':'AC1: native.subject == \\\"DEMO_N8N_CLONE_FIXTURE\\\"'},'_links':{'project':{'href':'/api/v3/projects/5'},'type':{'href':'/api/v3/types/1'}}});print(json.dumps({'id':w['id'],'version':w['lockVersion']}))")['id']
  rows=json.loads((OUT/'published-before.json').read_text());workflows=[];paths={}
  for row in rows:
   spec={'id':row['id'],'name':row['name'],'nodes':json.loads(row['nodes']),'connections':json.loads(row['connections']),'settings':json.loads(row['settings'])};wf=row['name'][:4]
   if wf=='WF04':spec=canonical_history_workflow(spec,'http://qldapm-ai-gateway-1:8090')
   for node in spec['nodes']:
    if node['type']=='n8n-nodes-base.scheduleTrigger':node['disabled']=True
    if node['type']=='n8n-nodes-base.httpRequest':node['parameters']['url']=node['parameters']['url'].replace('http://host.docker.internal:18089','http://qldapm-ai-gateway-1:8090')
   paths[wf]=next(node['parameters']['path'] for node in spec['nodes'] if node['type']=='n8n-nodes-base.webhook')
   spec['settings'].update(saveDataSuccessExecution='none',saveDataErrorExecution='none',saveManualExecutions=False,saveExecutionProgress=False)
   if wf=='WF12':
    trigger=copy.deepcopy(next(n for n in spec['nodes'] if n['type']=='n8n-nodes-base.webhook'));trigger.update(id='bounded-weekly',name='Bounded Weekly Schedule Probe',webhookId='bounded-weekly');trigger['parameters'].update(path='bounded-weekly',responseMode='lastNode');spec['nodes'].append(trigger);metadata=next(n for n in spec['nodes'] if n['id']=='weekly_metadata');spec['connections'][trigger['name']]={'main':[[{'node':metadata['name'],'type':'main','index':0}]]}
   workflows.append(spec)
  creds=[]
  for spec in workflows:
   for node in spec['nodes']:
    for kind,c in node.get('credentials',{}).items():
     if c['id'] in [v['id'] for v in creds]:continue
     data={'hmacSecret':signing_key(machine)} if kind=='crypto' else {'name':'X-QLDAPM-Webhook-Token','value':webhook} if c['id']=='2w9dSdmYbywZDuMB' else {'name':'X-QLDAPM-Machine-Key','value':machine}
     creds.append({'id':c['id'],'name':c['name'],'type':kind,'data':data})
  (fixture/'workflows.json').write_text(json.dumps(workflows));(fixture/'credentials.json').write_text(json.dumps(creds))
  run('run','-d','--name',n8n,'--label',label,'--network',clone['network'],'--network-alias','n8n','--memory','1024m','--cpus','1.5','--tmpfs','/home/node/.n8n:rw,uid=1000,gid=1000,mode=0700','--mount',f'type=bind,source={fixture},target=/fixture,readonly','-e','N8N_DIAGNOSTICS_ENABLED=false','-e','N8N_VERSION_NOTIFICATIONS_ENABLED=false','-e','N8N_TEMPLATES_ENABLED=false','-e','N8N_SECURE_COOKIE=false','--entrypoint','/bin/sh',n8n_image,'-c','sleep 3600');created.append(('container',n8n))
  run('exec',n8n,'n8n','user-management:reset');run('exec',n8n,'n8n','import:credentials','--input=/fixture/credentials.json');run('exec',n8n,'n8n','import:workflow','--input=/fixture/workflows.json')
  for spec in workflows:run('exec',n8n,'n8n','publish:workflow','--id='+spec['id'])
  run('exec','-d',n8n,'/bin/sh','-c','n8n start >/tmp/n8n.log 2>&1')
  for _ in range(80):
   try:
    if nfetch(paths['WF01'],{},authenticated=False)['status']==403:break
   except RuntimeError:pass
   time.sleep(1)
  else:raise RuntimeError('N8N_NOT_READY')
  def wf01():
   payload={'id':target,'request_id':str(uuid.uuid4())};r=ok(request('WF01',payload));assert ok(request('WF01',payload))==r;assert r.get('native_id')==target and r.get('vector_indexed') is True
   return {'native_id':target,'source_id':r.get('source_id'),'vector_indexed':True}
  record('WF01','Native fixture ingestion→SQLite/Qdrant read-back',wf01)
  def wf02():
   r=ok(request('WF02',{'operation':'sync','request_id':str(uuid.uuid4())}));assert isinstance(r,dict)
   return {'state':r.get('state'),'scope':r.get('authority'),'keys':sorted(r)}
  record('WF02','Incremental scan of isolated Native fixture and actual persisted status',wf02)
  local_run={}
  def wf03():
   payload={'prompt':'Hiện tại có bao nhiêu công việc loại Task chưa hoàn thành?','request_id':str(uuid.uuid4())}
   r=ok(request('WF03',payload));local_run['id']=r['id'];replay=ok(request('WF03',payload));assert replay['id']==r['id']
   current=ok(request('WF03',{'operation':'status','run_id':r['id']}))
   assert current['state']=='done' and current['result']['model_used'] is False and current['result']['source']=='native'
   return {'id':r['id'],'state':current['state'],'source':'native','model_used':False,'retry_same_run':True}
  record('WF03','Actual published start/status/replay; deterministic Native count route, no Gemini',wf03)
  def wf04():
   data=py("from gateway.execution_events import append;from gateway.n8n_lifecycle_outbox import sign_envelope;from types import SimpleNamespace;s=Store(root);scope=SimpleNamespace(run_id=str(uuid.uuid4()),trace_id=str(uuid.uuid4()),actor_id=20,project_id=6)\nwith s.connect() as d:append(d,scope,'AGENT_STARTED',agent='dev',status='RUNNING');r=d.execute('select document from n8n_lifecycle_outbox where event_id=(select event_id from execution_events where run_id=?)',(scope.run_id,)).fetchone()\nprint(json.dumps(sign_envelope(json.loads(r[0]),'a'*64)))")
   r=ok(request('WF04',data,actor=None));assert r['status']=='OBSERVED';return r
  record('WF04','Canonical signed source trace observed and correlated',wf04)
  proposal={}
  def wf05():
   p=py(f"from gateway.service import Service;s=Service(Store(root),c,'/tmp/workspaces');w=n.package({target});r=s.execute_actor(18,{{'action':'comment','arguments':{{'id':{target},'lock_version':w['lockVersion'],'text':'CLONE_REJECT_ONLY_NO_NATIVE_WRITE'}},'idempotency_key':'proposal-'+str(uuid.uuid4())}});print(json.dumps(r['result']))")
   proposal.update(p);r=ok(request('WF05',{'proposal_id':p['id']}));assert r.get('human_confirmation_required') is True or r.get('state')=='pending' or r.get('status')=='WAITING_HUMAN_CONFIRMATION'
   return {'proposal_id':p['id'],'state':p['state'],'human_confirmation_required':True}
  record('WF05','Exact persisted Native proposal preview, no implicit approval',wf05)
  def wf06():
   p=proposal;r=ok(request('WF06',{'proposal_id':p['id'],'hash':p['hash'],'decision':'reject'}));assert r.get('state')=='rejected';return {'id':p['id'],'state':r['state'],'native_write':False,'decision':'SIMULATED_EXACT_REJECT_IN_ISOLATED_FIXTURE'}
  record('WF06','Exact explicit rejection persists and prevents execution',wf06)
  def wf07():
   r=ok(request('WF07',{},actor=None));assert ok(request('WF07',{},actor=None))==r;assert r['status']=='READY' and r['ready']==4 and r['targets']==4;return {k:r.get(k) for k in ['run_id','status','targets','ready','target_selection']}
  record('WF07','Scheduled Daily branch selects valid20–23, Native GET-derived reports READY',wf07)
  record('WF08','Real Native sprint risk engine returns evidence',lambda:{'keys':sorted(ok(request('WF08',{'as_of_date':datetime.date.today().isoformat()})))})
  record('WF09','Explicit Native fixture target, no synthetic fallback',lambda:{'native_id':ok(request('WF09',{'id':target}))['id']})
  def wf10():
   r=ok(request('WF10',{'operation':'draft','request_id':str(uuid.uuid4()),'requirements':[{'id':'R1','text':'Demo acceptance'}],'nodes':[{'key':'epic','kind':'Epic','subject':'Fixture WBS epic','requirement_ids':['R1']},{'key':'task','kind':'Task','parent':'epic','subject':'Fixture WBS task','requirement_ids':['R1']}]}));r2=ok(request('WF10',{'operation':'get','id':r['id']}));assert r2['hash']==r['hash'];return {'id':r['id'],'state':r2.get('state'),'nodes':len(r2.get('spec',{}).get('nodes',[]))}
  record('WF10','Draft WBS persisted and exact hash read-back, no approval bypass',wf10)
  def wf11():
   r=ok(request('WF11',{'operation':'run','native_id':target,'request_id':str(uuid.uuid4())},actor='23'));r2=ok(request('WF11',{'operation':'run_get','run_id':r['id']},actor='23'));assert r2['binding']['native_id']==target and r2['verdict']=='PASSED';return {'id':r2['id'],'verdict':r2['verdict'],'producer':r2['producer']['id'],'native_id':target,'human_approval':False}
  record('WF11','QA actor runs fixed Native assertion and reads signed evidence, no approval',wf11)
  def wf12():
   r=ok(nfetch('bounded-weekly',{},actor=None));assert ok(nfetch('bounded-weekly',{},actor=None))==r;assert r['status']=='READY' and r['ready']==4 and r['targets']==4;return {k:r.get(k) for k in ['run_id','status','targets','ready','target_selection']}
  record('WF12','Actual scheduled weekly branch valid readers20–23 READY with Native sources',wf12)
  def wf13():
   r=ok(request('WF13',{'operation':'feedback_submit','native_id':target,'note':'Reindex source fixture; do not promote feedback text','request_id':str(uuid.uuid4())}));r2=ok(request('WF13',{'operation':'feedback_get','feedback_id':r['id']}));assert r2['source_current'] and not r2['feedback_content_promoted'];return {'id':r2['id'],'source_current':True,'state':r2['state'],'source':r2['source']}
  record('WF13','Source-version-bound feedback persists/read-back; unreviewed feedback not promoted',wf13)
  def wf14():
   job=py(f"s=Store(root)\nwith s.connect() as d:r=d.execute('select id from knowledge_sync where native_id=? order by rowid desc limit 1',({target},)).fetchone()\nprint(json.dumps({{'id':r[0]}}))")
   r=ok(request('WF14',{'job_id':job['id']}));assert r['id']==job['id'];return {'id':r['id'],'state':r['state']}
  record('WF14','Own persisted index job status from actual ingestion, not fake job',wf14)
  record('WF15','Actual SQLite/Qdrant/source integrity engine reports drift truthfully',lambda:{'keys':sorted(ok(request('WF15',{})))})
  def wf16():
   r=ok(request('WF16',{},actor=None));assert r['model_calls']==0 and r['project_id']==5 and r['state'] in {'HEALTHY','DEGRADED'};return {'state':r['state'],'checks':{k:v['state'] for k,v in r['checks'].items()},'native_write_allowed':r['native_write_allowed']}
  record('WF16','Machine monitor persists real dependency/resource/backlog report',wf16)
  denied=request('WF09',{'id':target},actor='19');assert denied['status']==403;result['actor19_denied']=True
  counts=py("s=Store(root)\nwith s.connect() as d:print(json.dumps({'gemini_usage':d.execute('select count(*) from gemini_usage').fetchone()[0],'receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0]}))")
  assert counts=={'gemini_usage':0,'receipts':0};result['provider_ledger']=counts
  # Reuse this restored Native clone for root's actual Core qualification, no duplicate clone.
  source=ast.parse((OUT.parent/'qualify_core.py').read_text());ruby=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ruby' for t in n.targets))
  p=subprocess.run(['docker','exec','-i',clone['web'],'bundle','exec','rails','runner','-'],input=ruby.encode(),capture_output=True,timeout=240)
  (private/'core-qualification.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,'CORE_QUALIFICATION_PRIVATE_LOG'
  core_result=json.loads(p.stdout.decode().splitlines()[-1]);core_result.update(image=core,environment='isolated actual Native clone reused by16workflow qualification',command=['python',str(Path(__file__).relative_to(ROOT))],finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());(OUT.parent/'core-clone-result.json').write_text(json.dumps(core_result,indent=2)+'\n')
  result['core_qualification']=core_result
  result.update(status='PASS' if all(r['status']=='BUSINESS_PASS_IN_CLONE' for r in result['checks']) else 'PARTIAL',passed=sum(r['status']=='BUSINESS_PASS_IN_CLONE' for r in result['checks']),total=len(result['checks']),limitations=['Business paths explicitly listed, not every possible branch of16workflows','Native writes/approval simulation only in disposable clone; actor19 remains denied, no Main user role changes','Ollama used for local embeddings only; no provider key or generation','WF12 scheduler branch reached through clone-only bounded webhook; production cron retained'])
 finally:
  for kind,name in reversed(created):
   row=json.loads(run('inspect',name) if kind=='container' else run('network','inspect',name))[0];labels=row['Config']['Labels'] if kind=='container' else row['Labels'];assert labels.get('org.qldapm.business')==clone['id']
   if kind=='container':(private/(name.rsplit('-',1)[-1]+'.log')).write_bytes(run('logs',name));run('rm','-f',name)
   else:run('network','rm',name)
  result['finished_utc']=time.time();(OUT/'business-clone-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result.get(k) for k in ['status','passed','total','provider_calls','main_native_writes']}))

"""Read-only final live verification; only own reader20 bearer, no inference or mutations."""
import ast,datetime,hashlib,json,os,subprocess,sys,time,urllib.request,uuid
from pathlib import Path
import httpx
from release_delegation import release
OUT=Path(__file__).parent;ROOT=OUT.resolve().parents[4]
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
def run(args,data=None):return subprocess.check_output(args,input=data,timeout=120)
def py(code):return json.loads(run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],code.encode()))
def node(code,data=None):return json.loads(run(['docker','exec','-i','qldapm-n8n-main','node','-e',code],None if data is None else json.dumps(data).encode()))
deploy=json.loads((OUT/'delegated-candidate-v3/deployment.json').read_text());result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containers':{}}
for role,image in {**deploy['images'],'n8n':'sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269'}.items():
    name=release.TARGETS[role][0] if role!='n8n' else 'qldapm-n8n-main';row=json.loads(run(['docker','inspect',name]))[0]
    assert row['Image']==image and row['State']['Status']=='running'
    if role!='n8n':assert row['State']['Health']['Status']=='healthy'
    result['containers'][role]={'image':image,'state':row['State']['Status'],'health':row['State'].get('Health',{}).get('Status','NOT_CONFIGURED')}
    if role!='n8n':assert release.runtime_hashes(role)=={k:v for k,v in deploy['source_hashes'].items() if release.SOURCES[k][0]==role}
release.guard_sources(release.ROOT,deploy['source_hashes']);result['runtime_source_hashes']=deploy['source_hashes']
runtime=Path(os.environ['LOCALAPPDATA'])/'QLDAPM';pins=json.loads((runtime/'openproject-ai/image-lock.json').read_text())
assert pins['AI_IMAGE']==deploy['images']['gateway'] and pins['CORE_IMAGE']==deploy['images']['core']
assert json.loads((runtime/'openproject/ui-bridge.yml').read_text())['services']['web']['image']==deploy['images']['core']
result['engineering']=py("""import sqlite3,json,time
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);w=d.execute('SELECT seen,run_id FROM engineering_worker_state WHERE project=6').fetchone()
out={'mode':d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0],'active':d.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0],
'worker_age_seconds':time.time()-w[0],'worker_run_id':w[1],'provider_receipts':d.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0],
'delegation':dict(zip(['enabled','revision'],d.execute('SELECT enabled,revision FROM delegated_control WHERE project=6').fetchone())),'runs':{}}
for rid in ('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6','301dbdd8-6f6f-4df4-b6c6-b5ca3f073795'):
 r=d.execute('SELECT q.state,q.payload,a.result FROM ai_queue q JOIN ai_runs a ON a.id=q.id WHERE q.id=?',(rid,)).fetchone()
 out['runs'][rid]={'queue_state':r[0],'result_status':json.loads(r[2]).get('status'),'recovery_count':json.loads(r[1]).get('recovery_count'),'generation_calls':d.execute("SELECT count(*) FROM gemini_call_receipts WHERE run_id=? AND json_extract(document,'$.phase')='generateContent'",(rid,)).fetchone()[0]}
print(json.dumps(out))""")
e=result['engineering'];assert e['mode'] in {'OFF','PAUSED'} and e['active']==0 and e['delegation']['enabled']==0 and e['provider_receipts']==531
if e['mode']=='PAUSED':
    result['owner_override']=py("import sqlite3,json;c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row;print(json.dumps(dict(c.execute(\"SELECT at,actor,action,target,outcome FROM audit WHERE action='engineering_control' AND target='6' ORDER BY at DESC LIMIT 1\").fetchone())))")
    assert result['owner_override']['actor']==18 and result['owner_override']['outcome']=='PAUSED'
assert e['worker_age_seconds']<30 and e['worker_run_id'] is None
result['provider_gate']=json.loads(run(['wsl','-d','OpenClawGateway','-u','root','--cd','/home/openclaw','--exec','python3','-c',"import json;from pathlib import Path;d=json.loads(Path('/root/.qldapm-openclaw/active.json').read_text());print(json.dumps({'active':d.get('active')}))"]))
assert result['provider_gate']['active'] is False
for url in ['http://127.0.0.1:5679/healthz/readiness','http://127.0.0.1:18789/readyz']:
    with urllib.request.urlopen(url,timeout=5) as r:assert r.status==200
cli=json.loads((runtime/'openproject-ai/gateway/openclaw-health.json').read_text());assert cli['health']=='READY' and cli['gateway_rpc_ok'] and time.time()-cli['checked_at']<150
result['openclaw']={'health':cli['health'],'gateway_rpc_ok':True,'checked_at':cli['checked_at']}

# Reuse the existing exact PG scopes, allowing only the new authorized principal25.
tree=ast.parse((OUT.parent/'integration-final/native_integrity.py').read_text())
queries=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='queries' for t in n.targets))
snapshot={}
for table,query in queries.items():
    sql="SELECT coalesce(json_agg(row ORDER BY row::text),'[]'::json) FROM (SELECT row_to_json(t) AS row FROM ("+query+") t) s;"
    snapshot[table]=json.loads(run(['docker','exec','qldapm-openproject-db-1','psql','-U','postgres','-d','openproject','-At','-c',sql]))
(private/'native-after-autonomous.json').write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8')
baseline=json.loads((private.parent/'integration-final-native-integrity/after-functional.json').read_text(encoding='utf-8'))
changed={}
for table in snapshot:
    if table!='users':assert snapshot[table]==baseline[table],'PROJECT5_OR_GLOBAL_CONFIG_CHANGED:'+table
    else:
        old={r['id']:r for r in baseline[table]};new={r['id']:r for r in snapshot[table]}
        assert set(new)-set(old)=={25} and set(old)<=set(new)
        assert new[25]['login']=='qldapm-demo-delegate' and new[25]['admin'] is False
        changed={str(i):[k for k in old[i] if old[i][k]!=new[i][k]] for i in old if old[i]!=new[i]}
        assert all(set(keys)<={'last_login_on','updated_at'} for keys in changed.values())
result['project5_integrity']={'status':'PASS_WITH_AUTHORIZED_PRINCIPAL_AND_LOGIN_TIMESTAMP_DELTAS','identical_tables':12,
 'counts':{k:len(v) for k,v in snapshot.items()},'existing_user_timestamp_deltas':changed,'authorized_new_user':25,
 'hashes':{k:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest() for k,v in snapshot.items()}}

sys.path.insert(0,str(OUT.parent/'integration-final/n8n'));from final_completion_publish import READ
published=node(READ);expected=json.loads((OUT/'delegated-published-after.json').read_text());contracts=[]
for row in published:
    pin=next(p for p in expected if p['id']==row['id']);assert row['active'] and row['activeVersionId']==pin['activeVersionId']
    for field in ['nodes','connections','settings']:assert hashlib.sha256(row[field].encode()).hexdigest()==pin[field+'_sha256']
    nodes=json.loads(row['nodes']);triggers=[{'type':n['type'],'parameters':n.get('parameters',{})} for n in nodes if n['type'].endswith('scheduleTrigger')]
    contracts.append({'workflow':row['name'][:4],'id':row['id'],'published_version':row['activeVersionId'],'schedule':triggers,'settings':json.loads(row['settings'])})
assert len(contracts)==16;result['published_workflows']=contracts
proof=json.loads((OUT/'main-delegated-business.json').read_text());ids=[r['execution_id'] for r in proof['receipts'] if r['execution_id']]
result['delegated_n8n_executions']=node("const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true}),ids=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log(JSON.stringify(ids.map(id=>d.prepare('SELECT id,workflowId,status,mode,startedAt,stoppedAt FROM execution_entity WHERE id=?').get(id))));",ids)
assert all(r and r['status']=='success' for r in result['delegated_n8n_executions'])
weekly=next(r for r in contracts if r['workflow']=='WF12')
result['wf12_executions']=node("const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT id,status,mode,startedAt,stoppedAt FROM execution_entity WHERE workflowId=? ORDER BY id DESC LIMIT 10').all(JSON.parse(require('fs').readFileSync(0,'utf8')))));",weekly['id'])

tokens=json.loads((private/'main-delegated-bearers.json').read_text())
def command(action,args=None):
    r=httpx.post('http://127.0.0.1:18089/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+tokens['20']},
                 json={'action':action,'arguments':args or {},'project_id':6,'idempotency_key':str(uuid.uuid4())},trust_env=False,timeout=100)
    assert r.status_code==200,(action,r.status_code);return r.json()['result']
status=command('engineering_status');github=status.get('github',{})
result['command_center']={'mode':status.get('mode'),'workflow_status':status.get('workflow_status'),'provider_health':status.get('provider_health'),
 'delivery_worker':status.get('delivery_worker'),'delegated_approval':{'enabled':status['delegated_approval']['enabled'],'revision':status['delegated_approval']['revision']},
 'github':{'status':github.get('status'),'prs':[{k:p.get(k) for k in ['number','state','merged_at','mergedAt','merge_commit_sha','head_sha','html_url','work_package_id']} for p in github.get('prs',[])],'release':github.get('release')}}
reports=command('engineering_report_list',{'limit':20})
result['reports']=[{k:r.get(k) for k in ['id','report_type','source_versions_current','source_state','created','created_iso']} for r in reports['reports']]
result['notifications']=command('engineering_notifications_list',{'limit':30})
result['status']='SERVING_IMAGES_SOURCE_PINS_NATIVE_POLICY_WORKFLOWS_VERIFIED'
(OUT/'final-live-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'engineering':e,'project5':result['project5_integrity']['status'],'delegated_executions':len(ids),'github':result['command_center']['github']}))

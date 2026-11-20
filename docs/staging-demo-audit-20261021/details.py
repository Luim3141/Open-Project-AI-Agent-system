"""Supplementary read-only runtime metadata; no raw credentials or business contents exported."""
import hashlib
import json
from pathlib import Path
from read_only_audit import command, OUT, RUNTIME


def sql(query):
    statement = "BEGIN READ ONLY; SELECT coalesce(json_agg(x),'[]'::json) FROM ("+query+") x; ROLLBACK;"
    return json.loads(command(['docker','exec','-i','qldapm-ai-stage-db-1','psql','-v','ON_ERROR_STOP=1','-U','postgres','-d','openproject','-Atq'],statement).strip())


result = {}
result['schema'] = sql("SELECT table_name,column_name FROM information_schema.columns WHERE table_name IN ('grids','grid_widgets','sprints','two_factor_authentication_devices','queries') ORDER BY table_name,ordinal_position")
result['totp'] = sql('SELECT id,user_id,type,active,"default" FROM two_factor_authentication_devices ORDER BY user_id,id')
result['login_state'] = sql("SELECT id,login,failed_login_count,last_failed_login_on,last_login_on FROM users WHERE type='User' ORDER BY id")
result['boards'] = sql("SELECT id,type,name,options,project_id FROM grids ORDER BY id")
result['sprints'] = sql('SELECT id,project_id,name,start_date,finish_date FROM sprints ORDER BY project_id,id')
result['queries'] = sql('SELECT id,project_id,name FROM queries WHERE project_id=3 ORDER BY id')
result['settings'] = sql("SELECT name,value FROM settings WHERE name IN ('per_page_options','authentication','two_factor_authentication') ORDER BY name")

program = '''import json,sqlite3,pathlib,collections,hashlib,uuid,time
root=pathlib.Path('/state'); db=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True); db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON')
out={}; config=json.loads((root/'config.json').read_text()); out['config']={k:config[k] for k in ['project_id','gateway_mode','gemini_multi_agent_enabled','multi_agent','hosts'] if k in config}
g=json.loads((root/'gemini.json').read_text());out['gemini']={k:g[k] for k in ['enabled','model','multi_agent','authorization','data_scope'] if k in g}
for name in ['gemini-readiness.json']:
 p=root/name
 if p.exists():
  d=json.loads(p.read_text());out[name]={k:d[k] for k in ['passed','checked_at','model'] if k in d}
out['blocks']=[dict(r) for r in db.execute('SELECT reason FROM gemini_blocks')]
out['recovery']=[dict(r) for r in db.execute('SELECT reason,retry_at FROM gemini_recovery')]
out['receipts']=[]
for r in db.execute('SELECT id,actor,run_id,document FROM gemini_call_receipts ORDER BY rowid DESC LIMIT 15'):
 d=json.loads(r['document']); safe={k:d[k] for k in ['state','status','agent','model','model_used','input_tokens','output_tokens','usage','usage_metadata','created_at','provider','http_attempts','error','code'] if k in d};out['receipts'].append(dict(id=r['id'],actor=r['actor'],run_id=r['run_id'],details=safe,keys=list(d)))
out['runs']=[]
for r in db.execute('SELECT id,actor,project,document FROM agent_runs ORDER BY rowid DESC LIMIT 25'):
 d=json.loads(r['document']); safe={k:d[k] for k in ['state','engine','model_used','created_at','finished_at','trace_id','error','error_code','run_class'] if k in d};out['runs'].append(dict(id=r['id'],actor=r['actor'],project=r['project'],details=safe,keys=list(d)))
out['ai_results']=[]
for r in db.execute('SELECT id,actor,state,result FROM ai_runs ORDER BY rowid DESC LIMIT 5'):
 d=json.loads(r['result'] or '{}'); safe={k:d[k] for k in ['engine','model_used','provenance','state','source','error','error_code','plan','execution_plan'] if k in d}; out['ai_results'].append(dict(id=r['id'],actor=r['actor'],state=r['state'],details=safe,keys=list(d)))
out['daily_briefs']=[]
for r in db.execute('SELECT actor,project,day,document FROM daily_briefs ORDER BY day DESC LIMIT 5'):
 d=json.loads(r['document']);out['daily_briefs'].append(dict(actor=r['actor'],project=r['project'],day=r['day'],keys=list(d),state=d.get('state')))
k=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);k.row_factory=sqlite3.Row;k.execute('PRAGMA query_only=ON');out['knowledge']=[dict(r) for r in k.execute('SELECT project_id,source_id,title,allowed_roles,metadata FROM knowledge_documents')]
out['fts_read_query_count']=k.execute("SELECT count(*) FROM knowledge_fts WHERE knowledge_fts MATCH 'AUTH'").fetchone()[0]
from gateway.planner import plan_request
from gateway.agent_models import AgentTask
task=AgentTask(task_id=str(uuid.uuid4()),actor_id=7,project_id=3,conversation_id=str(uuid.uuid4()),agent='supervisor',instruction='BA và QA: chỉ đọc; không ghi thay đổi. Phân tích yêu cầu và các ca kiểm thử cho công việc 49.',created_at=time.time(),expires_at=time.time()+60)
p=plan_request(task,'PM');out['pure_planner_probe']={'agents':[s.agent for s in p.steps],'write_approval':p.requires_pm_approval}
from gateway.agent_registry import get_agent_registry
out['registry']=list(get_agent_registry().list_agents())
out['runtime_modules']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app/gateway').glob('*.py')}
print(json.dumps(out,ensure_ascii=False))'''
result['gateway'] = json.loads(command(['docker','exec','-i','qldapm-ai-stage-staging-gateway-1','python','-'],program))
program = """const {DatabaseSync}=require('node:sqlite');const db=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});let o={};o.tables=db.prepare(\"SELECT name FROM sqlite_master WHERE type='table'\").all().map(x=>x.name);o.workflows=db.prepare('SELECT id,name,active FROM workflow_entity').all();o.executions=db.prepare('SELECT id,workflowId,status,mode,startedAt,stoppedAt FROM execution_entity ORDER BY id DESC LIMIT 12').all();console.log(JSON.stringify(o));db.close();"""
try:
    result['n8n'] = json.loads(command(['docker','exec','qldapm-ai-stage-n8n-1','node','-e',program]))
except RuntimeError as e:
    result['n8n_error'] = str(e)
result['private_hashes'] = {}
for directory, names in [('stage-ai',['gemini.key','gemini.json','config.json','credentials.json','ui.key','automation.key']),('stage',['accounts.json','deep-test-receipt.key']),('n8n-stage',['encryption.key']),('access',['current-url.json'])]:
    for name in names:
        path = RUNTIME/directory/name
        if path.is_file():
            result['private_hashes'][directory+'/'+name] = hashlib.sha256(path.read_bytes()).hexdigest()
target = OUT/'details.json'
assert not target.exists(), 'Refuse evidence overwrite'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'evidence':str(target),'boards':result['boards'],'sprints':result['sprints'],'totp':result['totp'],'registry':result['gateway']['registry'],'planner':result['gateway']['pure_planner_probe'],'n8n':result.get('n8n',result.get('n8n_error'))},ensure_ascii=False))

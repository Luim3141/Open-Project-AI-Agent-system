"""Semantic assertions against captured real read results; fresh global tool reads, no inference."""
import json,subprocess,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
report=json.loads((OUT/'main-integrations.json').read_text(encoding='utf-8'))
tools={r['tool']:r.get('result') for r in report['tools']};checks={}
task=tools['get_task_progress'];checks['task398_exact_id_run']=task['task_id']==398 and task['latest_run_id']=='de391b2f-e5f2-4bc3-be10-54ab11d73099'
checks['398_business_vs_runtime']=task['workflow_status']=='COMPLETED' and task['business_status']=='READY FOR RELEASE' and task['acceptance_status']=='AWAITING_OWNER_APPROVAL'
checks['398_native_version']=tools['get_task_details']['id']==398 and tools['get_task_details']['lockVersion']==10
stages={s['agent_role']:s for s in task['stages']};checks['recorded_stages_complete']=set(stages)=={'dev','reviewer','qa'} and all(s['status']=='COMPLETED' for s in stages.values())
dev=json.loads(stages['dev']['summary']);review=json.loads(stages['reviewer']['summary']);qa=json.loads(stages['qa']['summary'])
checks['dev_files_revision']=dev['files']==['tests/test_health_regression.py'] and dev['head_sha']=='7ceac4e6b2b9103b18e1a8be37e15f3c05b8de70'
checks['reviewer_evidence']=review['verdict']=='PASS' and review['findings']==[]
checks['qa_evidence']=qa['qa']['status']=='PASS' and qa['qa']['exit_code']==0 and qa['qa']['failures']==[]
checks['checkpoint_and_resume']=len(task['checkpoint']['completed_steps'])==11 and task['checkpoint']['version']==27 and task['resume']['eligible'] is False
checks['no_current_agent']=tools['get_current_agent']['current_agent'] is None
checks['run_exact_binding']=tools['get_run_details']['run_id']==task['latest_run_id'] and tools['get_run_details']['project_id']==6
checks['unauthorized_and_project_isolation']=all(report['checks'].values())
script='''import asyncio,json,tempfile,sqlite3
from pathlib import Path
from app.config import Settings
from app.gateway import GatewayClient
from app.storage import Repository
from app.tools import ToolExecutor,context_result
async def main():
 s=Settings.from_env();g=GatewayClient(s);out=[]
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'auth.sqlite'
  with sqlite3.connect(s.db_path.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(p) as b:a.backup(b)
  executor=ToolExecutor(g,Repository(p),s)
  for name in ['get_active_agents','get_blocked_tasks','get_pending_approvals']:
   value=await executor.execute(name,{},1916909968,1916909968,6)
   out.append({'tool':name,'correlation_id':g.last_correlation_id,'project_id':value.get('project_id'),'items':[{k:i.get(k) for k in ['task_id','task_title','workflow_status','current_agent','business_status','acceptance_status','freshness']} for i in value.get('items',[])],'truncated':value.get('truncated'),'scope_notice':value.get('scope_notice'),'context_truncated':context_result(value).get('truncated',False),'raw_json_bytes':len(json.dumps(value))})
 await g.close();return out
print(json.dumps(asyncio.run(main()),ensure_ascii=False))'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-telegram-ai-1','python','-'],input=script,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);assert p.returncode==0,p.stderr[-300:]
global_reads=json.loads(p.stdout)
checks['global_running_current_scope']=global_reads[0]['project_id']==6 and not global_reads[0]['items']
checks['pending_owner_scoped']=any(i['task_id']==398 for i in global_reads[2]['items']) and all(i['acceptance_status']=='AWAITING_OWNER_APPROVAL' for i in global_reads[2]['items']) and not any(i['task_id']==397 for i in global_reads[2]['items'])
result={'at':time.time(),'scope':'Semantic assertions real Gateway/Native snapshots + fresh global reads, no model calls/business writes','checks':checks,'global_reads':global_reads}
(OUT/'semantic-read-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False));assert all(checks.values())

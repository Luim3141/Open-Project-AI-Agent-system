"""Read native identity/data via existing credentials, and retain failed Main run metadata."""
import json
from read_only_audit import command, OUT

program = '''import json,pathlib,sqlite3
from gateway.native import Native
root=pathlib.Path('/state');config=json.loads((root/'config.json').read_text());creds=json.loads((root/'credentials.json').read_text());actor=int(next(k for k,v in config['users'].items() if v=='PM'))
n=Native(config['openproject_url'],creds[str(actor)],config['project_id']);out={'identity':n.identity(actor)}
packages=n.packages();out['work_packages_count']=len(packages);out['sprints']=n.sprints();out['package_38']=next(({k:p[k] for k in ['id','lockVersion','subject','startDate','dueDate'] if k in p} for p in packages if p['id']==38),None)
db=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');out['runs']=[]
for r in db.execute('SELECT r.id,r.actor,r.state,r.result,t.document FROM ai_runs r LEFT JOIN agent_tasks t ON t.id=(SELECT task_id FROM agent_runs a WHERE a.id=r.id) ORDER BY r.rowid DESC LIMIT 5'):
 result=json.loads(r['result'] or '{}');task=json.loads(r['document'] or '{}');plan=result.get('plan') or {};receipts=[json.loads(x[0]) for x in db.execute('SELECT document FROM gemini_call_receipts WHERE run_id=?',(r['id'],))]
 safe_receipts=[{k:x[k] for k in ['agent','phase','state','error','http_status','usage','at'] if k in x} for x in receipts]
 out['runs'].append({'id':r['id'],'actor':r['actor'],'state':r['state'],'task_agent':task.get('agent'),'requested_ba_qa':'BA' in task.get('instruction','') and 'QA' in task.get('instruction',''),'error':result.get('error'),'execution_mode':result.get('execution_mode'),'model_used':result.get('model_used'),'plan_agents':[s.get('agent') for s in plan.get('steps',[])],'provider_receipts':safe_receipts})
out['source_modules']={}
import gateway.planner,inspect
from gateway.planner import resolve_target_agents
out['planner_module']=gateway.planner.__file__;out['planner_probe']=resolve_target_agents('BA và QA: chỉ đọc; không ghi thay đổi. Phân tích yêu cầu và các ca kiểm thử cho công việc 49.','supervisor') if hasattr(gateway.planner,'resolve_target_agents') else 'old_no_multi_resolver'
print(json.dumps(out,ensure_ascii=False))'''
out={}
for label,container in [('staging','qldapm-ai-stage-staging-gateway-1'),('main','qldapm-ai-gateway-1')]:
    # Old Staging has no multi-agent selector helper; omit the optional probe for that image.
    body=program if label=='main' else program[:program.index("out['source_modules']")]+'print(json.dumps(out,ensure_ascii=False))'
    try:out[label]=json.loads(command(['docker','exec','-i',container,'python','-'],body))
    except Exception as e:out[label]={'error':str(e)}
target=OUT/'native-and-main.json'
assert not target.exists()
target.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({label:dict(identity=d.get('identity'),count=d.get('work_packages_count'),error=d.get('error'),planner=d.get('planner_probe'),runs=[{k:r[k] for k in ['id','state','requested_ba_qa','error','plan_agents']} for r in d.get('runs',[])]) for label,d in out.items()},ensure_ascii=False))

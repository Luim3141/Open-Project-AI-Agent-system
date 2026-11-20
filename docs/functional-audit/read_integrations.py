"""Run inside Telegram container: real read tools, copied auth/memory, no business writes/inference."""
import asyncio,hashlib,json,sqlite3,tempfile,time
from pathlib import Path
from app.config import Settings
from app.gateway import GatewayClient
from app.storage import Repository
from app.tools import ToolExecutor,sanitize

async def main():
    settings=Settings.from_env();gateway=GatewayClient(settings);report={'at':time.time(),'scope':'REAL Telegram tool adapter → Gateway → Native/Observer; auth copied from existing pairing; test memory/audit only in temporary DB','tools':[],'commands':[]}
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'copied.sqlite'
        with sqlite3.connect(settings.db_path.as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(path) as target:source.backup(target)
        repo=Repository(path);tools=ToolExecutor(gateway,repo,settings);pair=repo.authorize(1916909968,1916909968);assert pair and 6 in pair['project_ids']
        cases=[('list_projects',{}),('search_tasks',{'query':'healthz'}),('get_task_details',{'task_id':398}),('get_task_progress',{'task_id':398}),('get_task_agent_runs',{'task_id':398}),('get_current_agent',{'task_id':398}),('get_task_artifacts',{'task_id':398}),('get_github_prs',{'task_id':398}),('get_review_results',{'task_id':398}),('get_qa_results',{'task_id':398}),('get_worker_status',{}),('get_queue_status',{}),('get_system_health',{}),('get_n8n_status',{}),('get_run_details',{'run_id':'de391b2f-e5f2-4bc3-be10-54ab11d73099'}),('get_run_errors',{'run_id':'de391b2f-e5f2-4bc3-be10-54ab11d73099'}),('get_checkpoint_status',{'run_id':'de391b2f-e5f2-4bc3-be10-54ab11d73099'}),('search_knowledge',{'query':'healthz'})]
        for name,args in cases:
            started=time.monotonic();row={'tool':name,'args':args}
            try:
                value=await tools.execute(name,args,1916909968,1916909968,6);row.update(status='READ_RETURNED',correlation_id=gateway.last_correlation_id,result=value)
            except Exception as e:row.update(status='FAIL',error_type=type(e).__name__,error=str(e)[:200])
            row['seconds']=round(time.monotonic()-started,3);report['tools'].append(row)
        cases=[('identity',{}),('get_project_options',{}),('get_permissions',{}),('engineering_status',{}),('get_control_center',{}),('engineering_report_list',{}),('engineering_report_schedule_get',{}),('engineering_notifications_list',{}),('knowledge_incremental_status',{}),('knowledge_sync_status',{}),('observer_task_progress',{'task_id':397}),('observer_task_progress',{'task_id':379})]
        for action,args in cases:
            try:
                value=await gateway.command(action,args,6);report['commands'].append({'action':action,'status':'READ_RETURNED','correlation_id':gateway.last_correlation_id,'result':sanitize(value)})
            except Exception as e:report['commands'].append({'action':action,'status':'FAIL','error_type':type(e).__name__,'error':str(e)[:200]})
        for project in [5,6]:
            try:await tools.execute('get_task_progress',{'task_id':398},999999,999999,project);report.setdefault('unauthorized',[]).append(False)
            except PermissionError:report.setdefault('unauthorized',[]).append(True)
        try:await gateway.command('observer_task_progress',{'task_id':398},5);report['cross_project_denied']=False
        except Exception as e:report['cross_project_denied']='403' in str(e) or '404' in str(e)
        await gateway.close()
        report['checks']={'unauthorized_denied':all(report['unauthorized']),'cross_project_denied':report['cross_project_denied']}
        return report
if __name__=='__main__':print(json.dumps(asyncio.run(main()),ensure_ascii=False))

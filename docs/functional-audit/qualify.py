"""Offline contract suites; temporary fixture stores, no MAIN credentials or network."""
import json,subprocess,time,os
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
base=json.loads((OUT/'baseline.json').read_text())['containers']
def run(name,cmd,expected=0):
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
    (OUT/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    return {'exit_code':p.returncode,'expected_exit':expected,'passed':p.returncode==expected,'tail':(p.stdout+p.stderr)[-600:]}
common=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:size=128m,mode=1777','-e','PYTHONDONTWRITEBYTECODE=1']
tests=f'type=bind,source={ROOT / "openproject/ai/telegram-ai/tests"},target=/qa,readonly'
bot=common+['--mount',tests,'--entrypoint','python']
results={'at':time.time(),'scope':'OFFLINE CONTRACTS; fixtures and real module code; not MAIN E2E'}
results['acceptance_red']=run('acceptance-red',bot+[base['qldapm-ai-telegram-ai-1']['image'],'-m','unittest','discover','-s','/qa','-p','test_acceptance_answer.py'],1)
host=common+['--mount',tests,'--mount',f'type=bind,source={ROOT / "openproject/ai/telegram-ai/app"},target=/app/app,readonly','--entrypoint','python',base['qldapm-ai-telegram-ai-1']['image']]
results['telegram_green']=run('telegram-contracts',host+['-m','unittest','discover','-s','/qa'])
modules=['test_gateway','test_agent_observer','test_telegram_notifications','test_observer_read_path','test_control_center','test_control_center_authorization','test_command_center_state_contract','test_supervisor','test_agent_queue','test_checkpoint','test_engineering_owner_controls','test_engineering_continuation','test_engineering_fencing','test_engineering_delivery_recovery','test_engineering_monitor_current','test_engineering_catalog_limit','test_engineering_reporting_contract','test_engineering_github_owner_contract','test_engineering_github_recovery','test_engineering_github_sync','test_business_acceptance','test_human_approval_lifecycle','test_native_qa_workflow','test_native_qa_evidence','test_takeover_security','test_automation_auth','test_n8n_lifecycle_adapter','test_n8n_lifecycle_outbox','test_notification_delivery','test_knowledge_storage','test_knowledge_integrity','test_knowledge_search','test_rag_recovery','test_knowledge_file_workflow','test_knowledge_feedback_apply']
modules=[m for m in modules if (ROOT/'openproject/ai/tests'/f'{m}.py').exists() and m not in {'test_control_center','test_control_center_authorization'}]
host_modules=['test_command_center_state_contract','test_checkpoint','test_owner_knowledge_ui_contract']
modules=[m for m in modules if m not in host_modules]+['test_cc_summary_reads']
extra=json.loads((OUT/'mutation-contracts.json').read_text())['modules']
modules=list(dict.fromkeys(modules+[m for m in extra if m!='test_proposal_aggregation']))
gw=common+['-e','QLDAPM_AI_RUNTIME=','-e','PYTHONPATH=/app:/app/tests:/repo:/repo/openproject/ai','--mount',f'type=bind,source={ROOT / "openproject/ai/tests"},target=/app/tests,readonly','--mount',f'type=bind,source={ROOT / "openproject/ai/core"},target=/app/core,readonly','--mount',f'type=bind,source={ROOT / "openproject"},target=/repo/openproject,readonly','--mount',f'type=bind,source={ROOT / "docs"},target=/repo/docs,readonly','--entrypoint','python',base['qldapm-ai-gateway-1']['image']]
results['gateway_modules']=modules
results['gateway']=run('gateway-contracts',gw+['-m','unittest',*['tests.'+m for m in modules]])
host_env={**os.environ,'PYTHONPATH':str(ROOT/'openproject/ai')+os.pathsep+str(ROOT)}
host=subprocess.run([str(ROOT/'openproject/ai/.venv/Scripts/python.exe'),'-m','unittest',*['tests.'+m for m in host_modules]],env=host_env,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
(OUT/'host-contracts.log').write_text(host.stdout+host.stderr,encoding='utf-8');results['host_contracts']={'exit_code':host.returncode,'tail':(host.stdout+host.stderr)[-800:]}
node=subprocess.run([str(ROOT/'openproject/ai/.venv/Scripts/python.exe'),'-m','unittest','tests.test_native_qa_workflow','tests.test_n8n_lifecycle_adapter','tests.test_n8n_publish_guards'],env=host_env,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
(OUT/'node-workflow-contracts.log').write_text(node.stdout+node.stderr,encoding='utf-8');results['node_contracts']={'exit_code':node.returncode,'tail':(node.stdout+node.stderr)[-500:]}
(OUT/'qualification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(results,ensure_ascii=False));assert all(results[k]['passed'] for k in ['acceptance_red','telegram_green','gateway']) and host.returncode==0 and node.returncode==0

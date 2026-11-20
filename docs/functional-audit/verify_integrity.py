"""Read-only data/source/restart verification. Only fingerprints/selected state leave stores."""
import hashlib,json,os,sqlite3,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'docs/agent-studio-v2-stabilization'))
from preservation import capture
before=json.loads((OUT/'baseline.json').read_text());after=capture();checks={}
checks['native_existing_projects_roles_workflows_passwords']=before['native']==after['native']
checks['settings_and_secret_files']=before['ecosystem']['files']==after['ecosystem']['files']
checks['all17_n8n_workflow_and_credentials']=before['ecosystem']['n8n']==after['ecosystem']['n8n']
checks['gateway_original_row_prefixes']=all(v['original_rows_sha256']==before['gateway']['tables'][k]['original_rows_sha256'] for k,v in after['gateway']['tables'].items())
checks['gateway_config_files']=before['gateway']['files']==after['gateway']['files']
checks['OFF_idle']=after['gateway']['mode']=='OFF' and after['gateway']['active']==0
stable_tg=['pairs','pair_codes','confirmations','notification_context','telegram_notification_outbox']
checks['pairing_confirmations_outbox_context_preserved']=all(before['ecosystem']['telegram_tables'][t]==after['ecosystem']['telegram_tables'][t] for t in stable_tg)
private_backup=Path(json.loads((OUT/'core-candidate/deployment.json').read_text())['private_backup'])/'gateway.sqlite'
tables=['agent_runs','agent_tasks','ai_queue','ai_runs','engineering_checkpoints','engineering_plans','engineering_unit_definitions','engineering_control','engineering_owner_commands','tokens']
def fingerprint(rows):return hashlib.sha256(json.dumps(rows,separators=(',',':'),default=lambda b:b.hex()).encode()).hexdigest()
with sqlite3.connect(private_backup.as_uri()+'?mode=ro',uri=True) as db:
    old={t:{'rows':db.execute('SELECT count(*) FROM '+t).fetchone()[0],'sha256':fingerprint(db.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall())} for t in tables}
program="""import json,hashlib,sqlite3,sys
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);tables=json.load(sys.stdin)
print(json.dumps({t:{'rows':d.execute('SELECT count(*) FROM '+t).fetchone()[0],'sha256':hashlib.sha256(json.dumps(d.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall(),separators=(',',':'),default=lambda b:b.hex()).encode()).hexdigest()} for t in tables}))"""
result=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-c',program],input=json.dumps(tables),text=True,capture_output=True,check=True);current=json.loads(result.stdout)
checks['all_agent_tasks_runs_checkpoints_plans_units_no_replay']=old==current
app_paths={k:v for k,v in before['sources'].items() if k.startswith('openproject/ai/core/overlay/')}
expected={k.removeprefix('openproject/ai/core/overlay/'):hashlib.sha256((ROOT/k).read_bytes()).hexdigest() for k in app_paths}
program="require 'json';require 'digest';p=JSON.parse(STDIN.read);puts JSON.generate(p.to_h{|k|f='/app/'+k;[k,File.file?(f) ? Digest::SHA256.file(f).hexdigest : nil]})"
p=subprocess.run(['docker','exec','-i','qldapm-openproject-web-1','ruby','-e',program],input=json.dumps(list(expected)),text=True,capture_output=True,check=True)
checks['full_core82_file_parity']=expected==json.loads(p.stdout)
other={k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest() for k in before['sources'] if not k.startswith('openproject/ai/core/overlay/')}
changed=[k for k,v in before['sources'].items() if hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=v]
checks['only_4_product_sources_changed']=set(changed)=={'openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb',*['openproject/ai/telegram-ai/app/'+n for n in ['engine.py','tools.py','system_instructions.py']]}
runtime_absent={}
for role,prefix,name in [('gateway','openproject/ai/gateway/','qldapm-ai-gateway-1'),('telegram','openproject/ai/telegram-ai/app/','qldapm-ai-telegram-ai-1')]:
    expected={k[len(prefix):]:v for k,v in other.items() if k.startswith(prefix)}
    program="import json,hashlib,pathlib,sys;p=json.load(sys.stdin);print(json.dumps({k:hashlib.sha256((pathlib.Path(sys.argv[1])/k).read_bytes()).hexdigest() if (pathlib.Path(sys.argv[1])/k).is_file() else None for k in p}))"
    p=subprocess.run(['docker','exec','-i',name,'python','-c',program,'/app/gateway' if role=='gateway' else '/app/app'],input=json.dumps(list(expected)),text=True,capture_output=True,check=True)
    actual=json.loads(p.stdout);runtime_absent[role]=[k for k,v in actual.items() if v is None]
    checks[role+'_deployed_source_parity']=all(v==expected[k] for k,v in actual.items() if v is not None)
    if role=='gateway':
        baseline=subprocess.run(['docker','run','--rm','--network','none','-i','--entrypoint','python',before['containers'][name]['image'],'-c',program,'/app/gateway'],input=json.dumps(list(expected)),text=True,capture_output=True,check=True)
        checks['gateway_absent_modules_unchanged_from_baseline']=actual==json.loads(baseline.stdout)
sys.path.insert(0,str(ROOT/'docs/telegram-observer'));from real_e2e import command
packet=command('observer_task_progress',{'task_id':398})['result'];native=command('get_work_package',{'id':398})['result'];prior=json.loads((OUT/'main-integrations.json').read_text(encoding='utf-8'));native_before=next(r['result'] for r in prior['tools'] if r['tool']=='get_task_details')
checks['398_full_native_content_preserved']=all(native.get(k)==native_before.get(k) for k in ['id','subject','lockVersion','description','startDate','dueDate','customField13','customField14','customField15'])
checks['398_awaiting_owner_not_DONE']=packet['acceptance_status']=='AWAITING_OWNER_APPROVAL' and packet['business_status']=='READY FOR RELEASE' and packet['version']==10
checks['398_no_false_completed_event']=not any(e['event_type']=='TASK_COMPLETED' for e in packet['notification_events'])
state=command('engineering_status',{})['result'];checks['catalog_exact14']=len(state['backlog'])==14
containers={}
for name in before['containers']:
    d=json.loads(subprocess.check_output(['docker','inspect',name]))[0];containers[name]={'id':d['Id'],'image':d['Image'],'healthy':d['State'].get('Health',{}).get('Status'),'started_at':d['State']['StartedAt'],'restart_policy':d['HostConfig']['RestartPolicy']}
checks['gateway_image_unchanged']=containers['qldapm-ai-gateway-1']['image']==before['containers']['qldapm-ai-gateway-1']['image']
checks['n8n_container_untouched']=containers['qldapm-n8n-main']['id']==before['containers']['qldapm-n8n-main']['id'] and containers['qldapm-n8n-main']['started_at']==before['containers']['qldapm-n8n-main']['started_at']
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/telegram-ai/state/telegram.sqlite'
with sqlite3.connect(private.as_uri()+'?mode=ro',uri=True) as d:
    memory=json.loads(d.execute('SELECT document FROM memories WHERE user_id=1916909968').fetchone()[0]);budget=d.execute('SELECT calls FROM model_budget ORDER BY day DESC LIMIT 1').fetchone()[0]
checks['conversation_persisted_after_restarts']=memory.get('current_task_id')==398 and any(m['text'].startswith('Dựa trên dữ liệu kiểm tra thời gian thực') for m in memory['recent_messages'] if m['role']=='model')
checks['daily_model_calls18_of20']=budget==18
report={'at':time.time(),'checks':checks,'critical_gateway_before':old,'critical_gateway_after':current,'product_changed_files':changed,'source_counts':{'core':len(app_paths),'other':len(other)},'containers':containers,'telegram_budget_calls':budget,'task398':{k:packet.get(k) for k in ['task_id','version','workflow_status','business_status','acceptance_status','latest_run_id']},'gateway_receipts':after['gateway']['tables']['gemini_call_receipts']['rows'],'scope':'MAIN read-only; immutable table snapshot compared with pre-Core-release SQLite backup, no restore','after':after}
(OUT/'integrity-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks':checks,'images':{n:v['image'] for n,v in containers.items()},'model_calls':budget},ensure_ascii=False));assert all(checks.values())

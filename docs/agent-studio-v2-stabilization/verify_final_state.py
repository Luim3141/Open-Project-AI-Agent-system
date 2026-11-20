"""Read-only source/data/Telegram/n8n verification after resume; no sends or model calls."""
import json,hashlib,subprocess,sys,time,os
from pathlib import Path
from release import release,OUT
from preservation import capture
data=capture();before=json.loads((OUT/'resume-preservation-before.json').read_text());checks={}
checks['native']=data['native']==before['native']
checks['settings']=data['ecosystem']['files']==before['ecosystem']['files']
checks['n8n']=data['ecosystem']['n8n']==before['ecosystem']['n8n']
checks['telegram_tables']=data['ecosystem']['telegram_tables']==before['ecosystem']['telegram_tables']
checks['unrelated_containers']=data['ecosystem']['containers']==before['ecosystem']['containers']
checks['idle']=data['gateway']['mode']=='OFF' and data['gateway']['active']==0
parity={}
for role in ['core','gateway']:
 expected={k:v for k,v in release.source_hashes().items() if release.SOURCES[k][0]==role};actual=release.runtime_hashes(role);parity[role]={'files':len(expected),'match':expected==actual};checks[role+'_parity']=expected==actual
sys.path.insert(0,str(OUT.parents[1]/'openproject/ai/telegram-ai'))
import importlib.util
spec=importlib.util.spec_from_file_location('demo_reader',OUT/'live_demo.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
packet=prior.prior.command('observer_task_progress',{'task_id':398})['result']
checks['398_runtime']=packet['workflow_status']=='COMPLETED'
checks['398_awaiting_owner']=packet['acceptance_status']!='COMPLETED' and packet['business_status']=='READY FOR RELEASE'
checks['no_false_completed']=not any(e.get('event_type')=='TASK_COMPLETED' for e in packet.get('notification_events',[]))
checks['all_stages']=all(s['status']=='COMPLETED' for s in packet['stages']) and {s['agent_role'] for s in packet['stages']}=={'dev','reviewer','qa'}
report={'at':time.time(),'checks':checks,'source_parity':parity,'preservation':data,'task398':{k:packet.get(k) for k in ['task_id','version','workflow_status','business_status','acceptance_status','latest_run_id','related_tasks','notification_events']},'scope':'No Telegram sends or inference; existing full-read contract with real Gateway bearer and Native ACL'}
(OUT/'final-state.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'checks':checks,'parity':parity,'task398':report['task398']},ensure_ascii=False));assert all(checks.values())

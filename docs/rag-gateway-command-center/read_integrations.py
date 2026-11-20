"""Reuse live adapter read checks; extend to all 22 declared read tools. No model or writes."""
import json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
source=(OUT.parent/'functional-audit/read_integrations.py').read_text(encoding='utf-8')
source=source.replace("('list_projects',{})","('get_project_options',{}),('get_active_agents',{}),('get_pending_approvals',{}),('get_blocked_tasks',{}),('list_projects',{})",1)
p=subprocess.run(['docker','exec','-i','qldapm-ai-telegram-ai-1','python','-'],input=source,text=True,capture_output=True,encoding='utf-8',timeout=300)
(OUT/'main-integrations-stderr.log').write_text(p.stderr,encoding='utf-8')
assert p.returncode==0,p.stderr[-500:]
report=json.loads(p.stdout)
(OUT/'main-integrations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'tools':[{k:v for k,v in r.items() if k!='result'} for r in report['tools']],'checks':report['checks']},ensure_ascii=False))
assert len(report['tools'])==22 and all(r['status']=='READ_RETURNED' for r in report['tools']) and all(report['checks'].values())

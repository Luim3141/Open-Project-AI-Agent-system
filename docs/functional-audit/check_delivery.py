"""Whitelist and credential scan; never prints actual credentials or inspects unrelated user files."""
from pathlib import Path
import json,subprocess,os,re
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/functional-audit'
source=['architecture.md','openproject/ai/CHECKPOINT.md','openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb']+['openproject/ai/telegram-ai/app/'+n for n in ['engine.py','tools.py','system_instructions.py']]+['openproject/ai/telegram-ai/tests/'+n for n in ['test_engine.py','test_acceptance_answer.py','test_checkpoint_context.py','test_global_reads.py']]+['openproject/ai/tests/'+n for n in ['test_bridge_busy_controller.rb','test_read_bridge_errors.rb','test_report_controller.rb','test_native_qa_evidence.py','test_command_center_state_contract.py','test_owner_knowledge_ui_contract.py','test_native_qa_workflow.py']]
evidence=[str(p.relative_to(ROOT)).replace('\\','/') for p in OUT.iterdir() if p.is_file() and p.suffix in {'.md','.json','.py','.png','.log','.diff'}]+['docs/functional-audit/'+d+'/deployment.json' for d in ['core-candidate','core-candidate-v2']]
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai';secrets=[]
def sensitive(key,value):return bool(re.search('TOKEN|KEY|PASSWORD|SECRET',key,re.I)) and not key.endswith('_FILE') and len(value)>=8
for p in [private/'.env',private/'telegram-ai/.env']:
    if not p.exists():continue
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line or line.lstrip().startswith('#'):continue
        k,v=line.split('=',1);v=v.strip().strip('"').strip("'")
        if sensitive(k,v):secrets.append(v)
for p in [private/'telegram-ai/secrets/gateway.token',private/'secrets/gateway.token',private/'secrets/notification.key']:
    if p.exists():secrets.append(p.read_text().strip())
for name in ['qldapm-openproject-web-1','qldapm-ai-gateway-1','qldapm-ai-telegram-ai-1','qldapm-n8n-main']:
    d=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
    for item in d['Config']['Env']:
        k,_,v=item.partition('=')
        if sensitive(k,v):secrets.append(v)
hits=[]
for filename in source+evidence:
    p=ROOT/filename
    if p.suffix=='.png':continue
    data=p.read_text(encoding='utf-8-sig',errors='replace')
    if any(s and s in data for s in secrets):hits.append(filename)
    if re.search(r'\bAIza[\w-]{28,}|\b\d{7,12}:[A-Za-z0-9_-]{28,}',data):hits.append(filename+' TOKEN_PATTERN')
proof={'scope':'Explicit source/evidence whitelist; actual local and serving-container credentials plus token patterns. *_FILE values are mount paths, not secret contents. PNGs reviewed separately.','files':len(source+evidence),'leaks':hits,'passed':not hits,'excluded':'candidate contexts/manifests, __pycache__, .env, private cookies, DBs and unrelated untracked files'}
(OUT/'secret-scan.json').write_text(json.dumps(proof,indent=2)+'\n');assert not hits,hits
for name in ['secret-scan.json','commit-whitelist.json']:
    p='docs/functional-audit/'+name
    if p not in evidence:evidence.append(p)
(OUT/'commit-whitelist.json').write_text(json.dumps({'source':source,'evidence':evidence},indent=2)+'\n')
print(json.dumps(proof))

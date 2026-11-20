"""Scan explicit handoff paths against actual local credentials without printing any value."""
import json,os,re,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
paths=json.loads((OUT/'handoff-files.json').read_text())
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai'
secrets=set()
def add(value):
    if isinstance(value,str) and len(value.strip())>=8 and not value.startswith(('/', 'C:', 'D:', '${')):secrets.add(value.strip().encode())
for name in ['qldapm-ai-gateway-1','qldapm-ai-telegram-ai-1','qldapm-openproject-web-1','qldapm-openproject-db-1']:
    inspect=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
    for line in inspect['Config']['Env']:
        key,_,value=line.partition('=')
        if not key.endswith(('_FILE','_REF')) and re.search(r'(TOKEN|API_KEY|PASSWORD|SECRET|SECRET_KEY_BASE)$',key):add(value)
for file in [private/'.env',private/'telegram-ai/.env']:
    for line in file.read_text(encoding='utf-8-sig').splitlines():
        key,_,value=line.partition('=')
        if not key.endswith(('_FILE','_REF')) and re.search(r'(TOKEN|API_KEY|PASSWORD|SECRET|SECRET_KEY_BASE)$',key):add(value.strip('"\''))
for file in (private/'telegram-ai/secrets').iterdir():
    if file.is_file() and file.stat().st_size<65536:add(file.read_text(encoding='utf-8').strip())
for name in ['gemini.key','automation.key','ui.key','n8n_encryption.key','engineering-provider-token','test_pm_token.secret']:
    file=private/'gateway'/name
    if file.is_file():add(file.read_text(encoding='utf-8').strip())
def credentials(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if re.search(r'token|api.?key|password|secret',key,re.I) and not re.search(r'file|path|ref',key,re.I):add(item)
            credentials(item)
    elif isinstance(value,list):
        for item in value:credentials(item)
for name in ['config.json','credentials.json','gemini.json','webhook_secret.json']:
    file=private/'gateway'/name
    if file.exists():credentials(json.loads(file.read_text(encoding='utf-8-sig')))
for file in [private/'telegram-ai/ui-uat.json']:
    if file.exists():add(json.loads(file.read_text(encoding='utf-8-sig')).get('password'))
matches=[];patterns=[]
for relative in paths:
    path=ROOT/relative;raw=path.read_bytes()
    if any(value in raw for value in secrets):matches.append(relative)
    if path.suffix.lower() not in {'.png'} and re.search(rb'AIza[A-Za-z0-9_-]{30,}|\b\d{8,12}:[A-Za-z0-9_-]{30,}\b',raw):patterns.append(relative)
report={'scope':'Exact handoff whitelist; actual container/env/secret-file/UI credentials read locally, never exported','files':len(paths),'credential_values_checked':len(secrets),'actual_credential_matches':matches,'high_confidence_patterns':patterns,'passed':not matches and not patterns}
(OUT/'secret-scan.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['passed']

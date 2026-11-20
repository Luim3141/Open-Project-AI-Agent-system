"""Verify original rows/config remain intact while allowing the approved fresh E2E additions."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))['protected_state']
code = '''import sqlite3,json,hashlib,pathlib,sys
p=json.load(sys.stdin);c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
tables={}
for t in ['ai_queue','ai_runs','requests','gemini_call_receipts','engineering_checkpoints','tokens']:
 n=p['tables'][t]['rows'];old=c.execute('SELECT * FROM '+t+' ORDER BY rowid LIMIT ?',(n,)).fetchall()
 tables[t]={'original_rows':n,'original_rows_sha256':hashlib.sha256(json.dumps(old,separators=(',',':')).encode()).hexdigest(),'current_rows':c.execute('SELECT count(*) FROM '+t).fetchone()[0]}
print(json.dumps({'tables':tables,'files':{f:hashlib.sha256((pathlib.Path('/state')/f).read_bytes()).hexdigest() for f in p['files']},'control':c.execute('SELECT project,mode FROM engineering_control').fetchall(),'active':c.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]}))'''
result = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-c', code],
    input=json.dumps(baseline), text=True, capture_output=True, timeout=90)
assert result.returncode == 0, 'COMPATIBILITY_READ_FAILED'
state = json.loads(result.stdout)
for name, values in state['tables'].items():
    assert values['original_rows_sha256'] == baseline['tables'][name]['sha256'], 'ORIGINAL_ROWS_CHANGED:' + name
assert state['files'] == baseline['files'], 'ORIGINAL_PROVIDER_OR_CONFIG_CHANGED'
containers = {}
for name in ['qldapm-ai-gateway-1', 'qldapm-openproject-web-1', 'qldapm-ai-telegram-ai-1', 'qldapm-n8n-main']:
    item = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
    containers[name] = {'image': item['Image'], 'state': item['State']['Status'],
        'health': item['State'].get('Health', {}).get('Status'),
        'started_at': item['State']['StartedAt'], 'restart_policy': item['HostConfig']['RestartPolicy']['Name'],
        'networks': list(item['NetworkSettings']['Networks'])}
assert containers['qldapm-n8n-main']['image'] == json.loads((OUT / 'baseline.json').read_text())['containers']['n8n']['image']
program = """const {DatabaseSync}=require('node:sqlite');const {createHash}=require('node:crypto');
const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const pin=t=>d.prepare('SELECT * FROM '+t+' ORDER BY id').all().map(r=>({id:r.id,sha256:createHash('sha256').update(JSON.stringify(r)).digest('hex')}));
console.log(JSON.stringify({workflows:pin('workflow_entity'),credentials:pin('credentials_entity')}));d.close();"""
current_n8n = json.loads(subprocess.check_output(['docker', 'exec', 'qldapm-n8n-main', 'node', '-e', program]))
original_n8n = json.loads((OUT / 'ecosystem-before.json').read_text())['n8n']
n8n_preserved = all(row in current_n8n[k] for k in ('workflows', 'credentials') for row in original_n8n[k])
assert n8n_preserved, 'EXISTING_N8N_ROWS_CHANGED'
report = {'status': 'PASS', 'scope': 'ORIGINAL_GATEWAY_ROWS_AND_CONFIG_PLUS_APPROVED_NEW_E2E',
    'state': state, 'containers': containers, 'original_n8n_rows_preserved': n8n_preserved,
    'n8n': current_n8n,
    'native_security_limitation': 'Users full baseline hash differs after actual failed/successful UI authentication; exact entire delta not proven. No reset or role/password mutation performed.'}
(OUT / 'compatibility-final.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'PASS', 'original_rows': {k: v['original_rows'] for k, v in state['tables'].items()},
    'current_rows': {k: v['current_rows'] for k, v in state['tables'].items()}, 'control': state['control'], 'active': state['active']}))

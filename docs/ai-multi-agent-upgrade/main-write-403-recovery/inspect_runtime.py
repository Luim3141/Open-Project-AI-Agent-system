"""Read-only incident snapshot. Never emit credentials, prompts or session data."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'openproject/ai'))
from jira_sync_backup import database_state
from free_tier_staging import private_directory

def run(*args, data=None):
    p = subprocess.run(args, input=data, capture_output=True, timeout=90)
    assert p.returncode == 0, 'DIAGNOSTIC_FAILED_OUTPUT_WITHHELD:' + args[0]
    return p.stdout.decode('utf-8')

def main():
    target = OUT / 'runtime-before.json'
    assert not target.exists(), 'SNAPSHOT_EXISTS_DO_NOT_OVERWRITE'
    private = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/main-write-403-recovery'
    private_directory(private)
    result = {'at': datetime.now(timezone.utc).isoformat(), 'containers': {}, 'source': {}}
    for name in run('docker', 'ps', '--format', '{{.Names}}').splitlines():
        c = json.loads(run('docker', 'inspect', name))[0]
        result['containers'][name] = {k: c[k] for k in ('Id', 'Image')}
        result['containers'][name]['started'] = c['State']['StartedAt']
    for folder in ('gateway', 'core/overlay'):
        for path in (ROOT/'openproject/ai'/folder).rglob('*'):
            if path.is_file() and '__pycache__' not in str(path):
                rel = path.relative_to(ROOT).as_posix()
                result['source'][rel] = hashlib.sha256(path.read_bytes()).hexdigest()
                copy = private/'source-before'/rel
                copy.parent.mkdir(parents=True, exist_ok=True)
                copy.write_bytes(path.read_bytes())
    result['database'] = database_state('qldapm-openproject-db-1')
    code = '''import sqlite3,json,hashlib,pathlib
s=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);s.row_factory=sqlite3.Row
c=json.loads(pathlib.Path('/state/config.json').read_text());g=json.loads(pathlib.Path('/state/gemini.json').read_text())
print(json.dumps({'mode':c.get('gateway_mode'),'project':c['project_id'],'users':c['users'],'multi_agent':g.get('multi_agent'),
'busy':s.execute("select count(*) from ai_runs where state in ('running','queued')").fetchone()[0],
'provider_receipts':s.execute('select count(*) from gemini_call_receipts').fetchone()[0],
'usage':s.execute('select count(*) from gemini_usage').fetchone()[0],
'recent_denials':[dict(r) for r in s.execute("select id,at,actor,action,target,outcome,run_id,trace_id from audit where outcome in ('PermissionError','403','409','422') order by at desc limit 30")],
'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app/gateway').glob('*') if p.is_file()}}))'''
    result['gateway'] = json.loads(run('docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-', data=code.encode()))
    for name in ('qldapm-ai-gateway-1', 'qldapm-openproject-web-1'):
        p = subprocess.run(['docker', 'logs', '--timestamps', '--since', '4h', name], capture_output=True)
        # Structured request lines only: no request params, cookies or free text.
        lines = (p.stdout+p.stderr).decode(errors='replace').splitlines()
        safe = [line for line in lines if ('method=' in line and 'controller=QldapmAIController' in line)
                or ('HTTP/1.1' in line and '/internal/ui' in line)]
        (OUT/(name+'-requests.log')).write_text('\n'.join(safe), encoding='utf-8')
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result['gateway'].items() if k!='hashes'}))

if __name__ == '__main__': main()

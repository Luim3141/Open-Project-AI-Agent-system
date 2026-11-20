"""Restart only Telegram service and verify durable records without showing their contents."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

OUT = Path(__file__).resolve().parent
NAME = 'qldapm-ai-telegram-ai-1'


def call(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, 'LOCAL_CHECK_FAILED'
    return result.stdout


def snapshot():
    code = '''import sqlite3,json,hashlib
c=sqlite3.connect('file:/state/telegram.sqlite?mode=ro',uri=True)
tables={}
for t in ['pairs','memories','updates','notification_context','telegram_notification_outbox','model_budget']:
 rows=c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall()
 tables[t]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()}
print(json.dumps(tables))'''
    return json.loads(call(['docker', 'exec', NAME, 'python', '-c', code]))


before = snapshot()
inspection = json.loads(call(['docker', 'inspect', NAME]))[0]
assert inspection['HostConfig']['RestartPolicy']['Name'] == 'unless-stopped'
assert inspection['HostConfig']['ReadonlyRootfs']
assert not inspection['HostConfig']['PortBindings']
call(['docker', 'restart', NAME])
for _ in range(25):
    item = json.loads(call(['docker', 'inspect', NAME]))[0]
    if item['State'].get('Health', {}).get('Status') == 'healthy':
        break
    time.sleep(2)
assert item['State'].get('Health', {}).get('Status') == 'healthy'
after = snapshot()
assert after['pairs'] == before['pairs'], 'PAIRING_PERSISTENCE_FAILED'
assert after['telegram_notification_outbox'] == before['telegram_notification_outbox'], 'DELIVERED_OUTBOX_CHANGED'
assert after['notification_context'] == before['notification_context'], 'REPLY_CONTEXT_CHANGED'
no_new_updates = after['updates'] == before['updates']
if no_new_updates:
    assert after['memories'] == before['memories'], 'MEMORY_PERSISTENCE_FAILED'
    assert after['model_budget'] == before['model_budget'], 'UNREQUESTED_STARTUP_INFERENCE'
source = "import pathlib,hashlib,json;print(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in pathlib.Path('/app/app').glob('*.py')}))"
actual = json.loads(call(['docker', 'exec', NAME, 'python', '-c', source]))
expected = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (OUT.parents[1] / 'openproject/ai/telegram-ai/app').glob('*.py')}
assert actual == expected
result = {'status': 'PASS', 'scope': 'TELEGRAM_SERVICE_ONLY', 'image': item['Image'],
    'restart_policy': 'unless-stopped', 'health': 'healthy', 'source_parity': True,
    'before': before, 'after': after, 'no_new_updates_during_restart': no_new_updates,
    'desktop_restart': False, 'windows_reboot': False}
(OUT / 'service-restart.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k not in {'before', 'after'}}))

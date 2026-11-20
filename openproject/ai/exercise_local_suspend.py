"""Bounded staging suspension fault drill; does not put Windows to sleep."""
import json
from pathlib import Path
import time

from jira_sync_backup import command, inspect
from local_runtime import check_owned, expected_images, name, services, status


def gateway_state():
    program = '''import sqlite3,json
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
result={t:dict(d.execute('select state,count(*) from '+t+' group by state')) for t in ('jobs','ai_runs','proposals')}
result['usage_rows']=d.execute('select count(*) from gemini_usage').fetchone()[0]
print(json.dumps(result))
'''
    return json.loads(command(['docker', 'exec', name('staging-gateway'), 'python', '-c', program]))


before = gateway_state()
assert not any(before['jobs'].get(s, 0) for s in ('queued', 'running', 'failed_or_unknown'))
assert before['ai_runs'].get('running', 0) == 0
images = expected_images()
infos = {s: inspect(name(s)) for s in services()}
for service, info in infos.items():
    check_owned(service, info, images)
    assert info['State']['Running'] and not info['State']['Paused']
targets = [name(s) for s in services()]
paused = False
try:
    command(['docker', 'pause', *targets])
    paused = True
    assert all(inspect(n)['State']['Paused'] for n in targets)
    time.sleep(35)
finally:
    # Even a failed assertion must not leave the staged application paused.
    if paused:
        command(['docker', 'unpause', *targets])
deadline = time.monotonic() + 300
while time.monotonic() < deadline:
    if status()['all_healthy']:
        break
    time.sleep(3)
else:
    raise RuntimeError('SUSPEND_RESUME_READINESS_TIMEOUT')
assert gateway_state() == before, 'GATEWAY_STATE_CHANGED_DURING_SUSPEND'
assert all(inspect(name(s))['Id'] == info['Id'] for s, info in infos.items())
result = {'passed': True, 'processes_suspended_seconds': 35, 'services': list(infos),
          'containers_recreated': False, 'gateway_ledger_jobs_runs_proposals_unchanged': True,
          'all_healthy_after_resume': True, 'physical_windows_sleep_tested': False,
          'windows_power_settings_changed': False, 'google_called': False}
output = Path(__file__).resolve().parents[2] / 'docs/ai-multi-agent-upgrade/artifacts/QUICK-suspend-resume.json'
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(result))

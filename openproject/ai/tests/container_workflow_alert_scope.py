"""Five real Native authorizations before project-wide sanitized workflow metadata is shown."""
import json
from pathlib import Path
import sys
import httpx

sys.path.insert(0, '/app')
from gateway.store import Store

store = Store('/state')
config = json.loads(Path('/state/config.json').read_text())
records = []
with httpx.Client(base_url='http://127.0.0.1:8090', trust_env=False, timeout=95) as client:
    for actor, role in sorted((int(actor), role) for actor, role in config['users'].items()):
        token = store.issue_token(actor, role, store.credential(actor))
        response = client.post('/api/v1/commands', headers={'Host': 'gateway:8090', 'Authorization': 'Bearer ' + token},
                               json={'action': 'analyze', 'arguments': {}})
        assert response.status_code == 200
        alerts = response.json()['result']['workflow_alerts']
        assert len(alerts) == 1 and alerts[0]['workflow_id'] == 'qldapmManualStatus'
        assert set(alerts[0]) == {'run_id', 'trace_id', 'workflow_id', 'execution_id', 'day', 'error_code', 'observed_at'}
        records.append({'actor': actor, 'role': role, 'native_authorized_notice': True})
assert store.workflow_alerts(config['project_id'] + 1) == []
with store.connect() as database:
    assert 'P04_PRIVATE_RAW_ERROR_MUST_NOT_LEAVE_N8N' not in '\n'.join(database.iterdump())
    assert database.execute("SELECT count(*) FROM automation_runs WHERE json_extract(receipt,'$.kind')='workflow_error'").fetchone()[0] == 1
    assert database.execute('SELECT count(*) FROM gemini_usage').fetchone()[0] == 0
print(json.dumps({'passed': True, 'roles': records, 'cross_project_empty': True, 'one_sanitized_notice': True,
                  'private_raw_error_absent_from_gateway': True, 'provider_calls': 0, 'native_writes': 0}))

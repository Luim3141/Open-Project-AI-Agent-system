"""HTTP own daily snapshots on real native identities; no provider/native writes."""
import json
from pathlib import Path
import sys
import httpx

sys.path.insert(0, '/app')
from gateway.store import Store
from gateway.daily_brief import day
from gateway.native import Native, NativeError

store = Store('/state')
config = json.loads(Path('/state/config.json').read_text())
records = []
with httpx.Client(base_url='http://127.0.0.1:8090', trust_env=False, timeout=95) as client:
    for actor, role in sorted((int(actor), role) for actor,role in config['users'].items()):
        token = store.issue_token(actor, role, store.credential(actor))
        headers = {'Host': 'gateway:8090', 'Authorization': 'Bearer ' + token}
        response = client.post('/api/v1/commands', headers=headers, json={'action': 'analyze', 'arguments': {}})
        assert response.status_code == 200, 'NATIVE_ACTOR_ANALYZE_FAILED'
        summary = response.json()['result']
        brief = summary['daily_brief']
        native = Native(config['openproject_url'], store.credential(actor), config['project_id'])
        compact = native.summary(actor)
        assert compact == {key: sorted(summary[key]) if key == 'overdue_ids' else summary[key]
                           for key in ('count', 'by_status', 'overdue_ids')}, 'COMPACT_HAL_MISMATCH:' + json.dumps({key: compact[key] == (sorted(summary[key]) if key == 'overdue_ids' else summary[key]) for key in compact})
        assert brief['state'] == 'READY', 'BRIEF_STATE:' + brief['state']
        assert brief['snapshot']['count'] == summary['count'], 'SNAPSHOT_COUNT_MISMATCH'
        assert brief['snapshot']['by_status'] == summary['by_status'] and 'by_assignee' not in brief['snapshot'], 'SNAPSHOT_STATUS_OR_PRIVACY_MISMATCH'
        for selector in ('actor=12', 'project_id=99', 'user_id=7'):
            try:
                native.call('/api/v3/qldapm/daily_summary?' + selector)
            except NativeError as error:
                assert error.status == 422
            else:
                raise AssertionError('NATIVE_SUMMARY_SELECTOR_ACCEPTED')
        stored = store.daily_brief(actor, config['project_id'], day())
        assert stored['actor'] == actor and stored['role'] == role
        assert store.daily_brief(actor, config['project_id'] + 1, day()) is None
        denied = client.post('/api/v1/commands', headers=headers, json={'action': 'analyze', 'arguments': {'actor_id': actor + 100}})
        assert denied.status_code == 422
        records.append({'actor': actor, 'role': role, 'own_native_snapshot_ready': True,
                        'count': brief['snapshot']['count'], 'cross_actor_parameter_denied': True,
                        'compact_native_equals_full_hal': True, 'native_query_selectors_denied': True})
with store.connect() as database:
    rows = database.execute('SELECT receipt FROM automation_runs').fetchall()
    receipts = [json.loads(row[0]) for row in rows]
    daily = [receipt for receipt in receipts if receipt['kind'] == 'daily_brief']
    assert len(daily) == 1 and daily[0]['ready'] == 5 and daily[0]['state'] == 'COMPLETED'
    assert database.execute('SELECT COUNT(*) FROM daily_briefs').fetchone()[0] == 5
    assert database.execute('SELECT COUNT(*) FROM gemini_usage').fetchone()[0] == 0
    started = database.execute('SELECT created FROM automation_runs WHERE request_key=?', ('daily:' + day(),)).fetchone()[0]
    reports = [json.loads(row[0]) for row in database.execute('SELECT document FROM daily_briefs')]
    elapsed = max(report['observed_at'] for report in reports) - started
    assert 0 <= elapsed < 25
print(json.dumps({'passed': True, 'actual_native_roles': records, 'one_daily_receipt_five_reports': True,
                  'five_actor_collection_seconds': round(elapsed, 3),
                  'provider_calls': 0, 'native_writes': 0, 'primary_gateway_data_mounted': False}))

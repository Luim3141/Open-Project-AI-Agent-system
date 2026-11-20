"""Narrow native sync writes with durable receipts and conservative reconciliation."""
import json
import re
from copy import deepcopy
import time
from pathlib import Path

from gateway.native import NativeError
from jira_sync import fingerprint, private_save


def payload_matches(resource, payload):
    for key, value in payload.items():
        if key == '_links':
            if any(resource.get('_links', {}).get(name, {}).get('href') != link['href'] for name, link in value.items()):
                return False
        elif key == 'description':
            if resource.get(key, {}).get('raw', '') != value['raw']:
                return False
        elif resource.get(key) != value:
            return False
    return True


def apply_content(row, target, directory):
    if type(row['id']) is not int or row['id'] <= 0 or set(row['payload']) - {'subject', 'description', 'startDate', 'dueDate', '_links'}:
        raise ValueError('CONTENT_PAYLOAD_SCOPE_DENIED')
    if set(row['payload'].get('_links', {})) - {'parent', 'assignee', 'priority', 'sprint'}:
        raise ValueError('CONTENT_LINK_SCOPE_DENIED')
    path = Path(directory) / f"content-{row['id']}.json"
    current = target.call(f"/api/v3/work_packages/{row['id']}")
    if path.exists():
        receipt = json.loads(path.read_text())
        if receipt['hash'] != fingerprint(row):
            raise ValueError('RECEIPT_OPERATION_CONFLICT')
        if receipt['state'] == 'applied':
            return receipt if payload_matches(current, row['payload']) else {'state': 'conflict', 'id': row['id'], 'reason': 'APPLIED_DATA_CHANGED'}
        return {**receipt, 'state': 'unknown'} if receipt['state'] == 'pending' else receipt
    if current['lockVersion'] != row['version']:
        return {'state': 'conflict', 'reason': 'NATIVE_VERSION_CHANGED', 'id': row['id']}
    if not row['payload']:
        return {'state': 'unchanged', 'id': row['id']}
    receipt = {'state': 'pending', 'id': row['id'], 'hash': fingerprint(row), 'before_version': current['lockVersion']}
    private_save(path, receipt)
    try:
        result = target.call(f"/api/v3/work_packages/{row['id']}?notify=false", 'PATCH', {**row['payload'], 'lockVersion': current['lockVersion']})
        actual = target.call(f"/api/v3/work_packages/{row['id']}")
        receipt.update(state='applied' if payload_matches(actual, row['payload']) else 'conflict',
                       after_version=actual['lockVersion'], native_result_id=result['id'])
    except NativeError as error:
        receipt.update(state='conflict' if error.status == 409 else 'blocked' if 400 <= error.status < 500 and error.status not in {408, 429} else 'unknown', http_status=error.status,
                       reason='NATIVE_REQUEST_DENIED' if error.status < 500 else 'RECONCILE_BEFORE_RETRY')
    except (TimeoutError, RuntimeError):
        receipt.update(state='unknown', reason='RECONCILE_BEFORE_RETRY')
    private_save(path, receipt, replace=True)
    return receipt


def apply_preview(preview, target, directory, activity_id, source_check=lambda: None, progress=lambda *args: None):
    if preview['target'] != target.name or preview['project_id'] != target.project or preview['actor'] != target.actor:
        raise ValueError('APPROVED_TARGET_OR_ACTOR_MISMATCH')
    directory = Path(directory)
    time_entries = target.collection('/api/v3/time_entries')
    results = []
    order = {'Epic': 0, 'Task': 1, 'Subtask': 2}
    rows = sorted(preview['rows'], key=lambda row: (order.get(row.get('kind', ''), 3), row['id']))
    for number, row in enumerate(rows, 1):
        if (number - 1) % 10 == 0:
            source_check()
        current = target.call(f"/api/v3/work_packages/{row['id']}")
        if (current.get(target.bootstrap['fields']['Source ID']) != row['source_id'] or
                current['_links']['project']['href'] != f'/api/v3/projects/{target.project}'):
            raise ValueError('NATIVE_SOURCE_OR_PROJECT_CHANGED')
        result = {'id': row['id'], 'source_id': row['source_id'], 'jira_key': row['jira_key'],
                  'content': apply_content(row, target, directory), 'comments': [], 'worklogs': [],
                  'skipped': row['skipped'], 'status': {'state': 'unchanged'}}
        if result['content']['state'] == 'unknown':
            results.append(result)
            private_save(directory / 'results.json', {'at': time.time(), 'preview_hash': fingerprint(preview), 'rows': results}, replace=True)
            break
        if result['content']['state'] in {'applied', 'unchanged'}:
            for kind, child_key in [('comment', 'comments'), ('worklog', 'worklogs')]:
                if any(child['state'] == 'unknown' for key in ('comments', 'worklogs') for child in result[key]):
                    break
                for record in row['children'][child_key]:
                    receipt = apply_record(kind, row['id'], record, target, directory, activity_id,
                                           existing_records=time_entries if kind == 'worklog' else None)
                    result[child_key].append({'source_id': record['source_id'], **receipt})
                    if receipt['state'] == 'unknown':
                        break
            if (row['source_status'] != row['native_status'] and
                    not any(child['state'] == 'unknown' for key in ('comments', 'worklogs') for child in result[key])):
                result['status'] = {'state': 'blocked', 'source_status': row['source_status'], 'reasons': row['gate_errors']}
                if target.name == 'staging' and not row['gate_errors']:
                    result['status'] = apply_status(row, target, directory)
        results.append(result)
        private_save(directory / 'results.json', {'at': time.time(), 'preview_hash': fingerprint(preview), 'rows': results}, replace=True)
        progress(number, len(rows))
        if any(child['state'] == 'unknown' for key in ('comments', 'worklogs') for child in result[key]) or result['status']['state'] == 'unknown':
            break
    return results


def apply_status(row, target, directory):
    path = Path(directory) / f"status-{row['id']}.json"
    signature = fingerprint({'id': row['id'], 'status_id': row['status_id'], 'preview_row': row})
    actual = target.call(f"/api/v3/work_packages/{row['id']}")
    if path.exists():
        previous = json.loads(path.read_text())
        if previous['hash'] != signature:
            raise ValueError('RECEIPT_OPERATION_CONFLICT')
        if previous['state'] in {'pending', 'unknown'}:
            return {**previous, 'state': 'unknown'}
        if previous['state'] == 'applied' and actual['_links']['status']['href'] != f"/api/v3/statuses/{row['status_id']}":
            return {'state': 'conflict', 'reason': 'APPLIED_STATUS_CHANGED'}
        return previous
    if actual['_links']['status']['title'].upper() != row['native_status']:
        return {'state': 'conflict', 'reason': 'NATIVE_STATUS_CHANGED'}
    capability = target.call('/api/v3/qldapm/capabilities')
    if capability.get('gate_schema') != 2 or capability.get('enforced') is not True or capability.get('project_id') != target.project:
        raise ValueError('ENFORCED_CORE_GATE_REQUIRED')
    gate = target.call(f"/api/v3/qldapm/gates/{row['id']}")
    if not any(edge['to'] == row['source_status'] and not edge['errors'] for edge in gate['transitions']):
        return {'state': 'blocked', 'reason': 'NATIVE_GATE_CHANGED'}
    receipt = {'state': 'pending', 'hash': signature, 'before_version': actual['lockVersion']}
    private_save(path, receipt)
    try:
        target.call(f"/api/v3/work_packages/{row['id']}?notify=false", 'PATCH',
            {'lockVersion': actual['lockVersion'], '_links': {'status': {'href': f"/api/v3/statuses/{row['status_id']}"}}})
        changed = target.call(f"/api/v3/work_packages/{row['id']}")
        receipt.update(state='applied' if changed['_links']['status']['href'] == f"/api/v3/statuses/{row['status_id']}" else 'conflict',
                       after_version=changed['lockVersion'])
    except NativeError as error:
        receipt.update(state='conflict' if error.status == 409 else 'blocked' if 400 <= error.status < 500 and error.status not in {408, 429} else 'unknown', http_status=error.status)
    except (RuntimeError, TimeoutError):
        receipt.update(state='unknown', reason='RECONCILE_BEFORE_RETRY')
    private_save(path, receipt, replace=True)
    return receipt


def verify_preview(preview, target, activity_id):
    items = {row['id']: row for row in target.packages()}
    time_entries = target.collection('/api/v3/time_entries')
    report = []
    for row in preview['rows']:
        actual = items.get(row['id'])
        entry = {'id': row['id'], 'source_id': row['source_id'], 'jira_key': row['jira_key'],
                 'content': 'synced' if actual and payload_matches(actual, row['payload']) else 'conflict',
                 'status': 'synced' if actual and actual['_links']['status']['title'].upper() == row['source_status'] else 'blocked',
                 'jira_status': row['source_status'], 'native_status': actual['_links']['status']['title'] if actual else None,
                 'status_reasons': row['gate_errors'], 'skipped': row['skipped'], 'comments': [], 'worklogs': []}
        for kind, key in [('comment', 'comments'), ('worklog', 'worklogs')]:
            records = target.collection(f"/api/v3/work_packages/{row['id']}/activities") if row['children'][key] and kind == 'comment' else time_entries
            for record in row['children'][key]:
                payload = deepcopy(record['payload'])
                if kind == 'worklog':
                    payload['_links']['activity'] = {'href': f'/api/v3/time_entries/activities/{activity_id}'}
                matching = [item for item in records if record['marker'] in (item.get('comment') or {}).get('raw', '')]
                entry[key].append({'source_id': record['source_id'], 'state': 'synced' if len(matching) == 1 and record_matches(kind, matching[0], payload, target.actor) else 'conflict'})
        report.append(entry)
    return {'target': target.name, 'project_id': target.project, 'at': time.time(), 'rows': report,
            'summary': {'source_rows': len(report), 'native_total': len(items),
                'content_synced': sum(row['content'] == 'synced' for row in report),
                'content_conflicts': sum(row['content'] != 'synced' for row in report),
                'statuses_synced': sum(row['status'] == 'synced' for row in report),
                'statuses_blocked': sum(row['status'] == 'blocked' for row in report),
                'comments_synced': sum(child['state'] == 'synced' for row in report for child in row['comments']),
                'worklogs_synced': sum(child['state'] == 'synced' for row in report for child in row['worklogs'])}}


def seconds_from_iso(value):
    match = re.fullmatch(r'PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?', value or '')
    if not match or not any(match.groups()):
        raise ValueError('NATIVE_DURATION_INVALID')
    return sum(float(part or 0) * unit for part, unit in zip(match.groups(), [3600, 60, 1]))


def record_matches(kind, resource, payload, actor):
    if ((resource.get('comment') or {}).get('raw') != payload['comment']['raw'] or
            resource.get('_links', {}).get('user', {}).get('href') != f'/api/v3/users/{actor}'):
        return False
    if kind == 'worklog':
        return (resource.get('spentOn') == payload['spentOn'] and
            seconds_from_iso(resource.get('hours')) == seconds_from_iso(payload['hours']) and
            all(resource.get('_links', {}).get(name, {}).get('href') == value['href'] for name, value in payload['_links'].items()))
    return True


def apply_record(kind, work_package, record, target, directory, activity_id=None, existing_records=None):
    if kind not in {'comment', 'worklog'} or type(work_package) is not int or work_package <= 0:
        raise ValueError('CHILD_OPERATION_SCOPE_DENIED')
    payload = deepcopy(record['payload'])
    if kind == 'worklog':
        if type(activity_id) is not int or activity_id <= 0:
            raise ValueError('SIMULATION_ACTIVITY_REQUIRED')
        if (payload['_links']['entity']['href'] != f'/api/v3/work_packages/{work_package}' or
                payload['_links']['user']['href'] != f'/api/v3/users/{target.actor}'):
            raise ValueError('WORKLOG_ACTOR_OR_ENTITY_MISMATCH')
        payload['_links']['activity'] = {'href': f'/api/v3/time_entries/activities/{activity_id}'}
    signature = fingerprint({'kind': kind, 'work_package': work_package, 'payload': payload})
    path = Path(directory) / ('child-' + signature + '.json')
    previous = json.loads(path.read_text()) if path.exists() else None
    if previous and previous['hash'] != signature:
        raise ValueError('RECEIPT_OPERATION_CONFLICT')
    collection = f'/api/v3/work_packages/{work_package}/activities' if kind == 'comment' else '/api/v3/time_entries'
    records = target.collection(collection) if existing_records is None else existing_records
    matches = [row for row in records if record['marker'] in (row.get('comment') or {}).get('raw', '')]
    if len(matches) > 1:
        return {'state': 'conflict', 'reason': 'DUPLICATE_SOURCE_MARKER'}
    if matches:
        row = matches[0]
        if not record_matches(kind, row, payload, target.actor):
            return {'state': 'conflict', 'reason': 'SOURCE_MARKER_PAYLOAD_OR_ACTOR_MISMATCH'}
        receipt = {'state': 'reconciled', 'native_id': row['id'], 'hash': signature,
                   'source_marker': record['marker'], 'previous_state': previous.get('state') if previous else None}
        private_save(path, receipt, replace=path.exists())
        return receipt
    if previous:
        return {'state': 'unknown' if previous['state'] in {'pending', 'unknown'} else 'conflict',
                'reason': 'SOURCE_RECEIPT_NO_LONGER_VISIBLE_NO_RETRY', 'hash': signature}
    receipt = {'state': 'pending', 'hash': signature, 'source_marker': record['marker']}
    private_save(path, receipt)
    try:
        created = target.call(collection + '?notify=false', 'POST', payload)
        resource = target.call('/api/v3/activities/' + str(created['id']) if kind == 'comment' else '/api/v3/time_entries/' + str(created['id']))
        receipt.update(state='applied' if record_matches(kind, resource, payload, target.actor) else 'conflict', native_id=created['id'])
        if receipt['state'] == 'applied' and existing_records is not None:
            existing_records.append(resource)
    except NativeError as error:
        receipt.update(state='blocked' if 400 <= error.status < 500 and error.status not in {408, 429} else 'unknown', http_status=error.status)
    except (RuntimeError, TimeoutError):
        receipt.update(state='unknown', reason='RECONCILE_BEFORE_RETRY')
    private_save(path, receipt, replace=True)
    return receipt

"""Read-only workflow projection. The host supplies bounded, sanitized n8n metadata."""
import json
import math
import re
import time


# Fixed MAIN identities; an installation change requires explicit source review.
CATALOG = [
    ('WF01', 'X2O2QdPY6QLOrWqL', 'Local Document Ingestion', 'Nạp nguồn đã được cấp quyền', 'Authenticated source webhook', 'tab-knowledge'),
    ('WF02', 'Anl8LNdN4NNTKRpe', 'OpenProject Event Sync', 'Đối chiếu Native version/visibility', 'Native inventory event / authenticated sync', 'tab-backlog'),
    ('WF03', 'XoP4M520TMG3WgeY', 'Natural Language Request Orchestrator', 'Tiếp nhận yêu cầu qua n8n', 'Authenticated request webhook', 'tab-backlog'),
    ('WF04', 'elfapV5D2PTnLiHW', 'Multi-Agent Execution Tracking', 'Quan sát lifecycle và GitHub delivery', 'Durable lifecycle / GitHub event', 'tab-mission'),
    ('WF05', 'xCZFw45fmDQG5gNq', 'Native API Approval Workflow', 'Xem đúng proposal; không tự phê duyệt', 'Authenticated proposal preview', None),
    ('WF06', 'Jq18aFSqfuUybEic', 'Native API Execution & Verification', 'Thực thi quyết định được phép và read-back', 'Explicit human decision', None),
    ('WF07', 'BpCQrGR866vg4BqQ', 'Daily Project Brief', 'Thu thập báo cáo ngày', 'Daily cron / signed collector', 'tab-reports'),
    ('WF08', 'RXWjVUL8ozqhjY4w', 'Sprint Risk', 'Đọc rủi ro sprint', 'Authenticated risk webhook', None),
    ('WF09', 'tOyBIPw6sGjgzjtU', 'Bug Lifecycle Automation', 'Bug context / đề xuất transition', 'Authenticated bug webhook', 'tab-backlog'),
    ('WF10', 'tOY7QUa9SrWPOe9e', 'Task Orchestration & Decomposition', 'WBS draft/read; materialization riêng', 'Authenticated decomposition webhook', 'tab-backlog'),
    ('WF11', 'LeRVT3LWNBkJ2iz3', 'QA Gate Transition', 'Đối chiếu tested commit, review và QA', 'Engineering QA event / authenticated QA', 'tab-execution'),
    ('WF12', 'ZkgS8RZbPRA2zbhQ', 'Weekly Summary', 'Thu thập báo cáo tuần', 'Weekly cron / signed collector', 'tab-reports'),
    ('WF13', '2tr0jpqaaAiq9IOU', 'Second Brain RAG Re-indexing', 'Kiểm chứng index/citation hoặc feedback', 'Index verified event / feedback webhook', 'tab-knowledge'),
    ('WF14', '8ycOUQy9gtT60nkN', 'Durable RAG Recovery', 'Quan sát retry/DLQ; worker sở hữu recovery', 'Index failed event / owned recovery webhook', 'tab-knowledge'),
    ('WF15', 'NLugfE3U8dBS88Wg', 'Reconciliation & Drift Detection', 'Đối chiếu và xếp hàng sửa drift có giới hạn', 'Reconcile event / integrity webhook', 'tab-knowledge'),
    ('WF16', '5FRYNPSot18UDpKa', 'Main Health Monitoring', 'Health/backlog; không phát inference', 'Monitoring cron / signed collector', 'tab-integrations'),
]
SNAPSHOT_FILE = 'n8n-workflow-status.json'
MAX_BYTES = 65536
MAX_AGE = 300
EXECUTION_KEYS = {'id', 'status', 'mode', 'started_at', 'stopped_at'}
BUSINESS_STATES = {'SOURCE_OBSERVED', 'TOMBSTONED_VISIBILITY', 'INDEX_VERIFIED', 'QA_VERIFIED',
                   'QA_BLOCKED', 'DELIVERY_OBSERVED', 'SUPERSEDED', 'WAITING_RETRY', 'BLOCKED_DLQ',
                   'DRIFT_OBSERVED', 'CONSISTENT', 'DRIFT_DETECTED', 'REPAIR_QUEUED',
                   'PLANNING_ACCEPTED', 'PLAN_NATIVE_UNITS_VERIFIED', 'COMMAND_RESULT_VERIFIED'}


def _time(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= time.time() + 30


def _identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', value) is not None


def _execution(value):
    if value is None:
        return None
    if (not isinstance(value, dict) or set(value) != EXECUTION_KEYS
            or not isinstance(value['id'], str) or not re.fullmatch(r'[0-9]{1,20}', value['id'])
            or value['status'] not in {'success', 'error', 'running', 'new', 'waiting', 'canceled', 'crashed'}
            or value['mode'] not in {'webhook', 'trigger', 'manual', 'retry', 'error', 'integrated'}
            or not _time(value['started_at']) or value['stopped_at'] is not None and not _time(value['stopped_at'])):
        raise ValueError('WORKFLOW_METADATA_INVALID')
    return dict(value)


def _metadata(store):
    try:
        path = store.root / SNAPSHOT_FILE
        if path.is_symlink() or path.stat().st_size > MAX_BYTES:
            raise ValueError('WORKFLOW_METADATA_INVALID')
        document = json.loads(path.read_bytes())
        if (set(document) != {'schema_version', 'checked_at', 'workflows'} or document['schema_version'] != 1
                or not _time(document['checked_at']) or not isinstance(document['workflows'], list)
                or len(document['workflows']) != 16):
            raise ValueError('WORKFLOW_METADATA_INVALID')
        expected = {row[0]: row[1] for row in CATALOG}
        rows = {}
        for raw in document['workflows']:
            if (set(raw) - {'last_failure'} != {'code', 'id', 'name', 'active', 'published_version_id', 'definition_sha256',
                                             'trigger_types', 'last_execution', 'last_success'}
                    or raw['code'] in rows or expected.get(raw['code']) != raw['id']
                    or not isinstance(raw['name'], str) or not 1 <= len(raw['name']) <= 160
                    or any(ord(c) < 32 for c in raw['name']) or type(raw['active']) is not bool
                    or raw['published_version_id'] is not None and not _identifier(raw['published_version_id'])
                    or not isinstance(raw['definition_sha256'], str) or not re.fullmatch('[a-f0-9]{64}', raw['definition_sha256'])
                    or not isinstance(raw['trigger_types'], list) or not set(raw['trigger_types']) <= {'webhook', 'schedule', 'lifecycle', 'manual'}):
                raise ValueError('WORKFLOW_METADATA_INVALID')
            latest, success, failure = _execution(raw['last_execution']), _execution(raw['last_success']), _execution(raw.get('last_failure'))
            if success and success['status'] != 'success' or failure and failure['status'] not in {'error', 'canceled', 'crashed'}:
                raise ValueError('WORKFLOW_METADATA_INVALID')
            rows[raw['code']] = {**raw, 'last_execution': latest, 'last_success': success, 'last_failure': failure}
        state = 'FRESH' if time.time() - document['checked_at'] <= MAX_AGE else 'STALE'
        return state, document['checked_at'], rows
    except FileNotFoundError:
        return 'NOT_OBSERVED', None, {}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return 'INVALID', None, {}


def _observations(store, actor, owner):
    observations = []
    with store.connect() as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if owner or actor == 20:
            if {'integration_event_outbox', 'integration_event_receipts'} <= tables:
                for row in db.execute('SELECT o.document,o.state,o.error,r.document AS receipt,r.execution_id,r.observed FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id ORDER BY o.rowid DESC LIMIT 500'):
                    event = json.loads(row['document'])
                    if event.get('project_id') != 6:
                        continue
                    command_id = (event.get('payload') or {}).get('command_id')
                    if command_id:
                        if 'workflow_command_sources' not in tables:
                            continue
                        source = db.execute('SELECT actor FROM workflow_command_sources WHERE id=?', (command_id,)).fetchone()
                        if not source or not owner and source['actor'] != actor:
                            continue
                    ack = json.loads(row['receipt']) if row['receipt'] else {}
                    if ack and (ack.get('event_id') != event.get('event_id') or ack.get('project_id') != 6
                                or ack.get('correlation_id') != event.get('correlation_id') or ack.get('workflow') != event.get('workflow')):
                        continue
                    observations.append((event.get('workflow'), dict(row), event, ack.get('business_result') or {}))
        if {'n8n_lifecycle_outbox', 'n8n_lifecycle_execution_metadata'} <= tables:
            for row in db.execute('SELECT o.document,o.state,o.error,m.execution_id,m.observed_at AS observed FROM n8n_lifecycle_outbox o LEFT JOIN n8n_lifecycle_execution_metadata m ON m.event_id=o.event_id WHERE (? OR o.actor=?) ORDER BY o.rowid DESC LIMIT 100', (owner, actor)):
                event = json.loads(row['document'])
                if event.get('project_id') == 6:
                    observations.append(('WF04', dict(row), event, {}))
    return observations


def snapshot(service, actor):
    from .engineering import authorized
    native, who = authorized(service, actor)
    metadata_state, checked_at, metadata = _metadata(service.store)
    observations = _observations(service.store, actor, who['role'] == 'AI_SYSTEM_OWNER')
    observations.sort(key=lambda item: item[2].get('timestamp', 0), reverse=True)
    visible = {}
    rows = []
    for code, identifier, name, purpose, trigger, tab in CATALOG:
        meta = metadata.get(code, {})
        execution = meta.get('last_execution')
        row = {'code': code, 'workflow_id': identifier, 'name': meta.get('name', name), 'purpose': purpose,
               'trigger': trigger, 'action_tab': tab, 'metadata_state': metadata_state, 'updated_at': checked_at,
               'active': meta.get('active'), 'published_version_id': meta.get('published_version_id'),
               'definition_sha256': meta.get('definition_sha256'), 'last_execution': execution,
               'last_successful_execution': meta.get('last_success'), 'last_failed_execution': meta.get('last_failure'), 'current_state': 'NOT_OBSERVED',
               'last_error': None, 'retry_eligibility': 'NOT_APPLICABLE', 'project_event': None,
               'business_side_effect': 'NOT_VERIFIED', 'workflow_url': 'http://localhost:5679/workflow/' + identifier,
               'execution_url': None, 'execution_scope': 'GLOBAL_WORKFLOW_METADATA; not Project6 business acceptance'}
        if meta.get('last_failure'):
            row['last_error'] = 'N8N_EXECUTION_' + meta['last_failure']['status'].upper() + ' #' + meta['last_failure']['id']
        if execution:
            row['execution_url'] = row['workflow_url'] + '/executions/' + execution['id']
            if metadata_state == 'FRESH':
                row['current_state'] = {'success': 'WORKFLOW_SUCCEEDED', 'error': 'FAILED', 'canceled': 'FAILED',
                                        'crashed': 'FAILED', 'new': 'WORKFLOW_TRIGGERED', 'running': 'WORKFLOW_EXECUTING',
                                        'waiting': 'WORKFLOW_EXECUTING'}[execution['status']]
                if row['current_state'] == 'FAILED':
                    row['last_error'] = 'N8N_EXECUTION_' + execution['status'].upper()
        candidate = next((item for item in observations if item[0] == code), None)
        if candidate:
            _, observed, event, business = candidate
            payload = event.get('payload') or event
            native_id = payload.get('native_id') or payload.get('work_package_id')
            if type(native_id) is int:
                if native_id not in visible:
                    try:
                        visible[native_id] = native.package(native_id)
                    except Exception:
                        visible[native_id] = None
                package = visible[native_id]
                if not package:
                    row['business_side_effect'] = 'SOURCE_NOT_VISIBLE; no retry permitted here'
                    rows.append(row)
                    continue
            else:
                package = None
            execution_id = observed.get('execution_id')
            if not isinstance(execution_id, str) or not re.fullmatch('[0-9]{1,20}', execution_id):
                execution_id = None
            state = business.get('state') if business.get('state') in BUSINESS_STATES else None
            row['project_event'] = {'project_id': 6, 'state': observed['state'], 'business_state': state,
                'event_id': event.get('event_id') if _identifier(event.get('event_id')) else None,
                'correlation_id': event.get('correlation_id') if _identifier(event.get('correlation_id')) else None,
                'run_id': payload.get('run_id') if _identifier(payload.get('run_id')) else None,
                'native_id': native_id, 'pr_number': payload.get('pr_number') if type(payload.get('pr_number')) is int else None,
                'execution_id': execution_id, 'execution_url': row['workflow_url'] + '/executions/' + execution_id if execution_id else None,
                'updated_at': observed.get('observed') or event.get('timestamp')}
            row['retry_eligibility'] = ('AUTOMATIC_BOUNDED_OUTBOX' if observed['state'] == 'RETRY' else
                                        'BLOCKED_REQUIRES_SOURCE_REVIEW' if observed['state'] == 'DEAD' else 'NOT_APPLICABLE')
            same_execution = execution and execution_id == execution['id'] and metadata_state == 'FRESH'
            if not same_execution and not execution:
                row['current_state'] = 'WORKFLOW_TRIGGERED' if execution_id else 'FAILED' if observed['state'] == 'DEAD' else 'COMMAND_ACCEPTED'
            if observed.get('error'):
                row['project_event']['last_error'] = 'DURABLE_OUTBOX_DELIVERY_FAILED'
            # A callback alone is not a successful n8n execution or completed business effect.
            if same_execution and execution['status'] == 'success' and observed['state'] == 'ACKED':
                row['business_side_effect'] = state or 'LIFECYCLE_OBSERVED'
                if state in {'INDEX_VERIFIED', 'QA_VERIFIED', 'PLAN_NATIVE_UNITS_VERIFIED', 'COMMAND_RESULT_VERIFIED'}:
                    if package and business.get('source_version') is not None and package.get('lockVersion') != business['source_version']:
                        row['business_side_effect'] = 'STALE_SOURCE_VERSION'
                    else:
                        row['current_state'] = 'BUSINESS_SIDE_EFFECT_VERIFIED'
            elif row['project_event']['business_state']:
                row['business_side_effect'] = 'RECEIPT_OBSERVED; execution completion not matched'
        if meta and not meta.get('trigger_types'):
            row['current_state'] = 'NOT_APPLICABLE'
        rows.append(row)
    return rows

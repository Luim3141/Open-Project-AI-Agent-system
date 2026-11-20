"""Deterministic multi-actor native snapshots (1 to MAX_ACTIVE_USERS, up to 20). Machine scheduling is never human write consent."""
from datetime import datetime
import time
from zoneinfo import ZoneInfo

from .native import NativeError
from .permissions import require, AI_SYSTEM_OWNER
from .store import canonical, digest


def day(at=None):
    return datetime.fromtimestamp(time.time() if at is None else at, ZoneInfo('Asia/Bangkok')).date().isoformat()


def projection(summary):
    return {'count': summary['count'], 'by_status': summary['by_status'], 'overdue_ids': sorted(summary['overdue_ids'])}


def fingerprint(actor, role, project, snapshot):
    return digest(canonical({'actor': actor, 'role': role, 'project': project, 'snapshot': snapshot}))


def visible(store, actor, role, project, summary):
    report = store.daily_brief(actor, project, day())
    if report is None:
        return {'state': 'MISSING', 'model_used': False}
    metadata = {key: report[key] for key in ('day', 'run_id', 'trace_id', 'observed_at')}
    metadata['model_used'] = False
    if report['state'] != 'READY':
        return {**metadata, 'state': report['state']}
    if report['fingerprint'] != fingerprint(actor, role, project, projection(summary)):
        return {**metadata, 'state': 'STALE'}
    return {**metadata, 'state': 'READY', 'snapshot': report['snapshot']}


def collect(service, command):
    from .automation_targets import select,finish
    targets,scoped_command,selection=select(service,command)
    roles = {'BA' if role == 'BA-PM' else role for _,role in targets}
    max_active_users = int(service.config.get('max_active_users', 20))
    valid_roles = {'PM', 'BA', 'FE', 'BE', 'QA'}
    if (not (1 <= len(targets) <= max_active_users)
            or len({actor for actor,_ in targets}) != len(targets)
            or not roles.issubset(valid_roles)
            or any(actor <= 0 for actor,_ in targets)):
        raise PermissionError('INVALID_ROLE_OR_USER_CAPACITY_CONFIGURATION')
    report_day = day(command['issued_at'])
    if command['request_key'] != 'daily:' + report_day:
        raise ValueError('DAILY_DATE_IDEMPOTENCY_REQUIRED')
    receipt, created = service.store.begin_automation(scoped_command, project=service.config['project_id'], targets=len(targets))
    if not created:
        return receipt
    deadline = time.monotonic() + 25
    reports = []
    try:
        for actor, role in sorted(targets):
            report = {'actor': actor, 'project': service.config['project_id'], 'day': report_day,
                      'run_id': receipt['run_id'], 'trace_id': receipt['trace_id'], 'observed_at': time.time(),
                      'role': role, 'model_used': False}
            try:
                native, who = service.native_actor(actor, deadline=deadline)
                require(who['role'], 'analyze')
                summary = native.summary(actor)
                snapshot = projection(summary)
                report.update(state='READY', snapshot=snapshot, observed_at=time.time(),
                              fingerprint=fingerprint(actor, role, service.config['project_id'], snapshot))
            except PermissionError:
                report['state'] = 'DENIED'
            except NativeError as error:
                report['state'] = 'DENIED' if error.status in {401, 403} else 'OFFLINE'
            except (OSError, KeyError):
                report['state'] = 'OFFLINE'
            reports.append(report)
        return finish(service.store,service.store.finish_daily_brief(receipt['run_id'], reports),selection)
    except Exception:
        service.store.fail_daily_brief(receipt['run_id'])
        raise

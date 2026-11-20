"""Durable operator receipts and read-only scheduler/worker observations."""
import json
import time
import uuid

from .store import canonical


def setup(db):
    db.execute('CREATE TABLE IF NOT EXISTS engineering_owner_revision(project INTEGER PRIMARY KEY,revision INTEGER NOT NULL)')
    db.execute('INSERT OR IGNORE INTO engineering_owner_revision VALUES(6,0)')
    db.execute('CREATE TRIGGER IF NOT EXISTS engineering_owner_revision_update AFTER UPDATE ON engineering_control '
               'BEGIN UPDATE engineering_owner_revision SET revision=revision+1 WHERE project=NEW.project; END')
    db.execute('CREATE TABLE IF NOT EXISTS engineering_owner_commands(sequence INTEGER PRIMARY KEY AUTOINCREMENT,'
               'command_id TEXT UNIQUE NOT NULL,actor INTEGER NOT NULL,document TEXT NOT NULL)')


def observe(service, backlog=None):
    now = time.time()
    with service.store.connect() as db:
        db.execute('BEGIN')
        mode = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        revision = db.execute('SELECT revision FROM engineering_owner_revision WHERE project=6').fetchone()[0]
        recent = [json.loads(row[0]) for row in db.execute('SELECT document FROM engineering_owner_commands ORDER BY sequence DESC LIMIT 10')]
        worker = db.execute('SELECT worker_id,seen,run_id FROM engineering_worker_state WHERE project=6').fetchone()
        active = db.execute("SELECT id,state,payload FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw' "
                            "AND json_extract(payload,'$.project_id')=6 AND state!='finished' ORDER BY created LIMIT 1").fetchone()
    worker = dict(worker) if worker else {}
    age = max(0, now-worker['seen']) if worker else None
    worker.update(state=('ALIVE' if age < 30 else 'STALE' if age < 120 else 'DEAD') if age is not None else 'DEAD',
                  heartbeat_age_seconds=age)
    eligible = [unit for unit in backlog or [] if unit.get('eligible') is True]
    blocked = [unit for unit in backlog or [] if unit.get('blocked_reason')]
    queue = {'state': 'RUNNING' if active and active['state']=='executing' else 'READY' if active or eligible else 'BLOCKED' if blocked else 'EMPTY',
             'ready': len(eligible), 'active': int(bool(active)), 'blocked': len(blocked),
             'eligible_unit': eligible[0]['unit'] if eligible else None,
             'reason_code': None if active or eligible else 'NO_ELIGIBLE_WORK'}
    executing = active and active['state']=='executing'
    cancelled = active and json.loads(active['payload']).get('cancel_requested') is True
    if cancelled:
        effective = 'CANCEL_REQUESTED'
    elif executing and mode=='PAUSED':
        effective = 'PAUSE_REQUESTED'
    elif executing and mode=='OFF':
        effective = 'STOP_AFTER_CURRENT'
    elif active and worker['state']!='ALIVE':
        effective = 'WORKER_STALE'
    elif executing:
        effective = 'RUNNING'
    elif mode=='PAUSED':
        effective = 'PAUSED'
    elif mode=='OFF':
        effective = 'OFF'
    elif active:
        effective = 'READY'
    else:
        effective = 'AUTO_IDLE' if mode=='AUTO' else 'OFF'
    control = {'desired_mode': mode if mode in {'OFF','AUTO','PAUSED'} else 'OFF',
               'effective_state': effective, 'state_revision': revision,
               'last_command': recent[0] if recent else None,'recent_commands':recent,
               'active_run_id': active['id'] if active else None, 'server_timestamp': now,
               'blocked_reason': 'WORKER_NOT_ALIVE' if active and worker['state']!='ALIVE' else queue['reason_code']}
    return control, queue, worker


def command_result(service, actor, action, result, accepted=True, reason=None, request_id=None):
    """Persist the operator outcome; this receipt never authorizes an operation."""
    control, _, _ = observe(service)
    receipt = {'command_id': str(uuid.uuid4()), 'requested_action': action,
               'request_id': request_id,
               'accepted': accepted, 'reason_code': reason or ('COMMAND_ACCEPTED' if accepted else 'COMMAND_REJECTED'),
               'current_state': control['effective_state'], 'desired_state': control['desired_mode'],
               'state_revision': control['state_revision'], 'server_timestamp': time.time(),
               'affected_run_id': result.get('id') or control['active_run_id']}
    if result.get('operation_id'):
        receipt.update(operation_id=result['operation_id'],operation_state=result.get('operation_state'))
    with service.store.connect() as db:
        db.execute('INSERT INTO engineering_owner_commands(command_id,actor,document) VALUES(?,?,?)',
                   (receipt['command_id'], actor, canonical(receipt)))
    return {**result, **receipt}


def attempt(service, actor, action, operation, request_id=None,context=None):
    """Preserve existing HTTP errors while making rejected authenticated commands discoverable."""
    try:
        return operation()
    except ValueError as error:
        from .engineering import setup
        from .engineering_telemetry import code
        setup(service.store)
        command_result(service,actor,action,{},False,code(str(error).split(';')[0]) or 'COMMAND_REJECTED',request_id)
        if action in {'PLAN','RUN_ONCE','RESUME'}:
            from .engineering_observability import notification
            reason='RESUME_FAILED' if action=='RESUME' else 'WORK_INTAKE_REJECTED'
            context=dict(context or {})
            if context.get('run_id') and not context.get('native_id'):
                with service.store.connect() as db:
                    row=db.execute("SELECT payload FROM ai_queue WHERE id=? AND json_extract(payload,'$.project_id')=6",(context['run_id'],)).fetchone()
                if row:context['native_id']=json.loads(row['payload']).get('native_id')
            notification(service,(request_id or str(uuid.uuid4()))+':'+reason,reason,
                message=code(str(error).split(';')[0]) or 'COMMAND_REJECTED',level='ERROR',
                run_id=context.get('run_id'),native_id=context.get('native_id'))
        raise

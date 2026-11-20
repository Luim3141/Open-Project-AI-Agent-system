"""Controlled Auto Mode and Admission Scheduler for QLDAPM Engineering.

Guarantees:
1. Opt-in only: Must be explicitly enabled by PM or AI_SYSTEM_OWNER.
2. Concurrency Lock: Exactly one active unit (queued or executing) at any time.
3. Dependency Order: Only units whose dependencies are DELIVERED are admitted.
4. Quota Safety: Verifies Gemini provider availability before admission.
5. Idle AUTO remains enabled; provider failures and failed runs shut scheduling off safely.
"""
import json
import time
from .store import canonical, digest

PROJECT = 6


def schedule_next_auto_unit(service, actor):
    """Evaluates the engineering backlog and admits the next eligible unit in AUTO mode."""
    from . import engineering
    from .engineering import authorized, setup
    native, who = authorized(service, actor)
    setup(service.store)

    with service.store.connect() as db:
        mode_row = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()
        current_mode = mode_row[0] if mode_row else 'OFF'
        if current_mode != 'AUTO':
            return {'scheduled': False, 'reason': 'MODE_NOT_AUTO', 'mode': current_mode}

        # Concurrency lock: strictly 1 active run across all openclaw engineering
        active = db.execute("SELECT id, state FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw' AND state!='finished'").fetchone()
        if active:
            return {'scheduled': False, 'reason': 'CONCURRENCY_LOCKED', 'active_run': active['id'], 'state': active['state']}

    from .engineering_observability import policy,describe_run
    rules=policy(service)
    if rules['auto_continue']:
        with service.store.connect() as db:
            recent=db.execute("SELECT q.id,q.created,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw' AND q.state='finished' ORDER BY q.created DESC LIMIT 1").fetchone()
        if recent:
            payload=json.loads(recent['payload']);result=json.loads(recent['result'] or '{}')
            from .engineering_lifecycle import load,resume
            checkpoint=load(service.store,recent['id']) or {}
            description=describe_run(service,{'id':recent['id'],'native_id':payload['native_id'],'unit':payload['unit'],
                'created_at':recent['created'],'queue_state':'finished','result':result,'checkpoint':checkpoint})
            recoverable=(description['failure']['category'] in {'DEV_BUDGET_EXHAUSTED','PROVIDER_QUOTA_EXHAUSTED'}
                and result.get('status') in {'blocked','failed'} and not payload.get('cancel_requested'))
            if recoverable:
                if description['resume']['eligible']:
                    try:
                        resumed=resume(service,actor,recent['id'],checkpoint.get('version'),preserve_auto=True)
                        return {'scheduled':True,'continuation':True,'run_id':recent['id'],**resumed}
                    except ValueError as error:
                        return {'scheduled':False,'reason':str(error).split(';')[0],'mode':'AUTO'}
                waiting=description['resume']['reason'] in {'COOLDOWN','PROVIDER_RECOVERY_REQUIRED'}
                if not waiting:
                    with service.store.connect() as db:db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode='AUTO'",(time.time(),))
                    from .engineering_observability import notification
                    notification(service,recent['id']+':auto-stop:'+description['resume']['reason'],'AUTO_CONTINUATION_STOPPED',
                        native_id=payload['native_id'],run_id=recent['id'],message=description['resume']['reason'],level='ERROR')
                return {'scheduled':False,'reason':'WAITING_FOR_QUOTA' if description['failure']['category']=='PROVIDER_QUOTA_EXHAUSTED' and description['resume']['reason'] in {'COOLDOWN','PROVIDER_RECOVERY_REQUIRED'} else description['resume']['reason'],
                    'resume_reason':description['resume']['reason'],'retry_at':description['resume'].get('cooldown_until'),'mode':'AUTO' if waiting else 'OFF'}

    # Quota and Provider Policy Check
    try:
        policy = service.gemini.settings()
        if not policy or policy.get('state') == 'UNAVAILABLE':
            with service.store.connect() as db:
                db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode='AUTO'", (time.time(),))
            service.store.record(actor, 'engineering_auto_shutoff', str(PROJECT), 'QUOTA_UNAVAILABLE')
            return {'scheduled': False, 'reason': 'QUOTA_UNAVAILABLE', 'mode': 'OFF'}
    except Exception as exc:
        with service.store.connect() as db:
            db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode='AUTO'", (time.time(),))
        service.store.record(actor, 'engineering_auto_shutoff', str(PROJECT), 'QUOTA_CHECK_FAILED')
        return {'scheduled': False, 'reason': 'QUOTA_CHECK_FAILED', 'mode': 'OFF'}

    # Fresh backlog evaluation
    backlog, _ = engineering.backlog_snapshot(service, actor)
    if not backlog:
        return {'scheduled': False, 'reason': 'NO_ELIGIBLE_WORK', 'mode': 'AUTO'}

    # Find next eligible unit: PLANNED with dependency_ready True
    eligible = [u for u in backlog if u.get('eligible') is True]
    if eligible:
        target = eligible[0]
        try:
            item = native.package(target['native_id'])
            lock_version = item['lockVersion']
        except Exception as exc:
            with service.store.connect() as db:
                db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode='AUTO'", (time.time(),))
            service.store.record(actor, 'engineering_auto_shutoff', str(PROJECT), 'SOURCE_FETCH_FAILED')
            return {'scheduled': False, 'reason': 'SOURCE_FETCH_FAILED', 'mode': 'OFF'}

        req_key = f"auto-{target['unit']}-{int(time.time())}"
        try:
            admitted = engineering.admit(service, actor, {
                'native_id': target['native_id'],
                'lock_version': lock_version,
                'unit': target['unit']
            }, req_key, expected_mode='AUTO')
        except ValueError as exc:
            if str(exc) not in {'ENGINEERING_MODE_CHANGED','ENGINEERING_UNIT_ALREADY_ACTIVE'} and not str(exc).startswith('ENGINEERING_UNIT_ALREADY_ACTIVE;'):
                raise
            return {'scheduled': False, 'reason': str(exc).split(';')[0]}

        service.store.record(actor, 'engineering_auto_scheduled', target['unit'], admitted['id'])
        return {'scheduled': True, 'unit': target['unit'], 'run_id': admitted['id'], 'mode': 'AUTO'}

    # If no unit is eligible: check if all are completed/delivered
    all_delivered = all(u.get('state') in {'succeeded', 'DELIVERED'} for u in backlog)
    delivered_count = sum(1 for u in backlog if u.get('state') in {'succeeded', 'DELIVERED'})
    total_count = len(backlog)
    reason = 'ALL_DELIVERED' if all_delivered else 'NO_ELIGIBLE_WORK'
    service.store.record(actor, 'engineering_auto_complete', str(PROJECT), reason)
    explanation = f'Không có unit đủ điều kiện ({delivered_count}/{total_count} units hoàn tất). AUTO vẫn bật và đang chờ công việc.'
    return {'scheduled': False, 'reason': reason, 'mode': 'AUTO', 'explanation': explanation}

"""Owner summaries from scoped durable evidence; never infer task completion from HTTP success."""
import json
import re
import time
import uuid
from contextlib import nullcontext

from .store import canonical


def policy(service):
    configured = getattr(service, 'config', {}).get('engineering', {}).get('continuation', {})
    values = {'attempt_calls': 12, 'task_calls': 72, 'max_continuations': 5, 'cooldown_seconds': 60, 'auto_continue': False}
    if not isinstance(configured, dict) or set(configured) - set(values):
        raise ValueError('ENGINEERING_CONTINUATION_POLICY_INVALID')
    values.update(configured)
    for key, minimum, maximum in [('attempt_calls',1,12),('task_calls',1,120),('max_continuations',0,5),('cooldown_seconds',0,86400)]:
        if type(values[key]) is not int or not minimum <= values[key] <= maximum:
            raise ValueError('ENGINEERING_CONTINUATION_POLICY_INVALID')
    if type(values['auto_continue']) is not bool:
        raise ValueError('ENGINEERING_CONTINUATION_POLICY_INVALID')
    return values


def describe_runs(service,runs,*,provider_readiness=None):
    if not runs:return []
    if len(runs)>100:raise ValueError('ENGINEERING_SUMMARY_LIMIT')
    ids=[r['id'] for r in runs];marks=','.join('?' for _ in ids)
    evidence={i:{'payload':{},'receipts':[],'events':[],'unsafe':False} for i in ids}
    with service.store.connect() as db:
        db.execute('BEGIN')
        for r in db.execute('SELECT id,payload FROM ai_queue WHERE id IN ('+marks+')',ids):evidence[r['id']]['payload']=json.loads(r['payload'])
        for r in db.execute('SELECT c.run_id,c.document FROM gemini_call_receipts c JOIN ai_queue q ON q.id=c.run_id AND q.actor=c.actor WHERE c.run_id IN ('+marks+') ORDER BY c.rowid',ids):evidence[r['run_id']]['receipts'].append(json.loads(r['document']))
        for r in db.execute('SELECT e.run_id,e.document FROM execution_events e JOIN ai_queue q ON q.id=e.run_id AND q.actor=e.actor WHERE e.project=6 AND e.run_id IN ('+marks+') ORDER BY e.sequence',ids):evidence[r['run_id']]['events'].append(json.loads(r['document']))
        for r in db.execute("SELECT DISTINCT q.id FROM requests r JOIN ai_queue q ON q.actor=r.actor AND r.key LIKE 'engineering-'||q.id||'-%' WHERE r.state NOT IN ('done','rejected') AND q.id IN ("+marks+')',ids):evidence[r['id']]['unsafe']=True
    return [describe_run(service,r,provider_readiness=provider_readiness,evidence=evidence[r['id']]) for r in runs]


def describe_run(service, run, *, provider_readiness=None, connection=None, evidence=None):
    rules = policy(service)
    if evidence is None:
        with nullcontext(connection) if connection is not None else service.store.connect() as db:
            row = db.execute('SELECT payload,actor FROM ai_queue WHERE id=?',(run['id'],)).fetchone()
            payload = json.loads(row['payload']) if row else {}
            actor = row['actor'] if row else 20
            receipts = [json.loads(r[0]) for r in db.execute('SELECT c.document FROM gemini_call_receipts c JOIN ai_queue q ON q.id=c.run_id AND q.actor=c.actor WHERE c.run_id=? ORDER BY c.rowid',(run['id'],))]
            events = [json.loads(r[0]) for r in db.execute('SELECT document FROM execution_events WHERE run_id=? AND actor=? AND project=6 ORDER BY sequence',(run['id'],actor))]
            unsafe = bool(db.execute("SELECT 1 FROM requests WHERE actor=? AND key LIKE ? AND state NOT IN ('done','rejected')",(actor,'engineering-'+run['id']+'-%')).fetchone())
    else:payload,receipts,events,unsafe=(evidence[k] for k in ['payload','receipts','events','unsafe'])
    result = run.get('result') or {}
    checkpoint = run.get('checkpoint') or {}
    generations = [r for r in receipts if r.get('phase')=='generateContent']
    latest = max(generations,key=lambda r:r.get('at') or 0) if generations else {}
    session = latest.get('session_id')
    current = [r for r in generations if session and r.get('session_id')==session]
    own_role_events = [e for e in events if e.get('agent_id') and e.get('event_type') in {'AGENT_STARTED','AGENT_COMPLETED','AGENT_FAILED','REVIEW_STARTED','REVIEW_COMPLETED'}]
    last_role_event = own_role_events[-1] if own_role_events else {}
    role = result.get('agent') or latest.get('agent') or last_role_event.get('agent_id') or next((role for prefix,role in [('dev-','dev'),('rework-','dev'),('review-','reviewer'),('qa-','qa')] if str(checkpoint.get('stage','')).startswith(prefix)),None)
    cap = latest.get('call_cap') or payload.get('budget',{}).get('attempt_calls',12)
    successes = sum(r.get('http_status')==200 for r in current)
    error = result.get('error') or checkpoint.get('error')
    category = None
    if result.get('status') in {'blocked','failed','paused','cancelled'}:
        if latest.get('http_status')==429: category = 'PROVIDER_QUOTA_EXHAUSTED'
        elif latest.get('http_status') in {401,403}: category = 'PROVIDER_AUTH_FAILED'
        elif latest.get('http_status') in {0,408,504} or 'TIMEOUT' in str(error): category = 'PROVIDER_TIMEOUT'
        elif error=='OPENCLAW_STEP_NOT_COMPLETED' and role=='dev' and len(current)>=cap and latest.get('http_status')==200: category = 'DEV_BUDGET_EXHAUSTED'
        elif unsafe or error=='OPENCLAW_OUTCOME_UNKNOWN': category = 'CHECKPOINT_UNSAFE'
        elif error and ('TOOL' in error or 'BOOTSTRAP' in error): category = 'OPENCLAW_TOOL_FAILURE'
        else: category = 'UNKNOWN_FAILURE'
    messages = {'DEV_BUDGET_EXHAUSTED':f'Hết ngân sách nội bộ {len(current)}/{cap} calls; Dev chưa hoàn tất.',
        'PROVIDER_QUOTA_EXHAUSTED':'Provider trả HTTP 429; chờ cooldown và readiness mới trước khi tiếp tục.',
        'PROVIDER_AUTH_FAILED':'Provider từ chối xác thực; cần sửa cấu hình trước khi tiếp tục.',
        'PROVIDER_TIMEOUT':'Provider/runtime timeout; cần đối soát kết quả trước khi retry.',
        'CHECKPOINT_UNSAFE':'Kết quả hoặc external write chưa rõ; phải reconcile trước khi resume.',
        'OPENCLAW_TOOL_FAILURE':'OpenClaw tool thất bại; xem bằng chứng kỹ thuật.',
        'UNKNOWN_FAILURE':'Lượt thực thi chưa hoàn tất; chưa đủ bằng chứng phân loại nguyên nhân.'}
    updated = max([run.get('created_at') or 0]+[e.get('timestamp') or 0 for e in events]+[r.get('completed_at') or r.get('at') or 0 for r in receipts])
    continuations = payload.get('recovery_count',0)
    remaining = max(0,rules['max_continuations']-continuations)
    cooldown = updated+rules['cooldown_seconds']
    provider_recovery={'verified':False,'reason':'NO_NEW_VERIFIED_PROVIDER_READINESS','checked_at':None}
    if category in {'PROVIDER_QUOTA_EXHAUSTED','PROVIDER_AUTH_FAILED','PROVIDER_TIMEOUT'}:
        try:
            readiness=provider_readiness if provider_readiness is not None else service.gemini.readiness(service.gemini.settings())
            checked=readiness.get('last_successful_check')
            verified=readiness.get('state')=='READY' and type(checked) in (int,float) and updated<checked<=time.time() and time.time()-checked<=300
            provider_recovery={'verified':verified,'reason':'NEW_VERIFIED_PROVIDER_READINESS' if verified else 'NO_NEW_VERIFIED_PROVIDER_READINESS','checked_at':checked}
        except Exception:
            pass
    reason = ('ALREADY_COMPLETED' if result.get('status')=='succeeded' else
        'WORKER_ACTIVE' if run.get('queue_state')=='executing' else
        'EXTERNAL_WRITE_RECONCILIATION_REQUIRED' if unsafe else
        'CHECKPOINT_NOT_SAFE' if not checkpoint.get('terminal_known') or not checkpoint.get('resumable') else
        'CONTINUATION_LIMIT_REACHED' if not remaining else
        'CUMULATIVE_BUDGET_EXHAUSTED' if len(generations)>=rules['task_calls'] else
        'PROVIDER_RECOVERY_REQUIRED' if category in {'PROVIDER_QUOTA_EXHAUSTED','PROVIDER_AUTH_FAILED','PROVIDER_TIMEOUT'} and not provider_recovery['verified'] else
        'COOLDOWN' if cooldown>time.time() else 'CHECKPOINT_READY')
    active = run.get('queue_state')=='executing'
    current_role = last_role_event.get('agent_id') if last_role_event.get('event_type') in {'AGENT_STARTED','REVIEW_STARTED'} else result.get('agent') if not last_role_event else None
    if not active: current_role = None
    task_state = ('ACTIVE' if active else 'READY' if run.get('queue_state')=='queued' else 'PLANNING_PUBLISHED' if payload.get('kind')=='planning' and result.get('status')=='succeeded' else 'COMPLETED' if result.get('status')=='succeeded' else 'BLOCKED')
    title = (payload.get('definition') or {}).get('title') or run.get('title') or run.get('unit')
    activities={}
    for agent in ['pm','ba','dev','reviewer','qa']:
        agent_receipts=[r for r in receipts if r.get('agent')==agent]
        agent_events=[e for e in events if e.get('agent_id')==agent]
        if not agent_receipts and not agent_events:continue
        starts=[e['timestamp'] for e in agent_events if e.get('event_type') in {'AGENT_STARTED','REVIEW_STARTED'}]
        ends=[e['timestamp'] for e in agent_events if e.get('event_type') in {'AGENT_COMPLETED','AGENT_FAILED','REVIEW_COMPLETED'}]
        prefixes={'dev':('dev-','rework-'),'reviewer':('review-',),'qa':('qa-',)}.get(agent,())
        successful_ends=[e['timestamp'] for e in agent_events if e.get('event_type') in {'AGENT_COMPLETED','REVIEW_COMPLETED'}]
        done=bool(successful_ends and (not starts or max(successful_ends)>=max(starts))) or any(str(step).startswith(prefixes) for step in checkpoint.get('completed_steps',[]))
        own_updated=max([e.get('timestamp') or 0 for e in agent_events]+[r.get('completed_at') or r.get('at') or 0 for r in agent_receipts])
        failed_current=role==agent and result.get('status') in {'blocked','failed','paused','cancelled'}
        own_result='running' if current_role==agent else result['status'] if failed_current else 'succeeded' if done else 'UNKNOWN'
        own_latest=max(agent_receipts,key=lambda r:r.get('at') or 0) if agent_receipts else {}
        own_calls=[r for r in agent_receipts if r.get('phase')=='generateContent' and r.get('session_id')==own_latest.get('session_id')]
        own_cap=own_latest.get('call_cap') or payload.get('budget',{}).get('attempt_calls',12)
        own_budget={'calls_used':len(own_calls),'call_cap':own_cap,'provider_response_count':sum(r.get('http_status')==200 for r in own_calls),
            'remaining':max(0,own_cap-len(own_calls)),'cumulative_calls':sum(r.get('phase')=='generateContent' for r in agent_receipts),
            'total_tokens_reported':sum((r.get('usage') or {}).get('totalTokenCount',0) for r in own_calls),'usage_source':'PROVIDER_RECEIPTS',
            'max_continuations':rules['max_continuations'],'continuations_used':continuations}
        activities[agent]={'budget':own_budget,'native_id':run['native_id'],'title':title,'run_id':run['id'],'stage':(agent_receipts[-1].get('step') if agent_receipts else None) or agent,
            'started_at':max(starts) if starts else min((r.get('at') or 0 for r in agent_receipts),default=None),
            'ended_at':max(ends) if ends else own_updated if run.get('queue_state')=='finished' else None,
            'result':own_result,'error':messages.get(category) if role==agent else None,
            'last_verified_evidence':own_updated,'receipt_id':agent_receipts[-1].get('id') if agent_receipts else None}

    return {'id':run['id'],'native_id':run['native_id'],'title':title,'project':6,'task_status':task_state,
        'created_at':run.get('created_at'),'updated_at':updated,'last_event':events[-1] if events else None,
        'last_agent':role,'agent':current_role or role,'current_agent':current_role,'agent_activities':activities,
        'stage':result.get('stage') or checkpoint.get('stage') or ('PLANNING' if payload.get('kind')=='planning' else None),
        'started_at':next((e.get('timestamp') for e in reversed(events) if e.get('event_type') in {'AGENT_STARTED','REVIEW_STARTED'}),None),
        'ended_at':updated if not active and run.get('queue_state')=='finished' else None,
        'failure':{'category':category,'message':messages.get(category),'raw_code':error if isinstance(error,str) and re.fullmatch('[A-Z][A-Z0-9_]{0,79}',error) else None,'evidence_source':'SCOPED_PERSISTED_RECEIPTS_AND_CHECKPOINT'},
        'budget':{'calls_used':len(current),'call_cap':cap,'provider_response_count':successes,'remaining':max(0,cap-len(current)),
            'cumulative_calls':len(generations),'task_call_cap':rules['task_calls'],'total_tokens_reported':sum((r.get('usage') or {}).get('totalTokenCount',0) for r in current),
            'usage_source':'PROVIDER_RECEIPTS','usage_missing':sum(type((r.get('usage') or {}).get('totalTokenCount')) is not int for r in current),
            'max_continuations':rules['max_continuations'],'continuations_used':continuations,'session_id':session},
        'resume':{'eligible':reason=='CHECKPOINT_READY','reason':reason,'checkpoint_version':checkpoint.get('version'),
            'completed_steps':checkpoint.get('completed_steps',[]),'remaining_continuations':remaining,'action':'RESUME_SAME_RUN','same_run_id':True,
            'cooldown_until':cooldown,'checkpoint_saved_at':None,'source_readback':'RECHECKED_AT_COMMAND',
            'provider_recovery':provider_recovery,
            'auto_enabled':rules['auto_continue'],'policy':rules},
        'checkpoint':checkpoint,'pr_url':result.get('pr_url'),'queue_state':run.get('queue_state'),'result':result.get('status'),
        'blocked_reason':category or error,'native_url':'/work_packages/'+str(run['native_id'])}


def enrich_profiles(profiles, descriptions):
    for profile in profiles:
        role = profile['agent']
        current = next((d for d in descriptions if d.get('current_agent')==role and d['queue_state']=='executing'),None)
        candidates=[d for d in descriptions if role in d.get('agent_activities',{})]
        previous=max(candidates,key=lambda d:d['agent_activities'][role]['last_verified_evidence']) if candidates else None
        profile.update(current_state='RUNNING' if current else 'STANDBY',status='RUNNING' if current else 'STANDBY',
                       current_run={'id':current['id'],'native_id':current['native_id'],'title':current['title'],'stage':current['stage']} if current else None)
        if previous:
            profile['last_activity'] = {**previous['agent_activities'][role],
                'failure':previous['failure'] if previous.get('last_agent')==role else {'category':None,'message':None},
                'checkpoint':previous['checkpoint'],'resume':previous['resume']}
        profile['runtime_verification'] = 'HISTORICAL_RECEIPT; current session chưa được xác minh' if profile.get('evidence','').startswith('Receipt:') else 'CONFIGURED_ONLY; chưa có receipt cho runtime'
    return profiles


def notification(service, key, reason, *, native_id=None, run_id=None, title=None, message=None, level='INFO', created=None, extra=None, connection=None):
    identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,'qldapm-notification:'+key))
    metadata={'native_id':native_id,'wp_title':title,'run_id':run_id,'reason_code':reason,'event_id':identifier,**(extra or {})}
    link='/projects/ai-dev-demo/qldapm-ai'+('?run_id='+run_id+'#run-'+run_id if run_id else '#mission')
    sql='INSERT OR IGNORE INTO engineering_notifications(id,project,actor,level,title,message,link,created,metadata) VALUES(?,6,NULL,?,?,?,?,?,?)'
    row=(identifier,level,('WP #'+str(native_id)+' — ' if native_id else '')+reason,message or reason,link,created or time.time(),canonical(metadata))
    if connection is not None:
        connection.execute(sql,row)
        return
    from .engineering_reporting import setup_reporting
    setup_reporting(service.store)
    with service.store.connect() as db:db.execute(sql,row)


def persist_notifications(service, descriptions):
    from .engineering_reporting import setup_reporting
    setup_reporting(service.store)
    with service.store.connect() as db:
        known={r[0] for r in db.execute('SELECT id FROM engineering_notifications WHERE project=6')}
        def emit(key,reason,**args):
            identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,'qldapm-notification:'+key))
            if identifier not in known:
                notification(service,key,reason,connection=db,**args)
                known.add(identifier)
        _persist_notifications(descriptions,emit)


def _persist_notifications(descriptions, emit):
    for item in descriptions:
        state=item['task_status']
        base=item['id']+':'+str(item['budget']['continuations_used'])
        reason=item['failure']['category'] or ('PLANNING_COMPLETE' if state=='PLANNING_PUBLISHED' else 'TASK_COMPLETED' if state=='COMPLETED' else 'AGENT_STARTED' if state=='ACTIVE' else 'WORK_INTAKE_ACCEPTED' if state=='READY' else None)
        args={'native_id':item['native_id'],'run_id':item['id'],'title':item['title'],'created':item['updated_at']}
        if reason:
            message=item['failure']['message'] or ('Kế hoạch đã published; chưa đồng nghĩa hoàn tất Dev.' if state=='PLANNING_PUBLISHED' else 'Agent bắt đầu thực thi.' if state=='ACTIVE' else 'Đã nhận yêu cầu; chờ thực thi.' if state=='READY' else 'Task hoàn tất với bằng chứng đã lưu.')
            emit(base+':'+reason,reason,**args,message=message,level='ERROR' if state=='BLOCKED' else 'INFO',extra={'resume_available':item['resume']['eligible']})
        for agent,activity in item.get('agent_activities',{}).items():
            if activity.get('started_at'):
                emit(base+':AGENT_STARTED:'+agent,'AGENT_STARTED',**{**args,'created':activity['started_at']},message=agent+' bắt đầu thực thi; xem run để biết kết quả hiện tại.')
        if item['resume']['eligible']:
            emit(base+':RESUME_AVAILABLE','RESUME_AVAILABLE',**args,message='Checkpoint có thể tiếp tục; Gateway sẽ kiểm tra lại source và external write khi nhận lệnh.')
        if item['pr_url']:
            emit(base+':PR_CREATED','GITHUB_PR_CREATED',**args,message='PR đã được ghi nhận; chưa đồng nghĩa merge/deploy.',extra={'pr_url':item['pr_url']})
        if state=='BLOCKED' and item['last_agent']=='qa':
            emit(base+':QA_FAILED','QA_FAILED',**args,message='QA chưa đạt; xem evidence đúng run.',level='ERROR')

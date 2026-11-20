"""Execution checkpoints in the existing Store; host artifacts remain authoritative."""
import json
import time

from .agent_models import AgentTask
from .store import canonical, digest


def setup(store):
    if getattr(store,'_engineering_lifecycle_ready',False):return
    with store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS engineering_checkpoints(run_id TEXT PRIMARY KEY,version INTEGER NOT NULL,document TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS engineering_plans(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,document TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS engineering_unit_definitions(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,native_id INTEGER NOT NULL,document TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS engineering_worker_state(project INTEGER PRIMARY KEY,worker_id TEXT NOT NULL,seen REAL NOT NULL,run_id TEXT)')
    store._engineering_lifecycle_ready=True


def heartbeat(store,worker_id,run_id=None):
    import uuid
    if str(uuid.UUID(worker_id))!=worker_id:raise ValueError('ENGINEERING_WORKER_ID_INVALID')
    if run_id is not None:
        with store.connect() as db:
            row=db.execute('SELECT state,payload FROM ai_queue WHERE id=? AND actor=20',(run_id,)).fetchone()
            if not row or row['state']!='executing' or json.loads(row['payload']).get('engine')!='openclaw':raise ValueError('ENGINEERING_RUN_NOT_CLAIMED')
    setup(store)
    with store.connect() as db:db.execute('INSERT INTO engineering_worker_state VALUES(6,?,?,?) ON CONFLICT(project) DO UPDATE SET worker_id=excluded.worker_id,seen=excluded.seen,run_id=excluded.run_id',(worker_id,time.time(),run_id))
    return {'recorded':True,'inference':False}


def load(store, run_id, *, connection=None):
    if connection is not None:
        row=connection.execute('SELECT version,document FROM engineering_checkpoints WHERE run_id=?',(run_id,)).fetchone()
        return {'version':row['version'],**json.loads(row['document'])} if row else None
    setup(store)
    with store.connect() as db:
        row=db.execute('SELECT version,document FROM engineering_checkpoints WHERE run_id=?',(run_id,)).fetchone()
    return {'version':row['version'],**json.loads(row['document'])} if row else None


def save(service,actor,run_id,document):
    from .engineering import authorized
    authorized(service,actor);run=service.store.agent_run(actor,6,run_id);setup(service.store)
    if (not isinstance(document,dict) or set(document)!={'stage','completed_steps','terminal_known','resumable','revision','session_id','error'}
            or len(canonical(document))>12000 or type(document['terminal_known']) is not bool or type(document['resumable']) is not bool):
        raise ValueError('ENGINEERING_CHECKPOINT_INVALID')
    with service.store.connect() as db:
        row=db.execute('SELECT state FROM ai_queue WHERE id=? AND actor=?',(run_id,actor)).fetchone()
        if not row or row['state']!='executing':raise ValueError('ENGINEERING_RUN_NOT_CLAIMED')
        previous=db.execute('SELECT document FROM engineering_checkpoints WHERE run_id=?',(run_id,)).fetchone()
        completed=set(json.loads(previous[0])['completed_steps']) if previous else set()
        db.execute('INSERT INTO engineering_checkpoints VALUES(?,1,?) ON CONFLICT(run_id) DO UPDATE SET version=version+1,document=excluded.document',(run_id,canonical(document)))
        from .execution_events import append
        for step in set(document['completed_steps'])-completed:
            agent=next((role for prefix,role in [('dev-','dev'),('rework-','dev'),('review-','reviewer'),('qa-','qa')] if step.startswith(prefix)),None)
            if agent:append(db,run,'AGENT_COMPLETED',agent=agent,status='COMPLETED',key='engineering-step-completed:'+step)
    return load(service.store,run_id)


def signal(store,actor,run_id):
    """OS worker polling, no Native/network calls and no change of authority."""
    with store.connect() as db:
        row=db.execute('SELECT state,payload FROM ai_queue WHERE id=? AND actor=?',(run_id,actor)).fetchone()
        mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()
    if not row or json.loads(row['payload']).get('engine')!='openclaw':raise PermissionError('ENGINEERING_RUN_REQUIRED')
    payload=json.loads(row['payload'])
    return {'mode':mode[0] if mode else 'OFF','queue_state':row['state'],
        'cancel_requested':payload.get('cancel_requested',False),'deadline':payload['deadline']}


def source_matches(store,actor,run_id,contract,item):
    if item['lockVersion']==contract['source_version'] and digest(item.get('description',{}).get('raw',''))==contract['spec_sha256']:return True
    if contract['native_id']==379:return False
    from .engineering_status_sync import owned_source_matches
    if digest(item.get('description',{}).get('raw',''))==contract['spec_sha256'] and owned_source_matches(store,run_id,contract['source_version'],item):return True
    key='engineering-'+run_id+'-child'
    with store.connect() as db:
        rows=db.execute("SELECT payload,result FROM requests WHERE actor=? AND state='done' AND (key=? OR key GLOB ?)",(actor,key,key+'-retry-*')).fetchall()
    for row in rows:
        request=json.loads(row['payload']);published=json.loads(row['result'])
        if (request.get('project_id')==6 and request.get('method')=='PATCH' and request.get('path')==f"/api/v3/work_packages/{contract['native_id']}"
                and published.get('id')==item['id'] and published.get('lockVersion')==item['lockVersion']
                and published.get('_links',{}).get('project',{}).get('href')=='/api/v3/projects/6'
                and digest(published.get('description',{}).get('raw',''))==digest(item.get('description',{}).get('raw',''))):return True
    return False


def cancel(service,actor,run_id):
    from .engineering import authorized
    authorized(service,actor);service.store.agent_run(actor,6,run_id)
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT state,payload,actor FROM ai_queue WHERE id=? AND json_extract(payload,'$.project_id')=6",(run_id,)).fetchone()
        if not row or json.loads(row['payload']).get('engine')!='openclaw':raise PermissionError('ENGINEERING_RUN_REQUIRED')
        if row['state']=='finished':return {'id':run_id,'cancelled':False,'state':'finished'}
        payload=json.loads(row['payload']);payload['cancel_requested']=True
        db.execute('UPDATE ai_queue SET payload=? WHERE id=?',(canonical(payload),run_id))
        db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6",(time.time(),))
        if row['state']=='queued':
            result={'status':'cancelled','error':'ENGINEERING_CANCELLED','text':'Đã hủy trước khi thực thi.'}
            db.execute("UPDATE ai_queue SET state='finished' WHERE id=?",(run_id,))
            db.execute("UPDATE ai_runs SET state='failed_or_unknown',result=? WHERE id=?",(canonical(result),run_id))
            service.store._sync_agent(db,run_id,'FAILED',result)
    service.store.record(actor,'engineering_cancel',run_id,'checkpoint_requested')
    return {'id':run_id,'cancelled':row['state']=='queued','state':'cancelling' if row['state']=='executing' else 'cancelled'}


def resume(service,actor,run_id,version,*,preserve_auto=False):
    from .engineering import authorized
    native,_=authorized(service,actor);run=service.store.agent_run(actor,6,run_id);setup(service.store)
    # Local readiness checks acquire their own Store transaction before the resume write lock.
    try:provider_readiness=service.gemini.readiness(service.gemini.settings())
    except Exception:provider_readiness={}
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT q.state,q.payload,q.served,r.result,q.actor FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id=? AND json_extract(q.payload,'$.project_id')=6",(run_id,)).fetchone()
        if not row or json.loads(row['payload']).get('engine')!='openclaw':raise PermissionError('ENGINEERING_RUN_REQUIRED')
        result=json.loads(row['result'] or '{}');contract=json.loads(row['payload'])
        if result.get('status')=='succeeded':return {'id':run_id,'deduplicated':True}
        if row['state']=='executing':raise ValueError('ENGINEERING_WORKER_STILL_ACTIVE')
        saved=db.execute('SELECT version,document FROM engineering_checkpoints WHERE run_id=?',(run_id,)).fetchone()
        checkpoint=json.loads(saved['document']) if saved else {}
        if row['served'] and (not saved or type(version) is not int or saved['version']!=version
                or not checkpoint.get('terminal_known') or not checkpoint.get('resumable')):
            raise ValueError('ENGINEERING_RECONCILIATION_REQUIRED')
        pending_resume=(row['state']=='queued' and result.get('status')=='waiting' and result.get('stage')=='RESUMING') or (row['state']=='finished' and result.get('error')=='ENGINEERING_PAUSED' and result.get('pending_resume') is True)
        mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        if pending_resume and mode=='RUN_ONCE':
            return {'id':run_id,'mode':'RUN_ONCE','recovery_count':contract.get('recovery_count',0),'deduplicated':True}
        from .engineering_observability import policy
        rules=policy(service)
        if preserve_auto and mode!='AUTO':raise ValueError('ENGINEERING_MODE_CHANGED')
        if preserve_auto and not rules['auto_continue']:raise ValueError('ENGINEERING_AUTO_CONTINUATION_DISABLED')
        if preserve_auto and (contract.get('cancel_requested') or result.get('status') in {'paused','cancelled'}):raise ValueError('ENGINEERING_CANCELLED_OR_PAUSED')
        if contract.get('recovery_count',0)>=rules['max_continuations'] and not (pending_resume and mode in {'PAUSED','OFF','AUTO'}):
            raise ValueError('ENGINEERING_RECOVERY_BUDGET_EXHAUSTED')
        if row['served'] and not pending_resume:
            from .engineering_observability import describe_run
            description=describe_run(service,{'id':run_id,'native_id':contract['native_id'],'unit':contract['unit'],
                'created_at':0,'queue_state':row['state'],'result':result,'checkpoint':{'version':saved['version'],**checkpoint}},provider_readiness=provider_readiness)
            reason=description['resume']['reason']
            if reason in {'CUMULATIVE_BUDGET_EXHAUSTED','CONTINUATION_LIMIT_REACHED','PROVIDER_RECOVERY_REQUIRED'}:
                raise ValueError('ENGINEERING_'+reason)
            if reason=='COOLDOWN' and description['failure']['category'] in {'DEV_BUDGET_EXHAUSTED','PROVIDER_QUOTA_EXHAUSTED'}:
                raise ValueError('ENGINEERING_CONTINUATION_COOLDOWN')
        item=native.package(contract['native_id'])
        if not source_matches(service.store,run.actor_id,run_id,contract,item):
            raise ValueError('ENGINEERING_SOURCE_STALE')
        if db.execute("SELECT 1 FROM ai_queue WHERE state!='finished' AND id!=?",(run_id,)).fetchone():raise ValueError('ENGINEERING_OTHER_RUN_ACTIVE')
        # External write outcomes are never guessed by an ordinary resume button.
        if db.execute("SELECT 1 FROM requests WHERE actor=? AND key LIKE ? AND state NOT IN ('done','rejected')",(run.actor_id,'engineering-'+run_id+'-%')).fetchone():
            raise ValueError('ENGINEERING_NATIVE_OUTCOME_RECONCILIATION_REQUIRED')
        now=time.time();contract.update(deadline=now+1800,recovery_count=contract.get('recovery_count',0)+(1 if row['served'] and not pending_resume else 0),cancel_requested=False)
        task=AgentTask.from_json(db.execute('SELECT document FROM agent_tasks WHERE id=?',(run.task_id,)).fetchone()[0])
        task=task.model_copy(update={'expires_at':now+2100})
        db.execute('UPDATE agent_tasks SET document=?,expires=? WHERE id=?',(task.model_dump_json(),task.expires_at,task.task_id))
        db.execute("UPDATE ai_queue SET state='queued',payload=?,lease_until=NULL WHERE id=?",(canonical(contract),run_id))
        db.execute("UPDATE ai_runs SET state='running',result=? WHERE id=?",(canonical({'status':'waiting','stage':'RESUMING','text':'Tiếp tục từ checkpoint đã đối soát.'}),run_id))
        db.execute('UPDATE agent_runs SET document=? WHERE id=?',(run.model_copy(update={'state':'QUEUED','result':None,'updated_at':now}).model_dump_json(),run_id))
        db.execute("UPDATE engineering_control SET mode=?,updated=? WHERE project=6",('AUTO' if preserve_auto else 'RUN_ONCE',now))
        from .execution_events import append
        append(db,run,'RETRY_SCHEDULED',status='QUEUED',key='engineering-resume:'+str(contract['recovery_count']))
    service.store.record(actor,'engineering_resume',run_id,'queued-unpaused' if pending_resume else str(version))
    return {'id':run_id,'mode':'AUTO' if preserve_auto else 'RUN_ONCE','recovery_count':contract['recovery_count']}

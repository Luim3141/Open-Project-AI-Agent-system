"""Project6 capability and durable delivery through the existing Supervisor queue."""
import copy
import json
import time
import uuid

from .agent_models import AgentTask
from .store import canonical, digest
from .engineering_units import UNIT,EXPANSION,UNITS

PROJECT = 6
IDENTIFIER = 'ai-dev-demo'
REPOSITORY = 'Luim3141/mini-task-manager'
STAGES = {'PLANNING', 'DEVELOPING', 'REVIEWING', 'TESTING', 'REWORK', 'FINALIZING', 'PUBLISHING'}


def project_for_run(service,actor,run_id):
    """REST/n8n reads resolve scope from an owned stored run, never a caller hint."""
    with service.store.connect() as db:
        row=db.execute("SELECT a.project FROM agent_runs a JOIN ai_queue q ON q.id=a.id WHERE a.id=? AND a.actor=? AND json_extract(q.payload,'$.engine')='openclaw'",(run_id,actor)).fetchone()
        if not row and actor == 18:
            row=db.execute("SELECT a.project FROM agent_runs a JOIN ai_queue q ON q.id=a.id WHERE a.id=? AND json_extract(q.payload,'$.engine')='openclaw'",(run_id,)).fetchone()
    return PROJECT if row and row['project']==PROJECT and service.config.get('engineering',{}).get('enabled') is True else None


def scoped_service(service, project):
    if project == service.config['project_id']:
        return service
    policy = service.config.get('engineering', {})
    if type(project) is not int or project != PROJECT or policy.get('enabled') is not True:
        raise PermissionError('ENGINEERING_PROJECT_NOT_ENABLED')
    actors = policy.get('actors')
    if not isinstance(actors, dict) or not actors or any(v not in {'PM', 'BA', 'QA', 'AI_SYSTEM_OWNER'} for v in actors.values()):
        raise PermissionError('ENGINEERING_ACTOR_POLICY_REQUIRED')
    config = copy.deepcopy(service.config)
    config.update(project_id=PROJECT, users=actors, native_incremental_sync={'enabled': False})
    config['_engineering_scope'] = True
    from .service import Service
    return Service(service.store, config, service.workspace.root, native_factory=service.native_factory)


def authorized(service, actor):
    policy = service.config.get('engineering', {})
    if service.config['project_id'] != PROJECT or policy.get('enabled') is not True:
        raise PermissionError('ENGINEERING_PROJECT_REQUIRED')
    native, who = service.native_actor(actor)
    if who['role'] not in {'PM', 'AI_SYSTEM_OWNER'}:
        raise PermissionError('ENGINEERING_PM_REQUIRED')
    project = native.call('/api/v3/projects/6')
    if project.get('identifier') != IDENTIFIER or not project.get('active'):
        raise PermissionError('ENGINEERING_PROJECT_MISMATCH')
    return native, who


def setup(store):
    if getattr(store,'_engineering_ready',False):return
    from .engineering_lifecycle import setup as lifecycle_setup
    lifecycle_setup(store)
    with store.connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS engineering_control(project INTEGER PRIMARY KEY,mode TEXT NOT NULL,updated REAL NOT NULL)")
        db.execute("INSERT OR IGNORE INTO engineering_control VALUES(6,'OFF',?)", (time.time(),))
        from .engineering_owner_control import setup as owner_setup
        owner_setup(db)
    # Repeated dashboard reads must not compete for the SQLite writer lock.
    store._engineering_ready=True


def build_workforce_profiles(service, quota_model):
    """Project6 observations only; configured quota/catalog entries are not execution proof."""
    from .agent_registry import engineering_profile
    profiles = []
    unknown = 'NOT VERIFIED — Chưa có bằng chứng'
    with service.store.connect() as db:
        run_roles = {row['id']: row['agent'] for row in db.execute(
            "SELECT q.id, json_extract(r.result,'$.agent') AS agent FROM ai_queue q JOIN ai_runs r ON r.id=q.id "
            "WHERE q.state='executing' AND json_extract(q.payload,'$.project_id')=6 "
            "AND json_extract(q.payload,'$.engine')='openclaw'"
        )}
        # Planning emits lifecycle events without updating result.agent; the latest handoff wins.
        for event in db.execute(
            "SELECT e.run_id, json_extract(e.document,'$.agent_id') AS agent, "
            "json_extract(e.document,'$.event_type') AS kind FROM execution_events e "
            "JOIN ai_queue q ON q.id=e.run_id AND q.actor=e.actor "
            "WHERE e.project=6 AND q.state='executing' AND json_extract(q.payload,'$.project_id')=6 "
            "AND json_extract(q.payload,'$.engine')='openclaw' "
            "AND json_extract(e.document,'$.agent_id') IS NOT NULL "
            "AND json_extract(e.document,'$.event_type') IN "
            "('AGENT_STARTED','AGENT_COMPLETED','AGENT_FAILED','REVIEW_STARTED','REVIEW_COMPLETED') "
            "ORDER BY e.sequence"
        ):
            run_roles[event['run_id']] = event['agent'] if event['kind'] in {'AGENT_STARTED', 'REVIEW_STARTED'} else None
        active_roles = set(run_roles.values())
        last_oc = db.execute(
            "SELECT q.id, q.state, q.payload, r.result FROM ai_queue q "
            "JOIN ai_runs r ON r.id=q.id "
            "WHERE json_extract(q.payload,'$.project_id')=6 "
            "AND json_extract(q.payload,'$.engine')='openclaw' "
            "ORDER BY q.created DESC LIMIT 1"
        ).fetchone()

        role_titles = {
            'supervisor': 'AI Supervisor (Orchestrator & Gatekeeper)',
            'pm': 'Product Manager Agent (Backlog & WBS)',
            'ba': 'Business Analyst Agent (Requirements & AC)',
            'dev': 'Senior Developer Agent (Implementation)',
            'reviewer': 'Code Reviewer Agent (Quality Gate)',
            'qa': 'QA Automation Lead (Acceptance & Test)'
        }

        for role in ['supervisor', 'pm', 'ba', 'dev', 'reviewer', 'qa']:
            prof = engineering_profile(role)
            rec_row = db.execute(
                "SELECT c.id, c.run_id, c.document FROM gemini_call_receipts c "
                "JOIN ai_queue q ON q.id=c.run_id AND q.actor=c.actor "
                "WHERE json_extract(q.payload,'$.project_id')=6 "
                "AND json_extract(q.payload,'$.engine')='openclaw' "
                "AND json_extract(c.document,'$.agent')=? "
                "ORDER BY CAST(json_extract(c.document,'$.at') AS REAL) DESC, c.rowid DESC LIMIT 1", (role,)
            ).fetchone()
            rec_doc = json.loads(rec_row['document']) if rec_row and rec_row['document'] else {}
            actual_model = rec_doc.get('model') or unknown
            provider = rec_doc.get('provider') or unknown
            runtime = 'openclaw (receipt)' if rec_doc.get('session_id') else prof['runtime'] + ' (configured; runtime NOT VERIFIED)'
            oc_session = rec_doc.get('session_id') or unknown
            last_exec = rec_row['run_id'] if rec_row else unknown
            last_err = rec_doc.get('error') or ('None' if rec_doc.get('state') in {'LIVE_SUCCESS', 'HTTP_SUCCESS'} else rec_doc.get('state') or unknown)
            evidence = 'Receipt: ' + canonical({
                'id': rec_row['id'], 'run_id': rec_row['run_id'], 'state': rec_doc.get('state') or unknown,
                'at': rec_doc.get('at') if rec_doc.get('at') is not None else unknown,
                'usage': rec_doc.get('usage') or unknown
            }) if rec_row else unknown
            if role == 'supervisor':
                actual_model = 'Không dùng model (LOCAL_DETERMINISTIC)'
                provider = 'local-deterministic'
                runtime = 'qldapm-supervisor (LOCAL_DETERMINISTIC)'
                oc_session = unknown
                last_exec = last_oc['id'] if last_oc else unknown
                result = json.loads(last_oc['result'] or '{}') if last_oc else {}
                last_err = result.get('error') or ('None' if result.get('status') == 'succeeded' else unknown)
                evidence = 'Stored queue run: ' + canonical({
                    'id': last_oc['id'], 'queue_state': last_oc['state'], 'status': result.get('status')
                }) if last_oc else unknown

            prof.update({
                'role_title': role_titles[role],
                'actual_model_id': actual_model,
                'provider': provider,
                'runtime_display': runtime,
                'openclaw_session': oc_session,
                'last_execution': last_exec,
                'last_error': last_err,
                'skills_loaded': unknown,
                'evidence': evidence,
                'status': 'RUNNING' if role in active_roles else 'STANDBY'
            })
            profiles.append(prof)
    return profiles


def backlog_snapshot(service,actor):
    """Local persisted eligibility; scheduling never polls GitHub or reports."""
    from .engineering_planning import definitions
    from .engineering_integrity import observed_result
    units=[]
    with service.store.connect() as db:
        mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        ready_plans={r[0] for r in db.execute("SELECT p.id FROM engineering_plans p JOIN ai_runs r ON r.id=p.id WHERE json_extract(p.document,'$.state')='PUBLISHED' AND json_extract(r.result,'$.status') IN ('succeeded','blocked')")}
        all_runs={}
        for r in db.execute("SELECT q.id,q.state,q.payload,r.result,q.actor,a.document AS agent_document FROM ai_queue q JOIN ai_runs r ON r.id=q.id LEFT JOIN agent_runs a ON a.id=q.id WHERE json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw' ORDER BY q.created"):
            agent_state=json.loads(r['agent_document'] or '{}').get('state')
            all_runs[json.loads(r['payload'])['unit']]={'id':r['id'],'queue_state':r['state'],
                'result':observed_result(json.loads(r['result'] or '{}'),agent_state),'actor':r['actor']}
    for key,definition in definitions(service.store,actor).items():
        run=all_runs.get(key)
        dependency=definition.get('base_unit')
        previous=all_runs.get(dependency)
        units.append({'unit':key,'title':definition['title'],'native_id':definition.get('native_id',379),
            'dependency':dependency,'dependency_ready':not dependency or bool(previous and (previous['result'] or {}).get('status')=='succeeded'),
            'planning_ready':not definition.get('plan_id') or definition['plan_id'] in ready_plans,
            'state':(run['result'] or {}).get('status',run['queue_state']) if run else 'PLANNED','run_id':run['id'] if run else None})
    has_active=any(run['queue_state']!='finished' for run in all_runs.values())
    for unit in units:
        unit['eligible']=unit['state']=='PLANNED' and unit['planning_ready'] and unit['dependency_ready'] is True and not has_active and mode!='PAUSED'
        unit['blocked_reason']=('ENGINEERING_PLAN_HANDOFF_REQUIRED' if not unit['planning_ready'] else
            'DEPENDENCY_NOT_VERIFIED' if not unit['dependency_ready'] else
            'RECONCILIATION_REQUIRED' if unit['state'] in {'blocked','failed','paused','cancelled'} else
            'CONCURRENCY_LOCKED' if has_active and unit['state']=='PLANNED' else
            'ENGINEERING_PAUSED' if mode=='PAUSED' and unit['state']=='PLANNED' else None)
    return units,all_runs


def status(service, actor):
    from .engineering_integrity import observed_result
    native,who=authorized(service, actor)
    setup(service.store)
    with service.store.connect() as db:
        mode = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        if mode=='RUN_ONCE' and not db.execute("SELECT 1 FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw' AND state!='finished'").fetchone():
            db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode='RUN_ONCE'",(time.time(),))
            mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        rows = db.execute("SELECT q.id,q.state,q.payload,r.result,q.actor,q.created FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw' ORDER BY q.created DESC LIMIT 100").fetchall()
    runs=[]
    with service.store.connect() as db:
        for r in rows:
            agent_document=db.execute('SELECT document FROM agent_runs WHERE id=?',(r['id'],)).fetchone()
            agent_state=json.loads(agent_document[0]).get('state') if agent_document else None
            receipts=[json.loads(v[0]) for v in db.execute('SELECT document FROM gemini_call_receipts WHERE run_id=?',(r['id'],))]
            usage=[v.get('usage') or {} for v in receipts]
            from .engineering_lifecycle import load
            checkpoint=load(service.store,r['id'],connection=db)
            runs.append({'id':r['id'],'queue_state':r['state'],'created_at':r['created'],'unit':json.loads(r['payload'])['unit'],
                'native_id':json.loads(r['payload'])['native_id'],'checkpoint':checkpoint,
                'result':observed_result(json.loads(r['result'] or '{}'),agent_state),
                'usage':{'requests_recorded':len(receipts),'total_tokens_reported':sum(v.get('totalTokenCount',0) for v in usage),
                    'usage_missing':sum('totalTokenCount' not in v for v in usage)}})
    units,all_runs=backlog_snapshot(service,actor)
    with service.store.connect() as db:
        plans=[]
        for r in db.execute('SELECT p.id,p.document,q.created FROM engineering_plans p LEFT JOIN ai_queue q ON q.id=p.id ORDER BY p.rowid DESC LIMIT 100'):
            plan=json.loads(r['document'])
            plan.update(run_id=r['id'],created_at=plan.get('created_at') or r['created'],published_at=plan.get('updated') if plan.get('state')=='PUBLISHED' else None)
            plans.append(plan)
        worker=db.execute('SELECT worker_id,seen,run_id FROM engineering_worker_state WHERE project=6').fetchone()
        worker={**dict(worker),'state':'ALIVE' if time.time()-worker['seen']<30 else 'STALE'} if worker else {'state':'NOT_SEEN'}
    for plan in plans:
        plan_run=next((run for run in runs if run['id']==plan.get('id')),None)
        if plan_run:
            plan.update(native_id=plan_run['native_id'],run_id=plan_run['id'],created_at=plan.get('created_at') or plan_run['created_at'])
        for key,entry in plan.get('native_units',{}).items():
            observed=all_runs.get(key)
            if observed and observed['result'].get('status')=='succeeded':
                entry.update(state='DELIVERED',delivery_run_id=observed['id'],head_sha=observed['result'].get('head_sha'),pr_url=observed['result'].get('pr_url'))
    packages=native.packages() if hasattr(native,'packages') else []
    tasks=[{'id':p['id'],'lock_version':p['lockVersion'],'subject':p['subject'],'created_at':p.get('createdAt'),'updated_at':p.get('updatedAt'),'project':6,'status':p.get('_links',{}).get('status',{}).get('title')} for p in packages if p['id'] in {379,*[u['native_id'] for u in units]}]
    try:
        policy=service.gemini.settings();quota={'model':policy['model'],'limits':policy['limits'],'fallback':False}
    except Exception:quota={'state':'UNAVAILABLE'}
    from .engineering_github_sync import read_projection
    github_info = read_projection(service)
    from . import engineering_reporting
    reporting_schedule = engineering_reporting.get_schedule(service, actor,verified_native=native)
    from .engineering_observability import describe_runs, enrich_profiles, persist_notifications, policy
    try:provider_readiness=service.gemini.readiness(service.gemini.settings())
    except Exception:provider_readiness={}
    descriptions = describe_runs(service,runs,provider_readiness=provider_readiness)
    persist_notifications(service, descriptions)
    notifications = engineering_reporting.list_notifications(service, actor, limit=50, unread_only=True)
    all_reports = engineering_reporting.list_reports(service, actor, limit=5,verified_native=native,versions={p['id']:p.get('lockVersion') for p in packages})
    from .engineering_owner_control import observe
    from .engineering_telemetry import snapshot
    control_state,queue_state,worker=observe(service,units)
    telemetry = snapshot(service.store,runs)
    by_id = {item['id']:item for item in descriptions}
    for run in runs:
        run.update({key:value for key,value in by_id[run['id']].items() if key!='result'})
    for item in telemetry['runs']:
        item.update(by_id[item['id']])
    by_native = {item['id']:item for item in tasks}
    for unit in units:
        description = by_id.get(unit.get('run_id')) or {}
        native_task = by_native.get(unit['native_id']) or {}
        unit.update({key:description.get(key) for key in ['agent','stage','failure','budget','resume','pr_url','task_status']})
        unit.update(created_at=native_task.get('created_at') or description.get('created_at'),
                    updated_at=description.get('updated_at') or native_task.get('updated_at'),project=6,
                    native_url='/work_packages/'+str(unit['native_id']))
        if description.get('blocked_reason'):unit['blocked_reason']=description['blocked_reason']
    units.sort(key=lambda unit: str(unit.get('updated_at') or ''),reverse=True)
    from .engineering_observability import notification
    if worker['state'] in {'STALE','DEAD'}:
        notification(service,'worker:'+str(worker.get('worker_id'))+':'+str(worker.get('seen'))+':'+worker['state'],
            'WORKER_'+worker['state'],message='Worker heartbeat không còn mới; không chứng minh Agent đang chạy.',level='ERROR')
    if quota.get('state')=='UNAVAILABLE':
        notification(service,'provider:UNAVAILABLE','PROVIDER_TEMPORARILY_UNAVAILABLE',message='Không đọc được provider policy; chưa kiểm tra inference.',level='ERROR')
    notifications = engineering_reporting.list_notifications(service, actor, limit=100, unread_only=True)
    with service.store.connect() as db:
        notification_unread_count=db.execute('SELECT count(*) FROM engineering_notifications WHERE project=6 AND unread=1').fetchone()[0]
    control_state['scheduler_policy']={'blocked_default':'STOP_AUTO_REQUIRE_OWNER','auto_continuation_enabled':policy(service)['auto_continue']}
    profiles = enrich_profiles(build_workforce_profiles(service, quota.get('model', 'gemini-3.5-flash-lite')),descriptions)
    knowledge_sources=[{'source_key':key,'label':key} for key,value in service.config.get('file_sources',{}).items() if isinstance(value,dict) and value.get('project_id')==6 and (who['role']=='AI_SYSTEM_OWNER' or who['role'] in value.get('allowed_roles',[]))]
    from .engineering_health import integration_health,provider_status,demo_observability
    from .workflow_status import snapshot as workflow_snapshot
    from .delegated_approval import status as delegated_status
    from .engineering_github_operations import snapshot as github_operations
    from .engineering_status_sync import snapshot as native_sync
    sync_by_id={s['native_id']:s for s in native_sync(service)}
    for task in tasks:
        sync=sync_by_id.get(task['id'])
        if sync and sync.get('native_version') and sync['native_version']!=task['lock_version']:
            sync={**sync,'state':'STALE_SOURCE','reason':'NATIVE_CHANGED_AFTER_SYNC_READBACK'}
        task['status_sync']=sync
    return {'native_status_sync':list(sync_by_id.values()),'github_operations':github_operations(service,actor),'delegated_approval':delegated_status(service,actor,packages=packages,authority=(native,who)),'knowledge_sources':knowledge_sources,'workflow_status':workflow_snapshot(service,actor,authority=(native,who),packages=packages),'demo_observability':demo_observability(service),'provider_health':provider_status(service),'integration_health':integration_health(service),'project_id':PROJECT,'mode':mode,'runs':runs,'backlog':units,'tasks':tasks,'plans':plans,'quota':quota,'delivery_worker':worker,'github':github_info,
        'control':control_state,'queue':queue_state,'telemetry':telemetry,
        'profiles': profiles,
        'reporting_schedule':reporting_schedule,'notifications':notifications,'notification_unread_count':notification_unread_count,'recent_reports':all_reports.get('reports',[])}


def github_sync(service, actor, request_key=None,*,authority=None):
    from .engineering_github_operations import enqueue
    return enqueue(service,actor,request_key,authority=authority)


def admit(service, actor, args, request_key, expected_mode=None):
    native, who = authorized(service, actor)
    from .engineering_planning import PLANNING,planning_definition,selected
    if not args:
        units,_=backlog_snapshot(service,actor)
        target=next((unit for unit in units if unit.get('eligible') is True or
            unit.get('state')=='PLANNED' and unit.get('blocked_reason')=='ENGINEERING_PAUSED'),None)
        if not target:raise ValueError('NO_ELIGIBLE_WORK')
        source=native.package(target['native_id'])
        args={'native_id':target['native_id'],'lock_version':source['lockVersion'],'unit':target['unit']}
    if set(args) not in ({'native_id','lock_version','unit'},{'native_id','lock_version','unit','feedback'}) or type(args['native_id']) is not int or not isinstance(args['unit'],str):
        raise PermissionError('ENGINEERING_APPROVED_UNIT_REQUIRED')
    setup(service.store)
    if args['unit']==PLANNING:
        if args['native_id']!=379 or not isinstance(args.get('feedback',''),str) or len(args.get('feedback',''))>6000:raise ValueError('ENGINEERING_PLAN_INPUT_INVALID')
        item=native.package(379);definition=planning_definition(item,args.get('feedback',''))
        args={**args,'unit':PLANNING+'-'+definition['source_hash'][:16],'lock_version':item['lockVersion']}
    else:
        definition=selected(service.store,actor,args['unit'])
        if 'feedback' in args or args['native_id']!=definition.get('native_id',379):raise PermissionError('ENGINEERING_APPROVED_UNIT_REQUIRED')
        if definition.get('plan_id'):
            with service.store.connect() as db:
                plan=db.execute('SELECT document FROM engineering_plans WHERE id=?',(definition['plan_id'],)).fetchone()
                result=db.execute('SELECT result FROM ai_runs WHERE id=?',(definition['plan_id'],)).fetchone()
            if not plan or json.loads(plan[0]).get('state')!='PUBLISHED' or not result or json.loads(result[0] or '{}').get('status') not in ('succeeded', 'blocked'):raise ValueError('ENGINEERING_PLAN_HANDOFF_REQUIRED')
        item=native.package(args['native_id'])
    if type(args['lock_version']) is not int or item['lockVersion'] != args['lock_version']:
        raise ValueError('ENGINEERING_SOURCE_STALE')
    if not isinstance(request_key, str) or not 1 <= len(request_key) <= 80:
        raise ValueError('IDEMPOTENCY_KEY_REQUIRED')
    setup(service.store)
    # The same business unit is returned even when two event sources use different keys.
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if expected_mode is not None and db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]!=expected_mode:
            raise ValueError('ENGINEERING_MODE_CHANGED')
        unit=args['unit']
        old = db.execute("SELECT q.id,q.state,q.served,q.payload,r.result,q.actor FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE json_extract(q.payload,'$.engine')='openclaw' AND json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.native_id')=? AND json_extract(q.payload,'$.unit')=?", (args['native_id'],unit)).fetchone()
        if old:
            run_actor = old['actor']
            run = service.store.agent_run(run_actor, PROJECT, old['id'])
            old_res = json.loads(old['result'] or '{}')
            paused = old['state'] == 'finished' and (old_res.get('status') == 'paused' or old_res.get('error') in {'ENGINEERING_PAUSED', 'ENGINEERING_PAUSED_CHECKPOINT_REQUIRED'})
            cancelled = old['state'] == 'finished' and old_res.get('error') == 'ENGINEERING_PAUSED'
            if old['state'] == 'queued' or ((paused or cancelled) and not old['served']):
                payload = json.loads(old['payload'])
                payload['source_version'] = item['lockVersion']
                now = time.time(); payload['deadline'] = now + 1800
                task = AgentTask.from_json(db.execute('SELECT document FROM agent_tasks WHERE id=?', (run.task_id,)).fetchone()[0])
                task = task.model_copy(update={'expires_at': now + 1800})
                db.execute('UPDATE agent_tasks SET document=?,expires=? WHERE id=?', (task.model_dump_json(), task.expires_at, run.task_id))
                db.execute("UPDATE ai_queue SET state='queued',payload=?,served=0 WHERE id=?", (canonical(payload), run.run_id))
                db.execute("UPDATE ai_runs SET state='running',result=? WHERE id=?", (canonical({'status': 'waiting', 'stage': 'QUEUED', 'text': 'Unit được tiếp tục thực thi theo RUN ONCE.'}), run.run_id))
                db.execute('UPDATE agent_runs SET document=? WHERE id=?', (run.model_copy(update={'state': 'QUEUED', 'result': None, 'updated_at': now}).model_dump_json(), run.run_id))
                db.execute("UPDATE engineering_control SET mode='RUN_ONCE',updated=? WHERE project=6", (now,))
                return {'id': run.run_id, 'deduplicated': True, 'resumed_before_execution': True, 'mode': 'RUN_ONCE'}
            return {'id': run.run_id, 'deduplicated': True,
                'requires_reconciliation': old['state'] == 'finished' and old_res.get('status') != 'succeeded'}
        active_check = db.execute("SELECT id, state, created FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw' AND state!='finished'").fetchone()
        if active_check:
            raise ValueError(f'ENGINEERING_UNIT_ALREADY_ACTIVE; run {active_check["id"]} is currently {active_check["state"]}')
        if db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0] == 'PAUSED':
            raise ValueError('ENGINEERING_PAUSED')
        base_sha=None
        if definition['base_unit']:
            previous=db.execute("SELECT r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.state='finished' AND json_extract(q.payload,'$.engine')='openclaw' AND json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.unit')=?",(definition['base_unit'],)).fetchone()
            result=json.loads(previous[0]) if previous else {}
            import re
            if result.get('status')!='succeeded' or not re.fullmatch('[a-f0-9]{40}',result.get('head_sha','')):
                raise ValueError('ENGINEERING_DEPENDENCY_NOT_VERIFIED')
            base_sha=result['head_sha']
            if definition.get('base_sha'):
                from .engineering_planning import integration_base
                verified=integration_base(service,base_sha)
                if verified!={key:definition[key] for key in ('base_sha','base_branch')}:
                    raise ValueError('ENGINEERING_INTEGRATION_BASE_STALE')
                base_sha=verified['base_sha']
        now = time.time()
        run_actor = 20 if actor == 18 else actor
        task = AgentTask(task_id=str(uuid.uuid4()), actor_id=run_actor, project_id=PROJECT,
            conversation_id=str(uuid.uuid4()), agent='supervisor', instruction=f'Engineering {unit} for #379',
            references=[{'work_package_id':args['native_id'],'lock_version':item['lockVersion']}], created_at=now, expires_at=now+1800)
        # Store methods open their own transactions; admission is serialized across callers by this transaction.
        from .agent_models import AgentRun
        run_id = str(uuid.uuid4()); trace = str(uuid.uuid4())
        run = AgentRun(run_id=run_id,task_id=task.task_id,actor_id=run_actor,project_id=PROJECT,
            trace_id=trace,created_at=now,updated_at=now)
        payload = {'engine':'openclaw','project_id':PROJECT,'native_id':args['native_id'],'source_version':item['lockVersion'],
            'definition':definition,'kind':definition.get('kind','development'),
            'unit':unit,'base_sha':base_sha,'repository':REPOSITORY,'stage':'ADMITTED','request_key':request_key,
            'spec':item.get('description',{}).get('raw',''),'spec_sha256':digest(item.get('description',{}).get('raw','')),
            'allow_routine_writes':False,'write_scope_ids':[],'deadline':now+1800}
        from .engineering_observability import policy
        payload['budget']=policy(service)
        db.execute('INSERT INTO agent_tasks VALUES(?,?,?,?,?,?)',(task.task_id,run_actor,PROJECT,task.conversation_id,task.model_dump_json(),task.expires_at))
        db.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?)',(run_id,task.task_id,run_actor,PROJECT,run.model_dump_json()))
        db.execute("INSERT INTO ai_runs VALUES(?,?,'running',?,?)",(run_id,run_actor,canonical({'status':'waiting','stage':'ADMITTED','text':'OpenClaw engineering unit đã được nhận; chờ worker.'}),now))
        db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,?,?,'queued',?,'agent')",(run_id,run_actor,canonical(payload),now))
        mode_row = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()
        target_mode = 'AUTO' if mode_row and mode_row[0] == 'AUTO' else 'RUN_ONCE'
        db.execute("UPDATE engineering_control SET mode=?,updated=? WHERE project=6",(target_mode,now))
        from .execution_events import append
        for event in ['REQUEST_RECEIVED','AUTHORIZED','QUEUED']:
            append(db,run,event,status='QUEUED',key=event)
    service.store.record(actor,'engineering_admit',run_id,'ADMITTED')
    return {'id':run_id,'deduplicated':False,'mode':target_mode}


def control(service, actor, mode, expected_revision=None, request_key=None):
    authorized(service, actor)
    if mode not in {'OFF','PAUSED','AUTO'}:
        raise ValueError('ENGINEERING_MODE_INVALID')
    setup(service.store)
    from .engineering_owner_control import command_result
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        revision=db.execute('SELECT revision FROM engineering_owner_revision WHERE project=6').fetchone()[0]
        if expected_revision is not None and (type(expected_revision) is not int or expected_revision!=revision):
            conflict=True
            current_mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        else:
            conflict=False
        if conflict:
            rows=[]
        else:
            db.execute('UPDATE engineering_control SET mode=?,updated=? WHERE project=6',(mode,time.time()))
            rows=db.execute("SELECT id,state FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw' AND state!='finished'").fetchall()
        for row in rows:
            if row['state']=='queued' and mode=='OFF':
                result={'status':'failed','text':'Engineering paused before execution.','error':'ENGINEERING_PAUSED'}
                previous=json.loads(db.execute('SELECT result FROM ai_runs WHERE id=?',(row['id'],)).fetchone()[0] or '{}')
                if previous.get('status')=='waiting' and previous.get('stage')=='RESUMING':result['pending_resume']=True
                db.execute("UPDATE ai_queue SET state='finished' WHERE id=?",(row['id'],))
                db.execute("UPDATE ai_runs SET state='failed_or_unknown',result=? WHERE id=?",(canonical(result),row['id']))
                service.store._sync_agent(db,row['id'],'FAILED',result)
    if conflict:
        return command_result(service,actor,mode,{'mode':current_mode},False,'ENGINEERING_STATE_REVISION_CONFLICT',request_key)
    service.store.record(actor,'engineering_control',str(PROJECT),mode)
    scheduled = None
    if mode == 'AUTO':
        from .engineering_auto import schedule_next_auto_unit
        try:scheduled = schedule_next_auto_unit(service, actor)
        except Exception:
            with service.store.connect() as db:db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode='AUTO'",(time.time(),))
            service.store.record(actor,'engineering_auto_shutoff',str(PROJECT),'ADMISSION_FAILED')
            raise
    with service.store.connect() as db:
        actual_mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
    return command_result(service,actor,mode,{'mode':actual_mode,'active_worker_must_checkpoint':any(r['state']=='executing' for r in rows),'scheduled':scheduled},
        reason=(scheduled or {}).get('reason'),request_id=request_key)


def claim(service, actor, worker_id=None):
    authorized(service, actor)
    setup(service.store)
    with service.store.connect() as db:
        mode = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        if mode not in {'RUN_ONCE', 'AUTO'}:
            return None
    claimed=service.store.claim_run(openclaw_only=True,worker_id=worker_id)
    if claimed and claimed['actor'] != actor and not (actor == 18 and claimed['actor'] in {18, 20}):
        raise PermissionError('ENGINEERING_CLAIM_ACTOR_MISMATCH')
    if claimed is None:
        with service.store.connect() as db:
            active = db.execute("SELECT 1 FROM ai_queue WHERE json_extract(payload,'$.engine')='openclaw' AND state!='finished'").fetchone()
            if not active:
                if mode == 'RUN_ONCE':
                    db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode='RUN_ONCE'",(time.time(),))
                elif mode == 'AUTO':
                    from .engineering_auto import schedule_next_auto_unit
                    schedule_next_auto_unit(service, actor)
    return claimed


def resume_reconciled(service,actor,run_id,result_sha256,artifact=None,rework_feedback=None):
    """OS operator only, after terminal OpenClaw outcome + no publication verified.

    This is an explicit repair of the existing claim, never an event-trigger replay.
    """
    native,_=authorized(service,actor)
    run=service.store.agent_run(actor,PROJECT,run_id)
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if actor == 18:
            row=db.execute('SELECT q.state,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id=?',(run_id,)).fetchone()
        else:
            row=db.execute('SELECT q.state,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id=? AND q.actor=?',(run_id,actor)).fetchone()
        if not row or row['state']!='finished' or digest(row['result'])!=result_sha256:
            raise ValueError('ENGINEERING_RECONCILIATION_CHANGED')
        old=json.loads(row['result']);contract=json.loads(row['payload'])
        artifact_repair=bool(artifact)
        if artifact_repair:
            import re
            if set(artifact)!={'diff_sha256','test_log_sha256','terminal_run_id'} or any(not re.fullmatch('[a-f0-9]{64}',artifact[k]) for k in ['diff_sha256','test_log_sha256']) or not re.fullmatch('[a-f0-9-]{36}',artifact['terminal_run_id']) or contract.get('artifact_reconciled'):
                raise ValueError('ENGINEERING_ARTIFACT_RECONCILIATION_INVALID')
        if rework_feedback is not None and (old.get('error') not in {'GEMINI_LOCAL_RPM_EXHAUSTED','OPENCLAW_STEP_NOT_COMPLETED'} or not isinstance(rework_feedback,str) or not 1<=len(rework_feedback)<=12000):
            raise ValueError('ENGINEERING_REWORK_CHECKPOINT_INVALID')
        if old.get('error') not in {'OPENCLAW_STEP_NOT_COMPLETED','GEMINI_LOCAL_RPM_EXHAUSTED'} or old.get('pr_url') or (contract.get('attempt',0)>=2 and not artifact_repair):
            raise ValueError('ENGINEERING_RECONCILIATION_UNSUPPORTED')
        if db.execute("SELECT 1 FROM requests WHERE key LIKE ?",('engineering-'+run_id+'-%',)).fetchone():
            raise ValueError('ENGINEERING_NATIVE_OUTCOME_RECONCILIATION_REQUIRED')
        item=native.package(379)
        if item['lockVersion']!=contract['source_version'] or digest(item.get('description',{}).get('raw',''))!=contract['spec_sha256']:
            raise ValueError('ENGINEERING_SOURCE_STALE')
        if db.execute("SELECT 1 FROM ai_queue WHERE state!='finished'").fetchone():raise ValueError('ENGINEERING_OTHER_RUN_ACTIVE')
        if db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]!='OFF':raise ValueError('ENGINEERING_OFF_REQUIRED')
        attempt=contract.get('attempt',0)+1
        contract.update(attempt=attempt,deadline=time.time()+1800)
        if artifact_repair:contract.update(artifact_reconciled=artifact,resume_stage='REVIEWING')
        if rework_feedback is not None:contract.update(resume_stage='REWORK',rework_feedback=rework_feedback)
        db.execute("UPDATE ai_queue SET state='queued',payload=?,lease_until=NULL WHERE id=?",(canonical(contract),run_id))
        db.execute("UPDATE ai_runs SET state='running',result=? WHERE id=?",(canonical({'status':'waiting','stage':'RECONCILED','prior_result_sha256':result_sha256,'text':'Operator reconciled terminal failure; existing unit resumed.'}),run_id))
        db.execute('UPDATE agent_tasks SET expires=? WHERE id=?',(time.time()+2100,run.task_id))
        db.execute('UPDATE agent_runs SET document=? WHERE id=?',(run.model_copy(update={'state':'QUEUED','result':None,'updated_at':time.time()}).model_dump_json(),run_id))
        db.execute("UPDATE engineering_control SET mode='RUN_ONCE',updated=? WHERE project=6",(time.time(),))
        from .execution_events import append
        append(db,run,'RETRY_SCHEDULED',status='QUEUED',key='RECONCILED_REPAIR_'+str(attempt))
    service.store.record(actor,'engineering_reconciled_resume',run_id,result_sha256)
    return {'id':run_id,'attempt':attempt,'mode':'RUN_ONCE'}


def progress(service, actor, run_id, stage, details):
    authorized(service,actor)
    run=service.store.agent_run(actor,PROJECT,run_id)
    if stage not in STAGES or len(canonical(details))>48000:
        raise ValueError('ENGINEERING_PROGRESS_INVALID')
    with service.store.connect() as db:
        mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        row=db.execute("SELECT state,payload FROM ai_queue WHERE id=? AND actor=?",(run_id,actor)).fetchone()
        if not row or row['state']!='executing' or json.loads(row['payload']).get('engine')!='openclaw':
            raise ValueError('ENGINEERING_RUN_NOT_CLAIMED')
        if mode not in {'RUN_ONCE', 'AUTO'}:
            raise ValueError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
        agent=details.get('agent')
        if agent in {'supervisor','pm','ba','dev','reviewer','qa'}:
            from .execution_events import append
            key=agent+':'+str(details.get('step',stage))+':'+str(json.loads(row['payload']).get('recovery_count',0))
            append(db,run,'AGENT_ASSIGNED',agent=agent,status='QUEUED',key='engineering-assigned:'+key)
            append(db,run,'AGENT_STARTED',agent=agent,status='RUNNING',key='engineering-started:'+key)
    service.store.progress_run(actor,run_id,{'status':'running','stage':stage,'text':stage,**details})
    from .agent_trace import bind_run,reset_run
    token=bind_run(service.store,actor,PROJECT,run_id)
    try:service.store.record(actor,'engineering_stage',run_id,stage)
    finally:reset_run(token)
    return {'stage':stage}


def finish(service, actor, run_id, result):
    authorized(service,actor)
    service.store.agent_run(actor,PROJECT,run_id)
    with service.store.connect() as db:
        row=db.execute('SELECT state,payload FROM ai_queue WHERE id=? AND actor=?',(run_id,actor)).fetchone()
        if not row or row['state']!='executing' or json.loads(row['payload']).get('engine')!='openclaw':
            raise ValueError('ENGINEERING_RUN_NOT_CLAIMED')
    if result.get('status') not in {'blocked','failed','succeeded','paused','cancelled'} or len(canonical(result))>64000:
        raise ValueError('ENGINEERING_RESULT_INVALID')
    required=['plan_id','native_readback','knowledge_readback'] if json.loads(row['payload']).get('kind')=='planning' else ['head_sha','test_evidence','review_evidence','pr_url','native_readback','knowledge_readback']
    if result['status']=='succeeded' and not all(result.get(k) for k in required):
        raise ValueError('ENGINEERING_COMPLETION_EVIDENCE_REQUIRED')
    service.store.finish_run(actor,run_id,result,'done' if result['status']=='succeeded' else 'failed_or_unknown')
    from .engineering_observability import describe_run,persist_notifications,policy
    from .engineering_lifecycle import load
    contract=json.loads(row['payload'])
    summary=describe_run(service,{'id':run_id,'native_id':contract['native_id'],'unit':contract['unit'],
        'created_at':0,'queue_state':'finished','result':result,'checkpoint':load(service.store,run_id)})
    persist_notifications(service,[summary])
    with service.store.connect() as db:
        current_mode = db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
        if current_mode == 'AUTO':
            if result.get('status') != 'succeeded':
                continuation_allowed=(policy(service)['auto_continue'] and result.get('status') in {'blocked','failed'}
                    and not contract.get('cancel_requested')
                    and ((summary['failure']['category']=='DEV_BUDGET_EXHAUSTED' and summary['resume']['reason'] in {'CHECKPOINT_READY','COOLDOWN'})
                         or (summary['failure']['category']=='PROVIDER_QUOTA_EXHAUSTED' and summary['resume']['reason'] in {'CHECKPOINT_READY','COOLDOWN','PROVIDER_RECOVERY_REQUIRED'})))
                if not continuation_allowed:
                    db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6",(time.time(),))
                    service.store.record(actor,'engineering_auto_shutoff',str(PROJECT),'RUN_BLOCKED_REQUIRES_OWNER',connection=db)
            else:
                from .engineering_auto import schedule_next_auto_unit
                schedule_next_auto_unit(service, actor)
        elif current_mode != 'PAUSED':
            db.execute("UPDATE engineering_control SET mode='OFF',updated=? WHERE project=6 AND mode!='PAUSED'",(time.time(),))
        mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
    return {'id':run_id,'mode':mode,'result':result}

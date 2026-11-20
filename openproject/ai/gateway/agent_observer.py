"""One Work Package, many recorded runs; read-only projection shared by UI and Telegram."""
import json
import re
import time
import uuid
import sqlite3
import logging
from urllib.parse import urlsplit
from pydantic import ValidationError

from .presentation import safe_text
from .store import canonical, digest

STATES = {'QUEUED':'QUEUED','NOT_RUN':'PENDING','RUNNING':'RUNNING','COMPLETED':'COMPLETED',
          'FAILED':'FAILED','BLOCKED':'BLOCKED','PAUSED':'PAUSED','CANCELLED':'CANCELLED'}


def public(value,max_items=300):
    if isinstance(value,dict):return {key:public(item,max_items) for key,item in value.items()}
    if isinstance(value,list):return [public(item,max_items) for item in value[:max_items]]
    return safe_text(value)[:12000] if isinstance(value,str) else value


def acceptance_for(package, project_id, monitor, approval):
    result=monitor.get('_runtime_result') or {};summary=monitor.get('execution_summary') or {}
    review=result.get('review_evidence') or {};qa=review.get('qa') or {};checkpoint=summary.get('checkpoint') or {}
    publication=result.get('native_readback') or {};approval=approval or {};change=approval.get('status_change') or {}
    planned=[n for n in monitor.get('nodes',[]) if n.get('agent') not in {'supervisor','final','provider','native','tools'}]
    roles={n.get('agent') for n in planned}
    revision=review.get('revision')
    gates={
        'runtime_delivery':monitor.get('state')=='COMPLETED' and result.get('status')=='succeeded',
        'recorded_stage_plan':bool(planned) and all(n.get('state')=='COMPLETED' for n in planned),
        'dev_commit':isinstance(result.get('head_sha'),str) and re.fullmatch('[a-f0-9]{40}',result['head_sha']) is not None,
        'independent_review':review.get('verdict')=='PASS' and review.get('findings')==[] and isinstance(revision,str) and re.fullmatch('[a-f0-9]{64}',revision) is not None and revision==checkpoint.get('revision'),
        'qa_passed':qa.get('status')=='PASS' and type(qa.get('exit_code')) is int and qa['exit_code']==0 and type((result.get('test_evidence') or {}).get('exit_code')) is int and result['test_evidence']['exit_code']==0,
        'handoff':publication.get('child_id')==package['id'] and publication.get('project_id')==project_id and type(publication.get('child_version')) is int and publication['child_version']<=package.get('lockVersion',-1),
        'native_final_gate':approval.get('verified') is True and approval.get('task_id')==package['id'] and approval.get('project_id')==project_id and approval.get('lock_version')==package.get('lockVersion') and approval.get('is_closed') is True and approval.get('status_name')=='DONE' and approval.get('gate_errors')==[],
        'owner_approval':type(change.get('journal_id')) is int and change.get('current_actor_role') in {'PM','AI_SYSTEM_OWNER'} and type(change.get('actor_id')) is int and type(change.get('at')) in {int,float} and change['at']>=(monitor.get('updated_at') or float('inf')) and change.get('to_status_id')==approval.get('status_id')}
    for role,gate in [('dev','dev_commit'),('reviewer','independent_review'),('qa','qa_passed')]:
        if role not in roles:gates.pop(gate)
    missing=[key for key,passed in gates.items() if not passed]
    status='COMPLETED' if not missing else 'AWAITING_OWNER_APPROVAL' if result.get('status')=='succeeded' and str(package.get('_links',{}).get('status',{}).get('title','')).upper().replace('_',' ')=='READY FOR RELEASE' else 'NOT_RECORDED'
    refs=[{'source_system':'AGENT_RUNTIME','source_record_id':monitor['run_id'],'run_id':monitor['run_id']}] if monitor.get('run_id') else []
    if change.get('journal_id'):refs.append({'source_system':'OPENPROJECT_JOURNAL','source_record_id':str(change['journal_id']),'run_id':monitor.get('run_id')})
    return {'status':status,'required_gates':[{'name':key,'passed':bool(passed)} for key,passed in gates.items()],
            'missing_gates':missing,'evidence_refs':refs,'owner_approval':change or None,
            'source_contract':'NATIVE_FINAL_JOURNAL_AND_EXACT_RUNTIME_REVIEW_QA_V1'}


def project_task(package, project_id, monitors, *, now=None, approval=None, event_limit=300, artifact_limit=100):
    now=time.time() if now is None else now
    if package.get('_links',{}).get('project',{}).get('href') != '/api/v3/projects/'+str(project_id):
        raise PermissionError('OBSERVER_TASK_PROJECT_MISMATCH')
    monitors=sorted(monitors,key=lambda m:(m.get('created_at') or 0,m['run_id']))
    stages={};runs=[];events=[];artifacts=[];conflicts=[];seen_events=set()
    for monitor in monitors:
        conflicts.extend(monitor.get('_source_conflicts',[]))
        identifier=monitor['run_id'];summary=monitor.get('execution_summary') or {}
        updated=max([monitor.get('updated_at') or monitor.get('created_at') or 0,summary.get('updated_at') or 0]+[e.get('timestamp') or 0 for e in monitor.get('events',[])]) or None
        heartbeat=monitor.get('_worker_seen')
        if monitor.get('state')=='RUNNING' and heartbeat:updated=max(updated or 0,heartbeat)
        age=max(0,now-updated) if updated else None
        state=STATES.get(monitor.get('state'),'UNKNOWN')
        runtime_result=monitor.get('_runtime_result') or {}
        if state=='FAILED' and runtime_result.get('status')=='blocked':state='BLOCKED'
        if state=='RUNNING' and (age is None or age>120):
            state='UNKNOWN';conflicts.append({'run_id':identifier,'reason':'RUNNING_TELEMETRY_STALE'})
        runs.append({'run_id':identifier,'state':state,'started_at':monitor.get('created_at'),'updated_at':updated,
                     'finished_at':updated if monitor.get('terminal') else None,'checkpoint':summary.get('checkpoint') or {},
                     'resume':summary.get('resume') or {'eligible':False,'reason':'NOT_RECORDED'},
                     'model_calls':(monitor.get('metrics') or {}).get('calls'),
                     'tokens_used':(monitor.get('metrics') or {}).get('tokens'),
                     'error_code':(summary.get('failure') or {}).get('raw_code'),
                     'error_message':(summary.get('failure') or {}).get('message'),
                     'blocker':summary.get('blocked_reason'), 'attempt':len(runs)+1})
        for node in monitor.get('nodes',[]):
            role=node.get('agent')
            if role in {'supervisor','final','provider','native','tools'} or not role:continue
            role_state=STATES.get(node.get('state'),'UNKNOWN')
            review=runtime_result.get('review_evidence') or {}
            if role=='reviewer' and review.get('verdict') in {'FAIL','REJECT','REJECTED'}:role_state='FAILED'
            if role=='qa' and (review.get('qa') or {}).get('status') in {'FAIL','FAILED'}:role_state='FAILED'
            if role_state=='RUNNING' and state=='UNKNOWN':role_state='UNKNOWN'
            evidence=[{'source_system':'AGENT_RUNTIME','source_record_id':identifier+':'+str(node.get('id')),
                       'run_id':identifier,'type':'STORED_AGENT_OUTPUT'}] if node.get('output') and node.get('output_origin') else []
            previous=stages.get(role,{})
            stages[role]={'stage_key':role,'stage':role,'agent_role':role,'status':role_state,
                          'started_at':node.get('started_at'),'updated_at':updated,'completed_at':node.get('ended_at'),
                          'latest_run_id':identifier,'attempts':previous.get('attempts',0)+1,
                          'summary':node.get('output') or 'NOT_RECORDED','blocker':summary.get('blocked_reason') if role_state in {'BLOCKED','FAILED','UNKNOWN'} else None,
                          'model_calls':node.get('calls'),'tokens_used':node.get('tokens'),'objective':node.get('objective'),
                          'retries':node.get('retries'),'errors':node.get('errors'),'error_code':node.get('error_code'),
                          'checkpoint':summary.get('checkpoint') or {},'resume':summary.get('resume') or {},'evidence_refs':evidence}
            if evidence:
                artifacts.append({'artifact_id':identifier+':'+str(node.get('id')),'task_id':package['id'],
                    'run_id':identifier,'type':role+'_output','title':node.get('name') or role,'content':node.get('output'),
                    'uri':None,'verification_status':'RECORDED_ARTIFACT','created_at':node.get('ended_at') or updated})
        pr=summary.get('pr_url')
        try:valid_pr=isinstance(pr,str) and urlsplit(pr).scheme=='https' and urlsplit(pr).hostname=='github.com'
        except ValueError:
            valid_pr=False;conflicts.append({'run_id':identifier,'reason':'INVALID_ARTIFACT_URI'})
        if valid_pr:
            publication=runtime_result.get('native_readback') or {}
            verified=runtime_result.get('status')=='succeeded' and publication.get('pr_url')==pr and publication.get('project_id')==project_id
            artifacts.append({'artifact_id':identifier+':pr','task_id':package['id'],'run_id':identifier,'type':'github_pr','title':'GitHub PR',
                              'uri':pr,'verification_status':'VERIFIED' if verified else 'RECORDED_ARTIFACT',
                              'verification_scope':'NATIVE_PUBLICATION_RECEIPT_NOT_CURRENT_PR_STATE','created_at':updated})
        for event in monitor.get('events',[]):
            event_id=event.get('event_id');key=(identifier,event_id)
            if not event_id or key in seen_events:continue
            seen_events.add(key)
            events.append({**event,'run_id':identifier,'task_id':package['id'],'source_system':event.get('origin') or 'AGENT_RUNTIME',
                           'source_record_id':event_id})
    events.sort(key=lambda e:(e.get('timestamp') or 0,e.get('sequence') or 0,e['run_id']))
    latest=runs[-1] if runs else {};updated=latest.get('updated_at');age=max(0,now-updated) if updated else None
    current=next((s for s in reversed(list(stages.values())) if s['status']=='RUNNING'),None)
    status=package.get('_links',{}).get('status',{}).get('title') or 'UNKNOWN'
    acceptance=acceptance_for(package,project_id,monitors[-1] if monitors else {},approval)
    if acceptance['status']=='COMPLETED':
        change=acceptance['owner_approval'];event_id='native-journal:'+str(change['journal_id'])
        events.append({'event_id':event_id,'run_id':latest.get('run_id'),'task_id':package['id'],
            'event_type':'TASK_ACCEPTANCE_COMPLETED','timestamp':change['at'],'source_system':'OPENPROJECT_JOURNAL',
            'source_record_id':str(change['journal_id'])})
        events.sort(key=lambda e:(e.get('timestamp') or 0,e.get('sequence') or 0,e['run_id'] or ''))
    latest_monitor=monitors[-1] if monitors else {};by_id={n['id']:n.get('agent') for n in latest_monitor.get('nodes',[])}
    flow_edges=[{'source':by_id[e['from']],'target':by_id[e['to']],'kind':e.get('kind','DEPENDENCY'),
                 'run_id':latest_monitor['run_id'],'evidence_ref':latest_monitor['run_id']+':edge:'+e['from']+'→'+e['to']}
                for e in latest_monitor.get('edges',[]) if by_id.get(e.get('from')) in stages and by_id.get(e.get('to')) in stages]
    snapshot={'project_id':project_id,'task_id':package['id'],'task_title':package.get('subject'),
              'version':package.get('lockVersion'),'business_status':status,'workflow_status':latest.get('state','UNKNOWN'),
              'current_stage':current['stage_key'] if current else None,'current_agent':current['agent_role'] if current else None,
              'latest_run_id':latest.get('run_id'),'started_at':runs[0]['started_at'] if runs else None,'updated_at':updated,
              'completed_at':(approval or {}).get('status_change',{}).get('at') if acceptance['status']=='COMPLETED' else None,'stages':list(stages.values()),'runs':runs,'events':events[-event_limit:],'artifacts':artifacts[-artifact_limit:],
              'flow_edges':flow_edges,'detail_counts':{'events':len(events),'artifacts':len(artifacts),'runs':len(runs)},
              'truncation':{'events':len(events)>event_limit,'artifacts':len(artifacts)>artifact_limit,'runs':len(monitors)>=50},
              'checkpoint':latest.get('checkpoint') or {},'resume':latest.get('resume') or {'eligible':False,'reason':'NOT_RECORDED'},
              'acceptance_status':acceptance['status'],'acceptance':acceptance,
              'freshness':{'observed_at':now,'source_updated_at':updated,'data_age_seconds':age,
                  'freshness_status':'UNKNOWN' if not runs else 'STALE' if age is not None and age>120 else 'PARTIAL' if conflicts else 'FRESH'},
              'source_conflicts':conflicts,'truncated':len(monitors)>=50,
              'warnings':['Stage completion refers to the recorded run only; it is not business acceptance.']}
    snapshot['revision']=digest(canonical({'version':snapshot['version'],'runs':runs,'acceptance':acceptance}))
    return public(snapshot,max(300,event_limit,artifact_limit))


def _rows(service,actor,task_id=None,limit=50,run_id=None):
    project=service.config['project_id']
    with service.store.connect() as db:
        return db.execute("""WITH records AS (SELECT a.id,a.actor,a.project,a.rowid AS record_sequence,q.created AS queue_created_at,
            CASE WHEN json_valid(a.document) AND substr(ltrim(a.document),1,1)='{' THEN a.document ELSE '{}' END document,
            CASE WHEN json_valid(t.document) AND substr(ltrim(t.document),1,1)='{' THEN t.document ELSE '{}' END task,
            CASE WHEN json_valid(q.payload) AND substr(ltrim(q.payload),1,1)='{' THEN q.payload ELSE '{}' END payload,
            CASE WHEN json_valid(r.result) AND substr(ltrim(r.result),1,1)='{' THEN r.result ELSE '{}' END result
            FROM agent_runs a JOIN agent_tasks t ON t.id=a.task_id AND t.actor=a.actor AND t.project=a.project
            LEFT JOIN ai_queue q ON q.id=a.id AND q.actor=a.actor
            LEFT JOIN ai_runs r ON r.id=a.id AND r.actor=a.actor
            WHERE a.project=? AND (a.actor=? OR ?=18)), owned AS (
            SELECT *,coalesce(CASE WHEN json_type(payload,'$.native_id')='integer' THEN json_extract(payload,'$.native_id') END,
                CASE WHEN json_type(result,'$.native_readback.child_id')='integer' THEN json_extract(result,'$.native_readback.child_id') END) owner_id FROM records)
            SELECT * FROM owned WHERE (? IS NULL OR id=?) AND (? IS NULL OR owner_id=? OR owner_id IS NULL AND EXISTS
                (SELECT 1 FROM json_each(task,'$.references') ref WHERE CASE WHEN json_valid(ref.value) THEN json_extract(ref.value,'$.work_package_id') END=?))
            ORDER BY CASE WHEN json_type(document,'$.created_at') IN ('integer','real') THEN json_extract(document,'$.created_at') ELSE queue_created_at END DESC,record_sequence DESC LIMIT ?""",
            (project,actor,actor,run_id,run_id,task_id,task_id,task_id,limit)).fetchall()


def unknown_monitor(row,reason):
    raw=json.loads(row['document'])
    times={key:raw.get(key) if type(raw.get(key)) in (int,float) else None for key in ('created_at','updated_at')}
    return {'run_id':row['id'],'state':'UNKNOWN',**times,'nodes':[],'events':[],'metrics':{},
            '_source_conflicts':[{'run_id':row['id'],'reason':reason}]}


def recorded_monitor(service,who,native,row,packages):
    from .agent_models import AgentRun,AgentTask
    from .engineering_integrity import observed_result
    from .execution_monitor import project_execution
    try:
        run=AgentRun.model_validate_json(row['document']);task=AgentTask.model_validate_json(row['task'])
    except ValidationError:
        raw=json.loads(row['document']);task=json.loads(row['task']);payload=json.loads(row['payload'] or '{}')
        refs={ref['work_package_id'] for ref in task.get('references',[]) if isinstance(ref,dict) and type(ref.get('work_package_id')) is int}
        if type(payload.get('native_id')) is int:refs.add(payload['native_id'])
        if not refs:raise PermissionError('OBSERVER_LEGACY_NATIVE_REFERENCE_REQUIRED')
        for identifier in refs:
            if identifier not in packages:packages[identifier]=native.package(identifier)
        return unknown_monitor(row,'LEGACY_AGENT_RUN_SCHEMA_UNSUPPORTED')
    if (run.actor_id,run.project_id,run.task_id)!=(row['actor'],row['project'],task.task_id) or task.actor_id!=row['actor'] or task.project_id!=row['project']:
        raise PermissionError('OBSERVER_RUN_SCOPE_MISMATCH')
    result=json.loads(row['result'] or '{}');payload=json.loads(row['payload'] or '{}')
    refs={ref.work_package_id for ref in task.references}
    if type(payload.get('native_id')) is int:refs.add(payload['native_id'])
    publication=result.get('native_readback') or {}
    if type(publication.get('child_id')) is int:refs.add(publication['child_id'])
    refs.update(v['id'] for v in publication.values() if isinstance(v,dict) and type(v.get('id')) is int)
    for identifier in refs:
        if identifier not in packages:packages[identifier]=native.package(identifier)
    events,receipts=service.store.execution_records(row['actor'],row['project'],row['id'])
    authorized={'id':row['id'],'state':'running' if run.state in {'RUNNING','QUEUED','WAITING_QUOTA','WAITING_PROVIDER','BLOCKED_KEY_OR_MODEL'} else 'done',
                'result':observed_result(result,run.state)}
    if payload.get('engine')=='openclaw' and row['project']==6:
        from .engineering_monitor import project
        monitor=project(service,who,authorized,task,run,payload,receipts,events)
        if monitor['state']=='RUNNING':
            with service.store.connect() as db:heartbeat=db.execute('SELECT seen,run_id FROM engineering_worker_state WHERE project=6').fetchone()
            if heartbeat and heartbeat['run_id']==row['id']:monitor['_worker_seen']=heartbeat['seen']
    else:monitor=project_execution(authorized,task,run,who['role'],receipts,events).model_dump()
    monitor['_runtime_result']=result
    return monitor


def task_progress(service, actor, task_id, *, native=None, who=None, packages=None, view='full', section=None, offset=0, limit=50, stage=None):
    if type(task_id) is not int or task_id<=0:raise ValueError('OBSERVER_TASK_ID_INVALID')
    if native is None:native,who=service.native_actor(actor)
    packages={} if packages is None else packages
    from .observer_reads import ReadNative,reference_ids,graph_summary,detail_page
    native=native if isinstance(native,ReadNative) else ReadNative(native,getattr(service,'_observer_metrics',None),getattr(service,'_observer_deadline',None))
    rows=_rows(service,actor,task_id)
    native.prime({task_id}|reference_ids(rows))
    if task_id not in packages:packages[task_id]=native.package(task_id)
    package=packages[task_id]
    from .native import NativeError
    monitors=[]
    for row in reversed(rows):
        try:monitors.append(recorded_monitor(service,who,native,row,packages))
        except PermissionError:monitors.append(unknown_monitor(row,'RUN_REFERENCES_NOT_VISIBLE'))
        except NativeError as error:
            if error.status not in {403,404}:raise
            monitors.append(unknown_monitor(row,'RUN_REFERENCES_NOT_VISIBLE'))
        except (ValueError,TypeError,KeyError,AttributeError) as error:
            logging.getLogger('uvicorn.error').warning('STUDIO_RECORD_INVALID run_id=%s error_class=%s',row['id'],type(error).__name__)
            monitors.append(unknown_monitor(row,'RECORDED_PROJECTION_INVALID'))
    try:approval=native.call('/api/v3/qldapm/observer_acceptance/'+str(task_id))
    except NativeError as error:
        if error.status not in {404,503}:raise
        approval=None
    snapshot=project_task(package,service.config['project_id'],monitors,approval=approval,
                          event_limit=10000 if view=='details' else 300,artifact_limit=1000 if view=='details' else 100)
    from .telegram_notifications import events
    snapshot['notification_events']=events(snapshot)
    parent=package.get('_links',{}).get('parent') or {}
    if parent.get('href'):snapshot['related_tasks']=[{'href':parent['href'],'task_id':int(parent['href'].rsplit('/',1)[-1]),'relationship':'NATIVE_PARENT','evidence_source':'OPENPROJECT_WORK_PACKAGE_PARENT'}]
    related=snapshot.setdefault('related_tasks',[])
    for row in rows:
        for ref in json.loads(row['task']).get('references',[]):
            if not isinstance(ref,dict):continue
            identifier=ref.get('work_package_id')
            if type(identifier) is not int or identifier==task_id:continue
            href='/api/v3/work_packages/'+str(identifier)
            if any(link['href']==href for link in related):continue
            planning=any(json.loads(r['payload']).get('kind')=='planning' for r in _rows(service,actor,task_id=identifier,limit=1))
            related.append({'href':href,'task_id':identifier,'relationship':'PLANNING_INPUT' if planning else 'INPUT_REFERENCE',
                            'evidence_source':'AGENT_TASK_REFERENCE','source_record_id':row['id']})
    if view=='graph':return graph_summary(snapshot)
    if view=='details':
        if stage is not None and (not isinstance(stage,str) or stage not in {s['stage_key'] for s in snapshot['stages']}):raise ValueError('OBSERVER_STAGE_INVALID')
        return detail_page(snapshot,section,offset,limit,monitors,stage)
    return snapshot


def system_snapshot(service):
    if service.config['project_id']!=6:return {'state':'NOT_RECORDED','project_id':service.config['project_id']}
    from .engineering_owner_control import observe
    from .engineering_health import integration_health
    control,queue,worker=observe(service)
    queue={**queue,'ready':None,'blocked':None,'backlog_state':'NOT_EVALUATED'}
    if not queue['active']:queue.update(state='UNKNOWN',reason_code='BACKLOG_NOT_EVALUATED')
    return {'project_id':6,'control':control,'queue':queue,'worker':worker,'integrations':integration_health(service)}


def execute(service,who,native,action,args):
    from .observer_reads import read_scope
    start=time.perf_counter()
    # Preserve the existing full Telegram contract; the new UI views keep an 8s budget.
    with read_scope(service,timeout=8 if args.get('view') else 60) as scoped:
        try:result=_execute(scoped,who,native,action,args)
        except sqlite3.OperationalError as error:
            from .native import NativeError
            raise NativeError(504 if 'interrupted' in str(error) else 503,'OBSERVER_DATABASE_DEADLINE' if 'interrupted' in str(error) else 'OBSERVER_DATABASE_UNAVAILABLE') from None
        if args.get('view'):
            result['_diagnostics']={**{k:round(v,3) for k,v in scoped._observer_metrics.items()},'observer_ms':round((time.perf_counter()-start)*1000,3)}
        return result


def _execute(service,who,native,action,args):
    actor=who['user_id']
    if action=='observer_task_progress':
        service.keys(args,{'task_id','view','section','offset','limit','stage'},{'task_id'})
        view=args.get('view','full');section=args.get('section');offset=args.get('offset',0);limit=args.get('limit',50)
        if view not in {'full','graph','details'} or type(offset) is not int or not 0<=offset<=10000 or type(limit) is not int or not 1<=limit<=50 or view=='details' and section not in {'overview','events','artifacts','runs','technical'}:raise ValueError('OBSERVER_VIEW_INVALID')
        return task_progress(service,actor,args['task_id'],native=native,who=who,view=view,section=section,offset=offset,limit=limit,stage=args.get('stage'))
    if action=='observer_run_details':
        service.keys(args,{'run_id'},{'run_id'})
        identifier=args['run_id']
        if not isinstance(identifier,str) or str(uuid.UUID(identifier))!=identifier:raise ValueError('OBSERVER_RUN_ID_INVALID')
        # Existing monitor performs exact actor/project/Native visibility checks.
        rows=_rows(service,actor,run_id=identifier,limit=1)
        if not rows:raise PermissionError('OBSERVER_RUN_NOT_FOUND')
        monitor=recorded_monitor(service,who,native,rows[0],{})
        return public({key:value for key,value in monitor.items() if not key.startswith('_')})
    service.keys(args,{'limit','query','state','summary_only','view','offset'},set())
    if args.get('view')=='list':
        from .observer_reads import light_list
        return light_list(service,actor,native,args)
    if args.get('view','full')!='full':raise ValueError('OBSERVER_VIEW_INVALID')
    brief=args.get('summary_only',False)
    if type(brief) is not bool:raise ValueError('OBSERVER_FILTER_INVALID')
    if brief:return {'items':[],'system':system_snapshot(service),'observed_at':time.time(),'truncated':False}
    limit=args.get('limit',20);query=args.get('query','');state=args.get('state')
    if type(limit) is not int or not 1<=limit<=50 or not isinstance(query,str) or len(query)>160 or state is not None and state not in set(STATES.values())|{'UNKNOWN','ALL'}:
        raise ValueError('OBSERVER_FILTER_INVALID')
    rows=_rows(service,actor,limit=200)
    ids=[]
    for row in rows:
        payload=json.loads(row['payload'] or '{}');task=json.loads(row['task'])
        targets=[payload['native_id']] if type(payload.get('native_id')) is int else [r['work_package_id'] for r in task.get('references',[])]
        published=(json.loads(row['result'] or '{}').get('native_readback') or {}).get('child_id')
        if type(published) is int and published not in targets:targets.insert(0,published)
        ids.extend(identifier for identifier in targets if identifier not in ids)
    from .observer_reads import ReadNative,reference_ids
    native=ReadNative(native,getattr(service,'_observer_metrics',None),getattr(service,'_observer_deadline',None))
    native.prime(set(ids)|reference_ids(rows))
    items=[];packages={}
    for identifier in ids:
        if len(items)>=limit:break
        try:
            item=native.package(identifier);packages[identifier]=item
        except PermissionError:continue
        except Exception as error:
            from .native import NativeError
            if not isinstance(error,NativeError) or error.status not in {403,404}:raise
            continue
        if query and query.casefold() not in (str(identifier)+' '+item.get('subject','')).casefold():continue
        snapshot=task_progress(service,actor,identifier,native=native,who=who,packages=packages)
        if state not in {None,'ALL'} and snapshot['workflow_status']!=state:continue
        items.append(snapshot)
    return {'items':items,'system':system_snapshot(service),'observed_at':time.time(),'limit':limit,'truncated':len(rows)>=200 or len(ids)>limit}

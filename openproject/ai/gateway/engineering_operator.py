"""OS-authenticated host worker operations; not a model tool or public API."""
import json
import re
import sys
import time
import uuid
from pathlib import Path

from . import engineering
from .agent_models import AgentTask, RunScope
from .agent_registry import get_agent_registry, engineering_profile
from .service import Service
from .store import Store,canonical,digest

ACTOR=20


def usage_receipt_id(run_id,step,index,receipt_scope):
    if str(uuid.UUID(receipt_scope))!=receipt_scope:raise ValueError('ENGINEERING_RECEIPT_SCOPE_REQUIRED')
    return str(uuid.uuid5(uuid.UUID(run_id),receipt_scope+':'+step+':'+str(index)))


def native_once(service,native,run_id,kind,path,method,payload,*,fence=None):
    from .engineering_fencing import check,CURRENT
    fence=fence or CURRENT.get()
    if fence:check(service.store,fence)
    key='engineering-'+run_id+'-'+kind
    command={'action':'engineering_native_'+kind,'project_id':6,'path':path,'method':method,'payload':payload}
    with service.store.connect() as db:
        receipts=db.execute('SELECT key,state,payload,result FROM requests WHERE actor=? AND (key=? OR key GLOB ?) ORDER BY rowid DESC',(ACTOR,key,key+'-retry-*')).fetchall()
    for receipt in receipts:
        previous=json.loads(receipt['payload'])
        if any(previous.get(k)!=command[k] for k in ['action','project_id','path','method']):raise ValueError('ENGINEERING_NATIVE_RECEIPT_SCOPE')
        if receipt['state']=='done':return json.loads(receipt['result'])
        if receipt['state']!='rejected':raise ValueError('OUTCOME_UNKNOWN_RECONCILE_FIRST')
    if receipts:key+='-retry-'+str(len(receipts))
    old=service.store.begin(ACTOR,key,command)
    if old is not None:return old
    if fence:check(service.store,fence)
    try:result=native.call(path,method,payload)
    except Exception as error:
        from .native import NativeError
        not_sent=isinstance(error,NativeError) and error.status==503 and str(error)=='REQUEST_DEADLINE_EXCEEDED'
        if isinstance(error,NativeError) and (error.status in {400,401,403,404,409,422} or not_sent):
            with service.store.connect() as db:db.execute("UPDATE requests SET state='rejected',result=? WHERE actor=? AND key=?",(canonical({'status':error.status,'outcome':'REJECTED_NO_WRITE'}),ACTOR,key))
            if not_sent:raise
            raise ValueError('ENGINEERING_NATIVE_REJECTED_'+str(error.status)) from None
        raise
    if fence:check(service.store,fence)
    service.store.finish(ACTOR,key,result)
    service.store.record(ACTOR,'engineering_native',run_id,kind)
    return result


def operation(service,op,args):
    from .engineering_fencing import bound,check
    if op=='claim':
        if str(uuid.UUID(args['worker_id']))!=args['worker_id']:raise ValueError('ENGINEERING_WORKER_ID_INVALID')
        return engineering.claim(service,ACTOR,worker_id=args['worker_id'])
    run_id=args.get('run_id') or (args.get('active_run_id') if op=='heartbeat' else None)
    fence={'run_id':run_id,'worker_id':args.get('worker_id'),'claim_token':args.get('claim_token')}
    if op=='signal':
        try:valid=check(service.store,fence)['claim_valid']
        except ValueError:valid=False
        return {**_operation(service,op,args),'claim_valid':valid}
    if op=='guard':
        check(service.store,fence)
        from .engineering_lifecycle import signal
        state=signal(service.store,ACTOR,run_id)
        if state['cancel_requested']:raise ValueError('ENGINEERING_CANCELLED')
        if state['mode'] not in {'RUN_ONCE','AUTO'}:raise ValueError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
        if time.time()>=state['deadline']:raise ValueError('ENGINEERING_DEADLINE_EXCEEDED')
        return {'claim_valid':True}
    if run_id and op not in {'resume_reconciled','resume','cancel'}:
        with bound(fence,service.store):
            check(service.store,fence)
            return _operation(service,op,args)
    return _operation(service,op,args)


def _operation(service,op,args):
    from . import engineering_lifecycle as lifecycle
    if op=='heartbeat':return lifecycle.heartbeat(service.store,args['worker_id'],args.get('active_run_id'))
    if op=='signal':return lifecycle.signal(service.store,ACTOR,args['run_id'])
    native,who=engineering.authorized(service,ACTOR)
    if op=='source':
        item=native.package(379)
        return {'project_id':6,'native_id':379,'lock_version':item['lockVersion'],'subject':item['subject']}
    if op=='status':return engineering.status(service,ACTOR)
    if op=='admit':return engineering.admit(service,ACTOR,args['arguments'],args['key'])
    if op=='resume_reconciled':return engineering.resume_reconciled(service,ACTOR,args['run_id'],args['result_sha256'],args.get('artifact'),args.get('rework_feedback'))
    if op=='control':return engineering.control(service,ACTOR,args['mode'])
    if op=='cancel':return lifecycle.cancel(service,ACTOR,args['run_id'])
    if op=='resume':return lifecycle.resume(service,ACTOR,args['run_id'],args['checkpoint_version'])
    if op=='github_sync':
        from .engineering_github_sync import reconcile_github_with_openproject
        return reconcile_github_with_openproject(service, native, actor=ACTOR, repo=args.get('repo', 'Luim3141/mini-task-manager'))
    run_id=args['run_id'];run=service.store.agent_run(ACTOR,6,run_id)
    with service.store.connect() as db:
        row=db.execute('SELECT state,payload FROM ai_queue WHERE id=? AND actor=?',(run_id,ACTOR)).fetchone()
    if not row or json.loads(row['payload']).get('engine')!='openclaw':
        raise PermissionError('ENGINEERING_RUN_REQUIRED')
    contract=json.loads(row['payload'])
    if op=='finish':return engineering.finish(service,ACTOR,run_id,args['result'])
    if op=='checkpoint':return lifecycle.save(service,ACTOR,run_id,args['document'])
    if row['state']!='executing' or (op not in {'usage','delivery_note'} and time.time()>=contract['deadline']):
        raise ValueError('ENGINEERING_DEADLINE_OR_NOT_EXECUTING')
    if op not in {'usage','delivery_note'} and lifecycle.signal(service.store,ACTOR,run_id)['mode'] not in {'RUN_ONCE', 'AUTO'}:
        raise ValueError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
    if op=='generate_plan':
        from .engineering_planning import generate
        return generate(service,ACTOR,run_id,contract)
    if op=='delivery_note':
        error=args['error']
        if not re.fullmatch('[A-Z][A-Z0-9_]{0,100}',error):error='ENGINEERING_CHECKPOINT_SAVED'
        native_once(service,native,run_id,'blocker-'+str(contract.get('recovery_count',0)),
            f"/api/v3/work_packages/{contract['native_id']}/activities",'POST',{'comment':{'format':'markdown','raw':f"WP #{contract['native_id']} — Engineering checkpoint: {error}. Run {run_id}; artifacts giữ nguyên, cần resume/reconcile theo checkpoint. Không đánh dấu Done."}})
        return {'project_id':6,'native_id':contract['native_id'],'error':error}
    if op=='progress':return engineering.progress(service,ACTOR,run_id,args['stage'],args.get('details',{}))
    if op=='context':
        item=native.package(contract['native_id'])
        if not lifecycle.source_matches(service.store,ACTOR,run_id,contract,item):
            raise ValueError('ENGINEERING_SOURCE_STALE')
        scope=RunScope(**{k:getattr(run,k) for k in RunScope.model_fields})
        task=service.store.agent_task(ACTOR,6,run.task_id)
        registry=get_agent_registry()
        outputs={role:registry.get_handler(role).run(task,scope,[item]).model_dump() for role in ['pm','ba']}
        knowledge=service.knowledge(who,native,'knowledge_search',{'query':'Mini Task Manager requirements','native_ids':[379],'limit':3})
        if not knowledge.get('items'):
            service.execute_actor(ACTOR,{'action':'knowledge_ingest','arguments':{'id':379},
                'idempotency_key':'engineering-context-'+run_id})
            service.sync_canonical_native(ACTOR,379)
            knowledge=service.knowledge(who,native,'knowledge_search',{'query':'Mini Task Manager','native_ids':[379],'limit':3})
        if not knowledge.get('items'):raise ValueError('ENGINEERING_CONTEXT_RETRIEVAL_EMPTY')
        selected=contract.get('definition') or engineering.UNITS[contract['unit']]
        plan={'unit':contract['unit'],'title':selected['title'],'spec_sha256':contract['spec_sha256'],
            'steps':['Define AC/API','Implement one feature in isolated worktree','Independent review','Independent tests','Publish PR and progress','Reindex authorized Native evidence'],
            'acceptance':selected['acceptance'],
            'interface':'task_manager.app.create_app(database_path); pytest; Python FastAPI + stdlib sqlite3',
            'permission':'demo repository and Project6 only; no merge/deploy; completion of unit is not WP379 DONE',
            'verification':'trusted external acceptance + repo pytest on exact tree; independent reviewer session'}
        if selected.get('plan_id'):
            with service.store.connect() as db:stored=db.execute('SELECT document FROM engineering_plans WHERE id=? AND actor=?',(selected['plan_id'],ACTOR)).fetchone()
            if not stored:raise ValueError('ENGINEERING_PLAN_HANDOFF_REQUIRED')
            planning=json.loads(stored[0]);plan.update(functional_specification=planning['ba'],pm_plan=planning['pm'],feedback=selected.get('feedback',''))
        return {'contract':contract,'plan':plan,'agent_outputs':outputs,'knowledge':knowledge,
            'profiles':{role:engineering_profile(role) for role in ['supervisor','pm','ba','dev','reviewer','qa']}}
    if op=='reserve':
        count=args['calls']
        if type(count) is not int or not 1<=count<=12:raise ValueError('ENGINEERING_CALL_BUDGET')
        from .engineering_observability import policy
        rules=policy(service)
        with service.store.connect() as db:
            used=db.execute("SELECT count(*) FROM gemini_call_receipts WHERE run_id=? AND json_extract(document,'$.phase')='generateContent'",(run_id,)).fetchone()[0]
        count=min(count,rules['attempt_calls'],rules['task_calls']-used)
        if count<=0:raise ValueError('ENGINEERING_CUMULATIVE_BUDGET_EXHAUSTED')
        policy=service.gemini.settings()
        if policy['model']!='gemini-3.5-flash-lite':raise ValueError('ENGINEERING_PROVIDER_POLICY_CHANGED')
        if args.get('deferred') is True:
            return {'project':policy['project'],'reservations':[],'model':policy['model'],'calls':count,'deferred':True}
        ids=[]
        def waiting(message,retry_at,queue_state='WAITING_QUOTA'):
            if lifecycle.signal(service.store,ACTOR,run_id)['mode'] not in {'RUN_ONCE', 'AUTO'}:raise ValueError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
            service.store.progress_run(ACTOR,run_id,{'status':'running','stage':queue_state,'text':message,'retry_at':retry_at})
        for _ in range(count):
            if lifecycle.signal(service.store,ACTOR,run_id)['mode'] not in {'RUN_ONCE', 'AUTO'}:raise ValueError('ENGINEERING_PAUSED_CHECKPOINT_REQUIRED')
            ids.append(service.gemini.reserve_budget(service.store,policy,16000,min(time.monotonic()+75,time.monotonic()+max(0,contract['deadline']-time.time())),waiting))
        return {'project':policy['project'],'reservations':ids,'model':policy['model'],'calls':count}
    if op=='usage':
        project=args['reservation']['project'];ids=args['reservation']['reservations']
        receipts=args['receipts']
        if args['reservation'].get('deferred') is True:
            with service.store.connect() as db:
                count=db.execute("SELECT count(*) FROM gemini_call_receipts WHERE run_id=? AND json_extract(document,'$.session_id')=?",(run_id,args['receipt_scope'])).fetchone()[0]
            if count!=len(receipts):raise ValueError('ENGINEERING_PROVIDER_RECEIPT_RECONCILIATION_REQUIRED')
            return {'recorded':count,'source':'PER_REQUEST_SHARED_PROJECT_LEDGER','unused_reservations_retained':0}
        if len(receipts)>len(ids):raise ValueError('ENGINEERING_BUDGET_RECEIPTS_INVALID')
        for i,receipt in enumerate(receipts):
            usage=receipt.get('usage') or {}
            if type(usage.get('promptTokenCount')) is int:service.store.settle_gemini_input(ids[i],project,usage['promptTokenCount'])
            identifier=usage_receipt_id(run_id,args['step'],i,args['receipt_scope'])
            service.store.provider_receipt({'id':identifier,'project':project,'actor':ACTOR,'run_id':run_id,
                'provider':'google','model':args['reservation']['model'],'source':'openclaw-gate',**receipt,
                'session_id':args['receipt_scope'],'step':args['step'],'call_cap':args['reservation'].get('calls',len(ids)),
                'agent':'reviewer' if args['step'].startswith('review') else 'qa' if args['step'].startswith('qa') else 'dev',
                'phase':'countTokens' if receipt['phase']=='countTokens' else 'generateContent',
                'state':'LIVE_SUCCESS' if receipt['http_status']==200 else 'PROVIDER_ERROR',
                'at':receipt['started'],'completed_at':receipt['finished'],
                'duration_seconds':round(receipt['finished']-receipt['started'],3),'attempt':0})
        return {'recorded':len(receipts),'unused_reservations_retained':len(ids)-len(receipts)}
    if op=='publish_native':
        result=args['result']
        if not re.fullmatch('[a-f0-9]{40}',result.get('head_sha','')) or not re.fullmatch(r'https://github.com/Luim3141/mini-task-manager/pull/[1-9][0-9]*',result.get('pr_url','')):
            raise ValueError('ENGINEERING_PUBLISH_ARTIFACT_REQUIRED')
        item=native.package(contract['native_id'])
        if not lifecycle.source_matches(service.store,ACTOR,run_id,contract,item):raise ValueError('ENGINEERING_SOURCE_STALE')
        description='Engineering unit '+contract['unit']+'\n\n'+json.dumps(result,ensure_ascii=False,indent=2)
        selected=contract.get('definition') or engineering.UNITS[contract['unit']]
        payload={'subject':'[AI unit] '+selected['title'],
            'description':{'format':'markdown','raw':description},'_links':{'project':{'href':'/api/v3/projects/6'},
            'parent':{'href':'/api/v3/work_packages/379'},'type':item['_links']['type']}}
        if contract['native_id']!=379:
            child=native_once(service,native,run_id,'child',f"/api/v3/work_packages/{item['id']}",'PATCH',{'lockVersion':item['lockVersion'],'description':{'format':'markdown','raw':item.get('description',{}).get('raw','')+'\n\n'+description}})
        else:
            form=native.call('/api/v3/projects/6/work_packages/form','POST',payload)
            errors=form.get('_embedded',{}).get('validationErrors',{})
            if errors:raise ValueError('ENGINEERING_NATIVE_FORM_REJECTED')
            child=native_once(service,native,run_id,'child','/api/v3/work_packages','POST',payload)
        child=native.package(child['id'])
        note={'comment':{'format':'markdown','raw':'Engineering unit verified; parent WP remains incomplete.\n'+description}}
        native_once(service,native,run_id,'progress','/api/v3/work_packages/379/activities','POST',note)
        # No automatic DONE transition: this first unit covers only part of WP379.
        return {'child_id':child['id'],'child_version':child['lockVersion'],
            'parent':{'id':379,'version':native.package(379)['lockVersion']},'project_id':6,'pr_url':result['pr_url']}
    if op=='knowledge':
        ids=[379,args['child_id']]
        result=[]
        for identifier in ids:
            ingested=service.execute_actor(ACTOR,{'action':'knowledge_ingest','arguments':{'id':identifier},
                'idempotency_key':'engineering-rag-'+run_id+'-'+str(identifier)})['result']
            canonical_result=service.sync_canonical_native(ACTOR,identifier)
            if ingested.get('vector_indexed') is not True or canonical_result.get('vector_indexed') is not True:
                raise ValueError('ENGINEERING_KNOWLEDGE_NOT_INDEXED')
            result.append(ingested)
        child=native.package(args['child_id'])
        found=service.knowledge(who,native,'knowledge_search',{'query':child['subject'],'native_ids':[args['child_id']],'limit':5})
        if not any(item.get('native_id')==args['child_id'] and item.get('lock_version')==child['lockVersion']
                   and item.get('citation')==f"/work_packages/{args['child_id']}" for item in found.get('items',[])):
            raise ValueError('ENGINEERING_KNOWLEDGE_CHILD_NOT_VERIFIED')
        return {'project_id':6,'ingestion':result,'retrieval':found}
    raise ValueError('ENGINEERING_OPERATOR_OPERATION_DENIED')


def main():
    try:
        request=json.loads(sys.stdin.buffer.read(131073))
        if len(canonical(request))>131072 or set(request)!={'op','args'}:raise ValueError('OPERATOR_REQUEST_INVALID')
        root=Path('/state');store=Store(root);config=json.loads((root/'config.json').read_text())
        service=engineering.scoped_service(Service(store,config,'/workspaces'),6)
        from .agent_trace import bind_run,reset_run
        token=None
        try:
            if request['args'].get('run_id') and request['op'] not in {'resume_reconciled','resume','cancel','signal'}:
                token=bind_run(store,ACTOR,6,request['args']['run_id'])
            result=operation(service,request['op'],request['args'])
        finally:reset_run(token)
        print(json.dumps({'ok':True,'result':result},ensure_ascii=False))
    except Exception as error:
        # Error code only: Native exceptions/config may contain credential-adjacent data.
        code=str(error).split(';')[0]
        if not re.fullmatch('[A-Z][A-Z0-9_]{0,100}',code):code=type(error).__name__
        print(json.dumps({'ok':False,'error':code}));return 1
    return 0


if __name__=='__main__':sys.exit(main())

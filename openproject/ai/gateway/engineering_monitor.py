"""Engineering projection into the existing Execution Monitor, without model calls."""
import json

from .engineering_lifecycle import load
from .execution_monitor import ExecutionMonitor,MonitorNode,observed
from .presentation import safe_text


def project(service,who,run,task,agent_run,contract,receipts,events,*,native=None):
    from .engineering_integrity import observed_result
    result=observed_result(run.get('result') or {},agent_run.state);checkpoint=load(service.store,run['id']) or {}
    state={'paused':'PAUSED','cancelled':'CANCELLED','blocked':'FAILED','succeeded':'COMPLETED'}.get(result.get('status'),agent_run.state)
    terminal=run['state']!='running'
    from .engineering_observability import describe_run
    summary = describe_run(service, {'id':run['id'],'native_id':contract['native_id'],'unit':contract['unit'],
        'created_at':agent_run.created_at,'queue_state':'finished' if terminal else 'executing' if agent_run.state=='RUNNING' else 'queued',
        'result':result,'checkpoint':checkpoint})
    roles=['ba','pm'] if contract.get('kind')=='planning' else ['dev','reviewer','qa']
    names={'ba':'BA · Requirements Analyst','pm':'PM · Senior Project Manager','dev':'Dev · OpenClaw','reviewer':'Reviewer · Independent','qa':'QA · Evidence Collector'}
    outputs={}
    if contract.get('kind')=='planning':
        with service.store.connect() as db:stored=db.execute('SELECT document FROM engineering_plans WHERE id=? AND actor=?',(run['id'],who['user_id'])).fetchone()
        plan=json.loads(stored[0]) if stored else {}
        outputs={role:json.dumps(plan[role],ensure_ascii=False) for role in roles if plan.get(role)}
    else:
        if result.get('files_changed'):outputs['dev']=json.dumps({'files':result['files_changed'],'head_sha':result.get('head_sha'),'terminal_partial':result.get('dev_execution')},ensure_ascii=False)
        if result.get('review_evidence'):outputs['reviewer']=json.dumps(result['review_evidence'],ensure_ascii=False)
        if result.get('test_evidence'):outputs['qa']=json.dumps({'host_test':result['test_evidence'],'qa':result.get('review_evidence',{}).get('qa')},ensure_ascii=False)
    nodes=[MonitorNode(id='supervisor',agent='supervisor',name='QLDAPM Supervisor',assigned_by=None,
        objective='Atomic claim, role delegation, bounded handoff/recovery và publication.',state=state,
        mode='LOCAL_DETERMINISTIC',planning_method='FIXED_ENGINEERING_CONTRACT',calls=0,
        output=safe_text(result.get('text')) or None,output_origin='STORED_ENGINEERING_RECEIPT')]
    edges=[];sources=[ref.model_dump() for ref in task.references]
    completed=set(checkpoint.get('completed_steps',[]))
    prefix={'dev':('dev-','rework-'),'reviewer':('review-',),'qa':('qa-',)}
    for i,role in enumerate(roles,1):
        usage=observed([r for r in receipts if r.get('agent')==role])
        role_events=[e for e in events if e.get('agent_id')==role]
        starts=[e['timestamp'] for e in role_events if e['event_type'] in {'AGENT_STARTED','REVIEW_STARTED'}]
        ends=[e['timestamp'] for e in role_events if e['event_type'] in {'AGENT_COMPLETED','AGENT_FAILED','REVIEW_COMPLETED'}]
        done=bool(outputs.get(role)) or any(step.startswith(prefix.get(role,())) for step in completed)
        node_state='RUNNING' if summary.get('current_agent')==role and not terminal else 'COMPLETED' if done else 'UNKNOWN' if usage['calls'] else 'NOT_RUN' if terminal else 'QUEUED'
        if terminal and not done and str(checkpoint.get('stage','')).startswith(prefix.get(role,())):node_state=state
        if role=='dev' and result.get('dev_execution',{}).get('status')=='PARTIAL_ARTIFACT_VERIFIED':node_state='PARTIAL'
        nodes.append(MonitorNode(id=str(i),agent=role,name=names[role],objective=role+' contract: '+contract.get('definition',{}).get('title',contract['unit']),
            dependencies=[str(i-1)] if i>1 else [],level=i,state=node_state,
            started_at=min(starts) if starts else None,ended_at=max(ends) if ends else None,
            duration_seconds=round(max(ends)-min(starts),3) if starts and ends else None,
            mode=usage['mode'],model=usage['model'],calls=usage['calls'],tokens=usage['tokens'],retries=usage['retries'],errors=usage['errors'],
            model_duration_seconds=usage['model_duration_seconds'],output=safe_text(outputs.get(role)) or None,
            output_origin='STORED_ENGINEERING_ARTIFACT' if outputs.get(role) else None,
            input_source_ids=[ref.work_package_id for ref in task.references],references=sources,
            validation='INDEPENDENT_EXACT_REVISION' if role=='reviewer' and result.get('review_evidence') else None))
        edges.append({'from':'supervisor','to':str(i),'kind':'ASSIGNMENT'})
        if i>1:edges.append({'from':str(i-1),'to':str(i),'kind':'DEPENDENCY'})
    nodes.append(MonitorNode(id='final',agent='final',name='Delivery artifacts',objective='GitHub/Native/knowledge readback đã lưu; không suy luận lại.',assigned_by='supervisor',dependencies=[str(len(roles))],level=len(roles)+1,state=state if terminal else 'QUEUED',
        mode='LOCAL_DETERMINISTIC',output=safe_text(json.dumps({key:result.get(key) for key in ['text','head_sha','pr_url','native_readback','knowledge_readback','error']},ensure_ascii=False)),output_origin='STORED_ENGINEERING_RECEIPT'))
    edges.append({'from':str(len(roles)),'to':'final','kind':'DEPENDENCY'})
    metrics=observed(receipts);metrics.update(agents=len(roles)+1,completed=sum(n.state=='COMPLETED' for n in nodes if n.agent!='final'),running=sum(n.state=='RUNNING' for n in nodes),steps=len(roles))
    projected_events=[dict(event) for event in events]
    for receipt in receipts:
        for event_type,at in [('MODEL_REQUEST_STARTED',receipt.get('at')),('MODEL_RESPONSE_RECEIVED',receipt.get('completed_at'))]:
            if at is not None:
                projected_events.append({'event_id':receipt['id']+':'+event_type,'run_id':agent_run.run_id,'trace_id':agent_run.trace_id,
                    'event_type':event_type,'agent_id':receipt.get('agent'),'timestamp':at,'phase':receipt.get('phase'),
                    'status':receipt.get('state'),'receipt_id':receipt['id'],'origin':'RECORDED_PROVIDER_RECEIPT'})
    projected_events.sort(key=lambda e:(e['timestamp'],e['event_id']))
    for i,event in enumerate(projected_events,1):event['sequence']=i
    document = ExecutionMonitor(run_id=agent_run.run_id,trace_id=agent_run.trace_id,actor_id=who['user_id'],actor_role=who['role'],project_id=6,
        request=task.instruction,state=state,terminal=terminal,mode=metrics['mode'],model=metrics['model'],created_at=agent_run.created_at,updated_at=agent_run.updated_at,
        duration_seconds=round(agent_run.updated_at-agent_run.created_at,3) if terminal else None,nodes=nodes,edges=edges,events=projected_events,metrics=metrics,sources=sources,
        final_output=safe_text(result.get('text')) or None,warnings=['Engineering outputs là artifacts của revision đã lưu; calls/usage bao gồm các attempts được giữ. Không là chứng nhận UAT.']).model_dump()

    document['execution_summary'] = summary
    if native is not None:
        item=native.package(contract['native_id'])
        summary['native_status']=item.get('_links',{}).get('status',{}).get('title')
        summary['title']=item.get('subject') or summary['title']
    return document

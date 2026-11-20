"""Read-only projection of authorized canonical runs, plans, outputs and receipts."""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .agent_models import AgentResult, ExecutionPlan
from .presentation import safe_text

NAMES={'supervisor':'Supervisor','pm':'PM Agent','ba':'BA Agent','fe':'FE Agent','be':'BE Agent','dev':'Developer Agent (legacy)','qa':'QA Agent','reviewer':'Reviewer','final':'Báo cáo tổng hợp'}
TERMINAL={'COMPLETED','FAILED','CANCELLED','STALE','PARTIAL','REVIEW'}


class MonitorNode(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    id: str
    agent: str
    name: str
    objective: str
    assigned_by: str | None='supervisor'
    dependencies: list[str]=Field(default_factory=list)
    state: str='UNKNOWN'
    level: int=0
    started_at: float | None=None
    ended_at: float | None=None
    duration_seconds: float | None=None
    model_duration_seconds: float | None=None
    mode: str | None=None
    model: str | None=None
    planning_method: str | None=None
    calls: int=0
    tokens: int | None=None
    retries: int=0
    errors: int=0
    error_code: str | None=None
    output: str | None=None
    output_origin: str | None=None
    references: list[dict]=Field(default_factory=list)
    validation: str | None=None
    input_source_ids: list[int]=Field(default_factory=list)
    limitations: str | None=None


class ExecutionMonitor(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    schema_version: Literal[1]=1
    run_id: str
    trace_id: str
    actor_id: int
    actor_role: str
    project_id: int
    request: str | None=None
    state: str
    terminal: bool
    mode: str | None=None
    model: str | None=None
    created_at: float
    updated_at: float
    duration_seconds: float | None=None
    nodes: list[MonitorNode]=Field(default_factory=list)
    edges: list[dict]=Field(default_factory=list)
    events: list[dict]=Field(default_factory=list)
    metrics: dict=Field(default_factory=dict)
    sources: list[dict]=Field(default_factory=list)
    final_output: str | None=None
    warnings: list[str]=Field(default_factory=list)


def observed(receipts):
    generations=[r for r in receipts if r.get('phase')=='generateContent']
    success=[r for r in generations if r.get('state') in {'LIVE_SUCCESS','MOCK_SUCCESS'}]
    mode='LIVE_GEMINI' if any(r['state']=='LIVE_SUCCESS' for r in success) else 'MOCK_TEST' if success else None
    usage=[r['usage'] for r in generations if isinstance(r.get('usage'),dict) and type(r['usage'].get('totalTokenCount')) is int]
    durations=[r['duration_seconds'] for r in generations if type(r.get('duration_seconds')) in {int,float}]
    return {'calls':len(generations),'tokens':sum(r['totalTokenCount'] for r in usage) if usage else None,
        'usage_complete':len(usage)==len(generations),'mode':mode,'model':next((r.get('model') for r in success),None),
        'retries':sum(r.get('attempt',0)>0 for r in receipts),
        'errors':sum(r.get('state') in {'PROVIDER_ERROR','INVALID_RESPONSE'} for r in receipts),
        'model_duration_seconds':round(sum(durations),3) if durations else None}


def layers(steps):
    ids={s.step_id for s in steps}
    if len(ids)!=len(steps) or any(set(s.dependencies)-ids or s.step_id in s.dependencies for s in steps):
        raise ValueError('EXECUTION_PLAN_INVALID_DEPENDENCY')
    levels={};pending={s.step_id:s for s in steps}
    while pending:
        ready=[s for s in pending.values() if set(s.dependencies)<=levels.keys()]
        if not ready:raise ValueError('EXECUTION_PLAN_CYCLE')
        for s in ready:
            levels[s.step_id]=1+max((levels[d] for d in s.dependencies),default=0);del pending[s.step_id]
    return levels


def project_execution(run,task,agent_run,role,receipts,events):
    """Caller MUST first use Service.get_ai_run (fresh Native ACL/version)."""
    r=run.get('result') or {};state=agent_run.state
    if r.get('stale') or r.get('status')=='stale':state='STALE'
    elif r.get('error')=='AGENT_CANCELLED':state='CANCELLED'
    elif r.get('status')=='partial':state='PARTIAL'
    elif run['state']=='running':
        state=agent_run.state if agent_run.state!='RUNNING' else r.get('queue_state') if r.get('queue_state') in {'PLANNING','REVIEWING','WAITING_QUOTA','WAITING_PROVIDER','BLOCKED_KEY_OR_MODEL'} else 'RUNNING'
        review_events=[e for e in events if e.get('event_type') in {'REVIEW_STARTED','REVIEW_COMPLETED'}]
        if review_events and review_events[-1]['event_type']=='REVIEW_STARTED':state='REVIEWING'
    base=dict(run_id=agent_run.run_id,trace_id=agent_run.trace_id,actor_id=agent_run.actor_id,
        actor_role=role,project_id=agent_run.project_id,state=state,terminal=state in TERMINAL,
        created_at=agent_run.created_at,updated_at=agent_run.updated_at)
    if state=='STALE':return ExecutionMonitor(**base,warnings=['Nguồn hoặc quyền đã đổi; nội dung cũ được ẩn.'])
    metrics=observed(receipts)
    if r.get('engine')=='local_supervisor':metrics.update(mode='LOCAL_DETERMINISTIC',tokens=0)
    plan=ExecutionPlan.model_validate(r['plan']) if r.get('plan') else None
    if plan and (plan.actor_id!=agent_run.actor_id or plan.project_id!=agent_run.project_id or plan.task_id!=agent_run.task_id):
        raise PermissionError('EXECUTION_PLAN_SCOPE_MISMATCH')
    steps=plan.steps if plan else [];levels=layers(steps)
    outputs={}
    for item in r.get('agent_outputs',[]):
        output=AgentResult.model_validate(item['result'])
        if any(getattr(output,k)!=getattr(agent_run,k) for k in ['run_id','task_id','actor_id','project_id','trace_id']):
            raise PermissionError('EXECUTION_OUTPUT_SCOPE_MISMATCH')
        outputs[item['step_id']]=output
    objectives={a['agent']:a['objective'] for a in (r.get('gemini_plan') or {}).get('agents',[])}
    warnings=[];legacy={}
    if not outputs and state in {'COMPLETED','REVIEW'} and r.get('agent_result') and metrics['mode']=='LIVE_GEMINI':
        # Legacy host aggregation used these exact labels. Ambiguous text stays unavailable.
        summary=r['agent_result']['summary'];labels=[s.agent.upper()+':\n' for s in steps if s.agent!='reviewer']
        matches=list(re.finditer(r'(?m)^(PM|BA|FE|BE|DEV|QA):\n',summary))
        if [m[0] for m in matches]==labels:
            for i,m in enumerate(matches):
                end=matches[i+1].start() if i+1<len(matches) else summary.find('\n\nReviewer local:',m.end())
                if end<0:end=len(summary)
                legacy[m[1].lower()]=summary[m.end():end].strip()
        warnings.append('Run này không có đầy đủ execution events. Output specialist được trích từ bản tổng hợp đã lưu khi phân tách được chắc chắn; thời gian agent không được ước lượng.')
    nodes=[];edges=[]
    supervisor_receipts=[x for x in receipts if x.get('agent')=='supervisor'];sup=observed(supervisor_receipts)
    planning=[x for x in events if x.get('event_type')=='PLANNING_STARTED'];planned=[x for x in events if x.get('event_type')=='PLAN_CREATED']
    sup_state='COMPLETED' if plan else state if base['terminal'] else 'PLANNING' if planning or supervisor_receipts else 'QUEUED' if state=='QUEUED' else state
    nodes.append(MonitorNode(id='supervisor',agent='supervisor',name='Supervisor',assigned_by=None,
        objective='Lập kế hoạch và điều phối các nhiệm vụ; các đường phụ thuộc không phải quyền gọi agent.',state=sup_state,
        started_at=planning[0]['timestamp'] if planning else None,ended_at=planned[-1]['timestamp'] if planned else None,
        duration_seconds=round(planned[-1]['timestamp']-planning[0]['timestamp'],3) if planning and planned else None,
        planning_method='GEMINI_MODEL_PLAN' if r.get('gemini_plan') else 'LOCAL_REGISTERED_ROUTING' if plan else None,
        mode=sup['mode'] or ('LOCAL_DETERMINISTIC' if plan else None),model=sup['model'],calls=sup['calls'],tokens=sup['tokens'],retries=sup['retries'],errors=sup['errors'],
        output=safe_text((r.get('gemini_plan') or {}).get('reasoning_summary')) or None,output_origin='STORED_PLAN' if r.get('gemini_plan') else None))
    for step in steps:
        rs=[v for v in receipts if v.get('agent')==step.agent];usage=observed(rs);ev=[v for v in events if v.get('step_id')==step.step_id]
        starts=[e['timestamp'] for e in ev if e['event_type'] in {'AGENT_STARTED','REVIEW_STARTED'}]
        ends=[e['timestamp'] for e in ev if e['event_type'] in {'AGENT_COMPLETED','AGENT_FAILED','REVIEW_COMPLETED'}]
        output=outputs.get(step.step_id);status=output.state if output else 'UNKNOWN'
        if ev:status=ev[-1].get('status') or status
        elif state in {'COMPLETED','REVIEW'}:status='COMPLETED'
        elif rs:status='FAILED' if any(x.get('state') in {'PROVIDER_ERROR','INVALID_RESPONSE'} for x in rs) else 'RUNNING' if not base['terminal'] else 'UNKNOWN'
        elif run['state']=='running':status='RUNNING' if r.get('current_step')==step.step_id else 'COMPLETED' if step.step_id<=r.get('completed_steps',0) else 'QUEUED'
        if base['terminal'] and status in {'RUNNING','REVIEWING','PLANNING','QUEUED'}:
            status='NOT_RUN' if status=='QUEUED' else 'INTERRUPTED'
        node=MonitorNode(id=str(step.step_id),agent=step.agent,name=NAMES[step.agent],level=levels[step.step_id],
            objective=safe_text(objectives.get(step.agent) or step.action),dependencies=[str(d) for d in step.dependencies],state=status,
            started_at=min(starts) if starts else None,ended_at=max(ends) if ends else None,
            duration_seconds=round(max(ends)-min(starts),3) if starts and ends else None,
            mode=usage['mode'] or ('LOCAL_DETERMINISTIC' if step.agent=='reviewer' or metrics['mode']=='LOCAL_DETERMINISTIC' else None),
            model=usage['model'],calls=usage['calls'],tokens=usage['tokens'],retries=usage['retries'],errors=usage['errors'],model_duration_seconds=usage['model_duration_seconds'],
            error_code=next((e['error_code'] for e in reversed(ev) if e.get('error_code')),None) or (output.error_code if output else None) or next((x['state'] for x in reversed(rs) if x.get('state') in {'PROVIDER_ERROR','INVALID_RESPONSE'}),None),
            output=safe_text(output.summary) if output else legacy.get(step.agent),output_origin='STORED_AGENT_RESULT' if output else 'LEGACY_AGGREGATE_SEGMENT' if step.agent in legacy else None,
            references=[v.model_dump() for v in output.references] if output else [],validation='VALIDATED_REFERENCES_SCOPE' if step.agent=='reviewer' and output and output.state=='COMPLETED' else None)
        nodes.append(node);edges.append({'from':'supervisor','to':node.id,'kind':'ASSIGNMENT'})
        edges.extend({'from':str(d),'to':node.id,'kind':'DEPENDENCY'} for d in step.dependencies)
    if steps:
        depended={d for s in steps for d in s.dependencies};leaves=[s for s in steps if s.step_id not in depended]
        nodes.append(MonitorNode(id='final',agent='final',name=NAMES['final'],assigned_by='supervisor',objective='Tổng hợp kết quả đã lưu; không gọi model để định dạng.',
            level=max(levels.values())+1,dependencies=[str(s.step_id) for s in leaves],state=state if base['terminal'] else 'QUEUED',mode='LOCAL_DETERMINISTIC',output=safe_text(r.get('text')) or None,output_origin='STORED_AGGREGATE'))
        edges.extend({'from':str(s.step_id),'to':'final','kind':'DEPENDENCY'} for s in leaves)
    safe_events=list(events)
    if not events:
        # Exact receipt timestamps/durations are recorded evidence, never synthetic per-agent durations.
        for receipt in receipts:
            for kind,at in [('MODEL_REQUEST_STARTED',receipt.get('at')),('MODEL_RESPONSE_RECEIVED',receipt.get('at',0)+receipt['duration_seconds'] if receipt.get('duration_seconds') is not None else None)]:
                if at is not None:safe_events.append({'event_id':receipt['id']+':'+kind,'run_id':agent_run.run_id,'trace_id':agent_run.trace_id,'event_type':kind,'agent_id':receipt.get('agent'),'step_id':next((s.step_id for s in steps if s.agent==receipt.get('agent')),None),'timestamp':at,'status':receipt.get('state'),'phase':receipt.get('phase'),'origin':'RECORDED_PROVIDER_RECEIPT'})
        safe_events.sort(key=lambda v:(v['timestamp'],v['event_id']))
        for i,e in enumerate(safe_events):e['sequence']=i+1
    source_refs=(r.get('agent_result') or {}).get('references',[])
    for node in nodes:
        node.input_source_ids=r.get('source_ids') or [ref['work_package_id'] for ref in source_refs]
        if node.output and 'Giới hạn:' in node.output:node.limitations=node.output.rsplit('Giới hạn:',1)[1].strip()
    if len(events)==200:warnings.append('Đang hiển thị tối đa 200 events đã lưu của run này.')
    agents={n.agent for n in nodes if n.agent!='final'}
    metrics.update(agents=len(agents),completed=sum(all(n.state=='COMPLETED' for n in nodes if n.agent==a) for a in agents),running=sum(n.state in {'RUNNING','REVIEWING','PLANNING'} for n in nodes),steps=len(steps))
    return ExecutionMonitor(**base,request=safe_text(task.instruction),mode=metrics['mode'],model=metrics['model'],nodes=nodes,edges=edges,events=safe_events,
        metrics=metrics,sources=source_refs,final_output=safe_text(r.get('text')) or None,warnings=warnings,
        duration_seconds=round(agent_run.updated_at-agent_run.created_at,3) if base['terminal'] else None)

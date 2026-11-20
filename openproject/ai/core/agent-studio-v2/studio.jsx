import React,{useState,useEffect,useMemo,useRef,useCallback} from 'react';
import {createRoot} from 'react-dom/client';
import {createPortal} from 'react-dom';
import {ReactFlow,Background,Controls,MiniMap,Handle,Position,BaseEdge,getSmoothStepPath} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './studio.css';
import {useObserverRead} from './observer-hooks.jsx';
import {graph,roles,stamp,short,structured,summarize,effectiveFreshness,safeLink,validateSnapshot,validateMonitor} from './model.mjs';

const iconPaths={graph:'M4 4h6v6H4z M15 14h6v6h-6z M4 17h6 M7 10v7h8',back:'m14 5-7 7 7 7 M7 12h14',refresh:'M20 8a8 8 0 1 0 0 8 M20 3v5h-5',moon:'M21 13a9 9 0 0 1-10-10A9 9 0 1 0 21 13',check:'m5 12 4 4L19 6',search:'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6',code:'m8 6-6 6 6 6 m8-12 6 6-6 6 m-3-15-2 18',clock:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M12 7v5l3 2',box:'m3 7 9-4 9 4v10l-9 4-9-4z M3 7l9 5 9-5 M12 12v9',alert:'m12 3 10 18H2z M12 9v5 M12 17v1',close:'m6 6 12 12 M6 18 18 6',arrow:'M4 12h16 m-6-6 6 6-6 6'};
function Icon({name='graph',size=18}){return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={iconPaths[name]||iconPaths.graph}/></svg>;}
function Badge({state='UNKNOWN'}){return <span className={`qas-badge state-${state.toLowerCase()}`}><span aria-hidden="true">{state==='COMPLETED'?'✓':state==='RUNNING'?'●':['FAILED','BLOCKED'].includes(state)?'!':'○'}</span>{state}</span>;}
const AgentNode=React.memo(function AgentNode({data}){
 if(globalThis.__studioMetrics)globalThis.__studioMetrics.nodeRenders=(globalThis.__studioMetrics.nodeRenders||0)+1;
 const [hover,setHover]=useState(false);
 const duration=typeof data.started_at==='number'?(data.active?Math.max(0,Math.round(Date.now()/1000-data.started_at)):typeof data.completed_at==='number'?Math.max(0,Math.round(data.completed_at-data.started_at)):null):null;
 return <div className={`qas-agent ${data.active?'is-active':''} state-${data.status?.toLowerCase()}`} onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}>
  <Handle type="target" position={data.direction==='TB'?Position.Top:Position.Left}/>
  <div className="qas-agent-top"><span className="qas-agent-icon"><Icon name={data.agent_role==='dev'?'code':data.agent_role==='qa'?'check':'graph'}/></span><span className="qas-agent-title">{data.title}<small>{data.kind==='attempt'?'RECORDED RUN':'AGENT STAGE'}</small></span><span className="qas-state-mark" aria-hidden="true">{data.status==='COMPLETED'?'✓':data.status==='RUNNING'?'●':'○'}</span></div>
  <div className="qas-node-status"><Badge state={data.status}/><small>{data.errors>0?`! ${data.errors} errors`:data.artifact_count>0?`${data.artifact_count} artifact`:data.checkpoint?.version?`checkpoint v${data.checkpoint.version}`:''}</small></div>
  <p className="qas-agent-summary">{data.status==='UNKNOWN'?'Chưa có dữ liệu đủ để xác minh trạng thái Agent.':data.blocker||data.error_code||data.active&&data.objective||summarize(data.summary)}</p>
  <div className="qas-agent-meta"><span>{data.model_calls??data.calls??'—'} calls</span><span>{data.attempts??'—'} {data.kind==='attempt'?'attempt':'runs'}{typeof data.retries==='number'?` · ${data.retries} retries`:''}</span><span>{duration!==null?`${duration}s`:'time —'}</span></div>
  <Handle type="source" position={data.direction==='TB'?Position.Bottom:Position.Right}/>
  {hover&&createPortal(<section className="qas-tooltip qas-floating-tooltip" role="tooltip"><strong>{data.title} <Badge state={data.status}/></strong><dl><dt>Task</dt><dd>#{data.task??'—'}</dd><dt>Current work</dt><dd>{data.objective||'Chưa ghi nhận mô tả bước'}</dd><dt>Result</dt><dd>{summarize(data.summary)}</dd><dt>Run ID</dt><dd>{data.latest_run_id||'Chưa ghi nhận'}</dd><dt>Started</dt><dd>{stamp(data.started_at)}</dd><dt>Completed</dt><dd>{stamp(data.completed_at)}</dd><dt>Last activity</dt><dd>{stamp(data.updated_at)}</dd><dt>Model calls</dt><dd>{data.model_calls??data.calls??'Chưa ghi nhận'}</dd><dt>Latest event</dt><dd>{data.latest_event||'Chưa ghi nhận'}</dd><dt>Blocker</dt><dd>{data.blocker||data.error_code||'Chưa ghi nhận'}</dd><dt>Evidence</dt><dd>{data.evidence_refs?.[0]?.source_record_id||'Xem run monitor'}</dd></dl><small>Click để xem timeline, artifacts và checkpoint.</small></section>,document.querySelector('#qldapm-agent-studio .qas'))}
 </div>;
},(old,next)=>JSON.stringify(old.data)===JSON.stringify(next.data));
function EvidenceEdge(props){const [path]=getSmoothStepPath({...props,borderRadius:18,offset:30});return <BaseEdge id={props.id} path={path} markerEnd={props.markerEnd} interactionWidth={26} style={{stroke:props.data.active?'var(--qas-cyan)':props.data.status==='FAILED'?'var(--qas-red)':props.data.status==='BLOCKED'?'var(--qas-amber)':props.data.complete?'var(--qas-green)':'var(--qas-edge)',strokeWidth:props.data.active?3:2,strokeDasharray:props.data.active?'7 7':props.data.complete?'none':'5 5'}} className={props.data.active?'qas-flow-active':''}/>;}
const nodeTypes={agent:AgentNode},edgeTypes={evidence:EvidenceEdge};

function Details({value,label='Technical Details'}){const [open,setOpen]=useState(false);return <details className="qas-technical" onToggle={e=>setOpen(e.currentTarget.open)}><summary>{label}</summary>{open&&<pre>{JSON.stringify(value,null,2)}</pre>}</details>;}
function Output({value}){
 const d=structured(value);if(!d)return <p className="qas-prose">{value&&value!=='NOT_RECORDED'?value:'Chưa có artifact được ghi nhận.'}</p>;
 const qa=d.qa||{},test=d.host_test||{};
 return <div className="qas-output">
  {typeof d.summary==='string'&&<p className="qas-prose">{d.summary}</p>}
  {['scope','api_behavior','edge_cases','acceptance','limitations','blockers'].filter(k=>Array.isArray(d[k])&&d[k].length).map(k=><Field key={k} label={k.replaceAll('_',' ')} value={d[k].join('\n')}/>)}
  {Array.isArray(d.assignments)&&d.assignments.filter(a=>a&&typeof a==='object').map(a=><Field key={a.unit} label={a.unit} value={`${a.objective} · priority ${a.priority} · dependencies: ${Array.isArray(a.dependencies)?a.dependencies.join(', '):'none'}`}/>)}
  {d.next_action&&<Field label="Next action" value={d.next_action}/>}
  {Array.isArray(d.files)&&<><h4>Files đã thay đổi</h4>{d.files.map((f,i)=><div className="qas-file" key={i}><Icon name="code"/>{String(f)}</div>)}</>}
  {d.head_sha&&<Field label="Commit SHA" value={d.head_sha}/>}
  {d.verdict&&<Field label="Review verdict" value={d.verdict}/>}
  {d.revision&&<Field label="Exact revision" value={d.revision}/>}
  {Array.isArray(d.findings)&&<Field label="Findings" value={d.findings.length?d.findings.map(f=>typeof f==='string'?f:f?.message||f?.title||'Finding có cấu trúc').join('\n'):'0 · không có finding được ghi nhận'}/>}
  {(qa.status||d.status)&&<Field label="Test status" value={qa.status||d.status}/>}
  {(qa.exit_code??test.exit_code??d.exit_code)!==undefined&&<Field label="Exit code" value={qa.exit_code??test.exit_code??d.exit_code}/>}
  {(qa.command||test.command||d.command)&&<Field label="Test command" value={qa.command||test.command||d.command}/>}
  {Array.isArray(qa.acceptance)&&<Field label="Acceptance criteria" value={qa.acceptance.join(' · ')}/>}
  {test.artifact&&<Field label="Report artifact (recorded path)" value={test.artifact}/>}
  {test.log_sha256&&<Field label="Report SHA256" value={test.log_sha256}/>}
  {!(d.summary||d.assignments||d.files||d.head_sha||d.verdict||qa.status||test.command||d.status)&&<p>{summarize(value)}</p>}
 </div>;
}
function Field({label,value}){return <div className="qas-field"><span>{label}</span><strong>{value===null||value===undefined||value===''?'Chưa ghi nhận':String(value)}</strong></div>;}
function Events({events}){return events.length?<ol className="qas-events">{[...events].reverse().map((e,i)=><li key={`${e.run_id}:${e.event_id||i}`}><span className="qas-event-dot"/><div><strong>{typeof e.event_type==='string'?e.event_type.replaceAll('_',' '):'UNKNOWN EVENT'}</strong><p>{e.agent_id?(roles[e.agent_id]||e.agent_id)+' · ':''}{e.status||e.error_code||e.source_system||e.origin||'AGENT_RUNTIME'}</p><small>{stamp(e.timestamp)} · {short(e.run_id)}</small><details><summary>Evidence reference</summary><p>{e.source_record_id||e.event_id||'Chưa ghi nhận'}</p>{e.receipt_id&&<p>Receipt {e.receipt_id}</p>}</details></div></li>)}</ol>:<p className="qas-empty">Chưa ghi nhận event trong phạm vi này.</p>;}
function ArtifactList({items}){return items.length?<div className="qas-artifacts">{items.map(a=><article key={a.artifact_id}><span className="qas-artifact-icon"><Icon name="box"/></span><div><h4>{a.title||a.type}</h4><small>{a.verification_status} · {stamp(a.created_at)}</small>{safeLink(a.uri)&&<p><a href={safeLink(a.uri)} target="_blank" rel="noopener noreferrer">Mở GitHub evidence <Icon name="arrow" size={14}/></a></p>}{a.verification_scope&&<p className="qas-note">Publication receipt lịch sử; không chứng minh trạng thái PR/deployment hiện tại.</p>}{a.content&&<Output value={a.content}/>}</div></article>)}</div>:<p className="qas-empty">Chưa có artifact được ghi nhận.</p>;}

function ReadState({read,retry}){return <div className="qas-read-state" data-phase={read.phase} role="status">{read.busy&&<span>Đang đọc dữ liệu…</span>}{read.phase==='cancelled'&&<span>Đã tạm dừng đọc.</span>}{read.error&&<><p className="qas-error">{read.error.message} HTTP {read.error.status} · {read.error.code}</p>{read.error.requestId&&<small>Request ID: {read.error.requestId}</small>}<button className="qas-button" onClick={retry}>Retry</button></>}</div>;}
function EvidencePanel({endpoint,task,section,stage,refresh,project,onRuns}){
 const [offset,setOffset]=useState(0),[retry,setRetry]=useState(0);
 const read=useObserverRead(endpoint,{task_id:task,view:'details',section,offset,limit:25,...(stage?{stage}:{})},{refresh:refresh+retry,validate:d=>{if(d.task_id!==task||(['events','artifacts','runs'].includes(section)&&!Array.isArray(d.items)))throw new Error('DETAIL_SCOPE_INVALID');}});
 const data=read.data,items=data?.items||[];
 useEffect(()=>{if(section==='runs'&&data)onRuns?.(data.items);},[data,section]);
 return <><ReadState read={read} retry={()=>setRetry(n=>n+1)}/>{data&&<>
 {section==='events'?<Events events={[...items].reverse()}/>:section==='artifacts'?<ArtifactList items={items}/>:section==='runs'?items.map(r=><section className="qas-run" key={r.run_id}><Badge state={r.state}/><h4>Attempt {r.attempt} · {short(r.run_id)}</h4><Field label="Checkpoint" value={r.checkpoint?.stage}/><Field label="Resume" value={r.resume?.reason}/><a href={`/projects/${project}/qldapm-ai/executions/${r.run_id}?studio_task_id=${task}`}>Mở Run Details</a><Details value={r}/></section>):section==='technical'?<Details label="Raw recorded snapshot" value={data.snapshot}/>:null}
 {data.source_limits&&<p className="qas-note">Cửa sổ nguồn: {data.source_limits.runs} runs · {data.source_limits.events_per_run} events/run. Xem Run Details để đọc trace của từng run.</p>}
 {data.next_offset!==undefined&&<div className="qas-pagination"><button className="qas-button" disabled={!offset||read.busy} onClick={()=>setOffset(Math.max(0,offset-25))}>Trang trước</button><span>{offset+1}–{offset+items.length} / {data.total_available}</span><button className="qas-button" disabled={data.next_offset===null||read.busy} onClick={()=>setOffset(data.next_offset)}>Trang sau</button></div>}
 </>}</>;
}
function Inspector({snapshot,selection,onClose,onExpand,expanded,endpoint,refresh,project,onRuns}){
 const [tab,setTab]=useState('overview'),[retry,setRetry]=useState(0),[technical,setTechnical]=useState(false);
 const role=selection?.split(':')[0];
 const read=useObserverRead(endpoint,{task_id:snapshot.task_id,view:'details',section:'overview',...(role?{stage:role}:{})},{enabled:!!selection,refresh:refresh+retry,validate:d=>validateSnapshot(d,snapshot.task_id)});
 const runId=selection?.includes(':')?selection.slice(selection.indexOf(':')+1):null;
 const runRead=useObserverRead(endpoint,{run_id:runId},{enabled:!!runId,refresh:refresh+retry,validate:d=>validateMonitor(d,runId)});
 const data=read.data||snapshot,latestStage=data.stages.find(s=>s.stage_key===role),node=runRead.data?.nodes?.find(n=>n.agent===role);
 const stage=runId?{...latestStage,status:node?.state||'UNKNOWN',summary:node?.output||'NOT_RECORDED',latest_run_id:runId,started_at:node?.started_at,completed_at:node?.ended_at,model_calls:node?.calls,retries:node?.retries,errors:node?.errors}:latestStage;
 useEffect(()=>{setTab('overview');setTechnical(false);},[selection]);
 const tabs=[['overview','Overview'],['runs','Agent Runs'],['events','Timeline'],['artifacts','Artifacts'],['errors','Errors / checkpoint']];
 return <aside className="qas-inspector" aria-label="Agent inspector"><div className="qas-inspector-title"><div><span className="qas-eyebrow">INSPECTOR · #{snapshot.task_id}</span><h3>{stage?(roles[stage.agent_role]||stage.agent_role):'Task evidence'}</h3></div><button className="qas-icon-button" onClick={onClose} aria-label="Đóng Agent inspector"><Icon name="close"/></button></div>
 <div className="qas-inspector-tabs" role="tablist">{tabs.map(([id,title])=><button key={id} role="tab" aria-selected={tab===id} onClick={()=>setTab(id)}>{title}</button>)}</div>
 <div className="qas-inspector-body" role="tabpanel"><ReadState read={read} retry={()=>setRetry(n=>n+1)}/>{runId&&<><ReadState read={runRead} retry={()=>setRetry(n=>n+1)}/><a href={`/projects/${project}/qldapm-ai/executions/${runId}?studio_task_id=${snapshot.task_id}`}>Mở trace đúng run {short(runId)}</a></>}
 {tab==='overview'&&<><Badge state={stage?.status||data.workflow_status}/><h4>Work summary</h4><Output value={stage?.summary}/><Field label="Recorded objective" value={stage?.objective}/><Field label="Run ID" value={stage?.latest_run_id||data.latest_run_id}/><Field label="Started" value={stamp(stage?.started_at??data.started_at)}/><Field label="Last activity" value={stamp(stage?.updated_at??data.updated_at)}/><Field label="Model calls / retries / errors" value={`${stage?.model_calls??'—'} / ${stage?.retries??'—'} / ${stage?.errors??'—'}`}/><h4>Business acceptance</h4><Field label="OpenProject status" value={data.business_status}/><Field label="Owner acceptance" value={data.acceptance_status}/><div className="qas-gates">{data.acceptance?.required_gates?.map(g=><div key={g.name}><span className={g.passed?'qas-pass':'qas-warn'}>{g.passed?'✓':'○'}</span>{g.name.replaceAll('_',' ')}</div>)}</div><p className="qas-note">Telemetry ghi nhận stage/model. Tool hoặc file activity chỉ có khi runtime lưu evidence.</p></>}
 {['runs','events','artifacts'].includes(tab)&&<>{tab==='runs'&&stage&&<button className="qas-button" onClick={()=>onExpand(stage.stage_key)}>{expanded.has(stage.stage_key)?'Thu gọn attempts':'Mở attempts trên graph'}</button>}<EvidencePanel key={`${snapshot.task_id}:${tab}:${role}`} endpoint={endpoint} task={snapshot.task_id} section={tab} stage={role} refresh={refresh} project={project} onRuns={onRuns}/></>}
 {tab==='errors'&&<><Field label="Blocker" value={stage?.blocker||data.runs.at(-1)?.blocker}/><Field label="Error code" value={data.runs.at(-1)?.error_code}/><Field label="Checkpoint stage" value={data.checkpoint?.stage}/><Field label="Checkpoint version" value={data.checkpoint?.version}/><Field label="Completed steps" value={data.checkpoint?.completed_steps?.join(' → ')}/><Field label="Resume policy" value={data.resume?.reason}/>{data.source_conflicts.map((c,i)=><Field key={i} label={short(c.run_id)} value={c.reason}/>)}</>}
 <details className="qas-technical" onToggle={e=>setTechnical(e.currentTarget.open)}><summary>Technical Details</summary>{technical&&<EvidencePanel key={snapshot.task_id+':technical:'+role} endpoint={endpoint} task={snapshot.task_id} section="technical" stage={role} refresh={refresh} project={project}/>}</details>
 </div></aside>;
}

function Studio({element}){
 const endpoint=element.dataset.endpoint,commandCenter=element.dataset.commandCenter;
 const projects=JSON.parse(element.dataset.projects),currentProject=element.dataset.project;
 const [theme,setTheme]=useState(()=>localStorage.getItem('qldapm-studio-theme')||'dark');
 const [mobile,setMobile]=useState(()=>element.clientWidth<=760);
 const [task,setTask]=useState(()=>{const v=new URL(location.href).searchParams.get('task_id');return /^\d+$/.test(v||'')?Number(v):null;});
 const [query,setQuery]=useState(''),[filter,setFilter]=useState('ALL'),[limit,setLimit]=useState(20);
 const [refresh,setRefresh]=useState(0),[selection,setSelection]=useState(null),[expanded,setExpanded]=useState(new Set()),[monitors,setMonitors]=useState([]),[bottom,setBottom]=useState('events'),[edgeHover,setEdgeHover]=useState(null),[tick,setTick]=useState(0);
 const graphRef=useRef(),fitTask=useRef(null);
 const listRead=useObserverRead(endpoint,{view:'list',query,state:filter,limit},{refresh,debounce:250,validate:d=>{if(!Array.isArray(d.items)||!d.items.every(i=>Number.isInteger(i.task_id)&&i.task_id>0))throw new Error('LIST_SCHEMA_INVALID');}});
 const taskRead=useObserverRead(endpoint,{task_id:task,view:'graph'},{enabled:!!task,poll:true,refresh,validate:data=>validateSnapshot(data,task)});
 const list=listRead.data,snapshot=taskRead.data,error=taskRead.error,busy=taskRead.busy,lastFetch=taskRead.lastFetch,listBusy=listRead.busy;
 useEffect(()=>{localStorage.setItem('qldapm-studio-theme',theme);},[theme]);
 useEffect(()=>{const resized=new ResizeObserver(entries=>setMobile(entries[0].contentRect.width<=760));resized.observe(element);return()=>resized.disconnect();},[element]);
 useEffect(()=>{if(snapshot?.workflow_status!=='RUNNING')return;const timer=setInterval(()=>{if(!document.hidden)setTick(t=>t+1);},5000);return()=>clearInterval(timer);},[snapshot?.workflow_status]);
 useEffect(()=>{setSelection(null);setExpanded(new Set());setMonitors([]);setEdgeHover(null);fitTask.current=null;},[task]);
 const choose=useCallback(id=>{if(id===task){setRefresh(n=>n+1);return;}setTask(id);const u=new URL(location.href);u.searchParams.set('task_id',String(id));history.pushState({...history.state,qldapmStudio:true},'',u);},[task]);
 useEffect(()=>{
  history.replaceState({...history.state,qldapmStudio:true},'',location.href);
  // Native host routers must not consume history entries owned by this island.
  const back=event=>{if(!event.state?.qldapmStudio||!location.pathname.endsWith('/qldapm-ai/observer'))return;event.stopImmediatePropagation();const v=new URL(location.href).searchParams.get('task_id');setTask(/^\d+$/.test(v||'')?Number(v):null);};
  window.addEventListener('popstate',back,true);return()=>window.removeEventListener('popstate',back,true);
 },[]);
 const toggleExpand=key=>setExpanded(old=>{const n=new Set(old);n.has(key)?n.delete(key):n.add(key);return n;});
 const receiveRuns=useCallback(runs=>setMonitors(old=>[...new Map([...old,...runs].map(r=>[r.run_id,r])).values()].slice(-50)),[]);
 const freshness=effectiveFreshness(snapshot,!!error||document.hidden),networkStale=!!error||document.hidden;
 const flow=useMemo(()=>snapshot?graph(snapshot,monitors,expanded,networkStale,mobile?'TB':'LR'):{nodes:[],edges:[]},[snapshot,monitors,expanded,networkStale,tick,mobile]);
 useEffect(()=>{const key=`${task}:${mobile}:${[...expanded].sort().join(',')}`;if(!snapshot||!flow.nodes.length||!graphRef.current||fitTask.current===key)return;const timer=setTimeout(()=>{graphRef.current?.fitView({padding:0.08,maxZoom:1,duration:0});fitTask.current=key;},200);return()=>clearTimeout(timer);},[flow.nodes.length,snapshot,task,mobile,expanded]);
 const [browserOpen,setBrowserOpen]=useState(true);
 const openExplorer=()=>{setBrowserOpen(true);requestAnimationFrame(()=>{const input=document.getElementById('qas-task-search');input?.scrollIntoView({block:'center'});input?.focus();});};
 const selectAgent=id=>{setSelection(id);if(mobile)requestAnimationFrame(()=>document.querySelector('.qas-inspector')?.scrollIntoView({block:'start',behavior:'instant'}));};
 return <div className="qas" data-theme={theme} data-transport="adaptive-polling" data-task={snapshot?.task_id||''} data-phase={taskRead.phase}>
  <header className="qas-header"><div className="qas-wordmark"><span className="qas-logo"><Icon name="graph" size={23}/></span><div><span className="qas-eyebrow">QLDAPM / AI OPERATIONS</span><h1>Agent Studio <span>V2</span></h1></div></div><div className="qas-header-actions"><a href={commandCenter} className="qas-button" id="qas-back"><Icon name="back"/>Command Center</a><button className="qas-icon-button" aria-label="Đổi theme" onClick={()=>setTheme(theme==='dark'?'light':'dark')}><Icon name="moon"/></button></div></header>
  <div className="qas-toolbar"><label>Project<select aria-label="Project" value={currentProject} onChange={e=>{location.href=projects.find(p=>p.identifier===e.target.value).url;}}>{projects.map(p=><option key={p.identifier} value={p.identifier}>{p.name}</option>)}</select></label><form onSubmit={e=>{e.preventDefault();if(/^#?\d+$/.test(query.trim()))choose(Number(query.replace('#','')));}}><label><Icon name="search"/><input id="qas-task-search" aria-label="Tìm Task ID hoặc tiêu đề" placeholder="Tìm Task ID hoặc tiêu đề…" value={query} maxLength={160} onChange={e=>{setQuery(e.target.value);setLimit(20);}}/></label></form><div className="qas-filters" aria-label="Lọc Tasks">{[['ALL','Recent'],['RUNNING','Active'],['BLOCKED','Blocked'],['COMPLETED','Completed']].map(([state,label])=><button key={state} className={filter===state?'selected':''} aria-pressed={filter===state} onClick={()=>{setFilter(state);setLimit(20);}}>{label}</button>)}</div><button className="qas-icon-button" aria-label="Làm mới Observer" onClick={()=>setRefresh(n=>n+1)}><Icon name="refresh"/></button></div>
  <div className="qas-connection" role="status" aria-live="polite"><span className={`qas-connection-dot ${freshness==='FRESH'?'fresh':''}`}/><strong>{snapshot?freshness:'UNKNOWN'}</strong><span>{document.hidden?'Tạm dừng tab ẩn':error?error.message:busy?'Đang đọc Observer…':lastFetch?'Observer đã phản hồi · '+new Date(lastFetch).toLocaleTimeString('vi-VN'):'Chọn Task để đọc Observer'}</span><span className="qas-transport">Bounded polling · 3–60s</span></div><ReadState read={taskRead} retry={()=>setRefresh(n=>n+1)}/>
  <div className={`qas-workspace ${browserOpen?'':'browser-collapsed'}`}>
   <aside className="qas-browser"><div className="qas-panel-heading"><h2>Task explorer</h2><span>{list?.items?.length??0}</span></div><p className="qas-note">Native Tasks và telemetry hiện có · ACL hiện hành</p><ReadState read={listRead} retry={()=>setRefresh(n=>n+1)}/>{listBusy&&<div className="qas-skeleton" role="status">Đang đọc danh sách…</div>}<div className="qas-task-list">{list?.items?.map(item=><button className={`qas-task ${task===item.task_id?'selected':''}`} key={item.task_id} onClick={()=>choose(item.task_id)}><span className="qas-task-top"><strong>#{item.task_id}</strong><span>{stamp(item.updated_at).split(' ')[0]}</span></span><span className="qas-task-name">{item.task_title}</span><Badge state={item.workflow_status}/><small>{item.run_count??0} runs · {item.freshness?.freshness_status||'UNKNOWN'}</small></button>)}</div>{!listBusy&&!list?.items?.length&&<p className="qas-empty">Không có Task phù hợp. Nhập ID chính xác và Enter để đọc Native.</p>}{list?.next_offset!==null&&list?.next_offset!==undefined&&limit<50&&<button className="qas-button qas-load-more" onClick={()=>setLimit(Math.min(50,limit+20))}>Load more</button>}{list?.truncated&&limit===50&&<p className="qas-note">Đã tới giới hạn. Thu hẹp tìm kiếm hoặc nhập ID.</p>}</aside>
   <main className="qas-main">
    {!snapshot?<section className="qas-welcome"><span className="qas-logo"><Icon name="graph" size={30}/></span><span className="qas-eyebrow">EXECUTION INTELLIGENCE</span><h2>{busy?'Đang đọc Task…':'Theo dõi công việc, từ bằng chứng.'}</h2><p>{error?.message||'Chọn một Task để xem Agent graph, run history và kết quả nghiệm thu trong cùng một không gian.'}</p><button className="qas-button" onClick={openExplorer}>Mở Task explorer</button><p className="qas-note">One Task → Multiple Agent Runs · Không suy luận trạng thái bằng LLM</p></section>:<>
     <section className="qas-task-header"><div><div className="qas-eyebrow">TASK #{snapshot.task_id} <span> / </span> {snapshot.stages.length} AGENT STAGES</div><h2>{snapshot.task_title}</h2><div className="qas-task-badges"><Badge state={snapshot.workflow_status}/><span className="qas-business">Business: <strong>{snapshot.business_status}</strong></span><span className="qas-business">Acceptance: <strong>{snapshot.acceptance_status}</strong></span></div></div><a className="qas-native-link" href={`/projects/${currentProject}/work_packages/${snapshot.task_id}`} target="_blank" rel="noopener noreferrer">Native Task <Icon name="arrow" size={15}/></a></section>
     <div className="qas-run-strip"><span><Icon name="clock"/>Run <strong title={snapshot.latest_run_id}>{short(snapshot.latest_run_id)}</strong></span><span>{snapshot.runs.length} recorded runs</span><span>Source activity <strong>{stamp(snapshot.updated_at)}</strong></span><span>Current agent <strong>{freshness==='FRESH'&&snapshot.workflow_status==='RUNNING'?snapshot.current_agent||'Chưa ghi nhận':'Không có RUNNING được xác minh'}</strong></span></div>
     <section className="qas-canvas-panel" aria-label="Agent execution graph"><div className="qas-canvas-heading"><div><Icon name="graph"/><h3>Execution graph</h3><span>Recorded dependencies</span></div><button className="qas-text-button" onClick={()=>browserOpen?setBrowserOpen(false):openExplorer()}>{browserOpen?'Ẩn':'Mở'} explorer</button></div>
      <div className="qas-canvas" onKeyDown={e=>{const n=e.target.closest(".react-flow__node");if(n&&(e.key==="Enter"||e.key===" ")){e.preventDefault();selectAgent(n.dataset.id);}}}><ReactFlow nodes={flow.nodes.map(n=>({...n,selected:n.id===selection}))} edges={flow.edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} nodesDraggable={false} nodesConnectable={false} elementsSelectable={true} deleteKeyCode={null} minZoom={0.22} maxZoom={1.6} onInit={api=>{graphRef.current=api;}} onNodeClick={(_,n)=>selectAgent(n.id)} onEdgeMouseEnter={(_,e)=>setEdgeHover(e.data)} onEdgeMouseLeave={()=>setEdgeHover(null)} onEdgeClick={(_,e)=>setEdgeHover(e.data)} onPaneClick={()=>setEdgeHover(null)} fitView fitViewOptions={{padding:0.16,maxZoom:1}} ariaLabelConfig={{'controls.zoomIn.ariaLabel':'Phóng to graph','controls.zoomOut.ariaLabel':'Thu nhỏ graph','controls.fitView.ariaLabel':'Fit graph'}}><Background gap={22} size={1} color={theme==='dark'?'#253747':'#d5dfe8'}/><Controls showInteractive={false}/><MiniMap pannable zoomable nodeColor={n=>n.data.active?'#22d3ee':n.data.status==='COMPLETED'?'#31c590':'#72869b'}/></ReactFlow>
       {!flow.nodes.length&&<div className="qas-no-graph">UNKNOWN · Chưa ghi nhận Agent stages. Không dựng graph giả.</div>}
       {edgeHover&&<div className="qas-edge-tooltip" role="tooltip"><strong>{roles[edgeHover.source]||edgeHover.source} → {roles[edgeHover.target]||edgeHover.target}</strong><Field label="Dependency type" value={edgeHover.kind}/><p>{edgeHover.explanation}</p><Field label="Last verified handoff" value={edgeHover.transition?`${edgeHover.transition.event_type} · ${stamp(edgeHover.transition.timestamp)}`:'Chưa ghi nhận handoff event'}/><Field label="Evidence reference" value={edgeHover.evidence||edgeHover.run_id}/></div>}
      </div><div className="qas-legend"><span><i className="qas-legend-dot complete"/>Completed</span><span><i className="qas-legend-dot active"/>Fresh active stage</span><span><i className="qas-legend-dot blocked"/>Blocked / failed</span><span><i className="qas-legend-dot"/>Pending / unknown</span><small>Stage completion ≠ Owner acceptance</small></div>
     </section>
     {snapshot.related_tasks?.length>0&&<nav aria-label="Related Tasks">{snapshot.related_tasks.map(r=><button className="qas-button" key={r.task_id} onClick={()=>choose(r.task_id)}>#{r.task_id} · {r.relationship}</button>)}</nav>}
     <section className="qas-bottom"><div className="qas-bottom-tabs" role="tablist">{[['events','Event timeline'],['artifacts','Artifacts'],['runs','Run history']].map(([id,label])=><button key={id} role="tab" aria-selected={bottom===id} onClick={()=>setBottom(id)}>{label}</button>)}</div><div className="qas-bottom-body" role="tabpanel"><EvidencePanel key={`${task}:${bottom}`} endpoint={endpoint} task={task} section={bottom} refresh={`${refresh}:${snapshot.revision}`} project={currentProject} onRuns={receiveRuns}/></div></section>
    </>}
   </main>
   {snapshot&&selection&&<Inspector key={`${task}:${selection}`} snapshot={snapshot} selection={selection} onClose={()=>setSelection(null)} expanded={expanded} onExpand={toggleExpand} endpoint={endpoint} refresh={`${refresh}:${snapshot.revision}`} project={currentProject} onRuns={receiveRuns}/>}
  </div>
  <footer className="qas-footer">Canonical Agent Observer · Native ACL · Không gọi model khi hover <span>Source freshness theo telemetry, không theo lần tải trang.</span></footer>
 </div>;
}

// Rails/Turbo may replace this island without unloading the browser document.
if(!window.qldapmStudioV2){
 let root=null,element=null,suspended=false;
 const unmount=()=>{root?.unmount();root=null;element=null;};
 const mount=()=>{suspended=false;const next=document.getElementById('qldapm-agent-studio');if(next===element)return;unmount();if(next){element=next;root=createRoot(next);root.render(<Studio element={next}/>);}};
 const suspend=()=>{suspended=true;unmount();};
 const observer=new MutationObserver(()=>{if(element&&!element.isConnected)unmount();if(!element&&!suspended)mount();});
 observer.observe(document.documentElement,{childList:true,subtree:true});
 document.addEventListener('turbo:load',mount);document.addEventListener('DOMContentLoaded',mount);document.addEventListener('turbo:before-cache',suspend);document.addEventListener('turbo:before-render',suspend);
 window.qldapmStudioV2={mount,unmount};mount();
}else window.qldapmStudioV2.mount();

"""One-time source transformation; no runtime or private data access."""
from pathlib import Path
p=Path('openproject/ai/core/agent-studio-v2/studio.jsx')
s=p.read_text(encoding='utf-8')
start=s.index('function Inspector(');end=s.index('\nfunction Studio(',start)
s=s[:start]+'''function ReadState({read,retry}){return <div className="qas-read-state" data-phase={read.phase} role="status">{read.busy&&<span>Đang đọc dữ liệu…</span>}{read.phase==='cancelled'&&<span>Đã tạm dừng đọc.</span>}{read.error&&<><p className="qas-error">{read.error.message} HTTP {read.error.status} · {read.error.code}</p>{read.error.requestId&&<small>Request ID: {read.error.requestId}</small>}<button className="qas-button" onClick={retry}>Retry</button></>}</div>;}
function EvidencePanel({endpoint,task,section,stage,refresh,project,onRuns}){
 const [offset,setOffset]=useState(0),[retry,setRetry]=useState(0);
 const read=useObserverRead(endpoint,{task_id:task,view:'details',section,offset,limit:25,...(stage?{stage}:{})},{refresh:refresh+retry});
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
 const read=useObserverRead(endpoint,{task_id:snapshot.task_id,view:'details',section:'overview',...(role?{stage:role}:{})},{enabled:!!selection,refresh:refresh+retry});
 const data=read.data||snapshot,stage=data.stages.find(s=>s.stage_key===role);
 useEffect(()=>{setTab('overview');setTechnical(false);},[selection]);
 const tabs=[['overview','Overview'],['runs','Agent Runs'],['events','Timeline'],['artifacts','Artifacts'],['errors','Errors / checkpoint']];
 return <aside className="qas-inspector" aria-label="Agent inspector"><div className="qas-inspector-title"><div><span className="qas-eyebrow">INSPECTOR · #{snapshot.task_id}</span><h3>{stage?(roles[stage.agent_role]||stage.agent_role):'Task evidence'}</h3></div><button className="qas-icon-button" onClick={onClose} aria-label="Đóng Agent inspector"><Icon name="close"/></button></div>
 <div className="qas-inspector-tabs" role="tablist">{tabs.map(([id,title])=><button key={id} role="tab" aria-selected={tab===id} onClick={()=>setTab(id)}>{title}</button>)}</div>
 <div className="qas-inspector-body" role="tabpanel"><ReadState read={read} retry={()=>setRetry(n=>n+1)}/>
 {tab==='overview'&&<><Badge state={stage?.status||data.workflow_status}/><h4>Work summary</h4><Output value={stage?.summary}/><Field label="Recorded objective" value={stage?.objective}/><Field label="Run ID" value={stage?.latest_run_id||data.latest_run_id}/><Field label="Started" value={stamp(stage?.started_at??data.started_at)}/><Field label="Last activity" value={stamp(stage?.updated_at??data.updated_at)}/><Field label="Model calls / retries / errors" value={`${stage?.model_calls??'—'} / ${stage?.retries??'—'} / ${stage?.errors??'—'}`}/><h4>Business acceptance</h4><Field label="OpenProject status" value={data.business_status}/><Field label="Owner acceptance" value={data.acceptance_status}/><div className="qas-gates">{data.acceptance?.required_gates?.map(g=><div key={g.name}><span className={g.passed?'qas-pass':'qas-warn'}>{g.passed?'✓':'○'}</span>{g.name.replaceAll('_',' ')}</div>)}</div><p className="qas-note">Telemetry ghi nhận stage/model. Tool hoặc file activity chỉ có khi runtime lưu evidence.</p></>}
 {['runs','events','artifacts'].includes(tab)&&<>{tab==='runs'&&stage&&<button className="qas-button" onClick={()=>onExpand(stage.stage_key)}>{expanded.has(stage.stage_key)?'Thu gọn attempts':'Mở attempts trên graph'}</button>}<EvidencePanel key={`${snapshot.task_id}:${tab}:${role}`} endpoint={endpoint} task={snapshot.task_id} section={tab} stage={role} refresh={refresh} project={project} onRuns={onRuns}/></>}
 {tab==='errors'&&<><Field label="Blocker" value={stage?.blocker||data.runs.at(-1)?.blocker}/><Field label="Error code" value={data.runs.at(-1)?.error_code}/><Field label="Checkpoint stage" value={data.checkpoint?.stage}/><Field label="Checkpoint version" value={data.checkpoint?.version}/><Field label="Completed steps" value={data.checkpoint?.completed_steps?.join(' → ')}/><Field label="Resume policy" value={data.resume?.reason}/>{data.source_conflicts.map((c,i)=><Field key={i} label={short(c.run_id)} value={c.reason}/>)}</>}
 <details className="qas-technical" onToggle={e=>setTechnical(e.currentTarget.open)}><summary>Technical Details</summary>{technical&&<EvidencePanel key={snapshot.task_id+':technical:'+role} endpoint={endpoint} task={snapshot.task_id} section="technical" stage={role} refresh={refresh} project={project}/>}</details>
 </div></aside>;
}
''' +s[end:]
start=s.index(' const selectedTask=');end=s.index(' const freshness=',start)
s=s[:start]+''' const [query,setQuery]=useState(''),[filter,setFilter]=useState('ALL'),[limit,setLimit]=useState(20);
 const [refresh,setRefresh]=useState(0),[selection,setSelection]=useState(null),[expanded,setExpanded]=useState(new Set()),[monitors,setMonitors]=useState([]),[bottom,setBottom]=useState('events'),[edgeHover,setEdgeHover]=useState(null),[tick,setTick]=useState(0);
 const graphRef=useRef(),fitTask=useRef(null);
 const listRead=useObserverRead(endpoint,{view:'list',query,state:filter,limit},{refresh,debounce:250});
 const taskRead=useObserverRead(endpoint,{task_id:task,view:'graph'},{enabled:!!task,poll:true,refresh,validate:data=>validateSnapshot(data,task)});
 const list=listRead.data,snapshot=taskRead.data,error=taskRead.error,busy=taskRead.busy,lastFetch=taskRead.lastFetch,listBusy=listRead.busy;
 useEffect(()=>{localStorage.setItem('qldapm-studio-theme',theme);},[theme]);
 useEffect(()=>{const resized=new ResizeObserver(entries=>setMobile(entries[0].contentRect.width<=760));resized.observe(element);return()=>resized.disconnect();},[element]);
 useEffect(()=>{if(snapshot?.workflow_status!=='RUNNING'||document.hidden)return;const timer=setInterval(()=>setTick(t=>t+1),5000);return()=>clearInterval(timer);},[snapshot?.workflow_status]);
 useEffect(()=>{setSelection(null);setExpanded(new Set());setMonitors([]);setEdgeHover(null);fitTask.current=null;},[task]);
 const choose=useCallback(id=>{if(id===task){setRefresh(n=>n+1);return;}setTask(id);const u=new URL(location.href);u.searchParams.set('task_id',String(id));history.pushState({qldapmStudio:true},'',u);},[task]);
 useEffect(()=>{const back=()=>{const v=new URL(location.href).searchParams.get('task_id');setTask(/^\\d+$/.test(v||'')?Number(v):null);};window.addEventListener('popstate',back);return()=>window.removeEventListener('popstate',back);},[]);
 const toggleExpand=key=>setExpanded(old=>{const n=new Set(old);n.has(key)?n.delete(key):n.add(key);return n;});
 const receiveRuns=useCallback(runs=>setMonitors(runs.map(r=>({...r,run_id:r.run_id}))),[]);
''' +s[end:]
s=s.replace(" const selectedNode=selection?.split(':')[0];"," const openExplorer=()=>{setBrowserOpen(true);requestAnimationFrame(()=>{const input=document.getElementById('qas-task-search');input?.scrollIntoView({block:'center'});input?.focus();});};")
s=s.replace('data-task={snapshot?.task_id||\'\'}','data-task={snapshot?.task_id||\'\'} data-phase={taskRead.phase}')
s=s.replace('<input aria-label="Tìm Task ID hoặc tiêu đề"','<input id="qas-task-search" aria-label="Tìm Task ID hoặc tiêu đề"')
a=s.index('  <div className="qas-connection"');b=s.index('  <div className={`qas-workspace',a)
s=s[:a]+'''  <div className="qas-connection" role="status" aria-live="polite"><span className={`qas-connection-dot ${freshness==='FRESH'?'fresh':''}`}/><strong>{snapshot?freshness:'UNKNOWN'}</strong><span>{document.hidden?'Tạm dừng tab ẩn':error?error.message:busy?'Đang đọc Observer…':lastFetch?'Observer đã phản hồi · '+new Date(lastFetch).toLocaleTimeString('vi-VN'):'Chọn Task để đọc Observer'}</span><span className="qas-transport">Bounded polling · 3–60s</span></div><ReadState read={taskRead} retry={()=>setRefresh(n=>n+1)}/>
''' +s[b:]
s=s.replace('<p className="qas-note">Chỉ Tasks có telemetry · tối đa 50</p>{listError&&<p className="qas-error">{listError}</p>}','<p className="qas-note">Native Tasks và telemetry hiện có · ACL hiện hành</p><ReadState read={listRead} retry={()=>setRefresh(n=>n+1)}/>')
s=s.replace('{item.runs.length} runs · {item.stages.length} stages','{item.run_count??0} runs · {item.freshness?.freshness_status||\'UNKNOWN\'}')
s=s.replace('{list?.truncated&&limit<50','{list?.next_offset!==null&&list?.next_offset!==undefined&&limit<50')
s=s.replace("<p>{error||'Chọn một Task", "<p>{error?.message||'Chọn một Task")
s=s.replace('onClick={()=>setBrowserOpen(true)}>Mở Task explorer','onClick={openExplorer}>Mở Task explorer')
s=s.replace("onClick={()=>setBrowserOpen(v=>!v)}", "onClick={()=>browserOpen?setBrowserOpen(false):openExplorer()}")
start=s.index('     <section className="qas-bottom">');end=s.index('\n    </>}',start)
s=s[:start]+'''     {snapshot.related_tasks?.length>0&&<nav aria-label="Related Tasks">{snapshot.related_tasks.map(r=><button className="qas-button" key={r.task_id} onClick={()=>choose(r.task_id)}>#{r.task_id} · {r.relationship}</button>)}</nav>}
     <section className="qas-bottom"><div className="qas-bottom-tabs" role="tablist">{[['events','Event timeline'],['artifacts','Artifacts'],['runs','Run history']].map(([id,label])=><button key={id} role="tab" aria-selected={bottom===id} onClick={()=>setBottom(id)}>{label}</button>)}</div><div className="qas-bottom-body" role="tabpanel"><EvidencePanel key={`${task}:${bottom}`} endpoint={endpoint} task={task} section={bottom} refresh={refresh} project={currentProject} onRuns={receiveRuns}/></div></section>''' +s[end:]
start=s.index('   {snapshot&&<Inspector');end=s.index('\n  </div>',start)
s=s[:start]+'''   {snapshot&&selection&&<Inspector key={`${task}:${selection}`} snapshot={snapshot} selection={selection} onClose={()=>setSelection(null)} expanded={expanded} onExpand={toggleExpand} endpoint={endpoint} refresh={refresh} project={currentProject} onRuns={receiveRuns}/>}''' +s[end:]
p.write_text(s,encoding='utf-8')

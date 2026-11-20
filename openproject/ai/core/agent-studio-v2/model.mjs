import dagre from '@dagrejs/dagre';
const layouts=new Map();
function positions(nodes,edges,direction){
 const key=JSON.stringify([direction,nodes.map(n=>n.id).sort(),edges.map(e=>[e.source,e.target]).sort()]);
 if(layouts.has(key))return layouts.get(key);
 const layout=new dagre.graphlib.Graph().setGraph({rankdir:direction,nodesep:44,ranksep:88,marginx:36,marginy:48});layout.setDefaultEdgeLabel(()=>({}));
 nodes.forEach(n=>layout.setNode(n.id,{width:280,height:176}));edges.forEach(e=>layout.setEdge(e.source,e.target));dagre.layout(layout);
 const result=new Map(nodes.map(n=>{const p=layout.node(n.id);return [n.id,{x:p.x-140,y:p.y-88}];}));
 if(layouts.size>=16)layouts.delete(layouts.keys().next().value);layouts.set(key,result);
 if(globalThis.__studioMetrics)globalThis.__studioMetrics.layouts=(globalThis.__studioMetrics.layouts||0)+1;
 return result;
}

export const roles={dev:'Developer',reviewer:'Reviewer',qa:'QA Engineer',ba:'Business Analyst',pm:'Project Manager'};
export const stamp=value=>typeof value==='number'?new Date(value*1000).toLocaleString('vi-VN',{timeZone:'Asia/Bangkok',hour12:false}):'Chưa ghi nhận';
export const short=value=>value?String(value).slice(0,8):'—';
export function validateSnapshot(data,task){
 if(data?.task_id!==task||!['stages','runs','events','artifacts','source_conflicts'].every(k=>Array.isArray(data[k]))||!data.freshness||!data.stages.every(s=>typeof s.stage_key==='string'&&typeof s.status==='string')||!data.runs.every(r=>typeof r.run_id==='string')||!data.events.every(e=>typeof e.event_id==='string'&&(e.timestamp===null||typeof e.timestamp==='number')))throw new Error('Observer snapshot không hợp lệ');
 return data;
}
export function validateMonitor(data,id){
 if(data?.run_id!==id||!Array.isArray(data.nodes)||!Array.isArray(data.edges))throw new Error('Run snapshot không hợp lệ');
 return data;
}
export function safeLink(value){try{const u=new URL(value);return u.protocol==='https:'?u.href:null;}catch{return null;}}
export function structured(value){try{const v=typeof value==='string'?JSON.parse(value):value;return v&&typeof v==='object'?v:null;}catch{return null;}}
export function summarize(value){
 if(!value||value==='NOT_RECORDED')return 'Chưa ghi nhận kết quả';
 const d=structured(value);if(!d)return String(value).replace(/\s+/g,' ').slice(0,220);
 const parts=[];
 if(Array.isArray(d.files)&&d.files.length)parts.push(`${d.files.length} file: ${d.files.join(', ')}`);
 if(d.head_sha)parts.push(`commit ${short(d.head_sha)}`);
 if(d.verdict)parts.push(`Review ${d.verdict}`);
 const qa=d.qa||d.host_test||d;
 if(qa.status)parts.push(qa.status);
 if(qa.exit_code!==undefined)parts.push(`exit code ${qa.exit_code}`);
 if(d.findings)parts.push(`${d.findings.length} findings`);
 return parts.join(' · ')||'Artifact có cấu trúc · mở inspector để xem bằng chứng';
}
export function effectiveFreshness(snapshot,disconnected,now=Date.now()/1000){
 if(disconnected)return 'STALE';
 const f=snapshot?.freshness;if(!f)return 'UNKNOWN';
 if(typeof f.source_updated_at==='number'&&now-f.source_updated_at>120)return 'STALE';
 return ['FRESH','STALE','PARTIAL','UNKNOWN'].includes(f.freshness_status)?f.freshness_status:'UNKNOWN';
}
export function graph(snapshot,monitors,expanded,disconnected,direction='LR'){
 const fresh=effectiveFreshness(snapshot,disconnected)==='FRESH';
 const stages=snapshot?.stages||[];
 const nodes=stages.map(stage=>({id:stage.stage_key,type:'agent',position:{x:0,y:0},data:{...stage,kind:'stage',latest_event:snapshot.events.filter(e=>e.agent_id===stage.agent_role).at(-1)?.event_type,title:roles[stage.agent_role]||stage.agent_role,task:snapshot.task_id,active:fresh&&stage.status==='RUNNING'&&snapshot.current_stage===stage.stage_key}}));
 const latest=monitors.find(m=>m.run_id===snapshot?.latest_run_id),edges=[];
 for(const node of nodes){const recorded=latest?.nodes?.find(n=>n.agent===node.id);Object.assign(node.data,{objective:node.data.objective??recorded?.objective,started_at:node.data.started_at??recorded?.started_at,retries:node.data.retries??recorded?.retries,errors:node.data.errors??recorded?.errors,error_code:node.data.error_code??recorded?.error_code,artifact_count:node.data.artifact_count??snapshot.artifacts.filter(a=>a.run_id===node.data.latest_run_id&&a.type===node.data.agent_role+'_output').length,clock:node.data.active?Math.floor(Date.now()/5000):null});}
 const byId=new Map((latest?.nodes||[]).map(n=>[n.id,n]));
 const stageKeys=new Set(nodes.map(n=>n.id));
 const recordedEdges=snapshot.flow_edges??latest?.edges??[];
 for(const [i,edge] of recordedEdges.entries()){
  const source=edge.source??byId.get(edge.from)?.agent,target=edge.target??byId.get(edge.to)?.agent;
  if(!stageKeys.has(source)||!stageKeys.has(target))continue;
  const destination=stages.find(s=>s.stage_key===target),origin=stages.find(s=>s.stage_key===source);
  // Stage activity is not evidence of messages moving along a dependency.
  const active=fresh&&destination.status==='RUNNING'&&snapshot.current_stage===target&&origin.status==='COMPLETED';
  const transition=(latest?.events||snapshot.events||[]).filter(e=>e.agent_id===target&&/HANDOFF/.test(e.event_type)&&e.timestamp).at(-1);
  edges.push({id:`dep-${i}`,source,target,type:'evidence',markerEnd:{type:'arrowclosed',color:active?'#22d3ee':'#688496',width:18,height:18},data:{kind:edge.kind||'DEPENDENCY',active,source,target,complete:origin.status==='COMPLETED'&&destination.status==='COMPLETED',status:destination.status,run_id:edge.run_id??latest?.run_id,transition:transition||null,evidence:edge.evidence_ref??`${latest?.run_id}:edge:${edge.from}→${edge.to}`,explanation:active?'Stage đích đang hoạt động; không chứng minh truyền message liên tục.':'Dependency trong monitor đã lưu; không tự coi là handoff thành công.'}});
 }
 const runOrder=new Map(snapshot.runs.map((r,i)=>[r.run_id,i]));
 const chronological=[...monitors].sort((a,b)=>(runOrder.get(a.run_id)??0)-(runOrder.get(b.run_id)??0));
 for(const stage of stages){
  if(!expanded.has(stage.stage_key))continue;
  let previous=null;
  for(const monitor of chronological){
   const n=(monitor.nodes||[]).find(n=>n.agent===stage.agent_role);if(!n)continue;
   const id=`${stage.stage_key}:${monitor.run_id}`,attempt=snapshot.runs.findIndex(r=>r.run_id===monitor.run_id)+1;
   nodes.push({id,type:'agent',position:{x:0,y:0},data:{...stage,...n,status:n.state,kind:'attempt',task:snapshot.task_id,title:`${roles[n.agent]||n.agent} · lần ${attempt}`,latest_run_id:monitor.run_id,summary:n.output,attempts:attempt,completed_at:n.ended_at,artifact_count:snapshot.artifacts.filter(a=>a.run_id===monitor.run_id&&a.type===n.agent+'_output').length,active:fresh&&n.state==='RUNNING'&&monitor.run_id===snapshot.latest_run_id}});
   edges.push({id:`expand-${id}`,source:stage.stage_key,target:id,type:'evidence',markerEnd:{type:'arrowclosed',color:'#688496'},data:{kind:'STAGE_ATTEMPT',source:stage.stage_key,target:id,run_id:monitor.run_id,explanation:'Attempt thuộc stage này; không phải handoff.'}});
   if(previous)edges.push({id:`order-${id}`,source:previous,target:id,type:'evidence',markerEnd:{type:'arrowclosed',color:'#688496'},data:{kind:'ATTEMPT_ORDER',source:previous,target:id,run_id:monitor.run_id,explanation:'Thứ tự các run đã ghi nhận. Resume cùng run nằm trong checkpoint/timeline, không suy diễn một lần retry mới.'}});
   previous=id;
  }
 }
 nodes.forEach(n=>{n.data.direction=direction;});
 const geometry=positions(nodes,edges,direction);nodes.forEach(n=>{n.position=geometry.get(n.id);});
 return {nodes,edges};
}

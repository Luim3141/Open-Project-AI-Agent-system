import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import dagre from '@dagrejs/dagre';
import {graph, effectiveFreshness, summarize, safeLink,validateSnapshot,validateMonitor} from './model.mjs';
const task=JSON.parse(readFileSync('../../../../docs/agent-studio-v2/task-397.json'));
const monitor=JSON.parse(readFileSync('../../../../docs/agent-studio-v2/run-397.json'));
test('graph summary renders recorded edges without fetching full monitor',()=>{
 const s=structuredClone(task);s.flow_edges=[{source:'dev',target:'reviewer',kind:'DEPENDENCY',run_id:s.latest_run_id,evidence_ref:'recorded:1→2'},{source:'reviewer',target:'qa',kind:'DEPENDENCY',run_id:s.latest_run_id,evidence_ref:'recorded:2→3'}];
 assert.equal(graph(s,[],new Set(),false).edges.length,2);
});
test('status-only refresh reuses Dagre geometry',()=>{
 const original=dagre.layout;let count=0;dagre.layout=(...args)=>{count++;return original(...args);};
 try{graph(task,[monitor],new Set(),false);const first=count;const next=structuredClone(task);next.stages[0].model_calls+=1;graph(next,[monitor],new Set(),false);assert.equal(count,first);}
 finally{dagre.layout=original;}
});
test('canonical boundary rejects malformed or wrong task/run snapshots',()=>{
 assert.equal(validateSnapshot(task,397),task);assert.equal(validateMonitor(monitor,task.latest_run_id),monitor);
 assert.throws(()=>validateSnapshot(task,391));assert.throws(()=>validateSnapshot({...task,events:[{timestamp:'invented'}]},397));
 assert.throws(()=>validateMonitor({...monitor,nodes:null},task.latest_run_id));
});
test('real coding Task preserves stages and recorded dependency direction',()=>{
 const result=graph(task,[monitor],new Set(),false);
 assert.deepEqual(result.nodes.map(n=>n.id),['dev','reviewer','qa']);
 assert.deepEqual(result.edges.map(e=>[e.source,e.target]),[['dev','reviewer'],['reviewer','qa']]);
 assert(result.edges.every(e=>!e.data.active && e.markerEnd.type==='arrowclosed'));
 assert(!result.nodes.some(n=>['ba','pm'].includes(n.id)));
});
test('Dagre positions do not overlap; expanding attempts uses run evidence',()=>{
 const second=structuredClone(monitor);second.run_id='second';
 const result=graph(task,[monitor,second],new Set(['dev']),false);
 assert.equal(result.nodes.filter(n=>n.data.kind==='attempt').length,2);
 assert(result.edges.some(e=>e.data.kind==='ATTEMPT_ORDER'));
 for(let i=0;i<result.nodes.length;i++) for(let j=i+1;j<result.nodes.length;j++){
  const a=result.nodes[i],b=result.nodes[j];assert(Math.abs(a.position.x-b.position.x)>=280||Math.abs(a.position.y-b.position.y)>=176);
 }
});
test('running animation needs fresh canonical evidence and healthy transport',()=>{
 const s=structuredClone(task),m=structuredClone(monitor);
 s.current_stage='reviewer';s.workflow_status='RUNNING';s.freshness={freshness_status:'FRESH',source_updated_at:Date.now()/1000};
 s.stages[1].status='RUNNING';m.nodes.find(n=>n.agent==='reviewer').state='RUNNING';
 assert(graph(s,[m],new Set(),false).edges.some(e=>e.data.active));
 assert(!graph(s,[m],new Set(),true).edges.some(e=>e.data.active));
 s.freshness.source_updated_at-=121;
 assert.equal(effectiveFreshness(s,false),'STALE');
 assert(!graph(s,[m],new Set(),false).edges.some(e=>e.data.active));
});
test('unknown monitor has no invented edges, no raw JSON summary, safe URLs only',()=>{
 assert.equal(graph(task,[],new Set(),false).edges.length,0);
 assert.equal(summarize('{"status":"PASS","exit_code":0}'),'PASS · exit code 0');
 assert.equal(summarize('{"unknown":"secret-looking-body"}'),'Artifact có cấu trúc · mở inspector để xem bằng chứng');
 assert.equal(safeLink('javascript:alert(1)'),null);assert.equal(safeLink('https://github.com/a/b/pull/1'),'https://github.com/a/b/pull/1');
 assert.equal(safeLink('https://evil.example'),'https://evil.example/');
});
test('legacy malformed file metadata remains readable',()=>{
 assert.doesNotThrow(()=>summarize('{"files":"legacy"}'));
});
test('newest-first history pages keep attempt edges chronological',()=>{
 const s=structuredClone(task),older={...structuredClone(monitor),run_id:'older'},newer={...structuredClone(monitor),run_id:'newer'};
 s.runs=[{run_id:'older'},{run_id:'newer'}];s.latest_run_id='newer';
 const edge=graph(s,[newer,older],new Set(['dev']),false).edges.find(e=>e.data.kind==='ATTEMPT_ORDER');
 assert.equal(edge.source,'dev:older');assert.equal(edge.target,'dev:newer');
});
test('resume checkpoints and model retries remain one recorded run, not extra attempts',()=>{
 const s=structuredClone(task),m=structuredClone(monitor);
 s.runs[0].resume={same_run_id:true,checkpoint_version:9};m.metrics={calls:12,retries:3};
 const result=graph(s,[m],new Set(['dev']),false);
 assert.equal(result.nodes.filter(n=>n.data.kind==='attempt').length,1);
 assert.equal(result.edges.filter(e=>e.data.kind==='ATTEMPT_ORDER').length,0);
});

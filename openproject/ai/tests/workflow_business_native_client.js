// Runs in the labelled private n8n clone. All Native decisions are simulated fixtures.
const fs=require('fs'),crypto=require('crypto'),assert=require('assert/strict');
const root='/qualification',base='http://localhost:5678',gateway='http://qldapm-ai-gateway-1:8090';
const tokens=JSON.parse(fs.readFileSync(root+'/bearers.json'));
const secret=JSON.parse(fs.readFileSync(root+'/credentials.json')).find(c=>c.name==='Clone webhook').data.value;
const fixture=JSON.parse(fs.readFileSync(root+'/approval-result.json'));
let cookie='',rows=[],monitorFault;
async function fixtureSignal(request,ready,body={}){fs.writeFileSync(root+'/'+request,JSON.stringify(body));for(let i=0;i<240;i++){if(fs.existsSync(root+'/'+ready))return JSON.parse(fs.readFileSync(root+'/'+ready));await new Promise(r=>setTimeout(r,500));}throw Error('CLONE_HOST_FIXTURE_TIMEOUT:'+request);}
async function http(url,body,headers={}) {
  const r=await fetch(url,{method:body?'POST':'GET',headers:{'content-type':'application/json',...headers},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(115000)});
  const text=await r.text();let data;try{data=JSON.parse(text);}catch{throw Error('NON_JSON_RESPONSE:'+r.status+':'+text.slice(0,200));}
  return {status:r.status,body:data,headers:r.headers};
}
async function api(path,body) {let r=await http(base+path,body,{cookie});assert.equal(r.status,200,JSON.stringify(r.body));let cs=r.headers.getSetCookie();if(cs.length)cookie=cs.map(s=>s.split(';')[0]).join('; ');return r.body.data;}
async function webhook(path,body={},actor='18') {let r=await http(base+'/webhook/'+path,body,{'X-QLDAPM-Webhook-Token':secret,...(actor?{Authorization:'Bearer '+tokens[actor]}:{})});return {status:r.status,body:r.body};}
async function command(action,args={},actor='18') {let r=await http(gateway+'/api/v1/commands',{action,arguments:args,idempotency_key:crypto.randomUUID()},{Authorization:'Bearer '+tokens[actor]});assert.equal(r.status,200,JSON.stringify(r.body));return r.body.result;}
async function cacheWebhook(path,body){let r;for(let i=0;i<60;i++){r=await webhook(path,body);if(r.status!==503||!/^KNOWLEDGE_BUSY|^KNOWLEDGE_VECTOR|^KNOWLEDGE_INTEGRITY_UNAVAILABLE$/.test(r.body.error||''))return r;await new Promise(resolve=>setTimeout(resolve,1000));}return r;}
function ok(r){assert.equal(r.status,200,JSON.stringify(r.body));return r.body.result;}
async function check(code,fn){try{let evidence=await fn();rows.push({code,state:'PASS',at:new Date().toISOString(),evidence});}catch(e){rows.push({code,state:'FAIL',at:new Date().toISOString(),error:e.message});}fs.writeFileSync(root+'/business-result.json',JSON.stringify(rows,null,2));console.log(code,rows.at(-1).state);}
(async()=>{
 const owner=JSON.parse(fs.readFileSync(root+'/owner.json'));await api('/rest/login',{emailOrLdapLoginId:owner.email,password:owner.password});
 for(let i=1;i<=16;i++){const code='WF'+String(i).padStart(2,'0');if(['WF05','WF06','WF12'].includes(code))continue;
  const spec=JSON.parse(fs.readFileSync(root+'/'+code+'.json'));let w=await api('/rest/workflows',spec);
  await api('/rest/workflows/'+w.id+'/activate',{versionId:w.versionId,...(w.checksum?{expectedChecksum:w.checksum}:{})});}
 const id=fixture.native_id;
 await check('WF01',async()=>{
  const req={id,request_id:crypto.randomUUID()},first=ok(await webhook('qldapm-ingest',req));assert.equal(first.native_id,id);assert.equal(first.vector_indexed,true);
  const again=ok(await webhook('qldapm-ingest',req));assert.deepEqual(again,first);
  const file=ok(await webhook('qldapm-ingest',{source_key:'clone-contract',request_id:crypto.randomUUID()}));assert.equal(file.vector_indexed,true);
  const hits=ok(await webhook('qldapm-ingest',{source_key:'clone-contract',operation:'search',query:'exact proposal approval'}));assert.ok(hits.items.length);
  const denied=await webhook('qldapm-ingest',{source_key:'clone-contract',operation:'search',query:'approval'},'21');assert.equal(denied.status,403);
  const formats=[];
  for(const source of (fs.existsSync(root+'/contract.pdf')?['clone-docx','clone-pdf']:[])){
    const indexed=ok(await webhook('qldapm-ingest',{source_key:source,request_id:crypto.randomUUID()}));assert.equal(indexed.vector_indexed,true);
    const read=ok(await webhook('qldapm-ingest',{source_key:source,operation:'read',document_id:indexed.document_id},'20'));assert.ok(read.content.includes('workflow citation.'));
    const found=ok(await webhook('qldapm-ingest',{source_key:source,operation:'search',query:'workflow citation'},'20'));assert.ok(found.items.length);
    formats.push({source,indexed,read,search:found});
  }
  return {native:first,file,search:hits,denied_http:denied.status,formats};
 });
 await check('WF02',async()=>{const sync=ok(await webhook('qldapm-op-sync',{operation:'sync',request_id:crypto.randomUUID()}));assert.equal(sync.state,'OBSERVED');assert.equal(sync.native_writes,0);assert.ok(sync.visible>=340);return sync;});
 let run;
 await check('WF03',async()=>{
  const req={prompt:'Hiện tại có bao nhiêu công việc loại Task chưa hoàn thành? Chỉ đọc số liệu, không tạo đề xuất.',request_id:crypto.randomUUID()};
  run=ok(await webhook('qldapm-agent-request',req));assert.ok(run.id);
  let final;for(let i=0;i<40;i++){final=ok(await webhook('qldapm-agent-request',{operation:'status',run_id:run.id}));if(final.state!=='running')break;await new Promise(r=>setTimeout(r,500));}
  assert.equal(final.state,'done');assert.equal(final.result.model_used,false);
  const replay=ok(await webhook('qldapm-agent-request',req));assert.equal(replay.id,run.id);
  return {run_id:run.id,final,scope:'Native deterministic orchestration; no live Gemini in this clone'};
 });
 await check('WF04',async()=>{
  const local=await command('start_ai_run',{prompt:'Phân tích tiến độ công việc '+id,engine:'supervisor',run_class:'agent',allow_routine_writes:false});
  let trace;for(let i=0;i<40;i++){trace=await webhook('qldapm-agent-trace',{run_id:local.id});if(trace.status===200&&trace.body.total_events>0)break;await new Promise(r=>setTimeout(r,500));}
  assert.equal(trace.status,200,JSON.stringify(trace.body));assert.ok(trace.body.total_events>0);return {run_id:local.id,...trace.body};
 });
 await check('WF07',async()=>{const r=ok(await webhook('qldapm-daily-brief',{},null));assert.equal(r.state,'COMPLETED');assert.equal(r.status,'READY');return r;});
 await check('WF08',async()=>{const r=ok(await webhook('qldapm-sprint-risk',{}));assert.ok(r.report_id&&r.report_sha256);const persisted=await command('get_report',{id:r.report_id});assert.ok(persisted);return r;});
 await check('WF09',async()=>{const r=ok(await webhook('qldapm-bug-lifecycle',{operation:'triage',id:371}));assert.ok(r);const deny=await webhook('qldapm-bug-lifecycle',{operation:'transition',id:371,status_id:1,approved:true,request_id:crypto.randomUUID()});assert.ok([403,409,422].includes(deny.status));return {triage:r,forged_authority_http:deny.status};});
 await check('WF10',async()=>{
  const draft=ok(await webhook('qldapm-task-orchestration',{operation:'draft',request_id:crypto.randomUUID(),requirements:[{id:'R1',text:'Isolated workflow acceptance'}],
   nodes:[{key:'epic',kind:'Epic',subject:'Isolated draft only',requirement_ids:['R1']}],share_for_review:true},'20'));
  assert.ok(draft.id&&draft.hash);const read=ok(await webhook('qldapm-task-orchestration',{operation:'get',id:draft.id},'20'));assert.equal(read.hash,draft.hash);return draft;
 });
 await check('WF11',async()=>{
  const old=await command('get_work_package',{id});
  const proposal=await command('update_work_package',{id,lock_version:old.lockVersion,changes:{description:'AC1: native.subject == "Isolated approved workflow fixture"'}});
  ok(await webhook('qldapm-execute-mutation',{proposal_id:proposal.id,hash:proposal.hash,decision:'approve'}));
  const startingState=await fixtureSignal('qa-fixture-request.json','qa-fixture-ready.json',{id});assert.equal(startingState.status_id,9);
  const forbidden=await webhook('qldapm-qa-gate',{operation:'run',native_id:id,request_id:crypto.randomUUID()},'21');assert.equal(forbidden.status,403);
  const tested=ok(await webhook('qldapm-qa-gate',{operation:'run',native_id:id,request_id:crypto.randomUUID()}));assert.equal(tested.verdict,'PASSED');
  let proof=ok(await webhook('qldapm-qa-gate',{operation:'from_run',run_id:tested.id,request_id:crypto.randomUUID()}));assert.equal(proof.state,'pending_qa');
  const decision={operation:'review',evidence_id:proof.id,hash:proof.hash,decision:'accept'};
  const outOfOrder=await webhook('qldapm-qa-gate',decision,'19');assert.equal(outOfOrder.status,403);
  const qa=ok(await webhook('qldapm-qa-gate',decision,'23'));assert.equal(qa.state,'qa_accepted');
  proof=ok(await webhook('qldapm-qa-gate',decision,'19'));assert.equal(proof.state,'accepted');assert.equal(proof.ready,true);
  const next=ok(await webhook('qldapm-qa-gate',{operation:'transition_prepare',evidence_id:proof.id,hash:proof.hash,status_id:34,request_id:crypto.randomUUID()},'19'));
  assert.equal(next.state,'pending');
  const written=ok(await webhook('qldapm-execute-mutation',{proposal_id:next.id,hash:next.hash,decision:'approve'},'19'));
  const read=await command('get_work_package',{id});assert.equal(read._links.status.href,'/api/v3/statuses/34');
  const legacy=ok(await webhook('qldapm-qa-gate',{id}));assert.ok(legacy.items.some(e=>e.id===proof.id&&e.native_id===id));
  return {starting_state_fixture:startingState,test_run_id:tested.id,evidence_id:proof.id,proof_hash:proof.hash,reviews:proof.reviews,out_of_order_http:outOfOrder.status,native_result:written,readback_version:read.lockVersion,default_read_evidence:legacy,authorization_kind:'SIMULATED_ISOLATED_FIXTURE_NOT_MAIN_HUMAN_APPROVAL'};
 });
 await check('WF12',async()=>{const r=ok(await webhook('qldapm-weekly-summary',{}));assert.ok(r.report_id&&r.report_sha256);return r;});
 await check('WF13',async()=>{const old=await command('get_work_package',{id});const p=await command('update_work_package',{id,lock_version:old.lockVersion,changes:{description:'Changed source revision from isolated n8n fixture'}});
  const written=ok(await webhook('qldapm-execute-mutation',{proposal_id:p.id,hash:p.hash,decision:'approve'}));
  const reindex=ok(await cacheWebhook('qldapm-rag-reindex',{id,request_id:crypto.randomUUID()}));assert.equal(reindex.vector_indexed,true);
  const hits=await command('knowledge_search',{query:'Changed source revision from isolated n8n fixture',native_ids:[id]});assert.ok(hits.items.some(h=>h.lock_version===old.lockVersion+1));
  return {native_write:written,reindex,citations:hits};
 });
 await check('WF14',async()=>{
  const setup=await fixtureSignal('dependency-fault-request.json','dependency-fault-ready.json');const job=setup.knowledge_sync.id;
  monitorFault=await webhook('qldapm-monitoring',{},null);const health=ok(monitorFault);assert.equal(health.state,'DEGRADED');assert.equal(health.checks.qdrant.state,'ERROR');
  const denied=await webhook('qldapm-error-handler',{job_id:job,operation:'status'},'21');assert.equal(denied.status,403);
  const before=ok(await webhook('qldapm-error-handler',{job_id:job,operation:'status'}));assert.equal(before.state,'dlq');
  const request={job_id:job,operation:'retry',request_id:crypto.randomUUID()};const retry=ok(await webhook('qldapm-error-handler',request));assert.equal(retry.state,'pending');
  assert.deepEqual(ok(await webhook('qldapm-error-handler',request)),retry);
  await fixtureSignal('dependency-recover-request.json','dependency-recovered.json');
  let final;for(let i=0;i<100;i++){final=ok(await webhook('qldapm-error-handler',{job_id:job,operation:'status'}));if(final.state==='verified')break;await new Promise(r=>setTimeout(r,1000));}
  assert.equal(final.state,'verified');assert.equal(final.result.vector_indexed,true);return {setup,before,retry,final,wrong_actor_http:denied.status};
 });
 await check('WF15',async()=>{
  const quiet=await fixtureSignal('quiescent-request.json','quiescent-ready.json');assert.equal(quiet.unfinished_cache_jobs,0);
  const target='http://qldapm-qdrant:6333/collections/qldapm_knowledge_dense/points';
  const points=await http(target+'/scroll',{limit:10000,with_payload:true,with_vector:false});assert.equal(points.status,200);
  const own=points.body.result.points.find(p=>p.payload.work_package_id===id&&p.payload.actor_id===18);assert.ok(own);
  const removed=await http(target+'/delete?wait=true',{points:[own.id]});assert.equal(removed.status,200);
  const drift=ok(await cacheWebhook('qldapm-reconciliation',{}));assert.equal(drift.mutations_performed,false);assert.ok(drift.missing_point_ids.includes(own.id));
  const repaired=ok(await cacheWebhook('qldapm-rag-reindex',{id,request_id:crypto.randomUUID()}));assert.equal(repaired.vector_indexed,true);
  const after=ok(await cacheWebhook('qldapm-reconciliation',{}));assert.ok(!after.missing_point_ids.includes(own.id));
  return {deliberate_removed_point:own.id,drift,repaired,after,scope:'Targeted fixture point repaired; text-only imported baseline has separately reported vector drift'};
 });
 await check('WF16',async()=>{assert.ok(monitorFault);const again=await webhook('qldapm-monitoring',{},null);ok(again);assert.equal(again.body.cached,true);assert.equal(again.body.correlation_id,monitorFault.body.correlation_id);return {failure:monitorFault.body,cached_after_dependency_recovery:again.body,scope:'Real paused clone Qdrant detected and persisted; receipt is cached for the configured 15-minute bucket'};});
 await check('ACL_REVOKE',async()=>{
  const before=ok(await webhook('qldapm-ingest',{source_key:'clone-contract',operation:'search',query:'workflow'},'20'));assert.ok(before.items.length);
  const setup=await fixtureSignal('acl-revoke-request.json','acl-revoked.json');assert.equal(setup.memberships,0);
  const search=await webhook('qldapm-ingest',{source_key:'clone-contract',operation:'search',query:'workflow'},'20');assert.ok([403,404].includes(search.status));assert.ok(!search.body.result);
  const agent=await webhook('qldapm-agent-request',{prompt:'Đọc công việc '+id,request_id:crypto.randomUUID()},'20');assert.ok([403,404].includes(agent.status));assert.ok(!agent.body.result);
  return {setup,before_source_id:before.items[0].source_id,search_denied:search,agent_denied:agent,scope:'Fresh Native membership checked before retrieval and agent enqueue'};
 });
 await check('DELETE_TOMBSTONE',async()=>{
  const protectedTask=await command('get_work_package',{id});
  const denied=await http(gateway+'/api/v1/commands',{action:'delete_work_package',arguments:{id,lock_version:protectedTask.lockVersion},idempotency_key:crypto.randomUUID()},{Authorization:'Bearer '+tokens['18']});
  assert.equal(denied.status,422);assert.ok((denied.body.error||'').includes('NATIVE_DELETE_NEW_ORPHAN_TASK_REQUIRED'));
  const create=await command('create_work_package',{source_id:'CLONE-DELETE-'+crypto.randomUUID(),subject:'Isolated disposable deletion fixture',type_id:1});
  const created=await webhook('qldapm-execute-mutation',{proposal_id:create.id,hash:create.hash,decision:'approve'});ok(created);
  const deletionId=created.body.result.id;
  let indexed;for(let i=0;i<100;i++){indexed=await command('knowledge_sync_status',{id:created.body.knowledge_sync.id});if(indexed.state==='verified')break;await new Promise(r=>setTimeout(r,1000));}
  assert.equal(indexed.state,'verified');
  return deleteFixture(deletionId,denied.status);
 });
 async function deleteFixture(id,protected_task_http){
  const before=await command('get_work_package',{id});const p=await command('delete_work_package',{id,lock_version:before.lockVersion});
  const deleted=await webhook('qldapm-execute-mutation',{proposal_id:p.id,hash:p.hash,decision:'approve'});ok(deleted);const receipt=deleted.body;assert.ok(receipt.knowledge_sync);
  const native=await http(gateway+'/api/v1/commands',{action:'get_work_package',arguments:{id}},{Authorization:'Bearer '+tokens['18']});assert.equal(native.status,404);
  let sync;for(let i=0;i<100;i++){sync=await command('knowledge_sync_status',{id:receipt.knowledge_sync.id});if(sync.state==='verified')break;await new Promise(r=>setTimeout(r,1000));}
  assert.equal(sync.state,'verified');assert.equal(sync.result.native_deleted,true);
  const search=await http(gateway+'/api/v1/commands',{action:'knowledge_search',arguments:{query:'Isolated approved workflow fixture',native_ids:[id]}},{Authorization:'Bearer '+tokens['18']});
  assert.ok([403,404,422].includes(search.status)||search.status===200&&search.body.result.items.length===0);
  const points=await http('http://qldapm-qdrant:6333/collections/qldapm_knowledge_dense/points/scroll',{limit:10000,with_payload:true,with_vector:false});assert.equal(points.status,200);assert.ok(points.body.result.points.every(p=>p.payload.work_package_id!==id));
  return {native_id:id,protected_task_http,proposal_id:p.id,receipt,sync,native_http:native.status,search_http:search.status,remaining_fixture_points:0,authorization_kind:'SIMULATED_ISOLATED_DISPOSABLE_FIXTURE_ONLY'};
 }
 if(rows.some(r=>r.state==='FAIL'))throw Error('BUSINESS_CHECKS_FAILED:'+rows.filter(r=>r.state==='FAIL').map(r=>r.code).join(','));
})().catch(e=>{console.error(e.message);process.exit(1)});

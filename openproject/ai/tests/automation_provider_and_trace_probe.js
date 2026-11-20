// Clone-only provider boundary and n8n trace check; no provider credentials are installed.
const fs=require('fs'),crypto=require('crypto'),assert=require('assert/strict'),root='/qualification';
const target=JSON.parse(fs.readFileSync(root+'/trace-target.json')),tokens=JSON.parse(fs.readFileSync(root+'/bearers.json'));
const secret=JSON.parse(fs.readFileSync(root+'/credentials.json')).find(c=>c.id==='2w9dSdmYbywZDuMB').data.value;
let cookie='';
async function http(url,body,headers={}){let r=await fetch(url,{method:body?'POST':'GET',headers:{'content-type':'application/json',...headers},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(115000)});let text=await r.text(),data;try{data=JSON.parse(text);}catch{data={error:'NON_JSON'};}return {status:r.status,body:data,headers:r.headers};}
async function api(path,body){const r=await http('http://localhost:5678'+path,body,{cookie});assert.equal(r.status,200);const cs=r.headers.getSetCookie();if(cs.length)cookie=cs.map(s=>s.split(';')[0]).join('; ');return r.body.data;}
(async()=>{
const owner=JSON.parse(fs.readFileSync(root+'/owner.json'));await api('/rest/login',{emailOrLdapLoginId:owner.email,password:owner.password});
const spec=JSON.parse(fs.readFileSync(root+'/WF03-probe.json'));let saved=await api('/rest/workflows',spec);await api('/rest/workflows/'+saved.id+'/activate',{versionId:saved.versionId,...(saved.checksum?{expectedChecksum:saved.checksum}:{})});
const headers={'X-QLDAPM-Webhook-Token':secret,Authorization:'Bearer '+tokens['18']};
const trace=await http('http://localhost:5678/webhook/qldapm-agent-trace',{run_id:target.run_id},headers);assert.equal(trace.status,200);assert.ok(trace.body.total_events>0);assert.ok(trace.body.events.every(x=>x.run_id===target.run_id));
const blocked=await http('http://localhost:5678/webhook/qldapm-agent-request',{operation:'plan',request_id:crypto.randomUUID(),prompt:'Phân tích chỉ đọc công việc #'+target.native_id+', không tạo đề xuất.'},headers);
assert.equal(blocked.status,503);assert.match(blocked.body.error,/GEMINI/);
const reads=await Promise.all(Array.from({length:3},async()=>{const started=performance.now();let response,attempts=0;for(;attempts<5;attempts++){response=await http('http://qldapm-ai-gateway-1:8090/api/v1/commands',{action:'knowledge_search',arguments:{query:'Automation stability isolated fixture',native_ids:[target.native_id]},idempotency_key:crypto.randomUUID()},{Authorization:'Bearer '+tokens['18']});if(response.status!==503)break;await new Promise(r=>setTimeout(r,1000));}assert.equal(response.status,200);assert.ok(response.body.result.items.some(x=>x.native_id===target.native_id));return {seconds:(performance.now()-started)/1000,attempts:attempts+1,citations:response.body.result.items.map(x=>({native_id:x.native_id,source_id:x.source_id,document_id:x.document_id,citation:x.citation,lock_version:x.lock_version}))};}));
const result={status:'CLONE_N8N_TRACE_PASS_LIVE_PROVIDER_BLOCKED',parent_trace_id:target.parent_trace_id,run_id:target.run_id,native_id:target.native_id,trace:{status:trace.status,body:trace.body},provider_boundary:{status:blocked.status,body:blocked.body},rag_reads:{concurrency:3,runs:reads},wf03:saved.id,at:new Date().toISOString()};
fs.writeFileSync(root+'/provider-trace-result.json',JSON.stringify(result));console.log(JSON.stringify({status:result.status,events:trace.body.total_events,provider_http:blocked.status}));
})().catch(e=>{console.error(e.message);process.exit(1)});

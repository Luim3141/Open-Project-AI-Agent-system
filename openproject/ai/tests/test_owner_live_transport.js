// Real inline Command Center transport in Node VM; no browser automation.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const template=fs.readFileSync(require('node:path').join(__dirname,'../core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'),'utf8');
const start=template.indexOf('  // Phase3 owner live transport'),end=template.indexOf('  // Phase 3.2 Modal',start);
assert(start>=0&&end>start,'missing owner JSON transport; existing handler permits native POST + only MODE polling');
const source=template.slice(start,end).replace(/<%= @project.identifier %>/g,'ai-dev-demo');
function harness(){
 const requests=[],timers=[],events={},toasts=[],elements={},replaced=[];
 const button={disabled:false,innerHTML:'Sync GitHub',classList:{add(){},remove(){}},setAttribute(){}};
 const form={id:'sync',tool:'engineering_github_sync',action:'/projects/ai-dev-demo/qldapm-ai/commands',dataset:{},closest(s){return s==='form'?this:s==='#qldapm-command-center'?{}:null;},querySelector(s){return s.includes('button')?button:s.includes('tool')?{value:this.tool}:null;}};
 for(const id of ['qcc-command-feedback','qcc-poll-status','qcc-last-refresh','tab-github','tab-reports','qcc-live-controls'])elements[id]={textContent:'',dataset:{},innerHTML:'OLD',contains(){return false;}};
 elements['qldapm-command-center']={dataset:{}};
 const document={hidden:false,activeElement:null,addEventListener(n,fn){events[n]=fn;},removeEventListener(n,fn){if(events[n]===fn)delete events[n];},getElementById(id){return elements[id]||null;},querySelector(s){return s.includes('csrf-token')?{content:'fixture-csrf'}:null;},querySelectorAll(){return [];}};
 const window={addEventListener(n,fn){events[n]=fn;},removeEventListener(n,fn){if(events[n]===fn)delete events[n];},location:{},crypto:{randomUUID(){return '10000000-0000-4000-8000-000000000001';}}};
 const context=vm.createContext({window,document,Date,Error,AbortController,crypto:window.crypto,qccOn(target,name,fn){target.addEventListener(name,fn);},FormData:class {constructor(form) {this.values={tool:form.tool,arguments:elements['qcc-schedule-args']?.value};}set(k,v){this.values[k]=v;}get(k){return this.values[k];}},setTimeout(fn,ms){let t={fn,ms};timers.push(t);return t;},clearTimeout(t){if(t)t.cancelled=true;},clearInterval(){},showClientToast(...v){toasts.push(v);},fetch(url,options){requests.push({url,options});return new Promise((resolve,reject)=>Object.assign(requests.at(-1),{resolve,reject}));}});
 function load(){vm.runInContext(source,context);}load();
 const submit=()=>{let e={target:form,preventDefault(){this.prevented=true;},stopImmediatePropagation(){}};events.submit(e);return e;};
 return {requests,timers,events,elements,document,window,form,button,toasts,submit,load,settle:()=>new Promise(setImmediate)};
}
function reply(revision=1,extra={}){return {engineering:{mode:'OFF',control:{state_revision:revision},queue:{active:0}},fragments:{'tab-github':'NEW REMOTE PR','tab-reports':'NEW REPORT'},...extra};}
(async()=>{
 const h=harness();h.submit();h.submit();
 const snapshot=harness();snapshot.events['turbo:before-cache']?.();snapshot.submit();assert.equal(snapshot.requests.length,1,'Turbo snapshot detached commands while the native AI page was still visible');
 const posts=h.requests.filter(r=>r.options.method==='POST');assert.equal(posts.length,1);assert.equal(posts[0].options.headers['X-CSRF-Token'],'fixture-csrf');assert.equal(posts[0].options.cache,'no-store');assert.equal(h.button.disabled,true);assert(h.button.innerHTML.includes('SYNCING'));
 posts[0].resolve({ok:true,status:200,json:async()=>reply(2,{result:{status:'SUCCESS',command_id:'cmd1',message:'Done'},correlation_id:'correlation1'})});await h.settle();
 assert.equal(h.elements['tab-github'].innerHTML,'NEW REMOTE PR','backend success did not refresh PRs');assert.equal(h.elements['tab-reports'].innerHTML,'NEW REPORT');assert.equal(h.button.disabled,false);assert(h.elements['qcc-command-feedback'].textContent.includes('correlation1'));
 const asyncSync=harness();asyncSync.submit();asyncSync.requests[0].resolve({ok:true,status:200,json:async()=>({result:{accepted:true,request_id:'10000000-0000-4000-8000-000000000001',operation_id:'sync-op',operation_state:'QUEUED',message:'Queued'}})});await asyncSync.settle();
 asyncSync.requests.at(-1).resolve({ok:true,status:200,json:async()=>reply(3,{engineering:{mode:'PAUSED',queue:{active:0},control:{state_revision:3},github_operations:[{operation_id:'sync-op',state:'COMPLETED',result:{changed:false,sync_meta:{total_checked:12,total_changed:0}}}]}})});await asyncSync.settle();
 assert(asyncSync.elements['qcc-command-feedback'].textContent.includes('SYNC COMPLETED — NO CHANGES'),'changed=false async completion remains silent');
 assert(asyncSync.elements['qcc-command-feedback'].textContent.includes('12'),'sync checked count missing');
 const denied=harness();denied.submit();denied.requests[0].resolve({ok:false,status:403,json:async()=>({error:'Access denied'})});await denied.settle();assert(denied.elements['qcc-command-feedback'].textContent.includes('403'));assert.equal(denied.button.disabled,false);
 const serverError=harness();serverError.submit();serverError.requests[0].resolve({ok:false,status:500,json:async()=>({error:'Response failed after effect'})});await serverError.settle();assert.equal(serverError.button.disabled,true,'ambiguous server500 permits newUUID replay');assert(serverError.window.qccLive.unknownRequest);assert(serverError.form.dataset.qccRequestId);
 const conflict=harness();conflict.submit();conflict.requests[0].resolve({ok:true,status:200,json:async()=>reply(10,{result:{accepted:false,reason_code:'ENGINEERING_STATE_REVISION_CONFLICT',message:'Incorrect success'}})});await conflict.settle();assert(conflict.elements['qcc-command-feedback'].textContent.includes('ENGINEERING_STATE_REVISION_CONFLICT'),'rejected receipt displayed success');assert(!conflict.elements['qcc-command-feedback'].textContent.includes('Incorrect success'));
 const unknown=harness();unknown.submit();unknown.requests[0].reject(Error('network'));await unknown.settle();assert.equal(unknown.button.disabled,true,'unknown write outcome unlocked for replay');assert(unknown.elements['qcc-command-feedback'].textContent.includes('Chưa xác định'));unknown.form.dataset={};unknown.submit();assert.equal(unknown.requests.filter(r=>r.options.method==='POST').length,1,'unknown receipt bypassed via fresh fragment form');
 const p=harness();p.window.qccLive.refresh();p.window.qccLive.refresh();assert.equal(p.requests.length,1,'overlapping poll');
 p.submit();assert.equal(p.requests.filter(r=>r.options.method==='POST').length,1);p.requests[1].resolve({ok:true,status:200,json:async()=>reply(5,{result:{message:'Synced'}})});await p.settle();p.requests[0].resolve({ok:true,status:200,json:async()=>reply(4,{fragments:{'tab-github':'STALE'}})});await p.settle();assert.equal(p.elements['tab-github'].innerHTML,'NEW REMOTE PR');
 p.document.hidden=true;p.window.qccLive.refresh();p.requests.at(-1).resolve({ok:true,status:200,json:async()=>reply(5)});await p.settle();assert(p.timers.some(t=>t.ms===60000));p.document.hidden=false;p.events.visibilitychange();assert.equal(p.requests.at(-1).options.method,'GET');
 const recover=harness();recover.submit();recover.requests[0].reject(Error('lost response'));await recover.settle();
 recover.requests.at(-1).resolve({ok:true,status:200,json:async()=>reply(8,{engineering:{mode:'OFF',queue:{active:0},control:{state_revision:8,last_command:{request_id:'other'},recent_commands:[{request_id:'10000000-0000-4000-8000-000000000001',reason_code:'COMMAND_ACCEPTED'}]}}})});await recover.settle();assert.equal(recover.window.qccLive.unknownRequest,null,'matching durable receipt hidden by later operator command');assert.equal(recover.button.disabled,false,'matching receipt left stable modal button disabled');assert.equal(recover.form.dataset.qccSubmitting,undefined);
 const sched=harness();sched.form.id='qcc-schedule-form';sched.form.tool='engineering_report_schedule_update';
 sched.elements['schedule-config-modal']={scheduleVersion:123.5};
 for(const [k,v] of Object.entries({daily_enabled:false,weekly_enabled:true,daily_hour:10,daily_minute:17,weekly_day:4,weekly_hour:13,weekly_minute:23}))sched.elements['sched_'+k]={value:String(v),checked:v};sched.elements['qcc-schedule-args']={value:''};sched.submit();
 assert.deepEqual(JSON.parse(sched.requests[0].options.body.get('arguments')),{daily_enabled:false,weekly_enabled:true,daily_hour:10,daily_minute:17,weekly_day:4,weekly_hour:13,weekly_minute:23,expected_updated:123.5});
 sched.requests[0].resolve({ok:true,status:200,json:async()=>({result:{updated:456.5,daily_hour:10}})});await sched.settle();
 assert.equal(sched.elements['schedule-config-modal'].scheduleVersion,456.5,'second edit conflicts with the editors own successful save');
 const active=harness();active.window.qccLive.refresh();active.requests[0].resolve({ok:true,status:200,json:async()=>reply(1,{engineering:{mode:'RUN_ONCE',queue:{active:1},control:{state_revision:1}}})});await active.settle();assert(active.timers.some(t=>t.ms===3000),'active work lacks fast bounded poll');
 const idle=harness();assert(idle.timers.some(t=>t.ms===15000),'idle polling interval missing');idle.events.offline();assert(idle.elements['qcc-poll-status'].textContent.includes('DISCONNECTED'));
 const nav=harness();const old=nav.window.qccLive;nav.load();assert.equal(old.stopped,true,'navigation retained old poll/listeners');nav.events.online();assert.equal(nav.requests.length,1);nav.events.pagehide();assert.equal(nav.window.qccLive.stopped,true);nav.events.pageshow();nav.submit();assert.equal(nav.requests.filter(r=>r.options.method==='POST').length,1,'native Back did not restore command transport');
 const slowSearch=harness();slowSearch.form.tool='knowledge_search';slowSearch.submit();
 assert.equal(slowSearch.window.qccLive.pending,false,'slow search freezes all controls');
 const controlButton={...slowSearch.button,disabled:false};const controlForm={...slowSearch.form,tool:'engineering_control',dataset:{},querySelector(s){return s.includes('button')?controlButton:s.includes('tool')?{value:this.tool}:null;}};
 slowSearch.events.submit({target:controlForm,preventDefault(){},stopImmediatePropagation(){}});
 assert.equal(slowSearch.requests.filter(r=>r.options.method==='POST').length,2,'control cannot be sent while read-only search is slow');
 assert(slowSearch.timers.some(t=>t.ms===110000),'knowledge deadline must cover the existing100s Rails read budget and rendering, while remaining bounded');
 const race=harness();race.form.tool='knowledge_search';
 race.elements['qcc-knowledge-results']={innerHTML:'OLD ANSWER',setAttribute(){}};
 race.elements['qcc-knowledge-status']={textContent:''};race.submit();
 assert.equal(race.elements['qcc-knowledge-results'].innerHTML,'','old answer remains under a new question');
 const otherButton={disabled:false,innerHTML:'Search file'};
 const otherForm={...race.form,tool:'knowledge_file_search',dataset:{},querySelector(s){return s.includes('button')?otherButton:s.includes('tool')?{value:this.tool}:null;}};
 race.events.submit({target:otherForm,preventDefault(){},stopImmediatePropagation(){}});
 const [firstQuery,secondQuery]=race.requests.filter(r=>r.options.method==='POST');
 assert(firstQuery.options.signal.aborted,'superseded read was not cancelled');
 secondQuery.resolve({ok:true,status:200,json:async()=>reply(3,{result:{},knowledge_html:'NEW ANSWER'})});await race.settle();
 firstQuery.resolve({ok:true,status:200,json:async()=>reply(2,{result:{},knowledge_html:'STALE ANSWER'})});await race.settle();
 assert.equal(race.elements['qcc-knowledge-results'].innerHTML,'NEW ANSWER','late search overwrote the latest question');
 for(const outage of ['503','network']){
  const fileRead=harness();fileRead.form.tool='knowledge_file_read';fileRead.elements['qcc-knowledge-results']={innerHTML:'KEEP SOURCE CITATIONS',setAttribute(){}};fileRead.submit();
  if(outage==='503')fileRead.requests[0].resolve({ok:false,status:503,json:async()=>({error:'FILE_SOURCE_UNAVAILABLE'})});else fileRead.requests[0].reject(Error('offline'));
  await fileRead.settle();assert(!fileRead.window.qccLive.unknownRequest,'read-only file outage creates an unknown-write lock');assert.equal(fileRead.button.disabled,false);assert.equal(fileRead.form.dataset.qccRequestId,undefined);assert.equal(fileRead.elements['qcc-knowledge-results'].innerHTML,'KEEP SOURCE CITATIONS');
 }
 const busyRead=harness();busyRead.form.tool='knowledge_file_read';busyRead.window.qccLive.pending=true;busyRead.window.qccLive.unknownRequest='existing-write';busyRead.submit();assert.equal(busyRead.requests.length,1,'source read blocked by unrelated write reconciliation');busyRead.requests[0].resolve({ok:false,status:503,json:async()=>({error:'FILE_SOURCE_UNAVAILABLE'})});await busyRead.settle();assert.equal(busyRead.window.qccLive.pending,true,'read cleared a pending write');assert.equal(busyRead.window.qccLive.unknownRequest,'existing-write','read cleared an unresolved write');
 const restored=harness();restored.elements['qldapm-command-center']={dataset:{}};restored.events.pagehide();
 assert.equal(restored.window.qccLive.stopped,true);assert.equal(typeof restored.events['turbo:load'],'function','no transport recovery after Turbo cache restore');restored.events['turbo:load']();restored.submit();assert.equal(restored.requests.filter(r=>r.options.method==='POST').length,1,'restored page submits a native form instead of JSON transport');
 console.log('PASS Owner JSON POST/CSRF, single sync, fresh PR/report fragments, denied/unknown, stale ordering, bounded visibility/reconnect, navigation cleanup; OWNER UAT PENDING');
})().catch(e=>{console.error(e);process.exitCode=1;});

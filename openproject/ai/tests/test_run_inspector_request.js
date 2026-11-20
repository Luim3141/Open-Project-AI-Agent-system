const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const t=fs.readFileSync(require('node:path').join(__dirname,'../core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'),'utf8');
const a=t.indexOf('    // Open Execution Inspector Modal'),b=t.indexOf('\n  function formatVNDateTime',a);
const s=t.slice(a,b).replace(/\n  \}\);\s*$/,'').replace(/<%= @project.identifier %>/g,'ai-dev-demo');
function harness(){
 const elements={},requests=[],seen=[];const document={getElementById(id){return elements[id]||(elements[id]={style:{},textContent:'',innerHTML:''});}};
 const ctx=vm.createContext({document,fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject})),renderExecutionData:d=>seen.push(d),escapeQccHtml:x=>x});
 const click=vm.runInContext('(function(target,e){'+s+'})',ctx);
 return {elements,requests,seen,open(id){click({closest(){return {getAttribute(){return id;}};}},{preventDefault(){}});}};
}
(async()=>{
 const h=harness();h.open('A');h.open('B');h.requests[1].resolve({ok:true,json:async()=>({id:'B'})});await new Promise(setImmediate);h.requests[0].resolve({ok:true,json:async()=>({id:'A'})});await new Promise(setImmediate);assert.deepEqual(h.seen,[{id:'B'}],'late A evidence overwrote B inspector');
 assert.equal(h.requests[0].options.cache,'no-store');
 const err=harness();err.open('A');err.open('B');err.requests[1].resolve({ok:true,json:async()=>({id:'B'})});await new Promise(setImmediate);err.requests[0].reject(Error('old failure'));await new Promise(setImmediate);assert.notEqual(err.elements['qcc-run-modal-status-badge'].textContent,'ERROR');
 console.log('PASS inspector out-of-order success/error isolation, no-store');
})().catch(e=>{console.error(e);process.exitCode=1;});

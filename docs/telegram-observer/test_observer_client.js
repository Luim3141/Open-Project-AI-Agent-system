const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../../openproject/ai/core/overlay/app/views/qldapm_ai/_observer_client.html.erb'),'utf8').split('\n').slice(1,-2).join('\n');
function verifyCacheRestore(code){
  const listeners=new Map(),root={dataset:{endpoint:'/observer.json'}};
  const element={addEventListener(){},value:''};
  const document={hidden:true,getElementById:id=>id==='qldapm-agent-studio'?root:element,
    addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener(){}};
  const context=vm.createContext({document,window:{addEventListener(){}},setTimeout(){},clearTimeout(){},URL,AbortController});
  vm.runInContext(code,context);
  assert.equal(root.dataset.bound,'true');
  listeners.get('turbo:before-cache')();
  assert.equal(root.dataset.bound,undefined,'Cache restore must allow rebinding');
  vm.runInContext(code,context);
  assert.equal(root.dataset.bound,'true');
}
assert.throws(()=>verifyCacheRestore(source.replace('delete root.dataset.bound;','')),/Cache restore/);
verifyCacheRestore(source);
async function verifyReconnect(code){
  const elements=new Map(),timers=new Map();let counter=0,calls=0;
  const make=()=>({value:'',textContent:'',append(){},replaceChildren(){},addEventListener(){},
    classList:{values:new Set(),add(v){this.values.add(v)},remove(v){this.values.delete(v)},contains(v){return this.values.has(v)}}});
  const root={dataset:{endpoint:'/observer.json'}};
  const document={hidden:false,getElementById(id){if(id==='qldapm-agent-studio')return root;if(!elements.has(id))elements.set(id,make());return elements.get(id)},
    createElement:make,addEventListener(){},removeEventListener(){}};
  const context=vm.createContext({document,window:{addEventListener(){}},location:{origin:'http://fixture.invalid'},
    URL,AbortController,Date,clearTimeout:id=>timers.delete(id),setTimeout(fn,ms){const id=++counter;timers.set(id,{fn,ms});return id},
    async fetch(){if(++calls===1)throw new Error('temporary offline');return {ok:true,async json(){return {items:[]}}}}});
  vm.runInContext(code,context);await new Promise(setImmediate);
  const connection=elements.get('qobs-connection');
  assert.equal(connection.classList.contains('qobs-warning'),true,'Network failure must warn');
  const retry=[...timers.values()].find(t=>t.ms===20000);assert.ok(retry,'Failure backs off');
  await retry.fn();
  assert.match(connection.textContent,/Đã đồng bộ/);
  assert.equal(connection.classList.contains('qobs-warning'),false,'Recovered connection must clear its old warning');
}
verifyReconnect(source).then(()=>console.log('PASS: cache restore and polling failure/recovery'))
  .catch(error=>{console.error(error.message);process.exitCode=1});

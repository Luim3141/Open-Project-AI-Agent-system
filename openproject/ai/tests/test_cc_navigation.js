// Executes the real navigation handler with OpenProject's <base href="/">.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'),'utf8');
assert.match(source,/<div id="qldapm-command-center"[^>]*data-turbo="false"/,'crossing to Native Angular must use full navigation so browser Back restores the AI document');
const helper=source.indexOf('  function qccRememberRun('),start=helper>=0?helper:source.indexOf('  function restoreActiveTab()'),end=source.indexOf('  // Client-side Toast Helper',start);
const callbacks={},saved={};
function node(id){return {id,attrs:{'data-tab':id},classList:{value:false,add(){this.value=true;},remove(){this.value=false;}},getAttribute(k){return this.attrs[k];},setAttribute(k,v){this.attrs[k]=v;}};}
const nav=['tab-mission','tab-github','tab-backlog'].map(node),panes=nav.map(n=>node(n.id));
const location=new URL('http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?run_id=fixture#tab-mission');
const history={entries:[],replaceState(_state,_title,value){this.entries.push(['replace',value]);location.href=new URL(value,'http://127.0.0.1:18088/').href;},pushState(_state,_title,value){this.entries.push(['push',value]);location.href=new URL(value,'http://127.0.0.1:18088/').href;}};
const document={getElementById(id){return panes.find(n=>n.id===id);},querySelectorAll(selector){return selector==='.qcc-nav-item'?nav:selector==='.qcc-tab-pane'?panes:[];}};
const context=vm.createContext({window:{location},history,localStorage:{getItem(k){return saved[k];},setItem(k,v){saved[k]=v;}},document,
 qccOn(_target,event,fn){(callbacks[event]??=[]).push(fn);},setTimeout(){},URL});
vm.runInContext(source.slice(start,end),context);
function click(id){const item=nav.find(n=>n.id===id);const target={closest(selector){return selector==='.qcc-nav-item'?item:null;}};for(const callback of callbacks.click)callback({target,preventDefault(){}});}
click('tab-backlog');
assert.equal(location.pathname,'/projects/ai-dev-demo/qldapm-ai','tab click changed canonical route to homepage; F5 loses AI Center');
assert.equal(location.search,'?run_id=fixture');assert.equal(location.hash,'#tab-backlog');
assert.equal(history.entries.at(-1)[0],'push','tab navigation does not participate in browser back/forward');
location.hash='#tab-github';for(const callback of callbacks.popstate||[])callback();
assert.equal(nav.find(n=>n.id==='tab-github').classList.value,true,'back/forward did not restore active panel');
assert.equal(nav.find(n=>n.id==='tab-github').attrs['aria-selected'],'true');
assert.equal(nav.find(n=>n.id==='tab-backlog').attrs['aria-selected'],'false');
assert.equal(typeof context.qccRememberRun,'function','selected Inspector run has no canonical URL persistence');
context.qccRememberRun('11111111-1111-4111-8111-111111111111');
assert.equal(location.pathname,'/projects/ai-dev-demo/qldapm-ai');
assert.equal(location.searchParams.get('run_id'),'11111111-1111-4111-8111-111111111111','F5 cannot restore selected run');
context.qccRememberRun(null);assert.equal(location.searchParams.has('run_id'),false,'closed Inspector still reopens on F5');
console.log('PASS canonical route/query, reload URL, tab back/forward and ARIA state');

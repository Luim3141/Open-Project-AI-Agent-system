const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb'),'utf8');
const helpers=source.slice(source.indexOf('  function qccShowModal('),source.indexOf("  qccOn(document,'click'",source.indexOf('  function qccShowModal(')));
const keyboard=source.slice(source.indexOf('  // Modal Escape key support'),source.indexOf('  // Phase3.1 owner filters'));
let keydown,aborts=0,remembered;
const document={activeElement:null,querySelectorAll(){return [modal];},querySelector(){return fallback;}};
function item(){return {isConnected:true,focus(){document.activeElement=this;},getClientRects(){return [1];}};}
const first=item(),last=item(),opener=item(),fallback=item();
const modal={style:{display:'none'},querySelector(){return first;},querySelectorAll(){return [first,last];},contains(n){return [first,last].includes(n);},reportController:{abort(){aborts++;}},inspectorController:{abort(){aborts++;}}};
const context=vm.createContext({window:{location:{href:'http://127.0.0.1/projects/ai-dev-demo/qldapm-ai?run_id=fixture'}},document,URL,qccRememberRun(id){remembered=id;},qccOn(_target,event,fn){if(event==='keydown')keydown=fn;}});
vm.runInContext(helpers+keyboard,context);
context.qccShowModal(modal,opener);assert.equal(document.activeElement,first);
function press(key,shiftKey=false){let prevented=false;keydown({key,shiftKey,preventDefault(){prevented=true;}});return prevented;}
document.activeElement=last;assert(press('Tab'));assert.equal(document.activeElement,first);
assert(press('Tab',true));assert.equal(document.activeElement,last);
document.activeElement=opener;assert(press('Tab'));assert.equal(document.activeElement,first);
assert(press('Escape'));assert.equal(modal.style.display,'none');assert.equal(document.activeElement,opener);assert.equal(aborts,2);assert.equal(remembered,null);
context.qccShowModal(modal,opener);opener.isConnected=false;press('Escape');assert.equal(document.activeElement,fallback);
console.log('PASS modal initial focus, Tab/Shift+Tab containment, Escape abort, opener restore and replaced-opener fallback');

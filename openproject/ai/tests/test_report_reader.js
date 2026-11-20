// Executes actual reader transport in Node VM; Markdown/URL safety tested with Rails dependencies separately.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const template=fs.readFileSync(path.join(__dirname,'../core/overlay/app/views/qldapm_ai/_engineering_report_reader.html.erb'),'utf8');
assert(template.includes('<%= nonced_javascript_tag do %>'),'Report initializer must use the application CSP nonce');
const source=template.split('<%= nonced_javascript_tag do %>')[1].split('<% end %>')[0].replace(/<%= @project.identifier %>/g,'ai-dev-demo');
function harness(){
  const elements={},requests=[],copied=[],timers=[];
  function element(tag='div'){
    return {tagName:tag.toUpperCase(),textContent:'',innerHTML:'',style:{},hidden:false,children:[],attributes:{},nodeType:1,parentElement:null,
      get nextSibling(){return this.parentElement?.children[this.parentElement.children.indexOf(this)+1]||null;},
      setAttribute(k,v){this.attributes[k]=v;},appendChild(child){if(child.parentElement)child.parentElement.children.splice(child.parentElement.children.indexOf(child),1);this.children.push(child);child.parentElement=this;return child;},insertBefore(child,next){this.children.splice(this.children.indexOf(next),0,child);child.parentElement=this;},replaceChildren(){this.children=[];},querySelectorAll(){return [];},closest(){return null;},addEventListener(){}};
  }
  for(const id of ['qcc-report-modal','modal-report-title','qcc-modal-report-type','qcc-modal-report-time','qcc-modal-report-body','qcc-report-raw','qcc-report-toc-list','qcc-report-source-status','qcc-report-ai-status','qcc-report-raw-toggle','qcc-report-sections-toggle','qcc-report-toc','qcc-modal-report-status','qcc-report-summary','btn-copy-report','qcc-report-export'])elements[id]=element();
  const context=vm.createContext({window:{},AbortController,setTimeout(fn,ms){let timer={fn,ms};timers.push(timer);return timer;},clearTimeout(timer){timer.cleared=true;},document:{getElementById:id=>elements[id],createElement:element},navigator:{clipboard:{writeText(value){copied.push(value);return Promise.resolve();}}},fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}))});
  vm.runInContext(source,context);
  return {elements,requests,copied,timers,reader:context.window.qccReportReader,open(id){
    const attrs={'data-report-id':id,'data-report-title':id,'data-report-type':'DAILY','data-report-time':'1793610000'};
    const button={getAttribute:key=>attrs[key]};
    this.reader.handleClick({target:{closest:selector=>selector==='.qcc-read-report-btn'?button:null},preventDefault(){}});
  },click(id){const action=element('button');action.id=id;this.reader.handleClick({target:{closest:selector=>selector==='#qcc-report-modal'?elements['qcc-report-modal']:selector==='button'?action:null}});}};
}
function report(id,raw='## Đã lưu',html='<h2 id="report-section-1">Đã lưu</h2>'){
  return {id,title:'Báo cáo '+id,report_type:'DAILY',generated_at:1793610000,source_state:'HISTORICAL',source_status:'PARTIAL',ai_narrative_status:'GENERATED',metrics:{runs:{total:8,succeeded:3,failed_or_cancelled:5},work_packages:{total_items:4},github:{total_prs:null}},reader:{rendering:'COMMONMARK_SANITIZED',raw_markdown:raw,rendered_html:html}};
}
async function settle(){await new Promise(resolve=>setImmediate(resolve));}
async function run(){
  const basic=harness();basic.open('A');assert.equal(basic.requests.length,1);assert.equal(basic.requests[0].options.cache,'no-store');assert.equal(basic.requests[0].options.credentials,'same-origin');
  assert.equal(basic.elements['btn-copy-report'].disabled,true,'loading report can copy an empty document');
  assert.equal(basic.elements['qcc-report-export'].disabled,true,'loading report can export an empty document');
  assert.equal(basic.elements['qcc-modal-report-time'].textContent,'02/11/2026 16:00:00');
  const raw='## Gốc\n\n**Có nguồn** </script>';basic.requests[0].resolve({ok:true,json:async()=>report('A',raw,'<h2 id="report-section-1">Gốc</h2><p><strong>Có nguồn</strong></p>')});await settle();
  assert(basic.elements['qcc-modal-report-body'].innerHTML.includes('<strong>Có nguồn</strong>'));assert.equal(basic.elements['qcc-report-raw'].textContent,raw);
  assert.equal(basic.elements['btn-copy-report'].disabled,false);
  assert(basic.elements['qcc-report-source-status'].textContent.includes('HISTORICAL'));assert(basic.elements['qcc-report-source-status'].textContent.includes('PARTIAL'));assert(basic.elements['qcc-report-ai-status'].textContent.includes('chưa xác minh'));
  const summary=basic.elements['qcc-report-summary'].children.map(node=>node.textContent).join('\n');assert(summary.includes('Runs: 8'));assert(!summary.includes('Pull Requests: null'));assert(summary.includes('Không có trường tổng hợp'));
  basic.click('btn-copy-report');await settle();assert.equal(basic.copied[0],raw);
  basic.click('qcc-report-raw-toggle');assert.equal(basic.elements['qcc-report-raw'].hidden,false);assert.equal(basic.elements['qcc-modal-report-body'].hidden,true);
  for(const response of [{ok:false,status:503},{ok:true,json:async()=>report('B')},{ok:true,json:async()=>{throw Error('INVALID_JSON');}},{ok:true,json:async()=>({id:'A',narrative:'unsafe raw fallback forbidden'})}]){
    const h=harness();h.open('A');h.requests[0].resolve(response);await settle();assert(h.elements['qcc-modal-report-status'].textContent.startsWith('Lỗi nạp báo cáo ('),h.elements['qcc-modal-report-status'].textContent);assert(!h.elements['qcc-modal-report-body'].innerHTML.includes('unsafe'));
  }
  for(const fail of [false,true]){
    const h=harness();h.open('A');h.open('B');h.requests[1].resolve({ok:true,json:async()=>report('B','Current B','<p>Current B</p>')});await settle();
    if(fail)h.requests[0].reject(Error('Offline'));else h.requests[0].resolve({ok:true,json:async()=>report('A','Stale A','<p>Stale A</p>')});
    await settle();assert.equal(h.elements['qcc-modal-report-body'].innerHTML,'<p>Current B</p>');assert.equal(h.elements['qcc-report-modal'].reportMarkdown,'Current B');
  }
  const closed=harness();closed.open('A');closed.elements['qcc-report-modal'].style.display='none';closed.requests[0].resolve({ok:true,json:async()=>report('A')});await settle();assert.equal(closed.elements['qcc-modal-report-body'].innerHTML,'');
  const hidden=harness();hidden.open('A');hidden.requests[0].resolve({ok:true,json:async()=>({...report('A','', ''),data_hidden:true})});await settle();assert(hidden.elements['qcc-modal-report-status'].textContent.includes('đã ẩn'));
  const slow=harness();slow.open('A');assert.equal(slow.timers[0].ms,15000);slow.timers[0].fn();assert(slow.requests[0].options.signal.aborted);slow.requests[0].reject(Error('aborted'));await settle();assert(slow.elements['qcc-modal-report-status'].textContent.includes('Lỗi nạp báo cáo'));
  const switched=harness();switched.open('A');switched.open('B');assert(switched.requests[0].options.signal.aborted,'changing reports leaves the old request running');
  const sections=harness(),body=sections.elements['qcc-modal-report-body'],headings=[];
  for(let i=0;i<3;i++){const heading={tagName:'H3',nodeType:1,parentElement:body,id:'heading-'+i,textContent:'Section '+i,closest(){return null;},get nextSibling(){return this.parentElement.children[this.parentElement.children.indexOf(this)+1]||null;}};headings.push(heading);body.appendChild(heading);body.appendChild({tagName:'P',nodeType:1,parentElement:null,textContent:'Evidence '+i});}
  body.querySelectorAll=selector=>selector==='details'?body.children.filter(n=>n.tagName==='DETAILS'):selector.split(',').map(t=>t.toUpperCase()).includes('H3')?headings:[];
  sections.reader.render(report('sections'));assert.equal(body.querySelectorAll('details').length,3,'Daily h3 sections cannot be collapsed individually');
  sections.click('qcc-report-sections-toggle');assert(body.querySelectorAll('details').every(n=>n.open===false));sections.click('qcc-report-sections-toggle');assert(body.querySelectorAll('details').every(n=>n.open===true));
  console.log('PASS report reader: sanitized HTML, exact raw/copy, source/AI provenance, factual summary, timestamp, errors, no-store, stale success/error, closed/hidden guards; OWNER UAT PENDING');
}
run().catch(error=>{console.error(error);process.exitCode=1;});

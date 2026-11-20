"""Executed only inside the disposable Native/Gateway/n8n business harness."""

def api(action,arguments=None,actor=None,project=6,key=None):
    actor=actor or str(principal['principal_id'])
    command={'action':action,'arguments':arguments or {},'project_id':project,'idempotency_key':key or str(uuid.uuid4())}
    return py("bearers=json.load(open(fixture/'bearers.json'));r=httpx.post('http://qldapm-ai-gateway-1:8090/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+bearers["+repr(actor)+"]},json="+repr(command)+",timeout=90,trust_env=False);print(json.dumps({'status':r.status_code,'body':r.json()}))")

def command(action,arguments=None,**kwargs):
    response=api(action,arguments,**kwargs)
    assert response['status']==200,response
    return response['body']['result']

def drain(limit=12):
    return py("from gateway.service import Service\nfrom gateway.integration_events import deliver_pending\ns=Service(Store(root),c,'/tmp/delegated-workspaces');states=[]\nfor _ in range("+str(limit)+"):\n state=deliver_pending(s);states.append(state)\n if state=='IDLE':break\n time.sleep(5)\nwith s.store.connect() as d:\n receipts=[dict(r) for r in d.execute('SELECT o.workflow,o.state,r.execution_id,r.document FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id ORDER BY o.rowid')]\nprint(json.dumps({'states':states,'receipts':[{'workflow':r['workflow'],'state':r['state'],'execution_id':r['execution_id'],'business':json.loads(r['document'])['business_result'] if r['document'] else None} for r in receipts]}))")

def current():
    return py("n6=Native('http://web:8080',keys["+repr(str(principal['principal_id']))+"],6);n6.identity("+str(principal['principal_id'])+");w=n6.package("+str(fixture_info['fixture']['native_id'])+");print(json.dumps({'native_id':w['id'],'lock_version':w['lockVersion'],'status_id':int(w['_links']['status']['href'].rsplit('/',1)[1]),'description':w['description']['raw']}))")

def propose(action,value,key=None,version=None):
    before=current()
    return command('delegated_preview',{'native_id':before['native_id'],'lock_version':before['lock_version'] if version is None else version,'action':action,'value':value},key=key)

def proposal(identifier):
    return next(p for p in command('delegated_status')['proposals'] if p['id']==identifier)

def delegated_case():
    result['approval_stage']='DEFAULT_OFF_AND_IDENTITY_GUARDS'
    state=command('delegated_status');assert state['enabled'] is False
    before=current();waiting=propose('SET_FIXTURE_NOTE','CHECKED');drain()
    assert proposal(waiting['id'])['decision']=='REQUIRES_HUMAN_APPROVAL' and current()==before
    assert api('delegated_control',{'enabled':True,'expected_revision':0},actor='20')['status']==403
    enabled=command('delegated_control',{'enabled':True,'expected_revision':0});assert enabled['enabled'] is True
    assert api('engineering_control',{'mode':'AUTO'})['status']==403
    assert api('delegated_preview',{'native_id':before['native_id'],'lock_version':before['lock_version'],'action':'SET_FIXTURE_NOTE','value':'CHECKED'},actor='19')['status']==403
    key=str(uuid.uuid4());note=propose('SET_FIXTURE_NOTE','CHECKED',key=key);note_args=note['arguments'];drain()
    result['approval_stage']='NOTE_NATIVE_READBACK_AND_REPLAY'
    verified=proposal(note['id']);after=current()
    assert verified['state']=='BUSINESS_VERIFIED' and verified['decision']=='OWNER_DELEGATED_POLICY_APPROVED'
    assert verified['execution_principal']==principal['principal_id'] and verified['execution_principal']!=18
    assert after['lock_version']>before['lock_version'] and after['description'].endswith('CHECKED')
    assert command('delegated_preview',note_args,key=key)['id']==note['id'] and current()==after
    invalid=api('delegated_preview',{**note_args,'lock_version':after['lock_version'],'action':'DELETE_WORK_PACKAGE'})
    assert invalid['status']==200 and invalid['body']['result']['decision']=='REJECTED'
    stale=propose('SET_FIXTURE_NOTE','BASELINE',version=before['lock_version']);assert stale['decision']=='REJECTED' and current()==after
    assert api('delegated_preview',{**note_args,'lock_version':after['lock_version']},project=5)['status']==403
    result['approval_stage']='STALE_APPROVED_PROPOSAL_GUARD'
    # Advance the fixture after WF05; WF06 must reject the now stale approved proposal.
    stale_after=propose('SET_FIXTURE_NOTE','BASELINE');drain(limit=1)
    assert proposal(stale_after['id'])['state']=='APPROVED'
    native_before=current()
    py("n6=Native('http://web:8080',keys["+repr(str(principal['principal_id']))+"],6);w=n6.package("+str(native_before['native_id'])+");n6.call('/api/v3/work_packages/'+str(w['id']),'PATCH',{'lockVersion':w['lockVersion'],'description':{'format':'markdown','raw':"+repr(fixture_info['fixture']['marker']+'\nDelegated fixture state: BASELINE')+"}});print('{}')")
    changed=current();drain();assert proposal(stale_after['id'])['state']=='REJECTED' and current()==changed
    result['approval_stage']='VALID_BUG_NATIVE_TRANSITION'
    bug=propose('TRANSITION_FIXTURE_BUG',fixture_info['fixture']['target_status']);final_delivery=drain()
    bug_result=proposal(bug['id']);final=current()
    assert bug_result['state']=='BUSINESS_VERIFIED' and final['status_id']==fixture_info['fixture']['target_status']
    assert {r['workflow'] for r in final_delivery['receipts'] if r['state']=='ACKED'}=={'WF05','WF06','WF09'}
    assert any(r['business'] and r['business']['state']=='BUG_NATIVE_VERIFIED' for r in final_delivery['receipts'])
    assert final['description']==before['description']
    result['approval_stage']='FINAL_OFF_AUDIT_AND_N8N_EXECUTIONS'
    disabled=command('delegated_control',{'enabled':False,'expected_revision':1});assert disabled['enabled'] is False
    stored=py("s=Store(root)\nwith s.connect() as d:\n reports=[json.loads(r[0]) for r in d.execute(\"SELECT document FROM engineering_reports WHERE report_type='WORKFLOW_AUDIT'\")]\n notifications=d.execute(\"SELECT count(*) FROM engineering_notifications WHERE json_extract(metadata,'$.proposal_id') IS NOT NULL\").fetchone()[0]\n calls=d.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0]\n audit=[{'stage':r['stage'],'state':json.loads(r['document']).get('state'),'decision':json.loads(r['document']).get('decision')} for r in d.execute('SELECT stage,document FROM delegated_audit ORDER BY id')]\nprint(json.dumps({'reports':reports,'notifications':notifications,'generation_receipts':calls,'audit':audit}))")
    assert len(stored['reports'])==2 and stored['generation_receipts']==0 and stored['notifications']>=6
    assert api('delegated_control',{'enabled':True,'expected_revision':2})['status']==403
    execution_ids=sorted({r['execution_id'] for r in final_delivery['receipts'] if r['execution_id']})
    script="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT id,status,mode,workflowId FROM execution_entity ORDER BY id').all()));d.close()"
    executions=json.loads(run('exec',n8n,'node','-e',script))
    assert all(any(str(e['id'])==identifier and e['status']=='success' for e in executions) for identifier in execution_ids)
    return {'before':before,'after':final,'service_principal':principal['principal_id'],'note_proposal':note['id'],'bug_proposal':bug['id'],
        'note_compensation':'BASELINE restored; Native workflow does not permit IN ANALYSIS→NEW; owned non-coding fixture remains in its valid tested state',
        'stale_approved_proposal':stale_after['id'],'receipts':final_delivery['receipts'],
        'executions':executions,'stored':stored,'delegation_final_enabled':False,'human_approval_claimed':False,
        'generation_calls':0,'main_writes':0}

record('OWNER_DELEGATED_PROJECT6','Real service principal; WF05/06/09 Native effects, signed n8n receipts, stale/replay/project/action guards, report/notification and final OFF',delegated_case)

def delegated_core_case():
    import base64
    source=OUT.parent/'functional-completion/qualify_core.py'
    tree=ast.parse(source.read_text(encoding='utf-8'));ruby=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ruby' for t in n.targets))
    status=globals().get('core_status_override') or command('delegated_status',actor='18')
    # Native HTTP was proven above; stop Puma before a second Rails boot in this cgroup.
    if not globals().get('core_before_web'):
        pid=int(run('exec',clone['web'],'cat','/tmp/clone-web-server.pid').decode().strip());assert pid>1
        run('exec',clone['web'],'ruby','-e',"Process.kill('TERM',Integer(ARGV.fetch(0)))",str(pid));time.sleep(2)
    start=ruby.index('# Actual Native HTTP on clone;');end=ruby.index('# Exact Rails routing/login filter',start)
    ruby=ruby[:start]+ruby[end:]
    ruby=ruby.replace("native_http:'PASS'","native_http:'PREVIOUS_BACKEND_CASE_NOT_REPEATED'")
    marker='Qldapm::AiBridge.fixture=fixture;Qldapm::AiBridge.observed=[]'
    assert ruby.count(marker)==1
    encoded=base64.b64encode(json.dumps(status,ensure_ascii=False).encode()).decode()
    ruby=ruby.replace(marker,"require 'base64';fixture['delegated_approval']=JSON.parse(Base64.decode64('"+encoded+"'));\n"+marker)
    point=" when 'engineering_control'\n"
    assert ruby.count(point)==1
    ruby=ruby.replace(point," when 'delegated_preview' then {'id'=>'fixture-proposal','state'=>'ACCEPTED','request_id'=>command[:idempotency_key],'accepted'=>true}\n when 'delegated_control' then {'enabled'=>false,'revision'=>3,'request_id'=>command[:idempotency_key],'accepted'=>true}\n"+point)
    point='before_calls=Qldapm::AiBridge.observed.size'
    assert ruby.count(point)==1
    checks=r'''
delegated_page=Nokogiri::HTML.fragment(d['fragments']['tab-integrations'])
raise 'DELEGATED_PANEL_MISSING' unless delegated_page.at_css('#qcc-delegated-policy')
raise 'DELEGATED_FIXTURE_FORM_MISSING' unless delegated_page.css('form input[name="tool"][value="delegated_preview"]').size>=2
raise 'DELEGATED_OVERRIDE_MISSING' unless delegated_page.at_css('form input[name="tool"][value="delegated_control"]')
raise 'DELEGATED_IDENTITY_PROVENANCE_MISSING' unless delegated_page.text.include?('OWNER_DELEGATED_POLICY_APPROVED') && delegated_page.text.include?('BUSINESS_VERIFIED')
%w[delegated_preview delegated_control].each do |tool|
 args=tool=='delegated_preview' ? {'native_id'=>390,'lock_version'=>2,'action'=>'SET_FIXTURE_NOTE','value'=>'CHECKED'} : {'enabled'=>false,'expected_revision'=>2}
 http.post('/projects/ai-dev-demo/qldapm-ai/commands',params:{tool:tool,arguments:args.to_json,request_id:SecureRandom.uuid},headers:{'Accept'=>'application/json','X-CSRF-Token'=>csrf})
 raise 'DELEGATED_COMMAND_ROUTE_FAILED_'+tool+'_'+http.response.status.to_s unless http.response.status==200
 seen=Qldapm::AiBridge.observed.reverse.find{|x|x['action']==tool}
 raise 'DELEGATED_ARGUMENTS_CHANGED' unless seen['arguments']==args
end
'''
    ruby=ruby.replace(point,checks+point)
    output=run('exec','-i',clone['web'],'bundle','exec','rails','runner','-',data=ruby.encode(),timeout=180)
    proof=json.loads(output.decode().splitlines()[-1]);assert proof['status']=='PASS'
    return {**proof,'core_image':core,'delegated_forms':'PASS','delegated_authenticated_controller_commands':'PASS',
            'gateway_boundary':'synthetic response shim for controller/render; actual Native/Gateway/n8n effects verified in previous case',
            'human_browser_uat':False}

if result['checks'][-1]['status']=='BUSINESS_PASS_IN_CLONE':
    record('OWNER_DELEGATED_CORE','Actual Rails session/CSRF/routes/render for delegated forms and audit metadata; separate from actual Gateway business proof',delegated_core_case)

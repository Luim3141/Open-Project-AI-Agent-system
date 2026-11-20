"""Single controlled MAIN acceptance, using the real delegated principal's own bearer."""
import datetime,json,os,subprocess,time,uuid
from pathlib import Path
import httpx
OUT=Path(__file__).parent
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
intent=private/'main-delegated-acceptance-intent.json';assert not intent.exists(),'ACCEPTANCE_INTENT_EXISTS_RECONCILE_NO_REPLAY'
setup=json.loads((private/'delegated-main-registry.json').read_text());actor=setup['policy']['principal_id'];identifier=setup['fixture']['native_id']
deployed=json.loads((OUT/'delegated-candidate-v3/deployment.json').read_text());published=json.loads((OUT/'delegated-publish-result.json').read_text())
assert published['gateway_image']==deployed['images']['gateway'] and published['core_image']==deployed['images']['core']
def py(code):
    process=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=120)
    if process.returncode:
        (private/'main-delegated-diagnostic.log').write_bytes(process.stderr);raise RuntimeError('MAIN_READ_FAILED_PRIVATE_DIAGNOSTIC')
    return json.loads(process.stdout)
pre="import json,sqlite3\nfrom gateway.store import Store\nfrom gateway.native import Native\ns=Store('/state');c=json.load(open('/state/config.json'))\n"
tokens=py(pre+"actors=["+str(actor)+",20];tokens={}\nfor a in actors:\n n=Native(c['openproject_url'],s.credential(a),6);who=n.identity(a);assert who['role']=='PM'\n tokens[str(a)]=s.issue_token(a,'PM',s.credential(a))\nprint(json.dumps(tokens))")
(private/'main-delegated-bearers.json').write_text(json.dumps(tokens))
def api(action,args=None,*,caller=actor,project=6,key=None):
    body={'action':action,'arguments':args or {},'project_id':project,'idempotency_key':key or str(uuid.uuid4())}
    response=httpx.post('http://127.0.0.1:18089/api/v1/commands',headers={'Host':'qldapm-ai-gateway-1:8090','Authorization':'Bearer '+tokens[str(caller)]},json=body,timeout=100,trust_env=False)
    return response.status_code,response.json()
def command(action,args=None,**kwargs):
    status,body=api(action,args,**kwargs);assert status==200,{'http_status':status,'body':body};return body['result']
def current():
    return py(pre+"n=Native(c['openproject_url'],s.credential("+str(actor)+"),6);n.identity("+str(actor)+");w=n.package("+str(identifier)+");print(json.dumps({'id':w['id'],'version':w['lockVersion'],'status_id':int(w['_links']['status']['href'].rsplit('/',1)[1]),'status':w['_links']['status']['title'],'description':w['description']['raw']}))")
def propose(action,value,*,version=None,key=None):
    before=current();args={'native_id':identifier,'lock_version':before['version'] if version is None else version,'action':action,'value':value}
    return command('delegated_preview',args,key=key),args
def wait_for(proposal,states):
    deadline=time.monotonic()+150
    while time.monotonic()<deadline:
        doc=next(r for r in command('delegated_status')['proposals'] if r['id']==proposal['id'])
        if doc['state'] in states:return doc
        if doc['state'] in {'REJECTED','REQUIRES_HUMAN_APPROVAL','OUTCOME_UNKNOWN'}:raise AssertionError({'proposal':doc['id'],'state':doc['state'],'reason':doc.get('reason')})
        time.sleep(5)
    raise TimeoutError('MAIN_DELEGATED_RECEIPT_WAIT_EXPIRED_RECONCILE_NO_REPLAY')
before=current();status=command('delegated_status');assert status['enabled'] is False
record={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'project_id':6,'principal_id':actor,'fixture_before':before,'state':'PREPARED','human_approval_claimed':False}
with intent.open('x') as stream:json.dump(record,stream,indent=2)
activated=False;proposals=[]
try:
    waiting,_=propose('SET_FIXTURE_NOTE','CHECKED');proposals.append(wait_for(waiting,{'REQUIRES_HUMAN_APPROVAL'}));assert current()==before
    assert api('delegated_control',{'enabled':True,'expected_revision':0},caller=20)[0]==403
    assert api('engineering_control',{'mode':'AUTO'})[0]==403
    assert command('delegated_control',{'enabled':True,'expected_revision':0})['enabled'] is True;activated=True
    key=str(uuid.uuid4());note,note_args=propose('SET_FIXTURE_NOTE','CHECKED',key=key);proposals.append(wait_for(note,{'BUSINESS_VERIFIED'}));after_note=current()
    assert after_note['version']>before['version'] and after_note['description'].endswith('CHECKED')
    assert command('delegated_preview',note_args,key=key)['id']==note['id'] and current()==after_note
    stale,_=propose('SET_FIXTURE_NOTE','BASELINE',version=before['version']);assert stale['decision']=='REJECTED'
    invalid=command('delegated_preview',{**note_args,'lock_version':after_note['version'],'action':'DELETE_WORK_PACKAGE'});assert invalid['decision']=='REJECTED'
    outside=command('delegated_preview',{**note_args,'native_id':394,'lock_version':after_note['version']});assert outside['decision']=='REJECTED'
    assert api('delegated_preview',{**note_args,'lock_version':after_note['version']},project=5)[0]==403
    baseline,_=propose('SET_FIXTURE_NOTE','BASELINE');proposals.append(wait_for(baseline,{'BUSINESS_VERIFIED'}));assert current()['description']==before['description']
    bug,_=propose('TRANSITION_FIXTURE_BUG',setup['fixture']['target_status']);proposals.append(wait_for(bug,{'BUSINESS_VERIFIED'}))
    final=current();assert final['status_id']==setup['fixture']['target_status'] and final['description']==before['description']
    # Wait for the post-transition WF09 observer, without manually draining production.
    for _ in range(24):
        receipts=py(pre+"with s.connect() as d:rows=[dict(r) for r in d.execute(\"SELECT o.workflow,o.state,r.execution_id,r.document FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id WHERE json_extract(o.document,'$.payload.proposal_id') IN (\"+','.join('?' for _ in "+repr([p['id'] for p in proposals])+")+\") ORDER BY o.rowid\","+repr([p['id'] for p in proposals])+")]\nprint(json.dumps([{'workflow':r['workflow'],'state':r['state'],'execution_id':r['execution_id'],'business':json.loads(r['document'])['business_result'] if r['document'] else None} for r in rows]))")
        if any(r['workflow']=='WF09' and r['state']=='ACKED' and (r['business'] or {}).get('state')=='BUG_NATIVE_VERIFIED' for r in receipts):break
        time.sleep(5)
    else:raise TimeoutError('MAIN_BUG_POST_READBACK_RECEIPT_MISSING')
    reports=command('engineering_report_list',{'limit':20},caller=20)
    audit_reports=[r for r in reports['reports'] if r['report_type']=='WORKFLOW_AUDIT']
    assert len(audit_reports)>=3
    latest=command('engineering_report_get',{'id':audit_reports[0]['id']},caller=20)
    assert latest['source_versions_current'] is True and latest['facts']['execution_principal']==actor
    record.update(state='MAIN_BUSINESS_VERIFIED',fixture_after=final,proposals=proposals,negative_proposals=[stale['id'],invalid['id'],outside['id']],
                  receipts=receipts,latest_audit_report=latest['id'],latest_audit_source_state=latest['source_state'],
                  status_rollback='NOT_SUPPORTED_BY_NATIVE_WORKFLOW; owned non-coding fixture remains IN ANALYSIS; baseline note compensated')
finally:
    if activated:
        policy=command('delegated_status')
        if policy['enabled']:command('delegated_control',{'enabled':False,'expected_revision':policy['revision']})
    policy=command('delegated_status');record['delegation_final_enabled']=policy['enabled']
    record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();intent.write_text(json.dumps(record,indent=2)+'\n')
    (OUT/'main-delegated-business.json').write_text(json.dumps(record,indent=2)+'\n')
assert record['delegation_final_enabled'] is False
assert api('delegated_control',{'enabled':True,'expected_revision':policy['revision']})[0]==403
print(json.dumps({k:record[k] for k in ('state','principal_id','fixture_after','delegation_final_enabled')}))

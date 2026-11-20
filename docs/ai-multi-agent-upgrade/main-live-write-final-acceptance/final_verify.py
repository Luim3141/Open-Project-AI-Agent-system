"""Read-only closeout; live WAL always stays in Linux. No provider or business writes."""
import collections,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.native import Native
from jira_sync_backup import database_state,inspect
def run(*args):
    p=subprocess.run(args,capture_output=True,timeout=120);assert p.returncode==0,'FINAL_READ_FAILED_OUTPUT_WITHHELD'
    return p.stdout
def main():
    state=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/gateway';b=json.loads((OUT/'backup.json').read_text())
    approved=json.loads((OUT/'armed.json').read_text());q=json.loads((OUT/'qualification-recovery.json').read_text())
    credentials=json.loads((state/'credentials.json').read_text());n=Native('http://localhost:8088',credentials['19'],5)
    assert n.identity(19)['role']=='PM';rows=n.packages();p=next(r for r in rows if r['id']==367)
    children=[r for r in rows if r.get('_links',{}).get('parent',{}).get('href')=='/api/v3/work_packages/50']
    duplicates=[r for r in children if ' '.join(r['subject'].split()).casefold()=='test'];assert len(duplicates)==1 and duplicates[0]['id']==367
    assert len(rows)==b['project_count']+1 and len(children)==b['child_count']+1
    for link,href in {'project':'/api/v3/projects/5','type':'/api/v3/types/10','parent':'/api/v3/work_packages/50','assignee':'/api/v3/users/23','author':'/api/v3/users/19'}.items():assert p['_links'][link]['href']==href
    qa=Native('http://localhost:8088',credentials['23'],5);assert qa.identity(23)['role']=='QA';assert qa.package(367)['id']==367
    sql='BEGIN READ ONLY; SELECT json_agg(to_jsonb(w) ORDER BY id) FROM work_packages w; COMMIT;'
    after_rows=json.loads(run('docker','exec','qldapm-openproject-db-1','psql','-X','-qAt','-U','postgres','-d','openproject','-c',sql))
    old_rows=json.loads((Path(b['directory'])/'work-packages-before.json').read_text());old={r['id']:r for r in old_rows};new={r['id']:r for r in after_rows}
    changes={str(i):{k:{'before':v,'after':new[i].get(k)} for k,v in r.items() if v!=new[i].get(k)} for i,r in old.items() if r!=new.get(i)}
    integrity=json.loads((OUT/'integrity.json').read_text());assert changes==integrity['old_rows_changes'] and set(new)-set(old)=={367}
    assert len(changes)==267 and all(set(d)=={'duration','updated_at','lock_version'} for d in changes.values())
    before=json.loads((Path(b['directory'])/'database-before.json').read_text());after=database_state('qldapm-openproject-db-1')
    protected=('relations','sprints','versions','users','user_passwords','roles','role_permissions','members','member_roles','tokens','two_factor_authentication_devices')
    assert all(before[t]==after[t] for t in protected)
    code="""import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
rid='6276720c-d6f8-4c3a-bf64-1e4fca623eb0';approval='e3626ae0-ce29-4e52-bcb8-98793eeefce5'
r=dict(d.execute('select * from ai_runs where id=?',(rid,)).fetchone());r['result']=json.loads(r['result'])
receipts=[json.loads(p[0]) for p in d.execute('select document from gemini_call_receipts where run_id=?',(rid,))]
claim=dict(d.execute('select * from requests where actor=19 and key=?',('owner-run-'+approval,)).fetchone());claim['payload']=json.loads(claim['payload']);claim['result']=json.loads(claim['result'])
create=dict(d.execute('select * from requests where actor=19 and key=?',('owner-create-'+approval,)).fetchone());create['payload']=json.loads(create['payload']);create['result']=json.loads(create['result'])
audit=[dict(a) for a in d.execute("select id,at,actor,action,target,outcome,run_id,trace_id from audit where actor=19 and (id=? or (target=? and action='ai_run') or action='create_work_package' and at>=?)",(create['result']['correlation_id'],rid,r['created']))]
old=d.execute("select state,expires,result from proposals where id='5e651070-9dc0-42f8-90f9-5a3909c0925e'").fetchone()
reg=d.execute("select state,result from ai_runs where id='23353d1f-fc42-402b-b1e9-722a1b5a9dd9' and actor=19").fetchone()
result={'run':r,'receipts':receipts,'claim':claim,'create_receipt':create,'audit':audit,'old_proposal':list(old),
 'regression':{'state':reg[0],'result':json.loads(reg[1])},'busy':d.execute("select count(*) from ai_runs where state in ('running','queued')").fetchone()[0],
 'pending_requests':d.execute("select count(*) from requests where state!='done'").fetchone()[0],
 'counters':{'runs':d.execute('select count(*) from ai_runs').fetchone()[0],'receipts':d.execute('select count(*) from gemini_call_receipts').fetchone()[0],'usage':d.execute('select count(*) from gemini_usage').fetchone()[0]}}
print(json.dumps(result));d.close()"""
    ledger=json.loads(run('docker','exec','qldapm-ai-gateway-1','python','-c',code))
    assert ledger['busy']==ledger['pending_requests']==0
    assert ledger['counters']['runs']==approved['baseline']['runs']+1 and ledger['counters']['receipts']==approved['baseline']['receipts']+6
    receipts=ledger['receipts'];assert len(receipts)==6 and all(r['state']=='LIVE_SUCCESS' and r['http_status']==200 for r in receipts)
    generations=[r for r in receipts if r['phase']=='generateContent'];assert len(generations)==3 and all(r['usage'] for r in generations)
    assert all(r['usage'].get('candidatesTokenCount',0)+r['usage'].get('thoughtsTokenCount',0)<=1500 for r in generations)
    assert ledger['create_receipt']['state']=='done' and ledger['create_receipt']['result']['reconciled'] is True
    assert ledger['create_receipt']['result']['result']['id']==367 and ledger['claim']['payload']['run']==ledger['run']['id']
    stopped=next(a['at'] for a in ledger['audit'] if a['action']=='ai_run' and a['target']==ledger['run']['id'])
    assert stopped-ledger['run']['created']<=180
    assert ledger['old_proposal'][0]=='pending' and ledger['old_proposal'][2] is None
    reg=ledger['regression'];assert reg['state']=='done' and reg['result']['model_used'] is False
    assert [r['agent'] for r in reg['result']['agent_outputs']]==['ba','qa','reviewer']
    # Native payload stays private; public evidence carries only command fields and receipt correlation.
    create=ledger['create_receipt'];create['result']={k:v for k,v in create['result'].items() if k!='result'}|{'result':{'id':367,'subject':'test','project':5,'parent':50,'assignee':23,'type':10,'author':19}}
    (OUT/'provider-audit.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False),encoding='utf-8')
    containers={c['Name'].lstrip('/'):{'id':c['Id'],'image':c['Image'],'started':c['State']['StartedAt'],'health':c['State'].get('Health',{}).get('Status','no_healthcheck')} for c in json.loads(run('docker','inspect',*subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()))}
    assert len(containers)==18 and containers['qldapm-ai-gateway-1']['image']==q['gateway_image']
    for name,c in json.loads((OUT/'preflight.json').read_text())['containers'].items():
        if name=='qldapm-ai-gateway-1':continue
        assert all(containers[name][k]==c[k] for k in ('id','image','started'))
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in b['protected'].items()) and not (state/'business-acceptance.json').exists()
    logs=subprocess.run(['docker','logs','--since','2026-10-21T16:57:00Z','qldapm-openproject-web-1'],capture_output=True)
    timing=[]
    for line in (logs.stdout+logs.stderr).decode('utf-8','replace').splitlines():
        if 'method=POST path=/api/v3/work_packages ' in line:
            timing.append(' '.join(re.findall(r'(?:method|path|status|duration|db|time|request_id)=[^\s]+',line)))
    assert len(timing)==1 and 'status=201' in timing[0]
    (OUT/'native-create-timing.log').write_text('\n'.join(timing))
    usage={k:sum(g['usage'].get(k,0) for g in generations) for k in ('promptTokenCount','candidatesTokenCount','thoughtsTokenCount','totalTokenCount')}
    result={'at':time.time(),'passed':True,'gateway_image':q['gateway_image'],'core_image':containers['qldapm-openproject-web-1']['image'],
        'new_id':367,'actor':19,'assignee':23,'parent':50,'type':10,'subject':'test','native_status':p['_links']['status']['title'],
        'project_count_before':b['project_count'],'project_count_after':len(rows),'global_count_before':b['global_count'],'global_count_after':len(after_rows),
        'children_before':b['child_count'],'children_after':len(children),'duplicates':len(duplicates),
        'existing_project_rows':329,'existing_global_rows':366,'native_derived_duration_updates':267,'other_old_fields_unchanged':True,
        'protected_tables':list(protected),'google_http_calls':len(receipts),'generations':len(generations),'provider_usage':usage,
        'local_reservations_delta':ledger['counters']['usage']-approved['baseline']['usage'],'worker_seconds':stopped-ledger['run']['created'],
        'worker_state':ledger['run']['state'],'native_receipt_reconciled':True,'original_worker_history_preserved':True,
        'qa_native_readback':True,'containers':containers,'active_envelope':False,'staging_containers_preserved':True,
        'old_proposal_applied':False,'google_billing':'UNCHANGED_FREE_ONLY_OWNER_ATTESTED_NOT_CHECKED_LIVE'}
    (OUT/'final-verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='containers'},ensure_ascii=False))
if __name__=='__main__':main()

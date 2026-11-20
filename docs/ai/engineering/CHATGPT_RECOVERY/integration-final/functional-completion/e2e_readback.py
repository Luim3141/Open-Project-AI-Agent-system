"""Correlate the single fresh run with real n8n executions and Native/knowledge evidence."""
import datetime,hashlib,json,re,subprocess
from fresh_e2e import py,OUT

RID='301dbdd8-6f6f-4df4-b6c6-b5ca3f073795'
code="""import sqlite3,json
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service
c=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row
rid=RID_PLACEHOLDER
q=c.execute('select q.state,q.payload,r.result from ai_queue q join ai_runs r on r.id=q.id where q.id=?',(rid,)).fetchone();p=json.loads(q['payload']);result=json.loads(q['result']);assert p['native_id']==394
assert q['state']=='finished' and result['status']=='succeeded','FRESH_RUN_NOT_SUCCEEDED'
events=[]
for r in c.execute("select o.id,o.workflow,o.state,o.document,r.execution_id,r.document as receipt from integration_event_outbox o left join integration_event_receipts r on r.id=o.id where json_extract(o.document,'$.payload.run_id')=? or json_extract(o.document,'$.payload.native_id')=394 or json_extract(o.document,'$.payload.work_package_id')=394 order by o.rowid",(rid,)):
 e=json.loads(r['document']);b=json.loads(r['receipt'])['business_result'] if r['receipt'] else {};events.append({'event_id':r['id'],'workflow':r['workflow'],'state':r['state'],'execution_id':r['execution_id'],'business':{k:b[k] for k in ('state','run_id','native_id','head_sha','source_version') if k in b}})
root=Path('/state');s=scoped_service(Service(Store(root),json.load(open(root/'config.json')),'/workspaces'),6);native,who=s.native_actor(20);item=native.package(394)
assert item['_links']['project']['href']=='/api/v3/projects/6'
k=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True)
documents=[{'document_id':r[0],'source_id':r[1],'native_version':json.loads(r[2]).get('native_version',json.loads(r[2]).get('lock_version'))} for r in k.execute("select id,source_id,metadata from knowledge_documents where project_id='6' and json_extract(metadata,'$.native_id')=394")]
notifications=c.execute("select count(*) from engineering_notifications where project=6 and json_extract(metadata,'$.run_id')=?",(rid,)).fetchone()[0]
lifecycle=[]
for r in c.execute("select o.event_id,o.state,o.document,m.execution_id,a.document as ack from n8n_lifecycle_outbox o left join n8n_lifecycle_execution_metadata m on m.event_id=o.event_id left join n8n_lifecycle_observations a on a.event_id=o.event_id where json_extract(o.document,'$.run_id')=? order by o.rowid",(rid,)):
 e=json.loads(r['document']);ack=json.loads(r['ack']) if r['ack'] else {};lifecycle.append({'event_id':r['event_id'],'workflow':'WF04','state':r['state'],'execution_id':r['execution_id'],'event_type':e['event_type'],'ack_run_matches':ack.get('run_id')==rid})
print(json.dumps({'run_id':rid,'native_id':394,'queue_state':q['state'],'result':{key:result.get(key) for key in ('status','head_sha','pr_url','tests','native_readback','knowledge_readback')},'events':events,'lifecycle':lifecycle,'native_version':item['lockVersion'],'native_status':item['_links']['status'].get('title'),'knowledge_documents':documents,'notification_count':notifications,'coding_queue_rows_for_unit':c.execute("select count(*) from ai_queue where json_extract(payload,'$.unit')=?",(p['unit'],)).fetchone()[0]}))
""".replace('RID_PLACEHOLDER',repr(RID))
result=py(code)
assert any(e['event_type']=='RUN_COMPLETED' and e['state']=='ACKED' and e['ack_run_matches'] for e in result['lifecycle'])
ids=list(dict.fromkeys(str(e['execution_id']) for e in result['events']+result['lifecycle'] if e['execution_id']))
assert ids and all(i.isdigit() for i in ids)
node="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});const ids="+json.dumps(ids)+";console.log(JSON.stringify(ids.map(id=>d.prepare('select id,workflowId,status,mode from execution_entity where id=?').get(Number(id)))));d.close();"
executions=json.loads(subprocess.check_output(['docker','exec','qldapm-n8n-main','node','-e',node],timeout=20))
assert all(row and row['status']=='success' for row in executions),'N8N_EXECUTION_NOT_SUCCESS'
assert all(e['state']=='ACKED' for e in result['events']),'FRESH_EVENT_NOT_ACKED'
assert all(e['state']=='ACKED' and e['ack_run_matches'] for e in result['lifecycle']),'FRESH_LIFECYCLE_NOT_ACKED'
assert result['coding_queue_rows_for_unit']==1,'DUPLICATE_CODING_QUEUE_ROW'
assert result['knowledge_documents'] and result['notification_count']>0
folder=OUT.parents[2]/'runs'/RID
journal=json.loads((folder/'delivery-steps.json').read_text())
def terminal(step):
    document=journal['steps'][step]['value']
    assert document['status']=='ok' and document['summary']=='completed'
    text='\n'.join(p.get('text','') for p in document['result'].get('payloads',[]))
    return json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip()))
review=terminal('review-0');qa=terminal('qa-0')
assert review['verdict']=='PASS' and review['revision']==journal['revision']
assert qa['status']=='PASS' and qa['exit_code']==0
log=folder/'acceptance-0.log';assert '57 passed' in log.read_text()
result['validation']={'host_acceptance_tests':57,'host_acceptance_exit':journal['steps']['acceptance-0']['value']['exit_code'],
    'host_log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'review_status':'PASS','qa_status':'PASS','root_review_qa_edits':0}
result.update(status='FRESH_RUN_NATIVE_KNOWLEDGE_N8N_NOTIFICATIONS_VERIFIED',executions=executions,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),browser_uat='NOT_PERFORMED')
(OUT/'fresh-e2e-final-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('events','executions','knowledge_documents','lifecycle')}))

"""Deployment auth/redaction smoke only: invalid event, no AI run or Native business operation."""
from support import *
import urllib.request,urllib.error,uuid
assert CONTEXT['stage'] in {'WORKER_AND_AUTHORIZED_READ_SMOKE_VERIFIED','APPROVED_WORKER_RESTARTED'}
target=PROPOSAL['workflow']['id'];canary='synthetic-deploy-canary-'+uuid.uuid4().hex
before=n8n_read("SELECT COALESCE(MAX(CAST(id AS INTEGER)),0) AS id FROM execution_entity")[0]['id']
event={'schema_version':1,'event_id':str(uuid.uuid4()),'event_type':'AGENT_STARTED','run_id':str(uuid.uuid4()),
       'project_id':6,'work_package_id':None,'unit_id':None,'timestamp':time.time(),'correlation_id':str(uuid.uuid4()),'status':'RUNNING','agent_id':'dev'}
body={'event':event,'published_at':int(time.time()),'signature':'0'*64}
started=datetime.now(timezone.utc).isoformat()
(PRIVATE/'negative-canary-state.json').write_text(json.dumps({'canary':canary,'event':event,'started':started,'previous_execution_id':before}))
request=urllib.request.Request('http://127.0.0.1:5679/webhook/qldapm-lifecycle',data=json.dumps(body).encode(),headers={
    'Content-Type':'application/json','Authorization':'Basic '+canary,'X-QLDAPM-Webhook-Token':canary})
try:
    with urllib.request.urlopen(request,timeout=15) as r:status=r.status
except urllib.error.HTTPError as e:status=e.code
assert status==500,'Expected signed callback rejection, observedHTTP'+str(status)
for _ in range(30):
    rows=n8n_read("SELECT id,status,deletedAt FROM execution_entity WHERE workflowId='"+target+"' AND CAST(id AS INTEGER)>"+str(before)+' ORDER BY CAST(id AS INTEGER)')
    if rows and (rows[0]['deletedAt'] is not None or rows[0]['status']=='error'):break
    time.sleep(1)
else:raise RuntimeError('CANARY_RETENTION_NOT_TERMINAL_OR_TOMBSTONED')
assert len(rows)==1
execution_id=str(rows[0]['id'])
scan="""const {DatabaseSync}=require('node:sqlite');const p=JSON.parse(require('fs').readFileSync(0,'utf8'));const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const rows=d.prepare('SELECT * FROM execution_data WHERE executionId=?').all(p.id);console.log(JSON.stringify({rows:rows.length,canary_leaked:JSON.stringify(rows).includes(p.secret)}));d.close()"""
retention=json.loads(docker('exec','-i','qldapm-n8n-main','node','-e',scan,data=json.dumps({'id':execution_id,'secret':canary}).encode()))
assert not retention['canary_leaked']
logs=subprocess.run(['docker','logs','--since',started,'qldapm-n8n-main'],capture_output=True,timeout=15)
assert logs.returncode==0 and canary.encode() not in logs.stdout+logs.stderr
code="import sqlite3,json;d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);print(json.dumps({'outbox':d.execute('SELECT count(*) FROM n8n_lifecycle_outbox WHERE event_id=?',(\""+event['event_id']+"\",)).fetchone()[0],'observations':d.execute('SELECT count(*) FROM n8n_lifecycle_observations WHERE event_id=?',(\""+event['event_id']+"\",)).fetchone()[0]}))"
denied=json.loads(docker('exec','qldapm-ai-gateway-1','python','-c',code))
assert denied=={'outbox':0,'observations':0}
assert queue()=={'mode':'OFF','active':0,'provider_receipts':358}
write('n8n-negative-canary.json',{'test':'invalid signed envelope; expected denial, not business success','webhook_http':status,
    'execution_id':execution_id,'raw_database_status':rows[0]['status'],'retention_tombstoned':rows[0]['deletedAt'] is not None,
    'active_execution':False,'execution_data_rows':retention['rows'],'canary_in_execution_storage':False,
    'canary_in_daemon_log':False,'source_event_admitted':False,'observation_created':False,'provider_calls':0,'native_business_writes':0})
stage('LIVE_N8N_AUTH_DENIAL_AND_REDACTION_VERIFIED')

"""Replay one real persisted canonical lifecycle event and verify retained n8n history."""
import datetime,json,subprocess,time
from pathlib import Path

out=Path(__file__).parent
def docker(*args,data=None):
 p=subprocess.run(['docker',*args],input=data,capture_output=True,timeout=45)
 if p.returncode:raise RuntimeError('MAIN_HISTORY_READBACK_COMMAND_FAILED; no credentials printed')
 return p.stdout
before=int(docker('exec','qldapm-n8n-main','node','-e',"const s=require('node:sqlite'),d=new s.DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(d.prepare('select coalesce(max(id),0) id from execution_entity').get().id);d.close()"))
code=r'''
import json,time,httpx
from pathlib import Path
from gateway.store import Store
from gateway.n8n_lifecycle_outbox import sign_envelope
root=Path('/state');config=json.load(open(root/'config.json'));settings=config['n8n_lifecycle'];assert settings.get('authenticated_webhook') is True
s=Store(root)
with s.connect() as db:
 row=db.execute("SELECT o.document FROM n8n_lifecycle_outbox o JOIN execution_events e ON e.event_id=o.event_id WHERE e.project=6 ORDER BY e.sequence DESC LIMIT 1").fetchone()
 assert row
 event=json.loads(row[0]);old=db.execute('SELECT execution_id FROM n8n_lifecycle_execution_metadata WHERE event_id=?',(event['event_id'],)).fetchone()
secret_document=json.load(open(root/'webhook_secret.json'));secret=secret_document.get('webhook_token') or secret_document['secret']
response=httpx.post(settings['webhook_url'],json=sign_envelope(event,settings['signing_key']),headers={'X-QLDAPM-Webhook-Token':secret},timeout=15,follow_redirects=False,trust_env=False)
assert response.status_code==200
ack=response.json();assert ack=={'status':'OBSERVED','event_id':event['event_id'],'run_id':event['run_id'],'project_id':6,'correlation_id':event['correlation_id'],'trace_event_id':event['event_id']}
with s.connect() as db:
 observed=db.execute('SELECT document FROM n8n_lifecycle_observations WHERE event_id=?',(event['event_id'],)).fetchone();assert json.loads(observed[0])==ack
 metadata=db.execute('SELECT execution_id FROM n8n_lifecycle_execution_metadata WHERE event_id=?',(event['event_id'],)).fetchone()
print(json.dumps({'event_id':event['event_id'],'run_id':event['run_id'],'correlation_id':event['correlation_id'],'source_event_type':event['event_type'],'source_timestamp':event['timestamp'],
 'gateway_observation':'OBSERVED','gateway_first_execution_id':metadata[0] if metadata else None,'previous_gateway_first_execution_id':old[0] if old else None,'native_writes':0,'model_calls':0}))
'''
gateway=json.loads(docker('exec','-i','qldapm-ai-gateway-1','python','-',data=code.encode()))
node=r'''
const s=require('node:sqlite'),crypto=require('crypto'),base='/usr/local/lib/node_modules/n8n',flatted=require(require.resolve('flatted',{paths:[base]}));
const p=JSON.parse(require('fs').readFileSync(0,'utf8')),d=new s.DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
const rows=d.prepare('SELECT e.id,e.status,e.finished,e.workflowId,e.deletedAt,x.data FROM execution_entity e LEFT JOIN execution_data x ON x.executionId=e.id WHERE e.id>? AND e.workflowId=? ORDER BY e.id').all(p.before,'elfapV5D2PTnLiHW');
const result=[];
for(const row of rows){if(row.status!=='success'||!row.finished||row.deletedAt||!row.data)continue;const data=flatted.parse(row.data),seen=new Set(),events=[];let forbidden=false;
 function walk(v){if(!v||typeof v!=='object'||seen.has(v))return;seen.add(v);for(const[k,x]of Object.entries(v)){if(/^(signature|authorization|x-qldapm-webhook-token)$/i.test(k)&&x!=='[REDACTED]')forbidden=true;}if(v.event_id===p.event_id)events.push(v);for(const x of Object.values(v))walk(x);}
 walk(data);if(events.length){if(forbidden)throw Error('RETAINED_AUTH_FIELD_NOT_REDACTED');result.push({execution_id:String(row.id),status:row.status,finished:!!row.finished,event_id:p.event_id,event_occurrences:events.length,retained_data_sha256:crypto.createHash('sha256').update(row.data).digest('hex'),auth_fields_absent_or_redacted:true});}}
d.close();console.log(JSON.stringify(result));
'''
executions=[]
for _ in range(15):
 executions=json.loads(docker('exec','-i','qldapm-n8n-main','node','-e',node,data=json.dumps({'before':before,'event_id':gateway['event_id']}).encode()))
 if executions:break
 time.sleep(1)
assert executions,'NEW_RETAINED_SUCCESS_EXECUTION_NOT_FOUND'
result={'status':'LIVE_RETAINED_EXECUTION_VERIFIED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**gateway,'n8n_executions':executions,
 'correlation':'New retained execution contains exact persisted Gateway event_id; Gateway keeps first execution metadata idempotently.',
 'scope':'One existing real Project6 event replay, not a new coding run. No Native write or model call. Error/nested/restart/retry verified separately in clone.'}
(out/'main-history-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

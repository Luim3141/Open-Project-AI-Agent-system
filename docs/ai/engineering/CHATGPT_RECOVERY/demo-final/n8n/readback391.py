"""Read existing new RUN_COMPLETED observation and retained n8n execution, no replay."""
import datetime,json,subprocess
from pathlib import Path
out=Path(__file__).parent
code=r'''
import json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True)
r=d.execute("SELECT e.event_id,e.document,m.execution_id,o.document FROM execution_events e JOIN n8n_lifecycle_execution_metadata m ON e.event_id=m.event_id JOIN n8n_lifecycle_observations o ON e.event_id=o.event_id WHERE e.run_id=? AND json_extract(e.document,'$.event_type')='RUN_COMPLETED' ORDER BY e.sequence DESC LIMIT 1",('b7fd6aec-3357-495f-b9e5-f7ba04d67ad6',)).fetchone()
assert r
event=json.loads(r[1]);ack=json.loads(r[3]);assert ack['event_id']==r[0] and ack['run_id']==event['run_id']
print(json.dumps({'event_id':r[0],'execution_id':r[2],'run_id':event['run_id'],'event_type':event['event_type'],'timestamp':event['timestamp'],'ack':ack}))
'''
p=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,check=True,timeout=30)
event=json.loads(p.stdout)
node=r'''
const fs=require('fs'),s=require('node:sqlite'),crypto=require('crypto'),p=JSON.parse(fs.readFileSync(0,'utf8'));
const db=new s.DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
const row=db.prepare('SELECT e.id,e.status,e.finished,e.deletedAt,x.data FROM execution_entity e JOIN execution_data x ON x.executionId=e.id WHERE e.id=?').get(p.execution_id);
if(!row||row.status!=='success'||!row.finished||row.deletedAt||!row.data)throw Error('RETAINED_COMPLETED_EXECUTION_REQUIRED');
const flat=require(require.resolve('flatted',{paths:['/usr/local/lib/node_modules/n8n']})),data=flat.parse(row.data),seen=new Set();let found=false;
function walk(v){if(!v||typeof v!=='object'||seen.has(v))return;seen.add(v);if(v.event_id===p.event_id)found=true;
for(const [k,x] of Object.entries(v)){if(/^(signature|authorization|x-qldapm-webhook-token)$/i.test(k)&&x!=='[REDACTED]')throw Error('UNREDACTED_AUTH_FIELD');walk(x);}}
walk(data);if(!found)throw Error('EVENT_CORRELATION_MISSING');db.close();
console.log(JSON.stringify({execution_id:String(row.id),status:row.status,finished:true,event_correlated:true,retained_sha256:crypto.createHash('sha256').update(row.data).digest('hex'),auth_fields_absent_or_redacted:true}));
'''
p=subprocess.run(['docker','exec','-i','qldapm-n8n-main','node','-e',node],input=json.dumps(event).encode(),capture_output=True,check=True,timeout=30)
result={'status':'LIVE_RUN391_COMPLETED_EXECUTION_VERIFIED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**event,'n8n':json.loads(p.stdout),'replayed':False,'model_calls':0,'native_writes':0}
(out/'run391-completed-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

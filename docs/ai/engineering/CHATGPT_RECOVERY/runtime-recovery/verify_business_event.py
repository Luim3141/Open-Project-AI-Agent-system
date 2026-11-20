"""Read back one actual post-restart UI command through signed n8n observation."""
import datetime,json,subprocess,time
from pathlib import Path
OUT=Path(__file__).parent
code=r'''
import json,sqlite3
d=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);d.row_factory=sqlite3.Row
s=d.execute("SELECT * FROM workflow_command_sources WHERE action='sprint_risks' AND actor=18 ORDER BY created DESC LIMIT 1").fetchone()
doc=json.loads(s['document']);row=d.execute("SELECT o.state,o.error,o.document,r.document AS ack,r.execution_id FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id WHERE json_extract(o.document,'$.source_id')=?",('ui-command:'+s['id'],)).fetchone()
event=json.loads(row['document']) if row else {};ack=json.loads(row['ack']) if row and row['ack'] else {}
print(json.dumps({'command_id':s['id'],'created':s['created'],'model_used':doc['result']['model_used'],'report_id':doc['result']['report_id'],'report_sha256':doc['result']['report_sha256'],'outbox_state':row['state'] if row else None,'error':row['error'] if row else None,'event_id':event.get('event_id'),'workflow':event.get('workflow'),'correlation_id':event.get('correlation_id'),'business_result':ack.get('business_result'),'execution_id':row['execution_id'] if row else None}))
'''
for attempt in range(20):
    proof=json.loads(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=15))
    if proof['outbox_state']=='ACKED':break
    time.sleep(2)
start=datetime.datetime.fromisoformat(json.loads((OUT/'coordinated-start.json').read_text())['finished_utc']).timestamp()
assert proof['created']>start and proof['model_used'] is False and proof['workflow']=='WF08'
assert proof['outbox_state']=='ACKED' and proof['business_result']['state']=='COMMAND_RESULT_VERIFIED',proof
assert proof['business_result']['native_writes'] is False and proof['correlation_id']==proof['command_id']
js="const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});console.log(JSON.stringify(d.prepare('SELECT id,status,workflowId FROM execution_entity WHERE id=?').get(process.argv[1])))"
for attempt in range(10):
    execution=json.loads(subprocess.check_output(['docker','exec','qldapm-n8n-main','node','-e',js,proof['execution_id']]))
    if execution['status']=='success':break
    time.sleep(1)
expected=next(w['id'] for w in json.loads((OUT/'baseline.json').read_text())['workflow_pins'] if w['code']=='WF08')
assert execution['status']=='success' and execution['workflowId']==expected
proof.update(n8n_execution=execution,status='MAIN_UI_GATEWAY_SIGNED_N8N_NATIVE_READBACK_PASS',native_write=False)
(OUT/'business-after-restart.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps(proof))

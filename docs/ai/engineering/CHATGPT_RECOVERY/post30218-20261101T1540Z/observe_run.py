"""Read-only live metadata for the one authorized Project 6 E2E run."""
import json,sqlite3,sys,time
run=sys.argv[1]
db=sqlite3.connect('file:/state/gateway.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row
q=db.execute('SELECT q.state,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON q.id=r.id WHERE q.id=?',(run,)).fetchone()
if not q:raise SystemExit('RUN_NOT_FOUND')
payload=json.loads(q['payload']);result=json.loads(q['result'] or '{}')
events=[json.loads(r[0]) for r in db.execute('SELECT document FROM execution_events WHERE run_id=? ORDER BY sequence',(run,))]
outbox=[dict(r) for r in db.execute("SELECT o.state,count(*) AS count FROM n8n_lifecycle_outbox o JOIN execution_events e ON e.event_id=o.event_id WHERE e.run_id=? GROUP BY o.state",(run,))]
observation=db.execute('SELECT count(*) FROM n8n_lifecycle_observations o JOIN execution_events e ON e.event_id=o.event_id WHERE e.run_id=?',(run,)).fetchone()[0]
checkpoint=db.execute('SELECT version,document FROM engineering_checkpoints WHERE run_id=?',(run,)).fetchone()
agent=db.execute('SELECT document FROM agent_runs WHERE id=?',(run,)).fetchone()
last=events[-1] if events else {}
print(json.dumps({'at':time.time(),'run_id':run,'queue_state':q['state'],'unit':payload.get('unit'),
  'stage':result.get('stage'),'status':result.get('status'),'error':result.get('error'),
  'agent_state':json.loads(agent['document']).get('state') if agent else None,
  'events':len(events),'last_event':{k:last.get(k) for k in ['event_type','agent_id','status','timestamp']},
  'outbox':outbox,'observations':observation,'checkpoint_version':checkpoint['version'] if checkpoint else None,
  'checkpoint_stage':json.loads(checkpoint['document']).get('stage') if checkpoint else None}))

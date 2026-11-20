"""Read-only Project 6 E2E preflight; print metadata only, never credentials."""
import json
import sqlite3
import time
from pathlib import Path
from gateway.store import Store
from gateway.service import Service
from gateway import engineering
from gateway.engineering_planning import definitions

store=Store('/state')
config=json.loads(Path('/state/config.json').read_text())
service=engineering.scoped_service(Service(store,config,Path('/workspaces')),6)
native,identity=engineering.authorized(service,20)
marker='QLDAPM-E2E-20261101-POST-ROLLOUT-001'
packages=native.packages()
matching=[p['id'] for p in packages if marker in p.get('subject','') or marker in p.get('description',{}).get('raw','')]
with store.connect() as db:
    mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
    active=db.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]
    receipts=db.execute('SELECT count(*) FROM gemini_call_receipts').fetchone()[0]
    worker=db.execute('SELECT worker_id,seen,run_id FROM engineering_worker_state WHERE project=6').fetchone()
    pending=db.execute("SELECT count(*) FROM requests WHERE state NOT IN ('done','rejected')").fetchone()[0]
    outbox=[dict(r) for r in db.execute('SELECT state,count(*) AS n FROM n8n_lifecycle_outbox GROUP BY state')]
    runs=[dict(r) for r in db.execute("SELECT json_extract(q.payload,'$.unit') AS unit,q.id,q.state,json_extract(r.result,'$.status') AS result FROM ai_queue q JOIN ai_runs r ON q.id=r.id WHERE json_extract(q.payload,'$.project_id')=6 AND json_extract(q.payload,'$.engine')='openclaw' ORDER BY q.created")]
units=[{'unit':key,'native_id':value.get('native_id'),'base_unit':value.get('base_unit'),'plan_id':value.get('plan_id')} for key,value in definitions(store,20).items()]
try:
    policy=service.gemini.settings()
    provider={'status':'POLICY_VERIFIED','model':policy['model'],'tier':policy['tier'],
              'billing_enabled':policy['billing_enabled'],'limits':policy['limits'],
              'readiness':service.gemini.readiness(policy)['state']}
except Exception as exc:
    provider={'status':'BLOCKED','error':str(exc) if str(exc).startswith('GEMINI_') else type(exc).__name__}
print(json.dumps({'at':time.time(),'project':6,'actor':identity['user_id'],'role':identity['role'],
 'marker_existing_native_ids':matching,'parent_id':379,'parent_lock':native.package(379)['lockVersion'],
 'project6_count':len(packages),'mode':mode,'active_queue':active,'provider_receipts':receipts,
 'worker':{'worker_id':worker['worker_id'],'age_seconds':time.time()-worker['seen'],'run_id':worker['run_id']} if worker else None,
 'pending_native_receipts':pending,'outbox':outbox,'runs':runs,'units':units,'provider':provider},ensure_ascii=False))

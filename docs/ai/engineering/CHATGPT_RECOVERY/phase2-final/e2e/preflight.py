"""Run inside Gateway; read-only business/preflight state, no generation or admission."""
import json,time,sys
from pathlib import Path
from gateway import engineering
from gateway.engineering_planning import planning_definition
from gateway.store import Store,pacific_day
from gateway.service import Service

spec=json.loads(sys.stdin.read())
store=Store('/state');service=engineering.scoped_service(Service(store,json.loads(Path('/state/config.json').read_text()),'/workspaces'),6)
native,who=engineering.authorized(service,20)
items=native.packages();parent=native.package(379)
assert not [p for p in items if spec['marker'] in json.dumps(p,ensure_ascii=False)]
policy=service.gemini.settings();ready=service.gemini.readiness(policy)
assert policy['tier']=='Free' and policy['billing_enabled'] is False and ready['state']=='READY'
unit='feedback-'+planning_definition(parent,spec['feedback'])['source_hash'][:16]
with store.connect() as db:
    active=db.execute("SELECT count(*) FROM ai_queue WHERE state!='finished'").fetchone()[0]
    mode=db.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
    assert active==0 and mode in {'OFF','PAUSED'}
    assert not db.execute("SELECT 1 FROM ai_queue WHERE payload LIKE ?",('%'+spec['marker']+'%',)).fetchone()
    daily=db.execute('SELECT count(*) FROM gemini_usage WHERE project=? AND at>=?',(policy['project'],pacific_day(time.time())[0])).fetchone()[0]
    assert policy['limits']['rpd']-daily>=70
    worker=dict(db.execute('SELECT worker_id,seen,run_id FROM engineering_worker_state WHERE project=6').fetchone())
    assert time.time()-worker['seen']<30 and worker['run_id'] is None
print(json.dumps({'at':time.time(),'actor':who['user_id'],'project':6,'parent_lock':parent['lockVersion'],
    'mode':mode,'active':active,'unit':unit,'branch':'codex/openclaw-'+unit,'quota_remaining':policy['limits']['rpd']-daily,
    'provider':'FREE_POLICY_CACHED_READINESS','worker_age':time.time()-worker['seen'],'marker':spec['marker']}))

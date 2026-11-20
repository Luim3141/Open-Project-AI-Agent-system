"""One Project6 source, one process-local canonical failure; production worker owns retry."""
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

OUT=Path(__file__).parent


def py(code):
    result=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code,
        text=True,capture_output=True,timeout=150)
    assert result.returncode==0,'SCOPED_MAIN_RECOVERY_FAILED: '+result.stderr[-600:]
    return json.loads(result.stdout.splitlines()[-1])


PRE="""import json,time,uuid
from pathlib import Path
from gateway.store import Store,canonical
from gateway.service import Service
from gateway.engineering import scoped_service
root=Path('/state');store=Store(root);config=json.load(open(root/'config.json'))
s=scoped_service(Service(store,config,'/workspaces'),6)
"""


def begin(existing_id=None):
    return py(PRE+f'existing_id={existing_id!r}\n'+"""
with store.connect() as d:
 assert d.execute("SELECT mode FROM engineering_control WHERE project=6").fetchone()[0]=='OFF'
 assert not d.execute("SELECT 1 FROM ai_queue WHERE state IN ('queued','executing')").fetchone()
 assert not d.execute("SELECT 1 FROM integration_event_outbox WHERE state IN ('PENDING','RETRY','SENDING')").fetchone()
native,who=s.native_actor(20);assert who['role']=='PM'
marker='RECOVERY-P6-'+uuid.uuid4().hex[:12]
item=native.package(existing_id) if existing_id else native.call('/api/v3/work_packages','POST',{'subject':marker,config['source_field']:marker,
 'description':{'raw':'Controlled Project6 recovery fixture. ORBIT-CANONICAL recovery requires a durable index failure receipt and current source citation. Not a coding task.'},
 '_links':{'project':{'href':'/api/v3/projects/6'},'type':{'href':'/api/v3/types/1'}}})
identifier=item['id'];key=f"native-event-6-{identifier}-{item['lockVersion']}-final-completion-{uuid.uuid4()}"
with store.connect() as d:
 d.execute('BEGIN IMMEDIATE');receipt={};store._enqueue_knowledge_sync(d,20,key,identifier,receipt)
 job=receipt['knowledge_sync']['id'];lease=str(uuid.uuid4())
 assert d.execute("UPDATE knowledge_sync SET state='running',attempts=1,lease=?,lease_until=? WHERE id=? AND state='pending'",(lease,time.time()+300,job)).rowcount==1
 claim=dict(d.execute('SELECT * FROM knowledge_sync WHERE id=?',(job,)).fetchone())
# Only this Store and Service instance can see the injection; the serving worker is untouched.
store.claim_knowledge_sync=lambda:claim
def fail_own_canonical(actor,native_id):
 assert actor==20 and native_id==identifier
 raise RuntimeError('CONTROLLED_OWN_JOB_CANONICAL_BOUNDARY_FAILURE')
s.sync_canonical_native=fail_own_canonical
assert s.process_knowledge_sync() is True
state=store.knowledge_sync(20,job);assert state['state']=='retry' and state['attempts']==1
if existing_id:
 # The first five-second retry overtook its event. Hold only this fixture for an observation window.
 with store.connect() as d:
  assert d.execute("UPDATE knowledge_sync SET next_at=max(next_at,?) WHERE id=? AND state='retry' AND attempts=1",(time.time()+30,job)).rowcount==1
 state=store.knowledge_sync(20,job)
print(json.dumps({'native_id':identifier,'native_version':item['lockVersion'],'job_id':job,'marker':marker,
 'failed_state':{k:state[k] for k in ['state','attempts','next_at','error']},'fault':'own process-local Service.sync_canonical_native only',
 'production_worker_unchanged':True,'global_retry_policy_unchanged':True,'own_fixture_observation_hold_seconds':30 if existing_id else 0,
 'native_creates':0 if existing_id else 1,'native_deletes':0,'coding_tasks_created':0}))
""")


def read(job,identifier):
    return py(PRE+f"""
job={job!r};identifier={identifier!r}
with store.connect() as d:
 rows=d.execute("SELECT o.id,o.state,o.attempts,o.error,o.document,r.execution_id,r.document AS receipt FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id WHERE json_extract(o.document,'$.payload.job_id')=? ORDER BY o.rowid",(job,)).fetchall()
 events=[{{'event_id':r['id'],'kind':json.loads(r['document'])['kind'],'state':r['state'],'attempts':r['attempts'],'execution_id':r['execution_id'],'business_result':json.loads(r['receipt'])['business_result'] if r['receipt'] else None}} for r in rows]
state=store.knowledge_sync(20,job)
print(json.dumps({{'job':state,'events':events}}))
""")


if __name__=='__main__':
    result={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':'MAIN',
        'route':'one isolated local job process; actual durable knowledge worker and normal 5-second integration outbox',
        'status':'RUNNING'}
    result.update(begin(int(sys.argv[1]) if len(sys.argv)>1 else None))
    path=OUT/'final-completion-main-wf14-recovery.json'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    for _ in range(24):
        observed=read(result['job_id'],result['native_id'])
        result['readback']=observed
        if observed['job']['state']=='verified' and {e['kind'] for e in observed['events'] if e['state']=='ACKED'}>={'INDEX_FAILED','INDEX_VERIFIED'}:break
        time.sleep(5)
    else:
        result['status']='INCOMPLETE';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
        raise SystemExit('RECOVERY_READBACK_INCOMPLETE')
    failures=[e for e in observed['events'] if e['kind']=='INDEX_FAILED']
    if not any(e['business_result']['state']=='WAITING_RETRY' for e in failures):
        result['status']='RECOVERY_VERIFIED_WF14_SUPERSEDED';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
        raise SystemExit('WF14_RETRY_WAS_NOT_OBSERVED')
    result['status']='MAIN_WF14_FAILURE_AND_WORKER_RECOVERY_VERIFIED'
    result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'native_id':result['native_id'],'job_id':result['job_id'],
        'executions':[{k:e[k] for k in ['kind','execution_id','state','business_result']} for e in observed['events']]}))

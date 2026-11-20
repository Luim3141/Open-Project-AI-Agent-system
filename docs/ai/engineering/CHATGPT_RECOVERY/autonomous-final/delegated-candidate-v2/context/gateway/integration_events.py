"""Durable Project6 integration observations; existing workers retain execution/retry ownership."""
import hmac
import hashlib
import json
import re
import time
import uuid
from urllib.parse import urlsplit

from .store import canonical, digest
from .n8n_lifecycle_outbox import http_transport, sign_envelope

PATH='/internal/automation/integration-event'
ROUTES={'NATIVE_CHANGED':'WF02','NATIVE_WITHDRAWN':'WF02','INDEX_VERIFIED':'WF13',
        'INDEX_FAILED':'WF14','RECONCILE_REQUESTED':'WF15','ENGINEERING_QA_RESULT':'WF11','GITHUB_PR_CHANGED':'WF04',
        'PLANNING_ACCEPTED':'WF03','PLANNING_PUBLISHED':'WF10',
        'UI_RISK_COMPLETED':'WF08','UI_BUG_TRIAGED':'WF09','UI_FILE_INDEXED':'WF01','UI_WBS_DRAFTED':'WF10',
        'DELEGATED_PREVIEW':'WF05','DELEGATED_EXECUTE':'WF06','DELEGATED_BUG_VERIFIED':'WF09','DELEGATED_BUG_REQUEST':'WF09'}
FIELDS={'job_id','native_id','source_hash','run_id','pr_number','head_sha','merge_target','state',
        'reviews_state','checks_state','work_package_id','attempts','error_code','command_id','action','proposal_id'}


def _planning_admission(contract):
    # Queue progress changes must not republish a new admission event on every tick.
    return digest(canonical({k:contract.get(k) for k in
        ('engine','project_id','native_id','source_version','kind','unit','request_key','spec_sha256')}))


def setup(db):
    db.execute("CREATE TABLE IF NOT EXISTS integration_event_outbox(id TEXT PRIMARY KEY,workflow TEXT NOT NULL,document TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'PENDING',attempts INTEGER NOT NULL DEFAULT 0,next_at REAL NOT NULL DEFAULT 0,lease TEXT,lease_until REAL NOT NULL DEFAULT 0,error TEXT)")
    db.execute('CREATE TABLE IF NOT EXISTS integration_event_receipts(id TEXT PRIMARY KEY,document TEXT NOT NULL,execution_id TEXT NOT NULL,observed REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS integration_event_claims(id TEXT PRIMARY KEY,lease TEXT NOT NULL,lease_until REAL NOT NULL)')


def enqueue(store,kind,source_id,source_version,*,correlation_id=None,payload=None):
    if kind not in ROUTES or not isinstance(source_id,str) or not 1<=len(source_id)<=200:
        raise ValueError('INTEGRATION_EVENT_SCOPE_INVALID')
    if not (type(source_version) is int and source_version>=0 or isinstance(source_version,str) and re.fullmatch('[a-f0-9]{64}',source_version)):
        raise ValueError('INTEGRATION_EVENT_VERSION_REQUIRED')
    payload=payload or {}
    if not isinstance(payload,dict) or set(payload)-FIELDS or len(canonical(payload))>3000:
        raise ValueError('INTEGRATION_EVENT_PAYLOAD_DENIED')
    for key,value in payload.items():
        if key in {'native_id','work_package_id','pr_number','attempts'}:
            if value is not None and (type(value) is not int or value<0):raise ValueError('INTEGRATION_EVENT_PAYLOAD_DENIED')
        elif value is not None and (not isinstance(value,str) or len(value)>200 or any(c in value for c in '\r\n')):
            raise ValueError('INTEGRATION_EVENT_PAYLOAD_DENIED')
    identity={'kind':kind,'source_id':source_id,'source_version':source_version,'payload':payload}
    identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,'qldapm.integration:'+digest(canonical(identity))))
    document={**identity,'schema_version':1,'event_id':identifier,'workflow':ROUTES[kind],'project_id':6,
              'timestamp':time.time(),'correlation_id':correlation_id or identifier,'idempotency_key':'integration:'+identifier}
    with store.connect() as db:
        setup(db)
        db.execute('INSERT OR IGNORE INTO integration_event_outbox(id,workflow,document) VALUES(?,?,?)',(identifier,ROUTES[kind],canonical(document)))
    return identifier


def publish(store):
    """Read durable source versions, not transient logs; no Native/provider calls."""
    from .workflow_commands import publish as publish_commands
    with store.connect() as db:setup(db)
    publish_commands(store)
    with store.connect() as db:
        setup(db)
        cursors=[dict(r) for r in db.execute('SELECT * FROM native_index_cursor WHERE project=6 AND actor=20')]
        jobs=[dict(r) for r in db.execute("SELECT * FROM knowledge_sync WHERE actor=20 AND request_key LIKE 'native-event-6-%' AND state IN ('verified','retry','dlq') ORDER BY rowid DESC LIMIT 100")]
        runs=[dict(r) for r in db.execute("SELECT q.id,q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.actor=20 AND json_extract(q.payload,'$.project_id')=6 AND q.state='finished' ORDER BY q.created DESC LIMIT 20")]
        planning=[dict(r) for r in db.execute("SELECT id,payload FROM ai_queue WHERE actor=20 AND json_extract(payload,'$.project_id')=6 AND json_extract(payload,'$.engine')='openclaw' AND json_extract(payload,'$.kind')='planning' ORDER BY created DESC LIMIT 20")]
        plans={r['id']:r['document'] for r in db.execute('SELECT id,document FROM engineering_plans WHERE actor=20')} if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_plans'").fetchone() else {}
    for row in cursors:
        enqueue(store,'NATIVE_CHANGED' if row['visible'] else 'NATIVE_WITHDRAWN',f"op:wp:{row['native_id']}",row['version'],
                payload={'native_id':row['native_id'],'source_hash':row['hash']})
    for row in jobs:
        kind='INDEX_VERIFIED' if row['state']=='verified' else 'INDEX_FAILED'
        enqueue(store,kind,'knowledge-job:'+row['id'],row['attempts'],payload={'job_id':row['id'],'native_id':row['native_id'],
            'state':row['state'],'attempts':row['attempts'],'error_code':row['error']})
    for row in runs:
        result=json.loads(row['result'] or '{}')
        if result.get('review_evidence') and result.get('test_evidence'):
            enqueue(store,'ENGINEERING_QA_RESULT','engineering:'+row['id'],digest(canonical(result)),
                    payload={'run_id':row['id'],'native_id':json.loads(row['payload'])['native_id'],'head_sha':result.get('head_sha')})
    for row in planning:
        contract=json.loads(row['payload']);payload={'run_id':row['id'],'native_id':contract['native_id']}
        enqueue(store,'PLANNING_ACCEPTED','engineering-planning:'+row['id'],_planning_admission(contract),
                correlation_id=row['id'],payload=payload)
        plan=json.loads(plans.get(row['id'],'{}'))
        if plan.get('state')=='PUBLISHED':
            enqueue(store,'PLANNING_PUBLISHED','engineering-plan:'+row['id'],digest(canonical(plan)),
                    correlation_id=row['id'],payload=payload)
    enqueue(store,'RECONCILE_REQUESTED','project:6:knowledge',int(time.time())//900)


def _repair_targets(store,report,items):
    from .knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
    storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(store.root/'knowledge.sqlite')))
    documents={d.source_hash:d for d in storage.query_documents('6')}
    sources={d.source_id:d.metadata.get('native_id') for d in documents.values()}
    points={str(uuid.uuid5(uuid.NAMESPACE_DNS,f"qldapm.chunk.{c['document_id']}:{c['chunk_index']}")):documents[c['document_id']].metadata.get('native_id')
        for c in storage._mock_tables[f'{storage.schema_name}.knowledge_chunks'].values() if c['document_id'] in documents}
    affected=set(report.get('missing_native_ids',[]));unmapped=[]
    for field in ['missing_point_ids','payload_mismatch_ids','invalid_chunk_hash_ids','invalid_source_hashes','fts_error_sources','stale_sources']:
        for identifier in report.get(field,[]):
            native_id=(points if field.endswith('_ids') else sources).get(identifier)
            if type(native_id) is int:affected.add(native_id)
            else:unmapped.append({'kind':field,'id':identifier})
    if report.get('orphan_fts_rows') or report.get('sqlite_quick_check','ok')!='ok':unmapped.append({'kind':'UNMAPPED_STORAGE_DRIFT'})
    visible={item['id']:item for item in items};outside=affected-set(visible)
    selected=[visible[identifier] for identifier in sorted(affected&set(visible))[:50]]
    return selected,{'affected_visible_sources':len(affected&set(visible)),'selected_sources':len(selected),
        'remaining_sources':max(0,len(affected&set(visible))-len(selected)),'unmapped_drift':len(unmapped),'outside_visible_scope':len(outside),
        'repair_scope_complete':not unmapped and not outside and len(affected&set(visible))<=50}


def _business(service,event):
    if event['kind'] in {'DELEGATED_PREVIEW','DELEGATED_EXECUTE','DELEGATED_BUG_VERIFIED','DELEGATED_BUG_REQUEST'}:
        from .delegated_approval import business
        return business(service,event)
    from .engineering import scoped_service
    scoped=scoped_service(service,6);store=scoped.store;p=event['payload'];kind=event['kind']
    if kind in {'UI_RISK_COMPLETED','UI_BUG_TRIAGED','UI_FILE_INDEXED','UI_WBS_DRAFTED'}:
        from .workflow_commands import business
        return business(service,event)
    if kind in {'PLANNING_ACCEPTED','PLANNING_PUBLISHED'}:
        with store.connect() as db:
            row=db.execute("SELECT payload,state FROM ai_queue WHERE id=? AND actor=20 AND json_extract(payload,'$.project_id')=6 AND json_extract(payload,'$.engine')='openclaw' AND json_extract(payload,'$.kind')='planning'",(p['run_id'],)).fetchone()
            saved=db.execute('SELECT document FROM engineering_plans WHERE id=? AND actor=20',(p['run_id'],)).fetchone() if kind=='PLANNING_PUBLISHED' else None
        if not row:raise PermissionError('PLANNING_SOURCE_REQUIRED')
        contract=json.loads(row['payload'])
        if contract['native_id']!=p['native_id']:raise PermissionError('PLANNING_NATIVE_SCOPE_DENIED')
        native,_=scoped.native_actor(20);item=native.package(p['native_id'])
        if kind=='PLANNING_ACCEPTED':
            if _planning_admission(contract)!=event['source_version']:return {'state':'SUPERSEDED','run_id':p['run_id']}
            return {'state':'PLANNING_ACCEPTED','run_id':p['run_id'],'native_id':item['id'],
                    'queue_state':row['state'],'execution_owner':'ENGINEERING_WORKER','native_write':False}
        if not saved:raise PermissionError('PUBLISHED_PLAN_REQUIRED')
        plan=json.loads(saved['document'])
        if digest(canonical(plan))!=event['source_version']:return {'state':'SUPERSEDED','run_id':p['run_id']}
        if (plan.get('id')!=p['run_id'] or plan.get('project_id')!=6 or plan.get('native_id')!=p['native_id'] or
            plan.get('state')!='PUBLISHED' or not plan.get('ba') or not plan.get('pm') or not plan.get('native_units')):
            raise ValueError('PUBLISHED_PM_BA_NATIVE_PLAN_REQUIRED')
        assignments={a['unit'] for a in plan['pm'].get('assignments',[])}
        if assignments!=set(plan['native_units']):raise ValueError('PLAN_NATIVE_UNIT_COVERAGE_REQUIRED')
        units=[native.package(unit['id'])['id'] for unit in plan['native_units'].values()]
        return {'state':'PLAN_NATIVE_UNITS_VERIFIED','run_id':p['run_id'],'native_id':item['id'],
                'plan_sha256':event['source_version'],'native_unit_ids':units,'ba_present':True,'pm_present':True,
                'native_write':False,'execution_owner':'ENGINEERING_WORKER'}
    if kind in {'NATIVE_CHANGED','NATIVE_WITHDRAWN'}:
        with store.connect() as db:row=db.execute('SELECT version,hash,visible FROM native_index_cursor WHERE project=6 AND actor=20 AND native_id=?',(p['native_id'],)).fetchone()
        if not row:raise ValueError('SOURCE_INVENTORY_REQUIRED')
        if row['version']!=event['source_version'] or row['hash']!=p['source_hash']:
            return {'state':'SUPERSEDED','native_id':p['native_id'],'source_version':row['version']}
        if not row['visible']:return {'state':'TOMBSTONED_VISIBILITY','native_id':p['native_id'],'physical_deletion':False}
        native,_=scoped.native_actor(20);item=native.package(p['native_id'])
        if item['lockVersion']!=row['version']:return {'state':'SUPERSEDED','native_id':item['id'],'source_version':item['lockVersion']}
        return {'state':'SOURCE_OBSERVED','native_id':item['id'],'source_version':item['lockVersion'],'index_owner':'GATEWAY_DURABLE_KNOWLEDGE_WORKER'}
    if kind in {'INDEX_FAILED','INDEX_VERIFIED'}:
        with store.connect() as db:row=db.execute('SELECT * FROM knowledge_sync WHERE id=? AND actor=20',(p['job_id'],)).fetchone()
        if not row or row['native_id']!=p['native_id'] or not row['request_key'].startswith('native-event-6-'):raise PermissionError('KNOWLEDGE_JOB_SCOPE_DENIED')
        if row['attempts']!=event['source_version'] or row['state']!=p['state']:
            return {'state':'SUPERSEDED','job_id':row['id'],'current_index_state':row['state']}
        if kind=='INDEX_FAILED':return {'state':'WAITING_RETRY' if row['state']=='retry' else 'BLOCKED_DLQ','job_id':row['id'],'next_at':row['next_at'],'attempts':row['attempts'],'retry_owner':'GATEWAY_DURABLE_KNOWLEDGE_WORKER'}
        result=json.loads(row['result'] or '{}')
        if result.get('vector_indexed') is not True:raise ValueError('VECTOR_AND_LEXICAL_INDEX_REQUIRED')
        native,who=scoped.native_actor(20);item=native.package(row['native_id'])
        if result.get('lock_version')!=item['lockVersion']:return {'state':'SUPERSEDED','job_id':row['id'],'source_version':item['lockVersion']}
        found=scoped.knowledge(who,native,'knowledge_search',{'query':item['subject'],'native_ids':[item['id']],'limit':5})
        if not any(r.get('native_id')==item['id'] and r.get('lock_version')==item['lockVersion'] and r.get('citation')==f"/work_packages/{item['id']}" for r in found.get('items',[])):
            raise ValueError('CURRENT_CITATION_READBACK_REQUIRED')
        return {'state':'INDEX_VERIFIED','job_id':row['id'],'source_version':item['lockVersion'],'native_id':item['id'],'citation':f"/work_packages/{item['id']}"}
    if kind=='ENGINEERING_QA_RESULT':
        with store.connect() as db:row=db.execute("SELECT q.payload,r.result FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE q.id=? AND q.actor=20 AND json_extract(q.payload,'$.project_id')=6 AND q.state='finished'",(p['run_id'],)).fetchone()
        if not row:raise PermissionError('ENGINEERING_QA_SOURCE_REQUIRED')
        result=json.loads(row['result'] or '{}');contract=json.loads(row['payload'])
        if digest(canonical(result))!=event['source_version']:return {'state':'SUPERSEDED','run_id':p['run_id']}
        test=result.get('test_evidence',{});review=result.get('review_evidence',{});qa=review.get('qa',{})
        if (result.get('status')!='succeeded' or not re.fullmatch('[a-f0-9]{40}',result.get('head_sha','')) or test.get('exit_code')!=0
            or not test.get('command') or review.get('verdict')!='PASS' or qa.get('status')!='PASS' or qa.get('exit_code')!=0):
            return {'state':'QA_BLOCKED','run_id':p['run_id'],'native_id':contract['native_id'],'native_approval':False}
        return {'state':'QA_VERIFIED','run_id':p['run_id'],'native_id':contract['native_id'],'tested_commit':result['head_sha'],
                'test_command':test['command'],'exit_code':0,'review_verdict':'PASS','qa_verdict':'PASS','native_approval':False}
    if kind=='GITHUB_PR_CHANGED':
        return {**p,'github_state':p.get('state'),'state':'DELIVERY_OBSERVED','native_write':False,'source_version':event['source_version']}
    if kind=='RECONCILE_REQUESTED':
        from .native_incremental import status
        scan_result=status(store,20,6)
        native,who=scoped.native_actor(20)
        # Fixed machine read; do not widen the public Engineering command allowlist.
        report=scoped.perform(who,native,'knowledge_integrity',{})
        jobs=[];repair_scope={}
        if report.get('status')=='DRIFT_DETECTED':
            targets,repair_scope=_repair_targets(store,report,native.packages())
            missing=digest(canonical({k:report.get(k) for k in ['missing_native_ids','missing_point_ids','payload_mismatch_ids','invalid_chunk_hash_ids','invalid_source_hashes','fts_error_sources','stale_sources']}))
            with store.connect() as db:
                # shortcut: bound affected-source repair to50; explicitly report the remainder.
                for item in targets:
                    receipt={};key=f"native-event-6-{item['id']}-{item['lockVersion']}-reconcile-{event['event_id']}-{missing}"
                    store._enqueue_knowledge_sync(db,20,key,item['id'],receipt)
                    jobs.append(dict(db.execute('SELECT id,state FROM knowledge_sync WHERE id=?',(receipt['knowledge_sync']['id'],)).fetchone()))
        pending=sum(row['state'] in {'pending','running','retry'} for row in jobs)
        state='REPAIR_QUEUED' if pending else 'RECONCILED' if report.get('status')=='VERIFIED' else 'DRIFT_OBSERVED'
        return {'state':state,'queued_jobs':pending,'repair_job_ids':[r['id'] for r in jobs],
                'inventory_observed_at':scan_result.get('observed_at'),'report_id':report.get('report_id'),'report_sha256':report.get('report_sha256'),
                'index_status':report.get('state') or report.get('status'),'native_writes':0,'repair_scope':repair_scope}
    raise ValueError('INTEGRATION_EVENT_KIND_DENIED')


def observe(service,envelope,execution_id):
    if not isinstance(envelope,dict) or set(envelope)!={'event','published_at','signature'}:raise PermissionError('INTEGRATION_ENVELOPE_DENIED')
    settings=service.config.get('n8n_integration',{});key=settings.get('signing_key') or service.config.get('n8n_lifecycle',{}).get('signing_key','')
    if not re.fullmatch('[a-f0-9]{64}',key):raise PermissionError('INTEGRATION_SIGNING_KEY_REQUIRED')
    unsigned={k:envelope[k] for k in ('event','published_at')}
    signature=hmac.new(key.encode('ascii'),canonical(unsigned).encode(),hashlib.sha256).hexdigest()
    if (not isinstance(envelope['signature'],str) or not hmac.compare_digest(signature,envelope['signature']) or
        type(envelope['published_at']) is not int or not -15<=time.time()-envelope['published_at']<=60):raise PermissionError('INTEGRATION_SIGNATURE_EXPIRED_OR_DENIED')
    event=envelope['event']
    if not isinstance(event,dict) or event.get('project_id')!=6 or not isinstance(execution_id,str) or not re.fullmatch('[0-9]{1,20}',execution_id):raise PermissionError('INTEGRATION_SCOPE_DENIED')
    lease=str(uuid.uuid4());now=time.time()
    with service.store.connect() as db:
        setup(db);db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT document FROM integration_event_outbox WHERE id=?',(event.get('event_id'),)).fetchone()
        if not row or row[0]!=canonical(event):raise PermissionError('INTEGRATION_SOURCE_DENIED')
        old=db.execute('SELECT document FROM integration_event_receipts WHERE id=?',(event['event_id'],)).fetchone()
        if old:return json.loads(old[0])
        claim=db.execute('SELECT lease_until FROM integration_event_claims WHERE id=?',(event['event_id'],)).fetchone()
        if claim and claim[0]>now:raise ValueError('INTEGRATION_OBSERVATION_BUSY')
        db.execute('INSERT INTO integration_event_claims VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET lease=excluded.lease,lease_until=excluded.lease_until',
                   (event['event_id'],lease,now+120))
    try:business=_business(service,event)
    except Exception:
        with service.store.connect() as db:db.execute('DELETE FROM integration_event_claims WHERE id=? AND lease=?',(event['event_id'],lease))
        raise
    ack={'status':'OBSERVED','event_id':event['event_id'],'workflow':event['workflow'],'project_id':6,
         'correlation_id':event['correlation_id'],'business_result':business}
    with service.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        claim=db.execute('SELECT lease FROM integration_event_claims WHERE id=?',(event['event_id'],)).fetchone()
        if not claim or claim[0]!=lease:raise ValueError('INTEGRATION_OBSERVATION_LEASE_LOST')
        db.execute('INSERT OR IGNORE INTO integration_event_receipts VALUES(?,?,?,?)',(event['event_id'],canonical(ack),execution_id,time.time()))
        db.execute('DELETE FROM integration_event_claims WHERE id=? AND lease=?',(event['event_id'],lease))
        return json.loads(db.execute('SELECT document FROM integration_event_receipts WHERE id=?',(event['event_id'],)).fetchone()[0])


def deliver_pending(service,*,transport=http_transport,now=None):
    settings=service.config.get('n8n_integration',{})
    if settings.get('enabled') is not True:return 'DISABLED'
    from .delegated_approval import publish as publish_delegated
    publish_delegated(service)
    base=settings.get('base_url','');url=urlsplit(base)
    if url.scheme not in {'http','https'} or not url.hostname or url.username or url.password or url.path not in {'','/'} or url.query or url.fragment:raise ValueError('INTEGRATION_TARGET_INVALID')
    key=settings.get('signing_key') or service.config.get('n8n_lifecycle',{}).get('signing_key','')
    if not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('INTEGRATION_SIGNING_KEY_REQUIRED')
    secret=json.loads((service.store.root/'webhook_secret.json').read_text());token=secret.get('webhook_token') or secret.get('secret')
    if not isinstance(token,str) or not 16<=len(token)<=512 or '\n' in token or '\r' in token:raise ValueError('INTEGRATION_WEBHOOK_KEY_REQUIRED')
    now=time.time() if now is None else now;lease=str(uuid.uuid4())
    with service.store.connect() as db:
        setup(db);db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT * FROM integration_event_outbox WHERE state IN ('PENDING','RETRY','SENDING') AND next_at<=? AND lease_until<=? ORDER BY rowid LIMIT 1",(now,now)).fetchone()
        if not row:return 'IDLE'
        db.execute("UPDATE integration_event_outbox SET state='SENDING',attempts=attempts+1,lease=?,lease_until=? WHERE id=?",(lease,now+60,row['id']))
    event=json.loads(row['document']);state='ACKED';error=None
    try:
        ack=transport(base.rstrip('/')+'/webhook/qldapm-integration-'+row['workflow'].lower(),sign_envelope(event,key),20,
                      headers={'X-QLDAPM-Webhook-Token':token})
        if (ack.get('status')!='OBSERVED' or ack.get('event_id')!=event['event_id'] or ack.get('workflow')!=row['workflow'] or
            ack.get('project_id')!=6 or ack.get('correlation_id')!=event['correlation_id'] or not isinstance(ack.get('business_result'),dict) or not ack['business_result'].get('state')):
            raise ValueError('INTEGRATION_BUSINESS_ACK_REQUIRED')
        with service.store.connect() as db:receipt=db.execute('SELECT document,execution_id FROM integration_event_receipts WHERE id=?',(event['event_id'],)).fetchone()
        if not receipt or receipt['document']!=canonical(ack) or not re.fullmatch('[0-9]{1,20}',receipt['execution_id']):raise ValueError('INTEGRATION_DURABLE_RECEIPT_REQUIRED')
    except Exception:state='DEAD' if row['attempts']+1>=5 else 'RETRY';error='INTEGRATION_DELIVERY_FAILED'
    with service.store.connect() as db:db.execute('UPDATE integration_event_outbox SET state=?,error=?,next_at=?,lease=NULL,lease_until=0 WHERE id=? AND lease=?',
        (state,error,now+min(300,5*2**row['attempts']),event['event_id'],lease))
    return state


def tick(service):
    if service.config.get('n8n_integration',{}).get('enabled') is not True:return 'DISABLED'
    now=time.monotonic()
    if now<getattr(service,'_n8n_integration_at',0):return 'THROTTLED'
    service._n8n_integration_at=now+5
    publish(service.store)
    return deliver_pending(service)


def dispatch(service):
    if service.config.get('n8n_integration',{}).get('enabled') is not True:return
    previous=getattr(service,'_n8n_integration_thread',None)
    if (previous is not None and previous.is_alive()) or time.monotonic()<getattr(service,'_n8n_integration_at',0):return
    def run():
        try:tick(service)
        except Exception as error:
            import logging
            logging.getLogger(__name__).warning('Integration delivery unavailable: %s',type(error).__name__)
    import threading
    service._n8n_integration_thread=threading.Thread(target=run,name='n8n-integration-delivery',daemon=True)
    service._n8n_integration_thread.start()


def snapshot(store):
    with store.connect() as db:
        setup(db);rows=db.execute('SELECT o.workflow,o.state,o.error,o.document,r.document AS receipt,r.execution_id,r.observed FROM integration_event_outbox o LEFT JOIN integration_event_receipts r ON r.id=o.id WHERE o.rowid IN (SELECT max(rowid) FROM integration_event_outbox GROUP BY workflow) ORDER BY o.rowid DESC').fetchall()
    latest={}
    for row in rows:
        if row['workflow'] in latest:continue
        event=json.loads(row['document']);ack=json.loads(row['receipt']) if row['receipt'] else {}
        latest[row['workflow']]={'workflow':row['workflow'],'integration_state':row['state'],'error':row['error'],'event_id':event['event_id'],
            'kind':event['kind'],'source_id':event['source_id'],'source_version':event['source_version'],'project_id':6,'timestamp':event['timestamp'],
            'business_result':ack.get('business_result'),'execution_id':row['execution_id'],'observed_at':row['observed'],'correlation_id':event['correlation_id']}
    return list(latest.values())


def response(service,scope,headers,body):
    from starlette.responses import JSONResponse
    try:
        if service.config.get('n8n_integration',{}).get('enabled') is not True or scope['method']!='POST' or scope.get('query_string') or headers.get('authorization') or headers.get('origin'):raise PermissionError('INTEGRATION_SCOPE_DENIED')
        return JSONResponse(observe(service,json.loads(body),headers.get('x-qldapm-n8n-execution')))
    except (KeyError,ValueError,TypeError,PermissionError):return JSONResponse({'error':'INTEGRATION_OBSERVATION_DENIED'},status_code=403)

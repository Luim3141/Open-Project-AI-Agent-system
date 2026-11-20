# Refresh only the isolated Gateway module after review fixes; retain Native/n8n/index state.
updated_source=ROOT/'openproject/ai/gateway/integration_events.py'
(code/'integration_events.py').write_bytes(updated_source.read_bytes())
result['gateway_sources']['integration_events.py']=hashlib.sha256(updated_source.read_bytes()).hexdigest()
run('restart',gateway)
for _ in range(30):
    try:
        if py("print(json.dumps(httpx.get('http://qldapm-ai-gateway-1:8090/health',trust_env=False).json()))").get('status')=='ok':break
    except RuntimeError:pass
    time.sleep(1)
else:raise RuntimeError('CLONE_GATEWAY_REFRESH_FAILED')
result['gateway_refreshed_for_review_fixes']=True
result['published_source_sha256']=hashlib.sha256(json.dumps([{k:r[k] for k in ['id','name','nodes','connections','settings']} for r in json.loads((BASE/'published-after.json').read_text())],sort_keys=True).encode()).hexdigest()
result['adapter_sha256']=hashlib.sha256((ROOT/'openproject/ai/automation/n8n_integration_adapter.py').read_bytes()).hexdigest()
# Stagger real cron first-generation, preserving production definitions outside this clone.
now=datetime.datetime.now(datetime.timezone.utc)
cron_specs=[]
for wf,delay in [('WF07',90),('WF12',150)]:
    spec=next(s for s in workflows if s['name'].startswith(wf));fire=now+datetime.timedelta(seconds=delay)
    for node in spec['nodes']:
        if node['type']=='n8n-nodes-base.scheduleTrigger':
            node.pop('disabled',None);node['parameters']={'rule':{'interval':[{'field':'cronExpression','expression':f'{fire.second} {fire.minute} * * * *'}]}}
    cron_specs.append(spec)
(fixture/'staggered-cron.json').write_text(json.dumps(cron_specs))
run('exec',n8n,'n8n','import:workflow','--input=/fixture/staggered-cron.json')
for spec in cron_specs:run('exec',n8n,'n8n','publish:workflow','--id='+spec['id'])
# Server restart reloads supported CLI-published schedules; SQLite/credentials/history remain.
run('exec',n8n,'/bin/sh','-c','test -s /tmp/n8n-server.pid && kill "$(cat /tmp/n8n-server.pid)"')
time.sleep(2);run('exec','-d',n8n,'/bin/sh','-c','echo $$ >/tmp/n8n-server.pid; exec n8n start >/tmp/n8n-staggered.log 2>&1')
query="const s=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));const d=new s.Database('/home/node/.n8n/database.sqlite',s.OPEN_READONLY);d.all(\"SELECT id,status,mode,workflowId,startedAt,stoppedAt FROM execution_entity WHERE mode='trigger' ORDER BY id\",(e,r)=>{if(e)throw e;console.log(JSON.stringify(r));d.close()})"
for _ in range(120):
    rows=json.loads(run('exec',n8n,'node','-e',query));codes={spec['id']:spec['name'][:4] for spec in workflows}
    if {'WF07','WF12'}<={codes.get(r['workflowId']) for r in rows if r['status']=='success'}:break
    time.sleep(2)
else:raise RuntimeError('STAGGERED_CRON_DID_NOT_COMPLETE')
result['actual_staggered_cron_executions']=rows
record('WF07','Actual cron first-generation plus authenticated duplicate readback, correct readers4/4',wf07)
record('WF12','Actual cron first-generation plus signed duplicate readback, correct readers4/4',wf12)

# Executed by the actual n8n/Native qualification runner, sharing its isolated fixtures.
def integration_cases():
    target6=py("n6=Native('http://web:8080',keys['20'],6);w=n6.call('/api/v3/work_packages','POST',{'subject':'INTEGRATION_EVENT_CREATE_'+str(uuid.uuid4()),c['source_field']:'INTEGRATION-EVENT-'+str(uuid.uuid4()),'description':{'raw':'Knowledge freshness controlled source; exact citation required.'},'_links':{'project':{'href':'/api/v3/projects/6'},'type':{'href':'/api/v3/types/1'}}});print(json.dumps({'id':w['id'],'version':w['lockVersion']}))")
    identifier=target6['id']
    setup="from gateway.service import Service\nfrom gateway.engineering import scoped_service\nfrom gateway import integration_events as ie\nfrom gateway.native_incremental import scan\nfrom gateway.n8n_lifecycle_outbox import sign_envelope\ns=Service(Store(root),c,'/tmp/event-workspace');sc=scoped_service(s,6)\n"
    def seed(kind,source,version,payload):
        return py(setup+f"event=ie.enqueue(s.store,{kind!r},{source!r},{version!r},payload={payload!r})\nwith s.store.connect() as d:row=d.execute('SELECT document FROM integration_event_outbox WHERE id=?',(event,)).fetchone()\nprint(json.dumps(sign_envelope(json.loads(row[0]),'a'*64)))")
    def send(event):
        r=nfetch('qldapm-integration-'+event['event']['workflow'].lower(),event,actor=None)
        assert r['status']==200,{'status':r['status'],'json':r.get('json')}
        return r['json']
    initial=py(setup+f"r=scan(sc,20,authority='machine')\nwith s.store.connect() as d:row=d.execute('SELECT version,hash FROM native_index_cursor WHERE actor=20 AND project=6 AND native_id=?',({identifier},)).fetchone()\nprint(json.dumps(dict(row)))")
    first=seed('NATIVE_CHANGED',f'op:wp:{identifier}',initial['version'],{'native_id':identifier,'source_hash':initial['hash']})
    receipt=send(first);assert receipt['business_result']['state']=='SOURCE_OBSERVED'
    assert send(first)==receipt
    updated=py(f"n6=Native('http://web:8080',keys['20'],6);w=n6.package({identifier});r=n6.call('/api/v3/work_packages/{identifier}','PATCH',{{'lockVersion':w['lockVersion'],'subject':'INTEGRATION_EVENT_UPDATED_'+str(uuid.uuid4())}});print(json.dumps({{'version':r['lockVersion']}}))")
    # A distinct persisted old source event must read the current Native version, not trust the publisher.
    stale=seed('NATIVE_CHANGED',f'op:wp:{identifier}:stale',initial['version'],{'native_id':identifier,'source_hash':initial['hash']})
    stale_receipt=send(stale);assert stale_receipt['business_result']['state']=='SUPERSEDED'
    inventory=py(setup+f"scan(sc,20,authority='machine')\nwith s.store.connect() as d:row=d.execute('SELECT version,hash FROM native_index_cursor WHERE actor=20 AND project=6 AND native_id=?',({identifier},)).fetchone()\nprint(json.dumps(dict(row)))")
    changed=seed('NATIVE_CHANGED',f'op:wp:{identifier}',inventory['version'],{'native_id':identifier,'source_hash':inventory['hash']});assert send(changed)['business_result']['state']=='SOURCE_OBSERVED'
    # Inject one transient indexing outage in the disposable process; the durable worker owns retries.
    failed=py(setup+f"from unittest.mock import patch\nwith s.store.connect() as d:d.execute(\"UPDATE knowledge_sync SET next_at=? WHERE native_id!=?\",(time.time()+3600,{identifier}))\nwith patch.object(Service,'sync_canonical_native',side_effect=RuntimeError('CLONE_TRANSIENT_VECTOR_OUTAGE')):s.process_knowledge_sync()\nwith s.store.connect() as d:row=d.execute(\"SELECT id,state,attempts FROM knowledge_sync WHERE native_id=? AND state='retry' ORDER BY rowid DESC LIMIT 1\",({identifier},)).fetchone()\nprint(json.dumps(dict(row)))")
    failure_event=seed('INDEX_FAILED','knowledge-job:'+failed['id'],failed['attempts'],{'job_id':failed['id'],'native_id':identifier,'state':'retry','attempts':failed['attempts'],'error_code':'KNOWLEDGE_SYNC_FAILED'})
    failure_receipt=send(failure_event);assert failure_receipt['business_result']['state']=='WAITING_RETRY'
    verified=py(setup+f"with s.store.connect() as d:d.execute('UPDATE knowledge_sync SET next_at=0 WHERE native_id=?',({identifier},))\nfor _ in range(10):\n s.process_knowledge_sync()\n with s.store.connect() as d:row=d.execute(\"SELECT id,state,attempts,result FROM knowledge_sync WHERE native_id=? ORDER BY rowid DESC LIMIT 1\",({identifier},)).fetchone()\n if row['state']=='verified':break\nassert row['state']=='verified',dict(row)\nprint(json.dumps(dict(row)))")
    indexed=seed('INDEX_VERIFIED','knowledge-job:'+verified['id'],verified['attempts'],{'job_id':verified['id'],'native_id':identifier,'state':'verified','attempts':verified['attempts'],'error_code':None})
    index_receipt=send(indexed);assert index_receipt['business_result']['state']=='INDEX_VERIFIED'
    # Remove clone-only vectors; WF15 repairs through the same durable queue and never writes Native.
    repair_seed=py(setup+f"from gateway.vector_client import VectorClient\nv=VectorClient();before=[r['id'] for r in v.scroll_points('6') if r['payload'].get('source_id')=='op:wp:{identifier}'];assert before,before;assert v.delete_by_source_id('op:wp:{identifier}','6');after=[r['id'] for r in v.scroll_points('6') if r['payload'].get('source_id')=='op:wp:{identifier}'];assert not after;v.close();print(json.dumps({{'removed_point_ids':before,'remaining_source_points':after}}))")
    reconcile=seed('RECONCILE_REQUESTED','project:6:knowledge:controlled-drift',int(time.time()),{})
    result['event_stage']='wf15_drift_repair'
    repair=send(reconcile);assert repair['business_result']['state']=='REPAIR_QUEUED',repair
    assert send(reconcile)==repair
    result['event_stage']='durable_repair_readback'
    recovery=py(setup+f"for _ in range(60):\n s.process_knowledge_sync()\n with s.store.connect() as d:r=d.execute(\"SELECT count(*) FROM knowledge_sync WHERE request_key LIKE ? AND state!='verified'\",('%'+{reconcile['event']['event_id']!r}+'%',)).fetchone()[0]\n if r==0:break\nassert r==0,r\nprint(json.dumps({{'unverified_repair_jobs':r}}))")
    result['event_stage']='authorized_clone_owner_delete'
    # Delete is isolated Native fixture only; fresh visibility withdraws retrieval without inventing physical-delete authority.
    py(f"n6=Native('http://web:8080',keys['18'],6);n6.call('/api/v3/work_packages/{identifier}','DELETE');print('{{}}')")
    withdrawn=py(setup+f"scan(sc,20,authority='machine')\nwith s.store.connect() as d:row=d.execute('SELECT version,hash,visible FROM native_index_cursor WHERE actor=20 AND project=6 AND native_id=?',({identifier},)).fetchone()\nassert row['visible']==0\nprint(json.dumps(dict(row)))")
    tombstone=seed('NATIVE_WITHDRAWN',f'op:wp:{identifier}',withdrawn['version'],{'native_id':identifier,'source_hash':withdrawn['hash']});tombstone_receipt=send(tombstone)
    assert tombstone_receipt['business_result']['state']=='TOMBSTONED_VISIBILITY'
    deleted_search=py(setup+f"native,who=sc.native_actor(20);r=sc.knowledge(who,native,'knowledge_search',{{'query':'INTEGRATION_EVENT_UPDATED','native_ids':[{identifier}],'limit':5}});assert not r['items'];print(json.dumps({{'items':r['items']}}))")
    pr=seed('GITHUB_PR_CHANGED','github:fixture:pr:100','b'*64,{'pr_number':100,'head_sha':'c'*40,'state':'open','merge_target':'FEATURE_BRANCH','work_package_id':identifier})
    delivery=send(pr);assert delivery['business_result']['state']=='DELIVERY_OBSERVED'
    qa=py(setup+f"run=str(uuid.uuid4());result={{'status':'succeeded','head_sha':'c'*40,'test_evidence':{{'command':'python -m unittest acceptance','exit_code':0}},'review_evidence':{{'verdict':'PASS','qa':{{'status':'PASS','exit_code':0}}}}}}\nfrom gateway.store import canonical,digest\nwith s.store.connect() as d:\n d.execute('INSERT INTO ai_queue VALUES(?,?,?,?,?,?,?,?)',(run,20,canonical({{'project_id':6,'native_id':{identifier}}}),'finished',time.time(),None,1,'agent'))\n d.execute('INSERT INTO ai_runs VALUES(?,?,?,?,?)',(run,20,'done',canonical(result),time.time()))\nprint(json.dumps({{'run':run,'hash':digest(canonical(result))}}))")
    qa_event=seed('ENGINEERING_QA_RESULT','engineering:'+qa['run'],qa['hash'],{'run_id':qa['run'],'native_id':identifier,'head_sha':'c'*40});qa_receipt=send(qa_event)
    assert qa_receipt['business_result']['state']=='QA_VERIFIED' and not qa_receipt['business_result']['native_approval']
    failed_qa=py(setup+f"from gateway.store import canonical,digest\nwith s.store.connect() as d:\n r=json.loads(d.execute('SELECT result FROM ai_runs WHERE id=?',({qa['run']!r},)).fetchone()[0]);r['review_evidence']['qa']['exit_code']=1;r['review_evidence']['qa']['status']='FAIL';d.execute('UPDATE ai_runs SET result=? WHERE id=?',(canonical(r),{qa['run']!r}))\nprint(json.dumps({{'hash':digest(canonical(r))}}))")
    blocked=seed('ENGINEERING_QA_RESULT','engineering:'+qa['run'],failed_qa['hash'],{'run_id':qa['run'],'native_id':identifier,'head_sha':'c'*40})
    denied=nfetch('qldapm-integration-wf11',blocked,actor=None);assert denied['status']>=400
    receipts=py(setup+"print(json.dumps(ie.snapshot(s.store)))")
    assert next(r for r in receipts if r['workflow']=='WF11')['business_result']['state']=='QA_BLOCKED'
    return {'native_id':identifier,'created_version':initial['version'],'updated_version':updated['version'],'event_receipts':[receipt,stale_receipt,failure_receipt,index_receipt,repair,tombstone_receipt,delivery,qa_receipt],'persistent_execution_metadata':receipts,'recovery':recovery,'actual_vector_loss':repair_seed,'deleted_source_search':deleted_search,'qa_fixture':'persisted synthetic worker-result contract, not a fresh coding/provider run'}
record('EVENTS','Actual published6machine branches + Native create/update/delete + vector failure/retry/repair and citations',integration_cases)

# Read actual scheduler-mode executions, not webhook stand-ins.
def cron_cases():
    query="const s=require(require.resolve('sqlite3',{paths:['/usr/local/lib/node_modules/n8n']}));const d=new s.Database('/home/node/.n8n/database.sqlite',s.OPEN_READONLY);d.all(\"SELECT id,status,mode,workflowId,startedAt,stoppedAt FROM execution_entity WHERE mode='trigger' ORDER BY id\",(e,r)=>{if(e)throw e;console.log(JSON.stringify(r));d.close()})"
    rows=[]
    for _ in range(5):
        rows=json.loads(run('exec',n8n,'node','-e',query));codes={spec['id']:spec['name'][:4] for spec in workflows}
        success={codes.get(r['workflowId']) for r in rows if r['status']=='success'}
        if {'WF07','WF12'}<=success:break
        time.sleep(2)
    assert {'WF07','WF12'}<=success,rows
    reports=py("s=Store(root)\nwith s.connect() as d:rows=[{'id':r['id'],'created':r['created'],'receipt':json.loads(r['receipt'])} for r in d.execute(\"SELECT * FROM automation_runs WHERE request_key LIKE 'daily:%' OR request_key LIKE 'weekly:%'\")]\nprint(json.dumps(rows))")
    assert len(reports)>=2
    return {'schedule':'clone-only staggered second/minute, separate first-generation','actual_trigger_executions':rows,'persisted_collectors':reports,'main_crons_unchanged':True}
record('CRON','Actual WF07/WF12 scheduled executions with persisted collector readback',cron_cases)

def approval_cases():
    def propose(text):
        return py(f"from gateway.service import Service\ns=Service(Store(root),c,'/tmp/workspaces');w=n.package({target});r=s.execute_actor(18,{{'action':'comment','arguments':{{'id':{target},'lock_version':w['lockVersion'],'text':{text!r}}},'idempotency_key':'clone-approval-'+str(uuid.uuid4())}});print(json.dumps(r['result']))")
    marker='CLONE_VALID_APPROVAL_'+uuid.uuid4().hex
    proposal=propose(marker)
    unauthorized=request('WF06',{'proposal_id':proposal['id'],'hash':proposal['hash'],'decision':'approve'},actor='19');assert unauthorized['status']==403
    approved=ok(request('WF06',{'proposal_id':proposal['id'],'hash':proposal['hash'],'decision':'approve'}))
    duplicate=request('WF06',{'proposal_id':proposal['id'],'hash':proposal['hash'],'decision':'approve'})
    result['approval_stage']='activity_readback'
    readback=py(f"items=n.collection('/api/v3/work_packages/{target}/activities');found=[a['id'] for a in items if a.get('comment',{{}}).get('raw','').startswith({marker!r}+chr(10)*2+'<!-- QLDAPM-request-')];assert len(found)==1,found;print(json.dumps({{'activity_ids':found,'version':n.package({target})['lockVersion']}}))")
    result['approval_stage']='stale_preview'
    stale=propose('CLONE_STALE_MUST_NOT_WRITE_'+uuid.uuid4().hex)
    py(f"w=n.package({target});n.call('/api/v3/work_packages/{target}','PATCH',{{'lockVersion':w['lockVersion'],'subject':'CLONE_STALE_VERSION_'+str(uuid.uuid4())}});print('{{}}')")
    rejected=request('WF06',{'proposal_id':stale['id'],'hash':stale['hash'],'decision':'approve'});assert rejected['status']>=400
    current=py(f"s=Store(root);print(json.dumps(s.proposal(18,{stale['id']!r})))")
    assert current['state']=='failed_or_unknown'
    return {'environment':'isolated Native clone; explicit synthetic human decision, no MAIN Owner decision','approved_proposal_id':proposal['id'],'approved_response':approved,'duplicate_http':duplicate['status'],'native_readback':readback,'unauthorized_actor19_http':403,'stale_proposal_id':stale['id'],'stale_http':rejected['status'],'stale_state':current['state'],'compensation':'comment append is exact-once; stale case aborts before Native mutation; disposable fixture removed with clone'}
record('APPROVAL','WF05/06 valid clone approval, reject, unauthorized, stale, duplicate and exact Native activity readback',approval_cases)


def local_document_cases():
    owner,local_actor,denied_actor='18','20','21'
    identity=py("from gateway.service import Service\ns=Service(Store(root),c,'/tmp/local-identity');print(json.dumps({str(a):s.native_actor(a)[1]['role'] for a in (18,20,21)}))")
    assert identity=={'18':'AI_SYSTEM_OWNER','20':'BA','21':'BE'},identity
    result['local_stage']='fixture_hash'
    source_hash=py("import hashlib;f=fixture/'local-source.md';h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==c['file_sources']['clone-local']['sha256'];print(json.dumps({'sha256':h}))")
    key='clone-local';payload={'source_key':key,'request_id':str(uuid.uuid4())}
    result['local_stage']='owner_ingest'
    ingested=ok(request('WF01',payload,actor=owner));assert ingested.get('vector_indexed') is True
    assert ok(request('WF01',payload,actor=owner))==ingested
    result['local_stage']='authorized_search'
    found=ok(request('WF01',{'source_key':key,'operation':'search','query':'lunar-calendar release guideline','limit':5},actor=local_actor))
    assert found['items'] and all(r['document_id']==ingested['document_id'] and r['source_sha256']==ingested['source_sha256'] for r in found['items'])
    read=ok(request('WF01',{'source_key':key,'operation':'read','document_id':ingested['document_id']},actor=local_actor))
    assert read['citation']=='file:'+key+'#sha256='+ingested['source_sha256'] and 'signed artifact receipt' in read['content']
    denied=request('WF01',{'source_key':key,'operation':'search','query':'lunar-calendar'},actor=denied_actor);assert denied['status']==403
    result['local_stage']='database_readback'
    readback=py("from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig\nfrom gateway.vector_client import VectorClient\nstorage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(root/'knowledge.sqlite')));docs=[d for d in storage.query_documents('5','BA') if d.source_id=='file:clone-local'];assert len(docs)==1;v=VectorClient();points=[r for r in v.scroll_points('5') if r['payload'].get('source_id')=='file:clone-local'];assert points and all(p['payload']['document_id']==docs[0].source_hash and p['payload']['allowed_roles']==['BA'] for p in points);v.close();print(json.dumps({'document_id':docs[0].source_hash,'source_sha256':docs[0].metadata['source_sha256'],'point_ids':[p['id'] for p in points],'roles':docs[0].allowed_roles}))")
    result['local_stage']='stale_pin'
    original=(fixture/'local-source.md').read_bytes();(fixture/'local-source.md').write_bytes(original+b'\nChanged after pin for stale-source test.\n')
    try:
        stale=request('WF01',{'source_key':key,'operation':'read','document_id':ingested['document_id']},actor=local_actor);assert stale['status']==409
    finally:(fixture/'local-source.md').write_bytes(original)
    return {'source_key':key,'source_sha256':ingested['source_sha256'],'document_id':ingested['document_id'],'citation':read['citation'],'actual_sqlite_vector_readback':readback,'ingest_actor':18,'authorized_actor':20,'denied_actor':21,'fresh_native_roles':identity,'unauthorized_read_http':403,'changed_file_pin_denied':409,'replay_same_result':True,'Native_writes':0,'fixture_scope':'isolated clone file registry only; no MAIN Project5 source added'}
record('LOCAL_DOCUMENT','Actual WF01 pinned local file ingest/search/read, SQLite/Qdrant identity, citation, ACL, replay and stale pin',local_document_cases)


def local_document_p6_cases():
    result['local_stage']='project6_native_identity'
    identity=py("from gateway.service import Service\nfrom gateway.engineering import scoped_service\ns=Service(Store(root),c,'/tmp/local-p6-identity');sc=scoped_service(s,6);print(json.dumps({str(a):sc.native_actor(a)[1]['role'] for a in (18,20)}))")
    assert identity=={'18':'AI_SYSTEM_OWNER','20':'PM'},identity
    key='clone-local-p6';payload={'source_key':key,'request_id':str(uuid.uuid4()),'project_id':6}
    result['local_stage']='project6_ingest'
    ingested=ok(request('WF01',payload,actor='20'));assert ingested.get('vector_indexed') is True,{'step':'ingest','vector_indexed':ingested.get('vector_indexed'),'source_id':ingested.get('source_id')}
    result['local_stage']='project6_replay'
    replay=ok(request('WF01',payload,actor='20'));assert replay==ingested,{'step':'replay','source_id':replay.get('source_id'),'document_matches':replay.get('document_id')==ingested.get('document_id')}
    result['local_stage']='project6_search_read'
    found=ok(request('WF01',{'source_key':key,'operation':'search','query':'lunar-calendar release guideline','project_id':6},actor='20'))
    assert found['items'] and all(r['document_id']==ingested['document_id'] and r['source_sha256']==ingested['source_sha256'] for r in found['items'])
    read=ok(request('WF01',{'source_key':key,'operation':'read','document_id':ingested['document_id'],'project_id':6},actor='20'))
    assert read['citation']=='file:'+key+'#sha256='+ingested['source_sha256'] and 'signed artifact receipt' in read['content']
    result['local_stage']='project6_denied_actor'
    denied=request('WF01',{'source_key':key,'operation':'search','query':'lunar-calendar','project_id':6},actor='21');assert denied['status'] in {403,404}, {'status':denied['status'],'error':denied.get('json',{}).get('error')}
    result['local_stage']='project6_cross_source'
    cross=request('WF01',{'source_key':'clone-local','operation':'search','query':'lunar-calendar','project_id':6},actor='20');assert cross['status']==403
    result['local_stage']='project6_store_readback'
    readback=py("from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig\nfrom gateway.vector_client import VectorClient\nstorage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(root/'knowledge.sqlite')));docs=[d for d in storage.query_documents('6','PM') if d.source_id=='file:clone-local-p6'];assert len(docs)==1;v=VectorClient();points=[r for r in v.scroll_points('6') if r['payload'].get('source_id')=='file:clone-local-p6'];assert points and all(p['payload']['document_id']==docs[0].source_hash and p['payload']['allowed_roles']==['PM'] for p in points);v.close();print(json.dumps({'document_id':docs[0].source_hash,'source_sha256':docs[0].metadata['source_sha256'],'point_ids':[p['id'] for p in points],'roles':docs[0].allowed_roles}))")
    result['local_stage']='project6_stale_pin'
    original=(fixture/'local-source.md').read_bytes();(fixture/'local-source.md').write_bytes(original+b'\nChanged after pin.\n')
    try:
        stale=request('WF01',{'source_key':key,'operation':'read','document_id':ingested['document_id'],'project_id':6},actor='20');assert stale['status']==409
    finally:(fixture/'local-source.md').write_bytes(original)
    return {'project':6,'source_key':key,'document_id':ingested['document_id'],'source_sha256':ingested['source_sha256'],'citation':read['citation'],'actual_sqlite_vector_readback':readback,'fresh_native_roles':identity,'actor21_denied_http':denied['status'],'cross_project_source_denied_http':403,'stale_pin_denied_http':409,'replay_same_result':True,'main_native_writes':0}

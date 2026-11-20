"""Executed only inside an isolated comment qualification Gateway; no Main credentials or writes."""
import datetime
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from gateway.native import Native
from gateway.service import Service
from gateway.store import Store
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.knowledge_ingestion import KnowledgeIngester
from gateway.openproject_loader import work_package_to_document,actor_work_package_document
from gateway.vector_client import VectorClient

root=Path('/qualification')
clone=json.loads((root/'clone.json').read_text())
assert os.environ.get('QLDAPM_COMMENT_SYNC_CLONE')==clone['id'] and clone['base_url']=='http://web:8080'
config=json.loads((root/'config.json').read_text());keys=json.loads((root/'credentials.json').read_text())
store=Store(root/'state');service=Service(store,config,root/'workspace')
tokens={a:store.issue_token(a,config['users'][str(a)],keys[str(a)]) for a in (18,19,20)}
def native(actor=18):return Native(clone['base_url'],keys[str(actor)],5)
def command(action,args,actor=18):
    return service.execute(tokens[actor],{'action':action,'arguments':args,'idempotency_key':str(uuid.uuid4())})['result']
storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(root/'state/knowledge.sqlite')))
# Establish an exact read-only Native baseline without re-embedding unrelated snapshot data.
n=native();rows=n.packages();bootstrap=KnowledgeIngester(storage,None)
indexed={d.source_id:d for d in storage.query_documents('5')}
for wp in rows:
    canonical=work_package_to_document(wp,'5');old=indexed.get(canonical.source_id);own=indexed.get(f'actor:18:wp:{wp["id"]}')
    if old and old.source_hash==canonical.source_hash and old.metadata==canonical.metadata and own and own.metadata.get('source_updated_at')==wp.get('updatedAt'):
        continue
    bootstrap.ingest(canonical)
    bootstrap.ingest(actor_work_package_document(wp,5,18,'AI_SYSTEM_OWNER',native().collection(f'/api/v3/work_packages/{wp["id"]}/activities')))
print('Native text baseline prepared',len(rows),'packages',flush=True)
scan_started=time.monotonic();baseline=command('knowledge_incremental_sync',{});scan_seconds=time.monotonic()-scan_started
assert baseline['changed']==0,baseline
print('Native baseline scan',len(rows),'packages',round(scan_seconds,2),'seconds',flush=True)
vector=VectorClient();assert vector.ensure_collection()
created=native().call('/api/v3/work_packages','POST',{'subject':'Isolated comment synchronization fixture',
    config['source_field']:'ISOLATED-COMMENT-'+str(uuid.uuid4()),
    'description':{'raw':'Isolated Native create description'},'_links':{'project':{'href':'/api/v3/projects/5'},'type':{'href':'/api/v3/types/1'}}})
identifier=created['id'];assert identifier>max(wp['id'] for wp in rows)
traces=[]
def await_sync(label,query=None):
    deadline=time.monotonic()+900
    while time.monotonic()<deadline:
        with store.connect() as db:
            jobs=[dict(r) for r in db.execute('select id,state,result from knowledge_sync where native_id=?',(identifier,))]
        fresh=native().package(identifier)
        own=next((d for d in storage.query_documents('5') if d.source_id==f'actor:18:wp:{identifier}'),None)
        expected=actor_work_package_document(fresh,5,18,'AI_SYSTEM_OWNER',native().collection(f'/api/v3/work_packages/{identifier}/activities'))
        if own and own.source_hash==expected.source_hash and own.metadata==expected.metadata and jobs and all(j['state']=='verified' for j in jobs):
            hits=command('knowledge_search',{'query':query or 'Isolated synchronization fixture','native_ids':[identifier]})
            if query:assert hits['items'],hits
            traces.append({'label':label,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'native_id':identifier,'lock_version':fresh['lockVersion'],'activity_ids':own.metadata['activity_ids'],
                'document_id':own.source_hash,'source_id':own.source_id,'jobs':[{'id':j['id'],'state':j['state']} for j in jobs],
                'citations':hits['items']})
            (root/'progress.json').write_text(json.dumps(traces,indent=2))
            print('Verified automatic sync',label,flush=True)
            return own
        time.sleep(1)
    raise AssertionError('AUTOMATIC_SYNC_TIMEOUT: '+label)

service.start_knowledge_worker()
def assert_removed_content(marker):
    documents=[d for d in storage.query_documents('5') if d.metadata.get('native_id')==identifier]
    assert documents and all(marker not in d.content for d in documents)
    points=[p for p in vector.scroll_points('5') if p['payload'].get('work_package_id')==identifier]
    assert points and all(marker not in p['payload']['chunk_text'] for p in points)
    # Semantic search may return the related current document; it must never return the removed text/revision.
    hits=command('knowledge_search',{'query':marker,'native_ids':[identifier]})['items']
    assert all(marker not in h['snippet'] and h['document_id'] in {d.source_hash for d in documents} for h in hits)
try:
    await_sync('CREATE')
    before=native().package(identifier)
    native().call(f'/api/v3/work_packages/{identifier}','PATCH',{'lockVersion':before['lockVersion'],'description':{'raw':'Updated automatic description marker'}})
    await_sync('UPDATE','Updated automatic description marker')
    before=native().package(identifier)
    activity=native().call(f'/api/v3/work_packages/{identifier}/activities','POST',{'comment':{'raw':'commentnonce alpha fresh requirement'}})
    after=native().package(identifier);assert before['lockVersion']==after['lockVersion']
    own=await_sync('COMMENT_ONLY','commentnonce alpha fresh requirement')
    # Same-project actors cannot retrieve an Owner-only snapshot, even with the same resource visibility.
    assert command('knowledge_search',{'query':'commentnonce alpha fresh requirement','native_ids':[identifier]},19)['items']==[]
    native().call(f'/api/v3/activities/{activity["id"]}','PATCH',{'comment':'replacementnonce beta revised requirement'})
    await_sync('EDIT_COMMENT','replacementnonce beta revised requirement')
    assert_removed_content('commentnonce alpha')
    native().call(f'/api/v3/activities/{activity["id"]}','PATCH',{'comment':''})
    await_sync('REMOVE_COMMENT')
    assert_removed_content('replacementnonce beta')
finally:
    service.stop_knowledge_worker()
    service._knowledge_thread.join(timeout=120)
    assert not service._knowledge_thread.is_alive()
final_scan=command('knowledge_incremental_sync',{});assert final_scan['changed']==0
points=vector.scroll_points('5');fixture_points=[p for p in points if p['payload'].get('work_package_id')==identifier]
assert fixture_points
vectors=vector._http.post(f'{vector.qdrant_url}/collections/{vector.collection_name}/points',
    json={'ids':[p['id'] for p in fixture_points],'with_vector':True}).json()['result']
assert len(vectors)==len(fixture_points) and all(len(p['vector'])==1024 for p in vectors)
with sqlite3.connect(root/'state/knowledge.sqlite') as db:
    fts=db.execute('select count(*) from knowledge_fts where source_hash in (select source_hash from knowledge_documents where json_extract(metadata,\'$.native_id\')=?)',(identifier,)).fetchone()[0]
    assert fts==2
result={'status':'CLONE_NATIVE_COMMENT_SYNC_PASS','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'clone_id':clone['id'],'scan_packages':len(rows),'baseline_scan_seconds':scan_seconds,'traces':traces,
    'final_scan_generation':final_scan['generation'],'fixture_qdrant_point_ids':[p['id'] for p in fixture_points],
    'embedding_model':'bge-m3','dimensions':1024,'fixture_fts_documents':fts,'main_business_writes':0,
    'limits':['Native Core/PG/Gateway worker/SQLite/FTS/Qdrant/Ollama exercised; Gemini and n8n not exercised in this suite',
              'Bootstrap existing Native corpus text-only; only the new fixture is auto-indexed with real embeddings',
              'Latest 20 bounded actor-authorized comments; no claim of complete journal history']}
(root/'result.json').write_text(json.dumps(result,indent=2));print(result['status'],flush=True)
vector.close()

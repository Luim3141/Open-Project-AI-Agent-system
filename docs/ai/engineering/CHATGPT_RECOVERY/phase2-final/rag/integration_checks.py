"""Actual isolated-Qdrant ACL/indexing checks, never connected to Main Qdrant."""
from benchmark_phase2 import *
from gateway.knowledge_classifier import classify_document
from gateway.knowledge_points import point

started=utc();checks={}
client=VectorClient(qdrant_url='http://127.0.0.1:16334',collection_name='phase2_contracts')
assert client.qdrant_url=='http://127.0.0.1:16334'
store=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(PRIVATE/'contracts.sqlite')))
ingester=KnowledgeIngester(store,client)
engine=KnowledgeSearchEngine(store,vector_client=client)
def doc(version,word):return classify_document(KnowledgeDocType.WORK_PACKAGE,'6','phase2-contract-freshness',
    'Synthetic freshness contract',f'Synthetic freshness {word} requirements for the isolated contract check.',
    allowed_roles=['PM'],metadata={'native_id':910001,'actor_id':20,'lock_version':version})
def query(text,project='6',role='PM',actor=20,scope=None):
    return engine.search(text,project,role,limit=5,actor_id=actor,document_ids=scope)
try:
    first=doc(1,'alpha');second=doc(2,'omega')
    assert ingester.ingest(first).vector_indexed
    assert query(first.content)[0].document_id==first.source_hash
    checks['new_index_visible']=True
    for name,kwargs in [('wrong_project',{'project':'7'}),('wrong_role',{'role':'QA'}),
            ('wrong_actor',{'actor':999}),('empty_native_document_scope',{'scope':[]})]:
        assert query(first.content,**kwargs)==[],name;checks[name]=True
    vectors=client.embed_texts([first.content])[0]
    for name,kwargs in [('qdrant_project_prefilter',{'project_id':'7','role':'PM'}),
            ('qdrant_role_prefilter',{'project_id':'6','role':'QA'}),
            ('qdrant_actor_prefilter',{'project_id':'6','role':'PM','actor_id':999}),
            ('qdrant_empty_document_scope',{'project_id':'6','role':'PM','document_ids':[]})]:
        assert client.search_dense(query_vector=vectors,**kwargs)==[],name;checks[name]=True
    assert ingester.ingest(second).vector_indexed
    points=client.scroll_points('6')
    assert points and all(p['payload']['document_id']==second.source_hash for p in points)
    assert [d.source_hash for d in store.query_documents('6','PM')]==[second.source_hash]
    checks['revision_pruned_old_sqlite_and_qdrant']=True
    registered=points[0]
    payload=dict(registered['payload']);payload['work_package_id']=999
    bad={'id':registered['id'],'payload':payload,'vector':client.embed_texts([second.content])[0]}
    assert client.upsert_points([bad])
    hits=query(second.content)
    assert hits and all(h.native_id==910001 for h in hits)
    checks['forged_citation_alias_cannot_override_verified_native_id']=True
    bad['payload']={**payload,'metadata':{**payload['metadata'],'actor_id':999}}
    assert client.upsert_points([bad])
    assert query('unrelated semantic probe',scope=[second.source_hash])==[]
    checks['forged_metadata_rejected_after_vector_filter']=True
    bad['payload']={**registered['payload'],'chunk_text':'Forged content with an unchanged chunk hash'}
    assert client.upsert_points([bad])
    assert query('unrelated semantic probe',scope=[second.source_hash])==[]
    checks['forged_chunk_rejected_after_vector_filter']=True
    bad['payload']=registered['payload'];assert client.upsert_points([bad])
    restarted=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(PRIVATE/'contracts.sqlite')))
    assert KnowledgeSearchEngine(restarted,vector_client=client).search(second.content,'6','PM',actor_id=20)[0].document_id==second.source_hash
    checks['restart_readback']=True
    assert ingester.deindex_source(second.source_id,'6')
    assert client.scroll_points('6')==[] and query(second.content)==[]
    checks['deleted_source_absent_from_both_indexes']=True
    # Repeat a frozen dev query with real embeddings/search twice to check the observed transport.
    candidate=VectorClient(qdrant_url='http://127.0.0.1:16334',collection_name='phase2_candidate')
    try:
        s=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(PRIVATE/'candidate.sqlite')))
        e=KnowledgeSearchEngine(s,vector_client=candidate);allowed=[d.source_hash for d in s.query_documents('6','PM')]
        signatures=[]
        for _ in range(3):
            hits=e.search(DEV[0][2],'6','PM',limit=5,actor_id=20,document_ids=allowed)
            signatures.append([(h.document_id,h.score,h.match_type,h.snippet) for h in hits])
        assert signatures[0]==signatures[1]==signatures[2]
        checks['three_repeated_query_rankings_identical_in_clone']=True
    finally:candidate.close()
    result={'started_utc':started,'ended_utc':utc(),'environment':'Windows host Python; isolated Qdrant 16334, synthetic contract corpus; local Ollama only',
        'command':' '.join(sys.argv),'checks':checks,'passed':len(checks),
        'source_sha256':{n:sha(Path('openproject/ai/gateway')/n) for n in ['knowledge_search.py','knowledge_ingestion.py','vector_client.py']},
        'image_digest':'sha256:9bfc89f9914fc14876a88c05270685921a55b8877b254a98bcc1cc2f0a424cd2',
        'limits':'Not Main Native authorization or end-user citation rendering; synthetic integration corpus.'}
    (OUT/'integration-results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
finally:client.close()

"""One Project6 operational replay on disposable SQLite/Qdrant, no live Native writes."""
from datetime import datetime,timezone
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

sys.path.insert(0,str(Path.cwd()/'openproject/ai'))
from gateway.knowledge_classifier import KnowledgeDocument,KnowledgeDocType
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.knowledge_points import point
from gateway.native import NativeError
from gateway.native_incremental import scan
from gateway.permissions import AI_SYSTEM_OWNER
from gateway.service import Service
from gateway.store import Store
from gateway.vector_client import VectorClient

OUT=Path(__file__).parent
PRIVATE=Path(os.environ['QLDAPM_RAG_EXPERIMENT_ROOT']) if 'QLDAPM_RAG_EXPERIMENT_ROOT' in os.environ else Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase3-native-audit'
SNAPSHOT=PRIVATE/'refresh-native-index-snapshot.json'
QDRANT=os.environ.get('QLDAPM_RAG_QDRANT_URL','http://127.0.0.1:16335')
COLLECTION='qldapm_phase3_native_refresh_corrected'
CONTAINER='qldapm-phase3-rag-refresh'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class CloneVector(VectorClient):
    def __init__(self):
        assert QDRANT in ['http://127.0.0.1:16335','http://qldapm-phase3-rag-refresh:6333']
        super().__init__(ollama_url=os.environ.get('QLDAPM_RAG_OLLAMA_URL','http://127.0.0.1:11434'),qdrant_url=QDRANT,
            collection_name=COLLECTION,batch_size=1,timeout=30)
    def _embed_texts(self,texts):
        vectors=[]
        for text in texts:
            response=self._http.post(self.ollama_url+'/api/embed',json={
                'model':'bge-m3','input':[text],'truncate':False,'options':{'num_thread':1}})
            response.raise_for_status();batch=response.json()['embeddings']
            assert len(batch)==1 and len(batch[0])==1024 and all(math.isfinite(x) for x in batch[0])
            vectors.extend(batch)
        return vectors


def main():
    started=datetime.now(timezone.utc).isoformat()
    assert sha(SNAPSHOT)=='b126f57943622ad7c5b0ed0c3dcbe641f11cf31b6d188a1b54b8e0e34395375e'
    snapshot=json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    current={d['native_id']:d for d in snapshot['documents']}
    assert len(current)==10 and snapshot['actors']['20']['role']=='PM' and snapshot['actors']['18']['role']==AI_SYSTEM_OWNER
    root=PRIVATE/'operational-clone-corrected'
    assert not root.exists(),'ONE_OPERATIONAL_QUALIFICATION_ONLY'
    root.mkdir()
    store=Store(root)
    store.issue_token(20,'PM','FIXTURE_PM_NOT_A_LIVE_CREDENTIAL')
    store.issue_token(18,AI_SYSTEM_OWNER,'FIXTURE_OWNER_NOT_A_LIVE_CREDENTIAL')
    storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(root/'knowledge.sqlite')))
    for r in snapshot['index_documents']:
        doc=KnowledgeDocument(KnowledgeDocType(r['doc_type']),r['project_id'],r['source_id'],r['title'],
            r['content'],r['source_hash'],json.loads(r['allowed_roles']),json.loads(r['metadata']))
        assert storage.store_document(doc,chunks=[c for c in snapshot['index_chunks'] if c['document_id']==doc.source_hash])
    canonical=json.loads((PRIVATE/'canonical-index-snapshot.json').read_text(encoding='utf-8'))
    assert len(canonical['documents'])==10
    for r in canonical['documents']:
        doc=KnowledgeDocument(KnowledgeDocType(r['doc_type']),r['project_id'],r['source_id'],r['title'],
            r['content'],r['source_hash'],json.loads(r['allowed_roles']),json.loads(r['metadata']))
        assert doc.project_id=='6' and doc.source_id==f'op:wp:{doc.metadata["native_id"]}' and 'actor_id' not in doc.metadata
        assert storage.store_document(doc,chunks=[c for c in canonical['chunks'] if c['document_id']==doc.source_hash])
    class FrozenNative:
        native_writes=0
        def __init__(self,url,credential,project):assert project==6
        def identity(self,actor):
            assert actor in [18,20]
            return {'user_id':actor,'project_id':6,'role':AI_SYSTEM_OWNER if actor==18 else 'PM',
                'capabilities':[AI_SYSTEM_OWNER] if actor==18 else []}
        def packages(self):return [copy.deepcopy(d['native_package']) for d in current.values()]
        def package(self,identifier):
            if identifier not in current:raise NativeError(404,'FROZEN_NATIVE_NOT_VISIBLE')
            return copy.deepcopy(current[identifier]['native_package'])
        def collection(self,path):
            for identifier,d in current.items():
                if path==f'/api/v3/work_packages/{identifier}/activities':return copy.deepcopy(d['native_activities'])
            raise AssertionError('FROZEN_NATIVE_READ_SCOPE')
        def call(self,*args,**kwargs):
            type(self).native_writes+=1
            raise AssertionError('NO_NATIVE_CALL_OR_BUSINESS_WRITE_IN_CLONE')
    service=Service(store,{'project_id':6,'users':{'18':AI_SYSTEM_OWNER,'20':'PM'},'gateway_mode':'native',
        'openproject_url':'http://127.0.0.1:8088','engineering':{'enabled':True}},root/'workspace',FrozenNative)
    native,pm=service.native_actor(20)
    _,owner=service.native_actor(18)
    checks={};latencies=[]
    vector=CloneVector()
    try:
        models=vector._http.get(vector.ollama_url+'/api/tags').json()['models']
        digest=next(m['digest'] for m in models if m['name']=='bge-m3:latest')
        assert digest=='7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab'
        assert vector.ensure_collection()
        assert vector.upsert_points(snapshot['vectors']) and vector.verify_points(snapshot['vectors'])
        baselines={}
        for identifier,query in [(384,'healthz'),(390,'GET /tasks/{task_id}/title')]:
            baselines[str(identifier)]=service._knowledge(pm,native,'knowledge_search',{'query':query,'native_ids':[identifier]},vector)['items']
        checks['stale_exact_lookups_empty']=all(not rows for rows in baselines.values())
        with patch('gateway.vector_client.VectorClient',CloneVector):
            report=scan(service,20,authority='machine')
            expected=set(current)-{379}
            checks['exactly9_project6_refreshes']=report['changed']==9 and {j['native_id'] for j in report['jobs']}==expected
            with store.connect() as db:
                jobs=[dict(r) for r in db.execute('SELECT * FROM knowledge_sync')]
            checks['only_project6_actor20_jobs']=len(jobs)==9 and all(r['actor']==20 and r['request_key'].startswith('native-event-6-') for r in jobs)
            drained=0
            for _ in range(12):
                if not service.process_knowledge_sync():break
                drained+=1
            with store.connect() as db:
                states=[r[0] for r in db.execute('SELECT state FROM knowledge_sync')]
                proposal_count=db.execute('SELECT count(*) FROM proposals').fetchone()[0]
                p5_cursors=db.execute('SELECT count(*) FROM native_index_cursor WHERE project=5').fetchone()[0]
            checks['all9_verified_within_bound']=drained==9 and states==['verified']*9
            checks['no_project5_or_native_proposals']=p5_cursors==0 and proposal_count==0
            checks['settled_scan_no_new_jobs']=scan(service,20,authority='machine')['changed']==0
        storage._reload()
        own={d.metadata['native_id']:d for d in storage.query_documents('6','PM') if d.metadata.get('actor_id')==20}
        checks['all10_frozen_current_source_hashes_and_metadata']=len(own)==10 and all(
            own[i].source_hash==d['source_hash'] and own[i].metadata==d['metadata'] for i,d in current.items())
        points=[]
        with storage._connection() as db:
            for doc in own.values():
                for chunk in db.execute('SELECT * FROM knowledge_chunks WHERE document_id=? ORDER BY chunk_index',(doc.source_hash,)):
                    points.append(point(doc,dict(chunk),vector))
        checks['current_actor_chunk_payloads_readback']=vector.verify_points(points)
        exact=[]
        for identity in [pm,owner]:
            for identifier,query in [(384,'healthz'),(390,'GET /tasks/{task_id}/title')]:
                for _ in range(3):
                    tick=time.monotonic()
                    result=service._knowledge(identity,native,'knowledge_search',{'query':query,'native_ids':[identifier]},vector)
                    latencies.append(time.monotonic()-tick)
                    hits=result['items']
                    exact.append(bool(hits) and all(h['native_id']==identifier and h['source_id']==f'actor:20:wp:{identifier}'
                        and h['lock_version']==current[identifier]['native_lock_version'] and h['citation']==f'/work_packages/{identifier}'
                        and h['document_id']==current[identifier]['source_hash'] for h in hits))
        checks['pm_owner_exact_citations_current']=all(exact)
        probe=snapshot['vectors'][0]['vector'];allowed=[d.source_hash for d in own.values()]
        acl={}
        for name,kwargs in [('wrong_project',dict(project_id='7',role='PM',actor_id=20,document_ids=allowed)),
            ('wrong_role',dict(project_id='6',role='QA',actor_id=20,document_ids=allowed)),
            ('wrong_actor',dict(project_id='6',role='PM',actor_id=999)),
            ('empty_document_scope',dict(project_id='6',role='PM',actor_id=20,document_ids=[]))]:
            acl[name]=not vector.search_dense(query_vector=probe,limit=10,**kwargs)
        checks['actual_qdrant_acl_prefilters']=all(acl.values())
        checks['native_business_writes_zero']=FrozenNative.native_writes==0
        p95=sorted(latencies)[math.ceil(.95*len(latencies))-1]
        checks['warm_exact_p95_at_most5sec']=p95<=5
        result={'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
            'status':'PENDING_HOST_RUNTIME_GATES' if all(checks.values()) else 'OPERATIONAL_REFRESH_CLONE_FAILED',
            'checks':checks,'scan_native_ids':[j['native_id'] for j in report['jobs']],'drained_jobs':drained,
            'baseline_exact_hit_counts':{k:len(v) for k,v in baselines.items()},'acl_checks':acl,
            'current_actor_sources':len(own),'verified_actor_chunks':len(points),'warm_exact_query_p95_seconds':p95,
            'model_digest':digest,'snapshot_sha256':sha(SNAPSHOT),'predeclared_gate_sha256':sha(OUT/'REFRESH_GATE.md'),
            'canonical_snapshot_sha256':sha(PRIVATE/'canonical-index-snapshot.json'),
            'ollama_resident_models':vector._http.get(vector.ollama_url+'/api/ps').json(),
            'source_hashes':{p:sha(Path('openproject/ai/gateway')/p) for p in ['service.py','native_incremental.py','knowledge_search.py','knowledge_ingestion.py','vector_client.py']},
            'command':'openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase3-owner/rag/qualify_refresh.py',
            'limits':'Frozen Native fixture after independently authenticated current read. Real local BGE and disposable Qdrant. No Main Native/index/config mutation. Not semantic accuracy/human benchmark or browser Owner UAT. Qdrant cap excludes existing Ollama model/GPU memory; sequential warm timing not concurrent SLA.'}
        (OUT/'operational-clone-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
        assert all(checks.values()),'PREDECLARED_OPERATIONAL_GATE_FAILED'
    finally:
        vector.close()


if __name__=='__main__':main()

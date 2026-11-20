"""Local embeddings and exact scoped snapshot retrieval; never writes Main indexes."""
from datetime import datetime,timezone
import argparse,hashlib,json,math,os,sys,time
from pathlib import Path
import httpx
sys.path.insert(0,str(Path.cwd()/'openproject/ai'))
from gateway.knowledge_classifier import KnowledgeDocument,KnowledgeDocType
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.knowledge_search import KnowledgeSearchEngine,_tokenize
from gateway.vector_client import VectorClient
ROOT=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
parser=argparse.ArgumentParser();parser.add_argument('split',choices=['dev','holdout']);args=parser.parse_args()
labels=json.loads((ROOT/'labels-frozen.json').read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/'source-snapshot.json').read_bytes()).hexdigest()==labels['snapshot_sha256']
source=json.loads((ROOT/'source-snapshot.json').read_text(encoding='utf-8'))
scope=json.loads((ROOT/'native-scope.json').read_text())
assert scope['project_id']==6 and scope['actor_id']==20 and scope['role']=='PM' and scope['verified_read_only'] is True
docs=[]
for r in source['documents']:
    m=json.loads(r['metadata']);native=scope['native_versions'].get(str(m['native_id']))
    if native!=m['lock_version']:continue
    docs.append(KnowledgeDocument(KnowledgeDocType(r['doc_type']),r['project_id'],r['source_id'],r['title'],r['content'],r['source_hash'],json.loads(r['allowed_roles']),m))
allowed={d.source_hash:d for d in docs}
assert allowed
if not (ROOT/'source-vectors-frozen.json').exists():
    points=[];offset=None
    with httpx.Client(timeout=20) as c:
        while True:
            body={'filter':{'must':[{'key':'project_id','match':{'value':'6'}},{'key':'allowed_roles','match':{'value':'PM'}},
                {'key':'actor_id','match':{'value':20}},{'key':'document_id','match':{'any':list(allowed)}}]},'limit':256,'with_vector':True,'with_payload':True}
            if offset is not None:body['offset']=offset
            res=c.post('http://127.0.0.1:6333/collections/qldapm_knowledge_dense/points/scroll',json=body);res.raise_for_status();r=res.json()['result'];points.extend(r['points']);offset=r['next_page_offset']
            if offset is None:break
    (ROOT/'source-vectors-frozen.json').write_text(json.dumps(points))
points=json.loads((ROOT/'source-vectors-frozen.json').read_text())
chunks={(c['document_id'],c['chunk_index']):c for c in source['chunks']}
verified=[]
for p in points:
    payload=p['payload'];doc=allowed.get(payload.get('document_id'));chunk=chunks.get((payload.get('document_id'),payload.get('chunk_index')))
    assert doc and chunk
    assert payload['chunk_text']==chunk['chunk_text'] and payload['chunk_hash']==chunk['chunk_hash']
    assert payload['metadata']==doc.metadata and payload['source_id']==doc.source_id and payload['allowed_roles']==doc.allowed_roles
    assert payload['project_id']=='6' and payload['actor_id']==20
    verified.append(p)
missing_current_vectors=set(allowed)-{p['payload']['document_id'] for p in verified}
# A disappeared revision is not reconstructed into the authorized corpus from stale SQLite text.
allowed={k:v for k,v in allowed.items() if k not in missing_current_vectors}
docs=list(allowed.values())
assert allowed
storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(ROOT/'benchmark.sqlite')))
for doc in docs:assert storage.store_document(doc,chunks=[c for c in source['chunks'] if c['document_id']==doc.source_hash])
def cosine(a,b):return sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
class Scoped:
    enabled=True
    def embed_texts(self,texts):return [self.q]
    def search_dense(self,**kw):
        rows=[]
        for p in verified:
            v=p['payload']
            if v['project_id']!=kw['project_id'] or kw['role'] not in v['allowed_roles']:continue
            if kw.get('document_ids') is not None and v['document_id'] not in kw['document_ids']:continue
            if kw.get('actor_id') is not None and v['actor_id']!=kw['actor_id']:continue
            rows.append({'payload':v,'score':cosine(kw['query_vector'],p['vector'])})
        return sorted(rows,key=lambda h:(-h['score'],h['payload']['document_id'],h['payload']['chunk_index']))[:kw['limit']]
fixture=Scoped();engine=KnowledgeSearchEngine(storage,vector_client=fixture);client=VectorClient(timeout=60)
probe=verified[0]['vector'];acl_checks={}
for name,kw in [('wrong_project',{'project_id':'7','role':'PM','actor_id':20,'document_ids':list(allowed)}),
        ('wrong_role',{'project_id':'6','role':'QA','actor_id':20,'document_ids':list(allowed)}),
        ('wrong_actor',{'project_id':'6','role':'PM','actor_id':999,'document_ids':list(allowed)}),
        ('empty_document_scope',{'project_id':'6','role':'PM','actor_id':20,'document_ids':[]}),
        ('stale_snapshot_source_scope',{'project_id':'6','role':'PM','actor_id':20,'document_ids':[r['source_hash'] for r in source['documents'] if json.loads(r['metadata'])['native_id']==390]})]:
    assert fixture.search_dense(query_vector=probe,limit=60,**kw)==[],name
    acl_checks[name]=True
all_cases=[c for c in labels['cases'] if c['split']==args.split]
allowed_native={d.metadata['native_id'] for d in docs}
stale_cases=[c for c in all_cases if c['kind']=='positive' and not set(c['relevant_ids']) & allowed_native]
cases=[c for c in all_cases if c not in stale_cases];out=[];pairs=[]
try:
    for i,case in enumerate(cases):
        t=time.perf_counter()
        response=client._http.post(client.ollama_url+'/api/embed',json={'model':'bge-m3','input':[case['query']],
            'truncate':False,'options':{'num_thread':1}},timeout=60)
        response.raise_for_status();fixture.q=response.json()['embeddings'][0]
        assert len(fixture.q)==1024 and all(math.isfinite(x) for x in fixture.q)
        embed=time.perf_counter()-t
        t=time.perf_counter();hits=engine.search(case['query'],'6','PM',limit=5,actor_id=20,document_ids=list(allowed));base_seconds=time.perf_counter()-t
        t=time.perf_counter();dense=fixture.search_dense(query_vector=fixture.q,project_id='6',role='PM',actor_id=20,document_ids=list(allowed),limit=40)
        lex=engine._lexical_search(_tokenize(case['query'])[:30],'6','PM',10,actor_id=20,document_ids=list(allowed))
        pool=[];seen=set()
        for p in dense+[{'payload':p['payload'],'score':None} for h in lex for p in verified if p['payload']['document_id']==h.document_id]:
            payload=p['payload'];key=(payload['document_id'],payload['chunk_index'])
            if key in seen:continue
            seen.add(key);pair_id=f'{args.split}:{i}:{len(pool)}'
            pool.append({'pair_id':pair_id,'native_id':allowed[key[0]].metadata['native_id'],'document_id':key[0],
                'chunk_index':key[1],'chunk_hash':payload['chunk_hash'],'dense_score':p['score']})
            if len(pool)>=60:break
        # Two dense-ranked representatives retain document coverage without reranking every audit chunk.
        counts={};representatives=[]
        for item in pool:
            key=item['document_id']
            if counts.get(key,0)>=2:continue
            counts[key]=counts.get(key,0)+1;representatives.append(item)
            chunk=chunks[(key,item['chunk_index'])]
            pairs.append({'id':item['pair_id'],'query':case['query'],'passage':allowed[key].title+'\n'+chunk['chunk_text']})
        raw_pool_size=len(pool);pool=representatives
        out.append({'case':case,'baseline':[{'native_id':h.native_id,'document_id':h.document_id,'snippet':h.snippet} for h in hits],
            'embedding_seconds':embed,'baseline_retrieval_seconds':base_seconds,'candidate_retrieval_seconds':time.perf_counter()-t,'raw_pool_size':raw_pool_size,'pool':pool})
        print(args.split,i+1,len(cases),flush=True)
finally:client.close()
record={'utc':datetime.now(timezone.utc).isoformat(),'split':args.split,'native_scope':scope,'allowed_documents':list(allowed),
    'labels_sha256':hashlib.sha256((ROOT/'labels-frozen.json').read_bytes()).hexdigest(),
    'source_vectors_sha256':hashlib.sha256((ROOT/'source-vectors-frozen.json').read_bytes()).hexdigest(),
    'retrieval':'exact cosine copied authorized vectors; deterministic tie order; production KnowledgeSearchEngine baseline; actual Qdrant filters checked separately',
    'missing_current_vector_revisions_excluded':sorted(missing_current_vectors),
    'prefilter_acl_checks':acl_checks,
    'stale_snapshot_cases_excluded_before_any_scoring':stale_cases,'cases':out}
(ROOT/f'{args.split}-candidates.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/f'{args.split}-pairs.json').write_text(json.dumps({'pairs':pairs},ensure_ascii=False),encoding='utf-8')
print('prepared',len(pairs),'pairs;',len(allowed),'authorized docs')

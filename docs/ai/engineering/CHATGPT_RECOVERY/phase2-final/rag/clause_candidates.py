"""Prepare baseline and bounded literal-clause pairs from an immutable local file corpus."""
import argparse,hashlib,json,math,os,sys,time
from pathlib import Path
from datetime import datetime,timezone
from clause_experiment import authorized_sources,clauses,content_terms,constraints_supported,normalize_question
sys.path.insert(0,str(Path.cwd()/'openproject/ai'))
from gateway.knowledge_classifier import KnowledgeDocument,KnowledgeDocType,_compute_hash
from gateway.knowledge_ingestion import chunk_text
from gateway.knowledge_points import point
from gateway.knowledge_search import KnowledgeSearchEngine,_tokenize
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.vector_client import VectorClient

P=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-evidence-clauses'
parser=argparse.ArgumentParser();parser.add_argument('split',choices=['dev','holdout']);args=parser.parse_args()
manifest=json.loads((P/'source-manifest.json').read_text());labels=json.loads((P/'labels-frozen.json').read_text(encoding='utf-8'))
assert hashlib.sha256((P/'source-manifest.json').read_bytes()).hexdigest()==labels['source_manifest_sha256']
revision_map={s['source_key']:s['source_revision'] for s in manifest['sources']}
allowed=authorized_sources(manifest,'6','PM',20,revision_map);assert len(allowed)==12
checks={}
for name,scope in [('wrong_project',('7','PM',20,revision_map)),('wrong_role',('6','QA',20,revision_map)),
        ('wrong_actor',('6','PM',999,revision_map)),('empty_scope',('6','PM',20,{})),
        ('stale_revisions',('6','PM',20,{k:'stale' for k in revision_map}))]:
    assert authorized_sources(manifest,*scope)==[],name;checks[name]=True
client=VectorClient(timeout=60)
def sha(value):return hashlib.sha256(value.encode()).hexdigest()
def cosine(a,b):return sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
def embed(texts):
    vectors=[]
    for start in range(0,len(texts),2):
        response=client._http.post(client.ollama_url+'/api/embed',json={'model':'bge-m3','input':texts[start:start+2],
            'truncate':False,'options':{'num_thread':1}},timeout=60);response.raise_for_status();v=response.json()['embeddings']
        assert len(v)==len(texts[start:start+2]) and all(len(x)==1024 and all(math.isfinite(t) for t in x) for x in v)
        vectors.extend(v)
    return vectors
storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(P/'baseline.sqlite')))
docs={};units=[];original=[]
for s in allowed:
    raw=Path(s['copy']).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['raw_sha256'];text=raw.decode('utf-8-sig')
    title=next((l.lstrip('# ').strip() for l in text.splitlines() if l.strip()),s['source_key'])
    h=_compute_hash(text,'ADR','file:'+s['source_key'],'6')
    doc=KnowledgeDocument(KnowledgeDocType.ADR,'6','file:'+s['source_key'],title,text,h,['PM'],
        {'actor_id':20,'source_key':s['source_key'],'file_sha256':s['raw_sha256'],'source_revision':s['source_revision'],'classification':s['classification'],'origin':'REPO_FILE_NOT_NATIVE'})
    docs[h]=doc;old=chunk_text(text);assert storage.store_document(doc,chunks=old)
    original.extend({**point(doc,c,client),'key':s['source_key']} for c in old)
    for c in clauses(text,Path(s['copy']).suffix.lstrip('.')):
        assert text[c['start']:c['end']]==c['text'] and sha(c['text'])==c['sha256']
        units.append({**c,'source_key':s['source_key'],'document_id':h,'source_revision':s['source_revision'],'raw_file_sha256':s['raw_sha256']})
vectors_path=P/'corpus-vectors.json'
if vectors_path.exists():vectors=json.loads(vectors_path.read_text())
else:
    alltexts=[p['payload']['chunk_text'] for p in original]+[u['text'] for u in units]
    vectors=embed(alltexts);vectors_path.write_text(json.dumps(vectors));print('embedded corpus',len(alltexts),flush=True)
assert len(vectors)==len(original)+len(units)
for p,v in zip(original,vectors):p['vector']=v
for u,v in zip(units,vectors[len(original):]):u['vector']=v
class Fixture:
    enabled=True
    def embed_texts(self,texts):return [self.q]
    def search_dense(self,**kw):
        hits=[]
        for p in original:
            v=p['payload']
            if v['project_id']!=kw['project_id'] or kw['role'] not in v['allowed_roles']:continue
            if kw.get('document_ids') is not None and v['document_id'] not in kw['document_ids']:continue
            if kw.get('actor_id') is not None and v['actor_id']!=kw['actor_id']:continue
            hits.append({'payload':v,'score':cosine(self.q,p['vector'])})
        return sorted(hits,key=lambda h:(-h['score'],h['payload']['document_id'],h['payload']['chunk_index']))[:kw['limit']]
fixture=Fixture();engine=KnowledgeSearchEngine(storage,vector_client=fixture)
freq={t:sum(t in content_terms(d.content) for d in docs.values()) for t in set().union(*(content_terms(d.content) for d in docs.values()))}
def coverage(query,evidence):
    q=content_terms(query);e=content_terms(evidence)
    weight=lambda t:1+math.log((len(docs)+1)/(freq.get(t,0)+1))
    return sum(weight(t) for t in q&e)/sum(weight(t) for t in q) if q else 0
records=[];pairs=[];cases=[c for c in labels['cases'] if c['split']==args.split]
try:
    for i,case in enumerate(cases):
        begin=time.perf_counter();fixture.q=embed([case['query']])[0];embed_seconds=time.perf_counter()-begin
        begin=time.perf_counter();baseline=engine.search(case['query'],'6','PM',limit=5,actor_id=20,document_ids=list(docs));base_seconds=time.perf_counter()-begin
        begin=time.perf_counter();ranked=fixture.search_dense(query_vector=fixture.q,project_id='6',role='PM',actor_id=20,document_ids=list(docs),limit=len(original))
        dense_docs=[]
        for h in ranked:
            key=h['payload']['document_id']
            if key not in dense_docs:dense_docs.append(key)
        lexical=engine._lexical_search(_tokenize(case['query'])[:30],'6','PM',12,actor_id=20,document_ids=list(docs))
        fusion={h:1/(60+r) for r,h in enumerate(dense_docs,1)}
        for r,h in enumerate(lexical,1):fusion[h.document_id]=fusion.get(h.document_id,0)+1/(60+r)
        topdocs=sorted(fusion,key=lambda h:(-fusion[h],h))[:6]
        candidates=[]
        for doc in topdocs:
            ranked_clauses=sorted([u for u in units if u['document_id']==doc],key=lambda u:(-cosine(fixture.q,u['vector']),u['start']))[:2]
            candidates.extend(ranked_clauses)
        pool=[]
        for u in candidates:
            pairid=f'{args.split}:{i}:{len(pool)}'
            p={k:v for k,v in u.items() if k not in ('vector','text')}
            pool.append({**p,'pair_id':pairid,'content_coverage':coverage(case['query'],u['text']),
                'constraints_supported':constraints_supported(case['query'],u['text'])})
            pairs.append({'id':pairid,'query':normalize_question(case['query']),'original_query':case['query'],'passage':u['text']})
        records.append({'case':case,'embedding_seconds':embed_seconds,'baseline_retrieval_seconds':base_seconds,
            'candidate_retrieval_seconds':time.perf_counter()-begin,'pool':pool,
            'baseline':[{'source_key':h.metadata['source_key'],'document_id':h.document_id,'snippet':h.snippet} for h in baseline]})
        print(args.split,i+1,len(cases),flush=True)
    (P/f'{args.split}-candidates.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'labels_sha256':hashlib.sha256((P/'labels-frozen.json').read_bytes()).hexdigest(),'source_manifest_sha256':labels['source_manifest_sha256'],'scope_checks':checks,'cases':records},ensure_ascii=False,indent=2),encoding='utf-8')
    (P/f'{args.split}-pairs.json').write_text(json.dumps({'pairs':pairs},ensure_ascii=False),encoding='utf-8')
    print('PAIRS',len(pairs),'literal clauses',len(units),'original windows',len(original))
finally:client.close()

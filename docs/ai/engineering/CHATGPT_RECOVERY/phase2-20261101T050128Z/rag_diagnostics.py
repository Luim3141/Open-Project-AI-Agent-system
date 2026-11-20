"""Read copied vectors and local embeddings; export scores/rejection reasons, never content."""
from pathlib import Path
import json, math, sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.vector_client import VectorClient
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
RUN=Path(__file__).parent
private=Path(json.loads((RUN/'rag-corpus-result.json').read_text())['private_copy'])
points=json.loads((private/'source-vectors.json').read_text())
storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(private/'knowledge.sqlite')))
docs={d.source_hash:d for d in storage.query_documents('6','PM') if d.metadata.get('actor_id')==20}
client=VectorClient()
results=[]
try:
    for query in ['kiểm tra sức khỏe máy chủ','service health check endpoint','email','database backup retention policy']:
        v=client.embed_texts([query])[0]
        scored=[]
        for p in points:
            w=p['vector']; payload=p['payload']; d=docs.get(payload.get('document_id'))
            score=sum(a*b for a,b in zip(v,w))/math.sqrt(sum(a*a for a in v)*sum(b*b for b in w))
            if d:
                score_record={'native_id':d.metadata.get('native_id'),'cosine':round(score,6),
                    'metadata_matches':all(payload.get(k)==x for k,x in {'source_id':d.source_id,'project_id':d.project_id,'doc_type':d.doc_type.value,'title':d.title,'allowed_roles':d.allowed_roles,'metadata':d.metadata}.items())}
                scored.append(score_record)
        scored.sort(key=lambda x:x['cosine'],reverse=True)
        results.append({'query':query,'top5':scored[:5],'wp384_max':max((x['cosine'] for x in scored if x['native_id']==384),default=None)})
finally:client.close()
(RUN/'rag-score-diagnostics.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))

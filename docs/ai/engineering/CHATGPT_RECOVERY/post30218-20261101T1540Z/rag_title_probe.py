"""Private corpus title/query calibration; export scores and IDs only."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.vector_client import VectorClient
RUN=Path(__file__).parent
previous=json.loads((RUN.parent/'phase2-20261101T050128Z/rag-corpus-result.json').read_text())
store=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(Path(previous['private_copy'])/'knowledge.sqlite')))
docs=[d for d in store.query_documents('6','PM') if d.metadata.get('actor_id')==20]
queries=[('kiểm tra sức khỏe máy chủ',384),('tìm kiếm không phân biệt hoa thường unicode',383),
         ('thống kê số lượng công việc theo trạng thái',386),('service health check endpoint',384),
         ('case insensitive unicode search',383),('count tasks by status',386),
         ('upload user avatar',None),('database backup retention policy',None),('send transactional email',None)]
client=VectorClient(timeout=45)
try:
    titles=client.embed_texts([d.title for d in docs])
    vectors=client.embed_texts([q for q,_ in queries])
finally:client.close()
def cosine(a,b):return sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
rows=[]
for (query,expected),vec in zip(queries,vectors):
    hits=sorted([{'native_id':d.metadata.get('native_id'),'score':round(cosine(vec,t),6)} for d,t in zip(docs,titles)],key=lambda h:h['score'],reverse=True)
    rank=next((i for i,v in enumerate(hits,1) if v['native_id']==expected),None) if expected else None
    rows.append({'query':query,'expected_native_id':expected,'expected_rank':rank,'top3':hits[:3]})
(RUN/'rag-title-probe.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(rows,ensure_ascii=False))

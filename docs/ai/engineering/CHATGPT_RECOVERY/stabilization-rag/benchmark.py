import sys,json,math,tempfile,shutil
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'openproject/ai'))
from gateway.vector_client import VectorClient
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
import gateway.knowledge_search as ks
p=Path(sys.argv[1])
points=json.loads((p/'source-vectors.json').read_text())
queries=[('kiểm tra sức khỏe máy chủ',384),('tìm kiếm không phân biệt hoa thường unicode',383),('thống kê số lượng công việc theo trạng thái',386),('service health check endpoint',384),('case insensitive unicode search',383),('count tasks by status',386),('upload user avatar',None),('database backup retention policy',None),('send transactional email',None),('tải ảnh đại diện người dùng',None),('chính sách sao lưu cơ sở dữ liệu',None),('gửi email giao dịch',None)]
client=VectorClient(timeout=45)
try: vecs=client.embed_texts([q for q,_ in queries])
finally: client.close()
class Fixture:
 enabled=True
 def __init__(self,v): self.v=v
 def embed_texts(self,texts): return [self.v]
 def search_dense(self,**kw):
  scores=[]
  for point in points:
   w=point['vector']; score=sum(a*b for a,b in zip(self.v,w))/math.sqrt(sum(a*a for a in self.v)*sum(b*b for b in w))
   payload=point['payload']
   if payload.get('project_id') != kw['project_id']: continue
   scores.append({'payload':payload,'score':score})
  return sorted(scores,key=lambda x:x['score'],reverse=True)[:kw['limit']]
with tempfile.TemporaryDirectory() as tmp:
 db=Path(tmp)/'bench.sqlite';shutil.copyfile(p/'knowledge.sqlite',db)
 storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(db)))
 docs=storage.query_documents('6','PM'); allowed=[d.source_hash for d in docs if d.metadata.get('actor_id')==20]
 result=[]
 for (q,expected),v in zip(queries,vecs):
  record={'query':q,'expected':expected}
  for threshold in (.65,.57,.52):
   ks.DENSE_MIN_COSINE=threshold
   engine=ks.KnowledgeSearchEngine(storage,vector_client=Fixture(v))
   hits=engine.search(q,'6','PM',limit=10,actor_id=20,document_ids=allowed)
   ids=[h.native_id for h in hits]
   record[str(threshold)]={'ids':ids,'rank':ids.index(expected)+1 if expected in ids else None,'types':[h.match_type for h in hits]}
  result.append(record)
 ks.DENSE_MIN_COSINE=.52
 e=ks.KnowledgeSearchEngine(storage,vector_client=Fixture(vecs[0]))
 acl={'wrong_role_count':len(e.search(queries[0][0],'6','QA',document_ids=allowed)), 'empty_scope_count':len(e.search(queries[0][0],'6','PM',document_ids=[])), 'wrong_actor_count':len(e.search(queries[0][0],'6','PM',actor_id=999))}
 print(json.dumps({'cases':result,'acl':acl,'points':len(points),'authorized_documents':len(allowed)},ensure_ascii=False,indent=2))


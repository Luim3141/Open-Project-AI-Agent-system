"""Fresh dev-only baseline: read-only Main snapshot, isolated Qdrant, no holdout access."""
import datetime,hashlib,json,math,os,sqlite3,subprocess,sys,time
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.vector_client import VectorClient

OUT=Path(__file__).parent;EVAL=OUT/'eval';PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev'
PRIVATE.mkdir(parents=True,exist_ok=True)
plan=json.loads((EVAL/'evaluation-plan.json').read_text(encoding='utf-8'))
devfile=EVAL/'dev.json';assert hashlib.sha256(devfile.read_bytes()).hexdigest()==plan['dev_sha256']
manifest=json.loads((EVAL/'native-source-manifest.json').read_text(encoding='utf-8'))
cases=json.loads(devfile.read_text(encoding='utf-8'))['cases']
code="import sqlite3,sys;s=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);d=sqlite3.connect(':memory:');s.backup(d);sys.stdout.buffer.write(d.serialize())"
snapshot=PRIVATE/'knowledge.sqlite'
if not snapshot.exists():snapshot.write_bytes(subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=45))
db=sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True)
live=dict(db.execute("SELECT source_id,source_hash FROM knowledge_documents WHERE project_id='6' AND source_id LIKE 'actor:20:wp:%'"))
expected={doc['source_id']:doc['source_hash'] for doc in manifest['documents']}
assert live==expected,'SOURCE_DRIFT_SNAPSHOT_REQUIRES_NEW_EVAL'
pointsfile=PRIVATE/'points.json'
if not pointsfile.exists():
 points=[];offset=None
 with httpx.Client(timeout=20) as client:
  while True:
   body={'limit':100,'with_payload':True,'with_vector':True,'filter':{'must':[{'key':'project_id','match':{'value':'6'}},{'key':'document_id','match':{'any':sorted(expected.values())}}]}}
   if offset is not None:body['offset']=offset
   response=client.post('http://127.0.0.1:6333/collections/qldapm_knowledge_dense/points/scroll',json=body);response.raise_for_status();result=response.json()['result']
   points.extend(result['points']);offset=result.get('next_page_offset')
   if offset is None:break
 pointsfile.write_text(json.dumps(points,separators=(',',':')),encoding='utf-8')
name='qldapm-integration-rag-dev';port=16341
assert subprocess.run(['docker','inspect',name],capture_output=True).returncode!=0,'CLONE_ALREADY_EXISTS_DO_NOT_OVERWRITE'
subprocess.run(['docker','run','-d','--name',name,'--label','org.qldapm.integration-rag-dev=true','--memory','512m','--cpus','1','-p',f'127.0.0.1:{port}:6333','qdrant/qdrant:latest'],capture_output=True,check=True)
try:
 for _ in range(30):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/healthz',timeout=1).status_code==200:break
  except httpx.HTTPError:pass
  time.sleep(1)
 vc=VectorClient(qdrant_url=f'http://127.0.0.1:{port}',collection_name='frozen_dev',timeout=30)
 points=json.loads(pointsfile.read_text(encoding='utf-8'));assert vc.ensure_collection() and vc.upsert_points(points) and vc.verify_points(points)
 storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(snapshot)));ids=list(expected.values())
 class Cached:
  enabled=True
  def embed_texts(self,texts):return [self.vector]
  def search_dense(self,**kwargs):return vc.search_dense(**kwargs)
 cached=Cached();engine=KnowledgeSearchEngine(storage,vector_client=cached);rows=[]
 with httpx.Client(timeout=120) as client:
  for case in cases:
   start=time.monotonic();r=client.post('http://127.0.0.1:11434/api/embed',json={'model':'bge-m3','input':[case['query']],'truncate':False,'options':{'num_thread':1}});r.raise_for_status();cached.vector=r.json()['embeddings'][0]
   hits=engine.search(case['query'],'6','PM',limit=5,actor_id=20,document_ids=ids)
   returned=[hit.native_id for hit in hits];rank=next((i+1 for i,n in enumerate(returned) if n in case['relevant_ids']),None)
   docs={d['source_hash']:d for d in manifest['documents']}
   errors=sum(h.document_id not in docs or h.native_id!=docs[h.document_id]['metadata']['native_id'] or h.lock_version!=docs[h.document_id]['metadata']['lock_version'] for h in hits)
   rows.append({'case':case['id'],'kind':case['kind'],'language':case['language'],'rank':rank,'ids':returned,'citation_errors':errors,'seconds':round(time.monotonic()-start,3)})
   print('dev',len(rows),'/',len(cases),flush=True)
 pos=[r for r in rows if r['kind']=='positive'];neg=[r for r in rows if r['kind']=='negative'];times=sorted(r['seconds'] for r in rows)
 metrics={'positives':len(pos),'negatives':len(neg),'hit_at_5':sum(r['rank'] is not None for r in pos)/len(pos),'false_positive_rate':sum(bool(r['ids']) for r in neg)/len(neg),'citation_errors':sum(r['citation_errors'] for r in rows),'p95_seconds':times[math.ceil(.95*len(times))-1]}
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dev_sha256':plan['dev_sha256'],'scope':'real local BGE-M3 and isolated Qdrant/SQLite; Project6 actor20; author-reviewed labels','metrics':metrics,'rows':rows}
 (OUT/'baseline-dev.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(metrics))
finally:
 subprocess.run(['docker','stop',name],capture_output=True,timeout=30)

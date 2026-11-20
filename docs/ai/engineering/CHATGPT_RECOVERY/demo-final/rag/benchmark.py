"""Frozen split evaluation on actual BGE-M3 + isolated Qdrant, never MAIN index writes."""
import datetime,hashlib,json,math,os,subprocess,sys,time,importlib.util
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'openproject/ai'))
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.vector_client import VectorClient
OUT=Path(__file__).parent;PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/demo-final-rag'
archive=OUT/'rejected-candidate'
CandidateEngine=KnowledgeSearchEngine
if archive.exists():
 for name in ['knowledge_query','knowledge_search']:
  module_name='gateway.'+('knowledge_query' if name=='knowledge_query' else 'rejected_knowledge_search')
  spec=importlib.util.spec_from_file_location(module_name,archive/(name+'.py'))
  module=importlib.util.module_from_spec(spec);sys.modules[module_name]=module;spec.loader.exec_module(module)
  if name=='knowledge_search':CandidateEngine=module.KnowledgeSearchEngine
split=sys.argv[1];assert split in {'dev','holdout'}
plan=json.loads((OUT/'evaluation-plan.json').read_text());assert hashlib.sha256((PRIVATE/'labels.json').read_bytes()).hexdigest()==plan['labels_sha256']
labels=json.loads((PRIVATE/'labels.json').read_text(encoding='utf-8'))
cases=[c for c in labels['cases'] if c['split']==split]
if split=='holdout':
 lock=json.loads((OUT/'candidate-lock.json').read_text())
 for rel,sha in lock['source'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha
 assert not (OUT/'holdout-result.json').exists(),'Holdout is one-shot; preserve it'
name='qldapm-demo-rag-evaluation';port=16339
if subprocess.run(['docker','inspect',name],capture_output=True).returncode:
 subprocess.run(['docker','run','-d','--name',name,'--label','org.qldapm.demo-rag=true','--memory','512m','--cpus','1','-p',f'127.0.0.1:{port}:6333','qdrant/qdrant:latest'],capture_output=True,check=True)
 for _ in range(30):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/healthz',timeout=1).status_code==200:break
  except httpx.HTTPError:pass
  time.sleep(1)
vc=VectorClient(qdrant_url=f'http://127.0.0.1:{port}',collection_name='demo_frozen',timeout=30)
if split=='dev':
 points=json.loads((PRIVATE/'source-vectors.json').read_text());assert vc.ensure_collection() and vc.upsert_points(points) and vc.verify_points(points)
storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(PRIVATE/'knowledge.sqlite')))
docs=[d for d in storage.query_documents('6','PM') if d.metadata.get('actor_id')==20]
ids=[d.source_hash for d in docs];metadata={d.source_hash:d.metadata for d in docs}
class Cached:
 enabled=True
 def __init__(self):self.vector=None
 def embed_texts(self,texts):return [self.vector]
 def search_dense(self,**kwargs):return vc.search_dense(**kwargs)
cached=Cached();engines={'baseline':KnowledgeSearchEngine(storage,vector_client=cached),'candidate':CandidateEngine(storage,vector_client=cached,hybrid_evidence=True)}
query_cache=PRIVATE/(split+'-embeddings.json')
vectors=json.loads(query_cache.read_text()) if query_cache.exists() else {}
rows=[]
with httpx.Client(timeout=90) as client:
 for i,case in enumerate(cases):
  start=time.monotonic()
  if case['id'] not in vectors:
   response=client.post('http://127.0.0.1:11434/api/embed',json={'model':'bge-m3','input':[case['query']],'truncate':False,'options':{'num_thread':1}});response.raise_for_status()
   vectors[case['id']]=response.json()['embeddings'][0];query_cache.write_text(json.dumps(vectors))
  cached.vector=vectors[case['id']];embed_seconds=time.monotonic()-start
  for mode,engine in engines.items():
   begin=time.monotonic();hits=engine.search(case['query'],'6','PM',limit=5,actor_id=20,document_ids=ids)
   returned=[hit.native_id for hit in hits];rank=next((j+1 for j,hit in enumerate(returned) if hit in case['relevant_ids']),None)
   citation_errors=sum(hit.document_id not in metadata or hit.native_id!=metadata[hit.document_id].get('native_id') or hit.lock_version!=metadata[hit.document_id].get('lock_version') for hit in hits)
   rows.append({'case':case['id'],'kind':case['kind'],'language':case['language'],'mode':mode,'rank':rank,'ids':returned,'citation_errors':citation_errors,'seconds':time.monotonic()-begin+embed_seconds})
  print(json.dumps({'split':split,'case':i+1,'total':len(cases)}),flush=True)
def metrics(mode):
 subset=[r for r in rows if r['mode']==mode];pos=[r for r in subset if r['kind']=='positive'];neg=[r for r in subset if r['kind']=='negative'];times=sorted(r['seconds'] for r in subset)
 return {'positives':len(pos),'negatives':len(neg),'hit_at_5':sum(r['rank'] is not None for r in pos)/len(pos),'false_positive_rate':sum(bool(r['ids']) for r in neg)/len(neg),
         'citation_errors':sum(r['citation_errors'] for r in subset),'p95_seconds':times[math.ceil(.95*len(times))-1]}
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'split':split,'metrics':{mode:metrics(mode) for mode in engines},'label_sha256':plan['labels_sha256'],
 'scope':'real local BGE-M3/query embeddings + actual isolated Qdrant/SQLite frozen Project6 actor20; agent-labelled correlated paired queries, HUMAN_REVIEW_PENDING','rows':rows}
(OUT/(split+'-result.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['metrics']))

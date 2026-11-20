"""Real local BGE-M3/Qdrant against captured authorized IDs, never a mock/live-MAIN-API claim."""
import json,os,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
script='''import json,sys,time,sqlite3
from pathlib import Path
from gateway.knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig
from gateway.vector_client import VectorClient
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.knowledge_answer import grounded_response
import gateway.knowledge_search as search
data=json.load(sys.stdin);corpus=data['corpus'];gold=[c for c in data['gold']['cases'] if not data['calibration_only'] or c['partition']=='calibration'];cache={}
s=KnowledgeStorage(KnowledgeStorageConfig(db_path='/scratch/knowledge.sqlite'));v=VectorClient(timeout=20)
db=sqlite3.connect('file:/scratch/knowledge.sqlite?mode=ro',uri=True)
digest=next(m['digest'] for m in v._http.get(v.ollama_url+'/api/tags').json()['models'] if m['name']=='bge-m3:latest')
cache_path=Path('/scratch/query-embeddings.json')
if cache_path.exists():
 old=json.loads(cache_path.read_text());cache=old['vectors'] if old['model_digest']==digest else {}
for case in gold:
 if case['expected_behavior'] in ['deny','runtime_tool']:continue
 if case['question'] not in cache:
  cache[case['question']]=v.embed_texts([case['question']]);cache_path.write_text(json.dumps({'model_digest':digest,'vectors':cache}))
embed=v.embed_texts;v.embed_texts=lambda texts:cache[texts[0]]
results=[]
for threshold in data['thresholds']:
 search.DENSE_MIN_COSINE=threshold;rows=[]
 for case in gold:
  if case['expected_behavior'] in ['deny','runtime_tool']:continue
  ids=list(next(x['document_ids'] for x in corpus if x['project']==case['project_scope']))
  for row in db.execute("SELECT source_hash FROM knowledge_documents WHERE project_id=? AND source_id IN ('file:main-workflow-contract','file:project6-integration-qualification')",(str(case['project_scope']),)):ids.append(row[0])
  engine=KnowledgeSearchEngine(s,vector_client=v);start=time.monotonic()
  hits=engine.search(case['question'],str(case['project_scope']),'AI_SYSTEM_OWNER',5,actor_id=18,document_ids=ids)
  found=[h.source_id for h in hits]
  expected=case['expected_source_ids'];hit=all(x in found for x in expected) if expected else not found
  items=[{'title':h.title,'source_id':h.source_id,'document_id':h.document_id,'native_id':h.native_id,'lock_version':h.lock_version,
    'project_id':case['project_scope'],'source_sha256':h.metadata.get('source_sha256'),'citation':f'/work_packages/{h.native_id}' if h.native_id else h.source_id+'#sha256='+str(h.metadata.get('source_sha256')),
    'passage':h.passage,'chunk_index':h.chunk_index,'chunk_hash':h.chunk_hash,'retrieval_reference':f'{h.document_id}:{h.chunk_index}:{h.chunk_hash}'} for h in hits]
  answer=grounded_response(case['question'],items,engine.dense_state,mode='answer')
  quoted=chr(10).join(c['quote'] for c in (answer.get('answer') or {}).get('claims',[]))
  fact_pass=all(f in quoted for f in case['expected_answer_facts']) if case['expected_answer_facts'] else answer.get('answer') is None
  rows.append({'id':case['id'],'partition':case['partition'],'question':case['question'],'sources':found,'expected':expected,'hit':hit,'answer_fact_pass':fact_pass,'answer':answer,'dense_state':engine.dense_state,'matches':[{ 'source':h.source_id,'type':h.match_type,'score':h.score,'snippet':h.snippet} for h in hits],'seconds':time.monotonic()-start})
 results.append({'threshold':threshold,'calibration':{'passed':sum(r['hit'] for r in rows if r['partition']=='calibration'),'total':sum(r['partition']=='calibration' for r in rows)},'rows':rows})
v.close();print(json.dumps({'scope':'Actual BGE-M3/Qdrant read-only + captured Native ACL/version document-ID scope; SQLite private backup; not Main command API or Gemini answer E2E','results':results},ensure_ascii=False))'''
serving=json.loads(subprocess.check_output(['docker','inspect','qldapm-ai-gateway-1']))[0]
private=Path(next(m['Source'] for m in serving['Mounts'] if m['Destination']=='/state'))/'operator/phase4-rag-20261113';private.mkdir(parents=True,exist_ok=True)
copy="import sqlite3;from pathlib import Path;p=Path('/state/operator/phase4-rag-20261113');p.mkdir(parents=True,exist_ok=True);a=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);b=sqlite3.connect(p/'knowledge.sqlite');a.backup(b);b.close();a.close()"
if not (private/'knowledge.sqlite').exists():subprocess.run(['docker','exec','qldapm-ai-gateway-1','python','-c',copy],check=True)
assert (private/'knowledge.sqlite').exists()
network=next(iter(json.loads(subprocess.check_output(['docker','inspect','qldapm-ai-gateway-1']))[0]['NetworkSettings']['Networks']))
thresholds=[float(x) for x in sys.argv[2:] if not x.startswith('--')] or [0.65]
data={'corpus':json.loads((OUT/'authorized-corpus.json').read_text(encoding='utf-8')),'gold':json.loads((OUT/'gold.json').read_text(encoding='utf-8')),'thresholds':thresholds,'calibration_only':'--calibration' in sys.argv}
cmd=['docker','run','--rm','-i','--network',network,'-e','QLDAPM_AI_RUNTIME=/scratch','--mount',f'type=bind,source={ROOT / "openproject/ai/gateway"},target=/app/gateway,readonly','--mount',f'type=bind,source={private},target=/scratch','--entrypoint','python','sha256:6edeea411e079bb8b2cb8242b4a79673cd74734943536e965d69bbbfbd61cef0','-c',script]
shared_lock=private.parents[1]/'qldapm-bge-m3.lock'
assert shared_lock.is_file()
cmd[2:2]=['--mount',f'type=bind,source={shared_lock},target=/scratch/qldapm-bge-m3.lock']
p=subprocess.run(cmd,input=json.dumps(data),text=True,capture_output=True,encoding='utf-8',timeout=600)
(OUT/(sys.argv[1]+'-stderr.log')).write_text(p.stderr,encoding='utf-8');assert p.returncode==0,p.stderr[-400:]
value=json.loads(p.stdout);(OUT/(sys.argv[1]+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'threshold':r['threshold'],'calibration':r['calibration'],'total_hits':sum(x['hit'] for x in r['rows']),'total':len(r['rows'])} for r in value['results']]))

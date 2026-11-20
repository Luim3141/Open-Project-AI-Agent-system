"""Read authorized Project6 Native sources; no database/config/provider mutation."""
import hashlib,json,os,sqlite3,subprocess
from pathlib import Path
OUT=Path(__file__).parent;RAG=OUT.parent/'integration-final/rag'
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
target=private/'native-whole-journals-snapshot.json'
assert not target.exists(),'PRESERVE_EXISTING_SNAPSHOT'
db=sqlite3.connect((private/'knowledge-baseline.sqlite').as_uri()+'?mode=ro',uri=True)
ids=sorted({json.loads(r[0])['native_id'] for r in db.execute("SELECT metadata FROM knowledge_documents WHERE project_id='6' AND source_id LIKE 'actor:20:wp:%'")})
code=(RAG/'native_corpus_candidate.py').read_text()+'''
import time
from pathlib import Path
from gateway.store import Store
from gateway.native import Native
from gateway.openproject_loader import sanitize_text
from gateway.knowledge_classifier import _compute_hash,KnowledgeDocType
s=Store('/state');key=s.credential(20);n=Native('http://web:8080',key,6);who=n.identity(20)
assert who['role']=='PM' and who['user_id']==20
documents=[]
for identifier in '''+repr(ids)+''':
 n=Native('http://web:8080',key,6);wp=n.package(identifier)
 activities=n.collection(f'/api/v3/work_packages/{identifier}/activities')
 text,meta=document_text(wp,activities,lambda value:sanitize_text(value,6))
 source_id=f'actor:20:wp:{identifier}'
 meta.update(native_id=identifier,lock_version=wp['lockVersion'],actor_id=20,source_updated_at=wp.get('updatedAt'))
 documents.append({'source_id':source_id,'document_id':_compute_hash(text,KnowledgeDocType.WORK_PACKAGE.value,source_id,'6'),
  'project_id':6,'allowed_roles':['PM'],'title':sanitize_text(wp['subject'],6),'content':text,'metadata':meta,
  'source_sha256':hashlib.sha256(text.encode()).hexdigest()})
n=Native('http://web:8080',key,6);assert n.identity(20)['role']=='PM'
print(json.dumps({'documents':documents,'observed':time.time(),'actor':20,'project_id':6},ensure_ascii=False))
'''
process=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=code.encode(),capture_output=True,timeout=180)
if process.returncode:
    (private/'native-snapshot-failure.log').write_bytes(process.stderr);raise RuntimeError('NATIVE_READ_SNAPSHOT_FAILED_PRIVATE_DIAGNOSTIC')
body=json.loads(process.stdout);assert len(body['documents'])==len(ids)
with target.open('xb') as stream:stream.write(process.stdout)
result={'status':'READ_ONLY_NATIVE_CANDIDATE_SNAPSHOT','documents':len(ids),'actor':20,'project_id':6,
        'snapshot_sha256':hashlib.sha256(process.stdout).hexdigest(),
        'loader_sha256':hashlib.sha256((RAG/'native_corpus_candidate.py').read_bytes()).hexdigest(),
        'source_chars':sum(len(d['content']) for d in body['documents']),
        'whole_journals':sum(len(d['metadata']['activity_ids']) for d in body['documents']),
        'omitted_journals':sum(len(d['metadata']['omitted_activity_ids']) for d in body['documents']),
        'partial_json_truncation':False,'holdout_access':False,'main_business_writes':0,'generation_calls':0,
        'versions':{str(d['metadata']['native_id']):d['metadata']['lock_version'] for d in body['documents']}}
(OUT/'rag-native-candidate-snapshot.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

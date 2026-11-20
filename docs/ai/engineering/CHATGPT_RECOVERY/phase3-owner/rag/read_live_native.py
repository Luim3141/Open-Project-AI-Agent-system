"""Read bounded Project6 Native/index provenance; raw source stays private."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

OUT = Path(__file__).parent
PRIVATE = Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase3-native-audit'
CODE = r'''
from datetime import datetime,timezone
import hashlib,json,sqlite3
from pathlib import Path
from gateway.native import Native
from gateway.openproject_loader import actor_work_package_document
from gateway.vector_client import VectorClient
ids=[379,380,381,382,383,384,386,387,389,390]
config=json.loads(Path('/state/config.json').read_text())
credentials=json.loads(Path('/state/credentials.json').read_text())
assert config['engineering']['enabled'] is True
out={'utc':datetime.now(timezone.utc).isoformat(),'project_id':6,'actors':{},'documents':[]}
native=None
for actor in [18,20]:
 client=Native(config['openproject_url'],credentials[str(actor)],6)
 who=client.identity(actor)
 assert who['user_id']==actor and who['role']==config['engineering']['actors'][str(actor)]
 project=client.call('/api/v3/projects/6')
 assert project['identifier']=='ai-dev-demo' and project['active']
 versions={}
 for identifier in ids:
  wp=client.package(identifier)
  assert wp['_links']['project']['href']=='/api/v3/projects/6'
  versions[str(identifier)]=wp['lockVersion']
  if actor==20:
   activities=client.collection(f'/api/v3/work_packages/{identifier}/activities')
   doc=actor_work_package_document(wp,6,actor,who['role'],activities)
   out['documents'].append({'native_id':identifier,'native_lock_version':wp['lockVersion'],
    'title':doc.title,'source_id':doc.source_id,'source_hash':doc.source_hash,
    'metadata':doc.metadata,'content':doc.content,'allowed_roles':doc.allowed_roles,
    'native_package':wp,'native_activities':activities})
 out['actors'][str(actor)]={'role':who['role'],'project_id':who['project_id'],'versions':versions}
db=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row
out['index_documents']=[dict(r) for r in db.execute("SELECT * FROM knowledge_documents WHERE project_id='6' AND json_extract(metadata,'$.actor_id')=20")]
out['index_chunks']=[dict(r) for r in db.execute("SELECT c.* FROM knowledge_chunks c JOIN knowledge_documents d ON d.source_hash=c.document_id WHERE d.project_id='6' AND json_extract(d.metadata,'$.actor_id')=20")]
db.close()
with VectorClient()._http as http:
 offset=None;points=[]
 for _ in range(5):
  body={'filter':{'must':[{'key':'project_id','match':{'value':'6'}}, {'key':'allowed_roles','match':{'value':'PM'}},{'key':'actor_id','match':{'value':20}}]},'limit':256,'with_vector':True,'with_payload':True}
  if offset is not None:body['offset']=offset
  response=http.post('http://qldapm-qdrant:6333/collections/qldapm_knowledge_dense/points/scroll',json=body,timeout=20)
  response.raise_for_status();result=response.json()['result'];points.extend(result['points']);offset=result['next_page_offset']
  if offset is None:break
 else:raise AssertionError('SCOPED_POINT_READ_BOUND')
out['vectors']=points
out['source_hashes']={name:hashlib.sha256(Path('/app/gateway',name).read_bytes()).hexdigest() for name in ['knowledge_search.py','knowledge_ingestion.py','openproject_loader.py','service.py','vector_client.py']}
print(json.dumps(out,ensure_ascii=False))
'''


def run(refresh=False):
    PRIVATE.mkdir(exist_ok=True)
    result=subprocess.run(['docker','exec','-i','qldapm-ai-gateway-1','python','-'],input=CODE,
        text=True,encoding='utf-8',capture_output=True,timeout=180)
    if result.returncode:
        raise RuntimeError(f'READ_ONLY_SNAPSHOT_FAILED_EXIT_{result.returncode}: '+result.stderr[-1500:])
    raw=json.loads(result.stdout)
    prefix='refresh-native-index' if refresh else 'current-native-index'
    path=PRIVATE/(prefix+'-snapshot.json')
    assert not path.exists(), 'DO_NOT_OVERWRITE_FROZEN_SOURCE'
    path.write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
    docs={d['source_hash']:d for d in raw['index_documents']}
    points=raw['vectors']
    rows=[]
    for d in raw['documents']:
        indexed=[v for v in docs.values() if json.loads(v['metadata'])['native_id']==d['native_id']]
        exact=[v for v in indexed if v['source_hash']==d['source_hash'] and json.loads(v['metadata'])==d['metadata']]
        pp=[p for p in points if p['payload']['document_id']==d['source_hash']]
        rows.append({'native_id':d['native_id'],'native_lock_version':d['native_lock_version'],
            'native_source_hash':d['source_hash'],'native_content_chars':len(d['content']),
            'index_versions':[json.loads(v['metadata'])['lock_version'] for v in indexed],
            'current_source_exactly_indexed':bool(exact),'current_source_vector_points':len(pp),
            'sqlite_chunks':len([c for c in raw['index_chunks'] if c['document_id']==d['source_hash']])})
    image=subprocess.run(['docker','inspect','qldapm-ai-gateway-1','--format','{{.Image}}'],capture_output=True,text=True,check=True).stdout.strip()
    summary={'utc':raw['utc'],'route':'OS_OPERATOR_NATIVE_READ_ONLY_AND_SCOPED_INDEX_READ',
        'command':'openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase3-owner/rag/read_live_native.py',
        'container':'qldapm-ai-gateway-1','image':image,'actors':raw['actors'],'project_id':6,
        'raw_snapshot_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_hashes':raw['source_hashes'],
        'documents':rows,'scoped_vector_count':len(points),'mutation_calls_performed':0,
        'limits':'Sequential non-atomic Native identity/project/GET and SQLite mode=ro/Qdrant filtered scroll only. No signed Core bridge, no search/generation or index/config/business mutation. Snapshot in private operator directory.'}
    (OUT/(prefix+'-audit.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    import sys
    run(refresh='--refresh' in sys.argv[1:])

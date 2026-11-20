"""Read-only Main Project6 RAG corpus snapshot, private data and public hashes only."""
import datetime,hashlib,json,os,sqlite3,subprocess
from pathlib import Path
import httpx

OUT=Path(__file__).parent
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/demo-final-rag'
PRIVATE.mkdir(parents=True,exist_ok=False)
code="import sqlite3,sys;s=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);d=sqlite3.connect(':memory:');s.backup(d);sys.stdout.buffer.write(d.serialize())"
data=subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=45)
(PRIVATE/'knowledge.sqlite').write_bytes(data)
db=sqlite3.connect((PRIVATE/'knowledge.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
documents=[dict(r) for r in db.execute("SELECT * FROM knowledge_documents WHERE project_id='6'")]
allowed={r['source_hash'] for r in documents if json.loads(r['metadata']).get('actor_id')==20}
assert allowed
points=[];offset=None
with httpx.Client(timeout=20) as client:
 while True:
  body={'limit':100,'with_payload':True,'with_vector':True,'filter':{'must':[{'key':'project_id','match':{'value':'6'}},{'key':'document_id','match':{'any':sorted(allowed)}}]}}
  if offset is not None:body['offset']=offset
  response=client.post('http://127.0.0.1:6333/collections/qldapm_knowledge_dense/points/scroll',json=body);response.raise_for_status();doc=response.json()['result']
  points.extend(doc['points']);offset=doc.get('next_page_offset')
  if offset is None:break
(PRIVATE/'source-vectors.json').write_text(json.dumps(points,separators=(',',':')),encoding='utf-8')
manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only Main Project6 actor20 corpus; private SQLite/vectors; no Project5 mutation',
 'private_root':str(PRIVATE),'files':{n:hashlib.sha256((PRIVATE/n).read_bytes()).hexdigest() for n in ['knowledge.sqlite','source-vectors.json']},
 'documents':[{'source_hash':r['source_hash'],'source_id':r['source_id'],'title':r['title'],'native_id':json.loads(r['metadata']).get('native_id'),'version':json.loads(r['metadata']).get('lock_version'),'chars':len(r['content'])} for r in documents if r['source_hash'] in allowed],
 'point_count':len(points)}
(OUT/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))

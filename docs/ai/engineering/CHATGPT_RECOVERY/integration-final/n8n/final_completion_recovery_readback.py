"""Read-only Native/SQLite/FTS/Qdrant/search/execution check for the isolated recovery source."""
import datetime
import json
import subprocess
from pathlib import Path

OUT=Path(__file__).parent


def docker(container,program,command):
    p=subprocess.run(['docker','exec','-i',container,*program],input=command,text=True,capture_output=True,timeout=120)
    assert p.returncode==0,'READBACK_FAILED: '+p.stderr[-300:]
    return json.loads(p.stdout)


code="""import json,sqlite3
from pathlib import Path
from contextlib import closing
from gateway.store import Store
from gateway.service import Service
from gateway.engineering import scoped_service
from gateway.vector_client import VectorClient
r=Path('/state');s=scoped_service(Service(Store(r),json.load(open(r/'config.json')),'/workspaces'),6)
n,w=s.native_actor(20);item=n.package(392)
with sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True) as d:
 d.row_factory=sqlite3.Row
 documents=[dict(r) for r in d.execute("SELECT id,project_id,source_id,source_hash,metadata FROM knowledge_documents WHERE project_id='6' AND source_id IN ('op:wp:392','actor:20:wp:392')")]
 for doc in documents:
  metadata=json.loads(doc.pop('metadata'));doc['native_version']=metadata.get('lock_version');doc['native_id']=metadata.get('native_id')
  doc['chunks']=d.execute('SELECT count(*) FROM knowledge_chunks WHERE document_id=?',(doc['id'],)).fetchone()[0]
  doc['fts_rows']=d.execute('SELECT count(*) FROM knowledge_fts WHERE source_hash=?',(doc['source_hash'],)).fetchone()[0]
 assert len(documents)==2 and all(doc['native_id']==392 and doc['native_version']==item['lockVersion'] and doc['chunks']>0 and doc['fts_rows']==1 for doc in documents)
with closing(VectorClient()) as v:
 points=[p for p in v.scroll_points('6') if p['payload'].get('document_id') in {d['id'] for d in documents}]
assert len(points)==2
search=s.knowledge(w,n,'knowledge_search',{'query':item['subject'],'native_ids':[392],'limit':5})
assert search['items'] and all(r['native_id']==392 and r['lock_version']==item['lockVersion'] and r['citation']=='/work_packages/392' for r in search['items'])
with s.store.connect() as d:
 dead=[dict(r) for r in d.execute("SELECT id,state,attempts,error FROM integration_event_outbox WHERE state='DEAD'")]
 pending=d.execute("SELECT count(*) FROM integration_event_outbox WHERE state IN ('PENDING','RETRY','SENDING')").fetchone()[0]
 mode=d.execute('SELECT mode FROM engineering_control WHERE project=6').fetchone()[0]
from gateway.integration_events import snapshot
projection=next(r for r in snapshot(s.store) if r['workflow']=='WF14')
print(json.dumps({'native_id':392,'native_version':item['lockVersion'],'citation':'/work_packages/392',
 'documents':documents,'vector_point_ids':[str(p['id']) for p in points],'search_current_citation_count':len(search['items']),
 'workflow14_projection':projection,'pending_events':pending,'historical_dead':dead,'engineering_mode':mode,
 'provider_inference_calls':0,'native_business_writes':0}))
"""
readback=docker('qldapm-ai-gateway-1',['python','-'],code)
proof=json.loads((OUT/'final-completion-main-wf14-recovery.json').read_text())
identities=[{'id':e['execution_id'],'event_id':e['event_id']} for e in proof['readback']['events']]
javascript="""const fs=require('fs'),input=JSON.parse(fs.readFileSync(0,'utf8'));
const d=new(require('node:sqlite').DatabaseSync)('/home/node/.n8n/database.sqlite',{readOnly:true});
const rows=input.map(x=>{const r=d.prepare('SELECT e.id,e.workflowId,e.status,e.startedAt,e.stoppedAt,j.data FROM execution_entity e JOIN execution_data j ON j.executionId=e.id WHERE e.id=?').get(x.id);if(!r||r.status!=='success'||!r.data.includes(x.event_id))throw new Error('EXECUTION_EVENT_BINDING_REQUIRED');return {id:r.id,workflow_id:r.workflowId,status:r.status,started_at:r.startedAt,stopped_at:r.stoppedAt,event_id:x.event_id,stored_event_binding:true}});console.log(JSON.stringify(rows));d.close();"""
p=subprocess.run(['docker','exec','-i','qldapm-n8n-main','node','-e',javascript],input=json.dumps(identities),text=True,capture_output=True,timeout=30)
assert p.returncode==0,'EXECUTION_READBACK_FAILED: '+p.stderr[-200:]
readback['actual_n8n_executions']=json.loads(p.stdout)
readback['observed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
readback['status']='MAIN_FAILURE_RETRY_INDEX_CURRENT_CITATION_EXECUTIONS_VERIFIED'
(OUT/'final-completion-main-wf14-readback.json').write_text(json.dumps(readback,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':readback['status'],'documents':len(readback['documents']),'vectors':len(readback['vector_point_ids']),
    'search_current_citation_count':readback['search_current_citation_count'],'execution_ids':[r['id'] for r in readback['actual_n8n_executions']]}))

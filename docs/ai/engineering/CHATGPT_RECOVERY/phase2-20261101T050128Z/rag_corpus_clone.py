"""Real corpus/vector copies, disposable Qdrant, local BGE-M3; never writes MAIN."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import urllib.request
import base64
import httpx
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT/'openproject/ai'))
from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
from gateway.vector_client import VectorClient
from gateway.knowledge_search import KnowledgeSearchEngine
from gateway.knowledge_classifier import classify_document, KnowledgeDocType
from gateway.knowledge_ingestion import KnowledgeIngester

RUN=Path(__file__).parent
identifier=uuid.uuid4().hex[:12]
name='qldapm-recovery-p2-rag-'+identifier
network=name+'-net'
private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator'/name
private.mkdir()
shutil.copy2(Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/chatgpt-recovery-20261101T043043Z/knowledge.sqlite',private/'knowledge.sqlite')
result={'status':'RUNNING','private_copy':str(private),'queries':[]}
def docker(*a):return subprocess.check_output(['docker',*a],stderr=subprocess.PIPE,timeout=60)
def request(url,body=None,method=None):
    r=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(r,timeout=10) as response:return json.load(response)
points=[];offset=None
while True:
    data={'filter':{'must':[{'key':'project_id','match':{'value':'6'}}]},'limit':100,'with_payload':True,'with_vector':True}
    if offset is not None:data['offset']=offset
    page=request('http://127.0.0.1:6333/collections/qldapm_knowledge_dense/points/scroll',data)['result']
    points+=page['points'];offset=page.get('next_page_offset')
    if offset is None:break
(private/'source-vectors.json').write_text(json.dumps(points))
image=json.loads(docker('inspect','qldapm-qdrant'))[0]['Image']
docker('network','create','--internal','--label','org.qldapm.ragclone='+identifier,network)
started=False;vector=None;helper=False;host_http=None
try:
    docker('run','-d','--pull','never','--name',name,'--label','org.qldapm.ragclone='+identifier,
        '--network',network,'--tmpfs','/qdrant/storage:rw,size=256m',
        '-e','QDRANT__TELEMETRY_DISABLED=true',image);started=True
    # No published ports/egress: relay actual Qdrant HTTP through a disposable internal-network helper.
    docker('run','-d','--pull','never','--name',name+'-http','--label','org.qldapm.ragclone='+identifier,
        '--network',network,'--entrypoint','python','qldapm-ai:chatgpt-recovery-20261101-r2',
        '-c','import time;time.sleep(900)');helper=True
    relay="""import urllib.request,urllib.error,base64,json,sys
p=json.load(sys.stdin);r=urllib.request.Request(p['url'],data=base64.b64decode(p['body']) if p['body'] else None,headers=p['headers'],method=p['method'])
try:x=urllib.request.urlopen(r,timeout=20)
except urllib.error.HTTPError as e:x=e
print(json.dumps({'status':x.status,'body':base64.b64encode(x.read()).decode()}))
"""
    host_http=httpx.Client(timeout=60)
    def transport(req):
        if req.url.host==name:
            payload={'url':str(req.url),'method':req.method,'headers':dict(req.headers),'body':base64.b64encode(req.content).decode()}
            payload['headers']['accept-encoding']='identity'
            p=subprocess.run(['docker','exec','-i',name+'-http','python','-c',relay],input=json.dumps(payload).encode(),capture_output=True,check=True,timeout=30)
            response=json.loads(p.stdout)
            return httpx.Response(response['status'],content=base64.b64decode(response['body']),headers={'Content-Type':'application/json'})
        assert req.url.host=='127.0.0.1' and req.url.port==11434, 'UNEXPECTED_NETWORK_TARGET'
        return host_http.send(req)
    time.sleep(1)
    vector=VectorClient(qdrant_url='http://'+name+':6333',timeout=20)
    vector._http.close();vector._http=httpx.Client(transport=httpx.MockTransport(transport))
    assert vector.ensure_collection() and vector.upsert_points(points)
    storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(private/'knowledge.sqlite')))
    engine=KnowledgeSearchEngine(storage,vector_client=vector)
    for query,expected in [('healthz',384),('healthz route',384),('kiểm tra sức khỏe máy chủ',384),
                           ('service health check endpoint',384),('email',None)]:
        hits=engine.search(query,'6','PM',actor_id=20)
        ids=[h.native_id for h in hits]
        passed=expected in ids if expected is not None else not hits
        result['queries'].append({'query':query,'native_ids':ids,'match_types':[h.match_type for h in hits],
            'scores':[h.score for h in hits],'expected_native_id':expected,'status':'PASS' if passed else 'FAIL'})
    assert engine.search('healthz','999','PM',actor_id=20)==[]
    assert engine.search('healthz','6','PM',actor_id=999)==[]
    with patch.object(vector,'embed_texts',side_effect=TimeoutError('synthetic outage')):
        assert engine.search('healthz','6','PM',actor_id=20)
        assert engine.dense_state=='FALLBACK'
    result['acl_and_provider_fallback']='PASS'
    doc=classify_document(KnowledgeDocType.WORK_PACKAGE,'6','recovery-fixture:900001',
        'Isolated indexing marker','Recovery isolated vector indexing marker.',allowed_roles=['PM'],
        metadata={'actor_id':20,'native_id':900001,'lock_version':0})
    ingester=KnowledgeIngester(storage,vector)
    inserted=ingester.ingest(doc);assert inserted.vector_indexed
    hits=engine.search('indexing marker','6','PM',actor_id=20,document_ids=[doc.source_hash])
    assert hits and hits[0].native_id==900001
    assert ingester.deindex_source(doc.source_id,'6')
    assert engine.search('indexing marker','6','PM',actor_id=20,document_ids=[doc.source_hash])==[]
    result['synthetic_new_document_index_and_delete']='PASS'
    result['copied_vector_points']=len(points)
    result['status']='CLONE_CHECKS_COMPLETED' if all(q['status']=='PASS' for q in result['queries']) else 'SEMANTIC_RECALL_GAP'
finally:
    if vector:vector.close()
    if host_http:host_http.close()
    (RUN/'rag-corpus-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if started:
        data=json.loads(docker('inspect',name))[0];assert data['Config']['Labels']['org.qldapm.ragclone']==identifier
        docker('rm','-f',name)
    if helper:
        assert json.loads(docker('inspect',name+'-http'))[0]['Config']['Labels']['org.qldapm.ragclone']==identifier
        docker('rm','-f',name+'-http')
    assert json.loads(docker('network','inspect',network))[0]['Labels']['org.qldapm.ragclone']==identifier
    docker('network','rm',network)
print(json.dumps(result,ensure_ascii=False,indent=2))

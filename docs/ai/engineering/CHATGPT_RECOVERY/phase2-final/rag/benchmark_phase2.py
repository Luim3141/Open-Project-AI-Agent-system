"""Frozen source-grounded dev/holdout; isolated Qdrant only, no Main writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, str(Path.cwd()/'openproject/ai'))
from gateway.knowledge_classifier import KnowledgeDocument, KnowledgeDocType
from gateway.knowledge_ingestion import KnowledgeIngester
from gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
from gateway.knowledge_search import KnowledgeSearchEngine, DENSE_MIN_COSINE
from gateway.vector_client import VectorClient

OUT=Path(__file__).parent
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-final-rag'
SOURCE=PRIVATE.parent/'semantic-review-20261102'
DEV=[
 (383,'unicode','Tìm chữ hoa thường Unicode cho tiêu đề task','Locate task titles regardless of Unicode letter case'),
 (383,'german','Tìm Straße khi gõ STRASSE có được hỗ trợ không','Search for Straße using STRASSE and Unicode case folding'),
 (383,'sqlite','SQLite lower chỉ hỗ trợ ASCII, sửa tìm kiếm bằng cách nào','How is ASCII-only SQLite lower fixed for Unicode search'),
 (383,'escape','Từ khóa chứa phần trăm và gạch dưới được xử lý thế nào','How are percent and underscore escaped in task searches'),
 (384,'route','Route healthz trả JSON status ok và version nào','Which JSON status app and version does healthz return'),
 (384,'health','Kiểm tra tình trạng mini task manager qua endpoint healthz','Check mini task manager health with the healthz endpoint'),
 (384,'exact','GET /healthz','GET healthz status ok'),
 (384,'long','Tôi cần biết ứng dụng còn hoạt động hay không bằng route healthz, xem JSON status ok mà không thay đổi dữ liệu','Find the healthz route that reports application health without modifying task records'),
 (386,'summary','Tổng số task active completed lấy từ SQLite ở đâu','Where are total active completed task counts read from SQLite'),
 (386,'invariant','total bằng active cộng completed là điều kiện gì','Which task summary guarantees total equals active plus completed'),
 (386,'empty','Không có công việc thì summary trả total active completed bao nhiêu','What does the summary return for total active completed with no tasks'),
 (386,'exact','GET /tasks/summary','tasks summary active completed'),
]
HOLDOUT=[
 (380,'new-record','Tạo một mục công việc rồi lưu trong SQLite','Add a new task record and save it in SQLite'),
 (380,'listing','Xem toàn bộ danh sách công việc đã tạo','Show the list of tasks that were created'),
 (380,'durable','Ứng dụng lưu bền các task bằng SQLite','The application persists task records using SQLite'),
 (380,'exact','Create/list tasks SQLite persistence','Create and list tasks with SQLite persistence'),
 (381,'editing','Sửa lại thông tin của một công việc hiện có','Modify the information of an existing task'),
 (381,'removal','Loại bỏ một công việc không còn cần thiết','Remove a task that is no longer needed'),
 (381,'progress','Cập nhật trạng thái tiến độ của công việc','Update the progress status of a task'),
 (381,'web','Trên web người dùng có thể edit delete status và search task','The usable web interface supports editing deleting status and task search'),
 (382,'request','Khi HTTP request lỗi thì request helper xử lý và hiển thị ra sao','How does the request helper handle and display HTTP errors'),
 (382,'retry','Lỗi tải danh sách thì có loading empty và retry không','Does the interface show loading empty and retry states'),
 (382,'ordering','Phản hồi tìm kiếm cũ không được đè kết quả mới hơn','An older search response must not overwrite newer results'),
 (382,'submit','Sau khi nhấn submit thì phải chống gửi form lặp và khôi phục controls nếu lỗi','After submitting the form prevent duplicate submission and restore controls after errors'),
]
NEGATIVE_DEV=[
 ('avatar','Cách tải avatar cá nhân lên ứng dụng task','How to upload a personal avatar into the task application'),
 ('sms','Gửi tin nhắn SMS nhắc hạn task','Send SMS reminders for task deadlines'),
 ('payments','Thanh toán hóa đơn task qua Stripe','Pay task invoices through Stripe'),
 ('sso','Đăng nhập task qua SAML doanh nghiệp','Enterprise SAML login for the task manager'),
 ('audio','Đính kèm ghi âm vào task','Attach an audio recording to a task'),
 ('gps','Theo dõi vị trí GPS của người làm task','Track GPS locations of task workers'),
 ('video','Gọi video từ trang công việc','Start video calls from the task page'),
 ('push','Gửi push notification khi task sắp hết hạn','Send mobile push notifications before a task deadline'),
 ('billing','Tính phí thuê bao hằng tháng cho task manager','Charge monthly subscriptions for the task manager'),
 ('calendar','Đồng bộ lịch task với Outlook Calendar','Synchronize task dates with Outlook Calendar'),
]
NEGATIVE_HOLDOUT=[
 ('pdf','In báo cáo task thành PDF có chữ ký số','Print a task report as a digitally signed PDF'),
 ('csv-import','Nhập hàng loạt task từ một file CSV','Bulk import tasks from a CSV file'),
 ('oauth','Xác thực tài khoản task bằng Google OAuth','Authenticate task accounts using Google OAuth'),
 ('twofactor','Bật xác thực hai yếu tố cho ứng dụng task','Enable two factor authentication in the task application'),
 ('reminder','Lên lịch gửi email nhắc việc mỗi buổi sáng','Schedule task reminder emails every morning'),
 ('recurring','Tự động lặp lại một công việc vào thứ hai mỗi tuần','Automatically repeat a task every Monday'),
 ('role-permission','Phân quyền ai được sửa task theo nhóm người dùng','Control which user groups are allowed to edit tasks'),
 ('backup-retention','Cấu hình chính sách giữ bản backup SQLite của task manager','Configure SQLite backup retention for the task manager'),
 ('attachments','Lưu tài liệu đính kèm PDF vào từng task','Store attached PDF documents on individual tasks'),
 ('timezones','Chuyển hạn chót task giữa các múi giờ','Convert task deadlines between time zones'),
]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def load_candidate():
    import importlib.util
    path=OUT/'rejected_candidate_knowledge_ingestion.py'
    assert sha(path)=='68c0dbdada0b5a09fbab684585e60b9c857b7241878dcf9205b5a869a0c07c33'
    spec=importlib.util.spec_from_file_location('gateway.phase2_rejected_ingestion',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module
def docs_and_chunks():
    db=sqlite3.connect(f'file:{(SOURCE/"knowledge.sqlite").as_posix()}?mode=ro',uri=True);db.row_factory=sqlite3.Row
    docs=[];chunks={}
    for r in db.execute("SELECT * FROM knowledge_documents WHERE project_id='6' AND json_extract(metadata,'$.actor_id')=20"):
        d=KnowledgeDocument(KnowledgeDocType(r['doc_type']),r['project_id'],r['source_id'],r['title'],r['content'],r['source_hash'],json.loads(r['allowed_roles']),json.loads(r['metadata']))
        docs.append(d);chunks[d.source_hash]=[dict(c) for c in db.execute('SELECT chunk_index,chunk_text,chunk_hash FROM knowledge_chunks WHERE document_id=? ORDER BY chunk_index',(d.source_hash,))]
    db.close();assert len(docs)==7
    return docs,chunks

def prepare():
    PRIVATE.mkdir(exist_ok=True)
    target=PRIVATE/'labels.json'
    if target.exists():raise RuntimeError('FROZEN_DATASET_ALREADY_EXISTS')
    docs,chunks=docs_and_chunks();by_id={d.metadata['native_id']:d for d in docs};cases=[]
    for split,positive,negative in [('dev',DEV,NEGATIVE_DEV),('holdout',HOLDOUT,NEGATIVE_HOLDOUT)]:
        for native,intent,vi,en in positive:
            for language,query in [('vi',vi),('en',en)]:
                # Every relevant label is anchored in a source, with other overlapping sources graded partial.
                d=by_id[native]
                related={379,381,382,383} if native in (381,382,383) else {379}
                cases.append({'split':split,'kind':'positive','language':language,'intent':str(native)+':'+intent,
                    'query':query,'relevant_ids':[native],'partial_ids':sorted(related-{native}),
                    'source_hash':d.source_hash,'evidence_title':d.title,
                    'evidence_content_sha256':hashlib.sha256(d.content.encode()).hexdigest(),
                    'judgment':'agent source-content review; requested behavior/title directly supported; overlapping plans are partial, not proof of implementation','human_review':'PENDING'})
        for intent,vi,en in negative:
            for language,query in [('vi',vi),('en',en)]:cases.append({'split':split,'kind':'negative','language':language,'intent':intent,'query':query,'relevant_ids':[],'partial_ids':[],
                'judgment':'Feature absent in the seven allowed source contents. Task CRUD/storage references do not answer this requested extra capability. Agent judgment, human review PENDING.'})
    manifest={'created_utc':utc(),'source':{n:sha(SOURCE/n) for n in ['knowledge.sqlite','source-vectors.json']},
        'label_author':'same implementing agent; no independent human adjudication','scope':{'project':'6','role':'PM','actor':20},
        'gates':'phase2-final/rag/PLAN.md; unchanged dense cosine floor 0.65',
        'limitations':'paired language queries and few documents are correlated; historic intents known; fresh query holdout is source-group separated from development, not independently sampled',
        'cases':cases}
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'created_utc':manifest['created_utc'],'label_sha256':sha(target),'counts':{s:sum(c['split']==s for c in cases) for s in ['dev','holdout']}}))

class CachedEmbeddingClient:
    enabled=True
    def __init__(self,client):self.client=client;self.vector=None
    def embed_texts(self,texts):return [self.vector]
    def search_dense(self,**kwargs):return self.client.search_dense(**kwargs)

def metrics(rows):
    p=[r for r in rows if r['kind']=='positive'];n=[r for r in rows if r['kind']=='negative']
    ranks=[r['rank'] for r in p]
    times=sorted(r['total_seconds'] for r in rows)
    return {'positive':len(p),'negative':len(n),'hit1':sum(r==1 for r in ranks),'hit5':sum(r is not None and r<=5 for r in ranks),
        'mrr5':sum(1/r for r in ranks if r and r<=5)/len(p),'recall5':sum(r['recall5'] for r in p)/len(p),
        'negative_returned':sum(bool(r['ids']) for r in n),'abstention_correct':sum(not r['ids'] for r in n),
        'citation_identity_violations':sum(r['citation_errors'] for r in rows),
        'p50_seconds':times[len(times)//2],'p95_seconds':times[math.ceil(.95*len(times))-1]}

def run(split):
    started=utc();labels=json.loads((PRIVATE/'labels.json').read_text(encoding='utf-8'))
    assert all(sha(SOURCE/n)==h for n,h in labels['source'].items())
    assert DENSE_MIN_COSINE==.65
    docs,old_chunks=docs_and_chunks();allowed=[d.source_hash for d in docs]
    basestore=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(PRIVATE/'baseline.sqlite')))
    candstore=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(PRIVATE/'candidate.sqlite')))
    baseline=VectorClient(qdrant_url='http://127.0.0.1:16334',collection_name='phase2_baseline')
    candidate=VectorClient(qdrant_url='http://127.0.0.1:16334',collection_name='phase2_candidate')
    # Fail closed before every write unless this is the dedicated isolated port and collection.
    assert baseline.qdrant_url.endswith(':16334') and candidate.collection_name=='phase2_candidate'
    try:
        if split=='dev':
            points=[p for p in json.loads((SOURCE/'source-vectors.json').read_text()) if p['payload']['document_id'] in allowed]
            assert baseline.ensure_collection() and baseline.upsert_points(points) and baseline.verify_points(points)
            for d in docs:
                assert basestore.store_document(d,chunks=old_chunks[d.source_hash])
                result=load_candidate().KnowledgeIngester(candstore,candidate).ingest(d)
                assert result.vector_indexed,result
        clients={'baseline':CachedEmbeddingClient(baseline),'candidate':CachedEmbeddingClient(candidate)}
        stores={'baseline':basestore,'candidate':candstore};engines={k:KnowledgeSearchEngine(stores[k],vector_client=c) for k,c in clients.items()}
        cases=[c for c in labels['cases'] if c['split']==split];results={k:[] for k in engines}
        cache_path=PRIVATE/'query-vectors.json'
        cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
        for i,case in enumerate(cases):
            key=case['query'];begin=time.perf_counter();vec=baseline.embed_texts([key])[0];embed_s=time.perf_counter()-begin
            if key in cache:assert max(abs(a-b) for a,b in zip(vec,cache[key])) < 1e-5
            cache[key]=vec
            for name,engine in engines.items():
                clients[name].vector=vec;t=time.perf_counter()
                hits=engine.search(key,'6','PM',limit=5,actor_id=20,document_ids=allowed)
                elapsed=time.perf_counter()-t
                assert engine.dense_state=='READY'
                ids=[h.native_id for h in hits];rank=next((j+1 for j,id in enumerate(ids) if id in case['relevant_ids']),None)
                citation_errors=sum(h.document_id not in allowed or h.native_id!=next(d.metadata['native_id'] for d in docs if d.source_hash==h.document_id) for h in hits)
                results[name].append({'case_index':i,'query':key,'kind':case['kind'],'language':case['language'],'ids':ids,'rank':rank,
                    'recall5':len(set(ids)&set(case['relevant_ids']))/max(1,len(case['relevant_ids'])),
                    'citation_errors':citation_errors,'retrieval_seconds':elapsed,'embedding_seconds':embed_s,'total_seconds':elapsed+embed_s,
                    'match_types':[h.match_type for h in hits],'source_hashes':[h.document_id for h in hits]})
            print(split,i+1,len(cases),flush=True)
        cache_path.write_text(json.dumps(cache))
        output={'started_utc':started,'ended_utc':utc(),'environment':platform.platform()+'; isolated Qdrant 16334; local Ollama; historical Project6 SQLite copy',
            'command':' '.join(sys.argv),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'serving_gateway_image':'sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb (not deployed by benchmark)',
            'source_sha256':{n:sha(Path('openproject/ai/gateway')/n) for n in ['knowledge_search.py','knowledge_ingestion.py','vector_client.py','knowledge_storage.py']},
            'labels_sha256':sha(PRIVATE/'labels.json'),'snapshot_sha256':labels['source'],'threshold':DENSE_MIN_COSINE,
            'model':baseline._http.get(baseline.ollama_url+'/api/tags').json(),
            'metrics':{name:{lang:metrics([r for r in rows if lang=='all' or r['language']==lang]) for lang in ['vi','en','all']} for name,rows in results.items()},
            'results':results,'human_adjudication':'PENDING; not acceptance'}
        (PRIVATE/(split+'-results.json')).write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
        public={k:v for k,v in output.items() if k not in ('results','model')}
        public['model_digest']=output['model']['models'][0]['digest']
        (OUT/(split+'-summary.json')).write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(output['metrics'],indent=2))
    finally:baseline.close();candidate.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','dev','holdout']);args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:run(args.action)

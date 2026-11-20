"""Question labels authored from actual authorized source text; no invented source/fact IDs."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
snap=json.loads((OUT/'authorized-corpus.json').read_text(encoding='utf-8'))
files=json.loads((OUT/'dense-baseline.json').read_text(encoding='utf-8'))['files']
documents={d['source_id']:d for p in snap for d in p['documents']}
stored=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))['knowledge']['documents']
documents.update({d['source_id']:{**next(x for x in stored if x['source_id']==d['source_id']),**d} for d in files})
rows=[]
def add(question,project,sources=(),facts=(),group='semantic',behavior='sources',actor=18,partition='holdout'):
    for fact in facts:assert any(fact in documents[s]['content'] for s in sources),(question,fact)
    for s in sources:assert s in documents,s
    rows.append({'id':f'G{len(rows)+1:02}','question':question,'project_scope':project,'authorized_actor':actor,
        'expected_source_ids':list(sources),'expected_answer_facts':list(facts),'forbidden_claims':['Tài liệu chứng minh trạng thái runtime hiện tại','Owner đã nghiệm thu #398','Remote CI đã PASS'],
        'expected_behavior':behavior,'group':group,'partition':partition})
F='file:main-workflow-contract'
for q,fact,group in [
 ('WF01 supports which explicit sources?','an authorized Native Work Package ID','exact'),
 ('Muốn nạp tài liệu thì có thể đưa tên đường dẫn từ máy mình trực tiếp cho server không?','A source key never means a filesystem path.','semantic'),
 ('Nếu sửa file sau khi đăng ký mà chưa cập nhật dấu vân tay thì hệ thống làm gì?','A changed file is refused','semantic'),
 ('Tại sao vector ghi thất bại vẫn có thể repair mà không mất bản nguồn?','A failed vector commit is reported as pending','semantic'),
 ('Định dạng file nào được nạp tại boundary local knowledge?','UTF-8 TXT, Markdown, CSV, JSON','exact'),
 ('File PDF dạng ảnh có được nhận diện chữ tự động không?','OCR and arbitrary uploads are not implemented here.','semantic'),
 ('Bộ đọc PDF được chặn ở bao nhiêu trang và bao lâu?','15 seconds, 64 pages, 256 KiB','section'),
 ('Có thể dùng citation cũ sau khi source checksum thay đổi không?','stale citations and unregistered or unmatched points do not become evidence.','semantic'),
 ('WF01 file operations gồm những thao tác nào?','`ingest`, `reindex`, `search` and `read`','mixed'),
 ('Việc nạp file có đổi công việc trong OpenProject không?','Native Work Packages are never mutated by these operations.','semantic'),
 ('Hệ thống tạo embeddings và lưu các đoạn nội dung ở đâu?','persists document/chunk metadata in SQLite, embeds through local Ollama BGE-M3','multifact'),
 ('Citation cho file lưu những định danh nào?','logical source key, document identity and original file SHA256','citation'),
 ('Phản hồi chưa kiểm chứng của người dùng có tự đổi registry được không?','Unverified user feedback cannot change the registry or promote content.','semantic'),
 ('Ai có thể yêu cầu indexing theo hợp đồng local?','PM and AI System Owner can request indexing.','exact'),
 ('Search/readback có kiểm tra lại danh tính và vai trò không?','fresh authenticated identity and the current server role, project and checksum policy','semantic'),
 ('Tài liệu hợp đồng này có phải bằng chứng thực thi QA không?','not a QA test execution attestation','historical'),
]:add(q,5,[F],[fact],group,partition='calibration' if len(rows) in [0,1,2,3] else 'holdout')
for q,source,fact,group in [
 ('Theo tài liệu dự án, backend và nơi lưu công việc dùng công nghệ gì?','op:wp:379','Python FastAPI','semantic'),
 ('Ứng dụng quản lý việc này lưu thông tin bằng cơ sở dữ liệu nào?','op:wp:379','SQLite','semantic'),
 ('API nào đếm tổng số việc và số đang hoạt động, số hoàn thành?','op:wp:386','GET /tasks/summary','semantic'),
 ('Muốn tải danh sách công việc ra bảng CSV thì dùng API nào?','op:wp:391','GET /tasks/export.csv','semantic'),
 ('API kiểm tra có một công việc theo id hay không được mô tả ở đâu?','op:wp:389','GET /tasks/{task_id}/exists','semantic'),
 ('Chỉ đọc tên của một việc mà không cần lấy toàn bộ thông tin thì dùng gì?','op:wp:390','GET /tasks/{task_id}/title','semantic'),
 ('Endpoint GET /tasks/{task_id}/status yêu cầu kiểm tra lỗi nào?','op:wp:396','422','mixed'),
 ('Tài liệu nào yêu cầu chống gửi form hai lần và tránh response cũ ghi đè?','op:wp:382','double submit protection','semantic'),
 ('Để tìm kiếm chữ Unicode, SQLite đăng ký hàm gì?','op:wp:383','qldapm_casefold','semantic'),
 ('Tài liệu bổ sung route sức khỏe trả status ok nằm ở đâu?','op:wp:384','GET /healthz','semantic'),
 ('Trong yêu cầu #398, được sửa mã ứng dụng hay chỉ thêm regression tests?','actor:20:wp:398','khong sua code ung dung','citation'),
 ('Nguồn nào mô tả count với hai bộ lọc áp dụng đồng thời?','op:wp:394','logic AND','semantic'),
]:add(q,6,[source],[fact],group,partition='calibration' if len(rows) in [16,17,18] else 'holdout')
add('So sánh API lấy title với API chỉ đọc status theo tài liệu',6,['op:wp:390','op:wp:396'],['GET /tasks/{task_id}/title','GET /tasks/{task_id}/status'],'multi_source')
add('Có API xuất CSV và API kiểm tra sự tồn tại của việc không?',6,['op:wp:391','op:wp:389'],['GET /tasks/export.csv','GET /tasks/{task_id}/exists'],'multi_source')
for q,p in [('Tổng thống sao Hỏa uống cà phê giá bao nhiêu?',6),('Mật khẩu ngân hàng của chủ dự án là gì?',5),('Dự án dùng máy phản ứng hạt nhân loại nào?',6),('Hợp đồng WF01 của Project5 có được tiết lộ trong Project6 không?',6)]:
    add(q,p,group='no_answer' if 'WF01' not in q else 'wrong_project',behavior='abstain',partition='calibration' if len(rows)==30 else 'holdout')
for q in ['Task #398 hiện đang RUNNING hay đã DONE?','Agent nào hiện đang chạy trong dự án?','Task #398 đã được Owner nghiệm thu chưa?']:
    add(q,6,group='historical_vs_live',behavior='runtime_tool')
add('ORBIT-RECEIPT-20261103',6,['file:project6-integration-qualification'],['ORBIT-RECEIPT-20261103'],'exact')
add('Tài liệu WF01 có chứng minh Owner đã nghiệm thu không?',6,['file:project6-integration-qualification'],['does not certify semantic retrieval quality or Owner acceptance'],'historical')
add('Tìm knowledge của Project6',6,group='unauthorized',behavior='deny',actor=999999)
assert len(rows)==40,len(rows)
out={'source':'Actual MAIN authorized Native snapshots + currently registered file source contents; synthetic adversarial questions have no invented positive source','source_pins':{k:{'project':d.get('project_id',d.get('project')),'document_id':d.get('source_hash')} for k,d in documents.items() if any(k in r['expected_source_ids'] for r in rows)},'cases':rows}
(OUT/'gold.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('GOLD',len(rows),'calibration',sum(r['partition']=='calibration' for r in rows))

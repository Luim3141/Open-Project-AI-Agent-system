"""Freeze source-grounded fresh reranker queries before seeing any reranker score."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path

ROOT=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
source=json.loads((ROOT/'source-snapshot.json').read_text(encoding='utf-8'))
docs={json.loads(d['metadata'])['native_id']:d for d in source['documents']}
dev=[
 (383,'casefold','Unicode case-insensitive','Tìm kiếm task không bỏ sót ký tự ß và Đ khi đổi chữ hoa','Task search must handle ß and Đ when changing letter case'),
 (383,'sql-anchor','qldapm_casefold','Hàm SQLite qldapm_casefold giải quyết hạn chế lower như thế nào','What limitation of SQLite lower is addressed by qldapm_casefold'),
 (383,'percent','escape','Dữ liệu tìm kiếm có ký tự % và _ phải được escape trước LIKE','Search text with percent and underscore must be escaped before LIKE'),
 (383,'mixed','str.casefold','Cho tôi spec Unicode search kết hợp status filter AND','Find the specification combining Unicode search with the status filter using AND'),
 (384,'health-contract','GET /healthz','Muốn endpoint báo app mini-task-manager version 1.0.0 và status ok','Find the endpoint reporting app mini-task-manager version 1.0.0 and status ok'),
 (384,'health-route','GET /healthz','Đọc yêu cầu test cho route GET /healthz trả JSON','Read the test requirement for the GET /healthz JSON response'),
 (384,'health-exact','GET /healthz','GET /healthz version status ok','healthz mini-task-manager version 1.0.0'),
 (384,'health-long','GET /healthz','Tôi chỉ cần tìm yêu cầu route sức khỏe ứng dụng để giám sát mà không tạo sửa hay xóa task','Locate the application health route requirement used for monitoring without creating editing or deleting tasks'),
 (386,'counts','active','Đếm số task todo và in_progress trong active của summary','Count todo and in_progress tasks as active in the summary'),
 (386,'sum','total == active + completed','Yêu cầu bất biến tổng số công việc bằng active cộng completed','Find the invariant that the total task count equals active plus completed'),
 (386,'empty-summary','database chưa có dữ liệu','Nếu bảng tasks trống, summary phải trả ba trường bằng không','If the tasks table is empty the summary must return all three counts as zero'),
 (386,'summary-exact','GET /tasks/summary','GET /tasks/summary active todo in_progress done','Which summary endpoint groups todo in_progress and done task counts'),
]
holdout=[
 (387,'detail-fields','id, title, status','Lấy chi tiết một task qua ID và nhận đủ id title status trong JSON','Fetch one task by its ID and return id title and status in JSON'),
 (387,'detail-missing','HTTP 404','Yêu cầu GET chi tiết công việc trả 404 khi không có ID trong SQLite','Find the requirement that getting a missing task detail returns 404'),
 (387,'detail-invalid','HTTP 422','Route lấy thông tin task kiểm tra ID chữ cái và phản hồi 422','The single-task detail route rejects alphabetic identifiers with 422'),
 (387,'detail-negative','so am','Với route chi tiết task, ID âm không tồn tại phải trả lỗi gì','What error does the task detail route return for a nonexistent negative ID'),
 (387,'detail-exact','GET /tasks/{task_id}','GET /tasks/{task_id} id title status','GET /tasks/{task_id} JSON id title status'),
 (387,'detail-preserve','Khong thay doi schema','Bổ sung truy xuất task theo ID nhưng không đổi schema SQLite','Add task lookup by ID while keeping the SQLite schema unchanged'),
 (389,'exists-true','nếu task tồn tại','Kiểm tra task tồn tại theo ID và chỉ lấy cờ exists true','Check task existence by identifier and return only the exists true flag'),
 (389,'exists-false','nếu task không tồn tại','Task không tồn tại nhưng API existence phải trả HTTP 200 exists false','A missing task must still receive HTTP 200 and exists false from the existence API'),
 (389,'exists-invalid','HTTP 422','ID không nguyên trong route exists bị validation lỗi 422','A noninteger identifier on the exists route fails validation with 422'),
 (389,'exists-empty','SQLite trống','Spec API kiểm tra tồn tại khi cơ sở dữ liệu SQLite chưa có task','Find the existence API specification for an empty SQLite task database'),
 (389,'exists-exact','GET /tasks/{task_id}/exists','GET /tasks/{task_id}/exists 200 true false','GET /tasks/{task_id}/exists integer ID true false'),
 (389,'exists-preserve','Không thay đổi schema','Thêm exists endpoint nhưng giữ nguyên GET detail summary healthz và schema','Add the exists endpoint while preserving detail summary healthz and the schema'),
 (390,'title-payload','JSON gồm id và title','Route chỉ lấy tiêu đề task trả hai trường id và title','Find the route returning only task id and title'),
 (390,'title-unicode','Unicode','Phản hồi API title phải giữ nguyên tiếng Việt và emoji của tiêu đề','The task title API response must preserve Vietnamese characters and emoji'),
 (390,'title-missing','HTTP 404','Spec route title trả 404 nếu không tìm thấy công việc','Find the title route specification returning 404 when the task is missing'),
 (390,'title-invalid','HTTP 422','Route đọc title từ chối ID không nguyên bằng HTTP 422','The title-reading route rejects noninteger IDs with HTTP 422'),
 (390,'title-exact','GET /tasks/{task_id}/title','GET /tasks/{task_id}/title Unicode id title','GET /tasks/{task_id}/title Unicode JSON payload'),
 (390,'title-regression','/exists','Thêm API title nhưng không làm hỏng route exists và summary cũ','Add the title API while retaining existing exists and summary behavior'),
]
# More than minimum holdout positives are intentional; entire new primary source groups stay holdout.
negative_dev=[
 ('kanban','Kéo thả thẻ task giữa các cột Kanban bằng drag and drop','Drag task cards between Kanban columns'),
 ('websocket','Đẩy cập nhật task theo WebSocket thời gian thực','Push real time task updates through WebSocket'),
 ('encrypt','Mã hóa từng title của task khi lưu SQLite','Encrypt each task title inside SQLite'),
 ('dependency','Ngăn hoàn thành task nếu task phụ thuộc chưa xong','Prevent task completion until its dependencies finish'),
 ('subtasks','Tạo cây công việc con nhiều cấp','Create a hierarchical tree of nested subtasks'),
 ('audit-user','Ghi lịch sử người dùng đã chỉnh sửa từng trường task','Audit which user modified each task field'),
 ('offline','Đồng bộ task offline khi điện thoại có mạng trở lại','Synchronize offline tasks after a phone reconnects'),
 ('geo','Lọc task theo khoảng cách địa lý gần người dùng','Filter tasks by geographic distance from the user'),
 ('sla','Tính SLA tự động theo giờ làm việc của từng khách hàng','Calculate task SLA using each customer working hours'),
 ('signature','Yêu cầu ký điện tử trước khi hoàn thành công việc','Require an electronic signature before completing a task'),
]
negative_holdout=[
 ('title-history','API trả toàn bộ các phiên bản title trước đây của task','Return all previous task title versions through an API'),
 ('bulk-exists','Kiểm tra tồn tại hàng ngàn ID trong một request bulk exists','Check thousands of task IDs in a single bulk existence request'),
 ('archived-detail','Truy xuất chi tiết task đã xóa từ thùng rác','Retrieve deleted task details from a recycle bin'),
 ('title-translate','Dịch tiêu đề task tự động sang tiếng Nhật trong title API','Automatically translate task titles into Japanese in the title API'),
 ('exists-permission','Ẩn cờ tồn tại task theo quyền truy cập của từng user','Hide task existence based on per-user access permissions'),
 ('detail-comments','API chi tiết task trả toàn bộ file đính kèm và bình luận','The task detail API returns all attachments and discussion comments'),
 ('title-fuzzy','Tìm title gần đúng với sai chính tả bằng khoảng cách Levenshtein','Find misspelled task titles using Levenshtein distance'),
 ('detail-pagination','Phân trang các bản ghi lịch sử thay đổi của một task','Paginate the change history records of an individual task'),
 ('title-unique','Ngăn hai task dùng cùng title bằng unique constraint','Prevent two tasks from sharing a title using a unique constraint'),
 ('exists-cache','Cache kết quả exists bằng Redis cùng thời hạn TTL','Cache task existence results in Redis with a TTL'),
]
cases=[]
for split,positives,negatives in [('dev',dev,negative_dev),('holdout',holdout,negative_holdout)]:
    for native,intent,evidence,vi,en in positives:
        d=docs[native]
        assert evidence.casefold() in d['content'].casefold(),(native,intent,evidence)
        index=d['content'].casefold().index(evidence.casefold());support=d['content'][max(0,index-40):index+len(evidence)+80]
        support_chunks=[{'chunk_index':c['chunk_index'],'chunk_hash':c['chunk_hash']} for c in source['chunks'] if c['document_id']==d['source_hash'] and evidence.casefold() in c['chunk_text'].casefold()]
        assert support_chunks,(native,intent)
        for lang,q in [('vi',vi),('en',en)]:
            cases.append({'split':split,'kind':'positive','intent':f'{native}:{intent}','language':lang,'query':q,
                'relevant_ids':[native],'partial_ids':[379] if native!=379 else [],
                'source_hash':d['source_hash'],'evidence_literal':evidence,'evidence_excerpt':support,'supporting_chunks':support_chunks,
                'judgment':'Agent full-content judgment: source describes requested requirement; parent may be partial; not a claim that behavior is deployed.','human_review':'PENDING'})
    for intent,vi,en in negatives:
        for lang,q in [('vi',vi),('en',en)]:cases.append({'split':split,'kind':'negative','intent':intent,'language':lang,'query':q,
            'relevant_ids':[],'partial_ids':[],'judgment':'Agent review: none of the ten allowed source contents specifies this requested extra capability; adjacent CRUD/route text is insufficient.','human_review':'PENDING'})
target=ROOT/'labels-frozen.json';assert not target.exists()
data={'created_utc':datetime.now(timezone.utc).isoformat(),'snapshot_sha256':hashlib.sha256((ROOT/'source-snapshot.json').read_bytes()).hexdigest(),
    'scope':{'project':'6','actor':20,'role':'PM'},'label_author':'same source-reading agent; human PENDING',
    'split':'Primary source groups383/384/386 development; new groups387/389/390 holdout; holdout never scored on any reranker before freeze',
    'limits':'Few documents, paired languages/intents correlated; not independent human validation. Previously consumed passage holdout excluded from selection.',
    'cases':cases}
target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'created_utc':data['created_utc'],'counts':{s:{k:sum(c['split']==s and c['kind']==k for c in cases) for k in ['positive','negative']} for s in ['dev','holdout']}},indent=2))

"""Independently authored source-grounded cases; never score holdout before lock."""
import hashlib,json,datetime,re
from pathlib import Path

root=Path(__file__).resolve().parent.parent
source=json.loads((root/'native-source-manifest.json').read_text(encoding='utf-8'))
docs={d['metadata']['native_id']:d for d in source['documents']}
texts={i:(root/'private'/d['snapshot_file']).read_text(encoding='utf-8') for i,d in docs.items()}
dev_ids={380,381,388,389,390,391};holdout_ids={379,382,383,384,386,387}
assert dev_ids.isdisjoint(holdout_ids) and dev_ids|holdout_ids==set(docs)

# Each support phrase is literal text in a current source, not a generated answer.
dev=[
 (380,'create_list','Create/list tasks + SQLite persistence',
  'Tìm unit đầu tiên phụ trách tạo và liệt kê việc có lưu bằng SQLite.',
  'Which initial engineering unit creates and lists persisted tasks using SQLite?'),
 (380,'preserved_failure','terminal_failure_preserved',
  'Bằng chứng nào cho biết unit create/list đã giữ lại lỗi kết thúc cũ khi dùng partial artifact?',
  'Which create/list delivery retains its previous terminal failure alongside a verified partial artifact?'),
 (381,'crud_unit','Edit/delete/status/search and usable web interface',
  'Unit nào mở rộng chỉnh sửa, xoá, trạng thái và tìm kiếm trong giao diện web?',
  'Which delivery adds editing, deletion, status changes, search and a web interface?'),
 (381,'parent_review','WP379 awaits review/UAT',
  'Khi unit giao diện CRUD được xác minh, WP cha còn chờ bước nào?',
  'After the CRUD interface unit was verified, what remained pending for the parent work package?'),
 (388,'recovery_history','not restoration of Native history',
  'Bản thay thế WP385 có khôi phục lại lịch sử Native của bản bị xoá không?',
  'Does the replacement of WP385 restore the deleted Native history?'),
 (388,'dependency','Dependency: health-check-v1 / WP384',
  'Hạng mục thay thế WP385 phụ thuộc vào health-check nào?',
  'Which health-check work package is a dependency of the WP385 replacement?'),
 (389,'exists_noninteger','task_id không phải số nguyên trả về HTTP 422',
  'Tài liệu kiểm tra tồn tại việc quy định gì khi task_id không phải số nguyên?',
  'What response is specified when the task existence endpoint receives a noninteger task_id?'),
 (389,'exists_false','exists\\\": false',
  'Tìm yêu cầu existence endpoint trả giá trị false cho một ID không có trong SQLite.',
  'Find the existence check specification for an ID absent from SQLite, including the false result.'),
 (390,'title_unicode','Tiêu đề chứa ký tự Unicode được bảo toàn chính xác',
  'Tài liệu nào yêu cầu phản hồi title giữ đúng ký tự Unicode?',
  'Which title endpoint specification preserves Unicode characters in the response?'),
 (390,'title_invalid','task_id không phải số nguyên trả về HTTP 422',
  'Endpoint lấy title xử lý task_id dạng chữ như thế nào?',
  'How must the title-only endpoint handle an alphabetic task identifier?'),
 (391,'csv_delivery_base','codex/openclaw-feedback-9d0ff35386a63183',
  'Unit CSV ghi nhận base branch nào cho delivery?',
  'What base branch is recorded in the CSV delivery receipt?'),
 (391,'csv_delivery_review','"verdict": "PASS"',
  'Nguồn nào lưu kết quả review PASS cho unit export.csv?',
  'Find the persisted reviewer verdict for the export.csv engineering unit.'),
]

# Fresh wording and intent families are chosen independently; these are never used during dev tuning.
holdout=[
 (379,'stack','Backend: Python FastAPI','Backend của mục tiêu tổng thể dùng công nghệ gì?','Which backend technology is named in the overall project objective?'),
 (379,'planning_order','Establish dependencies and propose a development schedule','Kế hoạch tổng thể yêu cầu xác định phụ thuộc và đề xuất lịch ở giai đoạn nào?','Which overall project document asks the AI team to identify dependencies and propose a development schedule?'),
 (382,'aria_alert','aria-live và role=alert','Tài liệu yêu cầu thông báo lỗi có thuộc tính hỗ trợ screen reader nào?','Which UI requirement names aria-live together with role=alert for error messages?'),
 (382,'restore_controls','tự khôi phục controls khi xảy ra lỗi','Sau lỗi gửi form, yêu cầu UI nói gì về controls?','After a form submission error, which UI requirement restores the controls?'),
 (382,'validation_array','mảng chi tiết lỗi validation phức tạp','Client phải xử lý dạng dữ liệu validation phức tạp nào từ FastAPI?','What complex validation detail structure must the client handle from FastAPI?'),
 (382,'stale','response cũ, chỉ nhận response mới nhất','Khi các request tìm kiếm trả sai thứ tự, UI cần ưu tiên phản hồi nào?','Which UI requirement discards an older search response when requests resolve out of order?'),
 (383,'escape_like','%, _, backslash được escape','Tài liệu tìm kiếm Unicode xử lý các ký tự wildcard SQL nào trước khi thêm ký tự đại diện?','Before adding wildcard characters, which SQL LIKE characters must the Unicode search escape?'),
 (383,'and_filter','bộ lọc trạng thái (status) theo logic AND','Khi kết hợp tìm kiếm Unicode và lọc trạng thái, logic kết hợp được chỉ định là gì?','Which logical operator combines Unicode text search with the status filter?'),
 (383,'frontend_boundary','Không thay đổi giao diện HTML/frontend','Giới hạn nào của thay đổi casefold cấm đụng giao diện frontend?','Which casefold work package explicitly excludes frontend changes?'),
 (383,'casefold_db','hàm SQLite tùy chỉnh qldapm_casefold sử dụng str.casefold','Tìm chức năng SQL tự định nghĩa để chuẩn hoá chữ hoa thường Unicode theo Python.','Which custom SQLite function uses Python casefold for Unicode-insensitive matching?'),
 (384,'health_payload',"status: 'ok', app: 'mini-task-manager', version: '1.0.0'",'Health endpoint của demo trả app name và phiên bản theo yêu cầu nào?','Which health requirement includes the application name and version in its JSON?'),
 (384,'health_test','unit test trong test_crud_web.py','Test file nào được nêu cùng yêu cầu GET /healthz?','Which test file is named alongside the GET /healthz requirement?'),
 (386,'active_definition',"('todo', 'in_progress')",'Bộ đếm active của summary tính hai trạng thái tác vụ nào?','Which two task statuses count as active in the summary?'),
 (386,'total_relation','total == active + completed','Nguồn nào quy định tổng số phải bằng số active cộng completed?','Which specification requires total to equal active plus completed?'),
 (386,'summary_no_filter','không hỗ trợ các tham số bộ lọc phức tạp','Hạn chế nào của endpoint summary nói về lọc nâng cao?','Which summary-endpoint limitation rules out complex filters?'),
 (387,'detail_noninteger','task_id khong phai la so hop le','Tài liệu chi tiết task yêu cầu lỗi HTTP nào nếu ID không phải số hợp lệ?','For the detail endpoint, what HTTP error is specified for a nonnumeric task ID?'),
 (387,'detail_negative','so am hoac qua lon khong co trong CSDL tra ve ma loi 404','Tài liệu chi tiết task xử lý ID âm hoặc quá lớn không có trong database thế nào?','What status does the detail specification give to an absent negative or oversized ID?'),
 (387,'detail_db_boundary','Khong thay doi schema co so du lieu SQLite','Hạng mục task detail giới hạn thay đổi schema SQLite như thế nào?','Does the task detail work package permit a SQLite schema change?'),
 (382,'loading_retry','trạng thái loading, empty và có nút retry','Requirement nào yêu cầu loading, empty state và thao tác retry trong UI?','Which UI work package requires loading, empty and retry states?'),
 (379,'test_stack','Testing: pytest','Framework kiểm thử nào được ghi trong technology stack của dự án?','Which automated testing framework is named in the project technology stack?'),
]

# Negatives require the exact distinctive capability to be absent in the entire frozen corpus.
dev_neg=[
 ('mysql','mysql','Ứng dụng task có lưu dữ liệu vào MySQL thay cho SQLite không?','Does the task application persist records in MySQL instead of SQLite?'),
 ('pagination','page_size','API task có hỗ trợ page_size để chia trang không?','Does the task list API implement a page_size parameter?'),
 ('grpc','grpc','Tài liệu nào mô tả truy vấn task qua gRPC?','Which document describes querying tasks through gRPC?'),
 ('jwt','jwt','Ứng dụng task phát JWT để phân quyền từng endpoint ở đâu?','Where does the task application issue JWT credentials for its endpoints?'),
 ('cache','memcached','Task list được cache bằng Memcached ở đâu?','Where is the task list cached using Memcached?'),
 ('subtasks','parent_id','API tạo việc có trường parent_id để tạo subtask không?','Does task creation accept a parent_id for nested subtasks?'),
 ('priority_field','tasks.priority','Bảng tasks có cột tasks.priority để sắp xếp không?','Does the tasks table define tasks.priority for ordering?'),
 ('ical','calendar sync','Lịch công việc được đồng bộ qua calendar sync như thế nào?','How does the application implement calendar sync for tasks?'),
 ('openid','openid','Có đăng nhập OpenID cho ứng dụng task không?','Does the task application implement OpenID login?'),
 ('s3','s3 bucket','File task được lưu trong S3 bucket nào?','Which S3 bucket stores task files?'),
]
holdout_neg=[
 ('bulk','/tasks/bulk','Có endpoint /tasks/bulk để cập nhật hàng loạt không?','Is /tasks/bulk available to update multiple tasks at once?'),
 ('attachments','multipart/form-data','Giao diện task tải tệp đính kèm bằng multipart/form-data ở đâu?','Where does the task UI upload attachments using multipart/form-data?'),
 ('graphql','graphql','Có GraphQL API cho việc đọc danh sách task không?','Does a GraphQL API serve the task list?'),
 ('websocket','websocket','Có WebSocket đẩy trạng thái task theo thời gian thực không?','Does the app push task status updates over WebSocket?'),
 ('postgres','postgresql','Yêu cầu nào chuyển lưu trữ task sang PostgreSQL?','Which requirement moves task storage to PostgreSQL?'),
 ('deadline','deadline','Có filter task theo deadline không?','Does the task API provide a deadline filter?'),
 ('tags','tag_ids','API task có nhận tag_ids để lọc nhiều nhãn không?','Does the task API filter using tag_ids?'),
 ('saml','saml','Màn hình task hỗ trợ SAML đăng nhập một lần ở đâu?','Where does the task UI support SAML single sign-on?'),
 ('kafka','kafka','Ứng dụng phát sự kiện task lên Kafka topic nào?','Which Kafka topic receives task events?'),
 ('etag','etag','Endpoint sửa task sử dụng ETag để chống ghi đè ở đâu?','Where does task editing use an ETag for concurrency control?'),
]

mixed={
 'dev':[
  (388,'mixed-dependency','Dependency: health-check-v1 / WP384','Replacement WP385 có dependency tới health-check work package nào?'),
  (389,'mixed-exists-type','task_id không phải số nguyên trả về HTTP 422','Với exists endpoint, non-integer task_id phải trả HTTP code nào?'),
  (390,'mixed-title-unicode','Tiêu đề chứa ký tự Unicode được bảo toàn chính xác','Title response phải giữ Unicode characters trong task name như thế nào?')],
 'holdout':[
  (382,'mixed-control','tự khôi phục controls khi xảy ra lỗi','Sau submit error, form controls được recover như thế nào?'),
  (383,'mixed-and','bộ lọc trạng thái (status) theo logic AND','Kết hợp Unicode query với status filter dùng logical operator gì?'),
  (387,'mixed-id','task_id khong phai la so hop le','Request task detail với non-numeric ID nhận HTTP status gì?')],
}
mixed_neg={
 'dev':[('mixed-s3','s3 bucket','Task files lưu ở S3 bucket nào?'),('mixed-pages','page_size','Task list có page_size để pagination không?')],
 'holdout':[('mixed-bulk','/tasks/bulk','Có bulk update qua /tasks/bulk endpoint không?'),('mixed-tags','tag_ids','Task filter có nhận tag_ids để chọn nhiều labels không?')],
}

def positives(split,rows,allowed):
 out=[]
 for native,intent,literal,vi,en in rows:
  assert native in allowed and native in docs
  found=re.search(re.escape(literal),texts[native],re.IGNORECASE)
  if not found:raise ValueError('SUPPORT_NOT_FOUND:'+split+':'+intent)
  at=found.start();actual=found.group();assert actual.casefold()==literal.casefold()
  for lang,query in [('vi',vi),('en',en)]:
   out.append({'id':split+':'+intent+':'+lang,'split':split,'kind':'positive','language':lang,'query':query,
    'relevant_ids':[native],'source_id':docs[native]['source_id'],'source_hash':docs[native]['source_hash'],
    'source_version':docs[native]['metadata']['lock_version'],'support_literal':actual,'support_offset':at,
    'support_sha256':hashlib.sha256(actual.encode()).hexdigest(),'judgment':'Frozen source supports this requirement or historical receipt; not a live deployment claim.'})
 return out

def negatives(split,rows):
 out=[]
 for intent,anchor,vi,en in rows:
  assert all(anchor.casefold() not in t.casefold() for t in texts.values()),'NEGATIVE_ANCHOR_PRESENT:'+split+':'+intent
  for lang,query in [('vi',vi),('en',en)]:
   out.append({'id':split+':'+intent+':'+lang,'split':split,'kind':'negative','language':lang,'query':query,
    'relevant_ids':[],'absent_anchor':anchor,'judgment':'Capability is absent from frozen Project6 actor20 Native sources; lexical absence supports but does not independently prove semantic absence.'})
 return out

for split,rows,neg,allowed in [('dev',dev,dev_neg,dev_ids),('holdout',holdout,holdout_neg,holdout_ids)]:
 cases=positives(split,rows,allowed)+negatives(split,neg)
 for native,intent,literal,query in mixed[split]:
  assert native in allowed
  match=re.search(re.escape(literal),texts[native],re.IGNORECASE);assert match,'MIXED_SUPPORT_NOT_FOUND:'+intent
  actual=match.group()
  cases.append({'id':split+':'+intent,'split':split,'kind':'positive','language':'mixed','query':query,
   'relevant_ids':[native],'source_id':docs[native]['source_id'],'source_hash':docs[native]['source_hash'],
   'source_version':docs[native]['metadata']['lock_version'],'support_literal':actual,'support_offset':match.start(),
   'support_sha256':hashlib.sha256(actual.encode()).hexdigest(),'judgment':'Frozen source supports this requirement, not a live deployment claim.'})
 for intent,anchor,query in mixed_neg[split]:
  assert all(anchor.casefold() not in t.casefold() for t in texts.values()),'MIXED_NEGATIVE_ANCHOR_PRESENT:'+intent
  cases.append({'id':split+':'+intent,'split':split,'kind':'negative','language':'mixed','query':query,
   'relevant_ids':[],'absent_anchor':anchor,'judgment':'No exact distinctive capability anchor in frozen corpus; semantic absence needs independent review.'})
 target=root/('dev.json' if split=='dev' else 'private/holdout.json')
 content=json.dumps({'schema':1,'split':split,'cases':cases},ensure_ascii=False,indent=2)+'\n'
 if target.exists():assert target.read_text(encoding='utf-8')==content
 else:target.write_text(content,encoding='utf-8')
 print(json.dumps({'split':split,'positive':sum(c['kind']=='positive' for c in cases),'negative':sum(c['kind']=='negative' for c in cases),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))

plan={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'author':'independent evaluation agent separate from implementation agent; HUMAN_REVIEW_PENDING',
 'independence':'No previously locked holdout cases or labels intentionally reused. Source documents overlap past experiments because the live Native corpus is only 12 work packages; new wording may share underlying features. No human adjudication or population sampling.',
 'source_manifest_sha256':hashlib.sha256((root/'native-source-manifest.json').read_bytes()).hexdigest(),
 'dev_sha256':hashlib.sha256((root/'dev.json').read_bytes()).hexdigest(),'holdout_sha256':hashlib.sha256((root/'private/holdout.json').read_bytes()).hexdigest(),
 'source_splits':{'dev':sorted(dev_ids),'holdout':sorted(holdout_ids)},
 'acceptance':{'holdout_hit_at_5_min':.8,'holdout_false_positive_rate_max':.05,'citation_identity_errors_max':0,'acl_errors_max':0,'warm_query_p95_seconds_max':5},
 'holdout_policy':'Do not open, embed, score or calibrate on holdout until candidate source and parameters are frozen. Inspect labels independently after lock and before scoring; preserve original labels and flag ambiguity.',
 'scope':'PM actor20, Project6 native snapshots; local file corpus requires separate ACL/citation evaluation.'}
(root/'evaluation-plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')

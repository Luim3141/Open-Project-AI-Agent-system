"""Freeze new demo query split before retrieval/scoring; Native391/388 intents never used by prior experiments."""
import datetime,hashlib,json,os,sqlite3
from pathlib import Path

OUT=Path(__file__).parent
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/demo-final-rag'
db=sqlite3.connect((PRIVATE/'knowledge.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
docs={json.loads(r['metadata']).get('native_id'):dict(r) for r in db.execute("SELECT * FROM knowledge_documents WHERE project_id='6' AND json_extract(metadata,'$.actor_id')=20")}
dev=[
 (383,'casefold','str.casefold','Làm sao tìm tên việc mà không phân biệt hoa thường của chữ quốc tế?','How can searching a task title ignore case for international characters?'),
 (383,'sharp-s','str.casefold','Tên chứa chữ ß cần được so sánh thế nào khi người dùng gõ SS?','How should a title with the sharp s character compare with a query containing SS?'),
 (383,'sql-like','LIKE','Hàm SQLite nào giúp tra cứu tiêu đề tiếng Việt đúng chữ hoa chữ thường?','What SQLite function makes case insensitive task search work for non ASCII text?'),
 (383,'special-search','LIKE','Tôi muốn xem yêu cầu tìm kiếm khi từ khóa chứa ký hiệu đặc biệt của LIKE','Find the requirements for treating LIKE wildcard characters as literal task search text'),
 (384,'readiness','healthz','Tôi nên gọi chỗ nào để biết ứng dụng công việc còn sống?','Which endpoint tells me whether the task application is alive?'),
 (384,'health-body','status','Phản hồi kiểm tra sức khỏe của app có trạng thái và phiên bản gì?','What status and version does the app health response contain?'),
 (384,'health-route','/healthz','Cho tôi tài liệu về GET /healthz trong ứng dụng demo','Find the demo application requirements for GET /healthz'),
 (384,'health-nonmutating','healthz','Làm sao kiểm tra app mà không tạo hay sửa công việc?','How do I check app health without creating or modifying tasks?'),
 (386,'counts','total','Tìm chức năng thống kê bao nhiêu việc đang làm và bao nhiêu việc hoàn tất','Find the feature that counts unfinished and finished tasks'),
 (386,'summary-fields','completed','Số liệu tổng hợp công việc trả những bộ đếm nào?','Which counters does the task summary response expose?'),
 (386,'summary-invariant','active','Mối quan hệ giữa tổng số việc và số việc đang làm, đã xong là gì?','How does the total task count relate to active and completed counts?'),
 (386,'summary-empty','SQLite','Cơ sở dữ liệu chưa có việc nào thì số liệu tổng hợp như thế nào?','What counts should the summary return when the database has no task records?'),
]
holdout=[
 (388,'category-create','category on task POST/PATCH','Tìm yêu cầu gắn nhóm phân loại khi tạo hoặc sửa một công việc','Find the requirement for assigning a category when a task is created or changed'),
 (388,'category-filter','category=','Có yêu cầu lọc danh sách công việc theo nhóm phân loại không?','Where is the requirement to filter the task list by category?'),
 (388,'recovered-scope','AC10','Phần khôi phục công việc bị xóa bao gồm category và xuất bảng dữ liệu nào?','Which recovered work item covers task categories filtering and CSV export?'),
 (391,'csv-download','Content-Disposition','Tôi muốn tải danh sách việc về thành tệp để phần mềm bảng tính đọc được','I want to download the task list as a file readable by spreadsheet software'),
 (391,'csv-columns','id,title,status','Tệp xuất danh sách công việc có những cột dữ liệu nào?','Which columns are included in the exported task list file?'),
 (391,'csv-order','id tăng dần','Dữ liệu công việc trong tệp tải xuống được sắp xếp theo thứ tự gì?','In what order are task records written into the download file?'),
 (391,'csv-filter','q và status','Khi xuất bảng CSV có thể chọn theo nội dung tiêu đề và tiến độ không?','Can the CSV download be filtered by title text and task progress?'),
 (391,'csv-escaping','dấu phẩy','Tên việc có dấu phẩy, dấu nháy hoặc nhiều dòng thì xuất ra tệp thế nào?','How does the file export handle titles with commas quotes and line breaks?'),
 (391,'csv-empty','dòng tiêu đề','Danh sách việc rỗng thì tệp CSV còn có dòng tên cột không?','Does an empty task list still produce a CSV header row?'),
 (391,'csv-routing','route tĩnh','Làm sao để URL tải CSV không bị coi nhầm là mã công việc?','How is the CSV download URL prevented from being mistaken for a task ID?'),
]
negative_dev=[
 ('oauth-github','Đăng nhập ứng dụng bằng tài khoản GitHub được cấu hình ở đâu?','Where is GitHub account login configured for the application?'),
 ('images','Làm sao chụp ảnh từ camera rồi gắn vào công việc?','How do I capture a camera photo and attach it to a task?'),
 ('location-map','Có thể xem đường đi của người nhận việc trên bản đồ không?','Can the route of a task assignee be displayed on a map?'),
 ('stock','Hệ thống giảm số lượng tồn kho khi hoàn tất việc như thế nào?','How does completing a task reduce warehouse stock?'),
 ('bank','Tôi tìm thao tác chuyển khoản ngân hàng từ ứng dụng','Find the bank transfer action in this application'),
 ('language-auto','Làm sao tự dịch mọi tiêu đề task sang tiếng Nhật?','How can every task title be automatically translated into Japanese?'),
 ('transcription','Có thể chuyển lời nói trong cuộc họp thành task tự động không?','Can speech from meetings be transcribed into tasks automatically?'),
 ('encryption-field','Tìm cấu hình mã hóa riêng cột tiêu đề trong SQLite bằng AES','Find AES encryption configuration for the SQLite title column'),
 ('audit-sign','Tìm chữ ký số xác minh từng dòng thống kê task','Find digital signatures verifying each task statistics row'),
 ('availability-region','Cấu hình chạy ứng dụng đa vùng để tự failover như thế nào?','How is multiregion automatic failover configured for this application?'),
]
negative_holdout=[
 ('xlsx','Có endpoint xuất công việc thành tệp XLSX không?','Is there an endpoint to export tasks to an XLSX workbook?'),
 ('tsv','Tôi muốn xuất danh sách việc định dạng TSV thay CSV','I want a TSV task download instead of CSV'),
 ('ndjson','Xuất từng task thành dòng NDJSON bằng cách nào?','How can tasks be exported as NDJSON records?'),
 ('csv-due-date','Tệp CSV có cột due_date của từng việc không?','Does the CSV file include a due_date column for each task?'),
 ('csv-assignee','CSV có cột assignee_email và tên người thực hiện không?','Does the CSV contain an assignee_email column and the performer name?'),
 ('csv-compress','Có thể nhận dữ liệu CSV được nén gzip ngay từ endpoint không?','Can the endpoint return gzip compressed CSV data?'),
 ('category-tree','Có thể chia category thành cây phân loại nhiều tầng không?','Can categories be organized into a multilevel hierarchy?'),
 ('csv-date-range','Lọc bản CSV theo created_after và created_before ở đâu?','Where are created_after and created_before filters supported by CSV export?'),
 ('csv-password','Có thể đặt mật khẩu cho tệp CSV được tải về không?','Can the downloaded CSV file be protected with a password?'),
 ('csv-signature','Có tính năng gắn chữ ký điện tử vào bản CSV xuất ra không?','Can the exported CSV have an electronic signature attached?'),
]
cases=[]
for split,rows,negatives in [('dev',dev,negative_dev),('holdout',holdout,negative_holdout)]:
 for native,intent,evidence,vi,en in rows:
  doc=docs[native]
  assert evidence.casefold() in doc['content'].casefold(),(native,evidence)
  for lang,query in [('vi',vi),('en',en)]:cases.append({'id':split+':'+intent+':'+lang,'split':split,'kind':'positive','language':lang,'query':query,'relevant_ids':[native],
   'source_hash':doc['source_hash'],'support_literal':evidence,'source_version':json.loads(doc['metadata'])['lock_version'],
   'judgment':'Requested/specification scope in the frozen Native document; not proof that the feature is implemented/deployed.'})
 for intent,vi,en in negatives:
  for lang,query in [('vi',vi),('en',en)]:cases.append({'id':split+':'+intent+':'+lang,'split':split,'kind':'negative','language':lang,'query':query,'relevant_ids':[],
   'judgment':'Requested capability absent in all twelve scoped documents; nearby generic task/CSV references do not answer it.'})
target=PRIVATE/'labels.json';assert not target.exists()
labels={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_sha256':hashlib.sha256((OUT/'source-manifest.json').read_bytes()).hexdigest(),
 'label_author':'implementing agent source-grounded review; HUMAN_REVIEW_PENDING',
 'split_policy':'Development only on prior development sources383/384/386. New holdout source388/391 has new CSV/category intents not scored in prior Native or clause experiments. New negatives not reused from prior heldout queries. Twenty paired positives and twenty negatives are small/correlated, not a representative production certification.',
 'scope':{'project':'6','actor':20,'role':'PM'},'cases':cases}
target.write_text(json.dumps(labels,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest={'created_utc':labels['created_utc'],'labels_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'counts':{s:{k:sum(c['split']==s and c['kind']==k for c in cases) for k in ['positive','negative']} for s in ['dev','holdout']},
 'acceptance':{'holdout_hit_at_5_min':.8,'holdout_false_positive_rate_max':.05,'citation_identity_errors_max':0,'acl_errors_max':0,'warm_query_p95_seconds_max':5},
 'iteration_policy':'At most two bounded development refinements, no scoring/embedding/ranking holdout until source+parameters frozen; holdout once only. No label/threshold changes after holdout.',
 'raw_queries':'Private labels.json, not printed to logs; source clauses frozen before model scoring. Author knows authored queries; evaluation not independently blinded.'}
(OUT/'evaluation-plan.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))

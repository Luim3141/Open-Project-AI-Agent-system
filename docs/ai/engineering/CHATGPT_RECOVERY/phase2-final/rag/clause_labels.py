"""Freeze full source-backed clause judgments before embeddings/model scoring."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
from clause_experiment import clauses
P=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-evidence-clauses'
m=json.loads((P/'source-manifest.json').read_text());sources={r['source_key']:r for r in m['sources']};texts={};parts={}
for key,r in sources.items():
    raw=Path(r['copy']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['raw_sha256']
    texts[key]=raw.decode('utf-8-sig');parts[key]=clauses(texts[key],Path(r['copy']).suffix.lstrip('.'))
positive=[
 ('file-contract','key','A source key never means a filesystem path','Client được gửi đường dẫn file trực tiếp thay cho source key không','Can a client supply a filesystem path instead of a registered source key'),
 ('file-contract','revision','A changed file is refused','Nếu file nguồn thay đổi bytes thì việc index lại cần kiểm tra gì','What must be checked before reindexing a file whose bytes have changed'),
 ('file-contract','pdf','15 seconds, 64 pages, 256 KiB','Giới hạn tài nguyên khi đọc PDF được nêu thế nào','What resource bounds apply when parsing a PDF document'),
 ('file-contract','pending','same ingestion key may safely repair it','Khi commit vector lỗi, có thể sửa lại bằng cùng ingestion key không','Can the same ingestion key repair a failed vector commit'),
 ('adr1','startup','mở Docker Desktop thủ công','Theo quyết định local ban đầu, người dùng khởi động hệ thống hằng ngày bằng cách nào','According to the original local decision how does a user start the system each day'),
 ('adr1','privacy','Nội dung mật/PII','Theo thiết kế được ghi nhận, dữ liệu cá nhân nhạy cảm cần điều kiện gì trước khi gửi provider','Under the documented design what is required before private personal data is sent to a provider'),
 ('adr2','owner','Một owner vận hành editor localhost','Theo ADR n8n, năm vai trò nghiệp vụ có được cấp riêng editor seats không','Under the n8n decision are separate editor seats allocated to the five business roles'),
 ('adr2','bootstrap','từ chối ghi đè một owner đã có','Owner bootstrap cần làm gì nếu đã có owner được tạo trước đó','What must owner bootstrap do when an owner already exists'),
 ('ingestion','denied-paths','Denylist cấm','Theo báo cáo ingestion cũ, những loại thư mục nhạy cảm nào bị chặn khi nạp tài liệu','According to the historical ingestion report which sensitive path types are excluded'),
 ('ingestion','embedding','không có NaN hoặc Inf','Báo cáo ingestion yêu cầu kiểm tra vector embedding trước khi lưu những gì','Which embedding validation checks are listed before storing vectors in the ingestion report'),
 ('retrieval','fusion','RRF $k=60$','Theo tài liệu retrieval cũ, thứ hạng dense và lexical được kết hợp bằng công thức nào','According to the historical retrieval document how are dense and lexical ranks combined'),
 ('retrieval','outage','fallback 100% sang SQLite FTS5','Tài liệu retrieval nói hệ thống dùng đường tìm kiếm nào khi dịch vụ vector bị offline','What search path does the retrieval document describe when vector services are offline'),
 ('demo-readme','create','non-blank title','README của revision demo yêu cầu title khi tạo task phải như thế nào','What does the demo revision README require of a title when creating a task'),
 ('demo-readme','order','stable ID order','README demo mô tả thứ tự trả về danh sách công việc thế nào','What ordering of returned tasks is described in the demo README'),
 ('adr3','library','Typed State Machine nội bộ','Theo quyết định orchestration lịch sử, giải pháp nào được chọn thay cho LangGraph','Which orchestration approach was selected instead of LangGraph in the recorded decision'),
 ('adr3','approval','trạng thái `REVIEW`','Theo thiết kế orchestration, một proposal thay đổi nghiệp vụ phải qua đâu trước khi áp dụng','Under the orchestration design what must a business mutation proposal pass through before application'),
 ('adr4','identities','Mỗi người dùng có định danh','Trong thiết kế mở rộng người dùng, những thông tin nào được cô lập cho mỗi người','Under the user expansion design what is isolated separately for every user'),
 ('adr4','fairness','round-robin','Tài liệu thiết kế mô tả cách tránh một người dùng chiếm hết quota AI như thế nào','How does the design prevent one user from monopolizing the shared AI quota'),
 ('adr4','priority','Ưu tiên lệnh tương tác','Trong thiết kế hàng đợi, tác vụ tương tác hay báo cáo tự động được ưu tiên','Which gets priority in the queue design interactive requests or automatic reports'),
 ('domain','identity','OpenProject ID và Jira key','Source ID có đồng nghĩa ID của OpenProject và key của Jira là một không','Does a source identifier mean that an OpenProject ID and Jira key are the same identity'),
 ('domain','status','53 User Story','Có thể coi toàn bộ User Story trong backlog là chức năng OpenProject đã thực hiện không','Can all user stories in the backlog be treated as already implemented OpenProject features'),
 ('tracker','independent','không đồng bộ hai chiều','Theo quy tắc tracker được lưu, deployment OpenProject có tự đồng bộ sang Jira hai chiều không','Under the recorded tracker rules does an OpenProject deployment automatically synchronize Jira bidirectionally'),
 ('tracker','unknown','Timeout giữ UNKNOWN','Theo hướng dẫn tracker, khi ghi bị timeout thì có được retry mù không','Under the tracker guidance may a timed out write be blindly retried'),
 ('triage','field','custom field single-select `Triage`','Các nhãn needs-info và ready-for-agent được lưu vào đâu theo hợp đồng triage','Where are needs-info and ready-for-agent labels stored under the triage contract'),
 ('triage','wontfix','`wontfix` không tự CANCELLED','Gán wontfix có tự hủy công việc hoặc tự duyệt trạng thái ready không','Does setting wontfix automatically cancel work or approve a ready status'),
 ('demo-api','exists','return {"exists": bool(row)}','Trong source demo revision, route kiểm tra tồn tại trả về cờ boolean từ kết quả truy vấn như thế nào','In the demo revision source how does the existence route return a boolean from the query result'),
 ('demo-api','title404','def get_task_title','Trong source demo, endpoint chỉ đọc title xử lý task không tồn tại ra sao','In the demo source how does the title-only endpoint handle a nonexistent task'),
 ('demo-api','blank','Title cannot be blank','Source tạo task từ chối title trống hoặc chỉ gồm khoảng trắng bằng lỗi nào','What error does the task creation source use for an empty or whitespace-only title'),
 ('demo-api','unicode','conn.create_function("qldapm_casefold"','Source tìm kiếm task làm thế nào để hỗ trợ so khớp không phân biệt hoa thường Unicode','How does the task search source implement Unicode case insensitive matching'),
]
negative_dev=[
 ('pdf-forms','Sau ingestion PDF có tự trích giá trị AcroForm thành field có quyền riêng không','After PDF ingestion are AcroForm values mapped into separately permissioned fields'),
 ('csv-types','WF01 tự suy luận kiểu dữ liệu từng cột CSV và sửa schema theo nó như thế nào','How does WF01 infer CSV column types and migrate the schema from them'),
 ('connector-delta','File registry đọc thay đổi từ Microsoft SharePoint bằng delta cursor như thế nào','How does the file registry read SharePoint changes using a delta cursor'),
 ('embedding-prune','BGE-M3 giảm số chiều tự động theo lượng RAM còn trống bằng thuật toán nào','What algorithm automatically reduces BGE-M3 dimensions when free RAM decreases'),
 ('hybrid-personal','Thứ hạng BM25 tự học sở thích tìm kiếm riêng của từng người dùng như thế nào','How does BM25 ranking learn an individual users search preferences'),
 ('n8n-key-ttl','ADR n8n quy định key owner tự đổi sau mỗi workflow bằng cơ chế nào','What mechanism in the n8n decision rotates the owner key after each workflow'),
 ('cold-standby','Thiết kế local tự chuyển sang máy Windows dự phòng khi máy chính lỗi như thế nào','How does the local design automatically fail over to a standby Windows host'),
 ('schema-version','README demo mô tả API thương lượng schema response theo phiên bản client như thế nào','How does the demo README specify response schema negotiation by client version'),
 ('pdf-structure','Parser PDF giữ cấu trúc bảng nhiều trang và quan hệ merged cells như thế nào','How does the PDF parser preserve multi-page table structure and merged cells'),
 ('query-typo','Retrieval sửa lỗi gõ tiếng Việt bằng từ điển tự học trước khi truy vấn như thế nào','How does retrieval repair Vietnamese spelling using a learned dictionary before searching'),
]
negative_holdout=[
 ('queue-sla','Hàng đợi bảo đảm thời gian chờ tối đa cho từng mức SLA khách hàng như thế nào','How does the queue guarantee a maximum wait for each customer SLA tier'),
 ('graph-adaptive','State machine tự thay đổi DAG dựa trên điểm chất lượng model qua các sprint như thế nào','How does the state machine adapt its DAG using model quality scores across sprints'),
 ('triage-expiry','Triage tự hết hạn needs-info rồi nhắc người được giao dựa trên thời gian thế nào','How does triage expire needs-info and remind the assignee based on elapsed time'),
 ('triage-probability','Nhãn triage có xác suất tin cậy từ bộ phân loại và audit model version ra sao','How do triage labels retain classifier confidence probabilities and model version audit'),
 ('domain-schema','Glossary tự đổi tên field API giữa hai tracker theo schema registry như thế nào','How does the glossary automatically rename API fields between trackers using a schema registry'),
 ('tracker-conflict','Hai tracker giải quyết tự động xung đột nhiều bản sửa bằng merge ba chiều ra sao','How do the trackers automatically resolve competing edits using three way merge'),
 ('task-etag','Source API kiểm tra ETag và If-None-Match để trả dữ liệu task có điều kiện ra sao','How does the API source use ETag and If-None-Match for conditional task responses'),
 ('task-range','API chia danh sách task bằng HTTP Range và Content-Range như thế nào','How does the API paginate tasks using HTTP Range and Content-Range'),
 ('task-multitenant','Source route tồn tại task phân biệt schema SQLite riêng theo tenant như thế nào','How does the task existence route select separate SQLite schemas for each tenant'),
 ('task-collation','Source tìm kiếm tự chọn collation theo ngôn ngữ người dùng như thế nào','How does task search dynamically choose a collation for the users language'),
]
cases=[]
for key,intent,literal,vi,en in positive:
    matches=[c for c in parts[key] if literal.casefold() in c['text'].casefold()]
    assert matches,(key,intent,literal)
    # All original literal-bearing spans are recorded before score inspection; semantic alternatives require review.
    for lang,q in [('vi',vi),('en',en)]:cases.append({'kind':'positive','split':sources[key]['split'],'language':lang,'intent':key+':'+intent,
        'query':q,'relevant_sources':[key],'partial_sources':[],'support_literal':literal,'supporting_spans':[{'start':c['start'],'end':c['end'],'sha256':c['sha256']} for c in matches],
        'judgment':'Agent full-source reading; asks only what the captured document/source revision states, not current runtime. Other semantic equivalent spans need independent review.','human_review':'PENDING'})
for split,bank in [('dev',negative_dev),('holdout',negative_holdout)]:
    for intent,vi,en in bank:
        for lang,q in [('vi',vi),('en',en)]:cases.append({'kind':'negative','split':split,'language':lang,'intent':intent,'query':q,'relevant_sources':[],'partial_sources':[],
            'judgment':'Agent full-corpus reading: requested specific mechanism/condition not described. Adjacent topic does not answer it; no assumption source absence proves product impossibility.','human_review':'PENDING'})
target=P/'labels-frozen.json';assert not target.exists()
data={'frozen_utc':datetime.now(timezone.utc).isoformat(),'source_manifest_sha256':hashlib.sha256((P/'source-manifest.json').read_bytes()).hexdigest(),
    'label_author':'same agent; humanPENDING; not independent validation','scope':'Repo-file corpus only; no Native recall acceptance',
    'cases':cases}
target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'clauses-frozen.json').write_text(json.dumps(parts,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'labels_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'utc':data['frozen_utc'],
    'counts':{s:{k:sum(c['split']==s and c['kind']==k for c in cases) for k in ['positive','negative']} for s in ['dev','holdout']},'clause_counts':{k:len(v) for k,v in parts.items()}},indent=2))

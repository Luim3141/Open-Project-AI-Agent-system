# M4 / M7 — published workflow adapters và report source integrity

Kết quả: **PARTIAL**. Đã chạy 49 checks trên n8n clone thật với published definitions lấy read-only từ MAIN; 49/49 PASS trong phạm vi adapter. Đây **không phải 16/16 business end-to-end PASS**. WF07 và WF12 trên MAIN vẫn có receipt `COMPLETED/PARTIAL`, `ready=4/targets=5`; actor19 bị từ chối đúng bởi admin security guard. Không sửa RBAC, credentials, Project5 hoặc published workflow trên MAIN.

## Evidence và provenance

- [clone-result.json](clone-result.json): từng test, UTC, HTTP result, request đi tới synthetic Gateway, command, exact n8n image và snapshot/harness SHA256. Run `2026-11-02T03:44:06Z` đến thời điểm `completed_utc` trong file. Image n8n `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`.
- [published-definitions.json](published-definitions.json): activeVersionId/history nodes + connections, workflow settings đọc từ workflow_entity. Không export credential values hoặc execution payload. [published-contracts.json](published-contracts.json): từng published version/hash, triggers, schedules, credential types, Gateway endpoints/options, wiring. 16 graph không dangling edges; kết quả này chỉ là structural evidence.
- [main-read-diagnostic.json](main-read-diagnostic.json): exact serving Gateway/Core/n8n image IDs, UTC, Native GET identity/summary, SQLite `mode=ro` latest collector receipts. [read_main.py](read_main.py) có command tái lập.
- [targeted-tests.json](targeted-tests.json), [targeted-tests.log](targeted-tests.log): 47/47 tests PASS, từng test có UTC và outcome, source commit `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e` **cộng per-file SHA256 của uncommitted working tree**, command và environment Windows Python3.14.3. Không đánh đồng test host với image MAIN mới hoặc cộng vào số test của revision khác.

## Bảng 16 workflow

`VERIFIED_IN_CLONE` dưới đây nghĩa là **nhánh adapter được ghi rõ đã chạy trong actual n8n**, đầu cuối Gateway là fixture. Không có khẳng định Native mutation/provider/RAG integration thật cho nhánh đó. Tất cả16 webhook thử không có transport credential đều trả403, không gọi Gateway fixture; 14 interactive branch giữ nguyên HTTP403 Gateway. WF07/16 dùng machine contract nên không áp dụng caller-Bearer passthrough.

| WF | Classification | Nhánh thực thi và evidence mới | Business boundary chưa được kiểm chứng |
|---|---|---|---|
|01 Local Document Ingestion|VERIFIED_IN_CLONE|`WF01_published_adapter`: source_key search → `knowledge_file_search`; synthetic result trả200; caller auth đi đúng|File ingest/reindex thật, source deletion, indexing read-back NOT_EXERCISED|
|02 OpenProject Event Sync|VERIFIED_IN_CLONE|`WF02_published_adapter`: status → `knowledge_incremental_status`,200|Incremental sync/upsert thật và event delivery NOT_EXERCISED|
|03 Natural Language Request Orchestrator|VERIFIED_IN_CLONE|`WF03_published_adapter`: UUID status → `get_ai_run`,200|Start/plan provider, planning/native writes NOT_EXERCISED|
|04 Multi-Agent Execution Tracking|VERIFIED_IN_CLONE|`WF04_published_adapter`: owned trace URL, synthetic event → TRACE_RETRIEVED/total_events1;403 propagated|Lifecycle signed ACK branch không replay trong run này; evidence historical không được nâng thành final-image proof|
|05 Native API Approval|VERIFIED_IN_CLONE|`WF05_published_adapter`: exact proposal GET; fixture pending/hash → human_confirmation_required;403 propagated|Actual approval không cần kích hoạt khi coding task không yêu cầu; PM decision thực NOT_EXERCISED|
|06 Native API Execution & Verification|VERIFIED_IN_CLONE|`WF06_published_adapter`: exact proposal UUID decision POST chỉ decision/hash;200/403 propagated|Native mutation/read-back/idempotent receipt thật NOT_EXERCISED; không auto-execute raw mutation|
|07 Daily Project Brief|FAILED|Clone `WF07_published_adapter` ký command daily_brief/READY200; `WF07_HTTP200_PARTIAL_is_failure` trả500. MAIN receipt ready4/5/PARTIAL, actor19 DENIED|Schedule08:00 Bangkok không đợi timer mới; MAIN business chưa READY, nguyên nhân bên dưới|
|08 Sprint Risk|VERIFIED_IN_CLONE|`WF08_published_adapter`: as_of_date → `sprint_risks`,200/403|Native relations/sprint risk calculation thật NOT_EXERCISED|
|09 Bug Lifecycle|VERIFIED_IN_CLONE|`WF09_published_adapter`: explicit389 → `get_work_package` include_context;200/403|Bug propose/fix/retest/transition và Native side effects NOT_EXERCISED|
|10 Task Orchestration & Decomposition|VERIFIED_IN_CLONE|`WF10_published_adapter`: UUID get → `wbs_get`,200/403|Draft/adopt/dependency mutation business NOT_EXERCISED|
|11 QA Gate|VERIFIED_IN_CLONE|`WF11_published_adapter`: explicit389 → `qa_evidence_list`,200/403|Capture/run/review/transition native gates NOT_EXERCISED; không tự nhận QA passed|
|12 Weekly Summary|FAILED|Clone interactive weekly_summary200/403; actual signed weekly branch qua clone-only trigger READY200, HTTP200/PARTIAL→500. MAIN ready4/5/PARTIAL actor19 DENIED|Friday17:00 timer không đợi; MAIN chưa READY|
|13 Second Brain Re-indexing|VERIFIED_IN_CLONE|`WF13_published_adapter`: feedback_get UUID → `knowledge_feedback_get`,200/403|Reindex/feedback decision/apply thật NOT_EXERCISED|
|14 Durable RAG Recovery|VERIFIED_IN_CLONE|`WF14_published_adapter`: UUID status → `knowledge_sync_status`,200/403|Retry/requeue/recovery native/index side effects NOT_EXERCISED|
|15 Reconciliation & Drift Detection|VERIFIED_IN_CLONE|`WF15_published_adapter`: `knowledge_integrity`,200/403|Native/SQLite/Qdrant actual identity comparison nằm ở RAG evidence riêng; synthetic body không chứng minh drift clean|
|16 Main Health Monitoring|VERIFIED_IN_CLONE|`WF16_published_adapter`: machine GET `/internal/automation/monitor`, synthetic HEALTHY200, missing transport403|15-minute timer và real dependency business health không xác nhận bởi fixture|

49 checks =16 positive adapters +16 transport denials +14 Gateway403 passthrough +1 daily PARTIAL guard +2 weekly signed branch READY/PARTIAL checks. Table classifications count14 `VERIFIED_IN_CLONE`,2 `FAILED`; không có `VERIFIED_ON_MAIN` từ run adapter này.

## Root cause WF07 / WF12 — không nới quyền để PASS

MAIN registry project5 chứa actor19 rolePM. Token đọc `/api/v3/users/me` trả đúng `id=19`, `login=ba-pm`, `status=active`, nhưng **admin=true**. `Native.identity()` từ chối privileged admin account ngoài exact system-owner18 bằng `IDENTITY_MISMATCH_OR_ADMIN_TOKEN`. Đây không phải token nhầm actor, thiếu webhook auth, hoặc service offline. Actors20–23 identity và scoped summary GET thành công, actor18 được loại khỏi target collector đúng contract. Latest daily/weekly receipts cho19 là DENIED, các target khác READY.

Giữ guard và registry, không hạ admin/migrate token/loại target âm thầm. Cần Owner quyết định account19 có nên tiếp tục là global admin; phương án sửa là identity/role/credential configuration được duyệt riêng và xác minh least privilege, sau đó tạo bounded new-period collector hoặc explicit supported recovery. Không replay cùng receipt idempotency key để giả tạo READY.

## Clone isolation và giới hạn

[qualify_published.py](qualify_published.py) import16 published definitions vào clean n8n tmpfs; synthetic header/HMAC credentials, private fixture files, `--internal` Docker network, không mount MAIN volume/DB, không expose host port. Chỉ rewrite Gateway URL sang fixture, disable schedule timers, force clone execution retention OFF. WF12 bổ sung **clone-only webhook nối vào published weekly_metadata** để chạy đúng signed scheduled branch mà không chờ lịch. Graph/code/HTTP body production không thay để xanh test. Clone containers/network đã xóa sau kiểm tra ownership labels; fixture-only files còn trong private operator folder.

Gateway fixture là Python HTTP server chạy trên baseline Gateway image `sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb`; **không phải Gateway Service/API thật**. Nó chỉ ghi request/headers synthetic và trả contract bodies xác định. Không chứng minh RBAC thực, provider, Qdrant/SQLite mutation, Native read-back, timer reliability, exactly-once, rollback hoặc security retention production. Runtime thử fetch n8n catalog bị external DNS block bởi internal network; adapter checks không phụ thuộc external fetch.

Lần harness trước thất bại do CLI2.43.6 không hỗ trợ `publish:workflow --all`, synthetic Crypto cần `hmacSecret`, và readiness health trước webhook registration. Đã sửa harness bằng exact per-ID publish, runtime credential schema và wait registration; run cuối49/49 có provenance riêng, không dùng failure làm production defect.

## M7 source fixed — engineering reports

`openproject/ai/gateway/engineering_reporting.py` đã sửa bằng red/green tests:

- Native/GitHub source unavailable trả unknown (`None`) và `source_status=PARTIAL`, tránh báo zero giả; không bịa parent379/title khi parent không có trong visible source list.
- WP narrative có source link `/work_packages/<exact-child>/activity`, PR có link exact number; không dùng parent làm proof child.
- `get_report` và `list_reports` re-read Native source IDs/lockVersions; source version đổi đánh dấu HISTORICAL, source thiếu/deleted/not-visible ẩn nội dung cũ. Legacy report thiếu source metadata trả UNKNOWN, không giả fresh. Native unavailable trả UNAVAILABLE.
- Error chỉ ghi exception class, không lưu raw exception message vào report/log từ nhánh collection vừa sửa.
- Tests stale trên `test_takeover_workflows.py` được giới hạn đúng human-trace reply branch sau lifecycle branch append; không thay security boundary/runtime workflow.

Red phase3 tests xác nhận lỗi unsupported parent/missing links/source_status trước fix; red bổ sung list-source-hidden cũng fail trước fix. Green cuối47/47 liên quan reporting, operational freshness/ACL, workflows và weekly date semantics; [targeted-tests.json](targeted-tests.json) là authority. Những sửa này là **SOURCE FIXED / host fixture tested**; root quản lý candidate build/deploy và verification chính xác image. Tài liệu này không tự nhận DEPLOYED_TO_MAIN hoặc LIVE VERIFIED cho report source fix.

Chưa kiểm Human UAT/UI, không deploy và không thực hiện production business write trong phạm vi này. Còn giới hạn MAIN WF07/WF12 PARTIAL do privileged actor19 và các write-heavy branches chưa business E2E.

## Bổ sung M7 — timestamp và provider usage (source-only, sau image bca)

Đã xác nhận hai lỗi bằng RED trước sửa: timestamp trả `2026-11-02 10:30:00` thiếu timezone thay vì exact instant ISO8601; usage đọc legacy requests9999 thay vì scoped generation receipt150. Source reporting mới:

- `format_iso` dùng timezone-aware `datetime.isoformat(timespec='seconds')`, giữ `None` cho missing và chấp nhận Unix epoch0. `created_iso`, schedule read-back và `generated_at_iso` có offset. ISO string round-trip về Unix timestamp gốc; không đổi Core/UI.
- Token totals lấy durable `gemini_call_receipts.document.usage.totalTokenCount`, join existing queue/run thuộc Project6, chỉ phase `generateContent`. Không cộng `countTokens`, requests legacy hoặc other-project receipt. Durable receipt primary-key upsert chỉ tính một lần; generation attempts có receipt riêng và usage thật vẫn được tính đúng.
- Giữ key `estimated_tokens_consumed` cho caller compatibility, thêm `usage_source`, `usage_complete`, `usage_missing_calls`, `runs_without_usage_receipts`. Có runs mà không biết usage trả `None`; biết một phần giữ known subtotal và đánh dấu incomplete. Zero chỉ khi không có run hoặc provider thực báo zero; không suy billing/quota từ tổng này.

[receipt-schema.json](receipt-schema.json) là read-only schema, document key names và aggregate phase/state/usage-presence, không xuất receipt body/credentials/source contents. Command tái lập [inspect_receipt_schema.py](inspect_receipt_schema.py). Exact image tại thời điểm metadata read được ghi trong file; không phải image đã chứa source fix.

[m7-time-usage.json](m7-time-usage.json), [m7-time-usage.log](m7-time-usage.log): **49/49 host fixture checks PASS** trên revision mới, source hash/command/UTC/environment từng test được giữ riêng; không cộng với47 tests của revision trước hoặc49 n8n adapter checks. Gồm timezone default/UTC/epoch/missing, generated/list ISO round-trip, project scope, countTokens exclusion, receipt upsert replay, partial/missing usage. Historical timezone database quy định Asia/Ho_Chi_Minh có offset+08 tại epoch1970; test epoch dùng UTC để kiểm instant đúng, không ép lịch sử thành UTC+7.

Trạng thái **SOURCE FIXED / HOST TESTED**. Source này khác image `bca` mà root đang dùng cho ongoing E2E; không dùng E2E đó để nhận timestamp/usage fix đã live. Root sẽ qualify/build/read-back reporting mới sau run idle. Không deploy, gọi provider, sửa Core/UI hoặc dữ liệu MAIN trong bổ sung này.

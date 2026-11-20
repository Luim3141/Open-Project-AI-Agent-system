# Trạng thái sau Owner approval — MAIN đã đổi

Proposal30218aff đã được duyệt và áp dụng. Xem [MAIN_ROLLOUT_RESULT.md](MAIN_ROLLOUT_RESULT.md) và `rollout-20261101T110426Z/deployment-result.json`. Các đoạn NOT_DEPLOYED/AWAITING_OWNER_APPROVAL phía dưới là pre-rollout snapshot, không phải trạng thái hiện tại. Chưa human acceptance/full business E2E.

---

# Phase2 current — 01/11/2026

Phase2 current: lifecycle outbox and actual GatewayASGI→n8ncloneACK verified; storage redaction tested beyond noneflags; actor19 identity19/admin=true explainsDENIED. Read N8N_EVENT_PUBLISHER_EVIDENCE.md and N8N_SECRET_RETENTION_REMEDIATION.md. The16workflow inventory/mapping below is the timestamped Phase1 live snapshot, not a fresh run of all16. WF02/03/10/11/13/14/15 remain role-scoped management adapters; no broad coding capabilities/schedule added. MAIN still unchanged; targetedWF04draft only private, noimport/publish.

---

# Audit n8n Main — 16 workflows và tích hợp coding pipeline

Snapshot: **2026-11-01 03:55:54 UTC / 10:55:54 Asia/Bangkok**; execution-body inspection thực hiện ngay sau snapshot. Chỉ CLI/read-only SQLite; **không Computer Use, không gọi webhook, không trigger workflow, không gọi LLM/provider, không sửa live DB/config/workflow, không Project5 write**. Chỉ tạo các artifact audit này.

## Kết luận

- Main thật là `qldapm-n8n-main`, image `docker.n8n.io/n8nio/n8n:2.43.6`, Docker volume `qldapm-n8n-main-data` → `/home/node/.n8n`. Đọc database bằng `sqlite3.OPEN_READONLY`, không chạy các script deploy/import/prune có sẵn.
- Có **16 workflow, 16 active, 16 activeVersionId có workflow_history, 16 registered webhook**. Tổng execution còn lưu: **538 success / 30 error**, không suy ra 538 business outcomes thành công.
- **15/16 active nodes+connections bằng draft chính xác**; WF12 có draft khác published. Khác biệt WF12 là layout, thứ tự object keys và explicit defaults (authentication none, HMAC SHA256/hex/binaryData false). Cả published và draft đều có schedule + completion guard. Chưa chứng minh đây là bug chức năng; không được tự publish draft.
- Chỉ **WF07, WF12, WF16** có Schedule Trigger. 13 workflow khác là webhook adapters cần caller; không phải 16 background automation đang tự chạy.
- Coding pipeline Project6 ghi execution_events vào Gateway SQLite; **WF04 đọc trace qua REST khi có webhook caller**. Không tìm thấy Gateway publisher POST đến n8n `/webhook/` trong `openproject/ai/gateway/*.py`. Vì vậy integration hiện có là trace-read adapter, chưa phải event bus điều phối coding tự động.
- WF07 và WF12 latest scheduled executions **error đúng guard** do Gateway trả `COMPLETED/PARTIAL`, 4/5 targets ready. WF12 actor19 `DENIED`, actors20–23 `READY`. Không bỏ guard hoặc tự sửa role/token.
- **Rủi ro High về secret retention:** execution_data latest của 13 workflow interactive chứa nonempty `Authorization` và `X-QLDAPM-Webhook-Token` trong webhook input. Chỉ xuất boolean presence, không giá trị. Nhiều workflow live bật lưu success/error/progress; source candidate đặt save none. Đây là lưu secret trong DB execution, không phải bằng chứng secret đã bị truy cập trái phép. Cần remediation được duyệt, tuyệt đối không copy DB/execution payload vào Git.

## Evidence artifacts và phương pháp

- `n8n_live_sanitized_20261101.json`: workflow IDs/versions, active nodes/code hashes, URL/path/schedule/graph và 5 latest execution metadata mỗi workflow. Không credential values, raw node code, payload hoặc environment.
- `n8n_execution_sanitized_20261101.json`: latest execution HTTP/business states và boolean secret presence. Không raw headers hoặc ticket content.
- Truy vấn read-only: `workflow_entity`, `workflow_history`, `webhook_entity`, `execution_entity`, `execution_data`; execution_data được dereference trong process và chỉ in allowlisted metadata.
- `docker inspect` chỉ `.Mounts`/`.State`; không dump Config.Env. n8n startup logs chọn dòng version/ready: n8n 2.43.6 ready port5678; internal Task Broker port5679. Host Main port5679 khác internal broker.
- Container restarted lúc **2026-11-01 03:52:41 UTC**. Latest retained executions là trước restart; khoảng trống downtime không chứng minh scheduler bị hỏng. Audit không chờ daily/weekly lịch mới và không trigger bù.

## Inventory thực tế

Thời gian ở bảng là **UTC** từ database. `success` là execution engine; cột HTTP/business mới cho biết outcome được kiểm tra.

| WF / tên | Trigger | Latest execution / UTC | n8n status | HTTP/business outcome | Classification |
|---|---|---|---|---|---|
| WF01: Local Document Ingestion | Webhook only | 2612 / 2026-10-28 16:16:30.422 | success | 409 FILE_DOCUMENT_REVISION_CHANGED | CONNECTED; latest policy/conflict refusal |
| WF02: OpenProject Event Sync | Webhook only | 2541 / 2026-10-28 05:01:47.909 | success | 200 | CONNECTED adapter; historical read/response |
| WF03: Natural Language Request Orchestrator | Webhook only | 2604 / 2026-10-28 15:35:03.869 | success | 200 | CONNECTED adapter; historical read/response |
| WF04: Multi-Agent Execution Tracking | Webhook only | 2701 / 2026-10-29 22:11:21.646 | success | 200 TRACE_RETRIEVED | CONNECTED adapter; historical read/response |
| WF05: Native API Approval Workflow | Webhook only | 2545 / 2026-10-28 05:01:56.419 | success | 400 USE_WF06_FOR_EXACT_PM_DECISION | CONNECTED; latest policy/conflict refusal |
| WF06: Native API Execution & Verification | Webhook only | 2547 / 2026-10-28 05:01:57.473 | success | 409 INVALID_ARGUMENTS | CONNECTED; latest policy/conflict refusal |
| WF07: Daily Project Brief | Webhook + daily08:00 Bangkok | 2812 / 2026-10-31 01:00:00.045 | error | PARTIAL | CONNECTED; business PARTIAL / NOT READY |
| WF08: Sprint Risk | Webhook only | 2549 / 2026-10-28 05:01:58.140 | success | 200 | CONNECTED adapter; historical read/response |
| WF09: Bug Lifecycle Automation | Webhook only | 2551 / 2026-10-28 05:02:03.781 | success | 200 | CONNECTED adapter; historical read/response |
| WF10: Task Orchestration & Decomposition | Webhook only | 2552 / 2026-10-28 05:02:08.908 | success | 200 | CONNECTED adapter; historical read/response |
| WF11: QA Gate Transition | Webhook only | 2613 / 2026-10-28 16:16:31.665 | success | 200 | CONNECTED adapter; historical read/response |
| WF12: Weekly Summary | Webhook + Fri17:00 Bangkok | 2750 / 2026-10-30 10:00:00.198 | error | PARTIAL | CONNECTED; business PARTIAL / NOT READY |
| WF13: Second Brain RAG Re-indexing | Webhook only | 2557 / 2026-10-28 05:02:17.532 | success | 200 | CONNECTED adapter; historical read/response |
| WF14: Durable RAG Recovery | Webhook only | 2558 / 2026-10-28 05:02:19.124 | success | 200 | CONNECTED adapter; historical read/response |
| WF15: Reconciliation & Drift Detection | Webhook only | 2559 / 2026-10-28 05:02:19.671 | success | 200 | CONNECTED adapter; historical read/response |
| WF16: Main Health Monitoring | Webhook + every15min | 2864 / 2026-10-31 14:30:00.018 | success | HEALTHY | CONNECTED; historical scheduled health |

`WF10 HTTP200` không tự chứng minh decomposition/adoption; `WF11 HTTP200` không chứng minh QA test pass/transition; `WF03 HTTP200` không chứng minh coding E2E hoặc provider inference. Latest body branches không được kích hoạt lại trong audit.

## Mapping source → live adapter → coding pipeline

| WF | Thực tế active workflow | Source connection và giới hạn |
|---|---|---|
| WF02 | `qldapm-op-sync`; explicit native upsert hoặc `knowledge_incremental_sync/status`, stable UUID request_id; caller Bearer | `automation/deploy_real_n8n_workflows.py:1722`; `gateway/service.py:1220`; Native incremental scan thực chạy trong Gateway background worker `service.py:565–574`, không Schedule Trigger của WF02. Không thấy Native→n8n event publisher. Project6 scan được gọi qua scoped service khi engineering enabled. |
| WF03 | `qldapm-agent-request`; `start_ai_run`, engine `gemini` hoặc `supervisor_gemini`, allow_routine_writes false; status qua `get_ai_run` | Builder `deploy_real_n8n_workflows.py:1562`. Không có OpenClaw/engineering admission branch trong active WF03. Coding Project6 admission là `gateway/engineering.py:298–306`, enqueue engine=openclaw ở existing ai_queue. Chưa nối WF03 thành coding command entrypoint. |
| WF04 | `qldapm-agent-trace` → GET `/api/v1/agent-runs/{run_id}/trace`; trả actual events; latest2701 HTTP200 TRACE_RETRIEVED | `gateway/app.py:253–262` suy project theo owned stored run; `engineering.py:17–24`; `execution_events.py:41–55` chỉ INSERT SQLite. `engineering_lifecycle.py:48–51` append step completion. Không POST webhook. Đây là existing trace read integration, không scheduler thứ hai. |
| WF10 | `qldapm-wbs-breakdown`; WBS draft/get/adopt/next/from_ba/dependency operations qua caller authority | Builder `deploy_real_n8n_workflows.py:1756`; `gateway/service.py:258` giới hạn command cho engineering scope, không mở wbs_* qua Project6 scope. Chưa chứng minh WF10 nhận coding-unit lifecycle hay tạo coding jobs. |
| WF11 | `qldapm-qa-gate`; qa_evidence/list/capture/get/review, test run/get/from_run, transition_prepare; explicit IDs và hashes | Builder `deploy_real_n8n_workflows.py:1782`; QA Native evidence gateway riêng. Không tự coi engineering JUnit/commit/PR là QA-gate evidence. Chưa có bằng chứng WF11 tự chạy sau coding test. |
| WF13 | `qldapm-reindex`; Native reindex/feedback submit/get/decision/apply | Builder `deploy_real_n8n_workflows.py:1734`; qua business commands, không tự được project override. Coding RAG ingestion dùng existing Gateway service/scoped knowledge worker; không tìm thấy coding publisher đến webhook này. |
| WF14 | `qldapm-error-handler`; knowledge_sync_status/retry trên own persisted job; UUID/idempotency guard | Builder `deploy_real_n8n_workflows.py:1615`. Không có n8n errorTrigger và không có auto schedule. Tên Error Webhook không biến nó thành handler của mọi error/coding exception. Gateway recovery worker `service.py:593–624` xử lý durable queue trực tiếp. |
| WF15 | `qldapm-reconciliation`; `knowledge_integrity` kiểm tra Native/SQLite/Qdrant | Builder `deploy_real_n8n_workflows.py:1610`; webhook only. Không có schedule hoặc auto coding completion publisher. Chưa audit lại corpus hoặc retry/reindex. |

Source path trong bảng tương đối với `openproject/ai/`; snapshot live là authority cho nodes published. Các builder lịch sử đầu file từng có mock constants/defaultWP38; `build_workflows()` hiện gọi `secure_workflows` ở cuối. Không lấy docstring đầu file hoặc JSON bundle cũ làm deployment proof.

`gateway/n8n_indexing_hook.py` chỉ có handler/export helper; không có caller/import trong Gateway search. Helper export trỏ staging legacy path và inactive. Không thấy workflow17/index-hook trong live inventory; không dùng module tồn tại để khẳng định Main events đã wired.

## Scheduled failures cần phân biệt với transport

- WF07 execution **2812** 31/10 01:00UTC và **2714** 30/10 01:00UTC: signing và Gateway HTTP node success, Gateway `state=COMPLETED,status=PARTIAL,targets=5,ready=4,unavailable=1`; final node throws `DAILY_REPORT_NOT_READY`. Execution2646 ngày29/10 là `READY` và success. Chưa suy actor bị denied trong daily vì response này chỉ có counts.
- WF12 execution **2750** 30/10 10:00UTC: signing và HTTP success, Gateway `COMPLETED/PARTIAL`, 4/5; actor19 DENIED. Final throws `WEEKLY_REPORT_NOT_READY`. `daily_brief.py:58–70` và `weekly_report.py:39–50` map permission/auth failures sang DENIED; bằng chứng chưa phân biệt missing credential, revoked token, membership mismatch hay policy role mismatch. Cần identity read-only với đúng credential, không reset role/token theo suy đoán.
- WF16 latest2864 31/10 14:30UTC trả `HEALTHY`; không phải proof fresh 01/11. 15-minute schedule có trong active history và registered workflow, nhưng chưa quan sát execution sau restart trong snapshot này.

## Findings và next tests khả thi

1. **High — secret retention trong execution_data.** Thiết kế lưu cần loại bỏ sensitive headers trước persistence hoặc disable success/error/progress retention đúng nhu cầu observability; giữ metadata/IDs/status được redact. Sau approval: dùng clone kiểm tra execution_data không còn Bearer/transport secret, rồi preview change cho live. Credential rotation/cleanup lịch sử là operation riêng, không thực hiện trong audit.
2. **Medium — daily/weekly business readiness chưa đạt** vì một target unavailable/denied. Kiểm tra read-only native identity/role/membership của target19 và private credential metadata/expiry. Giữ DENIED/READY boundaries; không hạ completion guard. Thử fixture clone bị revoke/role mismatch/timeouts để phân biệt reason codes.
3. **Integration gap — không có event publisher Gateway→n8n cho coding lifecycle.** Nếu yêu cầu sản phẩm là n8n thật sự orchestrate coding, cần chọn một authority: existing Gateway queue tiếp tục điều phối và n8n chỉ observe/schedule thì ghi rõ; hoặc thiết kế narrow signed/idempotent event adapter trong clone, giới hạn project6/run owner, không nhét raw code/prompt vào event. Không thêm scheduler thứ hai chỉ để đủ tên workflow.
4. **Medium — n8n success không phải business success.** WF01/05/06 latest trả 409/400/409 dù engine success (HTTP neverError + respond-to-webhook). Đây có thể là expected denial regression, không bug; dashboard/acceptance phải phân loại statusCode/error và business receipt thay vì đếm green execution.
5. **Low — WF12 draft/published lệch.** Diff theo semantic defaults trước quyết định; không tự publish. Active history0adeacb0… mới quyết định schedule thực tế, draftd753e6f3… chưa active.
6. **NOT VERIFIED trong audit:** fresh webhook auth/owned cross-project trace, new scheduled postrestart success, queue recovery outage, fresh QA evidence/adoption/decomposition, Native/RAG reconciliation, provider budget/inference, Internet route. Tất cả có thể tạo receipt/metadata hoặc business writes nếu trigger; audit không chạy chúng.

Đề xuất bước tiếp theo: tận dụng isolated clone với provider blocked để kiểm tra auth/secret persistence + daily/weekly deny diagnosis + semantics tất cả 16 outputs; chỉ chạy controlled Project6 coding E2E khi được giao riêng. Không dùng live Project5 hoặc chạy full qualification script vì các script đó có thể trigger inference, mutate workflow/Native và seed fixtures.

# QLDAPM MAIN — kết quả engineering 28/10/2026

**Trạng thái: `READY_FOR_OPERATOR_UAT`, có giới hạn được liệt kê bên dưới.** Chưa có human sign-off; không phải `UAT_PASSED` hoặc `FULL_LOCAL_GO_LIVE_READY`.

Target duy nhất: MAIN, Project **5 / qldapm-local**, workspace `D:\AI project\QLDAPM chat`. Branch `codex/local-multi-agent-upgrade`, HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e` giữ nguyên. Không commit, push, reset, clean hoặc xóa dữ liệu untracked. Kết quả này thay thế các tuyên bố readiness cũ trong báo cáo Gemini; giữ báo cáo lịch sử để truy vết.

Readback cuối lúc **23:29:47 ICT**, backup sau triển khai **23:30:39 ICT**, preflight mới **23:38 ICT**. Evidence đã lọc: [CODEX_TAKEOVER_20261028_EVIDENCE.json](CODEX_TAKEOVER_20261028_EVIDENCE.json). Checkpoint tiếp tục duy nhất: [CODEX_TAKEOVER_CHECKPOINT_20261028_RUNTIME.md](CODEX_TAKEOVER_CHECKPOINT_20261028_RUNTIME.md).

## 1. Những lỗi đã sửa và tính năng đã hoàn thiện

| Vấn đề trước sửa | Root cause và thay đổi | Kết quả thực tế |
|---|---|---|
| Scanner bỏ sót comment-only | Canonical document không có activities, Native journal không tăng lockVersion. Dùng shared actor snapshot, updatedAt và audit round-robin tối đa32 activities/WPs mỗi scan | Clone tự đồng bộ CREATE, UPDATE, thêm/sửa/clear comment; năm job verified, BGE-M3 thật, FTS/Qdrant/RAG khớp |
| Snapshot có thể cũ dù version không đổi | Kiểm tra hash từng comment cũ chưa chứng minh tập activities hiện hành khớp đầy đủ | Recheck cả bounded activity set trước tìm kiếm và trước prompt; chặn actor khác và nguồn stale/revoked |
| WF12 chỉ có webhook | Thiếu machine schedule và collector receipt | Publish nhánh Friday17:00 Asia/Bangkok, HMAC, báo cáo riêng từng actor, durable hash/idempotency, PARTIAL làm execution thất bại |
| Câu đếm Task trên UI trả339 và gọi model | Grammar không nhận tiền tố “Hiện tại” cùng suffix chỉ đọc | Cùng câu hỏi sau sửa trả57 Task, model0; không mở rộng quyền cho mixed-write prompt |
| PDF không chạy dù báo cáo cũ nói hỗ trợ | Image thiếu parser và allowlist chỉ nhận các format cũ | Pinned PDF ingestion với pypdf6.21.3, child process có giới hạn; MD/DOCX/PDF đã qua real embedding/index/search/read/ACL |
| Delete preview bị giữ vĩnh viễn bởi request cache cũ | Pending knowledge_ingest/deindex bị coi là Native write chưa rõ outcome | Bỏ hold riêng hai cache-only actions; unknown Native write vẫn giữ. Clone ký receipt/delete/tombstone và xóa đúng cache fixture thành công |
| Registered workflow contract không còn file | Registry trỏ `/app/knowledge_sources/main-workflow-contract.md`, image không chứa file | Khôi phục từ artifact lịch sử, cập nhật PDF contract, COPY vào hai Dockerfile; pin SHA mới, WF01 MAIN reindex/read/replay PASS |
| WF11 `{id}` mặc định thất bại Native mode | Node qa_target gọi custom get_gate không hỗ trợ | Chuyển sang qa_evidence_list(native_id), positive-int validation và Native ACL trước query; MAIN371 trả đúng pending evidence |
| Ollama task không bảo đảm chạy | Task disabled, action trỏ executable PowerShell không bền | Dùng WindowsPowerShell System32, enable task cũ limited/interactive, invocation result0, không tạo daemon trùng |
| MAIN thiếu lịch backup riêng | Chỉ có backup Staging và các snapshot thủ công | Task MAIN hourly/logon, snapshot tối đa một lần/24h thành công, PG/SQLite+n8n/assets/config; hai backup thực tế PASS |
| UAT preflight cũ báo sai và đọc SQLite không an toàn | Hardcode376docs/1745points, nhầm legacy theo source count, mở live DB từ Windows, chưa xét expiry | Đọc DB trong container sở hữu, reconcile provenance động, kiểm tra đúng ba legacy IDs, PM expiry và workflow published;9 targeted tests +actual preflight PASS |

Canonical document không chứa comments. Actor snapshots không chia sẻ nội dung bình luận của Owner cho PM. Giới hạn kế thừa:20 comments gần nhất, snippet750 ký tự/comment; hash dùng toàn bộ comment đã sanitize. Comment edit/clear có thể đợi một sweep khoảng `ceil(339/32)*60 = 660 giây`; không hứa full journal hoặc realtime webhook.

PDF contract: operator cấu hình source_key/root/path/SHA256/roles; tối đa256KiB input/text,64 trang, child15s, Linux192MiB/10CPU-s, decoded1MiB/trang và4MiB tổng. Encrypted/corrupt/empty/image-only/oversize fail toàn bộ. Không OCR, arbitrary upload hoặc tự tải mọi Native attachment. Tham khảo giới hạn parser: [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html), [advisory đã đối chiếu](https://github.com/py-pdf/pypdf/security/advisories/GHSA-4vqv-7265-gm2w), [bản6.21.3](https://pypi.org/project/pypdf/6.21.3/).

## 2. Second Brain và Gemini — phân loại bằng chứng

Clone `qualification-6` có Core/PG/Gateway/SQLite/Qdrant riêng, Native credentials tạo riêng, network/volume không dùng MAIN writable databases. Dùng host Ollama chỉ để embedding BGE-M3 thật1024D. Source fixture `actor:18:wp:377`, comment1036, lockVersion1 giữ nguyên khi thay comments.

| Stage | UTC | Job mới verified | Actor document revision |
|---|---|---|---|
| CREATE |11:59:32|0cdd7836-5027-5058-a000-5835096ff37f|e726cdca…|
| UPDATE |12:00:25|a510b964-41ca-5c05-83b4-318de692aaf5|1725eaaa…|
| COMMENT_ONLY |12:01:25|e672b87a-8905-54be-b35b-d30454a295cf|f586717a…|
| EDIT_COMMENT |12:08:32|8c7a8102-249c-5855-98e1-f91bf46cf0a4|1ce2e831…|
| REMOVE_COMMENT |12:19:38|90872148-03dd-54c2-8031-dbe15a2773fe|1725eaaa…|

Final scanner generation23; hai FTS documents/hai points cho fixture. Point IDs `92035f29-f304-50a9-8315-276a33860ca5`, `a7dfd582-3ccc-5c87-8ab0-ef6cf94c3f72`. Citation `/work_packages/377`, source/hash đầy đủ trong public evidence. PM19 không nhận actor18 snapshot. Failed attempts1–5 được giữ, không tính PASS.

Actual MAIN Gemini riêng biệt:

- API run `17054b69-beef-4abc-9a20-a666a58f839f`: LIVE_GEMINI, PM specialist + local Reviewer,1model call/3016tokens.
- n8n WF03 run `9f3cda3e-8a60-4784-bef8-d2a79c9c1682`: LIVE_GEMINI,1call/1944tokens, durable final và status polling.
- Cả hai dùng Native376/v0, RAG `op:wp:376`, doc `4a08e5947b04239d18f871a77b1d9abbe32f907389f1b842f8cb53e308055283`, provenance hash trước model, citation376, không Native write/proposal.
- Source fingerprint `8c902cb1a038655cccc19dff84bc9e5e59416a7aee5f2a3635c0763f873c71d3`. Truy xuất lại Native/ACL trước context; revocation fixture trong business clone chặn search và agent enqueue bằng404.

**Giới hạn acceptance:** chuỗi fresh Native change→auto scanner→RAG được chứng minh trong clone; RAG→Supervisor→Gemini thật được chứng minh trên MAIN với nguồn hiện có. Chưa có một run liên tục fresh clone change→live Gemini. Không gộp hai lần kiểm thử thành một E2E duy nhất; không copy Gemini key vào clone để né quota/credential isolation. Fresh live model coverage là PM+Reviewer, không phải mọi specialist đều gọi model mới. Các nhánh role còn lại có source/unit/historical evidence riêng.

## 3. Ma trận 16 workflow — trigger, auth, nghiệp vụ và durable final

Business suite `workflow-business-10` chạy **đúng final Gateway image**, real Core/PG/Qdrant/n8n và clone credentials,62 execution records được lưu. WF05/06 được helper kiểm tra riêng trước14 workflow checks; không suy ra16PASS từ việc active. Clone không cấu hình Gemini; WF03 live model có evidence MAIN riêng ở trên.

Auth dưới đây: **Actor** = webhook credential + actor bearer + fresh Native scope; **Machine** = signed fixed-purpose HMAC, không được Native write hoặc model. Mọi mutation/QA decision trong bảng chỉ là **disposable clone fixtures**, không phải phê duyệt của con người trên MAIN.

| WF | Trigger / auth | Business happy path và final state | Durable evidence |
|---|---|---|---|
|01 Ingestion|Webhook / Actor|Native + pinned MD/DOCX/PDF → parse/chunk/BGE-M3/index/search/full read|Document/source hash, chunks, citations; MAIN contract revision PASS|
|02 Native Sync|Webhook Actor; automatic worker|Scan/status; CREATE/UPDATE/comments tự vào verified; signed delete cleanup riêng|Five sync jobs/generation23; delete ledger/outbox/cache readback|
|03 Supervisor|Webhook / Actor|Deterministic request→done; riêng MAIN SupervisorGemini→done|Run/status receipts, context provenance, provider usage|
|04 Tracking|Webhook / Actor|Actual local Supervisor trace đúng actor/project/run|Persisted events/correlation/run IDs|
|05 Approval|Webhook / Actor|Own proposal preview/get; rejected proposal giữ state|Proposal/hash/state trong SQLite|
|06 Native Write|Webhook / Actor + exact approval fixture|Approved create→Native377/v0→independent readback|Exact proposal hash/receipt; không gửi lại Native write|
|07 Daily|Machine daily collector|5/5 role report READY, zero model/write|daily key, durable reports và collector receipt|
|08 Sprint Risk|Webhook / Actor|Native scope/dependencies→persisted risk analysis|report_id/report_sha256 + current source fingerprint|
|09 Bug|Webhook / Actor|Triage/classification đúng mapped Native Task|Triage source/version; forged authority bị từ chối|
|10 WBS|Webhook / Actor|Typed BA plan→structured draft/readback|Own immutable spec/id/hash; no Native write|
|11 QA|Webhook / Actor, tách producer/QA/PM|Automated readback proof→QA23→PM19→signed REVIEW transition|Artifact/proof/review receipts và Native version readback|
|12 Weekly|Actor webhook + Machine schedule|Clone actual schedule5/5; manual report đọc đúng rolling7day contract|weekly Monday dedupe key, peractor report hashes|
|13 Reindex|Webhook / Actor|Changed Native description→reindex→latest citation|New source revision/job/index readback|
|14 Recovery|Webhook / Actor|Deliberate DLQ fixture + real Qdrant pause→retry→verified|Status/attempt/receipt, worker recovery|
|15 Reconcile|Webhook / Actor|Xóa đúng một fixture point→detect drift→reindex repair|Missing point ID và before/after integrity reports|
|16 Monitor|Machine webhook/schedule|Real paused Qdrant→DEGRADED→durable alert metadata|Report/hash; configured15minute cache verified|

## 4. Workflow robustness — error, retry, idempotency, schedule, giới hạn

| WF | Error path / retry / idempotency đã kiểm tra | Scheduler và remaining boundary |
|---|---|---|
|01|Same UUID replay giống; source/hash/role bị chặn; malformed/encrypted/oversize PDF fail; RAG busy retry cùng key có giới hạn|Không có arbitrary upload/attachment crawler|
|02|Stale activity set fail trước prompt; snapshot failure không mất cursor; replay/restart và bounded audit tests|Worker60s; comment edit sweep tối đa khoảng11phút|
|03|Status polling tới durable final; typed scope/negative intent; provider timeout/quota/error regression|Không callback push mới; polling là contract đang dùng|
|04|Own trace/scope RBAC, không tạo mutation để lấy trace|Không cần scheduler|
|05|Own read/rejection; cross-role403; approvals không do model cấp|Không cần scheduler|
|06|BE403; consumed exact proposal replay409; clone Native create chỉ một lần|Lost-ACK/atomic boundaries có regression; không Main test write|
|07|HMAC/expiry/dedupe trong affected scheduler tests; actual5roles|Clone signed collector; không đợi nguyên ngày production để thử|
|08|Report readback kiểm tra hash và source scope; không invent status history|Snapshot risk, không tính velocity cá nhân|
|09|Forged authority denied; Bug/WBS unit group36PASS|Không gọi triage PASS là mọi Bug lifecycle đã UAT|
|10|Own draft scope/hash; shared proposal guards; không tự chuyển depends_on thành Native relation|Full relation workflow giữ nguyên existing contract/approval|
|11|Out-of-order review denied; Own producer không tự review; default native_id strict and scoped|IN TESTING starting state/reviewer được seed chỉ trong clone; human UAT pending|
|12|Durable report references/hash; duplicate/concurrency/interrupted fail-closed; PARTIAL không thành n8n success|MAIN Friday17:00 Bangkok static+published; clone everyminute actual. Monday key chỉ dedupe, báo cáo rolling7days|
|13|Changed revision readback; stale revision không được dùng|Không có Main source mutation để test|
|14|Wrong actor403; retry/replay/status và actual dependency recovery|DLQ state được inject; không khẳng định thử mọi fault/permutation|
|15|Exact point repaired; background fixture outbox quiescent trước drift|Imported clone baseline text-only; không claim toàn bộ baseline vectors complete|
|16|Timeout detected; cached result/hash giống sau dependency phục hồi|Clone schedule tắt để kiểm soát first probe; MAIN schedule giữ nguyên; không immediate uncached recovery claim|

Default WF11 MAIN id `LeRVT3LWNBkJ2iz3`, published version `65f31f4c-186a-4950-8178-f50204bc261c`; chỉ thay node qa_target. WF12 id `ZkgS8RZbPRA2zbhQ`, version `0adeacb0-8751-4603-9136-d8feeb2542b8`,4→9nodes; nguyên bốn webhook nodes giữ nguyên.14workflow còn lại nodes/connections/settings khớp before snapshot. Full active/version list trong evidence JSON.

## 5. Audit 28 subsystem theo requirement và source

Phân loại dựa actual contracts và bằng chứng đang có, không sao chép nhãn OPTIONAL/COMPLETE của Gemini. “Fresh” không bao hàm full UI/human UAT; “giữ nguyên” nghĩa không có thay đổi cần deployment mới, không có nghĩa test mọi nhánh.

| # | Subsystem | Kết luận và căn cứ | Gap/enhancement được xử lý thế nào |
|---|---|---|---|
|1|Core / Native API|MAIN identity/package read; clone actual writes/QA/tombstone; Core image giữ nguyên|Polling tự phát hiện change đã đáp ứng; direct webhook enhancement|
|2|Users/roles|Fresh Native RBAC và cloned membership revoke|Role editor phải dùng Native admin; không nới quyền trong CC|
|3|Gateway|Final image qualified/deployed/readback|Dynamic config reload không là prerequisite; controlled restart hiện hành|
|4|Assistant|Actual UI count57/render; actual model API |SSE streaming enhancement; không giả định human UAT|
|5|Control Center|Search/monitor/QA pending actual UI; state/API contracts|Không thêm duplicate admin editor; dùng existing tools/reindex route|
|6|Supervisor|Actual MAIN PM→Reviewer, typed scope/routing regression|Complex multi-hop prompt cần operator assessment; không ép mọi agent chạy|
|7|Agent registry|Current registry/source và workflow tests|External dynamic registration không là dependency local|
|8|Specialists|Fresh PM/live + localReviewer; other role source/offline/historical evidence|Multi-round debate không bắt buộc; không claim fresh five-role live model|
|9|Gemini|Actual two read-only runs, provider receipts/usage/context provenance|Ollama là embedding, không thêm chat fallback hoặc đổi FREE_ONLY policy|
|10|Deterministic tools|Actual same UI question57model0, Native total339|Không thêm RACI analytics khi thiếu requirements/data|
|11|Tool contracts|Typed action validation, unknown fields/role/source guarded|Giữ fail-closed; malformed payload không auto sửa rồi execute|
|12|16n8n|Fresh actual business clone suite + MAIN published definitions|Final via durable status polling; không coi thiếu push callback là mất final|
|13|Scheduler/webhook|WF12 gap đã sửa; daily/weekly actual clone; HMAC/replay tests|SQLite durable queue đủ local; không thêm Celery/Redis; không replay missed schedules|
|14|Ollama|Actual1024D embed, healthy worker, task result0|Physical reboot/pre-login chưa test|
|15|Qdrant|Registered provenance/chunks/points khớp, targeted fault/repair clone|Full restore BLOCKED_RESTORE_POLICY; không xóa3legacy để có VERIFIED tuyệt đối|
|16|SQLite FTS5|quick_check ok, exact FTS/no orphan, owning-container reads|Không dùng Windows liveWAL; title weighting tuning chưa cần|
|17|Ingestion|Comment sync + MD/DOCX/PDF pinned contract đã hoàn thiện|Native QA attachment verification có; automatic all-attachment indexing/OCR ngoài bounded source contract|
|18|Hybrid search|Real dense+FTS/HYBRID_RRF/citation in clone+MAIN|Adaptive dense/sparse tuning cần đo chất lượng trước|
|19|Provenance|Native version, document/snippet/source hashes trước prompt|Line-level code/file citations enhancement; không bịa số dòng|
|20|Proposal/approval|Actual clone approved/rejected/create/403/replay409|Human exact approval giữ nguyên; batch rejection UI không bắt buộc|
|21|QA proof/review|Actual clone producer/QA/PM/signedtransition; MAIN pending preserved|Không tự nghiệm thu Main; screenshot-upload UI enhancement|
|22|Audit/receipts|Durable requests/proposals/reports/provider/Native receipts|Existing structured report readback đủ local; CSV/PDF audit export enhancement|
|23|Workers|Queue drain86verified, recovery/retry clone và restart tests|Distributed queue không cần cho one-node deployment|
|24|Monitoring/recovery|Actual cloned outage detect/persist; Ollama limited task|Không cấp Docker admin API cho Gateway để auto restart containers|
|25|UI flows|Login/query/render/search/run monitor/QA pending quan sát; backend/contract regression|Human interaction/sign-off pending; không thêm dark mode|
|26|Deploy/rollback|Gateway-only exact pins/backups/source hashes; all otherMAIN identities retained|Không blue-green; physical reboot/full cross-service restore chưa qualify|
|27|External integration|Local metadata delivery có; actual external delivery `BLOCKED_CONFIGURATION`|Thiếu SMTP/chat credentials/destination/authorization; không tạo tài khoản, không gửi external message|
|28|MCP adapters|Actual HTTP initialize/list68PMtools/invoke; stdio initialize/list77/invoke; ownercall403|HTTP discovery filtered; stdio static catalog. LAN exposure/remoteSSE không cần và không bật|

Credential expiry đã được preflight kiểm tra bằng remaining_seconds thực tế, cảnh báo dưới3 ngày và FAIL nếu hết hạn; không chỉ kiểm tra revoked flag. Không rotate token/key hoặc thay account. External notification vẫn blocked; local durable receipt không được mô tả là email/chat đã gửi.

## 6. UI acceptance và security

Actual Edge UI đã quan sát: đăng nhập, Assistant submit/render câu Task-count, Second Brain search test2/citation376, execution monitor/graph/token usage, QA inbox/detail pending/ineligible self-review. Before fix run `6e8b567a-d361-40c8-8144-649ce8c81dff` sai339 và1Gemini call7553tokens vẫn giữ; after run `bd54830e-87b5-432e-b363-84f087096b2a` đúng57/model0. Không tuyên bố cả phiên zeroModel.

Sau khi phiên tab cũ hết hạn, user báo đã đăng nhập tab khác và yêu cầu ưu tiên terminal/source. Không submit lại vào tab hết hạn, không tiếp tục Computer Use khi API/code đã đủ bằng chứng. Approval/rejection/QA mutation coverage mới ở clone authenticated workflows; không claim mọi nút UI MAIN đã được bấm. Human UAT checklist mới giữ các ô trống.

Negative security coverage gồm actor18snapshot không đọc bởi PM19, Native membership revoke chặn retrieval và agent enqueue, stale comment/version và deleted source không vào kết quả/prompt, strict project/role scope, forged authority, schema errors, canonical không lẫn Owner comments. Protected source/version revalidation ở cả retrieval và model context được giữ. Project isolation và denied-before-prompt có targeted source/regression evidence; không claim adversarial test mọi vector/LLM injection.

## 7. Regression và giới hạn test

Các nhóm thực sự đã chạy (có overlap; **không cộng thành tổng duy nhất**):

- Scanner/comment/RAG29 tests; Linux initial56; storage/retrieval/etc61 Windows.
- Final-image QA/manual/automated/bridge/atomic/deletion/file66 Linux PASS; deletion/QAatomic/approval/PDF/scanner57 Linux PASS.
- File/PDF12 Linux PASS; scanner/count/weekly42; workflow/QA58 Windows.
- Bug/WBS/SupervisorScope/count36; deletion/QAatomic/backup34; backup schedule/aux/operations14 PASS.
- UAT preflight +MainOperations9 targeted tests PASS; actual MAIN preflight PASS. Final host regression gồm preflight/backup/MainOperations14tests PASS; Python compile/git diff check PASS.
- Node syntax check business client và Python compile targeted modules; real clone business suite và separate comment suite PASS.

Broad historical run có hai import errors do mount/PYTHONPATH, đã chạy lại affected modules với test path đúng;12 environment-dependent tests skipped. Không gọi toàn bộ broad run là all-pass. MockTransport HTTP200 tới Google trong unit logs là mock; chỉ hai MAIN model runs nêu trên là fresh live provider proof. Clone attempts thất bại giữ nguyên private logs; không sửa assertions để che product failure. Fixture corrections phân biệt rõ trong checkpoint.

## 8. Deployment, backup và bảo toàn

Final Gateway image: `sha256:eaaa1217ac79cfac4747e0fa71af40bf0d3c1a447f39e6cc24dc20e55a268fc4`, tag `qldapm-ai:main-qualified-qa-20261028`. Core web `sha256:08df5e2bda4042209217453a051671965b553e983001b76ebbb2e1a4d7ede9d3`, n8n `sha256:dd580fe1ab6e99e85bc66f2acf8bc8c5e9409fbe61b2e2803c5024403ef52833` giữ nguyên.

Gateway-only rollout dùng đúng compose.yml +gemini-free.main.yml, private env, `up -d --no-deps --pull never gateway`; source12files đối chiếu SHA256, no schema migration.14n8n definitions giữ nguyên; hai patch riêng WF11/WF12 đã read-back published. Mọi MAIN container khác giữ ID/image. Không restart DockerDesktop/WSL/Windows, không thao tác Staging, không public ports. Actual listeners chỉ127.0.0.1:18088/18089/5679/6333/11434.

| Dữ liệu | Readback cuối |
|---|---|
|Work Packages / Relations|376physical,339visible /352relations; Native business hashes unchanged|
|CustomValues/Journals/password rows|1695/1027/7; exact row fingerprints unchanged|
|WP376 test2|v0 NEW, user data giữ nguyên|
|Bug371|v4 IN ANALYSIS giữ nguyên|
|QA fc0479a8-b30a-5e88-9e4a-10748cb30415|pending_qa; zero human decision performed|
|2FA|4devices/IDs/secret fields unchanged; **chỉ device1.last_used_at đổi do user login**, không claim entire-row hash unchanged|
|Old29non-done requests|Retained; unknown_sha256 a0581b7ae81748f910412e8fa0240c809522da4bacebcd707479299eb12ecb06|
|Active/sync|Active0;86knowledge_sync verified, no pending/retry/DLQ tại snapshot|
|Knowledge|441docs/2027chunks/2030projectpoints; FTS441, quick_checkok, no orphan/missing/stale/payload mismatch|

Integrity status **PARTIAL_UNMATCHED_POINTS** do đúng ba protected legacy vector IDs không đăng ký trong SQLite; được giữ và không đưa vào retrieval. Không xóa để đổi status. Source hợp lệ `op:wp:42` vẫn có registered revision riêng; đếm theo source label không xác định được legacy point.

Source registry `main-workflow-contract` nay pin SHA `0283711d579898eab1b8026ee418cde7dfc9631c8c2fe72a3820814ace1126f1`; document `3c1f58ffd56f3c48f71b9378a6c96b85a005a1a5b097daeed4633b85122aa6dc`,5chunks. Same-key replay giống, read/search new revision PASS, đọc old revision409. Cache refresh không là Native business mutation.

`QLDAPM-Ollama-Health`: limited interactive LUIM,5min/logon, System32WindowsPowerShell, enabled/Ready, result0, listenerPID20592 không đổi. `QLDAPM-Main-Daily-Backup`: limited interactiveLUIM, hiddenPowerShell hourly/logon/IgnoreNew20min, daily duecheck. Backup ghi captured_active_work; **không defer vô hạn do pending/DLQ** (sửa mô tả lịch sử22:40). First snapshot `20261028T152847Z-ae319765`; post-final `20261028T163019Z-e13247c4` đều PASS. Không xóa backup cũ, không auto restore/replay. Backup cần Docker+interactive user và≥5GiB free. Snapshots nhất quán từng store, không atomic xuyên service; **không bao gồm Qdrant**, không gọi fullDR/reboot proof.

Private evidence root `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/codex-comment-sync-20261028`; scheduled backups ở sibling `main-scheduled-backups`. Chỉ SYSTEM/LUIM theo ACL hiện hành. Không commit private config/keys/owner credentials/container inspect. Public JSON chỉ có selected IDs/hashes/counts/statuses, không chứa private config dump. Delivery QA kiểm tra7tài liệu hiện hành, links, actual deployed source/artifact hashes và exact current secret material: PASS,0plaintext matches.

Rollback: dùng `.env.before`/`image-lock.json.before` trong đúng deployment-* directory và Gateway-only compose; giữ mọi DB/receipt/current user data. Nếu về image trước weekly_summary, rollback WF12 branch từ WF12-predeploy.json trước; nếu về image chưa có filtered QA read, rollback WF11 qa_target tương ứng. Nếu rollback file source revision phải xử lý cùng file bytes+registry pin, không chỉ đổi hash. Không dùng stale CORE_IMAGE từ AI sandbox lock làm serving Core proof. Không thực hiện rollback trên MAIN để test.

## 9. Danh sách source thực sự thay đổi trong đợt này

Trong `openproject/ai/`:

- `gateway/openproject_loader.py`, `gateway/native_incremental.py`, `gateway/service.py`, `gateway/automation.py`, `gateway/store.py`, `gateway/weekly_report.py`, `gateway/local_queries.py`, `gateway/file_knowledge.py`, `gateway/local_loaders.py`, `gateway/pdf_text.py`, `gateway/native_deletion.py`, `gateway/native_qa.py`.
- `requirements.txt`, `requirements.lock.txt`, `Dockerfile`, `Dockerfile.gateway-patch`, `knowledge_sources/main-workflow-contract.md`.
- `automation/deploy_real_n8n_workflows.py`, `automation/comment_sync_qualification.py`, `automation/weekly_summary_qualification.py`, `automation/main_operations.py`, `automation/main_auxiliary_backup.py`, `automation/main_backup_schedule.py`, `automation/operator_uat_preflight.py`, `Schedule-MainBackup.ps1`.
- `tests/comment_sync_native_client.py`, `tests/workflow_business_native_client.js`, `tests/test_native_incremental_sync.py`, `tests/test_native_open_counts.py`, `tests/test_scheduled_weekly_summary.py`, `tests/test_takeover_workflows.py`, `tests/test_allowlisted_file_knowledge.py`, `tests/test_native_deletion.py`, `tests/test_native_qa_evidence.py`, `tests/test_main_backup_schedule.py`, `tests/test_operator_uat_preflight.py`.

Documentation: root `architecture.md`, `openproject/ai/README.md`, checkpoint/guide/UAT checklist/readiness references và result/evidence files hiện hành. Không đổi Core source, native workflow/role permissions, schema hoặc staging config. Nhiều file đã untracked từ trước; danh sách trên là touch scope phiên này, không phải git commit diff.

## 10. Handoff và các gate chưa hoàn tất

[Operator checklist hiện hành](OPERATOR_UAT_SPECIFICATION_AND_CHECKLIST.md) không yêu cầu restore/drill lặp lại, không yêu cầu tự approve QA MAIN, không hardcode cache counts cũ. Chạy preflight từ repo root:

```powershell
$env:PYTHONPATH='openproject/ai'
& 'openproject/ai/.venv/Scripts/python.exe' -m automation.operator_uat_preflight
```

Human UAT/sign-off, physical reboot/pre-login recovery, full Qdrant/cross-service DR và một fresh clone-change→liveGemini run liên tục **chưa được chứng minh**. External notification `BLOCKED_CONFIGURATION`. Đây là các giới hạn còn rõ ràng; không thay bằng fake PASS, không publish/ranking người dùng, không thêm paid service. Phần sửa code, clone qualification, affected regression, safe deploy, preservation readback và UAT preparation đã thực hiện; không phát hiện critical regression còn mở trong phạm vi đã kiểm tra.

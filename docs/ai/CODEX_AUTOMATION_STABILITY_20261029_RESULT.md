# QLDAPM MAIN — Automation stability & E2E hardening, 29/10/2026

**Verdict: `AUTOMATION_CORE_E2E_PASS_WITH_LIMITATIONS`.** Native→Knowledge, scheduled read-only workflows và recovery đã được kiểm chứng trong clone thật; WF07 đã sửa và publish MAIN. Gate gọi Gemini thật từ một fresh clone change còn `EXTERNAL_DEPENDENCY_BLOCKED`. Không đánh dấu toàn bộ gates PASS, không human sign-off hoặc go-live.

Target: MAIN Project5 `qldapm-local`, workspace `D:\AI project\QLDAPM chat`; HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`, branch `codex/local-multi-agent-upgrade` giữ nguyên. Baseline là [kết quả28/10](CODEX_TAKEOVER_20261028_RESULT.md). Evidence hiện hành: [JSON đã lọc](CODEX_AUTOMATION_STABILITY_20261029_EVIDENCE.json); continuation vẫn dùng [checkpoint duy nhất](CODEX_TAKEOVER_CHECKPOINT_20261028_RUNTIME.md).

## A. Automation readiness

| System | Automatic trigger | End-to-end | Recovery | Stability | Result |
|---|---|---|---|---|---|
|Native Scanner|Gateway worker60s, actual multiple generations|Fresh CREATE/V2/comment tự tạo job; không manual ingest|Cursor/job sống qua Gateway restart|Generation2→12, đúng một fixture|PASS bounded clone|
|Second Brain|Durable outbox consumer|RealBGE-M3/1024D +FTS/Qdrant +latest citation|Ollama503/Qdrantpause→retry→verified|6jobs verified,2finalpoints/0duplicate|PASS registered fixture|
|n8n|Published WF07/WF12/WF16 cron|9trigger cycles mỗi workflow, business receipts READY|Actual clone restart giữ publication/history/credentials|27scheduled executions success, no duplicate-minute|PASS bounded clone; MAIN readback|
|Supervisor|Authenticated user request|Local PM/Reviewer final đúng sourceV2, own trace|Queue/unknown-outcome guards targeted tests|Durable own run; no unauthorized proposal|LOCAL PASS; live path blocked in clone|
|Gemini|Theo analysis request, không tự gọi vì mỗi data change|MAIN live proof28/10 retained; clone không có key/config riêng|Timeout/quota/provider failure: fresh unit mocks|Clone model calls0, không né quota|EXTERNAL_DEPENDENCY_BLOCKED for fresh continuous chain|
|Agents|Supervisor typed plan|Local agent outputs/references và7trace events|RBAC/source checks giữ nguyên; targeted tests|No Native writes từ analysis|LOCAL PASS; fresh all-specialist live calls chưa làm|
|Ollama|Existing health task +embedding requests|Real hostBGE-M3 qua fixed-route clone proxy|Proxy503 chỉ clone, worker tự recover|MainPID20592 không đổi, single daemon|PASS dependency boundary; no physical reboot|
|Qdrant|Ingestion +deterministic point IDs|Actual clone indexing/retrieval|Pause/unpause clone; no false verified|2finalpoints,0duplicate; Mainlegacy3 giữ|PASS bounded recovery; no fullDR|
|Gateway Workers|App lifespan startup|Auto sync và local AI queue|Actual claimed job survives restart/300slease|12reads/concurrency3, no runaway queue|PASS bounded clone|
|Backup|Windows hourly/logon duecheck, daily snapshot|Existing scheduled backup task result0; fresh predeploy PG/SQLite+n8n/assets snapshot|Task persisted after user Docker restart; no restore|No retention deletion/replay; private ACL|SNAPSHOT/SCHEDULE PASS, not cross-serviceDR|

Native→Knowledge chạy trực tiếp bởi Gateway worker. n8n không nằm bắt buộc trong đường scanner. WF02/WF13/WF14/WF15 giữ các route/coordinator đã qualified trước đó; không tạo vòng gọi workflow mới hoặc cron reconciliation không có trong config.

Các tác vụ có human approval vẫn cần người dùng theo thiết kế. Automation không tự approve QA/PM, không tự tạo Native mutation khi chỉ yêu cầu analysis.

## B. Continuous trace và ranh giới provider

Actual qualification `qualification-7`: **780,14 giây (~13 phút)** từ boot clone đến finish. Core/PG/Gateway/SQLite/Qdrant/n8n riêng, không port public hoặc MAIN writable database mount. Native/HMAC/n8n credentials tạo riêng; n8n data dùng bind directory riêng để thực sự sống qua restart. Ollama host chỉ nhận embedding qua proxy cố định hai route; proxy không nhận arbitrary URL.

Parent trace `8799d810-bd62-431c-a20e-7c102b29f92d`, fixture Native **377**, source `actor:18:wp:377` và canonical `op:wp:377`, citation `/work_packages/377`. Các thời điểm sau là **ICT,29/10/2026**.

| Stage | Verified at | Native version / generation | Knowledge job |
|---|---|---|---|
|CREATE V1|03:24:02|v0 /gen2|480404df-4f73-55bb-bfe4-6418f5660b1a|
|Description V2|03:24:43|v1 /gen3|bfd67d16-b59f-5b13-8d8b-5233acb2b93d|
|Comment-only, Owner scope|03:26:06|v1 /gen4|d66076a7-649c-5c3a-b883-bd36d0fbc784|
|Ollama recovery revision|03:26:59|v2 /gen5|3732ef88-b83f-5a50-b9ba-12541191b1fd|
|Qdrant recovery revision|03:28:08|v3 /gen6|316aa6f6-e491-5892-bc47-af661e7c220a|
|Gateway interrupted revision recovered|03:33:55|v4 /gen12|a2acc08b-ff77-5c18-a4ed-a7664adf6667|

- V1/V2/comment không gọi manual ingestion. Source hashes/updatedAt/activity hashes, scanner observation timestamps, every job state, FTS rows và citation revisions có trong JSON. V2 search không trả nội dung V1 đã cũ.
- FTS có2rows của fixture; vectors thực1024D, finalpoint IDs `15a3aabc-2a55-5e7b-aa71-04d58f9370f2`, `5332ebce-517f-55f9-8a74-833d3c53b55f`;0duplicate.
- PM19 có thể nhận canonical document được phép xem khi semantic query liên quan; không nhận actor18 snapshot hoặc private comment snippet. Test kiểm tra đúng source/content boundary, không đòi toàn bộ search phải rỗng.
- Local Supervisor run **4c0c1e86-5157-4cc9-8206-fbac81887a13**, final persisted lúc03:24:54; WF04 trả7event đúng run. Parent trace, server run/trace IDs và workflow execution records được nối trong evidence bằng fixture/source/version/run IDs.
- Local Supervisor đọc Native context hiện hành. Nhánh live Supervisor mới lắp RAG+Gemini context khi được cấu hình. Không mô tả local Native analysis như một model đã tiêu thụ RAG.
- Actual WF03 clone `plan` trả **HTTP503 /GEMINI_MULTI_AGENT_DISABLED**,0provider calls,0proposals. Không copy production Gemini secret hoặc reset quota để đạt PASS.

Vì vậy **chưa đạt `CONTINUOUS_CHANGE_TO_AGENT_E2E_PASS` với model thật**. Đây là external test configuration còn thiếu, không được ghép với hai MAIN live runs28/10 rồi coi là một lượt liên tục. MAIN live runs cũ vẫn là evidence riêng vì provider/Gateway source không đổi; không gọi model lại chỉ để tăng số liệu.

Các source của Native corpus nhập từ snapshot trong clone là text baseline; chỉ fixture mới được qualify đầy đủ vector. Không dùng clone thiếu baseline vectors để suy ra drift MAIN.

## C. Schedules và execution semantics

Production schedules giữ nguyên:

| Workflow | MAIN schedule | Actual clone repeated triggers |
|---|---|---|
|WF07 Daily Brief|08:00 Asia/Bangkok|9cycles từ03:24 đến03:33, READY5/5|
|WF12 Weekly Summary|Friday17:00 Asia/Bangkok|9cycles cùng khoảng, READY5/5|
|WF16 Monitoring|Mỗi15phút|9cycles cùng khoảng, durable bucket receipt|

Chỉ clone rút ngắn thành everyminute. Không bấm Execute để thay scheduled evidence. n8n restart có một phút không trigger; lần kế tiếp tiếp tục bình thường, không burst catch-up/replay. Mỗi workflow có tối đa một execution trong mỗi phút quan sát.

Daily/weekly collectors mỗi loại chỉ có **một durable receipt** theo day/week key dù workflow được đánh thức9lần; tổng2collector receipts, model0/proposal0. Weekly report giữ rolling7days/as_of_date; Monday key chỉ dedupe. Daily report là snapshot thời điểm thu thập, không hứa tự viết lại snapshot trong mọi phút.

Evidence JSON lưu từng execution ID, trigger timestamp, final status và receipt. Tổng31executions gồm27scheduled runs và các probe/trace. **30n8n technical success +1error không đồng nghĩa30business successes**:

- Legacy partial probe cố ý tái hiện false success cũ: HTTP200/PARTIAL nhưng n8n success.
- Candidate partial probe: HTTP500/n8n error đúng.
- WF03 đã hoàn thành route chuyển tiếp lỗi nhưng trả callerHTTP503; đó là **business/provider BLOCKED**, không phải live-Agent PASS.
- WF16 có thể hoàn tất công việc probe/persist với report DEGRADED; phải đọc report state, không dùng màu success của n8n thay tình trạng dependency.

**Sau Docker restart do người dùng thực hiện**, MAIN WF16 tự chạy execution2626 lúc03:15 và2627 lúc03:30, finished1/success. Không có agent global restart. Post-restart owner login và PM19token cũ đều authenticate được. Đây là bằng chứng Main scheduler/auth tự phục hồi; không là physical Windows reboot hoặc chủ động outage-test MAIN.

Post-patch WF07 MAIN08:00 và WF12 Friday17:00 chưa đến trong lượt này. Đã xác minh published/cron/auth wiring và clone business outcome; không manual trigger MAIN để tạo bằng chứng thay schedule.

## D. Fault injection và recovery

| Fault | Detection / durable state | Recovery và thời gian | Integrity / scope |
|---|---|---|---|
|Clone Ollama proxy trả503|Job retry, error persisted, không verified giả|Mở lại proxy; khoảng8,95s từ detected retry đến verified;52,80s toàn scenario gồm chờ auto scan|Jobattempt2, actualMainOllama không dừng|
|Pause clone Qdrant|Job retry, vector pending không thành verified|Unpause; khoảng13,98s từ detected retry đến verified;68,69s toàn scenario|Jobattempt2; deterministic currentpoints không trùng|
|Restart clone Gateway trong embedding call|Claim đang running giữ lease vàdurable source/job|Đợi lease300s thật; verified03:33:55, khoảng311s từ pre-restart observation,~13,5s sau lease expiry|Cùng job IDattempt2; không sửa clock/lease bằngSQL|
|Restart clone n8n|Published IDs/versions vàhistory snapshot trước/sau|Restart hoàn tất khoảng12s; các phút kế tiếp tự trigger|HMAC/credentials đọc được; receipts cũ giữ; không replay missed minute|
|Gemini timeout/quota/provider503|Targeted fresh unit tests dùng MockTransport|Bounded budget/terminal error/role revalidation PASS|Không phải live provider fault injection; noMainquota manipulation|

Unknown Native-write interruption không được inject lại trên MAIN hoặc trong read-only restart scenario này. Guard không replay có targeted unit/process tests và prior unchanged qualification; không tuyên bố đã làm một Native commit-under-restart drill mới.

Monitor cache vẫn15phút, nên không hứa bắt mọi outage ngắn giữa hai probes. Knowledge worker ghi retry/error của hai dependency faults. Existing WF16 fault-detection qualification28/10 giữ nguyên, không cần viết lại monitor.

## E. Source fix và deployment

**Root cause duy nhất cần production patch mới:** WF07 kết thúc ở HTTP collector; collector trả200/PARTIAL hợp lệ khi thiếu role/dependency, nhưng không có business validator sau đó nên n8n báo success. Red test fail trước sửa; actual n8n old/candidate contract probes xác nhận khác biệt.

Thay đổi trong `openproject/ai/`:

- `automation/deploy_real_n8n_workflows.py`: thêm `daily_business_result` sau node report, yêu cầu `COMPLETED/READY`, giữ payload nếu đạt. Không đổi collector, role, HMAC, cron hoặc schema.
- `tests/test_daily_workflow_finalization.py`: chạy generated Code bằng Node, reject partial/running/failed/null; kiểm tra connection.
- `automation/automation_stability_qualification.py`: reusable bounded real-clone harness cho auto change, schedules, failures vàrestart. Addon provider/trace probe đã chạy riêng cùng clone7; source hiện tích hợp addon vào lần chạy sau để không cần sidewatch.
- `tests/automation_dependency_proxy.py`, `tests/automation_schedule_setup.js`, `tests/automation_provider_and_trace_probe.js`: clone-only fixed-route outage/HTTPcontract fixture, private n8n bootstrap, WF04/WF03/RAG concurrency checks.
- `architecture.md`, operator guide, README, UAT reference, current result/evidence và single checkpoint được cập nhật. Không Core/Gateway business code, dependency hoặc database schema change.

MAIN deployment **03:36:04 ICT**: WF07 `BpCQrGR866vg4BqQ`, published version **c2a7a82c-9af8-479e-8156-c1d07f64a533**,5→6nodes. Năm node cũ/old connections/auth/retention giữ nguyên; chỉ nối thêm guard cuối.15workflow khác nodes/connections/settings/active versions khớp baseline. SourceSHA256 `5dfbb7aeb0e01de16581cae744cee6e7222f4d8066237a63f60fa6811fac19f1`.

Fresh PG/SQLite+n8n/assets snapshots đã PASS trước patch, private deployment directory giữ before/candidate/after/manifest. Không build hoặc restart Gateway/Core/n8n; mọi MAIN container IDs/images giữ nguyên. Gateway vẫn `sha256:eaaa1217ac79cfac4747e0fa71af40bf0d3c1a447f39e6cc24dc20e55a268fc4`, Core08df5e2b, n8ndd580fe1.

Rollback: PATCH đúng name/nodes/connections/settings từ private WF07-before.json, publish version mới rồi readback original5nodes/cron/retention và các workflow khác. Không restore DB, không đổi image hoặc xóa history. Không thực hiện rollback trên MAIN để thử.

## F. Regression và bounded endurance

| Nhóm | Passed | Failed | Skipped | Loại evidence |
|---|---:|---:|---:|---|
|Daily/weekly/workflow/finalization|27|0|0|Generated node thực thi bằng Node +targeted unit contracts|
|Provider/queue/lease/process/monitor|10|0|0|Targeted fresh units/process recovery, provider mocked|
|Qualification7|PASS|0|n/a|Real Core/PG/Gateway/Qdrant/n8n/BGE-M3; provider blocked rõ ràng|
|Provider/trace/RAG addon|PASS|0|n/a|Same clone/source/run; WF04actual, WF03returns503,3parallelRAGreads|

Compile Python, Node syntax và tracked git diff check đã chạy. Không chạy lại toàn bộ historical suite hoặc28subsystem audit. Sáu lượt harness failed/aborted trước được giữ nguyên, không tính PASS: health probe repr/Host, SQL quoting, aborted old code process, sai assertion đòi semantic result rỗng, và bootstrap fetch failure. Assertions được sửa để bám đúng source/content ACL; không giảm Native permission/hash/version guards. Bootstrap sau import hiện đóng kết nối idle, refresh readiness và lưu request stage/error cause; không blindly retry POST mutation. Không coi transient bootstrap failure chưa đủ root cause là production n8n defect.

Số đo clone13phút, Gateway1CPU/384MiB:

- 12Native reads, concurrency3, tất cả thành công; min3,83s /mean7,42s /max10,91s, gồm Docker probe overhead.
- 3parallelRAGreads, mỗi request một attempt:16,65–18,27s; không suy ra latency MAIN hoặc20-user SLO, không tối ưu mù bằng tăng query rate.
- Gateway sampled107,4→86,16(sau restart)→128,4MiB; n8n533,4→162,4→406,2MiB; Qdrant84,06→90,76→92,16MiB. Đều trong limits;3samples không chứng minh không memory leak dài hạn.
- n8n SQLite base file2.420.736→2.633.728bytes (+212.992bytes); WAL/SHM không nằm trong initial byte count, không gọi đây là tổng disk growth.
- Final6knowledgejobs verified, no runaway retry/DLQ;2currentpoints1024D/0duplicates. Restarted job chỉ tăngattempt1→2. Read-only/model0/proposal0 không là proof mọi Native mutation fault đã thử.
- Không24-hour soak, stress20users, globalrestart bởi agent hoặc fullDR.

## G. MAIN preservation, startup và observability

Final preflight **PASS_READ_ONLY_PREFLIGHT**; snapshot cuối không có n8n execution running/new/waiting: active0,441docs/2027chunks/2030points; registered source không missing/stale/hash/payload/FTS drift. Đúng3protectedlegacypoints giữ nguyên, status PARTIAL_UNMATCHED_POINTS được giải thích theo contract; không xóa để đổi màu.

Five Native/business/password table fingerprints khớp baseline:376WorkPackages,352relations,1695customvalues,1027journals,7password rows. WP376test2/v0NEW, Bug371/v4IN ANALYSIS, QA fc0479a8-b30a-5e88-9e4a-10748cb30415 pending_qa được giữ.29historical unresolved requests không replay hoặc sửa; unknown hash giữ nguyên. Agent không Native business write, QA decision, Staging operation, globalrestart, volume delete hoặc publicport.

Người dùng đã restart Docker toàn cục; những stack khác có thể tự restart do chính hành động đó. Agent chỉ đọc/kiểm tra và triển khai phạm vi MAIN, không tuyên bố Staging không hề đổi StartedAt.

Startup hiện hành: Docker Desktop có HKCU Run entry; MAIN containers `unless-stopped`; Gateway lifespan tự bật workers; n8n khôi phục active schedules. Hai Windows tasks `QLDAPM-Ollama-Health`/`QLDAPM-Main-Daily-Backup` Ready, result0, action `-WindowStyle Hidden`, principal limitedinteractiveLUIM. Ollama mutex/listener check và hidden daemon launch có sẵn, không thêm startup mechanism trùng. Chưa quan sát physical reboot/pre-login; không cần mở PowerShell thủ công để hai task chạy trong session phù hợp.

Quan sát dùng existing surfaces: scanner status/generation và sync job status/error; own run/trace/context/version; n8n Executions và structured business result; Control Center/local delivery metadata; private backup last-success/last-attempt và TaskScheduler. Không thêm dashboard, không gọi LLM cho health checks. Main post-restart PMtoken/ownerlogin và naturalWF16triggers chứng minh authentication/schedule vẫn dùng được.

## H. Limitations và handoff

- Fresh continuous clone Native-change→liveGemini cần credential/config thử nghiệm được cấp hợp lệ hoặc provider mechanism được phê duyệt; không gửi key qua chat, không copy production secret hay bỏ quota guard. Local/split evidence chưa thay gate này.
- Windows interactive login +Docker availability vẫn cần; **PHYSICAL_REBOOT_NOT_QUALIFIED**. User Docker restart recovery có evidence riêng.
- External SMTP/chat chưa cấu hình/authorized destination; không gửi thông báo ngoài. Local metadata delivery giữ nguyên.
- Không fullQdrant/cross-service DR hoặc production restore; fresh predeploy backup là individual consistent snapshots.
- Bounded comments latest20/750char snippets, full sanitized freshness hashes; edits/clear có thể~11phút ở339WPs. Không OCR/arbitrary attachment crawler mới.
- Cron không tự replay missed schedules hàng loạt; daily/weekly snapshot dedupe không bị biến thành continuous rewrite. Future MAIN08:00/Friday17:00 executions chưa được gắn PASS trước thời điểm chạy.
- Human UAT vẫn PENDING theo [checklist](OPERATOR_UAT_SPECIFICATION_AND_CHECKLIST.md). Backend/clone evidence không là human approval.

Các phần kỹ thuật an toàn thực hiện được đã hoàn tất: actual defect fix, repeated schedules, controlled recovery, bounded endurance, affected regression, snapshots, minimal publish và runtime preservation readback. Khi có test-provider configuration hoặc human UAT findings, tiếp tục đúng nhánh còn thiếu; không replay Main fixtures, không sửa dữ liệu để tạo PASS.

Delivery QA:6source hashes vàprivate evidence hashes khớp;7tài liệu hiện hành được kiểm tra links/exact secret material với0matches. Git HEAD giữ nguyên, tracked diff check PASS; không còn container clone gắn nhãn của phiên.

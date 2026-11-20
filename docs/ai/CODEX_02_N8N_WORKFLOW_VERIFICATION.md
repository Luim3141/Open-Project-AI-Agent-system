CURRENT MAIN — 2026-10-26T08:04:33.762688+00:00: Gatewayb2f2db56/Coree0a840b5; trusted Native delete contract deployed with empty ledger. Fresh518Windows/503Linux+15skips/15Ruby;73roles/48contracts/13readonly/40new delete policy checks PASS.338visible/375physical/original332/#370v2/security/history preserved. No Main Native write/human decision/model call. Full release PARTIAL; read CODEX_FINAL_REGRESSION_RELEASE_GATE.md and CODEX_MAIN_CONTINUATION_CHECKPOINT.json. All sections below are historical evidence.

CURRENT MAIN WEB — 2026-10-25T03:13:28.471356+00:00: Core Web `sha256:1bbe160472068a64d3a965fe2bbbd280c2095d17ce285785a3ad0df40825a61f`, Gateway `sha256:c0f328216654478cb58dc01dad737958416882f0352c450a0ae5a80438ca6372`. Chỉ1controller file được bổ sung wbs_from_ba/QA capture/read/prepare vào route và selector theo role; Gateway cùng9container Main khác giữ nguyên ID/image/start. QA review vẫn là endpoint human review riêng, không có qa_review/qa_pass AI command.6Ruby programs PASS, gồm actual controller6roles,42valid/42wrong-role edges, ActionView/XSS và signed test receipts. Postdeploy48contracts/73roles/13read-only/Native375/oldtree/RAG/fullNative-security preservation PASS. Không thêm Native write hoặc model call. New visual selector human UAT PASS: người dùng xác nhận Owner thấy wbs_from_ba/qa_evidence_get/qa_transition_prepare và không thấy qa_evidence_capture; không chạy browser automation hoặc gửi lệnh. Evidence: CODEX_OWNER_NEW_TOOLS_HUMAN_UAT_RESULT.json. Current full release PARTIAL. Các image Core dcb60182 bên dưới là bằng chứng trước Web-only delta này.

CURRENT — 2026-10-24T22:17:45.531409+00:00: Gatewayc0f32821/Core dcb60182, Main338 (#375v0 exact approved create; old337 unchanged),433Windows/421image+12platform,48contracts/73roles/36QA/13read-only PASS. Overall PARTIAL. See CODEX_FINAL_BUSINESS_ACCEPTANCE_REPORT.md and current checkpoint. All sections below are historical unless explicitly current.

Cập nhật hiện hành 2026-10-24T14:33:05.542398+00:00: Gateway `sha256:21ad074d2b51a9332850986a1673ffc894a99d8a99707ecef1f1445996a0e724`, Core `sha256:dcb6018226280bde73fb8812e463bdcb5ef6896cbe9a1c65be7516d993f4a3d4`; Main337, original333 exact rows/#370v2 giữ nguyên. Owner supported access và actual3-level Native tree/RAG PASS; overall PARTIAL. 374Windows/367image+7Node skips;48contracts/73role/13finalread-only PASS. Xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json và CODEX_FINAL_REGRESSION_RELEASE_GATE.md trước các đoạn lịch sử bên dưới.

<!-- CODEX_CURRENT_STATUS -->
Trạng thái hiện hành và giới hạn nghiệm thu: xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json, CODEX_SCENARIO_F_RESULT.json và CODEX_MAIN_WORKFLOW_ACCEPTANCE_MATRIX.json trong docs/ai. Các số liệu/candidate bên dưới là lịch sử.
<!-- END_CODEX_CURRENT_STATUS -->

# Codex — n8n Main workflow verification

**Status: FAILED cho nghiệm thu đủ16 workflows; candidate P0 PARTIAL.** Runtime n8n2.43.6;16 workflow active. Đã đọc nodes/connections/settings/version và lịch sử execution trực tiếp Main bằng SQLite read-only trong chính container; không sửa DB n8n. Tất cả16 live nodes khác file `workflows_main_bundle/all_16_workflows.json` trong repo.

| WF | Quan sát source/runtime Main | Phần chưa đạt |
|---|---|---|
| 01 | Gọi knowledge_ingest, default WP38; không dùng file_path thật | Document ingestion/embeddings/readback |
| 02 | List WP rồi ingest cứng38 | Event source ID, updates/deletes, stale removal |
| 03 | Gọi ai-runs, mặc định local supervisor | Không tự chứng minh Gemini/RAG/specialists đầy đủ |
| 04 | GET trace tồn tại | Không phải event ingestion/tracking pipeline; đã chứng minh cross-actor leak |
| 05 | GET proposal; code trả APPROVED/REJECTED theo body | Không lưu decision; P0 candidate bỏ status giả |
| 06 | Shared PM + raw mutation + auto_execute; default38 | Bypass approval; P0 candidate chuyển exact Gateway decision |
| 07 | Schedule08:00 + webhook, gọi insights | Chưa chứng minh persisted daily report/notification từ cron |
| 08 | List WP và tính readiness | Chưa đủ sprint risk/deadline/dependency analysis |
| 09 | Query bug, phân loại kết quả | Thiếu duplicate/proposal/assign/fix/retest/review lifecycle |
| 10 | Get project options | Chưa phải WBS proposals + approved Native writes |
| 11 | Đếm checkbox AC từ WP | Thiếu acceptance evidence và QA gate thực |
| 12 | Workload Balancing | **Weekly Summary gốc đã bị mất** |
| 13 | knowledge_ingest | Chưa có verified-feedback promotion/reindex lifecycle |
| 14 | Webhook + code trả retry/DLQ flags | **Không queue, không persistent DLQ, không retry/recovery thực** |
| 15 | Đọc OP/Qdrant counts, gắn constants326/1713/23/3 | **Không đối soát identity/hash/version; drift=false cố định** |
| 16 | Schedule15m + insights, health/KPI flags cứng | Thiếu probe Ollama/Qdrant/resources/backlog/embedding thực |

Không workflow nào có node `retryOnFail=true` ở snapshot live. Settings không chứng minh error workflow đầy đủ. Execution success cũ chỉ xác nhận engine chạy nodes đó; các output flags không chứng minh business side effect.

Changed source: `automation/deploy_real_n8n_workflows.py`; tests `test_takeover_workflows.py`. Candidate harden từ live snapshot, giữ workflow IDs/names và nghiệp vụ hiện hữu ngoài WF05/06; tắt cronWF07/WF16 vì không cấp cron Bearer người dùng. JSON candidate/private snapshot và hash ở deploy preview. Không deploy generator stub cũ.

Evidence thực chạy mới: negative ingress WF05 và cross-actor read WF04 (xem CODEX_01). Chưa kích hoạt các luồng ghi/ingest còn lại để tạo PASS. Test command: `python -m unittest tests.test_takeover_workflows -v` — static regression PASS, không gọi live n8n.

Next action: phê duyệt containment/P0; sau đó sửa từng workflow theo contract gốc và persisted side effects. Rollback giữ ingress/mutation bị khóa, không bật lại shared PM credential. P1 implementation và live execution gates còn BLOCKED/PENDING.


## WF04–WF06 response and lifecycle correction candidate

Sau khi Gateway sync image `99769ead...` được deploy và readback, candidate n8n chỉ sửa ba workflow Main. HTTP Request lấy full response và không throw cho HTTP 4xx/5xx; Respond to Webhook chuyển nguyên status/body đã được Gateway xác thực. Đây không phải bỏ authorization: request không hợp lệ vẫn bị Gateway từ chối. WF05 chỉ đọc stored proposal/lifecycle; WF06 chỉ chuyển exact decision/hash, không nhận raw Native command. Native write retries vẫn tắt. 5 source/Node.js formatter tests PASS; live workflow tests đang chờ deploy. Rollback: restore ba workflow snapshot trước sửa, activate version mới và read-back. Không đổi credentials hoặc Staging.


## Exact RAG reconciliation API / WF15 candidate

Source thêm `knowledge_integrity.py` và action PM-only `knowledge_integrity`, cùng VectorClient project-scoped scroll có deadline30s/bound10000 points. Audit giữ ingestion lease, so Native IDs/lockVersion, source hash, chunk hash/UUID, exact payload và FTS cardinality; không sửa/xóa corpus. WF15 chuyển caller Bearer tới action này và trả nguyên trạng thái audit thay vì số tổng cố định. Candidate audit đọc Qdrant Main thật và SQLite clone: 360 docs/1709 chunks/1712 scoped points, không missing/hash/payload/version/FTS lỗi, ba unmatched points. Trạng thái đúng là PARTIAL_UNMATCHED_POINTS; không được sửa thành VERIFIED chỉ để tổng số bằng nhau. Chưa deploy candidate ở checkpoint này. Rollback Gateway về image sync `99769ead...`, restore snapshot riêng WF15; không restore dữ liệu cho code rollback.


## Durable operational reports candidate

`operational_reports` trong Gateway SQLite lưu report do server tạo, actor/project scope, Native ID/version references và SHA-256; nội dung/reference giống nhau dùng cùng report ID. WF15 API response sẽ có report_id/report_sha256 để đọc lại bằng `get_report`. Hash bị đổi thì không trả evidence; actor/project khác bị chặn; đổi vai trò hoặc mất Native visibility thì ẩn content; source set/version đổi được đánh dấu historical. Không có endpoint upload report arbitrary và không lấy report cũ làm trạng thái live. Đây là additive table riêng, không migration PostgreSQL/Native. Năm regression tests PASS; candidate chưa deploy. Rollback về Gateway image integrity `d006b57e...`, giữ bảng report/queue.


## WF12 Weekly Summary / truthful status metrics candidate

Root causes: WF12 bị thay bằng workload detection; weekly_report suy close transition từ updatedAt, cửa sổ inclusive8ngày và coi percentageDone100 là closed dù statusNEW. Source sửa hai shared status helpers (sprint_report/pm_agent) và Service.analyze để dùng trạng thái Native; weekly window7ngày theo Asia/Bangkok, bỏ future update, không tự suy throughput. closed_this_week/throughput_velocity giữ key nhưng trả null với data_quality PARTIAL_STATUS_HISTORY_UNAVAILABLE; closed_updated_in_window là proxy có tên rõ. Bốn legacy test assertions dựa vào updatedAt không hợp lệ đã được thay bằng kiểm tra proxy và null; ba regression mới tái hiện lỗi trước sửa. 34 tests cho weekly + các caller sprint/alerts/workload/readiness/PM PASS.

Action weekly_summary đọc Native bằng caller thật, không model call, lưu report có hash và scope. WF12 candidate đổi đúng tên Weekly Summary/path qldapm-weekly-summary; chỉ forward as_of_date, không actor/role/user_id/model consent. Snapshot không tái dựng lịch sử trạng thái; chưa có Native status-transition history thì không được gọi đây là throughput tuần đã xác minh. Gateway/core UI không có binding trực tiếp vào các field numeric cũ qua Ruby/ERB/JS search. Candidate chưa deploy; rollback image reports b1bfce67..., snapshot WF12 trước sửa; giữ dữ liệu report.


## WF08/WF12 deployed readback — 23/10/2026

WF12 Weekly Summary đã deploy (e70f3bb7 ancestor), PM/BA báo cáo200 và persisted readback đúng SHA256; closed_this_week/throughput_velocity giữ null, không dùng updatedAt làm closure time. WF08 Sprint Risk hiện deploy trên Gateway9dcba73f; Native332WP/344relations (343follows/1relates). Sáu regression accuracy tests và43related Windows testsPASS; Linux177run/176PASS/1Node skip, Node formatterPASSWindows. Bản fixture Sprint Report trước đây dùng mô tả tự do “Chờ API...”; đổi thành explicit blocked declaration để phản ánh contract mới, không lấy mọi #ID làm blocker. Các probe lỗi ban đầu là verifier accessor hash→sha256 và expected malformed-date400→actual422; đã sửa verifier và chạy lại, không thay Gateway status để ép PASS.

LiveWF08PM200:22overdue/0blocked/264visible dependency rows. BA200:4ownoverdue/0blocked/105owndependency rows. Bearer thiếu401, transport thiếu403, malformeddate422, BAđọcPMreport403. Reportpersist/readbackSHA256 và Native332ID/lockVersion fingerprint không đổi. Không Native write/model call/Staging. Đây là CURRENT_VISIBLE_PROJECT_WORK_PACKAGES snapshot; chưa chọn Sprint Native, heuristic không phải dự báo. Old report không revalidate relation changes. Evidence: CODEX_SPRINT_DEPLOYMENT_RESULT.json, CODEX_WEEKLY_DEPLOYMENT_RESULT.json. Rollback previousweeklyimage và privateWF08snapshot; giữ report data.


## WF03 deployed Native route / persisted polling

Evidence CODEX_WF03_DEPLOYMENT_RESULT.json:9livechecksPASS, stableUUIDrequest replay cùngrun, persistedpoll200, crossactor403, validation422 vàingress401/403. Source/Node9testsPASS. Không còn timestamprequestkey/defaultprompt/localSupervisor mặc định, không formatSUCCESS giả. Contract mới start cầnprompt+request_idUUID; status cầnoperation=status/run_id. Không forward actor/role/writeconsent. Chưa freshGemini/sixrolechain; providerreceipts96/usage101 giữ nguyên, Native332WP không đổi. Một verifier dùng sai nestedresult ởstartreceipt đã sửa theo contract thực; không sửa app để épPASS.


## WF14 durable RAG recovery deployed

ActiveWF14ID8ycOUQy9gtT60nkN/versione07912bb-c40c-4e18-a016-2f16ff7a38a1; jobUUID+callerBearer nhậnGatewaydurablestate, retrycầnrequestUUIDvàownDLQ. Khôngcònaudit_logged/retry_scheduleddoJSONtựkhai.10source/Node+7SQLiteAPIrecoverytestsPASS;8livevalidation/denialPASS (403opaqueunknownjob,422missingrequest/native_retry/invalidjob/legacyclaimedstate,401/403ingress). Mainoutbox0,khôngtạoMainjobgiả/khônggâyoutage;khôngclaimpositiveMainDLQretry. CODEX_WF14_DEPLOYMENT_RESULT.json;rollbackprivatesnapshotWF14,giữGatewayqueue/receipts.

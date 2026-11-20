> Current Main 2026-10-26T12:26:49.046792+00:00: Gatewayffe20cad/Core545e498a/WF10142d0a0d-0c12-4b6d-b1f5-c91033fc854e. Registered-only vector pruning and explicit WBS relations deployed/qualified.581Windows/566Linux+15skips;73roles/48contracts/13readonly/38hierarchy/6QAreads + unchanged canonical42 smoke PASS.1731points incl3legacy, Native/history unchanged. Full release PARTIAL; see CODEX_RAG_REGISTERED_PRUNING_FINAL_READBACK.json and CODEX_FINAL_REGRESSION_RELEASE_GATE.md. Older milestones below are historical.

CURRENT MAIN — 2026-10-26T08:04:33.762688+00:00: Gatewayb2f2db56/Coree0a840b5; trusted Native delete contract deployed with empty ledger. Fresh518Windows/503Linux+15skips/15Ruby;73roles/48contracts/13readonly/40new delete policy checks PASS.338visible/375physical/original332/#370v2/security/history preserved. No Main Native write/human decision/model call. Full release PARTIAL; read CODEX_FINAL_REGRESSION_RELEASE_GATE.md and CODEX_MAIN_CONTINUATION_CHECKPOINT.json. All sections below are historical evidence.

<!-- QA_REVIEW_UI_CURRENT -->
## Main human QA review — 2026-10-25T03:36:33.562329+00:00

**Scoped deployment PASS; full release PARTIAL.** Gateway `sha256:8c91c1c0ae3edf754615b302575d093fa45b5257ffa0b86f84d7872830a3c3ec`, Core Web `sha256:175c337834cabb5e56689432cbb913e5dc4ef622d77b7e3e49d16333cdab85e2`. AI Assistant → AI Control Center → **Bằng chứng QA / Kiểm duyệt** opens the separate human review page. User confirmed the page/ID input/read button; final navigation button is qualified by actual ActionView six-role rendering, not a claimed browser click. PM/Owner review uses their own session, Rails CSRF, signed nonce, fresh Native identity, independent reviewer, exact source/hash and one-decision CAS. QA reads/captures their own evidence; BA/BE/FE and other Admins gain no approval authority. There is no review AI/MCP tool and no automatic Native write.

434 Windows tests,422 Linux tests(+12 platform cases passed on Windows),8Ruby programs,73role API checks,48contracts,13read-only checks and10signed bridge negative checks PASS. All67 serving Gateway sources and5changed Core templates/controller/routes match workspace. All375 physical WP rows and338Main versions remain exact;370v2 unchanged. ScenarioF consumed row/61audit rows/original RAG report, old history IDs and two unknown request rows are retained. No new provider receipt, proposal, QA decision, Native write, credential change or Staging operation. RAG338IDs/373docs/1728chunks/1731points remains consistent; three historical excluded points retained.

Actual371 next Native edge is NEW→IN ANALYSIS, not NEW→REVIEW. Existing Core policy still requires story, AC, scope evidence and scope approval; current records are empty. No evidence or approval was invented. Genuine Main QA production/independent review/valid closure remains incomplete, along with versioned Native dependency writes, trusted deletion and full recovery. See [qualification](CODEX_QA_REVIEW_UI_QUALIFICATION.json), [runtime preservation](CODEX_QA_REVIEW_UI_FINAL_READBACK.json), [Native readiness](CODEX_WF11_CURRENT_NATIVE_READINESS.json). Roll back only exact previous service images/config; retain current databases and prior fixes.
Typed decision input validation was separately regression-tested and deployed Gateway-only; no policy weakening. QA23 currently advertises comments but no attachment upload link; the V1 producer gap and proposed alternative are recorded in CODEX_WF11_QA_PRODUCER_CAPABILITY_RESULT.json and CODEX_WF11_NATIVE_QA_PRODUCER_DESIGN_PREVIEW.md. No upload/write was attempted.
<!-- END_QA_REVIEW_UI_CURRENT -->

CURRENT MAIN WEB — 2026-10-25T03:13:28.471356+00:00: Core Web `sha256:1bbe160472068a64d3a965fe2bbbd280c2095d17ce285785a3ad0df40825a61f`, Gateway `sha256:c0f328216654478cb58dc01dad737958416882f0352c450a0ae5a80438ca6372`. Chỉ1controller file được bổ sung wbs_from_ba/QA capture/read/prepare vào route và selector theo role; Gateway cùng9container Main khác giữ nguyên ID/image/start. QA review vẫn là endpoint human review riêng, không có qa_review/qa_pass AI command.6Ruby programs PASS, gồm actual controller6roles,42valid/42wrong-role edges, ActionView/XSS và signed test receipts. Postdeploy48contracts/73roles/13read-only/Native375/oldtree/RAG/fullNative-security preservation PASS. Không thêm Native write hoặc model call. New visual selector human UAT PASS: người dùng xác nhận Owner thấy wbs_from_ba/qa_evidence_get/qa_transition_prepare và không thấy qa_evidence_capture; không chạy browser automation hoặc gửi lệnh. Evidence: CODEX_OWNER_NEW_TOOLS_HUMAN_UAT_RESULT.json. Current full release PARTIAL. Các image Core dcb60182 bên dưới là bằng chứng trước Web-only delta này.

CURRENT — 2026-10-24T22:17:45.531409+00:00: Gatewayc0f32821/Core dcb60182, Main338 (#375v0 exact approved create; old337 unchanged),433Windows/421image+12platform,48contracts/73roles/36QA/13read-only PASS. Overall PARTIAL. See CODEX_FINAL_BUSINESS_ACCEPTANCE_REPORT.md and current checkpoint. All sections below are historical unless explicitly current.

Cập nhật hiện hành 2026-10-24T14:33:05.542398+00:00: Gateway `sha256:21ad074d2b51a9332850986a1673ffc894a99d8a99707ecef1f1445996a0e724`, Core `sha256:dcb6018226280bde73fb8812e463bdcb5ef6896cbe9a1c65be7516d993f4a3d4`; Main337, original333 exact rows/#370v2 giữ nguyên. Owner supported access và actual3-level Native tree/RAG PASS; overall PARTIAL. 374Windows/367image+7Node skips;48contracts/73role/13finalread-only PASS. Xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json và CODEX_FINAL_REGRESSION_RELEASE_GATE.md trước các đoạn lịch sử bên dưới.

<!-- CODEX_CURRENT_STATUS -->
Trạng thái hiện hành và giới hạn nghiệm thu: xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json, CODEX_SCENARIO_F_RESULT.json và CODEX_MAIN_WORKFLOW_ACCEPTANCE_MATRIX.json trong docs/ai. Các số liệu/candidate bên dưới là lịch sử.
<!-- END_CODEX_CURRENT_STATUS -->

# Codex — Test evidence và acceptance gates

**Status: PARTIAL. Full E2E BLOCKED.** Không gọi unit/static tests là live E2E.

## Kiểm tra thực chạy

- Hai regression RED trước fix: auto_execute không cần approval; altered stored payload vẫn execute. Sau fix security regressions PASS.
- **90 tests Windows PASS**, **76 tests Linux candidate PASS**. Container Linux chạy `--network none`, không mount state/business/secrets, read-only root, synthetic Native/provider fixtures. Log các URL Google trong unit tests là MockTransport, không phải provider calls thật.
- **90 tests legacy trong10 modules bị đánh dấu BLOCKED/SKIPPED** vì dùng Main state, token issuance, business WP38 hoặc production Qdrant collection. Không xóa assertions và không cộng chúng vào số PASS. Chúng chưa được chuyển toàn bộ thành safe controlled E2E.
- Live read-only: Native identity/project332 WP, SQLite+Qdrant exact payload reconciliation, Ollama embed1024/Docker connectivity/GPU, Gateway retrieval1/3Hit@5, missing webhook secret403, BA direct trace403 nhưng qua n8n200.
- Backup consistency: Gateway/knowledge/n8n SQLite backup API; cả 3 quick_check OK. Chưa full Main restore.

Từ `openproject/ai`, chạy Windows (PYTHONPATH trỏ workspace root):

```powershell
$env:PYTHONPATH = (Resolve-Path '../..').Path
./.venv/Scripts/python.exe -m unittest tests.test_takeover_security tests.test_takeover_workflows tests.test_gateway tests.test_level2 tests.test_business_lifecycle tests.test_supervisor tests.test_native_create_recovery tests.test_business_acceptance tests.test_knowledge_storage tests.test_knowledge_search tests.test_knowledge_ingestion -q
```

Linux chạy8module đầu trong candidate image với `/app/tests` và `/app/automation` read-only, `QLDAPM_AI_RUNTIME=` và `--network none`. Exact candidate image và source hashes trong deploy preview; logs riêng `linux-security-tests.log`, `windows-security-tests.log` trong snapshot operator.

## Mapping20 nhóm yêu cầu

| # | Nhóm | Kết luận hiện hành |
|---|---|---|
| 1 | Ollama embedding | VERIFIED1024/GPU/connectivity; không benchmark đại diện |
| 2 | Qdrant persistence | Payload live có; chưa restart/restore test mới |
| 3 | Document ingestion | Existing data; ingestion mới/roundtrip chưa test |
| 4 | OP source ingestion | Đủ332IDtrong corpus; chưa fresh ingestion |
| 5 | Incremental update | FAILED consistency: stale/missing vector |
| 6 | Delete propagation | Source có; live BLOCKED, không xóa data |
| 7 | ACL | Fixture boundary PASS; live n8n cross-actor FAILED |
| 8 | Hybrid retrieval | FAILED production wiring; Gateway chỉ lexical |
| 9 | Multi-Agent | Persisted live QA receipt; chưa full role-specific chain |
| 10 | Native read | VERIFIED actor 19/project5/332 WP |
| 11 | Controlled write | BLOCKED chờ test resource được duyệt |
| 12 | RBAC denied | Direct trace403; fixture mutations denied; n8n bypass FAILED |
| 13 | Optimistic locking | Fixture PASS, live mutation chưa chạy |
| 14 | Idempotency | Fixture replay/response-loss PASS; chưa full live |
| 15 | n8n execution | Live read security probes; business16 WF FAILED/PARTIAL |
| 16 | Approval lifecycle | Candidate fixture PASS; live deployment BLOCKED |
| 17 | Bug lifecycle | Chưa full implemented/accepted |
| 18 | Gemini429/503/timeout | Offline fixture coverage; không gây outage Main |
| 19 | Ollama/Qdrant failure/recovery | Task existing-listener PASS; chưa kill/outage/restore |
| 20 | Full E2E readback+RAGsync | BLOCKED, không cấp GO |

Scenarios A–F: A có partial read-only/persisted evidence; B/C chưa full business lifecycle; D chưa có cron→persist→notification proof; E chỉ fixture failure paths; F cần separate test resource approval. Không đánh20/20PASS.

Changed tests: thêm `test_takeover_security.py`, `test_takeover_workflows.py`; cập nhật hai existing Native tests sang approved semantics; quarantine10unsafe legacy modules. Root causes và rollout/rollback trong CODEX_01. Không sửa assertion để che lỗi; import-path failures và bypass-dependent failures ban đầu đã được sửa và rerun như trên.


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

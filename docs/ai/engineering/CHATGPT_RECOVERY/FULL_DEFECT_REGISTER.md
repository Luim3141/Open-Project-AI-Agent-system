<!-- RUNTIME_RECOVERY_CURRENT_20261105 -->
# MAIN current — runtime recovery nghiệm thu

**AI_CONTROL_CENTER_DEMO_READY trong phạm vi đóng băng đã kiểm** (05/11/2026 UTC+7). Chỉ đạo Owner mới bỏ performance gate cũ. Các block bên dưới là lịch sử; các số revision44/531 và OpenClaw DOWN bên dưới không phải trạng thái hiện hành.

MAIN final: **desired/effective PAUSED, revision50, delegation OFF, queue0, Worker ALIVE, OpenClaw CLI/RPC READY**. Sáu WP386/387/389/390/391/394 vẫn READY FOR RELEASE/v10, run b7fd6aec (WP391) và WP394 succeeded, không replay. Project5/global13scopes hash PASS, không có thay đổi dữ liệu/config/security. RAG FAILED/FROZEN.

Đã triển khai host worker v2: idle health recovery khởi động installed OpenClaw service đang stopped, bounded CLI/RPC convergence; chung RLock với claim/fence và giữ claim nếu terminal fence lỗi. Task wake WSL bằng /usr/bin/true, không thêm orchestrator. Ba source hashes/rollback ở runtime-recovery/host-release.json. Core/Gateway/n8n image vẫn77213702/5ee7a244/05376355 (full hashes trong FINAL_TEST_RESULTS.json và final-live-verification.json).

Đã restart Gateway, OpenClaw user service (explicit stop và SIGKILL), n8n, coordinated10QLDAPMcontainers; state/volumes/16published workflows/4credential pins giữ nguyên. UI thấy DOWN/STALE rồi tự hồi phục; signed WF08 execution3827 ACKED và Native read-back thật. Full coordinated restart dùng v1; v2 ownership refinement đã qua host Task cold startup/CLI/RPC/container transport và40final focused tests.22role/provider contracts cũng PASS; các suite overlap, không cộng tổng unique.221regressions/57of70MAIN_UI bindings source không đổi được reuse theo Owner.

Sau restart MAIN UI đã kiểm RUN ONCE no-work/OFF/AUTO_IDLE/PAUSED, GitHub Sync12checked/0changed, report reader/Raw/Copy6834chars/Export7310bytes, Schedule read/close và F5/Back/Forward. Schedule Save/restore/Notifications persistence/zoom200% dùng unchanged prior MAIN evidence; không gọi clone là Main. UI Weekly Monday09:00 daemon Gateway độc lập WF12 Friday17:00 Asia/Bangkok; Save UI không đổi WF12.

Exactly1authorized isolated fixed-public provider smoke HTTP200,24tokens, receipt14674050-4230-4ef9-a81a-651ffddc9bba:533→534receipts; không có coding task/source/PR effect. Runtime/dashboard startup không gọi inference. Provider readiness hiện READINESS_STALE theo TTL300s, không AVAILABLE giả; coding admission mới vẫn phải qua provider gate. Revision47→50 do safe UI controls. Original38pending requests giữ nguyên;1new conservative no-work reservation có durable rejection, không manual SQLite completion.

**DOCKER_DESKTOP_RESTART_NOT_EXECUTED** vì Birdsong đang chạy; dùng fallback QLDAPM-only đã được Owner cho phép. WSL distro termination/Windows reboot và fresh live coding/active Resume/Cancel chưa kiểm; không chứng nhận các nhánh này. Có role contracts/RPC/local runner/existing delivery receipts và1isolated inference, không giả per-role live E2E. Không cần rerun coding/RAG/performance campaign.

Nghiệm thu20câu và case matrix: [runtime recovery acceptance](<D:/AI project/QLDAPM chat/docs/ai/engineering/CHATGPT_RECOVERY/runtime-recovery/ACCEPTANCE.md>). [Demo startup checklist](<D:/AI project/QLDAPM chat/docs/ai/engineering/CHATGPT_RECOVERY/runtime-recovery/DEMO_STARTUP_CHECKLIST.md>). Evidence runtime-recovery/final-live-verification.json, runtime-final.json, browser-uat.json và native-integrity-after.json. Bàn giao không yêu cầu thêm lệnh start worker/OpenClaw; nếu runtime chưa hội tụ thì giữ PAUSED, đọc lý do, không bật AUTO hoặc tự retry model để ép xanh.
<!-- END_RUNTIME_RECOVERY_CURRENT_20261105 -->

<!-- BUTTON_AUDIT_CURRENT_20261105 -->
# MAIN current — button audit, performance còn mở

Cập nhật 2026-11-04T23:27:06.261431+00:00 UTC,05/11/2026 Asia/Bangkok. **CORE_SAFE_ACTIONS_MAIN_VERIFIED — PERFORMANCE_GATE_OPEN; chưa AI_CONTROL_CENTER_DEMO_READY.** Block bên dưới là lịch sử.

MAIN Gateway `sha256:77213702ef933943a1fbee6feffc0d410062b8f16928dd3d1621f9489e581a12`; Core `sha256:5ee7a24482be81dd7312e8c4560773aede32ec9f8bc2f6da9593c9f223e1b822`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Exact source/images/health và221immutable tests +actual Native/Core clone verified. Core reuse đúng image đã qua Rails login/CSRF/template clone; không gọi fixture/unit test là MAIN UI PASS.

Actual source70button declaration sites:57MAIN_UI_PASS (instance đại diện),7CLONE_PASS_ONLY,4RAG SAFETY_NOT_EXERCISED,2server-toast NOT_TESTED. DOM cuối567buttons/302links/283summary/17fields =1169instances, không nâng mọi hàng lặp thành PASS. Main đã kiểm RUN ONCE no-work; OFF/AUTO_IDLE/PAUSED; GitHub ACK→COMPLETED/nochanges12/0 không F5; Schedule Daily/Weekly Save thật có restore; report toàn văn6766chars, Copy paste thật và Export7242bytes; Inspector5panels; modal/focus; tabs/F5/Back/Forward. Zoom200% được Owner xác nhận/DPR2.5, lỗi tương phản số trong schedule đã sửa trên Core cuối.

Final **PAUSED/revision44, delegationOFF, queue0**, workerALIVE;21coding runs/531provider receipts giữ nguyên. Daily08:00/WeeklyMonday09:00 restored; chỉ updated token đổi đúng theo Save. Native386/387/389/390/391/394 READY FOR RELEASE/v10;391/b7fd và394SUCCEEDED, không replay. Project5+global13hash scopes PASS, không data/config changes. Không coding admission, provider generation, GitHub push/merge, Mini Task Manager, DR hoặc RAG algorithm/qualification; semantic RAG vẫn FAILED/FROZEN.

Gateway30samples trước2.78145/23.1726s p50/p95 →final2.4294/5.8609s. CPU1→2 sau bằng chứng throttling, RAM384MiB giữ nguyên; schema setup cached sau commit tránh writer lock trên read. F5 vẫn chậm:9successful observations median8.076s(range6.309–11.588), final reload có tool timeout rồi phục hồi. Tab36tool-roundtrips median331.5ms không phải paint. Initial usable<4s/paint<200ms/ACK<2s và precise Rails/browser tracing chưa nghiệm thu. **OpenClaw Gateway health DOWN** dù workerALIVE; GitHub browser logged-out404/n8n signin nên chưa có authenticated content proof. Đây là các giới hạn cản chứng nhận demo.

Bằng chứng và16câu trả lời: [ACCEPTANCE.md](<D:/AI project/QLDAPM chat/docs/ai/engineering/CHATGPT_RECOVERY/button-audit/ACCEPTANCE.md>); matrix70buttons `button-audit/button-acceptance.csv`; runtime `button-audit/final-live-verification.json`; browser `button-audit/browser-uat.json`; controls `button-audit/main-control-readback.json`; integrity `button-audit/native-integrity-after.json`. Tiếp tục đo/tối ưu bottleneck có trace và kiểm OpenClaw readiness trong scope an toàn; không coding E2E/RAG qualification. One-shot automation đã xóa, không lên lịch lại.


Defects của đợt button audit (chưa coi các dòng OPEN là đã hoàn thành):

| ID | Severity | Defect | State/evidence |
|---|---|---|---|
| CC-BTN-01 |High|Schedule lost update/API allowlist/version forwarding|FIXED_MAIN: Daily/Weekly Save+restore, SQL CAS, actual Native clone|
| CC-BTN-02 |High|Turbo snapshot detached command submit; HTML POST remained /commands|FIXED_MAIN: pagehide/pageshow;303 canonical, exact Rails/Node/MAIN JSON Save|
| CC-BTN-03 |Medium|Reader actions enabled while loading/error|FIXED_MAIN: disabled→enabled,6766chars Copy/Export|
| CC-BTN-04 |Medium|Empty Run ID Copy was enabled|FIXED_MAIN: Supervisor disabled+reason; nonempty clipboard paste verified|
| CC-BTN-05 |Medium|Schedule input contrast/overflow at200%, modal keyboard focus|FIXED_MAIN: screenshot+DPR2.5, labels/scroll/Escape; Node Tab trap|
| CC-PERF-01 |P0|Warm initial usable/F5/tail latency|OPEN: Gateway30 p50/p95 2.4294/5.8609s; F5 6.309–11.588s observations; final tool timeout recovered|
| CC-PERF-02 |High|Warm schema initialization waited for writer lock|FIXED_IMAGE_MAIN: real SQLite held-writer RED→GREEN,221tests; end-to-end tail still open|
| CC-AVAIL-01 |Demo blocker|OpenClaw Gateway health DOWN while worker heartbeatALIVE|OPEN_OBSERVED: no inference readiness claim; regression origin not established|
| CC-UAT-01 |Coverage|Two server-toast branches and provider-backed side effects not MAIN exercised|OPEN_LIMITATION:57/70 MAIN bindings;7clone-only;4RAG excluded;2NOT_TESTED|
| CC-UAT-02 |External session|GitHub browser logged-out404/n8n signin|OPEN_LIMITATION: correct navigation verified, authenticated content not accepted; GH Gateway Sync reads12|

<!-- END_BUTTON_AUDIT_CURRENT_20261105 -->

<!-- CC_STABILIZATION_CURRENT_20261104 -->
# Control Center/Reports MAIN — functional repairs verified, performance open

Cập nhật 2026-11-04T16:22:32.919239+00:00 UTC (Asia/Bangkok,04/11/2026). **FUNCTIONAL_REPAIRS_VERIFIED — PERFORMANCE_GATE_OPEN**; chưa chứng nhận `AI_CONTROL_CENTER_DEMO_READY` hoặc FULL FUNCTIONAL PASS. Các block bên dưới là lịch sử.

MAIN: Gateway `sha256:698224aa0ddc88808ebab30b4705dfe7050b09db67b8ae3fc4a569d6a8447e1c`; Core `sha256:1a8f2528da78860faa69610568985471e26136d441a594f4f098c045ca181189`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Images/source/pins được read-back; Gateway/Core healthy, n8n readiness200. Final PAUSED, queue0, workerALIVE, delegationOFF;21coding runs/531provider receipts giữ nguyên. Project5 scoped rows và global config/security tables bảo toàn; chỉ cho phép timestamp đăng nhập User thay đổi.

Native386/387/389/390/391/394 đã READY FOR RELEASE/v10 qua workflow thật và journal của principal25; không tự DONE.391/b7fd và394 vẫn SUCCEEDED, không replay. PR11MERGED/main, PR12OPEN; Demo artifact giữ nguyên. RAG algorithms đóng băng/FAILED; provider readiness riêng, không coi workerALIVE là inferenceREADY.

Report Reader đã sửa trên MAIN: CSP nonce, Turbo cache restore, timeout15s, không ghi đè response cũ; Daily6766ký tự/6sections/Raw Markdown, audit có facts/provenance thay vì trang trống. GitHub Sync hiển thị ACK→operation→COMPLETED — NO CHANGES/12checked/0changed mà không F5. Artifact caption ghi rõ metadata lịch sử; trạng thái merge hiện hành lấy từ bảng PR.

Gateway HTTP5samples: trước p50=9.8377s/samplep95(max)=18.9763s; sau p50=7.2148s/samplep95(max)=12.8446s. Mục tiêu initial usable<4s chưa đạt; warm UI paint<200ms chưa có phép đo riêng. Core observed GitHub Sync ACK1913.38ms là một mẫu, không phải p95. Gateway hiện1CPU/384MiB, có sample saturation~100% khi đo. Không tăng quota hay đổi nơi lưu DB để che giới hạn. Cần tiếp tục tối ưu/read-path load qualification trước chứng nhận Demo Ready.

Bằng chứng: [runtime](cc-stabilization/final-live-verification.json), [166 image regressions](cc-stabilization/image-regression-reports.json), [exact clone qualification](cc-stabilization/clone-qualification-caption.json), [browser](cc-stabilization/browser-uat.json), [Project5](cc-stabilization/native-integrity-after.json). Không đổi GitHub source/merge, Demo, RAG algorithms hoặc DR.

Chi tiết18câu trả lời: [FINAL_INTEGRATION_ACCEPTANCE.md](FINAL_INTEGRATION_ACCEPTANCE.md); checklist: [OWNER_MANUAL_UAT_GUIDE.md](OWNER_MANUAL_UAT_GUIDE.md).
<!-- END_CC_STABILIZATION_CURRENT_20261104 -->

<!-- AUTONOMOUS_FINAL_CURRENT_20261104 -->
# Defects current

RESOLVED: delegated MAIN05/06 decision/execution,09validNative transition, distinctrealprincipal and defaultOFF/audit/UItechnicalintegration.

**Semantic RAG FAILED qualification; serving RAG không đổi.** B5 replay xác định SPAN_REFERENCE_MISMATCH (span10 thay vì5); offline unique same-source pointer repair vẫn không chứng minh answer. Typed FORMAT/SOURCE/SPAN/QUOTE/SUPPORT + bounded redacted captures giữ validator chặt.

Root corpus:11/15docs có JSON bị cắt, các business fields/boolean/path mất; whole-journal candidate giữ15docs/230073chars/117journals,906typedfacts, Unicode offsets/hash. Decode trước split, phân biệt Native fields, requirements và historical receipts. Research actual BGE/Qdrant906points + FTS/identity cho **DEV retrievalHit@5=13/13 (100%)**; đây là observed correlated DEV, không phải benchmark độc lập hay serving quality.

Final answer chưa đạt: six-case semantic-fact pilot strictsupport3/4positive, no-answer0/2negative emitted; một CRUD answer còn lẫn parent379/copied objective. Warm1.424–2.827s/cold16.406s. Expanded DEV dùng lại5cached pilot replies, chỉ3generation requests mới, dừng đúng gate ở warm5.944s>5s.4positive answers được quan sát, strictsupport2/4: hai câu “initial unit/create/list/SQLite” chỉ chọn unitname nên không đủ toàn bộ evidence.17candidate citations kiểm exacthash/offset/Nativeid/version không lỗi, nhưng quote identity không đồng nghĩa semantic support. RepresentativeFPR **NOT_ESTABLISHED**;0/2negative không chứng minh≤5%. Không mở oldholdout, không tạo/scoring lockedholdout khi DEV gate còn fail, không đổi gate để gọi PASS.

Current serving vẫn metadata retrieval/answer:null, NO_EVIDENCE hoặc UNVERIFIED_RETRIEVAL. Baseline observedDEV Hit2/13/FPR1/20 là lịch sử của serving baseline, không lấy candidate13/13 gán cho MAIN. Không có qualified RAG image hoặc postdeploy semantic E2E mới. Source-grade nghiên cứu không thay cho retrieval→evidence→answer→citation acceptance. Chỉ WP392 threeintents từng được Owner xác nhận; các nhãn khác là assistant source review, không gọi human ground truth. Lượt tiếp tục này11local4B requests,0Gemini mới, không tải/đổi model hoặc trả phí.

16/16published definitions/versions/hash được đối chiếu actualMAIN,14workflow ngoàiWF05/06 giữ nguyên. [Current matrix](autonomous-final/N8N_ACCEPTANCE_MATRIX.md) có caller/trigger/contract/side effect/retry/correlation/CC action và actual latest execution; original [wiring contracts](integration-final/n8n/WIRING_MATRIX.md) phía sau được xem là lịch sử tại các hàng05/06/09/14.

WF12publishedcron `0 0 17 * * 5`, timezoneAsia/Bangkok: thứSáu17:00, lần kế tiếp06/11/2026. DefinitionVERIFIED; compatible actual n8n scheduled-trigger clonePASS, signed collectors20–23 (19denied), reports/dedup/period contracts đã có proof và không đổi source/schedule. MAIN human webhook3359 READY/persisted report thật; không phải scheduled branch. Current-cycle wallclock **WAITING_FOR_SCHEDULE**; historical trigger2750/30-10failed được giữ rõ. Không đổi lịch production hoặc chờ nhiều ngày để đổi trạng thái.

WF14 source392: dùng lại failure attempt1→execution3393 WAITING_RETRY→verified attempt2→WF13 execution3394. Native392v0, hai documents/FTS/chunks/vectors riêng biệt và current citation `/work_packages/392` còn đúng. WF15 execution3660 tại lần đối chiếu recovery ACK/DRIFT_OBSERVED: không có missing/stale/hash/FTS/orphan lỗi; tám unmatched points đều thuộc WP385 đã xóa. Hai event DEAD lịch sử là WF13/WP385 và WF10/old plan b1cca031 chứa385; không force retry hoặc che lỗi. Pending events bằng0 tại readback. Execution mới nhất của từng workflow xem ma trận động và snapshot runtime. [Recovery/current index](autonomous-final/recovery-current-readback.json), [integrity](autonomous-final/index-current-integrity.json).

Essential FAILED: Semantic RAG complete-answer/evidence selection và worst-case latency/representativeFPR chưaqualified; candidate khôngdeploy, MAINsemanticE2E chưachạy. PUBLICATION_REDACTED_UAT: browser interactions/accessibility/loading/error/links; WAITING_FOR_SCHEDULE: current WF12 wallclock. Preserved partial:8WP385 unmatchedvectors/2historicalDEAD và persistedproviderREADINESS_STALE. Không tuyên bố FULL FUNCTIONAL DEMO READY.

Tiếp tục duy nhất có ích: sửa complete-evidence selection/parent-copy ambiguity và ổn định latency với gate5s giữ nguyên; đóng băng nguồn+code+broaderdevelopment/lockedholdout labels có source review trước khi score; chỉ sau tất cảqualitygates mới tích hợp serving/rollout/RAGMAINE2E. Không replay các private consumedintents (`main-setup-intent`, `main-delegated-acceptance-intent`, pilots/DEV) hoặc tự kích lại delegation/AUTO. Một root làm tuần tự; không spawn thêm subagent. Inventory hiện tại không chứng minh được tài khoảnCodexkhác đã hoàn tất; không gọi đó là verified.
<!-- END_AUTONOMOUS_FINAL_CURRENT_20261104 -->

<!-- FUNCTIONAL_CURRENT_20261104 -->
# Defects04/11

RESOLVED: Command Center registered-source NameError (immutable13PASS/MAIN bridge); WSL missing verifiedbase import; startup CLI false-negative convergence (host10PASS/fullprepare).
WP394/run301dbdd8: **succeeded**, 43 generation receipts, recovery_count=5; PR https://github.com/Luim3141/mini-task-manager/pull/12. Một coding task, cùng run qua các continuation; không replay391/385, không merge/deploy PR mới. Dev hoàn tất, Review/QA PASS, host acceptance 57 tests PASS; Native394 vẫn NEW, tách biệt với engineering delivery và Owner acceptance.
RAG chưa đạt. Serving baseline trên observed DEV: Hit@5=2/13 (15.38%), FPR1/20 (5%); chưa có benchmark mới được chứng nhận. Reader candidate DEV Hit@5=6/13 (46.15%), support3/13, FPR4/20 (20%) bị REJECTED và không deploy. Owner đã xác nhận3intents WP392;6cards VN/EN tương quan không phải benchmark đại diện hay phê duyệt candidate.
Còn mở: semantic answerability/quality + independent evaluation; Owner UI UAT; WF05/06 Owner decision; WF09 approved Project6 mapping/transition; actual WF12 current-period cron. Historical WF13/WP385 DEAD và WF10 old plan chứa385 được giữ, không force retry.
Budget exhaustion giữ nguyên policy, không gọi là upstream429. Redacted diagnostic text được quan sát trong exported trajectory; chưa chứng minh runtime model-input corruption, không tắt guard.
<!-- END_FUNCTIONAL_CURRENT_20261104 -->

<!-- FULL_INTEGRATION_20261103_CURRENT -->
# Defects — full integration 03/11/2026

1. **OPEN — Semantic RAG:** DEV baseline 2/13, FPR1/20; candidate8/13, FPR2/20 and p95 7.281s. DEV8 document13/13 nhưng supporting span9/13; không có abstention, 20/20 negative có candidate, không được gọi là FPR. Holdout queries/labels sealed, document-unseen không còn do nguồn đã xuất hiện trong dev; labels chưa reviewer độc lập/human.
2. **BLOCKED — UI UAT:** Computer Use không xác định được browser URL để enforce policy; 0 scenario/screenshot, Owner acceptance PENDING. `integration-final/uat/RESULT.json`.
3. **OPEN — WP385 historical event:** WF13 DEAD sau 5 attempts, source visible0/Native404; giữ nguyên, không force retry/bypass.
4. **LIMIT — WF14 MAIN và WF12 cron:** WF14 failure/retry được chứng minh clone, chưa có positive MAIN mới; weekly human MAIN READY nhưng current-period cron bốn readers chưa được chứng minh.
5. **RESOLVED TRANSIENT / retained history — operator throttle:** drain vượt shared 30/min gây 94 HTTP429/retries; dừng drain, worker backoff tự phục hồi, terminal snapshot 0 pending/retry/sending. Không reset quota/attempt/history. `integration-final/n8n/operator-throttle-incident.json`.
6. **LIMIT — GitHub:** socket/DNS treo ngoài library timeout chưa có hard-kill proof; UI auto-refresh chưa UAT.

Chi tiết/bằng chứng: `FINAL_INTEGRATION_ACCEPTANCE.md`. Không nhầm các lỗi hay giới hạn này với Owner approval.
<!-- END_FULL_INTEGRATION_20261103_CURRENT -->

<!-- FINAL_DEMO_CURRENT -->
# Final Demo defect dispositions — 2026-11-02T21:53:26.525639+00:00

| Defect | Disposition | Evidence |
|---|---|---|
| WF04 không hiện retained history | LIVE VERIFIED; canonical-only workflow + projection ở persistence; bounded success/error retention | n8n3074 exact391completion, cloneerror/nested/retry/restart |
| WF07/WF12 PARTIAL do admin19 | LIVE VERIFIED; explicit20–23, giữ19deny, không impersonateOwner | main-report-readback.json READY4/4 each |
| OpenClaw/Demo UNKNOWN | LIVE VERIFIED measuredREADY/UP, CLI+HTTP, heartbeat độc lập | readback-final.json |
| Provider391429/dead-end | RECOVERED; perrequestlimiter/backoff andfreshprobe; same391SUCCEEDED in1continuation | provider-recovery-probe.json,45calls,PR10 |
| RAG semantic VN/EN | FAILED FUNCTIONAL ACCEPTANCE; candidate rejected, baseline retained | 13/20Hit5,14/20falsepositive holdout |
| Portable disaster recovery | LOCAL_RESTORE_VERIFIED; offhostOwnerpending | dr/restore-final.json |
| n8n master-key rotation | DEFERRED_BY_OWNER_FOR_LOCAL_DEMO; currentcredentialfunction verified4/4 | n8n/deployment.json |
| Historical secrets/enterprise hardening | PRODUCTION_HARDENING_DEFERRED; không tuyên bố đã clean mọihistory | Owner65747289 |
| Owner Browser UAT/physical laptop DR | PENDING OWNER / NOT TESTED | noGUI/no secondmachine |

Old register phía dưới là lịch sử, không ghi đè dispositions hiện tại.
<!-- END_FINAL_DEMO_CURRENT -->

<!-- PHASE3_1_CURRENT -->
# Phase3.1 — current, 2026-11-02T23:14:21+07:00

MAIN Gateway `sha256:b184f91963e53df47cbc884cc353d03b0bce871ee19b45b5dc7a5ca78fd638ab`, Core `sha256:e8474e53c7f56a46cd724f4a938a33f9ba01374fbaeb4bb729499cce4fbd4e84`. OFF/active0/workerALIVE; source+pins/API verified, **OWNER UAT PENDING**. #391 vẫn BLOCKED/provider429; không resume trong phiên này. Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json` và `FINAL_TEST_RESULTS.json` schema5. Các mục cũ phía dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

## Phase3.1 defects

| Defect | Disposition |
|---|---|
| WP identity/date/379 false Epic | FIXED / DEPLOYED; NativeTask vs engineering unit projection, no deletion |
| Workforce loses historical failure, rework shown succeeded | FIXED / DEPLOYED; per-role activity + regression |
| Mission/Pipeline fake active or opaque stages | FIXED / DEPLOYED in tested contracts; active0 does not imply AgentRUNNING |
| Budget generic failure / provider dead-end / nested SQLite write lock | FIXED / DEPLOYED; scoped classification/readiness-before-lock/race fence |
| Duplicate Resume spends continuation without execution | FIXED / DEPLOYED; pending marker/requeue dedup |
| Child blocked note/notification missing or ERROR shown INFO | FIXED / DEPLOYED; correct child/run/level, durable dedup/read |
| Raw Markdown reader / overflow | FIXED / DEPLOYED in Rails/Node/CSS contracts; pixel/print Owner UAT pending |
| Integrations lack sourced health | FIXED;5HTTP UP, OpenClaw/Demo UNKNOWN valid |
| #391 provider429 | OPEN operational block; no new provider/quota recovery evidence; task not complete |
| Semantic/n8n/WF07/12/DR historical blockers | UNCHANGED; not hidden by UX fixes |

---

# Defect register — post-30218aff

| Vấn đề | Trạng thái | Bằng chứng / giới hạn |
|---|---|---|
| n8n full-overwrite bypass redaction | Đã vá và deploy; giới hạn còn lại | `SECURITY_AND_CREDENTIAL_AUDIT.md`; clone SQLite, không chứng minh mọi secret payload |
| n8n master key trong source cũ, lịch sử chứa secret | OPEN / giảm rủi ro | Literal đã gỡ khỏi script workspace, bản gốc DPAPI roundtrip PASS; source snapshot cũ còn secret, clone restore có WAL/SHM và 4/4 credentials PASS, nhưng migration thử với key mới FAILED; chưa xoay key hoặc thử DR profile khác |
| WF04 execution retention | OPEN | Success/error không lưu; Gateway có event ACK nhưng UI execution history không đầy đủ |
| RAG semantic VN/EN | OPEN | `SECOND_BRAIN_RAG_EVALUATION.md`; targeted WP387 citation PASS không bao phủ corpus |
| Knowledge publication nhận parent thay child | ĐÃ VÁ, LIVE VERIFIED | Fresh E2E #389 trả đúng child citation/version sau patch; không chứng minh semantic RAG tổng quát |
| WP385 bị xóa | MITIGATED | #388 là replacement, không khôi phục ID/lịch sử; `WP385_RECOVERY_AUDIT.md` |
| Run resume prepare generic failure | RỦI RO TÁI HIỆN ĐÃ VÁ / historical root OPEN | Timeout trong resume bị che và cho replay; test tái hiện, timeout nay bị fence và lưu diagnostic redacted. Không có raw exception cũ để kết luận lỗi #387 cùng nguyên nhân |
| Dev budget | MITIGATED theo run | Lần đầu dừng ở 12 calls; resume cùng checkpoint thành công, chưa chứng minh giới hạn đủ cho mọi task |
| Expired lease / duplicate resume | ĐÃ VÁ, DEPLOYED | Test red-green: checkpoint expired bị fence; duplicate đang queued không dùng thêm recovery budget. Fresh E2E #389 chạy sau patch không cần resume; tình huống lỗi được test bằng fixture |
| GitHub Sync idempotency | LIVE CHECK PASS | Hai lần SUCCESS, lần hai không đổi; #387 có một matching activity |
| Demo health/summary cũ | Đã triển khai release có kiểm tra | PR #6 tree chưa merge; xem `DEPLOYMENT_AND_ROLLBACK.md` |
| Owner UI UAT và toàn bộ 16 business flows | NOT VERIFIED | Không dùng Computer Use; active không đồng nghĩa business PASS |
| Command Center worker/run/resume/cancel | ĐÃ SỬA, DEPLOYED; UAT PENDING | Test state contract, Core clone và health PASS; không tự chứng nhận UI human UAT |
| Report AI narrative bị bỏ qua im lặng | ĐÃ SỬA, LIVE VERIFIED | `include_narrative=true` tạo report có AI label và provider receipt; failure được đánh dấu UNAVAILABLE |

| Inspector XSS và trạng thái giả | ĐÃ VÁ, DEPLOYED / UAT PENDING | Node VM escaping test, Rails ERB và Native API clone PASS; dữ liệu chưa tin cậy được escape, nhãn giả đã bỏ; chưa có browser/human UAT |
| Admission dựa trên tuổi created_at | ĐÃ VÁ, DEPLOYED | Fixture worker lease hợp lệ trên 30 phút không bị kết thúc sai; xử lý side effect worker cũ sau lease hết hạn vẫn cần đối soát |

## Final Stabilization Phase 2 — current gates

| Capability / defect | Status | Bằng chứng và giới hạn |
|---|---|---|
| Stale worker publication | SOURCE FIXED / DEPLOYED | Token/identity, transaction và knowledge/vector guards, singleton cleanup; independent review và fault fixtures đạt. Request đã gửi vẫn cần đối soát |
| Coding intake #390 | LIVE VERIFIED | Hai run succeeded, 32 tests, PR #9 OPEN, commit 4a794e2b…, 22 ACK; chạy trên Gateway bca |
| Report source/time/usage | DEPLOYED / LIVE VERIFIED | Nguồn unknown/PARTIAL, ISO offset, generation usage, WP/PR links; 8cd API và 8359 provenance checks riêng |
| AI narrative receipt link | DEPLOYED / LIVE VERIFIED | Report be099f56… có hai LIVE_SUCCESS receipt; không giả mapping report cũ |
| Semantic chunk expansion | REJECTED | Holdout false positives 1→2/20; không deploy |
| Local ONNX reranker | REJECTED | Hit@5 10→19/24 nhưng false positives 0→2/20. Literal-support proxy 12/19 không đồng nghĩa 7 citation sai nghĩa |
| Citation ID alias | SOURCE FIXED / DEPLOYED | Lấy ID từ SQLite đã xác minh; exact #387/#389/#390 read-back đạt |
| n8n master-key migration | MASTER_KEY_CUTOVER_BLOCKED | Old DEK wrappers còn phụ thuộc key cũ; clone restore/decrypt đạt, new-key migration chưa đạt |
| n8n payload/history secrets | OPEN / mitigation | WF04 retention OFF, Gateway schema/projection có kiểm tra; generic payload và bản lịch sử chưa remediated |
| WF01–WF16 adapters | TESTED IN CLONE, limited | 49 checks với synthetic Gateway; 14 adapter VERIFIED_IN_CLONE, WF07/WF12 MAIN PARTIAL do admin guard |
| Command Center | DEPLOYED / OWNER UAT PENDING | Render clone và JS/Rails contracts; chưa thao tác browser |
| Demo release identity | LIVE VERIFIED | PR #6 unmerged được ghi rõ; health/summary và schema/rows đạt, PR #7/#8/#9 chưa deploy |
| Project 5 integrity | LIVE READBACK, scoped | WP/relations/journals/membership/version cùng quyền/settings được đối chiếu, không phải mọi bảng DB |
| Owner acceptance | OWNER UAT PENDING | Chỉ Owner được quyết định OWNER ACCEPTED |

## Final gate disposition — 2026-11-02 08:05 UTC

| Gate | Trạng thái cuối | Evidence / giới hạn |
|---|---|---|
| M1 fencing / delivery | SOURCE FIXED, DEPLOYED, LIVE VERIFIED cho coding flow | 146 current regression, review fixes, singleton denial, #390; external sent requests cần reconciliation |
| M2 semantic RAG | FAILED / PARTIAL | Chunk/reranker holdout rejected; clause dev7/28, holdout mới chưa dùng; không semantic rollout |
| M3 n8n key/history | BLOCKED / PARTIAL | Old-key portable restore đạt; new-key DEK unwrap thất bại; history arbitrary payload OPEN, retention OFF |
| M4 16 workflows | PARTIAL | 49 adapter checks; 14 clone adapter verified; WF07/12 privileged actor19 guard denial |
| M5 Command Center | SOURCE FIXED / DEPLOYED; OWNER UAT PENDING | Native/full ERB clone + actual-template Node VM, không browser UAT |
| M6 GitHub/OpenClaw/demo | LIVE VERIFIED trong scope | #390/PR9, PR graph/readback; demo vẫn PR6 unmerged, không auto-merge |
| M7 Reports/Knowledge | DEPLOYED / LIVE VERIFIED, semantic PARTIAL | Report8359 receipts linked, child version2; narrative chưa xác minh |
| M8 final runtime | LIVE VERIFIED; final acceptance PARTIAL | OFF / queue0 / worker ALIVE / source+pins khớp, không whole-image recoding lần hai |
| M9 handoff | UPDATED | Revision-specific index schema3, rollback/private backup, Owner UAT guide |

Không có OWNER ACCEPTED. Không chuyển toàn hệ thống thành FULL PASS khi RAG/key/history/workflow gates còn mở.

## Phase3 — owner failures and final disposition

- GitHub Sync stale UI: SOURCE FIXED / DEPLOYED / API VERIFIED, OWNER UAT PENDING. Root causes mode-only polling/native navigation + Rails cache hash overriding string header; now fresh fragments/no-store.
- Controls no clear effect: SOURCE FIXED / DEPLOYED, canonical desired/effective/revision/receipt + durable idempotency. MAIN OFF/replay read-back, active failure matrix in fixtures. OWNER UAT PENDING.
- Missing live activity: SOURCE FIXED / DEPLOYED / API VERIFIED for historical artifacts,100events/10stages; no new coding run. Browser latency/UAT pending.
- Review findings7Important: fixed red/green (rejectedreceipt, unknownACK, Inspector race, requestid replay, notifications, stable modal unlock, ambiguous5xx). Cache header and Native version label additionally fixed by actual Rails/targeted test.
- Project6 stale knowledge: FIXED / DEPLOYED / LIVE READ-BACK,10/10current sampled sources. Original operationalclone2overstrict assumptions FAILED retained; semantic quality still PARTIAL/FAILED.
- n8n arbitrary payload/history/master key: BLOCKED. Actual six filesystem routes leak nested/free-text canary; retentionOFF. Actor19guard valid,WF07/WF12all5PARTIAL. No RBAC/key/ciphertext mutation.
- DR byte verification improved; off-host destination/key custody and physical machine restore PENDING OWNER. User data13tables unchanged.

Exact43feature/WFrows: phase3-owner/ACCEPTANCE_MATRIX.json. No FULL SYSTEM PASS or OWNER ACCEPTED.

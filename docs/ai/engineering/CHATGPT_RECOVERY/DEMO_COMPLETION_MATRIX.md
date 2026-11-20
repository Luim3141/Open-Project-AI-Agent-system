<!-- AUTONOMOUS_FINAL_CURRENT_20261104 -->
# Acceptance matrix — deployed partial

Cập nhật 2026-11-04T09:30:39.415051+00:00 (UTC; ngày 04/11/2026 theo Asia/Bangkok). **DEPLOYED_PARTIAL — NOT_FULL_FUNCTIONAL_READY.** Các block bên dưới là lịch sử.

Gateway `sha256:f91c98823b42cb2d9499de1a8d3e3935fd59a594b6b92b3f9a4bd4cf2dc0087c`; Core `sha256:1f1b366abc88c20794992ee2df9a7227417fc3a770ca4b8abdb1e34becd82db8`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Source/runtime/pins và16published definitions khớp; Gateway/Core healthy, n8n ready, OpenClaw CLI/RPC READY, worker ALIVE/idle, queue0,531Gemini receipts không tăng. Delegation OFF/revision2. Engineering mode **PAUSED** là actual Owner18 override (audit1793775548); giữ nguyên, không giả OFF hoặc tự bật AUTO. Provider `READINESS_STALE`, gatefalse: workerALIVE không phải providerAVAILABLE.

Đã triển khai và xác minh nghiệp vụ thật của WF05/WF06/WF09 trên MAIN. Semantic RAG vẫn chưa đạt điều kiện triển khai; không coi hệ thống đã hoàn tất nghiệm thu.

Bằng chứng: [runtime hiện hành](autonomous-final/final-live-verification.json), [nghiệp vụ MAIN](autonomous-final/main-delegated-business.json), [đánh giá RAG](autonomous-final/rag-final-review.json).

**MAIN_BUSINESS_VERIFIED:** real principal25 `qldapm-demo-delegate`, non-admin, PM22, membership chỉ Project6, API key/bearer riêng. Không impersonate Owner18, không thêm general engineering/AUTO rights. WF05preview→OWNER_DELEGATED_POLICY_APPROVED→WF06execute/Native read-back có3 mutations hợp lệ trên fixture395: note BASELINE→CHECKED→BASELINE, rồi NEW1→IN ANALYSIS37, Nativev0→3. WF09preview3650→WF05decision3653→WF06execute3654→WF09current3655. Tổng9correlated n8n executions3643–3655 đều SUCCESS (không phải mọi số trong khoảng đều thuộc case). Approval tách khỏi execution; defaultOFF trả REQUIRES_HUMAN_APPROVAL, stale/action/project/role bị từ chối, duplicate không write lại.3audit reports,7durable notifications; latestaudit234ad848… CURRENT, hai audit cũ HISTORICAL. Policy finalOFF; service không tự bật lại grant đã dùng. Authenticated Owner override/disable giữ nguyên.

Fixture là NativeTask1 có `[Bug]` marker theo mapping thực Project6, không phải việc coding. Native cho NEW→IN ANALYSIS, không có37→1; description đã được bù trừ về BASELINE, fixture giữ trạng thái hợp lệ IN ANALYSIS. Không giả status rollback/QA/Done. Clone còn chứng minh stale-after-approval chặn trước Nativewrite và unknown write không blind replay. Human Owner không trực tiếp approve proposal; audit ghi đúng delegated policy.

16/16published definitions/versions/hash được đối chiếu actualMAIN,14workflow ngoàiWF05/06 giữ nguyên. [Current matrix](autonomous-final/N8N_ACCEPTANCE_MATRIX.md) có caller/trigger/contract/side effect/retry/correlation/CC action và actual latest execution; original [wiring contracts](integration-final/n8n/WIRING_MATRIX.md) phía sau được xem là lịch sử tại các hàng05/06/09/14.

WF12publishedcron `0 0 17 * * 5`, timezoneAsia/Bangkok: thứSáu17:00, lần kế tiếp06/11/2026. DefinitionVERIFIED; compatible actual n8n scheduled-trigger clonePASS, signed collectors20–23 (19denied), reports/dedup/period contracts đã có proof và không đổi source/schedule. MAIN human webhook3359 READY/persisted report thật; không phải scheduled branch. Current-cycle wallclock **WAITING_FOR_SCHEDULE**; historical trigger2750/30-10failed được giữ rõ. Không đổi lịch production hoặc chờ nhiều ngày để đổi trạng thái.

WF14 source392: dùng lại failure attempt1→execution3393 WAITING_RETRY→verified attempt2→WF13 execution3394. Native392v0, hai documents/FTS/chunks/vectors riêng biệt và current citation `/work_packages/392` còn đúng. WF15 execution3660 tại lần đối chiếu recovery ACK/DRIFT_OBSERVED: không có missing/stale/hash/FTS/orphan lỗi; tám unmatched points đều thuộc WP385 đã xóa. Hai event DEAD lịch sử là WF13/WP385 và WF10/old plan b1cca031 chứa385; không force retry hoặc che lỗi. Pending events bằng0 tại readback. Execution mới nhất của từng workflow xem ma trận động và snapshot runtime. [Recovery/current index](autonomous-final/recovery-current-readback.json), [integrity](autonomous-final/index-current-integrity.json).

**Semantic RAG FAILED qualification; serving RAG không đổi.** B5 replay xác định SPAN_REFERENCE_MISMATCH (span10 thay vì5); offline unique same-source pointer repair vẫn không chứng minh answer. Typed FORMAT/SOURCE/SPAN/QUOTE/SUPPORT + bounded redacted captures giữ validator chặt.

Root corpus:11/15docs có JSON bị cắt, các business fields/boolean/path mất; whole-journal candidate giữ15docs/230073chars/117journals,906typedfacts, Unicode offsets/hash. Decode trước split, phân biệt Native fields, requirements và historical receipts. Research actual BGE/Qdrant906points + FTS/identity cho **DEV retrievalHit@5=13/13 (100%)**; đây là observed correlated DEV, không phải benchmark độc lập hay serving quality.

Final answer chưa đạt: six-case semantic-fact pilot strictsupport3/4positive, no-answer0/2negative emitted; một CRUD answer còn lẫn parent379/copied objective. Warm1.424–2.827s/cold16.406s. Expanded DEV dùng lại5cached pilot replies, chỉ3generation requests mới, dừng đúng gate ở warm5.944s>5s.4positive answers được quan sát, strictsupport2/4: hai câu “initial unit/create/list/SQLite” chỉ chọn unitname nên không đủ toàn bộ evidence.17candidate citations kiểm exacthash/offset/Nativeid/version không lỗi, nhưng quote identity không đồng nghĩa semantic support. RepresentativeFPR **NOT_ESTABLISHED**;0/2negative không chứng minh≤5%. Không mở oldholdout, không tạo/scoring lockedholdout khi DEV gate còn fail, không đổi gate để gọi PASS.

Current serving vẫn metadata retrieval/answer:null, NO_EVIDENCE hoặc UNVERIFIED_RETRIEVAL. Baseline observedDEV Hit2/13/FPR1/20 là lịch sử của serving baseline, không lấy candidate13/13 gán cho MAIN. Không có qualified RAG image hoặc postdeploy semantic E2E mới. Source-grade nghiên cứu không thay cho retrieval→evidence→answer→citation acceptance. Chỉ WP392 threeintents từng được Owner xác nhận; các nhãn khác là assistant source review, không gọi human ground truth. Lượt tiếp tục này11local4B requests,0Gemini mới, không tải/đổi model hoặc trả phí.

Project5 read-only comparisonPASS:341WP/344relations/968journals và12bảng scope/config/security khớp snapshot trước. Globalusers chỉ thêm25 được Owner ủy quyền và existing login timestamps cho phép; không tuyên bố mọi global table byte-identical. Enrollment cũng giữ Project5members/roles/permissions và kiểm25 chỉ Project6. PR11actualMERGED03/11 13:23:29Z, PR12OPEN/head1ece6705; Demo18791 vẫn01d765c, khôngredeploy. Current GitHub PR state tách khỏi oldrelease metadata `main_merged:false` (mô tả release lúc deploy, không nói PR11 cònopen). Khôngpush/merge/rebase/newcodingrun/replay391/394/385/DR/keymigration/quota/modelbudgetchange.

Runb7fd6aec-3357-495f-b9e5-f7ba04d67ad6 hiệnSUCCEEDED/finished,45generationcalls/recovery3/checkpoint39 theo preservedproof; không còn là runfailed cầnresume. WP394/run301dbdd8 cũngSUCCEEDED/43calls/recovery5/57hostacceptancePASS, PR12giữOPEN. Native task status và engineering success vẫn tách biệt.
<!-- END_AUTONOMOUS_FINAL_CURRENT_20261104 -->

<!-- FUNCTIONAL_CURRENT_20261104 -->
Cập nhật 2026-11-03T20:13:07.428616+00:00. **DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY; OWNER_ACCEPTANCE_PENDING.** Phần phía dưới block này là lịch sử.
Gateway `sha256:a6fe1d61982db84447f45eb35a56809ae4ab16d854012bec59db1f58d890b2be`, Core `sha256:91afae9c6855417dcc14828d0bd16b3a5b780439d7d1fbbfede64c64241d83d4`, n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Source/pins, OFF/active0, worker và provider gatefalse: [integration-final/functional-completion/final-live-verification.json](integration-final/functional-completion/final-live-verification.json).

WP394/run301dbdd8: **succeeded**, 43 generation receipts, recovery_count=5; PR https://github.com/Luim3141/mini-task-manager/pull/12. Một coding task, cùng run qua các continuation; không replay391/385, không merge/deploy PR mới. Dev hoàn tất, Review/QA PASS, host acceptance 57 tests PASS; Native394 vẫn NEW, tách biệt với engineering delivery và Owner acceptance.
Demo18791 vẫn SHA01d765c / unmerged integration PR11; không deploy featurecount hoặc merge PR.
WF01/03/08/09/10 đã publish MAIN. WF08/09/10/01 command receipts3423/3424/3426/3427 đối chiếu business read-back; WF03 actual planning96b4cee5 và WF10 PUBLISHED plan/Native units. WF14 own-source392 failed-attempt1 → execution3393 WAITING_RETRY → retryverified2 → WF13execution3394/currentcitation. WF05/06 PENDING_OWNER_DECISION; WF09 đã triage read-only, chưa approval/Native status transition. WF12 cron clonePASS, current-period MAIN four-reader cron chưa tới lịch Fri17:00 Bangkok; manual READY không phải cron.
RAG chưa đạt. Serving baseline trên observed DEV: Hit@5=2/13 (15.38%), FPR1/20 (5%); chưa có benchmark mới được chứng nhận. Reader candidate DEV Hit@5=6/13 (46.15%), support3/13, FPR4/20 (20%) bị REJECTED và không deploy. Owner đã xác nhận3intents WP392;6cards VN/EN tương quan không phải benchmark đại diện hay phê duyệt candidate.
Còn mở: semantic answerability/quality + independent evaluation; Owner UI UAT; WF05/06 Owner decision; WF09 approved Project6 mapping/transition; actual WF12 current-period cron. Historical WF13/WP385 DEAD và WF10 old plan chứa385 được giữ, không force retry.
<!-- END_FUNCTIONAL_CURRENT_20261104 -->

<!-- FULL_INTEGRATION_20261103_CURRENT -->
# Demo completion — full integration 03/11/2026

**DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY; OWNER ACCEPTANCE PENDING.** Demo18791 chạy unmerged integration `01d765c`, PR6–10 và PR11 OPEN; 52 tests và actual HTTP/CSV/Unicode fixture PASS, SQLite preserved. Gateway/Core/n8n deployed, 138 verified event receipts; file P6, GitHub polling, weekly human report và post-recovery monitor có MAIN read-back. 16 workflow bounded clone evidence không thành mọi MAIN branch.

Chưa đạt: semantic RAG gate, Computer Use UAT (tool policy dừng trước scenario), current-period WF12 cron 4 readers, WF14 MAIN failure path, historical WP385 DEAD. Xem `FINAL_INTEGRATION_ACCEPTANCE.md`, `integration-final/uat/RESULT.json`.
<!-- END_FULL_INTEGRATION_20261103_CURRENT -->

# Demo completion matrix — Final03/11/2026

Overall PARTIAL: semantic RAG vẫn FAILED vàOwnerUATPENDING. Securitydeferkhôngchặncácchứcnăngđãverify.

| Component | Expected | Tested | Runtime Evidence | Status | Remaining |
|---|---|---|---|---|---|
|OpenProject|Task/data preservation|Native391v2;13Project5tablesidentical|native-after.json;readback-final.json|LIVE VERIFIED|OwnerUAT|
|AI Gateway|Orchestration/fencing|161immutabletests;source/pins|final-live-verification.json|LIVE VERIFIED|No allbranches claim|
|OpenClaw|Codingrunner/readiness|Real391Dev/Review/QA;HTTP+CLI|readback-final.json;runartifacts|LIVE VERIFIED|Idlefencingmaystopprocess truthfully|
|Gemini|Limits/recovery|Sharedledger10RPM175KTPM;actualprobe+9calls|providerprobe;391receipts|LIVE VERIFIED|Upstreamcapacitycannotguarantee|
|Multi-Agent|PM/BA/Dev/Reviewer/QA|Historicalplanning +same391delivery|checkpoint39;37pytest|LIVE VERIFIED|Not freshworkintakeE2E|
|GitHub|Commit/Push/PR/Sync|PR10headmatches;sourceAPI|readback-final.json;PR10|LIVE VERIFIED|PR10OPEN;noautomerge/deploy|
|WF01–WF16|Actualbusinesscontracts|16boundedscenariosactualclone|n8n/BUSINESS_MATRIX.md|TESTED IN CLONE|Branch-complete/humanapprovalnotclaimed|
|WF07/WF12|Validreportprincipals|MAINdaily/weekly4/4READY,19DENIED|n8n/main-report-readback.json|LIVE VERIFIED|Futurecronwallclocknotclaimed|
|WF04history|Retainedcanonicalevents|MAIN3074exactRUN_COMPLETED|n8n/run391-completed-readback.json|LIVE VERIFIED|Genericlegacysecretsdeferred|
|SecondBrainsemantic|VN/ENHit5>=80%,FPR<=5%|Candidate65%/70%;baseline15%/0%|rag/holdout-result.json|FAILED|Newranking/design+independentlabels|
|Knowledgefreshness/citation|Exactsource/version|391v2;actualcloneupdate/tombstone/integrity|391knowledge;n8nWF01/02/15|LIVE VERIFIED bounded|Not semanticPASS|
|Reports|Correctgeneration/reader|Native4reports;RailsMarkdown/NodeVM|n8nreports;checks|LIVE VERIFIED|OwnerlayoutUAT|
|Notifications|Scopedcompleted/blocked|161tests+actualnotesdedup|readback-final.json|LIVE VERIFIED|Ownerdismiss/clickUAT|
|DR|Portablelocalrestore|PG/Core/n8n/Gateway/Knowledge/Qdrant/OpenClaw/Git/demo|dr/restore-final.json|LIVE VERIFIED LOCAL_RESTORE|OFF_HOST_COPY_PENDING_OWNER;physicalNOTTESTED|
|OwnerUI|ManualUAT|NoGUIautomation|OWNER_MANUAL_UAT_GUIDE.md|OWNER UAT PENDING|Owneractions|
|Masterkeyrotation|Keepworkingcredentials|4/4decryptactualbusiness|n8ndeployment|DEFERRED BY OWNER|NotPASS,notfunctionalblock|
|Historysecurity/enterprise/physicalDR|Productionhardening|Ownerexplicitdisposition|SECURITY_AND_CREDENTIAL_AUDIT.md|DEFERRED BY OWNER|Legacyrisksremain|

Actual391continuation1/1; freshcodingtask0/1; noGUI/P5Nativewrites/paid/keyrotation/autoPRmerge/reset.

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
<!-- END_BUTTON_AUDIT_CURRENT_20261105 -->

<!-- CC_STABILIZATION_CURRENT_20261104 -->
# Control Center/Reports MAIN — functional repairs verified, performance open

Cập nhật 2026-11-04T16:22:32.919239+00:00 UTC (Asia/Bangkok,04/11/2026). **FUNCTIONAL_REPAIRS_VERIFIED — PERFORMANCE_GATE_OPEN**; chưa chứng nhận `AI_CONTROL_CENTER_DEMO_READY` hoặc FULL FUNCTIONAL PASS. Các block bên dưới là lịch sử.

MAIN: Gateway `sha256:698224aa0ddc88808ebab30b4705dfe7050b09db67b8ae3fc4a569d6a8447e1c`; Core `sha256:1a8f2528da78860faa69610568985471e26136d441a594f4f098c045ca181189`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Images/source/pins được read-back; Gateway/Core healthy, n8n readiness200. Final PAUSED, queue0, workerALIVE, delegationOFF;21coding runs/531provider receipts giữ nguyên. Project5 scoped rows và global config/security tables bảo toàn; chỉ cho phép timestamp đăng nhập User thay đổi.

Native386/387/389/390/391/394 đã READY FOR RELEASE/v10 qua workflow thật và journal của principal25; không tự DONE.391/b7fd và394 vẫn SUCCEEDED, không replay. PR11MERGED/main, PR12OPEN; Demo artifact giữ nguyên. RAG algorithms đóng băng/FAILED; provider readiness riêng, không coi workerALIVE là inferenceREADY.

Report Reader đã sửa trên MAIN: CSP nonce, Turbo cache restore, timeout15s, không ghi đè response cũ; Daily6766ký tự/6sections/Raw Markdown, audit có facts/provenance thay vì trang trống. GitHub Sync hiển thị ACK→operation→COMPLETED — NO CHANGES/12checked/0changed mà không F5. Artifact caption ghi rõ metadata lịch sử; trạng thái merge hiện hành lấy từ bảng PR.

Gateway HTTP5samples: trước p50=9.8377s/samplep95(max)=18.9763s; sau p50=7.2148s/samplep95(max)=12.8446s. Mục tiêu initial usable<4s chưa đạt; warm UI paint<200ms chưa có phép đo riêng. Core observed GitHub Sync ACK1913.38ms là một mẫu, không phải p95. Gateway hiện1CPU/384MiB, có sample saturation~100% khi đo. Không tăng quota hay đổi nơi lưu DB để che giới hạn. Cần tiếp tục tối ưu/read-path load qualification trước chứng nhận Demo Ready.

Bằng chứng: [runtime](cc-stabilization/final-live-verification.json), [166 image regressions](cc-stabilization/image-regression-reports.json), [exact clone qualification](cc-stabilization/clone-qualification-caption.json), [browser](cc-stabilization/browser-uat.json), [Project5](cc-stabilization/native-integrity-after.json). Không đổi GitHub source/merge, Demo, RAG algorithms hoặc DR.

## Checklist demo5–10phút

1. Mở `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai`: Project6, PAUSED/queue0/workerALIVE; đọc timestamp và provider state riêng.
2. Backlog: tìm391 và394; đối chiếu Engineering SUCCEEDED, Native READY FOR RELEASE/v10, Delivery riêng.
3. Mở Native WP/activity: kiểm status thật và journal principal25; không bấm DONE/transition.
4. Mở existing b7fd Run Inspector, xem QA/test/PR evidence; không Resume run đã hoàn tất.
5. GitHub: PR11MERGED/main, PR12OPEN; Demo artifact là metadata của lần deploy đã lưu.
6. Bấm Sync GitHub một lần; xem ACK/request, operation, rồi completed/no changes. Chuyển tab khi chờ; không F5 để tạo cảm giác hoàn tất.
7. Reports: Daily→Xem toàn văn→6sections→thu gọn/mở rộng→Raw Markdown. Native NEW trong report08:00 là HISTORICAL snapshot, không phải status live.
8. Audit mới nhất→Xem toàn văn: facts/provenance/decision principals; không tự gọi narrativeAI.
9. Đóng modal, F5 và Back/Forward; vẫn ở AI Center/tab. Run Once khi no eligible chỉ nhận từ chối rõ.
10. Kết thúc PAUSED/delegationOFF/queue0. Không bấm Snapshot+AI, giao task, merge/deploy Demo, RAG experiment hoặc restore DB. Dự trù thời gian tải chậm đã ghi, chưa gọi đây là Demo Ready.
<!-- END_CC_STABILIZATION_CURRENT_20261104 -->

<!-- AUTONOMOUS_FINAL_CURRENT_20261104 -->
# Human browser checklist —PUBLICATION_REDACTED_UAT

Cập nhật 2026-11-04T09:30:39.415051+00:00 (UTC; ngày 04/11/2026 theo Asia/Bangkok). **DEPLOYED_PARTIAL — NOT_FULL_FUNCTIONAL_READY.** Các block bên dưới là lịch sử.

Gateway `sha256:f91c98823b42cb2d9499de1a8d3e3935fd59a594b6b92b3f9a4bd4cf2dc0087c`; Core `sha256:1f1b366abc88c20794992ee2df9a7227417fc3a770ca4b8abdb1e34becd82db8`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Source/runtime/pins và16published definitions khớp; Gateway/Core healthy, n8n ready, OpenClaw CLI/RPC READY, worker ALIVE/idle, queue0,531Gemini receipts không tăng. Delegation OFF/revision2. Engineering mode **PAUSED** là actual Owner18 override (audit1793775548); giữ nguyên, không giả OFF hoặc tự bật AUTO. Provider `READINESS_STALE`, gatefalse: workerALIVE không phải providerAVAILABLE.

Đã triển khai và xác minh nghiệp vụ thật của WF05/WF06/WF09 trên MAIN. Semantic RAG vẫn chưa đạt điều kiện triển khai; không coi hệ thống đã hoàn tất nghiệm thu.

Bằng chứng: [runtime hiện hành](autonomous-final/final-live-verification.json), [nghiệp vụ MAIN](autonomous-final/main-delegated-business.json), [đánh giá RAG](autonomous-final/rag-final-review.json).

API/CLI ưu tiên; actualRailsclone đã kiểm login/CSRF/controller/render nhưng không thay humanbrowserUAT. Login bằng tài khoản Owner thật/MFA; không reset/bypass. Không nhập credential vào chat.

- Mở Project6 AI Command Center; modePAUSED, queue0, workerALIVE; providerREADINESS_STALE khác providerAVAILABLE.
- Automation:16workflowcards có trigger/version/timestamp/globalexecution và riêng Project6correlation/deeplink.05approved khác06businessverified;09currentNativeverified.
- Delegated policy ban đầuOFF/revision2. Xem fixture395v3/INANALYSIS/noteBASELINE và3proposalsBUSINESS_VERIFIED/1REQUIRES_HUMAN_APPROVAL; không cần thực thi lại để xemreceipt. Muốn demo bật lại phải Owner chủ động control; one-use servicegrant đã tiêu thụ, không tựbật. Nếu chủ độngdemo note-change, tắt lại sau đó; không đổiworkflow/status vì không có37→1.
- Reports: latestWORKFLOW_AUDIT234ad848… CURRENT; oldernote1/2HISTORICAL. Notifications7IDsđúngstage vàpollingkhôngtrùng; mởWP395/actualn8nexecutions/PRlinks.
- Search: VN/EN input, loading/empty/error, no-answer explanation, linksource392v0/citation; không coi metadatahit là supportedanswer. SemanticRAG vẫnFAILED, khôngsignoffFULLREADY.
- GitHub:PR11merged/PR12open, Demo18791frozen01d765c; chỉ đọc, khôngmerge/deploy.
- Run391/b7fd và394SUCCEEDED; khôngResume/replay. Không dùng385deleted hoặc371Project5 đểtest.
- WF12đợi lịchthật06/11/2026 17:00Asia/Bangkok; manualwebhook không thaycronreceipt. Không đổi productioncron.

Ghi kết quả từng thao tác PASS/FAIL và timestamp; lỗi có sourceWP/version/run/execution, không chụp secrets. API smoke không tự đánh dấu browser checklistPASS.
Essential FAILED: Semantic RAG complete-answer/evidence selection và worst-case latency/representativeFPR chưaqualified; candidate khôngdeploy, MAINsemanticE2E chưachạy. PUBLICATION_REDACTED_UAT: browser interactions/accessibility/loading/error/links; WAITING_FOR_SCHEDULE: current WF12 wallclock. Preserved partial:8WP385 unmatchedvectors/2historicalDEAD và persistedproviderREADINESS_STALE. Không tuyên bố FULL FUNCTIONAL DEMO READY.

Tiếp tục duy nhất có ích: sửa complete-evidence selection/parent-copy ambiguity và ổn định latency với gate5s giữ nguyên; đóng băng nguồn+code+broaderdevelopment/lockedholdout labels có source review trước khi score; chỉ sau tất cảqualitygates mới tích hợp serving/rollout/RAGMAINE2E. Không replay các private consumedintents (`main-setup-intent`, `main-delegated-acceptance-intent`, pilots/DEV) hoặc tự kích lại delegation/AUTO. Một root làm tuần tự; không spawn thêm subagent. Inventory hiện tại không chứng minh được tài khoảnCodexkhác đã hoàn tất; không gọi đó là verified.
<!-- END_AUTONOMOUS_FINAL_CURRENT_20261104 -->

<!-- FUNCTIONAL_CURRENT_20261104 -->
Cập nhật 2026-11-03T20:13:07.428616+00:00. **DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY; OWNER_ACCEPTANCE_PENDING.** Phần phía dưới block này là lịch sử.
Gateway `sha256:a6fe1d61982db84447f45eb35a56809ae4ab16d854012bec59db1f58d890b2be`, Core `sha256:91afae9c6855417dcc14828d0bd16b3a5b780439d7d1fbbfede64c64241d83d4`, n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Source/pins, OFF/active0, worker và provider gatefalse: [integration-final/functional-completion/final-live-verification.json](integration-final/functional-completion/final-live-verification.json).

Không tạo lại task394 hoặc Resume391/385. Dùng current existing task/run để kiểm status/workflow links/risk/Bugtriage/source search+read và GitHub refresh. Không nhấn approve/hash nếu chưa xem exactproposal. WF05/06 vẫn cần quyết định thật của Owner; Bugtransition cần mapping Project6 được duyệt. Không coi API/clone checks là browser/human acceptance.
Còn mở: semantic answerability/quality + independent evaluation; Owner UI UAT; WF05/06 Owner decision; WF09 approved Project6 mapping/transition; actual WF12 current-period cron. Historical WF13/WP385 DEAD và WF10 old plan chứa385 được giữ, không force retry.
<!-- END_FUNCTIONAL_CURRENT_20261104 -->

<!-- FULL_INTEGRATION_20261103_CURRENT -->
# Owner UAT — full integration 03/11/2026

Owner acceptance vẫn PENDING. Computer Use đã được phép nhưng tool dừng trước chọn browser vì không xác định được URL để enforce policy; không có UI scenario/screenshot. `integration-final/uat/RESULT.json`.

Khi công cụ/phiên browser an toàn khả dụng, kiểm read-only Command Center/Workforce/Execution/Reports, GitHub & Delivery (unmerged Demo SHA `01d765c` và auto-refresh), n8n histories WF04, Second Brain/citation, Demo18791/filter/CSV, accessibility/zoom theo checklist `integration-final/uat/PLAN.md`. Kết quả cần ghi từng vai trò/scenario; không xem READY backend như Owner acceptance. Không retry/resume WP391, force retry WP385 DEAD, hoặc merge PR11 nếu chưa có quyết định Owner. Semantic RAG hiện chưa đạt và không được trình bày như PASS. `FINAL_INTEGRATION_ACCEPTANCE.md` ghi trạng thái đầy đủ.
<!-- END_FULL_INTEGRATION_20261103_CURRENT -->

<!-- FINAL_DEMO_CURRENT -->
# Owner manual UAT — PENDING, Final Demo03/11/2026

Không Browserautomation đã chạy. API/Rails/NodeVM/CSScontracts không pixelvalidation. Owner tựthử:

1. Backlog/Mission/Workforce: #391 theo title/shortID/date, engineeringCOMPLETED sauDev/Review/QA; Native status riêng, không épDone. Lastactivity vàPR10đúng; OFFkhônghiển thịAgentRUNNING.
2. Inspector: same run `b7fd6aec-3357-495f-b9e5-f7ba04d67ad6`,45cumulativecalls,checkpoint39COMPLETE, freshsessionDev/Review/QA receipts; khôngResume taskđãhoàn tất. Mộtcontinuationchođợtnàyđãdùng1/1.
3. n8nExecutions: mởWF04execution3074, thấyminimal RUN_COMPLETED/event/run391 vàSUCCESS; cótimestamps/correlation. Old3060failureeventreplaylàlịchsửkhác.
4. Daily/Weekly: report4validreaders20–23 READY; source/citations/provenance. Actor19khôngđượcđổiOwnerhoặcbỏguard.
5. Integrations: OpenClawHTTP/CLI READY, Demo18791UP; Worker/providerriêng,providerprobeexpiredphảihiển thịREADINESS_STALE khiđúng. n8ncorrelation,indexscanage,DRbackupstatuscónguồnthời gian.
6. Reports: fullMarkdown headings/lists/table/TOC/rawcopy vàsource/narrativeverification; zoom200%/narrowviewport/keyboardscroll.
7. Notifications: đọccompletion391/oldblockedhistory,clickđúngrun,markreadpersist/reload,dedup. KhôngtựdismissOwnernotesbằngscript.
8. Control/GitHubSync: nếuOwnerbậtAUTO thìđọcqueue/backlogtrước; queueemptyAUTO_IDLE,OFFconfirmation. Auto_continuefalsemặcđịnh; khôngbậtđểtestkhiunreviewedworkeligible. Syncmộtlần,kiểmkhôngduplicate.
9. SecondBrain: exactWP391/citationversion2córeadback; semanticVN/EN**chưađạt**. KhôngcoiqueryđúngmãWP làsemanticacceptance.
10. Copykitciphertextvàbootstrap từ `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\demo-recovery-20261102T214523Z-final` sangổngoài/custodyriêng; giữrecoverykeybí mật theoDRREADME. OFF_HOST_COPY_PENDING_OWNER, chưatestmáykhác.
<!-- END_FINAL_DEMO_CURRENT -->

<!-- PHASE3_1_CURRENT -->
# Phase3.1 — current, 2026-11-02T23:14:21+07:00

MAIN Gateway `sha256:b184f91963e53df47cbc884cc353d03b0bce871ee19b45b5dc7a5ca78fd638ab`, Core `sha256:e8474e53c7f56a46cd724f4a938a33f9ba01374fbaeb4bb729499cce4fbd4e84`. OFF/active0/workerALIVE; source+pins/API verified, **OWNER UAT PENDING**. #391 vẫn BLOCKED/provider429; không resume trong phiên này. Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json` và `FINAL_TEST_RESULTS.json` schema5. Các mục cũ phía dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

## Owner manual acceptance

1. Mở Backlog, tìm391/title/run prefix. Xem đầy đủ ngày/giờ, NativeNEW và engineeringBLOCKED, Dev/provider429; đổi filter rồi chờ polling, selection/input không mất.
2. Mở Planning, tìm391; thấy plan liên quan đúng child, thời gian, short ID, related run và units; PUBLISHED không phải COMPLETED. Mở history/spec/WBS khi cần.
3. Mission: không có Agent thực thi, vẫn có #391 blocked/next action. WorkerALIVE và modeOFF không biến thành RUNNING.
4. Workforce: DevSTANDBY, last#391 blocked, 12/12calls, 11provider200, cumulative36. Cards3/2/1 columns, mở full receipts/copy, không tràn ngang.
5. Inspector #391: attemptFAILED/taskBLOCKED/NativeNEW riêng; rawcode giữ nguyên, classification429, checkpointv16, source/recovery fence; thử filters, source/diff/QA/raw. Không nhấn Resume để kiểm layout.
6. Bell/notification ERROR mở đúng run; đánh dấu đọc rồi reload phải giữ; polling không tạo duplicate. Chỉ Owner quyết định dismiss các thông báo thật.
7. Full On-Demand/Daily/Weekly: headings/lists/tables/TOC/sections, source/AI label, Raw/copy/export, mobile scroll; thử zoom200%. Không dùng report AI narrative làm evidence đã xác minh.
8. Integrations: kiểm nguồn/timestamp/latency và UNKNOWN hợp lệ; UP không chứng minh16workflows businessPASS hay DevRUNNING.
9. Nếu Owner chủ động thử controls: AUTO khi queue empty→AUTO_IDLE, OFF có confirmation/persisted state; GitHub Sync một lần→fresh fragments khôngF5/khôngduplicate. Không bắt #391 tiếp tục trước provider readiness mới và checkpoint read-back.

Không có OWNER ACCEPTED, fresh coding E2E hoặc xác nhận semantic/n8n/physical DR hoàn tất trong đợt này.


---

<!-- PHASE3_OWNER_UAT -->
# Owner UAT Phase 3 — PENDING OWNER

Mở http://localhost:18088/projects/ai-dev-demo/qldapm-ai và đăng nhập **op-owner**. Phase3 kiểm source/API/CLI/Node VM và actual Rails clone; chưa ai xác nhận browser UAT thay Owner. Gatewayce047/Core7649; exact digests/source tại `phase3-owner/final-live-verification.json`. Không cần dùng terminal/DB để làm các bước dưới đây.

1. **Đọc trạng thái ban đầu.** Live Control Bar phải cho thấy Desired OFF, Effective OFF, worker ALIVE, READY0/ACTIVE0 và lý do NO ELIGIBLE WORK ở checkpoint bàn giao. Xem heartbeat, revision và thời điểm refresh đầy đủ. Worker ALIVE không có nghĩa đang có Agent chạy. Nếu có task thật mới thì số liệu có thể khác snapshot; đọc live thay vì ép bằng số cũ.
2. **GitHub Sync một lần.** Mở GitHub & Delivery, bấm Đồng bộ GitHub ngay. Nút phải thành SYNCING, sau đó có phản hồi/correlation và Last successful sync thay đổi; PR table tự cập nhật, không F5. Bấm lại khi request trước đã kết thúc phải không tạo duplicate activity. Theo remote snapshot17:05+07, PR7/8/9OPEN, PR9basePR8; không merge chỉ để test. Nếu Owner chủ động đổi PR ngoài GitHub, sync phải phản ánh trạng thái mới; merged-to-feature không được gọi merged-to-main.
3. **AUTO idle rồi OFF.** Khi READY0/ACTIVE0, bật AUTO: phải nhận command và hiển thị AUTO_IDLE/NO ELIGIBLE WORK, không RUNNING giả hoặc tự OFF vì hết backlog. Sau đó OFF và kiểm desired/effective/read-back. Nếu READY>0, AUTO có thể chạy việc thật; chỉ bật khi Owner muốn xử lý backlog đó.
4. **RUN ONCE.** EMPTY phải disable và ghi NO ELIGIBLE WORK. Khi có PLANNED unit đủ dependency/version, chọn đúng task/unit và chạy một lần; phản hồi phải có runID/admission. Đừng bấm nhiều lần để đoán. Duplicate click trong request không tạo lượt thứ hai.
5. **Giao việc thật.** Work Intake → nhập một yêu cầu nghiệp vụ mới → gửi một lần. Kiểm planningrunID/PMBAfeedback, task/plan/unit xuất hiện trên Backlog và live feed. Không dùng lại marker `QLDAPM-E2E-20261102-PHASE2-FINAL-001` hoặc replay390. Phase3 chưa tạo fresh E2E; không cần tạo test task chỉ để tích lũyPASS.
6. **Quan sát live.** Trong Mission Control/AI Pipeline, đối chiếu WP/title/run/agent/stage/time/event/correlation. Poll interval target3sactive/15sidle/60shidden cộng thời gian API; không phải browser SLA. Không có phần trăm tiến độ giả. Khi trở lại tab hoặc mạng hồi phục, trạng thái tự refresh. DISCONNECTED/STALE phải hiện toàn trang; panel cũ được ghi rõ snapshot, không coi ALIVE cũ là hiện tại.
7. **Inspector đúng run.** Mở run390 hoặc run đang làm; xem plan/units, receipts, diff/commit, internal Reviewer/QA và logs, PR, Native/citation/n8nACK. Đổi nhanh giữa hai run không được lấy evidence runA đặt dưới runB. Review/QA internal không phải GitHub native approval. Bước Reports của run cũ có thể UNKNOWN khi không có linkage riêng; không tự gọi PASS.
8. **PAUSE/RESUME/CANCEL khi Owner muốn điều khiển một run.** PAUSE_REQUESTED/CANCEL_REQUESTED không phải tool đã dừng. Đợi effective checkpoint/terminal evidence. RESUME chỉ có khi checkpoint an toàn và version hiện hành; unknown outcome phải đối soát, không ép resume. OFF chặn admission tự động; queued jobs theo policy hiện tại có thể bị hủy trước thực thi, active worker checkpoint sau current noninterruptible operation. OFF không đồng nghĩa process đã biến mất tức thì.
9. **Timeout/409/403.** UI phải báo rejected hoặc unknown rõ ràng. Request có outcome unknown giữ UUID/khóa thao tác, không tự gửi lại. Matching receipt về có thể mở khóa đúng form. Nếu crash không có receipt hoặc đã vượt recent10, cần operator reconciliation; không đổi UUID/F5 rồi gửi lại để vượt guard. Ghi lại request/correlationID và thời gian.
10. **Reports.** Mở report list: dữ liệu tự refresh. Xem toàn văn, source CURRENT/HISTORICAL/UNKNOWN, links WP/PR, timestamp, AI chưa xác minh và usage incomplete. Report thật có provenance là `be099f56-cc9a-403c-96c2-9c958d4672dc`; report156c cũ chưa report-ID receipt mapping. Narrative không phải factual acceptance. Không cần bấm +AI để kiểm lại list/reader.
11. **Schedule và Notifications.** Mở lịch: kiểm Daily/Weekly enabled, giờ/phút/thứ. Nếu Owner muốn đổi, lưu một lần rồi mở lại để đối chiếu mọi trường; đổi một trường không được reset trường khác. Poll không ghi đè form đang sửa. Đánh dấu thông báo đã đọc phải thay persisted state, bar tự refresh.
12. **Second Brain.** Tìm exact387/389/390: citation phải đúng child và Native version2 tại checkpoint này; click mở WP. Tìm thêm câu VN/EN tự nhiên để đánh giá thật, ghi false positives/no-answer. Semantic vẫn chưa đạt benchmark; no result không chứng minh tài liệu không tồn tại. Poll giữ query/kết quả trong khi các tab khác cập nhật.
13. **n8n và demo.** Đối chiếu lifecycle event/correlation ở Gateway; WF04 retentionOFF nên không đòi full executionhistory trong n8n. WF07/WF12 vẫn PARTIAL do actor19admin bị từ chối đúng chính sách; không sửa quyền để xanh test. Demo18791health/release hiện PR6unmerged tree, chưa có PR7/8/9; tạo PR không đồng nghĩa demo đã deploy.
14. **DR Owner-only.** Đọc `phase3-owner/n8n/OFFHOST_OWNER_PROCEDURE.md`, chọn storage độc lập và giữ recovery key riêng. Checker chỉ xác nhận ciphertext bytes. Không gửi key vào chat/email/GitHub/logs. Physical-machine restore và master-key cutover chưa được chứng minh.

Ghi lỗi bằng thời gian `dd/MM/yyyy HH:mm:ss`, tab/hành động, expected/actual, command/request/correlation/run/WP/PRID. Không gửi tokens/keys/private prompts. Owner ghi kết luận từng mục PASS/FAIL/NOT TESTED; chỉ Owner quyết định **OWNER ACCEPTED**.
<!-- END_PHASE3_OWNER_UAT -->

---

# Owner manual UAT — PENDING OWNER

Phase2-final đã kiểm tra bằng source/API/CLI và clone, chưa xác nhận thao tác trên browser. Chỉ Owner ghi `OWNER ACCEPTED`. Xem `phase2-final/` cho image/source và evidence theo revision; không cộng các suite trùng nhau.

Trạng thái bàn giao 02/11/2026 08:05 UTC: mode OFF, queue0, worker ALIVE. Không chạy lại fresh marker hoặc tự tạo task E2E thứ hai. Latest AI report có provenance là `be099f56-cc9a-403c-96c2-9c958d4672dc`; report cũ 156c chưa liên kết receipt theo report ID.

Trong Project 6:

- Mission Control và Agent Workforce: đối chiếu mode, worker ALIVE/STALE, active run và receipt thực; integration chưa có health check phải ghi rõ chưa đo.
- Work Intake/Backlog/Plans: kiểm tra WP #390 của marker `QLDAPM-E2E-20261102-PHASE2-FINAL-001`, quan hệ parent #379, plan và unit tương ứng. Không gửi lại marker để tạo một test mới.
- Controls: RUN ONCE chỉ chọn unit PLANNED đủ dependency; double-click không gửi form lần hai. PAUSE/CANCEL đang chờ không được hiện như đã dừng xong; RESUME chỉ có khi checkpoint an toàn. Timeout giữ trạng thái chưa nhận xác nhận; xem run trước khi gửi lại.
- Execution Center/Inspector: trạng thái lỗi không hiện success, dữ liệu thiếu không bị thay bằng số liệu giả; output/event được hiển thị như text. Kiểm tra thời gian và refresh/polling sau chuyển tab hoặc tải lại.
- GitHub Sync: đối chiếu PR/SHA và nhánh base; merged-to-feature không đồng nghĩa merged-to-main. Không merge PR trong bài UAT này.
- Reports: đọc snapshot mới và báo cáo lịch sử; kiểm tra `CURRENT/HISTORICAL/UNKNOWN` cùng source links. AI narrative chưa xác minh phải được gắn nhãn; nguồn unavailable không được hiển thị như số 0 đã xác minh.
- Scheduling/Notifications: thử thay giờ/phút Daily và thứ/giờ/phút Weekly, tải lại để đối chiếu tất cả trường; việc đổi một trường không reset các trường khác. Kiểm tra đọc/đánh dấu notification theo quyền.
- Knowledge: exact lookup #387/#389/#390 phải mở đúng citation/version. Semantic VN/EN vẫn chưa đạt holdout gate; không lấy vài exact lookup làm nghiệm thu semantic.
- n8n: đối chiếu lifecycle observation với Gateway; WF04 retention vẫn OFF. Bảng 16 workflow chỉ có evidence adapter/clone, WF07/WF12 còn PARTIAL do actor19 admin guard; không nới RBAC để vượt bài kiểm tra.
- Demo 18791: `/_qldapm/release` và response header ghi `TEST RELEASE - UNMERGED SOURCE`, PR #6 revision `0498ceed…`. PR #7/#8 và PR từ #390 không tự được deploy.

Ghi mỗi lỗi bằng thời gian, tab/hành động, expected/actual, run/WP/PR ID; không chụp hoặc gửi token/keys. Mốc UAT bên dưới là dữ liệu lịch sử có thể dùng đối chiếu.

1. Trong Project 6, mở #387 và kiểm tra plan, PR #7, review/QA evidence, trace và report ON_DEMAND `156c3aa7-e5ad-4390-b213-c6efd697301a`; xác minh #388 được ghi rõ là replacement, không phải #385 gốc. Report có AI narrative được gắn nhãn chưa xác minh.
2. Kiểm tra Command Center hiển thị timestamp `dd/MM/yyyy HH:mm:ss` trong `Asia/Ho_Chi_Minh`, worker ALIVE/STALE, kết quả blocked/succeeded và nút resume theo checkpoint. Kiểm tra yêu cầu cancel đang chạy không bị hiển thị như đã hủy xong. Đối chiếu data với Native/GitHub, không coi trạng thái n8n engine tự nó là business success.
3. Trên demo đã deploy PR #6 tree, thử health, summary, CRUD/search bằng dữ liệu thử do Owner chủ động tạo. PR #7 chưa được deploy và chưa merge; không yêu cầu tính năng PR #7 có sẵn ở demo.
4. Tìm WP #387 trong Second Brain và mở citation; kiểm tra thêm truy vấn tiếng Việt/Anh, đặc biệt case không có kết quả. Chất lượng semantic corpus vẫn là mục OPEN.
5. Kiểm tra n8n WF04: lifecycle observation có ở Gateway, nhưng n8n success/error history hiện không lưu; đây là giới hạn đã biết. Ghi lại lỗi và thời gian nếu thấy sai lệch.

Chỉ Owner mới xác nhận human UAT PASS sau khi tự kiểm thử. Không thực hiện thao tác xóa dữ liệu hoặc merge PR nếu chưa có quyết định riêng.

Portable recovery kit: Owner cần quyết định nơi lưu off-host ciphertext và nơi giữ recovery key riêng; không gửi key vào chat, email, log hoặc repo. Hiện hai phần còn nằm local với ACL hạn chế, chưa phải off-host DR. Đọc `phase2-final/n8n/PORTABLE_RECOVERY_KIT.md` và giữ nguyên kit/backup gốc; chưa restore MAIN hoặc rotate key.

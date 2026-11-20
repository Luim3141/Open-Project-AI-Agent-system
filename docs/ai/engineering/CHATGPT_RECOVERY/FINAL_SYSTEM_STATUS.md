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

Chi tiết18câu trả lời: [FINAL_INTEGRATION_ACCEPTANCE.md](FINAL_INTEGRATION_ACCEPTANCE.md); checklist: [OWNER_MANUAL_UAT_GUIDE.md](OWNER_MANUAL_UAT_GUIDE.md).
<!-- END_CC_STABILIZATION_CURRENT_20261104 -->

<!-- AUTONOMOUS_FINAL_CURRENT_20261104 -->
# MAIN current —04/11/2026

Cập nhật 2026-11-04T09:30:39.415051+00:00 (UTC; ngày 04/11/2026 theo Asia/Bangkok). **DEPLOYED_PARTIAL — NOT_FULL_FUNCTIONAL_READY.** Các block bên dưới là lịch sử.

Gateway `sha256:f91c98823b42cb2d9499de1a8d3e3935fd59a594b6b92b3f9a4bd4cf2dc0087c`; Core `sha256:1f1b366abc88c20794992ee2df9a7227417fc3a770ca4b8abdb1e34becd82db8`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Source/runtime/pins và16published definitions khớp; Gateway/Core healthy, n8n ready, OpenClaw CLI/RPC READY, worker ALIVE/idle, queue0,531Gemini receipts không tăng. Delegation OFF/revision2. Engineering mode **PAUSED** là actual Owner18 override (audit1793775548); giữ nguyên, không giả OFF hoặc tự bật AUTO. Provider `READINESS_STALE`, gatefalse: workerALIVE không phải providerAVAILABLE.

Đã triển khai và xác minh nghiệp vụ thật của WF05/WF06/WF09 trên MAIN. Semantic RAG vẫn chưa đạt điều kiện triển khai; không coi hệ thống đã hoàn tất nghiệm thu.

Bằng chứng: [runtime hiện hành](autonomous-final/final-live-verification.json), [nghiệp vụ MAIN](autonomous-final/main-delegated-business.json), [đánh giá RAG](autonomous-final/rag-final-review.json).

**MAIN_BUSINESS_VERIFIED:** real principal25 `qldapm-demo-delegate`, non-admin, PM22, membership chỉ Project6, API key/bearer riêng. Không impersonate Owner18, không thêm general engineering/AUTO rights. WF05preview→OWNER_DELEGATED_POLICY_APPROVED→WF06execute/Native read-back có3 mutations hợp lệ trên fixture395: note BASELINE→CHECKED→BASELINE, rồi NEW1→IN ANALYSIS37, Nativev0→3. WF09preview3650→WF05decision3653→WF06execute3654→WF09current3655. Tổng9correlated n8n executions3643–3655 đều SUCCESS (không phải mọi số trong khoảng đều thuộc case). Approval tách khỏi execution; defaultOFF trả REQUIRES_HUMAN_APPROVAL, stale/action/project/role bị từ chối, duplicate không write lại.3audit reports,7durable notifications; latestaudit234ad848… CURRENT, hai audit cũ HISTORICAL. Policy finalOFF; service không tự bật lại grant đã dùng. Authenticated Owner override/disable giữ nguyên.

Fixture là NativeTask1 có `[Bug]` marker theo mapping thực Project6, không phải việc coding. Native cho NEW→IN ANALYSIS, không có37→1; description đã được bù trừ về BASELINE, fixture giữ trạng thái hợp lệ IN ANALYSIS. Không giả status rollback/QA/Done. Clone còn chứng minh stale-after-approval chặn trước Nativewrite và unknown write không blind replay. Human Owner không trực tiếp approve proposal; audit ghi đúng delegated policy.

**Semantic RAG FAILED qualification; serving RAG không đổi.** B5 replay xác định SPAN_REFERENCE_MISMATCH (span10 thay vì5); offline unique same-source pointer repair vẫn không chứng minh answer. Typed FORMAT/SOURCE/SPAN/QUOTE/SUPPORT + bounded redacted captures giữ validator chặt.

Root corpus:11/15docs có JSON bị cắt, các business fields/boolean/path mất; whole-journal candidate giữ15docs/230073chars/117journals,906typedfacts, Unicode offsets/hash. Decode trước split, phân biệt Native fields, requirements và historical receipts. Research actual BGE/Qdrant906points + FTS/identity cho **DEV retrievalHit@5=13/13 (100%)**; đây là observed correlated DEV, không phải benchmark độc lập hay serving quality.

Final answer chưa đạt: six-case semantic-fact pilot strictsupport3/4positive, no-answer0/2negative emitted; một CRUD answer còn lẫn parent379/copied objective. Warm1.424–2.827s/cold16.406s. Expanded DEV dùng lại5cached pilot replies, chỉ3generation requests mới, dừng đúng gate ở warm5.944s>5s.4positive answers được quan sát, strictsupport2/4: hai câu “initial unit/create/list/SQLite” chỉ chọn unitname nên không đủ toàn bộ evidence.17candidate citations kiểm exacthash/offset/Nativeid/version không lỗi, nhưng quote identity không đồng nghĩa semantic support. RepresentativeFPR **NOT_ESTABLISHED**;0/2negative không chứng minh≤5%. Không mở oldholdout, không tạo/scoring lockedholdout khi DEV gate còn fail, không đổi gate để gọi PASS.

Current serving vẫn metadata retrieval/answer:null, NO_EVIDENCE hoặc UNVERIFIED_RETRIEVAL. Baseline observedDEV Hit2/13/FPR1/20 là lịch sử của serving baseline, không lấy candidate13/13 gán cho MAIN. Không có qualified RAG image hoặc postdeploy semantic E2E mới. Source-grade nghiên cứu không thay cho retrieval→evidence→answer→citation acceptance. Chỉ WP392 threeintents từng được Owner xác nhận; các nhãn khác là assistant source review, không gọi human ground truth. Lượt tiếp tục này11local4B requests,0Gemini mới, không tải/đổi model hoặc trả phí.

Essential FAILED: Semantic RAG complete-answer/evidence selection và worst-case latency/representativeFPR chưaqualified; candidate khôngdeploy, MAINsemanticE2E chưachạy. PUBLICATION_REDACTED_UAT: browser interactions/accessibility/loading/error/links; WAITING_FOR_SCHEDULE: current WF12 wallclock. Preserved partial:8WP385 unmatchedvectors/2historicalDEAD và persistedproviderREADINESS_STALE. Không tuyên bố FULL FUNCTIONAL DEMO READY.

Tiếp tục duy nhất có ích: sửa complete-evidence selection/parent-copy ambiguity và ổn định latency với gate5s giữ nguyên; đóng băng nguồn+code+broaderdevelopment/lockedholdout labels có source review trước khi score; chỉ sau tất cảqualitygates mới tích hợp serving/rollout/RAGMAINE2E. Không replay các private consumedintents (`main-setup-intent`, `main-delegated-acceptance-intent`, pilots/DEV) hoặc tự kích lại delegation/AUTO. Một root làm tuần tự; không spawn thêm subagent. Inventory hiện tại không chứng minh được tài khoảnCodexkhác đã hoàn tất; không gọi đó là verified.
<!-- END_AUTONOMOUS_FINAL_CURRENT_20261104 -->

<!-- FUNCTIONAL_CURRENT_20261104 -->
Cập nhật 2026-11-03T20:13:07.428616+00:00. **DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY; OWNER_ACCEPTANCE_PENDING.** Phần phía dưới block này là lịch sử.
Gateway `sha256:a6fe1d61982db84447f45eb35a56809ae4ab16d854012bec59db1f58d890b2be`, Core `sha256:91afae9c6855417dcc14828d0bd16b3a5b780439d7d1fbbfede64c64241d83d4`, n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Source/pins, OFF/active0, worker và provider gatefalse: [integration-final/functional-completion/final-live-verification.json](integration-final/functional-completion/final-live-verification.json).

WP394/run301dbdd8: **succeeded**, 43 generation receipts, recovery_count=5; PR https://github.com/Luim3141/mini-task-manager/pull/12. Một coding task, cùng run qua các continuation; không replay391/385, không merge/deploy PR mới. Dev hoàn tất, Review/QA PASS, host acceptance 57 tests PASS; Native394 vẫn NEW, tách biệt với engineering delivery và Owner acceptance.
RAG chưa đạt. Serving baseline trên observed DEV: Hit@5=2/13 (15.38%), FPR1/20 (5%); chưa có benchmark mới được chứng nhận. Reader candidate DEV Hit@5=6/13 (46.15%), support3/13, FPR4/20 (20%) bị REJECTED và không deploy. Owner đã xác nhận3intents WP392;6cards VN/EN tương quan không phải benchmark đại diện hay phê duyệt candidate.
Còn mở: semantic answerability/quality + independent evaluation; Owner UI UAT; WF05/06 Owner decision; WF09 approved Project6 mapping/transition; actual WF12 current-period cron. Historical WF13/WP385 DEAD và WF10 old plan chứa385 được giữ, không force retry.
Authority: `FINAL_INTEGRATION_ACCEPTANCE.md` current block.
<!-- END_FUNCTIONAL_CURRENT_20261104 -->

<!-- FULL_INTEGRATION_20261103_CURRENT -->
# Full integration — MAIN 03/11/2026

**DEPLOYED_PARTIAL / NOT_FUNCTIONAL_DEMO_READY.** Gateway e9af9565/Core b5f3913a healthy; n8n 05376355 running, no Docker healthcheck. OFF/active0, worker heartbeat, provider gate false, 484 receipts; #391 succeeded checkpoint39/45 calls, không resume. Exact source/image/pins: `integration-final/final-live-verification.json` (13:03Z).

GitHub tự poll hai lần 11/10 rồi 11/0; Demo `01d765c` là unmerged integration, PR6–11 OPEN. 138 event receipts có n8n success; không còn pending/retry/sending, một WP385 DEAD được giữ. WF01 P6 file/readback PASS; WF12 human READY; WF16 HEALTHY sau recovery; 16 workflow clone PASS có phạm vi, không chứng minh mọi branch MAIN. Project5 12 bảng nguyên/users18 chỉ login timestamps.

RAG không đạt, candidate chưa deploy; Computer Use bị tool policy dừng trước scenario, Owner acceptance PENDING. 74 Windows qualification tests PASS; pinned Gateway Linux 73 PASS/1 SKIPPED. Bảng 16 workflow, 15 câu trả lời và evidence links: `FINAL_INTEGRATION_ACCEPTANCE.md`.
<!-- END_FULL_INTEGRATION_20261103_CURRENT -->

<!-- FINAL_DEMO_CURRENT -->
# Final Demo — 03/11/2026

**Đã triển khai và xác minh các phần runtime, n8n, khôi phục #391 và backup. Chưa đạt nghiệm thu toàn bộ vì semantic RAG còn FAILED; Owner Browser UAT vẫn PENDING.**

| Câu hỏi Owner | Kết quả đã kiểm chứng |
|---|---|
| 1. Bao nhiêu workflow business PASS? | 16/16 kịch bản hợp lệ có giới hạn trên clone thực. Không khẳng định mọi nhánh generation, approval và failure đã được nghiệm thu. |
| 2. WF07/WF12? | Daily và Weekly collectors trên MAIN đều READY 4/4 cho actor20–23; actor19 vẫn bị từ chối. Daily đi qua webhook MAIN; Weekly dùng đúng signed scheduled contract trên MAIN và chạy nhánh schedule qua webhook giới hạn trên clone. Chưa chờ một lần cron theo giờ thực. |
| 3. WF04 history? | Có execution3074 SUCCESS được lưu, chứa event RUN_COMPLETED của chính #391 và khớp Gateway ACK. Retention success/error đã bật; pruning720 giờ/10000 executions. 671 execution trước cutover và credentials được bảo toàn. |
| 4. OpenClaw READY? | Có: HTTP /readyz và CLI/RPC thực, kèm timestamp. Runtime được fence sau delivery; trạng thái DOWN trong lúc fencing phải hiển thị đúng, idle Gateway hiện đã khởi động lại. |
| 5. Demo18791? | UP từ /healthz, không còn UNKNOWN do thiếu adapter. Demo release chưa chứa PR10 chưa merge. |
| 6. Semantic RAG? | Holdout baseline Hit@5 3/20, false positives0/20; candidate13/20 nhưng false positives14/20. Candidate bị loại, không deploy hoặc tune lại holdout. Exact citation #391/version2 hoạt động riêng. |
| 7. Gemini429? | Đã deploy per-request shared limiter, headroom10RPM/175KTPM, durable cooldown, Retry-After/RetryInfo/backoff+jitter và retry hữu hạn. AUTO continuation vẫn opt-in, cần fresh readiness/checkpoint/source/budget và tôn trọng OFF/PAUSE/CANCEL; không tự coi hết cooldown là provider hồi phục. |
| 8. #391? | SUCCEEDED trong đúng một continuation mới của cùng run b7fd6aec-3357-495f-b9e5-f7ba04d67ad6. 9 generation calls mới, tổng45; checkpoint39 COMPLETE. Dev/Reviewer/QA, 37pytest PASS; PR10 OPEN, chưa merge/deploy. Native391 vẫn NEW/version2; không ép trạng thái nghiệp vụ thành Done. |
| 9. Backup restore? | LOCAL_RESTORE_VERIFIED cho8 nhóm: n8n credentials/server, Native/Core, Gateway/Knowledge, Qdrant, OpenClaw runtime, source/config/demo, Ollama model files. Archive mã hóa2.682GB,53 snapshots. Chưa copy off-host hoặc thử cài lại máy vật lý. |
| 10. MAIN image/source? | Gateway3c065590, Core5936d90e, n8n05376355. Full digests, source hashes, pins và worker/gate read-back ở demo-final/final-live-verification.json. |
| 11. Project5 thay đổi? | Không:13 nhóm dữ liệu đối chiếu giống hệt,341WP/344relations/968journals. Không có Native write vào Project5. |
| 12. Owner defer? | n8n master-key rotation, historical secret cleanup, legacy snapshot audit, enterprise hardening và full physical-machine DR. Giữ key đang hoạt động;4/4 credentials đã decrypt và chạy nghiệp vụ được. DEFER không phải PASS. |
| 13. Chức năng demo FAILED? | Semantic RAG VN/EN chưa đạt gate80%Hit@5/<=5%false positives. Đây là lỗi chức năng còn mở, không thuộc security defer. |
| 14. Owner thử gì trên web? | Workforce/Mission/Backlog/Inspector #391 và PR10; notification click/dismiss; Report Reader/Raw/TOC; Integrations; n8n execution3074; responsive/zoom200%; controls và GitHub Sync theo hướng dẫn. Không Resume #391 đã hoàn thành. |

PR: https://github.com/Luim3141/mini-task-manager/pull/10 — head1914f10d3bd0b2b05459914100c53549f63d0bc5, base là feature branch, không phải main.

Hiện tại: mode OFF, queue active0, Worker ALIVE, provider gate OFF. Một probe public riêng trảHTTP200/24tokens; không inference qua health polling. Tổng provider receipts474→484. Fresh coding task mới0/1; continuation #391 đã dùng1/1. Không GUI, paid service, key rotation, auto-merge hoặc reset DB.

Bằng chứng chính: [ma trận demo](DEMO_COMPLETION_MATRIX.md), [161 Gateway tests](demo-final/gateway-candidate-final.json), [Core clone](demo-final/core-clone-result.json), [workflow matrix](demo-final/n8n/BUSINESS_MATRIX.md), [#391 proof](demo-final/wp391-delivery-proof.json), [RAG holdout](demo-final/rag/RESULT.md), [restore cuối](demo-final/dr/restore-final.json), [hướng dẫn Owner](OWNER_MANUAL_UAT_GUIDE.md).

Kit private: C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\demo-recovery-20261102T214523Z-final. SHA256 ciphertext a94624d7f2339dc64accfe853e4f87a589a919bdeeddf22d42ad23420a857350. Theo [DR README](demo-final/dr/README.md) để copy ciphertext/bootstrap và giữ recovery key theo custody riêng. OFF_HOST_COPY_PENDING_OWNER.

Các phần phía dưới là lịch sử; dùng trạng thái Final Demo này để vận hành.
<!-- END_FINAL_DEMO_CURRENT -->


<!-- PHASE3_1_CURRENT -->
# MAIN — Phase 3.1 Owner UAT recovery

Checkpoint **2026-11-02T23:14:21+07:00**. Gateway `sha256:b184f91963e53df47cbc884cc353d03b0bce871ee19b45b5dc7a5ca78fd638ab`, Core `sha256:e8474e53c7f56a46cd724f4a938a33f9ba01374fbaeb4bb729499cce4fbd4e84`, n8n `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`.

**SOURCE FIXED / CANDIDATE TESTED / DEPLOYED / API VERIFIED; OWNER UAT PENDING.** Core/Gateway healthy, worker ALIVE, mode OFF, active0. Exact21 serving source files và pins đã kiểm tra; worker giữ protocol, nhận cap Gateway bằng một dòng đã có regression. Không Computer Use, không resume/tạo lại #391, không inference/provider probe, không tăng production cap để PASS.

#391: engineering BLOCKED/attempt FAILED; Native business status **NEW**. Ba Dev sessions: 12/12HTTP200, 12/12HTTP200, 11HTTP200+1HTTP429; tổng36 calls. Lượt đầu dừng do cap nội bộ; lỗi gần nhất là upstream429. Checkpointv16 còn nguyên; raw historical result/queue/checkpoint/Native row giữ nguyên hash, provider receipt count474 không đổi. Không có evidence phân biệt RPM/TPM/RPD hoặc thời điểm reset. Resume hiện bị fence `PROVIDER_RECOVERY_REQUIRED`; readiness đã lưu cũ không phải bằng chứng provider phục hồi.

UI: WP ngắn/ngày giờ đầy đủ, search/filter/selection, Current/Recent Work, Agent Current State + Last Activity, summary budget/checkpoint, durable child/run notifications, plan versions, structured sanitized Markdown/TOC/raw/export, health có nguồn/timestamp. #379 là Native **Task**, một record với hai engineering unit references; bỏ nhãn Epic giả, không xóa dữ liệu.

Validation: final immutable Gateway **105 tests PASS** (Owner recovery22 là tập con); final Core actual Rails/Native/login/session/CSRF/full-template clone PASS; Node VM polling/Inspector/reader/filter và Ruby Markdown/XSS/long-document PASS. Host163 PASS thuộc revision trước follow-up, không dùng để chứng nhận toàn source cuối hoặc cộng dồn. MAIN signed Rails→Gateway/API + production ERB read-back PASS; nhãn identity cuối được kiểm trên clone và serving hashes. Project5: toàn cột13 bảng scoped/global không đổi; 341WP/344relations/968journals. Không phải kiểm mọi bảng hoặc whole-image coding E2E.

Remaining: provider429/#391 chưa hoàn tất; Owner Browser UAT/pixel/200%zoom pending; historical checkpoint time không có timestamp đáng tin nên UNKNOWN; OpenClaw/Demo health UNKNOWN do thiếu safe endpoint đã cấu hình. In-app không bảo đảm báo khi đóng web. Semantic RAG FAILED/PARTIAL, n8n master-key/history OPEN/BLOCKED, WF04 retentionOFF, WF07/WF12 PARTIAL, off-host custody/physical DR PENDING giữ nguyên.

Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json`, `phase3_1/main-readback.json`, `FINAL_TEST_RESULTS.json` schema5. Các block cũ bên dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

<!-- PHASE3_CURRENT -->
# MAIN — Phase 3 Owner Control / Live Observability

Checkpoint **02/11/2026 17:27 +07:00** (signed status `2026-11-02T10:27:06.538856+00:00`; source/pin parity kiểm lúc17:14). Gateway `sha256:ce047f82692e7c46db1ddcb675be85d43a99936f0859e055db5513219a9ab6d4`, Core `sha256:7649e1f923e6af20ea6d3eb8820ff4d4466840728893374846b7875893e9bcc2`, n8n `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`. Gateway/Core healthy, n8n readiness200; worker ALIVE, mode **OFF**, active/executing **0**, provider gate false. 17 serving-source hashes và persistent image pins khớp. Phase2 bên dưới là lịch sử.

**Ba lỗi Owner báo:** SOURCE FIXED → TESTED IN CLONE → DEPLOYED → API VERIFIED; **PENDING OWNER UAT**. Không ghi OWNER ACCEPTED hoặc dùng tests để bác bỏ quan sát browser của Owner.

- GitHub Sync: một authenticated JSON POST có request UUID/correlation; API success trả fresh server fragments cho PR/reports/run/controls. Rails cache-control API giữ no-store sau callback chung. Actual signed Rails→Gateway sync hai lần SUCCESS, đều `changed=false`; replay cùng UUID trả exact cached response. PR7/8/9 vẫn OPEN/stacked theo remote read-back; không merge.
- Controls: desired/effective mode, revision, worker health, queue eligibility và receipt tách bạch. AUTO idle không tự chuyển OFF; admission check lại AUTO trong transaction. Durable request reservation bind actor/project/action/arguments, same-key replay không làm lại; unknown pending không tự replay. MAIN đã đọc lại OFF với Owner18; AUTO/RUN ONCE/PAUSE/RESUME/CANCEL failure matrix ở fixture/clone, không fault-inject MAIN.
- Live activity: Gateway persisted events/agent receipts/checkpoints → 10-stage pipeline và feed có timestamp/correlation/evidence. Polling single-flight 3s active /15s idle /60s hidden, timeout12s, refresh khi online/tab active, không để response cũ ghi đè command mới. Mất kết nối báo STALE/UNKNOWN ngay trên control bar. Run390 chiếu đúng PM/BA/Dev/Reviewer/QA/GitHub/Native/n8n/RAG evidence; Reports theo run giữ UNKNOWN do không có linkage. Không phải fresh coding E2E trên Phase3.

**Second Brain operational recovery:** Project5 activity404 tại WP175 khiến scan chung bỏ qua Project6. Tách lỗi từng scope và tick reporting; MAIN hiện **10/10** nguồn Project6 trong mẫu khớp current Native/SQLite/Qdrant, exact387/389/390 citation/version2 đạt. Không thay cosine0.65/chunk600/100/model. Semantic benchmark vẫn **FAILED/PARTIAL**; không dùng exact lookup hoặc freshness để tuyên bố semantic recovery.

**Tests:** 74 immutable Gateway candidate tests PASS; host engineering suite162 PASS trên Gateway source tương ứng (complete manifest đổi do Core chỉnh trong lúc chạy, ghi rõ trong index); final Core7649 actual Rails login/session/valid+invalid CSRF/JSON/fragments/no-store/knowledge cards clone PASS; Node VM transport/Inspector/reader PASS. Không cộng overlapping suites/revisions. Runtime/source proof: `phase3-owner/final-live-verification.json`; test index schema4.

**Dữ liệu:** 13 scoped Project5/global security/config tables so sánh toàn cột trước/sau cả rollout, không đổi;341 WP/344 relations/968 journals. Không phải chứng nhận mọi bảng DB. Phase3 không tạo coding task, không gọi paid provider, không dùng GUI. Demo vẫn PR6 unmerged test release.

**Remaining:** semantic relevance/answerability chưa đạt; n8n master-key migration/history/arbitrary payload persistence BLOCKED, WF04 retention OFF; WF07/WF12 PARTIAL vì actor19 admin bị từ chối đúng guard; off-host custody/physical DR và Owner UAT PENDING. New ciphertext-only copy checker10PASS/1privilege-skip; không copy key hoặc tự chọn remote destination.

Evidence chính: `OWNER_CONTROL_AND_LIVE_OBSERVABILITY_EVIDENCE.md`, `phase3-owner/ACCEPTANCE_MATRIX.json`, `phase3-owner/REVIEW.md`, `FINAL_TEST_RESULTS.json`. Owner UAT: `OWNER_MANUAL_UAT_GUIDE.md`.
<!-- END_PHASE3_CURRENT -->

# MAIN — Final Stabilization Phase 2

Snapshot 02/11/2026: Gateway `sha256:8359e250512b0a68a6e92892feb539d6f392b94aa39b91e670db42f49c411e8a`, Core `sha256:a6a61b685014039049f46d1d93a90340d4108265dccbed93cc6d04fbe3f027fd`, n8n `39299c21…`. Gateway/Core healthy; worker đang chạy, queue rỗng, mode **OFF** theo final read-back 08:05 UTC (PAUSED là snapshot trung gian sau test). Docker Desktop khởi động lại bằng CLI lúc 07:20 UTC sau khi engine ngừng phục vụ; image pins và kết quả run được bảo toàn.

**Engineering integrity — DEPLOYED / LIVE VERIFIED trong phạm vi bài coding.** Claim có worker UUID, token và generation lưu bền vững. Gateway transaction, knowledge SQLite commit và Qdrant mutation kiểm tra quyền claim. Host singleton lock giữ OpenClaw qua cleanup. Independent review tìm hai lỗi Important, đã có test đỏ/xanh sửa trước rollout. Request đã gửi ra hệ thống ngoài vẫn cần journal/read-back; token cục bộ không thể thu hồi request đó.

**Fresh E2E — succeeded.** Marker `QLDAPM-E2E-20261102-PHASE2-FINAL-001`: planning `8751d17a…` → WP #390, development `447d4fd9…` → PR #9 OPEN, commit `4a794e2b…`. OpenClaw Dev, reviewer đúng diff và QA thực thi; 32 acceptance tests đạt, một deprecation warning. Planning có 9 ACK, development có 13 ACK khớp observation/correlation. Không cần resume, không merge. Bài coding chạy trên Gateway `bca2ff25…` / Core `a6a61b68…`; các patch reporting sau đó được kiểm tra riêng. Giới hạn một fresh task đã dùng hết.

**Reporting — DEPLOYED / LIVE VERIFIED.** Nguồn unavailable trả unknown/PARTIAL; timestamp có offset, usage lấy generation receipts đúng Project 6, dữ liệu thiếu được ghi incomplete. On-Demand/Daily/Weekly có WP #390 và PR #9, đọc lại CURRENT. Narrative mới `be099f56-cc9a-403c-96c2-9c958d4672dc` có hai receipt LIVE_SUCCESS liên kết report ID và nhãn “chưa xác minh”. Chỉ gửi aggregate metrics, một generation/hai HTTP attempts, không retry. Report cũ `156c…` chưa có liên kết receipt theo report ID; không sửa bằng suy đoán.

**Semantic RAG — PARTIAL, chưa đạt acceptance.** Citation lấy Native ID từ metadata SQLite đã xác minh; exact lookup #387/#389/#390 đúng version/citation. Candidate chunk expansion và ONNX reranker đều bị loại vì tăng false positives trên holdout. Reranker đạt Hit@5 10→19/24, p95 4,12 giây, RAM khoảng 548 MiB nhưng false positives 0→2/20. Không đổi chunking/threshold production. Thử nghiệm evidence clauses trên 12 file thực đã dừng ở dev: Hit@5 7/28, negatives 0/20, p95 0,95 giây, RAM khoảng 549 MiB; gate chất lượng ≥2/3 không đạt. Holdout mới 30 positive/20 negative chưa sử dụng. Không deploy candidate; file-only corpus cũng không thay cho nghiệm thu Native corpus. Nhãn do agent đọc nguồn, Owner chưa adjudicate.

**n8n security — MASTER_KEY_CUTOVER_BLOCKED.** Persisted deployment DEKs vẫn wrapped bằng old master key. Import bốn ciphertext mới không đủ để vendor decrypt thành công. Old-key encrypted restore/decrypt 4/4 và hai server starts đạt; new-key business/DR khác profile chưa đạt. WF04 retention OFF; arbitrary payload và historical secrets vẫn OPEN. Strict lifecycle schema/projection của Gateway có test riêng, không chứng minh mọi webhook n8n an toàn.

**16 workflows — adapter evidence có giới hạn.** 49 checks dùng actual published definitions và synthetic Gateway. 14 workflow VERIFIED_IN_CLONE trong phạm vi adapter; WF07/WF12 còn PARTIAL trên MAIN do actor 19 là admin và bị guard từ chối đúng chính sách. Không nới RBAC, không tuyên bố 16 business E2E PASS.

**UI / demo / dữ liệu.** Core clone chạy Native API và render toàn bộ template; Node VM kiểm tra XSS, submit, polling và schedule. OWNER UAT PENDING. Demo vẫn PR #6 tree `0498ceed…`, endpoint/header ghi TEST RELEASE - UNMERGED SOURCE; health/summary 200 và SQLite không đổi qua wrapper update. Project 5: 341 WP, 344 relations, 968 journals, 967 work_package_journals cùng membership/version được giữ nguyên toàn cột; global settings và quyền không đổi. Chỉ user 18 có thay đổi last_login_on/updated_at quan sát được.

Evidence theo revision/image/command/time tại `phase2-final/` và `FINAL_TEST_RESULTS.json`. Không cộng suite trùng hoặc PASS từ revision cũ. Không FULL SYSTEM PASS hoặc OWNER ACCEPTED khi các gate còn mở.

## Final read-back — 2026-11-02 08:05 UTC

`phase2-final/final-live-verification.json`: Gateway/Core healthy, n8n readiness HTTP 200, worker heartbeat 1,16 giây, scheduled task Running; mode **OFF**, active/executing queue **0**, provider gate false. Mode PAUSED ở snapshot trước là trạng thái trung gian, đã đổi qua authenticated Gateway HTTP và SQLite read-back theo yêu cầu M8. Exact runtime source hashes và image pins khớp. 16 workflow có published version; chỉ 15 draft trùng published, WF12 đã có boundary draft/published riêng trong audit.

Final engineering regression trên source hiện tại: **146 tests PASS**, manifest không đổi trong run; reporting candidate hiện tại **21 checks PASS**. Chúng là hai phạm vi khác nhau, không cộng dồn. Index `FINAL_TEST_RESULTS.json` schema 3 giữ command/UTC/image/environment/hash của 18 records, gồm cả failed/historical records. Không còn container thí nghiệm RAG active trong inventory 12 container do agent sở hữu.

Portable AES-GCM old-key recovery kit đã được root verify độc lập: restore/decrypt 4/4 credentials, published/sharing 16/16, tamper/wrong-key/wrong-AAD bị từ chối. Đây là cold snapshot cũ, không phải new-key migration hoặc physical DR; off-host copy và Owner giữ recovery key riêng còn PENDING. Chưa sửa MAIN master key/history.

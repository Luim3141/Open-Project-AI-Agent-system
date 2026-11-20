<!-- TELEGRAM_OBSERVER_CURRENT_20261106 -->
# MAIN current — Telegram Commander và Agent Studio

Đã triển khai local ngày06/11/2026: bot `@qldapm_commander_bot` pair Owner thật, exact `gemini-3.5-flash-lite`, shared Observer API/Agent Studio và outgoing n8n workflow riêng. Fresh Task397 regression cho `/healthz` đã qua BA/PM, Dev/Reviewer/QA,63testsPASS và Owner nghiệm thu: DONE/v11,8gatesPASS; TASK_COMPLETED SENT/message16. Main UI397 desktop/mobile/canonical snapshot/51events/reload/project denial PASS. Control cuối OFF, queue0; không replay task cũ, không merge/deploy PR14, không đổi Coding Agent credentials/config.

Source branch `codex/telegram-agent-observer`, feature commit `4f2810b`; final images/evidence/limitations và journal-order fix ở [báo cáo](../../docs/telegram-observer/FINAL_REPORT.md). [Vận hành/pair/revoke/rollback](../../docs/telegram-observer/OPERATIONS.md). Không dùng các image/revision lịch sử bên dưới làm proof cho rollout mới. RAG/performance/global qualification cũ không được tính là đã sửa bởi feature này.

Live conversation cuối PASS: Owner input19 reply completion16→Task397, vượt memory391, Gateway/Gemini thật và actual Telegram answer20. Có audit reply provenance,38bot testsPASS; proof `docs/telegram-observer/live-reply-397.json`. Lượt cũ thiếu reply metadata chưa xác định nguyên nhân lịch sử, không giả thành đã tìm được root cause.
<!-- END_TELEGRAM_OBSERVER_CURRENT_20261106 -->

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
# MAIN current — Control Center/Reports

Cập nhật 2026-11-04T16:22:32.919239+00:00 UTC (Asia/Bangkok,04/11/2026). **FUNCTIONAL_REPAIRS_VERIFIED — PERFORMANCE_GATE_OPEN**; chưa chứng nhận `AI_CONTROL_CENTER_DEMO_READY` hoặc FULL FUNCTIONAL PASS. Các block bên dưới là lịch sử.

MAIN: Gateway `sha256:698224aa0ddc88808ebab30b4705dfe7050b09db67b8ae3fc4a569d6a8447e1c`; Core `sha256:1a8f2528da78860faa69610568985471e26136d441a594f4f098c045ca181189`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Images/source/pins được read-back; Gateway/Core healthy, n8n readiness200. Final PAUSED, queue0, workerALIVE, delegationOFF;21coding runs/531provider receipts giữ nguyên. Project5 scoped rows và global config/security tables bảo toàn; chỉ cho phép timestamp đăng nhập User thay đổi.

Native386/387/389/390/391/394 đã READY FOR RELEASE/v10 qua workflow thật và journal của principal25; không tự DONE.391/b7fd và394 vẫn SUCCEEDED, không replay. PR11MERGED/main, PR12OPEN; Demo artifact giữ nguyên. RAG algorithms đóng băng/FAILED; provider readiness riêng, không coi workerALIVE là inferenceREADY.

Report Reader đã sửa trên MAIN: CSP nonce, Turbo cache restore, timeout15s, không ghi đè response cũ; Daily6766ký tự/6sections/Raw Markdown, audit có facts/provenance thay vì trang trống. GitHub Sync hiển thị ACK→operation→COMPLETED — NO CHANGES/12checked/0changed mà không F5. Artifact caption ghi rõ metadata lịch sử; trạng thái merge hiện hành lấy từ bảng PR.

Gateway HTTP5samples: trước p50=9.8377s/samplep95(max)=18.9763s; sau p50=7.2148s/samplep95(max)=12.8446s. Mục tiêu initial usable<4s chưa đạt; warm UI paint<200ms chưa có phép đo riêng. Core observed GitHub Sync ACK1913.38ms là một mẫu, không phải p95. Gateway hiện1CPU/384MiB, có sample saturation~100% khi đo. Không tăng quota hay đổi nơi lưu DB để che giới hạn. Cần tiếp tục tối ưu/read-path load qualification trước chứng nhận Demo Ready.

Bằng chứng: [runtime](cc-stabilization/final-live-verification.json), [166 image regressions](cc-stabilization/image-regression-reports.json), [exact clone qualification](cc-stabilization/clone-qualification-caption.json), [browser](cc-stabilization/browser-uat.json), [Project5](cc-stabilization/native-integrity-after.json). Không đổi GitHub source/merge, Demo, RAG algorithms hoặc DR.
<!-- END_CC_STABILIZATION_CURRENT_20261104 -->

<!-- AUTONOMOUS_FINAL_CURRENT_20261104 -->
# MAIN current —04/11/2026

Gatewayf91c9882/Core1f1b366a/n8n05376355; exactproof `docs/ai/engineering/CHATGPT_RECOVERY/autonomous-final/final-live-verification.json`. Principal25/fixture395 WF05/06/09 MAIN_BUSINESS_VERIFIED, delegationOFF/revision2; actualOwnerPAUSED preserved,queue0,workerALIVE/providergatefalse,531receipts.391/394SUCCEEDED; no replay/newcoding/GitHub/Demo/DR. SemanticRAGcandidateFAILEDqualification, notdeployed; browserPENDING, WF12currentwallclockWAITING. Read current16answers in FINAL_INTEGRATION_ACCEPTANCE.md; olderblocksbelowarehistory.
<!-- END_AUTONOMOUS_FINAL_CURRENT_20261104 -->

<!-- FUNCTIONAL_CURRENT_20261104 -->
# MAIN current04/11/2026

Authority: `docs/ai/engineering/CHATGPT_RECOVERY/FINAL_INTEGRATION_ACCEPTANCE.md` current block; `integration-final/functional-completion/final-live-verification.json`.
Gatewaya6fe1d61/Core91afae9c/n8n05376355, OFF/active0/provider gatefalse/workerALIVE. WP394/run301dbdd8 SUCCEEDED/PR12 OPEN/57tests;43calls, recovery5. WP391/b7fd SUCCEEDED unchanged/PR10/checkpoint39; never replay. One coding task admitted; private intent consumed, never prepare/intake/run again. No new Codex subagents; root continues sequentially. RAG FAILED/candidates rejected; Owner UAT and WF05/06 decision pending, WF09 transition pending approved mapping, WF12 actual cron awaits schedule. Exact source/images/counters must be read from new evidence, older blocks below are history.
<!-- END_FUNCTIONAL_CURRENT_20261104 -->

<!-- FINAL_DEMO_CURRENT -->
# Final Demo03/11/2026

Authority: `docs/ai/engineering/CHATGPT_RECOVERY/FINAL_SYSTEM_STATUS.md`, `DEMO_COMPLETION_MATRIX.md`, `demo-final/final-live-verification.json`. Gateway3c065590/Core5936d90e/n8n05376355 deployed; OFF/active0/workerALIVE. #391SUCCEEDED/PR10OPEN/checkpoint39, oneauthorizedcontinuationused. 16boundedbusinessscenariosPASS, WF04history/WF07/12verified. LOCAL_RESTORE_VERIFIED/offhostOwnerpending. SemanticRAGFAILED/candidaterejected; OwnerUATPENDING. Oldblocksbelowarehistory; do notresume391/rotatekeys/reseed.
<!-- END_FINAL_DEMO_CURRENT -->

<!-- PHASE3_1_CURRENT -->
# MAIN current — Phase3.1, 02/11/2026

Authority: `docs/ai/engineering/CHATGPT_RECOVERY/FINAL_SYSTEM_STATUS.md`, `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json`. Gateway b184f919 / Core e8474e53 đã deploy, source/pins verified; OFF/active0/workerALIVE/provider gate false. #391 checkpointv16 giữ nguyên, latest upstream429 RESOURCE_EXHAUSTED, không tự Resume. Owner Browser UAT và provider recovery chưa xác minh. Các blocks Phase3/Phase2 phía dưới là lịch sử; không dùng pins cũ để vận hành MAIN.
<!-- END_PHASE3_1_CURRENT -->

<!-- PHASE3_CURRENT -->
# MAIN — Phase3 Owner Control / Live Observability

Gatewayce047/Core7649/n8n392; final17:14+07OFF/queue0, workerALIVE, provider gatefalse. Authoritative current status: docs/ai/engineering/CHATGPT_RECOVERY/FINAL_SYSTEM_STATUS.md firstblock, phase3-owner/final-live-verification.json, OWNER_CONTROL_AND_LIVE_OBSERVABILITY_EVIDENCE.md and FINAL_TEST_RESULTS schema4. P0 fixes deployed/API+cloneverified; browserUAT PENDING OWNER. Source mostlyuntracked; useexact hashes, nothistoricalGitHEAD. No replay390/newE2Eneeded;Phase3newcodingtaskcount0. RAGfreshness10/10samplecurrent, semanticqualityPARTIAL; n8nkey/history/WF07/12/DRblockersremain. Old blocks below historical.
<!-- END_PHASE3_CURRENT -->

<!-- FINAL_STABILIZATION_PHASE2_CURRENT -->
# MAIN — checkpoint 02/11/2026

Authority: `docs/ai/engineering/CHATGPT_RECOVERY/FINAL_SYSTEM_STATUS.md`, `CONTINUATION_HANDOFF.md`, `FINAL_TEST_RESULTS.json` và evidence `phase2-final/`.

Gateway8359e250/Corea6a61b68/n8n39299c21 đã deploy. Fresh E2E duy nhất mới WP390/PR9 succeeded trên coding Gatewaybca; reporting patches sau đó có candidate/API evidence riêng. Final 08:05 UTC: mode OFF/queue0, worker ALIVE, provider gate false; source/images/pins match. Docker CLI restart recovery đã giữ run/pins. Không replay run hoặc tạo thêm task E2E theo lịch sử phía dưới.

Semantic RAG, n8n master-key/history, 16 business E2E và Owner UAT chưa được chứng nhận hoàn tất. WF04 retentionOFF; chỉ Owner quyết định OWNER ACCEPTED. Không Computer Use, Project5 writes, reset/clean dữ liệu, paid provider hoặc PR merge. Image/source hashes cụ thể phải đọc live, các checkpoint cũ dưới đây là lịch sử.
<!-- END_FINAL_STABILIZATION_PHASE2_CURRENT -->

<!-- CHATGPT_RECOVERY_MAIN_30218AFF -->
# MAIN hiện hành — approved recovery patch30218aff

**DEPLOYED_TO_MAIN_READ_SMOKE_VERIFIED_WITH_LIMITS**, `2026-11-01T14:58:00.485036+00:00`. Gateway1c102481/Corec237e4a7/n8n9e8d3393;15 runtime file hashes match; WF04 thêm lifecycle adapter và retention/redaction,16 workflows active. Host worker đã restart, heartbeat ALIVE/idle, modeOFF/active0/provider receipts358. Project5=341/maxlock4 và379status7/lock4 giữ nguyên; credentials/TOTP/history được đối chiếu bảo toàn.

Authority: `docs/ai/engineering/CHATGPT_RECOVERY/MAIN_ROLLOUT_RESULT.md` và `docs/ai/engineering/CHATGPT_RECOVERY/rollout-20261101T110426Z/deployment-result.json`. Những image/title COMPLETE/UAT bên dưới là lịch sử. Không replay run, re-provision hoặc restore DB theo lịch sử cũ. Positive MAIN lifecycle/provider business E2E chưa chạy; UI PENDING OWNER MANUAL UAT. Demo18791/WP385/history cleanup/credential rotation không nằm trong rollout này.
<!-- END_CHATGPT_RECOVERY_MAIN_30218AFF -->

<!-- PHASE2_CONTINUATION_CURRENT -->
# Current Phase2 continuation

FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Authority: docs/ai/engineering/HANDOFF_GEMINI_LATEST.md, IMPLEMENTATION_STATE.json, FEATURE_COMPLETENESS.md, THREE_REPOSITORY_INTEGRATION.md and deployment.json. Existing historical image/UAT statements below are baseline, not current serving proof. No computer use or full regression requested. Main source uncommitted; preserve current snapshot/untracked. Read current runbook before any installer/deploy/replay.
<!-- END_PHASE2_CONTINUATION_CURRENT -->

<!-- AUTOMATION_STABILITY_CURRENT_20261029 -->
# MAIN automation — 29/10/2026

[Current automation result](../../docs/ai/CODEX_AUTOMATION_STABILITY_20261029_RESULT.md): actualclone13min/repeatedschedules/dependencyrecovery/restartsPASS; WF07 thêmCOMPLETED/READYguard đãpublishMAIN. Gatewayeaaa/Core08dfkhôngđổi. AUTOMATION_CORE_E2E_PASS_WITH_LIMITATIONS (livecloneproviderblocked, physicalWindowsreboot/humanUATpending). [Evidence](../../docs/ai/CODEX_AUTOMATION_STABILITY_20261029_EVIDENCE.json), [single checkpoint](../../docs/ai/CODEX_TAKEOVER_CHECKPOINT_20261028_RUNTIME.md). Khôngdùngoldfixtures/restore/StagewrapperschoMain. Cácmốcdướiđâylàhistory/baseline.
<!-- END_AUTOMATION_STABILITY_CURRENT_20261029 -->

<!-- MAIN_TAKEOVER_CURRENT_20261028 -->
# MAIN hiện hành — 28/10/2026

Project5 qldapm-local tại127.0.0.1:18088; Gateway18089/n8n5679/Qdrant6333/Ollama11434. FinalGatewayeaaa1217ac79…, Core08df5e2b giữ nguyên. READY_FOR_OPERATOR_UAT có giới hạn; chưa human sign-off. [Kết quả/code fixes/16workflow/28subsystem](../../docs/ai/CODEX_TAKEOVER_20261028_RESULT.md), [checkpoint](../../docs/ai/CODEX_TAKEOVER_CHECKPOINT_20261028_RUNTIME.md), [operator guide](../../docs/ai/CODEX_FULL_PROJECT_OPERATOR_GUIDE.md). Các mục Staging và nghiệm thu phía dưới là lịch sử, không là Main proof; không dùng wrapperStaging/legacyfixture để vận hànhMain.
<!-- END_MAIN_TAKEOVER_CURRENT_20261028 -->

<!-- EXECUTION_MONITOR_CURRENT -->
# Execution Monitor đã hoạt động trên Staging

**COMPLETE_ON_STAGING — 2026-10-19T20:01:45.802306+07:00.** Đã triển khai đúng preview owner duyệt: Gateway456c38f6, Core7d76c1eb và reload local-backup hiện hữu. Không cần deploy lại.

Mở [Lịch sử xử lý / Execution Monitor](https://buried-glad-rpg-recall.trycloudflare.com/projects/qldapm-local/qldapm-ai/executions) và đăng nhập bằng tài khoản hiện có. Trang http://localhost:18090 luôn hiển thị URL Quick Tunnel hiện tại.

30 ca Playwright/API công khai PASS với PM, BA, FE, BE, QA: login/TOTP/logout, Assistant/Control Center, history theo actor; graph6node/output/timeline/replay/mobile; hết phiên và chặn đọc chéo run bằng API403/UI. Source/image/runtime khớp51fileGateway và47fileCore. Qualification trước deploy:196testsWindows,127testsLinux,25ca browser trên clone. Không coi mock là Gemini live.

18container healthy;15container ngoài phạm vi giữ nguyên ID/image/starttime. Main/CSDLDPT, Quick Tunnel, n8n và database không bị restart bởi apply.372WorkPackages, mật khẩu, cấu hình TOTP, RBAC/nativegates và SecondBrain được giữ;9fileprivate không đổi. Sau UAT chỉ4bảng auth metadata đổi đúng dự kiến; mọi thuộc tính bảo mật của12users/28TOTPdevices giữ nguyên. LedgerGemini517→517; không có Googlecall mới hoặc Nativebusinesswrite.

Backup mới trước deploy đã restore221bảngPG/assets/config+3SQLite. Backup sau deploy61266765-03f3-459c-b7b1-a96f4a656591 đã restore3SQLite; run/output/proposal/audit/receipt cũ giữ nguyên. Image-lock/manifest/restartpolicy đã lưu; Gemini dùng lại key/policy hiện có.

Giới hạn: run cũ thiếu agenttiming/Revieweroutput riêng nên UI ghi rõ dữ liệu thiếu. Không gọi Gemini mới, không restartDockerDesktop thêm, không test20người hay promoteMain. QuickTunnel có thể đổi hostname sau lần khởi động Docker tiếp theo.

Đọc [readiness](../../docs/ai-multi-agent-upgrade/execution-monitor/FINAL_EXECUTION_MONITOR_READINESS.md), [deployment report](../../docs/ai-multi-agent-upgrade/execution-monitor/run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md) và checkpoint trước lịch sử bên dưới. **Không chạy lại provision/apply/fixture seeder hoặc xoay credentials.** 113taskobjects giữ nguyên; không còn approval đang chờ trong phạm vi Monitor.
<!-- END_EXECUTION_MONITOR_CURRENT -->

<!-- GEMINI_LIVE_CURRENT -->
# Trạng thái hiện tại — 2026-10-19T07:18:25.059814+07:00

**GEMINI_LIVE_STAGING_VERIFIED**. StagingGateway40cb4806/Core3b09393d; Gemini model/key hiện có hoạt động thật qua Supervisor + PM/BA/DEV/QA, aggregate/plan/usage/citations hiển thị trên Web. A–E/BE/BA-deny latestPASS;5rolelogin/TOTP/logout/CChistory/crossactor403PASS.178Windows/63Linux testsPASS;19generation/38HTTP phases,FREE_ONLY và savedkey được giữ. Billing OWNER_ATTESTED; không kiểm tra Console mới hoặc cam kết absolutezero.

Đọc [FINAL_LIVE_GEMINI_READINESS](../../docs/ai-multi-agent-upgrade/gemini-live-deployment/FINAL_LIVE_GEMINI_READINESS.md), CSV và run_20261019_0013/CHECKPOINT.md trước mọi lịch sử bên dưới.18servinghealthy/17khác nguyênID,372WP/8privatefiles/RBAC/TOTP/tokens giữ;ServingNativewrites0. Backup cuối ba33c28b-2cf2-4ad7-b9b8-c50c69ad08df,3SQLitecoldrestorePASS.4clones stopped/dữliệu giữ. Main chưa promote,20usersDEFERRED,TOTP_DO_NOT_ROTATE. UXcaption local cònP3; không restartCore/Tunnel/DockerDesktop mới. Không hỏi lại key/G2 hoặc tự replay failedruns.
ACL progress/partial readback FIXED_AND_VERIFIED;5roleUI reopened on40cb,19generationcalls retained.
<!-- END_GEMINI_LIVE_CURRENT -->

<!-- POST_DEPLOYMENT_UAT_CURRENT -->
# UAT hiện hành — 2026-10-18T22:52:55.637123+07:00

**LOCAL_STAGING_UAT_VERIFIED_WITH_GAPS**. Gateway47751dc2/Core3b09393d đang serving; UAT-01 đã sửa/deploy theo approval af53a2f8… chỉ Gateway.18container đúng cấu hình,17container khác giữ nguyên;372WP/RBAC/TOTP/keys giữ, Gemini ledger471/0Googlecalls.75serving+64clonebrowser+29API+9chain;2clonefix+7servingfix, DailyBrief/n8n UI+API+CLI thật đã thử;60Windows/41Linux/58mock tests. Xem post-deployment-uat/run_20261018_2200/UAT_EXECUTION_REPORT.md và CHECKPOINT.md trước mọi lịch sử bên dưới. Không coi mock là live Google hoặc mọi test đã rerun trên477.

5role đọc Backlog và5Sprint thật PASS; Supervisor trả output UI. PM canonical preview/approve/reject/Native receipt dùng fixture clone, qua explicit PM tool form; auto draft conversion chưa có. G2liveGemini vẫn BLOCKED_OWNER_VERIFICATION,20-user DEFERRED_BY_OWNER, Main chưapromote, TOTP_NOT_APPROVED_DO_NOT_ROTATE. Backup trước/sau3SQLite restore PASS;4clones stopped/data kept. Quick URL hiện tại https://therapeutic-price-various-marking.trycloudflare.com, lấy lại tại http://localhost:18090 sau restart. Không chạy lại provision hoặc fixture seeder chỉ vì lịch sử ghi chưa deploy.113task objects giữ nguyên, chỉ thêm extension UAT.
<!-- END_POST_DEPLOYMENT_UAT_CURRENT -->

<!-- REMAINING_DEVELOPMENT_CURRENT -->
# Đã triển khai Staging và kiểm tra phục hồi — 2026-10-18T21:50:12.893792+07:00

**STAGING_DEPLOYED_VERIFIED**, Gateway6afb78c4/Core3b09393d; owner đã duyệt hash265ab363… và app-only apply hoàn tất. Sau mất điện do owner báo, 18 container tự phục hồi đúng ID/image, không reapply hoặc chạy lại job. Không còn active/unknown job; SQLite quick_check PASS; manifest/image-lock/key khớp. Đọc remaining-development/STAGING_DEPLOYMENT_REPORT.md và deployment-summary.json trước lịch sử bên dưới.

5 tài khoản thật login/TOTP/Assistant/Control Center/Second Brain PASS qua HTTPS; 5 lượt Supervisor thực qua Rails bridge có plan/trace/model_used=false.35Gateway+7Core hash PASS;372WP và RBAC/credentials/device secrets giữ nguyên, chỉ access/session metadata đổi sau login. Ledger471 không tăng; old receipts/docs giữ nguyên. Backup mới trước/sau và 3SQLite cold restore PASS.520Windows/30Linux/64clonebrowser/13CC là bằng chứng qualification trước, không phải chạy lại sau mất điện.

Không promote Main, không đổi CSDLDPT, không migration hoặc Native fixture writes. Không rotate TOTP; G2 BLOCKED_OWNER_VERIFICATION và20-user DEFERRED_BY_OWNER. Gemini policy/key tự đọc lại từ private config, không cần nhập lại. Quick Tunnel URL có thể đổi sau restart; lấy link tại http://localhost:18090. Clone qualification vẫn stopped; không dùng synthetic credentials cho serving.113task objects nguyên vẹn. **Không chạy lại provision chỉ vì tài liệu lịch sử bên dưới ghi chưa deploy.**
<!-- END_REMAINING_DEVELOPMENT_CURRENT -->

# QLDAPM AI gateway và core gates

**Latest17Oct — P04-08 accepted53/113:** actual portable workflow export/version+SHA manifest/no-secret guard, JSON import into EMPTY n8n with private saved owner/encryption/credential configuration, manual+5READY daily after restart/dedup PASS.290Windows/9targeted PASS; only two JSON source files local commit de7fe8f, no push/global Git config. Primary runtime/data/keys/ledger unchanged6b4caf88/29ec871d/471.09errors/10outage next; see upgrade artifacts/P04-08-workflow-export-acceptance.md.

**Latest17Oct — P04-07 +11 accepted52/113:** stagingGateway6b4caf88/Core29ec871d adds ACL-native compact daily projection/card; actual n8n09:00/startup workflow5READY, same-day dedup,0LLM/native writes. Full clone schedule/restart/fresh restore+5roles PASS, actual Rails signed bridge5roles/PM-only ceiling PASS.288Windows/24Linux/29operator/view+XSS/cold old-image compatibility PASS. One owner/no shared editor/two encrypted credentials, all native fingerprints/keys/ledger471 retained.08exports/09errors/10outage next; main and physical-client acceptance later. Upgrade artifacts/P04-07-daily-brief-acceptance.md and P04 checkpoint current.

**Latest16Oct — P04-06 accepted50/113:** actual manual n8n Set/Crypto/HTTP workflow installed, owner API execution1 saves status/trace/history,0LLM/native writes.276Windows/13targeted and isolated product-workflow restart/fresh restore PASS. Source JSON has credential references only, user edits never overwritten; localhost5678 admin editor, daily schedule next. Gateway58937bdd/core1cdd/data/keys/usage471 retained. See upgrade P04 checkpoint/artifacts/P04-06-manual-workflow-acceptance.md.

**Latest16Oct — P04-05 accepted49/113:** staging58937bdd scoped signed status trigger, durable idempotent receipt/nonce protection, no actor/native write/LLM.272Windows/38Linux/16targeted plus actual n8n faults/12concurrent duplicates, old-image DB compatibility/restore and5native-role read PASS. Primary1owner/2encrypted credentials/0business workflows, key+ledger471 preserved. Manual workflow/digest next; P04 checkpoint/artifacts/P04-05-signed-command-acceptance.md current.

**Latest16Oct — P04-04 accepted48/113:** staging035a6752 has separate persisted n8n machine key/one encrypted scoped credential, fixed internal status read only/no human authority.264Windows/32Linux+9operator units, actual n8n network negative tests/5native-role read regression/backup key-pair restore PASS. One local Community owner/editor loopback; no business workflows yet. Usage471/native data/core/keys retained; signed triggers/reports next. Upgrade P04 checkpoint/artifacts/P04-04-machine-auth-acceptance.md current.

**Latest16Oct — P03 gate PASS44/113:** durable runtime/context/queue/trace/read APIs qualified; actual Rails signed bridge5roles and private-clone nonce/consent/readback tests PASS39regressions. Gateway6e221f66/native1cdd unchanged,248Windows/82Linux qualification retained; native dirty18files byte-preserved. P04 n8n owner/machine workflows next. Physical5browser/main approval and active Supervisor remain later; see upgrade P03 checkpoint/artifacts/P03-bridge-acceptance.md.

**Latest16Oct — P03-08:** staging6e221f66,248Windows/82Linux PASS; own actor/project paginated REST/MCP progress+trace available with read-only no-replay/reconcile hints, no raw task/result content. Five actual native-role clone acceptance and primary source/config/data preservation PASS. Signed bridge acceptance closesP03next; Supervisor/n8n not active. Upgrade checkpoint/artifacts/P03-api-acceptance.md current.

**Latest16Oct — P03-07:** staging73d117fa,242Windows/76Linux PASS; local trace IDs correlate runtime/Gateway/actual child-worker/native/provider attempts without prompts/keys/paths. Existing audit adds only4nullable IDs; every prior Gateway value preserved and old-image compatibility PASS. Read-only progress API and signedbridge acceptance next; Supervisor/n8n scheduling not active yet. Upgrade P03 checkpoint/artifacts/P03-trace-acceptance.md is current.

**Latest16Oct — P03-06:** stagingbc6fc2b3,237Windows/71Linux PASS; typed metadata now uses the existing single fair ai_queue/dispatcher, with atomic wait/claim/finish/expiry, durable receipts and no replay. Real cold-clone container restart5tasks PASS; active Supervisor submission/n8n scheduling still later. Read upgrade P03 checkpoint/artifacts/P03-agent-queue-acceptance.md for current evidence and initial fixture timeout disclosure.

**Latest16Oct — P03-05:** staging6ebd8f8a,229Windows/63Linux PASS; typed metadata state transitions and actual disposable-container restart/receipt retention/no requeue accepted. P03-06 executor binding and07trace/API follow; Supervisor still not active. Current upgrade checkpoint P03 and artifacts/P03-states-acceptance.md supersede older status below.

**Latest16Oct — P03-04:** staging3e2a64d5,224Windows/58Linux tests PASS; scoped/expiring native context references accepted via5actual-role REST clone tests. Exact read-only “task đó” followups need stored task+conversation IDs and fresh native ACL/lockVersion; old context never grants write consent. Automatic Supervisor/UI context creation still upcoming. Upgrade checkpoint P03/artifacts/P03-context-acceptance.md has current evidence.

**Latest16Oct — P03-03:** staging2e117f87 includes typed version1 agent contracts and additive SQLite task/run metadata.219Windows/53Linux PASS; actual stage cold-copy forward/rollback and old-image compatibility PASS; legacy receipts/usage471/roles/key/native core unchanged. No active Supervisor/task API yet; context/state/trace and n8n follow by dependency. Evidence upgrade artifacts/P03-store-acceptance.md.

**Latest16Oct — P02 gate PASS:** staging Gatewaybccd1d2c,209Windows/43Linux tests PASS; actual5role native reads and private clone quota/provider/cache faults PASS. Shared durable queue, class round budgets, safe provider-phase retries, native count/status/list/overdue/read with fresh ACL and explicit WAITING_QUOTA/OFFLINE/STALE states accepted. Usage471/key/native core/main preserved. Cached READY does not verify live billing. P03 agent runtime contracts/context are next; n8n workflows/Supervisor/knowledge not yet implemented. See upgrade PROJECT_STATE.md and artifacts/P02-fallback-acceptance.md; this supersedes older test counts/status below.

**Hiện hành16/10/2026 — upgrade local5users:** đọc docs/ai-multi-agent-upgrade/PROJECT_STATE.md/TASKS.json. Owner chọn Quick Tunnel thay Radmin; http://localhost:18090 cung cấp HTTPS link hiện tại. Gateway/DB/n8n private, main chưa promote. Owner xác nhận Free/No billing account15RPM250000TPM500RPD và redacted business content; key hiện có được giữ. Free-only guard/Pacific quota đã deploy staging, synthetic QLDAPM_OK thật PASS18+6tokens. Chỉ persistent continuous-free-only/billing_allowed=false được phép; đường authorize-continuous trả phí cũ bị chặn. Cấu hình private không cần nhập lại theo mỗi lần mở Docker. Không chạy lại hướng dẫn paid-consent hoặc one-hour renewal lịch sử bên dưới. Provider readiness dùng receipt đã kiểm chứng gắn exact proof/key/model và circuit; kiểm tra health/status không gọi model.171Windows unit tests PASS; final image/recovery receipt trong checkpoint nâng cấp.

**Hiện hành15/10 — sửa nhận biết và ngày:** staging có start_date/due_date, aliases set/thêm deadline/plural IDs, native calendar preflight và preview/kết quả rõ ngày thực tế; bỏ thông báo thiếu dữ liệu khi còn xử lý.147Windows/143Linux+4skip, native date/RBAC và Gemini thật/browser preview PASS. Xem [checkpoint](DATES_CHECKPOINT_2026-10-15.md) để biết phạm vi/giới hạn kiểm thử. PM-only-write giữ nguyên; live/Jira không đổi.

**Hiện hành15/10 — Administrator18091:** native user12/`system-admin`, admin toàn hệ thống và PM membership cả3project, có thể sửa/đổi assignee task của PM; giữ gate chống tự duyệt.47core/11real-account assertions PASS với rollback. Coree7fd2cb4…/gateway giữ1b59ea4d…; account admin chưa enroll Gemini/MCP. Live/Jira không đổi. Xem [checkpoint admin](ADMIN_ACCESS_CHECKPOINT_2026-10-15.md).

**Hiện hành15/10 — PM-only-write RBAC:** xem [checkpoint](RBAC_CHECKPOINT_2026-10-15.md) và [AS-IS/TO-BE audit](RBAC_AUDIT_2026-10-15.md). Staging đã thu hẹp native roles, chặn non-PM ghi ở core/Boards/Gateway/MCP/Gemini; chỉ đọc/comment/export.142Windows/138Linux+4skip, native5role/Gemini thật5role/UI/Boards/restart PASS. MCP thật BE PASS;4testBearer khác hết hạn nên BLOCKED, không đổi credential. Live/Jira không đổi; chưa production READY. Các ghi chú bên dưới về non-PM create/update/transition và manage_subtasks đã bị chính sách mới thay thế.

**Hoàn tất15/10 — sửa Gemini tạo/sửa lỗi:** đã deploy gateway87a6549b… trên staging18091/18092. Typed business tools, validation rõ, parent permission đúng, token budget và chờ quota phút, giữ receipt.137Windows/76Linux(1OSskip), native và Gemini thật5role, preview/8writes/browser/restart PASS.14fixtures đã dọn,329nguồn/role workflows/live/Jira giữ đúng phạm vi. Xem [checkpoint](RELIABILITY_CHECKPOINT_2026-10-15.md).

**Hiện hành15/10/2026 — Work Packages theo cây:** mặc định chỉ hiện Epic; mở Epic→Task→Subtask, phân trang giữ trọn nhánh và thứ tự nguồn Jira. Native table/filter/editor vẫn truy cập được;329nativeattributes giữ nguyên. Staging18091 đã nghiệm thu, xem [checkpoint mới](HIERARCHY_CHECKPOINT_2026-10-15.md).

**Hiện hành15/10/2026 — Không giới hạn số thao tác Gemini:** hard cap6 tool calls/batch/model turns/write_scope_ids đã bỏ trên staging18091/18092. Deadline600s, tài nguyên, quota và quyền native vẫn áp dụng; xem [checkpoint mới](UNLIMITED_CHECKPOINT_2026-10-15.md). Các ghi chú giới hạn6 bên dưới là lịch sử.

**Hiện hành15/10/2026 — Business Assistant staging:** [checkpoint](BUSINESS_CHECKPOINT_2026-10-15.md), [câu lệnh bằng lời](BUSINESS_COMMANDS.md). Gemini được đọc business description/comments/relations, trả lời tiếng Việt và dùng native type/status/priority IDs. Checkbox +ID rõ trong câu lệnh không cần nhập lại ô phạm vi; preview có before-after và giải thích, kết quả nổi bật/receipt/partial failures.128Windows/54Linux (1OS skip)/34nativeUI,10native nhóm và actualGemini7ca/API/MCP/browsercheckbox PASS;329nguồn và comment58 giữ nguyên. Live/Jira/billing/roles chưa đổi. Các mục metadata-only/Free1h bên dưới là lịch sử.


**Hiện hành15/10/2026:** đọc [continuous checkpoint](CONTINUOUS_CHECKPOINT_2026-10-15.md). User đã cho phép Gemini không hết hạn và chấp nhận chi phí; staging ON/authorized/expires:null, key/model/project/data scope giữ nguyên.117Windows regression/53Linux (1OS skip)/29UI/10native API, Google thật/API/MCP và human browser chat/auto refresh/restart PASS;329nguồn giữ nguyên. Main/live chưa deploy. Mọi rule Free1h/budget-zero/providerOFF bên dưới là lịch sử trước consent mới (không mở ngân sách Jira/add-ons).

**Gemini Assistant Level 2 —14/10:** đọc [checkpoint mới](LEVEL2_CHECKPOINT_2026-10-14.md) và [runbook](LEVEL2_RUNBOOK.md). Final pair d4b5…/bee98… chạy staging18091/18092; main8088/8090 không đổi.112Windows units/61Linux tests (1OS skip) PASS; Google SDK thật smoke/metadata329 và synthetic create/update đã có receipt. Parent hierarchy PASS sau user duyệt duy nhất staging PM manage_subtasks. Consent ghi giới hạn một run/ID đã chọn; mặc định proposal. Browser/qualification đầy đủ/production còn pending. Free proof hết hạn23:26:49+07, không tự gia hạn. Các trạng thái dưới đây là lịch sử.

**Terminal23:30+07:** final staging native/UI/API/MCP và DB/web/gateway restart PASS; nguồn329/keys/quota ledger/receipts/images giữ nguyên. Gemini hiện BLOCKED do proof hết hạn23:26:49; không tự renew. Browser thật/full new qualification/live còn pending; đọc Level2 checkpoint.

Trạng thái mới nhất: đọc `DEEP_AI_RUNBOOK.md` và đầu `CHECKPOINT.md`. Candidate AI Assistant/Insights/23 tools đã triển khai ở staging; **chưa có trên live**. Role live đã đối soát: user19 PM, user20 BA, user21 BE/user22 FE/user23 QA. Không chạy lại batch đổi role.

Gemini yêu cầu mới **FREE ONLY, staging only**: [GEMINI_FREE_TIER.md](GEMINI_FREE_TIER.md). Lệnh `free_tier_staging.py enroll` nhập key hiện có bằng prompt ẩn, giữ OFF; không dùng lệnh `manage_deep_ai.py provider` cũ. Project/quota/terms chưa xác minh thì không gọi API; Free không gửi ticket/code/dữ liệu nhân sự.

Đây là lớp điều khiển tracker OpenProject, không phải 53 chức năng sản phẩm đã hoàn thành. Jira độc lập; gateway/broker không gọi Jira hoặc thay credential/bot/lịch của Jira.

## Trạng thái triển khai

**Resume14/10 19:20+07:** target user corrected to main8088. Main official2bee…/gateway7190… unchanged, AI not promoted. Stage18091/18092 has working AI menu, public Gemini3.5Lite answer and POST→GET fix (core8193…/gateway74af…); actual browser screenshot and runs in CHECKPOINT. New project-metadata-only adapter is source-only,97unit tests PASS; it filters private ticket/code/person fields, returns cited counts/IDs and human-confirmed proposals. Production binding/paired rollout/real metadata Google acceptance remain pending. Existing one-hour Free proof expires19:27:19; startup does not renew it or promise continuous Free availability. Earlier statuses/ports below are historical.

Follow-up: finalstage262c30a1…/10496cd8… exact-source pair promoted,25nativeUI/bridge cases PASS/proposal preview links; **real metadata Google PASS** run25249758… cited329count with native readback +REST/MCP/replay. Usage18/circuit0, same proof timestamp retained; no writes/private text/code/people sent. Full qualificationb78f9fca… RUNNING. Production still unchanged; activation/ledger handoff/independent approved cutover pending. CHECKPOINT supersedes pre-build SOURCE ONLY note above.

**Hiện hành14/10 16:25+07:** chuyển model sang `gemini-3.5-flash-lite` theo yêu cầu user, giữ key/project cũ và không billing. User quota15RPM/250000inputTPM/500RPD → caps10/175000/350; usage giữ6→10, không reset. Direct Google smoke và actual REST/MCP HTTP/stdio/replay/anonymous-denial PASS, trả `QLDAPM_OK`, run `fdd77e23-82fe-4a50-92c2-eb76758b2c8d`. Staging **ON_SMOKE_ONLY đến14/10 17:21:52+07**, expiry fail-closed, chưa chat dữ liệu dự án.92units PASS; source/image12gateway files/UI heading verified. Stage core `c77dbdae…`, gateway `ec4b0e1e…` healthy; live2bee/7190 unchanged. Chỉ heading UI đổi thành Gemini không hardcode tên cũ. Không full release qualification mới hoặc human/live acceptance; historical proof stale, fork có1view change chưa commit. Artifact `artifacts/gemini-35-real-probe-20261014-1625.json`; mọi trạng thái3.8 phía dưới là lịch sử.

Terminal14/10: OfficialOrigin paired release+rollback now PASS on synthetic reconstructed original schema/actual official2bee binary (UUID2f495606…), restore494d… PASS33critical fingerprints/assets/config. Full qualification d6c2669c… exited1 only at remote DNS/getaddrinfo;28check logs passed, NO sealed proof. Separate unchanged HTTPS HTTP/stdio SDK rerun PASS without DNS/proxy/cert changes; do not forge/re-sign a combined release proof. Final both329SourceIDs/329NEW, stage8ae2/3f and live2bee/7190 healthy; no primary sync/live promotion. Existing key retained, GeminiOFF/4rolling reservations/1circuit, fresh quota still unavailable. CHECKPOINT records remaining general-data/human-approval/real-Google boundaries.

Resume14/10 14:00+07: full29-check qualification d6c2669c… RUNNING on frozen harness8bb0b9ac…/migrationf1cb2a4e…; old3aa… proof remains stale. Original-binary clone rollback and release each returned expected receipts, but final harness schema comparison failed; read-only RED→GREEN proved existing source-comparison mode is required only after successful migration. Harness fixed; do not call the whole pair PASS before rerun terminal result. Same existing key kept; fresh Cloud Console no billing, AI Studio quota unavailable/network error, GeminiOFF/no new inference/live mutation. CHECKPOINT has exact IDs.

Continuation14/10: migration had a live blocker (looked up BA-PM globally after live renamed BA). Fixed project-membership role resolution using existing GatePolicy aliases; native RED→GREEN covers renamed BA, foreign-role exclusion/ambiguous alias denial and329attribute rollback.92units and syntax PASS. Added qualification migration-role check; old3aa… proof is now STALE and cannot approve current source. Existing Docker pair harness OfficialOrigin mode is being tested in UUIDcb6d6755… from reconstructed synthetic legacy schema/actual official2bee, failure rollback first then success; not yet PASS, not a production DB clone. Main images/roles/data/provider remain unchanged. CHECKPOINT supersedes historical terminal28-check evidence below.

Terminal14/10 10:08+07: new pair stage8ae2…/3f53… now **qualification PASS28** (3aa5103c…/hasha557af77…, HMAC/current candidate/restore reverified, expiry15/10 10:05:12+07). Includes native/UI/privacy/five synthetic identities/write/replay, sandbox3suites, restore33critical-table fingerprints/assets/config, actual clone pair success+rollback and HTTPS HTTP/stdio SDK. Final stage/live329NEW, stage8092health200/livehealthy, source sync not applied and no independent local release approval/live cutover. Existing key models.get HTTP200/exact3.8Flash/generateContent supported, but0new inference calls; Gemini **OFF** because fresh quota UI still unavailable/old proof expired/1circuit,8reservations unchanged. General normal Free-data chat and official→candidate upgrade/real-user acceptance still missing. Historical RUNNING notes below are superseded; CHECKPOINT records exact scope.

14/10 follow-up: staging gateway now3f53f480…/core8ae2… after stopped-state private backup cfd081f5…; no production promotion. Exact source/image pair verified; forkclean1f4aa591… (owned simulation filter committed with explicit automated author, no global Git settings). Main real HTTP/stdio MCP/anonymous401/analyze329 PASS, Google calls0. Full technical qualification3aa5103c… is RUNNING: native gates/concurrency/UI/privacy/source comparison/five synthetic identities/write-cleanup/sandbox3suites and restore33critical-table fingerprints/assets/config have passed; Docker release/rollback and remote acceptance remain pending. A technical proof does not mean independent operator approval or official-to-candidate upgrade/live acceptance. Gemini remainsOFF/expired proof/8reservations/1circuit; correct-project quota UI unknown despite Free tier and No billing account. See CHECKPOINT for terminal result; do not use old image defaults or force providerON.

Resume14/10 09:25+07: live/stage healthy, both329NEW, no primary apply/approval receipt. Fresh official QAG3 source fields still match complete snapshot; qualified backups valid. New staging/live previews expire10:23:40/10:21:16+07; exact paths/hashes in JIRA_SYNC_RUNBOOK.md, old02:xxpreviews expired. Stage human-local confirmation is required before data/config writes and independent readback before live.92Windows tests and Docker92discovered/3OSskip PASS; general Gemini quota/parser patch built-only3f53f480…, not promoted. Gemini OFF/8reserved/1circuit, fresh quota UI unknown, no Google call or live rollout this resume. Details in current CHECKPOINT.md; historical readiness below is not completed sync or normal Gemini chat.

Final sync qualification14/10: both full DB/assets/config restore + native329content/2comments/265Simulation entries + replay/readback PASS;89units/42valid+42wrong-role policy edges PASS. Only staging-web now8ae2b351… with installed Insights regression PASS; gateway1cd… and live2bee…/7190… unchanged. Both primary data sets still329NEW, costs/permissions/Simulation unchanged: **READY FOR HUMAN-LOCAL APPLY, not yet synchronized**. Qualified previews require local exact hash;329native dates retained due344v7 scheduling relations, source dates visible in description; status differences remain gated. See current CHECKPOINT/JIRA_SYNC_RUNBOOK; historical partial notes below are superseded.

Power-loss resume: primary8088/8091 readback329NEW; stage đã start đúng pinned pair. Sync CLI snapshot/preview/apply/verify nay có implementation với human-local hash, OS lease và durable UNKNOWN receipts; chưa primary apply. DB/assets/config restore hai đích và native1-item Simulation import/replay/gate/Insights clone PASS; full329 exercise/candidate promotion/qualified preview vẫn cần hoàn tất. 86units/21sync tests PASS (xem CHECKPOINT); không thay Jira/Gemini/live image. Các mục dưới là lịch sử.

Jira sync tiếp tục sau user duyệt scope time tracking: fixed transaction-only cấu hình + native PM contract và isolated synthetic-stage DB dump/restore regression PASS;73units PASS. Không có committing runner hoặc sync apply/verify hoàn chỉnh, chưa backup/restore DB+assets+config cả hai đích. Readback cả8088/8091 vẫn329NEW; live/staging module/quyền/activity chưa persist thay đổi. Hash cấu hình cũ không dùng cho approval mới; local human approval vẫn bắt buộc. Xem JIRA_SYNC_RUNBOOK.md.

Jira sync20:47 ngày13/10: snapshot/preview CLI đã triển khai, **chưa apply/verify hoặc hoàn tất đồng bộ**. Official source329/265worklogs/2comments/1697history captured privately; previews map329both targets, staging denies242transitions. Both PM time-entry forms403 vì costs module/permissions/Simulation activity chưa có; cần user authority/local exact approval, không tự cấp quyền.72units và source-only Insights RED→GREEN/transactionrollback PASS; current329/106AC unchanged, no Jira/Gemini mutations or deployment. Xem JIRA_SYNC_RUNBOOK.md; không chạy Setup hoặc coi preview là sync thành công.

Hiện hành19:50 ngày13/10: Docker/staging đã khởi động lại đúng pair0ab…/1cd…, health và actual main REST/MCP HTTP/stdio/analyze329/anonymous401 PASS. Fresh official console Free/no-billing/quota5/250000/20; giữ cap3/175000/14/key, helper verify đúng provenance assistant/proof valid20:49:27. Một Google smoke countTokens18 PASS nhưng generateContent timeout; provider **OFF**, circuit latched, counter6→8/14, không retry/refund/paid fallback. Artifact gemini-real-probe-20261013-1950.json. Browser automation localhost bị policy chặn nên UI test mới NOT_RUN; không lách chặn. General chat vẫn chưa mở; các đoạn dưới là lịch sử.

Gemini fresh17:56 ngày13/10: Free/no-billing/quota đã đối soát lại, giữ key/caps/counters; proof valid đến18:56:21. Google thật countTokens PASS nhưng generateContent503/UNAVAILABLE, không output mới; provider OFF/circuit latched/usage6of14, không retry/paid fallback. Staging gateway cùng image đã phục hồi, main actual REST/MCP HTTP/stdio/native329 PASS. Artifact gemini-real-probe-20261013-1756.json và đầu checkpoint; Gemini chưa phải chat phân tích công việc đầy đủ. Lịch sử Google PASS buổi trưa không phải trạng thái lượt mới.

UI POST13/10: đã sửa root500 do `ArgumentError` bị shadow thành `I18n::ArgumentError`; explicit `::ArgumentError`, JSON/type validation, plain HTML forms và safe Gemini refusal messages. Final staging core0ab293ea…/forkc715001d…, gateway1cd1687b…;22UI/bridge regression cases,66units, native concurrency/integration,329SourceID/106AC và5fake-role REST/MCP/mainSDK HTTP/stdio PASS. Actual BE browser identity, malformedJSON/expired-provider alerts, fixture create/update preview→confirm→readback, self-approval denial và Insights own/other privacy PASS; fixture383 đã dọn, ảnh receipt thật tại artifacts/AI-UI-receipt-20261013-1745.png. Gemini hiện OFF do verification expiry13:26:11, không general chat; manual identity/read/proposal và Insights vẫn dùng local. Chi tiết/lịch sử test-session logout và fixture cleanup ở checkpoint. Không live cutover hoặc Jira changes; không chạy Setup để lấy UI.

UI startup13/10: staging core finalef4d6831…/fork2ce95aa8… sửa controller acronym/explicit Zeitwerk mapping, native permission checks AI/Gates và hostname8091 (Continue TOTP trước đó redirect nhầm8088). Native route và anonymous HTTP regression RED→GREEN, web healthy/deep bridge/receipt/privacy PASS. User tự onboarding BE/password/TOTP; browser AI Assistant hiển thị run thật QLDAPM_OK và Insights self-report PASS, screenshots artifacts/. UI: http://localhost:8091/projects/qldapm-local/qldapm-ai và qldapm-insights. Credential seed BE không còn là mật khẩu hiện hành sau user đổi. Không bypass authorization/TOTP hoặc live cutover; Gemini smoke scope/expiry phía dưới không đổi. Candidate mới cần qualify lại trước rollout.

Live OpenProject vẫn dùng image official 17.9.1; **chưa cutover hard gate**. Gateway riêng chạy loopback `127.0.0.1:8090`; bản core có gate đang ở staging `127.0.0.1:8091` với danh tính, mật khẩu và token giả. Gate kiểm tra tại đường ghi WorkPackage chung, không chỉ MCP. Subtask staging có 7 trạng thái và workstream ổn định; live vẫn dùng 4 trạng thái cũ.

Main staging `127.0.0.1:8091/8092` dùng core `0f8f5a1c…` và gateway `1cd1687b…`. Ngày13/10 Gemini `gemini-3.8-flash` đã PASS smoke Google thật và integration REST/MCP HTTP/stdio/replay/anonymous401; provider **ON_SMOKE_ONLY** đến13/10/2026 13:26:11 Asia/Bangkok, sau đó fail-closed. Fresh console cùng project xác nhận Free/no billing/quota5RPM/250000inputTPM/20RPD; caps3/175000/14, Linux usage4/14 sau2probes, không tăng/reset quota. Verification do assistant chạy theo explicit user authorization, có documentary reference; không phải independent human review/billing API verification. Free chỉ fixed synthetic smoke, không gửi ticket/code/personnel. General-tool claims/deadline đã qua fixture, chưa Google trên dữ liệu dự án. Không restart broker live/Register/Confirm bằng CLI candidate trước approved promotion.

Sự cố rehearsal11/10 đã làm DB/cache live stop/detach tạm do lỗi cách ly project; đã khôi phục đúng image/volume/network và API đọc329/identity PASS, không restore/migrate live. Chi tiết và guard regression ở checkpoint. Qualificationc23cabff… sau fix maintenance health đã PASS28checks gồm paired Docker success/rollback và remote MCP; chữ ký/candidate13/10 hợp lệ nhưng proof24h hết hạn, cần qualify mới trước rollout. Bài paired dùng schema candidate sẵn có, chưa official-to-candidate upgrade.

Main MCP test cấp Bearer BE giả mới qua local/native role check khi TTL hết, không thay token thành viên. Source verifier lưu full/source fingerprints riêng, không bỏ bảng AI đã có; staging RED→GREEN giữ Subject/source bất biến. Restore test dọn container/network UUID, giữ volume/backups. Không tự deploy live từ qualification hoặc Google smoke PASS.

Gateway candidate **fail-closed cho ghi nghiệp vụ**: tạo/sửa/comment/transition/gate cần capability schema2 của đúng core; schema1/official bị từ chối. Gateway cũ cũng từ chối core schema2, tránh mở quyền ghi AI cũ khi nâng cấp riêng core. Bản candidate trả proposal TTL15 phút cho mọi ghi công việc/code/gate/approval; chỉ UI ký với session/CSRF hoặc lệnh local được xác nhận. Đọc và test không cần xác nhận ghi; deploy/admin vẫn cần phê duyệt local độc lập.

REST `POST /api/v1/commands`, OpenAPI `GET /api/v1/openapi.json`, MCP JSON/stateless `POST /mcp` đều cần Bearer. `/health` chỉ trả trạng thái tối thiểu. API v3 OpenProject là nguồn công việc duy nhất; SQLite gateway chỉ lưu token hash, audit, idempotency và job.

## Chạy và cấp credential

### Lịch sử sửa vai trò theo email — đã được operator áp dụng

Yêu cầu 10/10/2026: `hiepk40c@gmail.com` (user19/login `ba-pm`) → **PM**; `2101minhkhai@gmail.com` (user20/login `pm`) → **BA**. Không đổi login/email/password/TOTP/assignee hoặc cấp admin. Native role BA giữ ID và workflow của role BA-PM cũ; BA-PM trong policy candidate là khóa BA lịch sử, không có quyền PM. Gateway mới nhận BA riêng và kiểm tra native role hiện thời, không dùng role cũ của Bearer để cấp quyền.

Image gateway đã build riêng `qldapm-ai:role-change`; chưa deploy. Helper local `change_member_roles.py` preview chỉ đọc live, khóa before-hash/source/image/runtime, hết hạn1h. Apply yêu cầu người vận hành gõ đúng hash trong console local, broker đã dừng và không có job pending/UNKNOWN. Không có API/MCP tool tự duyệt. Lệnh:

```powershell
Set-Location -LiteralPath 'D:\AI project\QLDAPM chat\openproject\ai'
& '.\Manage-OpenProjectAI.ps1' -Action Stop
$rolePreview = (& '.\.venv\Scripts\python.exe' change_member_roles.py preview | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0) { throw 'Preview failed; no role change applied.' }
& '.\.venv\Scripts\python.exe' change_member_roles.py apply --preview $rolePreview.preview
if ($LASTEXITCODE -ne 0) { throw 'Apply failed; inspect private evidence before retry.' }
& '.\Manage-OpenProjectAI.ps1' -Action Start -LocalOnly
```

Apply backup database bằng pg_dump và runtime/SQLite dưới private operator, rồi dừng riêng gateway/tunnel. DB transaction hoán đổi hai membership và rename role; assert hash workflow/work packages/user security/API tokens không đổi. Đồng bộ accounts/bootstrap/gateway role map/token-role metadata/image digest; không đổi hash/TTL/revoked/native token của credential. Không thay image core live, không tự mở public tunnel. Nếu lỗi sau mutation, giữ AI dừng; xem `native-result.json`/`completed.json` trong thư mục private cùng tên preview, không retry/restore mù. Backup DB/config phục vụ rollback có phê duyệt riêng; assets không bị thao tác. Quy trình orchestration apply/rollback chưa chạy live.

Sau apply dùng `provision_member_tokens.py verify` và kiểm tra UI bằng từng người; token hết hạn cần Register đúng người, không tự reset credential. Source overlay hỗ trợ BA đã đổi nên proof qualification cũ **không áp dụng cho candidate mới**; chưa build/sync fork/qualification hoặc cutover core mới. Staging giữ danh tính giả/role cũ sau test rollback.

Dùng PowerShell **7** trong workspace authoritative:

```powershell
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Setup
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Start -LocalOnly
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Status
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Stop
./openproject/ai/Test-OpenProjectAIRestore.ps1 # chỉ dữ liệu staging giả lập
```

Start không có `-LocalOnly` tạo Quick Tunnel riêng cho machine client, Bearer được gateway kiểm tra trước khi trả dữ liệu. Nó không thay tunnel UI/PIN email. URL chỉ công bố sau khi thêm hostname vào allowlist và kiểm tra anonymous bị 401; lỗi tunnel đóng đường remote. Quick URL đổi mỗi Start, không SLA hoặc SSE.

Mỗi người tự đổi mật khẩu, đăng ký TOTP, rồi tạo API token của **chính mình** trong OpenProject. Lệnh local nhập token ẩn, không nhận password, không gửi secret vào chat:

Nếu UI8088 đang maintenance như checkpoint, operator kiểm tra không có release/restore đang chạy rồi chủ động chạy `./openproject/Manage-OpenProject.ps1 -Action Start -LocalOnly` từ root workspace. Lệnh đổi hostname/HTTPS/WebSocket về local, có thể restart container và gỡ maintenance sau health; không thay image hoặc nhập dữ liệu. Đây là thay đổi live do operator quyết định, không phải agent tự gỡ cờ. Mở `http://localhost:8088` để người dùng onboarding; không gửi password/TOTP/recovery code vào chat.

```powershell
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Register -UserId 21 # BE nghiệm thu trước
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Revoke
```

IDs live: PM 19, BA 20, BE 21, FE 22, QA 23. Gateway xác minh user/membership/role native trước mỗi request/job; admin token bị từ chối. Bearer mặc định 24h, revoke qua lệnh local. Private runtime `%LOCALAPPDATA%/QLDAPM/openproject-ai` chỉ LUIM/SYSTEM; credential native và Bearer operator nằm ngoài Git, không xuất qua API/log.

Client local dùng `Start-OpenProjectMCP.ps1 -UserId 21`; thêm `-Remote` để adapter đi qua URL HTTPS hiện hành. Wrapper đọc private `operator/user-21.token`, không đưa token vào argv/config. Mẫu `codex-client.example.toml` chỉ chứa lệnh/cờ, phù hợp [cấu hình stdio của Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli#stdio-servers). Chưa đăng ký MCP global tự động; SDK transport pass không đồng nghĩa Codex client thật đã nghiệm thu. Remote HTTP trực tiếp dùng URL `/mcp` và Authorization Bearer; chưa triển khai OAuth cho ChatGPT.

Owner đã cho tác vụ khác cấp token PM20/BA-PM19; đọc `MEMBER_TOKEN_ENROLLMENT.md` khi nghiệm thu hai danh tính này. Giữ credential đã có. BE21 chưa hoàn tất đăng ký; native API token không chứng minh người dùng đã đổi password hoặc đăng ký TOTP.

## Catalog tool

| Nhóm | Tools |
|---|---|
| Đọc/phân tích | `identity`, `list_work_packages`, `get_work_package`, `analyze`, `get_gate` |
| Ghi nghiệp vụ | `create_work_package`, `update_work_package`, `comment`, `transition`, `change_gate` |
| Code/test | `list_code`, `read_code`, `write_code`, `request_test` |
| Vận hành | `get_configuration` (PM, core candidate), `propose_operation`, `get_job` |
| Timeout/replay | `request_status`, `reconcile_request` |

REST và MCP gọi cùng module `Service`. Tool nhận `arguments` và, với ghi, `idempotency_key` riêng cho đúng request. Update/gate/transition/comment cần `lock_version` đọc mới. Create cần Source ID ổn định, duy nhất. Không có shell, SQL, Rails code tùy ý hoặc proxy URL do AI nhập.

Artifact không secret: `openapi.json` và `mcp-tools.json`. HTTP/stdio dùng chung catalog có mô tả keys/role/idempotency. Evidence `test`, `retest`, `smoke` cần `result: passed|failed`; `deployment` cần `environment: Test|Staging|Production`, chỉ Test đạt release gate. Gate xét record mới nhất của revision, không chấp nhận kết quả passed cũ che failed mới. Chuyển ngược cần lý do và reference.

BE/FE chỉ sửa workspace của chính mình, với `expected_hash`; mọi thành viên có thể đọc workspace của thành viên khác. QA/PM/BE/FE chọn `workspace_actor` khi request test. Test suite cố định `gate-policy`, `gateway`, `core-integration`. Code/ticket là dữ liệu, không phải lệnh/phê duyệt. `analyze` đếm status/assignee, không xếp hạng năng lực cá nhân.

`request_test` trả job receipt ngay; broker lấy hash và bản copy immutable khi job bắt đầu, không băm toàn bộ workspace trong HTTP qua Windows bind mount. Đọc `get_job.result.snapshot_hash` để biết phiên bản thực đã test; nó không cam kết phiên bản tại lúc gửi request. Sửa file vẫn cần hash hiện thời; build được duyệt vẫn khóa `snapshot_hash` của đề xuất.

Automatic ticket evidence chỉ dùng `gate-policy`/`core-integration`. `gateway` chạy regression image hạ tầng đã pin, không chứng minh workspace code được kiểm thử; không nhận `work_package_id`. Catalog23tools hiện hành ở `mcp-tools.json`; bảng phía trên là nhóm tool cơ sở.

## Gate và workflow

Policy duy nhất: `core/overlay/app/models/qldapm/gate_policy.rb`. UI project menu **QLDAPM gates** và `/qldapm/gates/<id>` hiển thị checklist/evidence/reviewer, preview transition và lỗi. Native API `/api/v3/qldapm/gates/<id>` expose cùng dữ liệu.

Checklist nguồn ban đầu chưa đạt. Evidence có actor/time/revision/reference; approval gắn phiên bản, sửa nội dung liên quan làm hết hiệu lực. PM chọn reviewer độc lập trong 5 thành viên; assignee/contributor không tự duyệt. PM đang phụ trách phần việc cũng không tự scope/PM approve; phải phân công owner/reviewer phù hợp, không đổi dữ liệu import tự động để vượt gate.

BE/FE Subtask đi code-review/test; BA/QA/PM đi nhánh ngắn. Đổi assignee không đổi nhánh. PM reclassify phải có lý do/evidence khi NEW hoặc IN PROGRESS. Cha REVIEW/DONE chặn tạo/chuyển/sửa/reopen child; mở cha trước. Comment thường vẫn được phép. Không tự chuyển DONE hoặc mở Sprint. Source Story/106 AC/Description được giữ; AC có cấu trúc phục vụ phiên bản duyệt riêng.

`reconcile_request` chỉ kết thúc pending khi có bằng chứng: Source ID duy nhất, receipt gate đúng actor/request, marker comment, hash file hoặc job receipt. Update/transition ở candidate dùng receipt PostgreSQL cùng transaction với journal/ghi, gắn actor/request/hash; thiếu receipt vẫn UNKNOWN. **Không blind retry**, không đổi key để ghi đè.

## Broker và sandbox

Candidate broker/registration/revoke/local confirmation không mở SQLite từ Windows khi gateway Linux chạy. `operator_state.py` gọi module `gateway.local_operator` qua Docker exec/stdin với operations cố định, không public API/MCP route; mount sai/timeout/module thiếu dừng, không fallback host SQLite. **CLI candidate cần gateway candidate mới**: không restart broker live hoặc chạy Register/Confirm từ source mới trước approved paired promotion; live image cũ giữ nguyên. Token/key không nằm trong argv hoặc stdout log chung.

Resolve sau Stop dùng Linux one-shot pinned/no-network/no-pull, không bật gateway và không chạy job; job running chỉ được acknowledge khi có signed result receipt và human exact hash. Receipt là kết quả thao tác, queue state vẫn cần đối soát qua get_job. Offline helpers còn dùng host SQLite phải xác minh gateway stopped; không xóa WAL/SHM để retry. Checkpoint ghi test single-OS thực và phạm vi chưa deploy.

Start chạy broker local hidden. Một job tại một thời điểm. Test tự chạy theo role; build/admin/live config/delete/restore/start/stop cần PM đề xuất và người vận hành duyệt SHA256 **đúng job**, bằng lệnh local:

```powershell
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Preview -Job '<uuid>'
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Approve -Job '<uuid>' -Hash '<sha256>'
```

Phê duyệt HMAC/TTL và result proof nằm ở `operator/` ngoài mount gateway/workspaces. Admin lấy snapshot cấu hình, kiểm tra lại before-hash dưới khóa project, backup trước mutation. Worker chỉ thực thi argv/operation cố định, gateway không có Docker socket. Stop yêu cầu broker thoát sau job hiện tại, không kill job đang restore/build. `Process` chỉ dùng khi watcher không chạy.

Broker kiểm tra danh tính native bằng bridge GET-only trong network gateway, với token của chính actor. UI maintenance không làm mất khả năng kiểm tra quyền; bridge không thực thi mutation, không nhận URL tùy ý và không dùng bootstrap admin.

Job `running` hoặc `failed_or_unknown` chặn job tiếp theo. Operator kiểm tra kết quả thực/rollback, Stop AI rồi dùng `-Action Resolve -Job '<uuid>' -Hash '<sha256>'` và xác nhận hash ở console. Running job thiếu signed result receipt vẫn bị từ chối. Resolve ghi acknowledgement/audit, không retry hoặc suy đoán thao tác đã thành công.

Actor snapshot immutable, tối đa 50.000 file/2 GiB; path traversal/.git/.env/reparse-point/symlink/junction/hardlink bị chặn. Runner non-root, read-only, drop capabilities, no-new-privileges, CPU/RAM/PID/timeout; không Internet, secrets/live volume hoặc Docker socket. Core integration dùng DB clone staging **giả lập**, internal network riêng, dọn container/network test sau khi xong; không đưa mật khẩu/token/TOTP production vào sandbox.

Trust boundary: bảo vệ AI qua gateway/MCP và container. Tất cả vẫn thuộc cùng Windows user LUIM; một agent/malware có terminal toàn quyền của LUIM có thể đọc private operator key. Không tuyên bố chống host-admin hoặc đồng-user terminal. Cần OS identity tách biệt nếu muốn mức cách ly đó.

## Rollout và rollback

Release có implementation nhưng **chưa cutover hoặc nghiệm thu glue cutover/rollback live**. Qualification local chỉ cấp proof sau toàn bộ kiểm tra staging pass và candidate không đổi:

```powershell
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Stop
# Staging phải chạy image đã pin; không chạy các suite mutative song song.
./openproject/ai/Manage-OpenProjectAI.ps1 -Action Qualify
```

Proof HMAC/24h khóa commit fork clean, core/gateway immutable image pair khớp source, migration/harness hash và restore evidence. PM dùng `propose_operation` với action `release`, parameters gồm `qualification_id` và `qualification_hash` từ kết quả local. Người vận hành xem Preview, limitations, configuration before-hash và deployment hash, rồi duyệt chính job bằng Approve. Thay credential/key/config/.env/image-lock/volume/bridge sau duyệt làm approval stale. Mọi thay đổi candidate hoặc proof hết hạn yêu cầu qualification lại. Pipeline hiện chỉ hỗ trợ thay đổi overlay; full-core build khác overlay chưa được qualification.

Release được duyệt mới dừng UI tunnel, maintenance, backup frozen DB/assets/config, restore vào volume mới, kiểm tra before-hash bằng original image, migrate candidate, kiểm tra nguồn 329/106 và health. Thất bại giữ maintenance và chọn image/volume trước đó; không xóa volume. Thành công chỉ mở local UI, không tự mở public tunnel. Script này chưa được chạy live; qualification staging không chứng minh mọi nhánh rollback của glue. Move khác project vẫn fail-closed, chưa có approved broker path.

Release đóng machine tunnel/gateway trước backup state, pin hai image, giữ hai UI key mount file readonly bằng runtime `ui-bridge.yml`, kiểm tra schema2/capability trước mở maintenance và rollback gateway state/config/image cùng core. Actual Docker paired success/failure rollback đã PASS trên clone schema candidate sẵn có; không thay thế official-to-candidate binary upgrade rehearsal hoặc production acceptance. Single-OS broker state đã PASS trên fixture; chưa paired rollout live.

Giữ live image và volume hiện tại. Runbook backup/restore nền ở `../README.md`. TOTP, UI/WebSocket qua URL mới, Codex client thật và các nhánh admin/security chưa kiểm tra vẫn cần nghiệm thu riêng; unit/staging tests không thay thế production acceptance. Kết quả thực hiện hành tại `CHECKPOINT.md`.

## Kiểm thử

```powershell
cd 'D:/AI project/QLDAPM chat/openproject/ai'
./.venv/Scripts/python.exe -m unittest discover -s tests -v
./.venv/Scripts/python.exe -m tests.stage_api "$env:LOCALAPPDATA/QLDAPM/openproject-ai"
./.venv/Scripts/python.exe -m tests.stage_write "$env:LOCALAPPDATA/QLDAPM/openproject-ai"
# Dọn duy nhất fixture AI-TEST-* bằng core/cleanup_stage_test.rb trên staging.
./.venv/Scripts/python.exe -m tests.stage_transport "$env:LOCALAPPDATA/QLDAPM/openproject-ai"
```

`stage_write` thêm một fixture giả lập; dọn fixture trước suite đòi đúng 329 mục. Không chạy script staging trên live. Phạm vi nghiệm thu và gaps ở `TEST_MATRIX.md`; image/qualification/URL hiện hành ở `CHECKPOINT.md`. Mỗi mục chỉ PASS khi có kết quả thực.


###16Oct2026 — current P02 fair queue staging

Latest stage is2415e4a2 from P02-06: durable quota/provider wait, bounded explicit429/503 retry of the rejected SDK phase only, fresh shared quota reservation and600sdeadline. No replay of tool writes, no timeout/auth auto-retry or paid fallback.196unit/29Linux tests, same-container pending restart and real backup/isolated221-table+SQLite restore PASS. Key/config/usage471 retained. Evidence docs/ai-multi-agent-upgrade/artifacts/P02-06-provider-wait-acceptance.md.70c723below is the preceding accepted image retained for recovery.

Staging Gateway70c72319... now accepts durable actor-fair AI requests instead of AI_BUSY. One global worker slot, interactive priority, round-robin actors,20pending/actor100total; idle actors reuse spare turns. Never-started intents survive restart. Claimed uncertain writes are not requeued; original receipts remain failed_or_unknown after isolated-worker deadline margin. Submission receipt/audit/intent commit atomically under the existing idempotency key. Exact Free-policy hash and native current identity/permissions revalidate before execution. Gemini key/shared ledger retained;0new provider calls in acceptance.188unit tests,14Linux queue tests and same disposable-container restart PASS. Real five native roles read335; actor6 preserved BA-PM (historical BA shorthand was imprecise). Source/deploy evidence docs/ai-multi-agent-upgrade/artifacts/P02-05-fair-queue-acceptance.md. Provider wait/retry/allocation remain P02-06/07; n8n/Supervisor integration is not yet implemented.

Backup RO SQLite recovery also implemented: stable verified DB/WAL copies in private temporary storage, private SHM, SQLite backup API/quick_check; original live mount never opened writable or immutable. Actual221-table backup plus isolated native/assets/config and gateway/n8n logical restore PASS. Owner consent/proof/readiness/key pairing retained.

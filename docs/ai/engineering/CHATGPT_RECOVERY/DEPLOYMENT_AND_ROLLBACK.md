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

<!-- FINAL_DEMO_CURRENT -->
# Final Demo deployed / rollback

 Gateway `sha256:3c06559033eba39f423a0c6f9474d1f77e3ef2ebd3617e1b37e50147d2d51a31`, Core `sha256:5936d90e450e8af321557e94928807f646dd077e646c1ceb546f858890aef2e8`, n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Exact source/pins: `demo-final/final-live-verification.json`. OFF/active0/workerALIVE/provider gatefalse. OpenClaw READY và Demo UP từ API/CLI nguồn thực (`demo-final/readback-final.json`).



Gateway/Core backup `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\demo-final-rollout-20261102T213036\backup`; parentprivatefolder giữconfig/imagepins/worker.before/provider_gate.before. n8n backup `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\demo-n8n-rollout-20261102T213205`, previouscontainer `qldapm-n8n-main-pre-demo-history-20261102T213206` stoppedretained; coldvolume archive cócredentials/history/key. No automaticDBrestore.

Rollback khiOFF/idle: stopQLDAPMEngineeringDelivery; restoreprivateconfig/pins/sourceworker+rootWSLprovider_gate.py và restartproviderunit; recreateGateway/Core bằngoldb184/e847; health/sourceverify rồistartworker. WSLrollbackfailure không được chặnimagerollback; nếu chưaverifyđủ thì giữworkerSTOPPED. Workernewdeferredreserve phảiđi cùngGatewayprivateadmission/gatecode; khôngmixprotocolversions.

n8nrollback: stopnewcontainer, preservefailedcontainer/privatebackup, restoreoldworkflowdefinition bằngsupportedCLI, renameoldcontainerback/start; không restoreDB tựđộng hoặc xóanewexecutions. CácCLI/import/publish cóbảnscripts `demo-final/n8n/deploy_history.py`, noautoapplywhenreadingdocs. Exactcomposeparity preserved. Backuprestoreonlyisolatedclone; noMainDBreset.

RAGcandidatekhôngdeploy. Demoapplication18791khôngđổi release; PR10OPENkhôngphảiDEPLOYED. OpenClawruntimeđượcfence(stop) sau mỗi delivery; idleGateway đãstart/readinessverified riêng, providertransportvẫnOFF. DOWN trong lúcfencingphảihiển thịthực, khôngsuy ra providerAVAILABLE.
<!-- END_FINAL_DEMO_CURRENT -->

<!-- PHASE3_1_CURRENT -->
# Phase3.1 — current, 2026-11-02T23:14:21+07:00

MAIN Gateway `sha256:b184f91963e53df47cbc884cc353d03b0bce871ee19b45b5dc7a5ca78fd638ab`, Core `sha256:e8474e53c7f56a46cd724f4a938a33f9ba01374fbaeb4bb729499cce4fbd4e84`. OFF/active0/workerALIVE; source+pins/API verified, **OWNER UAT PENDING**. #391 vẫn BLOCKED/provider429; không resume trong phiên này. Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json` và `FINAL_TEST_RESULTS.json` schema5. Các mục cũ phía dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

## Phase3.1 rollout / rollback

`phase3_1/deployment-initial.json`, `deployment-pre-identity.json`, `deployment.json` retain each exact image/source revision. Initial pair backup: private `phase3_1-rollout-20261102T153924`; final backend/UI follow-up: `phase3_1-final-rollout-20261102T154856`; final Core identity-only correction: `phase3_1-core-identity-rollout-20261102`. All below `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/`; PG/SQLite/config before-files retained, no reset/restore. Scripts verify idleOFF/queue0, config image-only parity, candidate tests, worker stop/start, health and rollback.

Immediate rollback: when OFF/idle, stop `QLDAPMEngineeringDelivery`, restore Core image0d647f91 and ui-bridge/image-lock from identity backup, recreate only web, health+source read-back, start worker. This reverses labels/plan grouping only. Whole Phase3.1 rollback uses initial pair ce047/7649 and its three pin/config before-files; restore `engineering_worker.py.before` from initial backup if reversing Gateway protocol expectations. The worker change is reserved cap consumption only; don't casually mix older claim protocols. Do not auto restore databases: new notifications/command receipts would be lost. Unknown writes require reconciliation before retry. n8n/DB/Qdrant/Demo not deployed by this work.

Final immutable IDs: Gateway `sha256:b184f91963e53df47cbc884cc353d03b0bce871ee19b45b5dc7a5ca78fd638ab`, Core `sha256:e8474e53c7f56a46cd724f4a938a33f9ba01374fbaeb4bb729499cce4fbd4e84`. Exact hashes at `phase3_1/final-live-verification.json`. API read-back occurred on final Gateway with same controller and Core before final identity-only text/grouping patch; final Core subsequently qualified in Native clone and serving hash/pin verification. No whole-image coding E2E or Browser UAT claim.

---

# Deployment và rollback — post-30218aff

n8n MAIN hiện dùng image `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`; container cũ `qldapm-n8n-main-pre-overwrite-redaction-20261101` được giữ, cùng cold volume backup trong private operator directory `post30218-n8n-redaction`. Rollout kiểm tra config và HostConfig trước start, readiness sau start; 16/16 workflows active và lifecycle mới được ACK. Không thay WF04 settings. `post30218-20261101T1540Z/deploy_n8n_redaction.py` ghi quy trình và rollback khi start thất bại.

Gateway hiện dùng `sha256:cbea63868b3806ecf0e247ea6363be532c1e0149a8981aa3c9a1e719ae887e94`, chỉ thay `engineering_operator.py` so với `sha256:1c10248134b4f7973685433a9686f3d841ed96e5b767dd5b7d497adc0e3eceeb`. Backup PostgreSQL/SQLite và pin cũ lưu trong private operator directory `post30218-gateway-child-citation`; rollback dùng pin cũ và compose recreate Gateway khi queue idle, không restore DB trừ khi có kế hoạch riêng. Script deployment có rollback khi health failure; worker được restart sau cutover.

Stabilization tiếp theo thay Core bằng `sha256:524614e9e8dcdb53296e8b30f0261df523d42da501c8a3461c992ccde773cdff` và Gateway bằng `sha256:8614b7374ac554d5d3ca04bd3bf580b722bf9d64ad7cf9d8c5ce0d54a9562adb`; các pin nêu đầu đoạn trước là lịch sử. Các bản pin/config và PostgreSQL/SQLite backup trước từng rollout nằm trong private `stabilization-controls-rollout-20261102`, `stabilization-report-rollout-20261102`, `stabilization-report-budget-rollout-20261102`. `stabilization-workflows/deploy_controls.py` và `deploy_report*.py` ghi chính xác image, kiểm tra queue idle và rollback khi health failure; worker cũ/candidate cũng được lưu trong backup rollout Core. Không restore database bừa để tránh mất báo cáo hoặc dữ liệu mới.

Gateway sau cùng là `sha256:270a7c1db45cd16d6a29c6e2422433f49f0739bc841303d5ebfe8b7433d1d689`, thêm fencing stale lease và deduplicate resume. Hai backup/pin ngay trước lần thay cuối ở `stabilization-lease-rollout-20261102` và `stabilization-resume-rollout-20261102`; script `deploy_lease.py`/`deploy_resume.py` giữ rollback image và kiểm tra queue idle.

Sau đó Gateway được thay bằng `sha256:9d02446cecd21fccbed2bcc43ae0a7d488f3b5ae2617f1d918926b4ba39aa0d6` cho resumed run queued/PAUSED; backup và config trước thay đổi tại private `stabilization-paused-resume-rollout-20261102`, script `deploy_paused_resume.py`. Rollback về `270a7c1d…` chỉ đổi image/pin khi queue idle; không khôi phục database để tránh mất report/run mới.

Rollback có kiểm soát khi n8n idle: dừng container hiện tại, đổi tên nó thành tên dự phòng duy nhất, đổi tên container cũ về `qldapm-n8n-main`, start và kiểm tra readiness, active workflows, Gateway lifecycle. Hai container dùng cùng volume hiện hành; không tự restore cold volume vì có thể làm mất execution/workflow mới. Rollback image cũ đưa trở lại lỗi full-overwrite redaction đã được tái hiện; giữ WF04 retention tắt và xử lý nguy cơ trước khi bật.

Demo đang chạy release tree `0498ceeda97cd3e856a975129129e71f6c94a3dd`, chính xác head PR #6 còn OPEN, không phải commit đã merge main. Candidate tests PASS; `/healthz` và `/tasks/summary` HTTP 200, header revision đúng, schema và các dòng SQLite không đổi. Snapshot SQLite và wrapper trước thay đổi ở `/home/openclaw/engineering/operator/post30218-demo-20261101`; wrapper cũ trỏ `def9d0a8852af42a407bd42fb0051615a2de9331`. Rollback demo: khôi phục wrapper cũ đã lưu rồi restart riêng `qldapm-mini-task-manager`; không restore SQLite nếu không có lý do và kế hoạch dữ liệu. Script `post30218-20261101T1540Z/deploy_demo.py` tự rollback wrapper nếu health check thất bại. Release này không bao gồm PR #7 mới.

Owner manual UAT vẫn chưa thực hiện.

Rollout cuối: Gateway `sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb`, Core `sha256:00f1e372ded7dc3ee0bcb02275233e0baad08990893f8d1c27511b5a66cb9cd8`. Backup/pin ở private `stabilization-admission-rollout-20261102` và `stabilization-inspector-final-rollout-20261102`; script `stabilization-workflows/deploy_admission.py` và `deploy_inspector_final.py` kiểm tra queue OFF/idle, config parity, health và rollback khi lỗi. Rollback tương ứng về Gateway `9d02446c…`, Core `524614e9…` khi idle; không restore database nếu chưa có kế hoạch bảo toàn dữ liệu mới.

## Final Stabilization Phase2 — initial rollout and final reporting followups

Initial Phase2 Gateway `bca2ff25…`, Core `a6a61b68…` superseded earlier pins; final Gateway is `8359e250…` after reporting followups below. Full serving IDs are in `phase2-final/final-live-verification.json`. Initial Gateway rollout attempt stopped before mutation because modePAUSED, a subsequent staging-script path typo also stopped before mutation. Successful idle-preserving scripts are `phase2-final/deploy_gateway_idle.py` and `deploy_core_idle.py`; backup/config roots are private `phase2-final-gateway-rollout-r3-20261102` / `phase2-final-core-rollout-r3-20261102`. Candidate network-none tests/startup/rollback, exact final Core Native clone and full template render were verified. Serving source parity is recorded separately.

Rollback Gateway ONLY while queue idle and modeOFF/PAUSED: stop scheduled worker, restore previous AI_IMAGE pin698db791 and matching image-lock/env, restore host engineering_worker.py and engineering_delivery.py from `<private gateway rollout>/engineering_worker.py.before` and `<private gateway rollout>/engineering_delivery.py.before` respectively, recreate Gateway, verify health, then start worker. These host originals were hash-checked against M0. Do not mix old Gateway with new claim protocol worker or reverse. Core rollback independently to00f1e372 with previous ui-bridge/image-lock when idle. Do not restore DB automatically, which would lose new run/report data.

Demo label-only wrapper update retained PR6 source/database. Private WSL backup `/home/openclaw/engineering/operator/phase2-final-demo-20261102/server-before.py`; rollback restores wrapper and restarts only qldapm-mini-task-manager.service. SQLite snapshot exists but is not automatically restored. `phase2-final/demo/deployment-result.json` records schema/row equality and exact wrapper hash.

Reporting followups: image `8cd363f1…` thay riêng reporting.py từ bca; image `8359e250…` thêm liên kết report ID vào provider receipt. Full digest cuối là `sha256:8359e250512b0a68a6e92892feb539d6f392b94aa39b91e670db42f49c411e8a`. Private backup roots: `phase2-reporting-rollout-20261102` và `phase2-reporting-provenance-rollout-20261102`; scripts `deploy_reporting.py` / `deploy_reporting_provenance.py` giữ queue idle/PAUSED và rollback khi health lỗi.

Host claim protocol giữ nguyên từ bca. Rollback 8359→8cd chỉ đổi Gateway image/pins khi idle, không restore DB. Nếu quay về 698 phải phục hồi host worker/delivery cùng phiên bản như hướng dẫn ở trên. Coding E2E #390 dùng bca; API báo cáo và narrative receipt trên 8359 được kiểm chứng riêng, không dùng lại coding run làm bằng chứng cho image mới.

Portable n8n kit là phương tiện khôi phục old-key snapshot có ciphertext/recovery key độc lập, không phụ thuộc DPAPI khi restore vào Linux clone. Hướng dẫn và vị trí custody tại `phase2-final/n8n/PORTABLE_RECOVERY_KIT.md`; root proof `portable-root-verify.json`. Không dùng kit này để tự restore MAIN hoặc đổi key. Chưa có off-host custody và physical-machine DR.

## Phase3 — current images and rollback

Current Gateway `sha256:ce047f82692e7c46db1ddcb675be85d43a99936f0859e055db5513219a9ab6d4`; Core `sha256:7649e1f923e6af20ea6d3eb8820ff4d4466840728893374846b7875893e9bcc2`; n8n unchanged39299c21. Only6Gateway modules and3Core files copied; unrelated untracked experimental modules excluded.17serving hashes verified. Host worker/delivery protocol unchanged fromPhase2.

Private backups/config before-files: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/phase3-owner-rollout-20261102T100220` (Gateway8359/Corea6 before initial pair) and `phase3-owner-version-label-rollout-20261102` (Coreb2 before one-line Native version label followup). Scripts `phase3-owner/deploy_main.py` and `deploy_core_version_label.py` validate OFF/queue0, tested immutable candidate, backup, image-only compose diff, worker stop/start and healthy read-back. Initial Coreb2 is historical after7649followup.

Rollback only when idle: stop scheduled worker, restore appropriate AI_IMAGE/CORE_IMAGE and image-lock/ui-bridge before-files, recreate exact previous images and verify health/state before worker start. To reverse only final label use Coreb2 snapshot; reverse wholePhase3 to8359/a6 using initial pair snapshot. Do not automatically restore database: new owner receipt tables are additive; restoring DB would discard later runs/reports/knowledge refresh. Unknown request outcomes require reconciliation before any retry. Do not mix with older698Gateway/host protocol without Phase2 matching host restore.

Final13tableProject5/global comparison unchanged. Source/image proof final-live-verification.json; fresh codingE2EPhase3count0, current telemetry uses historical390 artifacts. No GUI, n8nkey migration or PRmerge.

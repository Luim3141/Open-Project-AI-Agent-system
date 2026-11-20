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

<!-- PHASE3_1_CURRENT -->
# Phase3.1 — current, 2026-11-02T23:14:21+07:00

MAIN Gateway `sha256:b184f91963e53df47cbc884cc353d03b0bce871ee19b45b5dc7a5ca78fd638ab`, Core `sha256:e8474e53c7f56a46cd724f4a938a33f9ba01374fbaeb4bb729499cce4fbd4e84`. OFF/active0/workerALIVE; source+pins/API verified, **OWNER UAT PENDING**. #391 vẫn BLOCKED/provider429; không resume trong phiên này. Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json` và `FINAL_TEST_RESULTS.json` schema5. Các mục cũ phía dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

## Evidence Phase3.1

`phase3_1/main-readback.json`: actual signed API/production ERB, #391/role/budget/notification/health. `native-identity.json`: Native379/391 cùng loạiTask,379một record; `wp391-before.json`/`wp391-after-identity.json`: exact protected record hashes/provider474 unchanged. `native-before.json`/`native-after-identity.json`:13tables identical. Candidate/clone/review scopes ở report tập trung; no GUI/provider inference.

---

# Owner controls và live observability — Phase 3

## Outcome và bằng chứng

Owner-reported GitHub Sync, controls và missing live observability được giữ là observed failures của Phase2. Phase3 đã sửa source, deploy và kiểm API/clone; chỉ Owner được quyết định browser acceptance. URL MAIN đã đọc port mapping: http://localhost:18088/projects/ai-dev-demo/qldapm-ai.

`phase3-owner/final-live-verification.json` là authority runtime/source/pins; `deployment.json` giữ rollout ban đầu và `core-version-followup-deployment.json` giữ bản sửa label Native version cuối. Gatewayce047/Core7649/n8n392; full digests trong JSON, modeOFF/queue0/provider gatefalse.

## GitHub Sync contract

`Owner click → capture submit once → FormData + CSRF + request UUID → authenticated Rails command → HMAC internal/ui Gateway → Native-authorized Owner18 → durable owner6 request reservation → fresh remote GH → Native activity journal/read-back → persisted sync metadata → JSON result/correlation + fresh server fragments → render tab-github`.

Không phụ thuộc native/Turbo form navigation hoặc F5. Khi sync nút ghi SYNCING; command error/rejection/unknown được phân biệt. Lần MAIN thực qua `Qldapm::AiBridge.call` trong `main-bridge-readback.json`: hai distinct UUID sync SUCCESS/changedfalse, cùng UUID replay exact response. Native POST activity có pending journal, marker GET read-back trước xác nhận; unknown không repost. External state change/403/429/500/concurrent/reordered replies/stacked merge-to-feature được kiểm bằng fixtures. Không đổi remote PR để chế tạo một MAIN test.

Một root cause chỉ thấy ở Rails clone: set header string no-store bị common cache callback ghi đè. `response.cache_control.merge!(no_store:true)` sửa response thực; clone gate đỏ trước sửa, xanh sau sửa. Không suy Node VM chứng minh browser interaction.

## Operator command contract

Rails không còn gọi invalid `engineering_control RUN_ONCE` rồi nuốt lỗi. Existing operation dùng đúng endpoint/action, request UUID được giữ tới terminal response. Gateway trả command_id/request_id/requested_action/accepted/reason_code/current_state/desired_state/state_revision/server_timestamp/affected_run_id, persisted recent receipts. Expected revision được gửi cho mode control; stale revision trả rejected/409 và fresh persisted mode, UI không báo thành công giả.

Store.begin/finish namespace owner6 bind authenticated actor/project/action/arguments. AUTO(keyX)→OFF(keyY)→replay AUTO(keyX) trả original response nhưng durable mode vẫnOFF. Different payload same UUID conflict; concurrent same report request một effect. Pending outcome không tự replay. HTTP5xx/409 thiếu matching durable receipt và network/JSON timeout giữ UUID/unknown lock; nếu receipt về qua recent_commands, unlock chỉ đúng form/request (kể cả stable intake/schedule modal). Lookup recent receipts giới hạn10; crash hoặc outcome không có receipt cần operator reconciliation, không có safe automatic retry.

Desired OFF/AUTO/PAUSED tách effective OFF/AUTO_IDLE/READY/RUNNING/PAUSE_REQUESTED/STOP_AFTER_CURRENT/CANCEL_REQUESTED/WORKER_STALE. OFF chặn automatic admission; worker cooperative guard checkpoint sau current noninterruptible operation, không tuyên bố active run đã dừng chỉ vì desiredOFF. PAUSE/CANCEL requested khác confirmed. RUN ONCE chỉ chọn canonical eligible=true và current Native version; queueEMPTY hiển thị NO ELIGIBLE WORK. Không làm yếu Native/Rails RBAC: Owner18 khác actor19.

## Durable telemetry và polling

`execution_events + gemini_call_receipts + engineering_checkpoints/plans + n8n durable outbox metadata` là canonical source, không phụ thuộc WF04 retained execution data. Bounded100events/10runs/20receipts mỗi run, allowlisted IDs/codes/hashes/timestamps; không raw prompts/auth headers/errors.

Feed có sequence/event_id/run_id/trace_id/agent/status/time; full snapshot replace tránh duplicate accumulation. Pipeline PM→BA→Dev→Reviewer→QA→GitHub→Native→n8n→RAG→Reports chỉ PASS khi persisted artifact tương ứng đủ điều kiện. Internal review/QA không phải GitHub native approval; PR không đồng nghĩa demo deployment. Run390 replay read-only nối đúng reviewed diff/head/test-log/child390v2/13ACK; ReportsUNKNOWN do thiếu per-run linkage, không bịa.

Adaptive polling:3sactive/15sidle/60shidden, timeout12s, không overlap; delay tính sau response, không phải SLA wall-clock bất kể network. Tab active/online refresh ngay khi không có request pending; stale generation/revision bị bỏ. Latency contract bằng fake clock/controlled requests, MAIN signed status/API đọc thật; không measurement browser/render latency. Disconnect label toàn trang đổi STALE/UNKNOWN, panel cũ ghi rõ snapshot. Server fragments10regions giữ focus input, modal edits/search state; forms và handlers dùng delegation, Turbo lifecycle cleanup chống listeners/pollers lặp. Inspector riêng có request token cho success/error để runA trả muộn không ghi evidence vào runB.

## Reports / Knowledge / Notifications

Reports list/card tự thay từ fresh projection, metrics theo đúng nested schema, narrative reader text-safe có ID/race/error guard. AI chưa xác minh và usage incomplete được hiển thị. Native version card dùng lock_version thực; citation chỉ chấp nhận `/work_packages/<id>` hoặc `/activity`, không dùng arbitrary vector URL.

Knowledge query/search form JSON update riêng results, không mất query khi poll. MAIN signed exact387/389/390 version2/citation đúng, denseREADY; `main-exact-knowledge.json`. Source refresh root cause/caveat tại `phase3-owner/rag/RESULT.md`, không semantic acceptance. Notifications bar có live region và dismiss có durable Gateway effect. Schedule mở từ latest read-back, payload gửi đủ fields; poll không clobber form đang sửa.

## Tests và runtime boundaries

- `gateway-candidate-final.json`:74 tests, immutablece047, networknone, readonly fixtures/adapters. Các failed harness trước giữ lại, không lấy làm production defects hoặc cộng số test.
- `checks/final-engineering-qualified-*.json`:162 host engineering tests; source manifest changed do Core work song song, Gateway6 production modules vẫn exactmatch. Không dùng suite này một mình xác nhận finalCore.
- `core-clone-result.json`: final7649 actual NativeAPI/Owner18 login/session, validCSRF JSONcommand, invalidCSRF bị401/403/422 trước Gateway,10livefragments/no-store/knowledge version. Password/TOTP/settings chỉ fixture trong clone, không sửa MAIN MFA. Gateway boundary synthetic; actual signed Rails→Gateway integration được kiểm riêng trên MAIN.
- `checks/ui-final-7649-*.json`: actual inline JS NodeVM transport/XSS/reader/Inspector, source stable; không browser automation.
- `REVIEW.md`: independent review7Important fixed red/green; thêm cache-control finding từ actual Rails và Native version mismatch đã sửa sau review bằng targeted contracts/clone.
- `native-after-final.json`:13tables toàn cột không đổi so baseline. Full database/infrastructure DR không thuộc so sánh này.

Không tạo Phase3 fresh E2E/coding task hoặc merge PR. Coding E2E390 là evidence lịch sửbca/Corea6, chỉ replay artifacts để kiểm projection Phase3. Không gọi đó whole-image coding E2Ece047/7649. Owner UAT vẫn PENDING.

Final signed read-back17:27+07 trên exactce047/7649: OFF/EMPTY/workerALIVE,100events; provider receipt count trước/sau status-only window bằng nhau (delta0), không suy billing từ con số này. Owner request3DONE, GitHub journal10DONE, historical generic pending set31 được giữ nguyên/khôngreplay (`final-journal-readback.json`).

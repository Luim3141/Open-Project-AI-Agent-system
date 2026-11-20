# Gemini Assistant Level 2 — checkpoint

**Hiện hành15/10/2026:** đọc [continuous checkpoint](CONTINUOUS_CHECKPOINT_2026-10-15.md). User đã cho phép Gemini không hết hạn và chấp nhận chi phí; staging ON/authorized/expires:null, key/model/project/data scope giữ nguyên.117Windows regression/53Linux (1OS skip)/29UI/10native API, Google thật/API/MCP và human browser chat/auto refresh/restart PASS;329nguồn giữ nguyên. Main/live chưa deploy. Mọi rule Free1h/budget-zero/providerOFF bên dưới là lịch sử trước consent mới (không mở ngân sách Jira/add-ons).

## Resume nhanh — trạng thái mới nhất14/10/2026 23:30+07

- Final **STAGING ONLY**18091/18092: cored4b5a070…/gatewaybee98f08…; clean fork3e2d226b…. Main8088/8090 giữ core2bee…/gateway7190…, chưa deploy live/Jira/đổi workflow.
- PASS112Windows units,61Linux tests (1OS skip),28native UI/bridge cases,10nhóm native API, HTTP+stdio MCP26tools, source/image/fork parity/pip check. Actual Google smoke/metadata329/create+scoped update PASS; synthetic fixtures394/395/396 đã dọn chính xác, nguồn329 giữ nguyên.
- User duyệt ONLY staging role12 QLDAPM PM manage_subtasks, đã áp dụng; backup rollback permissions private `stage/level2-pm-permission-before-20261014.json`. Không cấp quyền khác/live.
- **Gemini Free proof đã hết hạn23:26:49+07.** Không được tự renew/reset usage; key/config vẫn giữ. Native tools/proposals/history vẫn hoạt động. Muốn inference mới phải xác minh Free/no billing/quota đúng project/model và proof mới qua quy trình hiện có; không paste key vào chat.
- Restart final staging DB/web/gateway **PASS**, session94898 EXIT0/log `artifacts/level2-restart-final.log`/receipt `level2-restart-final.json`.329unique/NEW full native attributes, keys/config/proof, AI runs/usage/circuit và exact stage/live images giữ nguyên; Gateway ok/OpenProject authenticated/Gemini blocked do expiry, Google0. Script `tests/stage_restart_level2.py`. Hai preflight lỗi harness (`docker top` thiếu PID và tên DB container) đã sửa trước bất kỳ restart nào; không phải data/application failure. Không còn test process đang chạy.
- Manifest hiện tại `artifacts/level2-candidate.json` harness730beb4d…, **không** sealed qualification. Backup last stopped-state/lock/proof: private `operator/level2-consent-91e7b040-8cf5-4b94-b4a5-e35b13e6d127`; DB/full state backup `operator/level2-final-30d095b2-74ed-4f4a-bbb6-5b9e06f0c5bb` và `level2-stage-ea17d4f3-7673-4dcb-9ee7-bd873bfe4c14`.
- Còn thiếu: actual browser/login/TOTP acceptance (Edge3 unavailable), full new sealed qualification/restore và separate exact production approval/rollout, private semantic code/people/Sprint planning. AI GET server-side~18–19s trên constrained staging, chưa đo browser latency.
- Đọc `LEVEL2_RUNBOOK.md` và `TEST_MATRIX.md`. Không seed/reset/drop volumes, không host Windows SQLite khi gateway Linux đang chạy; dùng HTTP/ContainerState hoặc `docker exec` readonly. Không coi proof/qualification/log RUNNING cũ bên dưới là trạng thái hiện tại.

## Yêu cầu và quyền thực hiện

- Yêu cầu gốc: attachment `C:/Users/LUIM/.codex/attachments/ed55a45c-544e-478d-8bd5-ee13b5513e10/Pasted text.txt`.
- Hoàn thiện Gemini Assistant Level 2 trong workspace hiện có; ưu tiên chạy thực tế trước 15/10/2026. Người dùng yêu cầu lưu checkpoint để tiếp tục khi hết quota.
- Được chỉnh source, build và kiểm thử staging. Không reset dữ liệu/volumes, thay workflow live, tự cấp quyền hoặc deploy production. Production/rủi ro cao cần approval riêng.
- Budget zero; giữ key backend hiện có. Không gửi secret vào chat/log/frontend. Gemini proof hết hạn thì fail closed, không tự gia hạn hoặc reset usage.

## Khảo sát 14/10/2026 21:32 Asia/Bangkok

- Đã đọc AGENTS.md, README/CHECKPOINT/TEST_MATRIX, MEMBER_TOKEN_ENROLLMENT, gateway service/native/gemini/store/app, controller và mutation service core. Tài liệu lịch sử rất dài; ưu tiên phần resume mới nhất.
- Docker ps: live core/proxy/gateway healthy trên 8088/8090; stage core healthy và gateway running trên 18091/18092. Không có process release.py/Test-Release còn chạy theo Win32_Process. Chưa kiểm tra sealed result qualification b78f9fca…; không coi qualification PASS.
- Existing source: strict schema2 gate check trước ghi; native API client, actor binding, SQLite request/audit/proposal, UI session/CSRF signed bridge và Gemini bounded HTTP Function Calling. SDK Google chính thức chưa có trong requirements. Chưa Native Mode. Cập nhật mới hỗ trợ subject/description/assignee, chưa deadline/priority.
- Gemini chỉ smoke/public demo/project-metadata có proof manual Free/no billing TTL1h. Proof cũ expired 19:27:19+07; chưa gọi Google lượt này. Đã hỏi xác minh Free/no billing/quota mới qua async input; key không cần paste.
- Workspace phần lớn untracked từ trước; không dùng git reset/clean hoặc stage toàn bộ.

## Kế hoạch tiếp tục

1. Kiểm tra terminal qualification cũ và health/API hiện tại, lưu baseline image IDs.
2. Thêm strict/native rõ ràng, native API v3 giữ actor permission, optimistic lock, idempotency và audit; custom gate denied trong native. Strict giữ schema2 hiện có (không hạ xuống schema1).
3. Tích hợp Google GenAI SDK chính thức, model cấu hình, giữ Free proof/quota/circuit/data projection; kiểm thử lỗi upstream phân biệt nguồn.
4. Bổ sung deadline/priority, đọc/tìm kiếm/tiến độ quá hạn, reject proposal, history/settings/connectivity vào UI có sẵn; kiểm thử hành vi/quyền và readback.
5. Build/deploy riêng staging bằng pinned image và backup hiện có; không chạy Setup/seeder. Test API/UI/write/replay/restart với dữ liệu fixture staging. Google thật BLOCKED đến khi xác minh Free mới.
6. Cập nhật architecture.md/TEST_MATRIX/runbook/checkpoint. Chuẩn bị production preview, không cutover khi chưa approval.

## Quy tắc resume

- Đọc file này trước, rồi đầu CHECKPOINT.md. Kiểm tra process Docker/lease/job trước thay đổi; không giả định trạng thái cũ còn đúng.
- Chưa có code thay đổi tại mốc đầu; không có live/staging business writes hoặc Google calls.
- Cập nhật bằng chứng ở đây sau từng mốc; chỉ ghi PASS cho test đã chạy thành công, BLOCKED kèm nguyên nhân.

## Mốc source/build — 14/10 khoảng 22:00+07

- Đã triển khai source: `gateway_mode=strict|native` (default strict/schema2); native PATCH API v3/readback, custom gate denied; `auto_execute` chỉ bốn thao tác native thông thường do caller yêu cầu trực tiếp, worker Gemini không được cấp tự duyệt. UNKNOWN không tự retry.
- Thêm due_date/priority, query/parent filter, overdue, reject proposal, own history, safe status và UI dashboard/settings/Approve/Reject/history. Google GenAI SDK2.30.1 được cài trong venv và requirements/lock; retry1 attempt, automatic function execution/continuation OFF, bounded response và worker timeout giữ nguyên. SDK countTokens không hỗ trợ tools/system trên Developer API; thêm nội dung vào probe và dùng full payload byte cap khi reserve TPM.
- Offline test đã phát hiện và sửa khác biệt wire SDK (thinking enum snake/uppercase), fixture circuit isolation và shared fixture date. Lượt full104 đang chạy lại; chưa ghi PASS đến terminal result.
- Build core image566d2365… và gateway833963ea… PASS; chưa stage promotion ở mốc này. Source thay đổi làm mọi qualification cũ stale. Sealed result b78f9fca… không có; process cũ đã dừng. Không tự ký proof từ log từng phần.
- Linux read-only stage gateway: actor map6BA-PM/7PM/8BE/9FE/10QA, project3, strict,0running AI runs/0active jobs. Không đọc SQLite bằng Windows khi container đang chạy.
- Live2bee…/7190… chưa đổi. Google0calls lượt này; câu hỏi Free/no-billing/quota mới vẫn chưa có trả lời.

## Staging deployed / acceptance — 14/10 21:56+07

- Full104unit PASS (artifacts/level2-unit-all.log), provider/native28 targeted PASS sau model CLI thay đổi. Native core/UI/bridge25 cases + privacy/snapshot/provenance/receipt PASS (artifacts/level2-native-ui.log). Sau đó bổ sung2UI cases và SDK continuation/role regressions; final suite đang chạy, phải kiểm tra terminal.
- Stage promoted riêng: core `sha256:fd7f04c2ae6e225f703ab31bfa4736187dc73d324481be0145a954e64c476eb6`, gateway `sha256:3bb92dd125439703861c00d41ac0552f4b03c9ef5e87871618710ed55da54525`, runtime gateway_mode=native và stage-image-lock cập nhật. Không seeder/migration/recreate DB. Backup gateway stopped-state/full stage DB/old image lock: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/level2-stage-ea17d4f3-7673-4dcb-9ee7-bd873bfe4c14`.
- Actual API acceptance PARTIAL:10checks PASS qua real `/internal/ui` signed synthetic actor, native OpenProject readback; Task create/replay(one object), Subtask type create/assignee, description/deadline/priority/stale lock, comment journal/replay, BE valid transition/QA denial, preview/approve once, Reject no mutation/consumed denial, native customgate refusal/own history/search. Fixture388/389 cleaned EXACT IDs/UUID; baseline329 retained. Artifact `artifacts/level2-stage-acceptance.log`. No Google calls.
- Subtask parent BLOCKED: native role QLDAPM PM lacks `manage_subtasks`; `/work_packages/form` returns parent PropertyIsReadOnly. Initial test created Task only, failed parent child and cleaned owned Task. No permission bypass/grant. Asked async approval of adding ONLY manage_subtasks to STAGING PM; no answer yet. Continue independent tests with parent link explicitly BLOCKED, not full PASS.
- Edge new tab at staging AI URL requires login; marked handoff and asked user to log in. No session/TOTP/password changes. Actual visual/browser acceptance BLOCKED until login.
- Source after initial image deployment additionally adds role selectors (actual unique registered role reverified), SDK manual-model CLI, full actual status/due/type metadata, localized exact-fact rendering and expanded tool contracts. Must rebuild/redeploy final source and rerun tests before reporting final image parity. Existing stage images above are initial Level2 candidate, not final source.
- Gemini fresh proof and production cutover still not authorized/verified; no live/Jira/Google changes. Full semantic private ticket/code chat and personnel planning cannot be claimed from metadata-only mode.

## User approval / real Gemini — supersedes previous BLOCKED

- User confirms same Free/no billing/quota and approves ONLY staging PM manage_subtasks. Applied ONLY this permission to role12/project3; full329 WorkPackage-attribute fingerprint unchanged. Private before/rollback file `stage/level2-pm-permission-before-20261014.json`; artifact `artifacts/level2-permission-apply.log`. Browser “ok” did not prove login; tab still login on last read.
- Fresh user reconfirmation of previous official-console evidence, NOT fresh assistant console/billing API verification. Same existing key/project/model/quota15/250000/500 and project-metadata-only scope. Proof expires **14/10/2026 23:26:49+07**, no auto renewal. Private evidence `operator/gemini-free/user-reconfirmation-level2-20261014.md`, backup `level2-reconfirmation-18d4705e-7b4c-4d6a-9baa-59b490fb88d5`.
- Real SDK first smoke FAIL; gzip double decoding reproduced RED, encoding/length stripped after iter_bytes decoding → GREEN. Only diagnosed client-error circuit cleared with recovery receipt/same fresh proof; failed reservation retained. Controlled fixed countTokens/generateContent PASSQLDAPM_OK (`level2-google-sdk-smoke-fixed.log`),109Windows units PASS.
- Parent-enabled staging native10checks ALL PASS; exact fixtures392/393 cleaned,329source retained (`level2-stage-parent-approved.log`). No workflow/live/user/credential changes.
- First real metadata run1b88c780… rejected invalid claims. Added official Gemini3 structured JSON schema and explicit tool_index/tool_result paths; exact source-value validator retained. Real run **134a8a4d-c5c6-4313-bcf7-fb15ccdb83f2 PASS** returns `Số công việc: 329 [nguồn #0]`; independent native/REST/MCP HTTP+stdio/replay/anonymous401 PASS. Artifact `level2-google-metadata-structured-ready.log`. Earlier warmup disconnect was before any probe, logged separately.46 targeted regressions PASS.
- Deployed at that success: core33ee4753…/gatewayb6f5688c…; main2bee…/7190… unchanged. No sealed new full qualification.

## Run-scoped consent —23:04+07, promotion/testing pending

- Caller/UI allow_routine_writes defaultfalse, write_scope_ids max6positive existing IDs. Only four ordinary Native actions inherit explicit consent for ONE run. Target updates outside selected IDs denied; new IDs tracked locally; model cannot self-authorize. Code/gate/admin/deploy never inherit consent. Max6tool calls and original idempotency/readback remain.
- Confirmed output metadata excludes ticket text/people. Comment requires native activity readback. Caller, worker, REST/MCP HTTP+stdio, catalog/OpenAPI and Rails checkbox/scope fields updated. Full112Windows units PASS (`level2-unit-complete.log`), scope/flag/privacy tests included.
- Core synced clean forkcommit3e2d226b…; built final-consent pair core `sha256:d4b5a0700eb7dfa20d250222eeb161006bbcbbdc086e12cdc8d34e3619796ac1` / gateway `sha256:bee98f08ac24b25a6aef5bdc3df4b4fe716f1f9366f41f8490962e11484832d0`. NOT YET PROMOTED at this saved point.28UI/final API/actual Gemini write/restart checks pending. Preserve same cost proof; no renewal beyond23:26:49.

## Resume23:18+07 — final pair deployed; real write receipts retained

- Final pair d4b5…/bee98… IS deployed staging; live unchanged. Last stopped-state/lock/proof backup: private `operator/level2-consent-91e7b040-8cf5-4b94-b4a5-e35b13e6d127`.112Windows units PASS; Linux61tests/1OS skip PASS (`level2-linux-complete.log`).
- Actual Google create run `e8b2215d-7b43-4402-b3ac-2844286a72c2` and scoped update run `6d677900-f688-4d58-8104-3c02a067ed70` both DONE with native_confirmed exact claims. Synthetic Task394 sourceAI-LEVEL2-GENAI-* created for BE, update due2026-10-21. Both start replays returned same run IDs. Initial harness final readback/cleanup FAIL because one Native client shared90s deadline across two AI runs; application writes were successful. Fixed test to instantiate independent readback clients and persist run/source before polling. Recovery readback/EXACT fixture cleanup is currently session15468; inspect terminal before reporting cleanup/PASS. Do NOT repeat creates or infer missing result.
- Latest expanded28UI suite first FAIL only old prompt refusal fixture; safe synthetic prompt became allowed metadata and started readonly run00e80782…DONE/0tools. No business writes. Test fixture now synthetic employee@example.invalid to test privacy denial before Google; rerun pending after cleanup329.
- Proof expiry remains23:26:49+07; user reconfirmation not fresh assistant billing-console check. No auto renew/counter reset. Full qualification not sealed; browser last login and production still pending. Read this latest section first on resume.

### Recovery terminal / source parity23:19+07

- Recovery session15468 EXIT0: independent native Task394 subject/BE assignee/description/dueDate exact readback PASS; exact Source ID/project/childless guard cleanup PASS; source329 restored. No extra Google calls or mutation retries. Report `artifacts/level2-google-writes-real.json`, log `level2-google-writes-recovery.log`; original deadline failure log retained.
- `release.candidate()` PASS final immutable source/fork/image parity, commit3e2d226bed01613c90bd9d7ebcea5fdc4226cb4b, harness25d246504d56cef463769dafbf9f0b973d9eb5f09c445124fa6ae3f096112149; artifact `level2-candidate.json`. This is a manifest, NOT sealed qualification approval.
- Browser reread cannot proceed: Edge browser3 no longer available via extension. No auth bypass or browser acceptance claim. Reopen/login normally on18091 when user is available. UI28 rerun launched session; next inspect terminal before reporting PASS.

### Transport terminal23:22+07

- Final stage HTTP+stdio official MCP SDK/all26tools/BE identity/analyze329/anonymous401 PASS (`level2-final-transport.log`, session98680 EXIT0), Google0calls. Gateway pip check PASS. Active AI runs0 at readback.
- UI runner session26570 still running, Docker process `/qldapm-core/deep_stage_test.rb`; wait terminal before stage writes/restart. UI server-side GET observed ~18–19s with three signed native bridge calls on this constrained staging; browser performance not yet measured. Do not claim responsive latency from functional test alone.
- Next: UI terminal → final `tests.stage_level2` exact-fixture test → restart staging only after no active runner/jobs → verify source329/NEW/current images/persisted receipts/quota and expiry. Then update TEST_MATRIX/architecture. Do not automatically call Google again or renew proof.

### UI terminal23:23+07

- Session26570 EXIT0, final image actual AI/Gates UI+bridge **28cases PASS**, ERB rendering, CSRF/permissions/preview/reject/consent signed scope, simulation exclusion/privacy/immutable snapshots/native receipt PASS; transactions rolled back, source329. `artifacts/level2-native-ui-complete.log`. Synthetic session/HTTP fixtures, not actual browser/TOTP acceptance.
- Final native API suite launched after UI terminal; restart will wait for exact cleanup/result. No active AI runs or broker jobs on prior readback; no further Google calls scheduled.

### Final native terminal23:26+07

- Session9195 EXIT0 **10nhóm ALL PASS, blocked[]** on exact final pair; includes comment activity independent readback/new consent-era native source, stale lock/wrong-role/workflow/parent/Approve/Reject/history/search/replay. Exact fixtures395/396 cleaned, source329. Artifact `level2-final-native.log`, Google0calls.
- Restart script `tests/stage_restart_level2.py` checks no active UI/cleanup runner, AI runs/jobs; full native329unique/NEW attributes, private file hashes and persisted AI run/usage/circuit hashes before/after restart ONLY stage DB/web/gateway. Restart launched after native terminal. Preserve proof checked_at; expires23:26:49+07, no new inference.

### Final restart terminal23:30+07

- Session94898 EXIT0/PASS, `level2-restart-final.json`: stage DB/web/gateway restarted; full native329unique/allNEW attributes unchanged, AI run/usage/circuit hashes preserved, private config/key/proof unchanged, exact live/stage immutable images unchanged. HTTP200 status native/OpenProject authenticated/Gateway ok; Gemini **blocked expired** as expected, Google0calls. No active worker/AI/broker jobs before restart. No tests remain running.
- Final manifest parity rerun PASS after adding restart harness; current harness730beb4ddcce81de00659aa31930aa1a96e37a5b43075eda42ec1fd2d6508db2. No sealed new qualification or production release authorization. Runbook/test matrix/README/checkpoint/architecture updated with current results and resume boundaries.

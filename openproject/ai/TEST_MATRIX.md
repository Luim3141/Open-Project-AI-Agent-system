# Ma trận nghiệm thu API/MCP và core gate

**Hiện hành15/10/2026 — Không giới hạn số thao tác Gemini:** hard cap6 tool calls/batch/model turns/write_scope_ids đã bỏ trên staging18091/18092. Deadline120s, tài nguyên, quota và quyền native vẫn áp dụng; xem [checkpoint mới](UNLIMITED_CHECKPOINT_2026-10-15.md). Các ghi chú giới hạn6 bên dưới là lịch sử.

## Business Assistant —15/10/2026

-128Windows regression PASS;54Linux targeted PASS/1Windows-only skip: policy+key binding, full business projection/redaction, exact claims and natural analysis, scope inference/comment-body boundary, partial receipts, no model retry after unknown native write, historical failure visible without replay.
-34nativeRails UI/bridge PASS: readable before-after/comment preview, top status/partial native link, proper GET auto-refresh, expired proposal no approval, model text cannot render remote image/script, CSRF/actor/bounded error messages.
-ActualGoogle7business runs PASS: fullticket58 semantics, requestedcomment58 exactlyonce, PM Task/Subtaskparent/BEassignment, BE multi-field update/deadline/priority and validtransition, proposal→confirmation; exact native readback and ownfixture cleanup keep329.
-Actualbrowser checkboxTRUE/manualIDempty/natural“ngày mai” updates owned405→2026-10-16, autoGETupdate+VN changed-field note; native readback/exactfixturecleanup PASS. Fresh real readablepreview/test-onlyreject PASS, no nativecreate.
-10nativeAPI groups PASS/blocked[] and HTTP/stdioMCP/anonymous401 PASS. Unknown native write/provider failures simulated offline; no deliberate production/outage writes. New source is not a sealed production qualification. See BUSINESS_CHECKPOINT_2026-10-15.md for immutable images/restart terminal.

## Continuous owner authorization —15/10/2026, hiện hành

Staging finalcoreb2f3357f…/gatewayad7f19e7…; main2bee…/7190… unchanged. User ảnh Free tier +explicit cost consent; authorized/expiryNull, historical checked_at/quota không bị fake refresh, chưa billing API verification. Read CONTINUOUS_CHECKPOINT_2026-10-15.md before history below.

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| Windows regression | PASS117 +status targeted1 | continuous-unit-all.log/continuous-cli-status.log; year-later auth/OFF/key/env/cost/data binding, no usage reset,503/429 cooldown/restart/no retry/manual403 |
| Linux targeted | PASS53/1OS skip | continuous-linux.log; network none/read-only |
| Source/fork/image manifest | PASS | continuous-candidate.json, fork1cdc3be0 clean; not sealed qualification |
| Google thật smoke và metadata/API/MCP | PASS | continuous-google-smoke.log/continuous-google-metadata.log; runse5bee7d0…/ca9769a2…/6528f942…, exact329/replay/anonymous401; continuous-provider-acceptance.json confirms after restart/usage59→73 preserved |
| Native UI/bridge | PASS29 | continuous-ui-final.log; new standard http-equiv refresh regression, CSRF/consent/proposal/role/privacy/receipt/source329 |
| Human browser chat | PASS | User login existing BE; actual submit→GET/automatic refresh→cited329, dashboard/settings/menu/authorized/no expiry. continuous-browser-20261015.png; no TOTP claim |
| Native API regression | PASS10/allblocked[] | continuous-native-final.log; Task/Subtask parent/assignee/update/date/priority/comment/valid+wrongrole transition/stale/Approve/Reject/replay/history; exact397/398 cleaned/source329 |
| Stage DB/web/gateway restart | PASS | continuous-restart.json/log;329unique/NEW/full attrs, key/config/proof/usage/circuit/recovery/runs and images unchanged, authorized/expiresNull, Google0 |
| Full sealed qualification/restore/live rollout | NOT_RUN/NOT_APPROVED | Cost consent is not specific production release approval; old proofs stale |

Cooldown applies only to a new user request:4291h,408/5xx/network/timeout60s. Auth/key/client/schema stays manual repair; original run/native writes never replay automatically. Local70% old quota caps retained; Google quota/billing/availability still governs actual service. No endless idle inference, no paid billing setup/key/model change. Old1h policy remains for installations without continuous consent.


## Gemini Assistant Level2 — final staging14/10/2026

Final pair cored4b5a070…/gatewaybee98f08…; main2bee…/7190… giữ nguyên. Bằng chứng mới nhất ở `LEVEL2_CHECKPOINT_2026-10-14.md`; các mục RUNNING cũ bên dưới là lịch sử, không có sealed qualification mới.

| Kiểm tra | Trạng thái | Bằng chứng/phạm vi |
|---|---|---|
| Windows regression | PASS112 | `artifacts/level2-unit-complete.log`; Native/strict, privacy, consent/scope, SDK failure/quota/replay |
| Linux targeted regression | PASS61,1OS skip | `artifacts/level2-linux-complete.log`; network none/read-only |
| Exact source/fork/image + dependencies | PASS | `level2-candidate.json`, fork3e2d226b… clean; final gateway pip check no broken requirements |
| Google SDK thật | PASS | `level2-google-sdk-smoke-fixed.log`; countTokens/generateContent, bounded SDK, no retry |
| Google analyze dữ liệu thật | PASS | `level2-google-metadata-structured-ready.log`; run134a8a4d… trả329, native/REST/MCP/replay/anonymous401 |
| Google create và scoped update thật | PASS sau recovery đọc | `level2-google-writes-real.json`/`level2-google-writes-recovery.log`; runse8b2215d…/6d677900…, fixture394, native readback, replay, exact cleanup/source329. Original harness90s read deadline FAIL được giữ trong log; không gọi lại Google/ghi |
| Native Task/Subtask/parent/assignee/date/priority/status/comment | PASS10nhóm | `level2-stage-parent-approved.log`; synthetic fixtures, role permission/lock/replay/Approve/Reject/history/search. Parent enabled chỉ staging theo user approval |
| Expanded UI/bridge28cases final pair | PASS | `level2-native-ui-complete.log` EXIT0; consent/scope/CSRF/Approve/Reject/privacy/ERB, synthetic session, không browser proof |
| Final pair MCP HTTP+stdio transport | PASS | `level2-final-transport.log`; all26tools/BE identity/analyze329/anonymous401, Google0 |
| Final pair native acceptance | PASS10nhóm | `level2-final-native.log` EXIT0/blocked[]; Task/Subtask,parent, update/comment/transition, permission/lock/proposal/replay; fixtures395/396 cleaned/source329 |
| Final pair DB/web/gateway restart | PASS | `level2-restart-final.json`/log EXIT0; native329unique/NEW/full attributes, keys/config/proof, usage/circuit/runs và stage/live images unchanged; provider expired blocked, Google0 |
| Browser với tài khoản người dùng | BLOCKED | Edge browser3 unavailable; trước đó login chưa được xác minh; không thay credential/session |
| Full qualification/restore/live | NOT_RUN/NOT_APPROVED | Source đổi làm proof cũ stale; không ghép log thành sealed envelope, chưa production cutover |
| Private semantic ticket/code/people planning | NOT_ENABLED | Free metadata projection giữ text/code/PII local; chưa claim full BA/Sprint/HR automation |

Free/no billing/quota do user xác nhận lại evidence cũ; proof hết hạn14/10/2026 **23:26:49+07**, không tự renew/reset. Cho phép tối đa6calls/run và6selected IDs, large bulk/code/gate/admin/deploy cần approval riêng. UI status `verified` là proof còn hạn/circuit đóng, không phải vừa inference thành công.

## Resume14/10 — metadata assistant, staging only

-97Windows units PASS; malformed metadata/negative counts/privacy filtering/production binding and unchanged cost gates covered.4release tests PASS including key/proof deployment approval binding. Google-looking unit HTTP logs use MockTransport, not live calls.
-25native AI/Gates UI/bridge cases PASS on exact core262c30a1…; proposal preview link/manual confirmation boundary and run POST→GET covered, synthetic sessions and transaction rollback. Browser menu/public answer verified preceding turn; new metadata/proposal visual acceptance not rerun.
-Actual Gemini3.5Lite metadata inference PASS: run25249758… returned cited329count, independently matches native; REST/MCP HTTP/stdio/replay/anonymous denial PASS. No writes/private ticket/person/code sent; stage usage14→18/circuit0. Gateway10496cd8… exact source verified. Receipt artifacts/gemini-metadata-real-probe-20261014.json.
-Main8088/8090 not promoted/enabled. Full qualificationb78f9fca… currently RUNNING, not PASS/sealed. Production activation/single-ledger migration/local release approval/main acceptance remain NOT_RUN. Existing Free proof expiry enforced, no renewal/reset/paid fallback.

## Hiện hành — 2026-10-13

### Model switch14/10 — exact3.5Lite actual connectivity PASS

-92offline Windows regression tests PASS: expected literal outbound3.5Lite URL and minimal thinking, stale3.8model proof denial, shared privacy/expired/paid/key/production/429/replay guards. Mock HTTP is not Google smoke evidence.
- Fresh existing-key same-project Google direct fixed smoke PASS; separate real stage REST run PASSQLDAPM_OK/exact3.5Lite, same-ID replay/MCP HTTP/stdio read/anonymous401 PASS.2probes/4Google requests, usage6→10 retained, no arbitrary prompt/tool data or paid fallback. Stage-native SDKanalyze329 PASS/Google0.
- Cached offline stage pairc77dbdae…/ec4b0e1e… deployed, source/image12gateway file hashes/coreheading match; corehealthy/gatewayhealth200/liveunchanged. Compile/Bashsyntax/forkdiffcheck PASS. Backup stopped state/proof before mutation retained. Browser open queued, fresh browser acceptance NOT_RUN. Full release qualification/human/live acceptance NOT_RUN; older qualification cannot authorize changed pair/source. ON_SMOKE_ONLY expiry14/10 17:21:52+07; general project chat NOT_ENABLED.

### Terminal14/10 — native upgrade/rollback PASS; qualification not sealed

- d6c2669c… full run EXIT1 at remote DNS/getaddrinfo;28successful logs, no signed qualification. Same immutable candidate/harness unchanged after run. Separate unchanged remote HTTPS HTTP/stdio SDK rerun PASS; not counted as a successful full pipeline or independent local approval.
- Mandatory OfficialOrigin UUID2f495606… PASS: actual official2bee/old schema/BA/legacy4 before migration; injected failure returned original image/schema/full fingerprints/state, success migrated to8ae2/3f with source329/106AC/native guard/source comparison. Original schema reconstructed from synthetic stage, NOT actual production DB clone. Restore494d… PASS33critical fingerprints/assets/config; all3sandbox suites PASS, native receipt where supported. Temp containers/networks cleaned, volumes/backups retained.
- Final native personal-PM readback BOTH329uniqueSourceIDs/329NEW;0primary approval receipts/no primary sync/live image change. ProviderOFF/4natural rolling-window reservations/1circuit/keyretained. Fresh correct-project Free/no billing observed but quota unavailable; no new inference. Normal Free project/personnel chat, full sealed qualification/local independent approval and live/real-user acceptance remain incomplete.

### Resume14/10 14:00+07 — full rerun after official-origin readback fix

- UUIDa6a0f847… release and rollback receipts succeeded, but whole paired harness exited1 at final strict candidate-vs-original-schema assertion. Read-only retained clone comparison RED showed only expected migrated tables/field; source-mode comparison GREEN33. Source comparison now used only after OfficialOrigin success; exact full restore/official schema assertions retained for rollback. Parse/4release units PASS; prior partial trial remains NOT whole-test PASS.
- Qualification d6c2669c… RUNNING under broker lease,29checks expected with migration_roles and mandatory OfficialOrigin pair. Frozen images8ae2…/3f53…, fork1f4…, harness8bb0b9ac…/migrationf1cb2a4e…. No new proof or live approval yet; older3aa… stale. Same existing key kept, fresh no-billing observation but quota unavailable, providerOFF/no new inference.

### Continuation14/10 — BA migration regression and official-origin trial

- New native migrate_roles_test.rb RED RecordNotFound→GREEN after common migration resolves project-membership roles with existing GatePolicy aliases. Renamed BA works, foreign global BA-PM ignored, simultaneous project aliases denied; every change rolled back with329attribute fingerprints and original role verified.92Windows units/compile/Ruby/PowerShell syntax PASS.
- Earlier3aa… PASS28 proof is now STALE (new harness/migration hashes), not valid for deploy. Images/source work/credentials/Gemini unchanged. No primary apply/approval, no new Google request.
- Extended existing Docker paired seam OfficialOrigin mode (unknown parameter RED before support). UUID trial cb6d6755… currently RUNNING: reconstructed synthetic legacy schema/actual official2bee binary, failure rollback first then success. No live volumes/credentials or primary data used; source329/legacy4states/absent candidate schema must be asserted. No PASS claim yet; production-clone equivalence/real TOTP/Codex and normal Gemini data contract remain unverified.

### Terminal14/10 10:08+07 — PASS28 technical checks, not live/Gemini approval

- Qualification3aa5103c… exited0/PASS28, signature/candidate/harness/restore hash reverified PASS; expires15/10 10:05:12+07. Core8ae2…/gateway3f53…/forkclean1f4aa591…. All previously pending clone pair success+failure rollback and remote HTTPS HTTP/stdio SDK checks PASS; temporary containers/networks gone, retained snapshots/backups.
- Final primary329NEWboth/source sync NOT_APPLIED; stagegatewayhealth200/livehealthy and images unchanged. Existing key unchanged/providerOFF/8reservations/1circuit. One independent Google models.get READ HTTP200/exactmodel/generateContent supported;0new inference calls and no project data. This metadata response is NOT a generation smoke.
- Rate Limit correct project/All models still has no rows, quota UNKNOWN; old provider proof expired. Normal Free chat/data-policy, official→candidate binary upgrade, full-core non-overlay qualification, real-user TOTP/Codex and independent exact local release approval/live acceptance remain NOT_RUN/NOT_APPROVED. The qualification signature is technical test evidence only. RUNNING paragraphs below are history.

### 14/10 follow-up — new stage gateway, full qualification RUNNING

- Stage3f53f480…/8ae2…, forkclean1f4aa591…; exact candidate() manifests PASS. State backup copied/hash verified while stage gateway stopped and0active AI runs/jobs. No live image/config, source sync, Google proof/key/billing/counter changes.
- Actual main HTTP+stdio SDK/23tools/analyze329/anonymous401 PASS. Qualification3aa5103c… completed unit92, lease/pair fixture/Linux queue/operator confirmation, native migration/source329+106AC, native/bulk/hierarchy/self-approval/stale-review checks, concurrency,42valid+42wrong-role policy, metrics/test receipt, native UI/privacy, admin transaction rollback, source comparison, five synthetic API identities, writes+fixture cleanup and local transport.
- Sandbox gate-policy/gateway/core-integration PASS with immutable code snapshot; only first/third suites accepted as native automatic evidence. Restore51f3ade3… PASS33critical-table fingerprints/database/assets/config, retained isolated volumes/backups. Not a claim that every database table was fingerprinted by this restore harness.
- Full qualification still RUNNING: paired Docker release/rollback and remote acceptance pending; no sealed new proof or independent release approval yet. Official→candidate upgrade/real TOTP/Codex/live acceptance and general Gemini normal-data contract remain NOT_RUN. ProviderOFF/expired1hproof,8requests24h/1circuit, correct-project quota rows unavailable, no new Google request.

### Resume14/10 09:25+07

- PASS92Windows tests; Docker92discovered/3Windows-only skip (lease tested on Windows); compile/nested-core diff checks. New general provider malformed-generation fixture RED7errors→GREEN/no tool execution. Project budget reserves before each model round and counts full payload, exact thought signatures/call IDs retained. Google HTTP in these tests is MockTransport, not provider acceptance.
- PASS offline build3f53f480… and12gateway source/image hashes. Built-only; no stage/live promotion or full release qualification. Patched build recipe now included in release harness hash; nested core still dirty2ownedlines.
- PASS primary read-only329NEWboth/zero local apply receipts, official QAG3 identity/resources/project/source-field checksum and both current full native backup proofs. New previews0unmapped/329content/2comments/265Simulation logs; stage242blocked/live243retained. Apply/readback on primary NOT_RUN, pending exact local human confirmation.
- Gemini real new requests NOT_RUN; enabledfalse/8reserved24h/1circuit. AI Studio correct project Free tier, All models quota rows unavailable; quota UNKNOWN rather than assumed5/250000/20. Normal Free chat/data-policy and official→candidate upgrade/live rollout acceptance remain NOT_RUN.

### Final14/10 sync qualification — PASS clones, pending primary approval

| Check | Observed result |
|---|---|
| Full restore DB/sequence/assets/config | PASS live218/stage221; updated archives91d1…/9092… |
| Native full import/readback | PASS329contents/2comments/265Simulation entries each; native329/no content conflicts |
| Native replay | PASS329each/no duplicate markers or entries |
| Status scope | Live86same/243retained; stage87same/242gateblocked; no fake approvals/intermediate transitions |
| Scheduling | Retain344relations/old modes;329direct dates not equivalent, source dates documentary; no Gantt parity claim |
| Native stage gate/Insights | DirectDone rejected; imported simulation excluded; PASS |
| Runtime image policy | PASS42valid+42wrong-role edges/self-review/reviewer/emptyEpic |
| Source/helper regression |89Windows units/23sync PASS; compile/pip/diff PASS |
| Installed stage image |8ae2b351…/gateway1cd… healthy; Insights transaction rollback PASS |
| Primary after tests | Both329NEW; costs disabled/2PMpermissions absent/Simulation absent; no sync applied |
| General UI/Google/live core cutover | NOT_RUN in this sync; no provider/Jira/bot/schedule/billing mutation |

All owned clone containers/volumes/networks cleaned; backups and failed trial receipts retained. Exact local human preview approval remains required before primary apply; no automatic UNKNOWN retry/restore.

Latest14/10:89units/23sync PASS; native344relations/343follows evidence shows manual predecessor changes can reschedule automatic successors. Stale native versions were blocked correctly. Preview regression RED→GREEN now preserves linked-node dates/local mode and documents source dates, with relation-hash concurrency guard. Rejected full trials retained as FAIL, owned clone resources cleaned; new full trials stage86760797/live420d41e3 not accepted yet. Primary data/config/images/Jira/Gemini unchanged.

14/10 resume:88Windows units/22sync PASS. Actual clone parent-date readback RED (description exact; auto parent dates null) → public preview regression GREEN preserving automatic local schedule, reporting non-equivalence and retaining source dates. Fresh full329 native qualification still running. Rejected clone cleanup verified UUID labels; backups/receipts retained, primary data/images unchanged.

Power-loss resume: actual primary329NEWboth, stage exact-image restart PASS. Full backup restore DB/all tables+sequences/assets/config/config transaction PASS stage221/live218; first native sample worklog422 RED due comment1000 limit → compact+full-ticket-source GREEN (1content/1Simulation entry/replay/deniedDONE/Insights exclusion). Interrupted sample without result NOT_PASS.86full units PASS;21sync units after lease PASS. Added durable status-timeout replay denial and noninteractive CLI/config denial RED→GREEN. Full329 native import/candidate promotion/primary exact approval/apply NOT_RUN yet; no Jira/Google writes or source data apply.

Jira config follow-up after user scope approval: native staging transaction regression RED→GREEN for stale hash, no partial mutation, transaction requirement, replay, exact PM permissions, Simulation project isolation and non-admin PM time-entry creation contract; rollback verified.72 Windows units rerun PASS. No committing configuration runner/live apply, isolated backup/restore, native worklog import or sync verify accepted yet. Historical cfg hashes are not fresh approvals.

Follow-up validation:73 units PASS; isolated synthetic-stage **DB-only** dump/restore + native configuration regression PASS on pinned image; temporary UUID containers/network removed. Raw checkout attempt failed before config (CRLF ERB boot), corrected by testing the pinned runtime image rather than Windows sources for this suite. Full both-target DB/assets/config restore/hash and import/apply/verify still NOT_RUN.

### Jira one-way sync — PARTIAL20:47, chưa ghi dữ liệu

Official-MCP full snapshot329/265worklogs/2comments/1697changelogs/0attachments/1futureSprint PASS; interrupted-read checkpoints/resume completed after2readtimeouts, no source write. Both target SourceID maps329/no duplicates/unmapped PASS. Stage actual gate preview242denied/243differences, live native workflow validation pending; not status parity. PM native time-entry form403both; configuration proposal only, no grant/module/activity changes.72Windows unitsPASS including6new CLI-domain boundaries; source-only staging normalUpdateService/Insights regression RED→GREEN with transactionrollback, not deployed candidate. Live original329Source/106AC/parent/assignee/description/roles GET verifier PASS. Backup/rehearsal/apply/verify/idempotent write/import acceptance NOT_RUN/not implemented; requires new configuration authority. See JIRA_SYNC_RUNBOOK.md.

### Fresh Google probe19:50 — FAIL timeout, local transport PASS

Fresh Free/no billing/exact project/quota5/250000/20 đối soát bằng official browser; caps3/175000/14 và key giữ nguyên. Assistant documentary verification không independent human review; proof valid20:49:27. One actual smoke: countTokens parsed18 PASS, generation timeout/no output, providerOFF/circuit latched, usage6→8/14/no refund/retry/fallback. Main staging health/actual REST/MCP HTTP/stdio/anonymous401/analyze329 PASS, Google calls0 trong transport. Browser localhost automation bị policy từ chối, UI test mới NOT_RUN, không workaround. Artifact artifacts/gemini-real-probe-20261013-1950.json; chưa general chat/live release.

### Fresh Google probe17:56 — FAIL generation, không giả PASS

Fresh Google console Free/no billing/exact project/quota5/250000/20 verified; scopefixed-smoke/caps3/175000/14/key giữ nguyên. Assistant-operated verification có documentary provenance, không independent human review. Fresh proof valid18:56:21. One real probe countTokens PASS/generateContent503 UNAVAILABLE UNKNOWN, no text; Gemini OFF/circuit latched/usage4→6/14, no retry/refund/fallback. Same-image gateway restored/health200; actual native REST/MCP HTTP/stdio23tools/analyze329/anonymous401 rerun PASS, no extra Google calls. Official Status Free tier operational không bảo đảm từng request/model. Artifact artifacts/gemini-real-probe-20261013-1756.json; general chat chưa mở.

### Bugfix POST500 (mới nhất)

Final core0ab293ea…/forkc715001d…, gateway1cd1687b…. Root `I18n::ArgumentError` shadowing; native controller fixture RED500→GREEN với chuẩn `::ArgumentError`.22cases gồm18controller và4bridge HTTP fixtures; payload JSON sai/array, missing arguments/status, tool allowlist, CSRF, denied/unowned run/proposal, Insights PM/self/window/response privacy, self-approval/wrong reviewer, malformed job receipt, error redaction/2MiB/object response PASS. Không stub permission/Gemini thành công để lấy PASS; session DB changes rollback. Lần fixture CSRF đầu thu hồi BE staging session đã ghi trong checkpoint và sửa rollback.

Final deep bridge/native route/receipt replay/privacy/snapshot/cron/ERB PASS; native source integration và parent-lock concurrency PASS; gate-policy42valid/42wrong-role edges PASS;329SourceIDs/106AC PASS cả sau cleanup cuối;5fake roles native/REST/MCP và final main SDKHTTP/stdio23tools/analyze329/anonymous401 PASS. Initial5rolecount test failed do overlap330, rerun clean329 PASS.66Windows units PASS/0skip.

Actual BE/TOTP browser final PASS: identity đúng8/BE, JSON sai không500, provider expired fail-closed có giải thích, create preview không ghi trước confirm, create/update/confirm/readback đúngfixture383/lockVersion1/ai_gateway, self-approval bị chặn/approvals0, Insights otherQA denied/selfBE insufficient mở được. Exact383 đã dọn,329nguồn/106AC giữ; screenshots artifacts/AI-UI-receipt-20261013-1745.png và expired/preview/gate-denied. Test automation này không independent reviewer/deploy approval;5real users, fresh fullqualification/official-upgrade/live release chưa chạy. Gemini OFF expired, bugfix Google calls0, counter4/14 giữ nguyên; previous Google smoke là lịch sử không phải fresh final.

UI startup tiếp theo: native route regression RED missingQldapmAIController → GREEN sau controller/explicit OpenProject inflection; class-only candidate FAILboot nên không dùng. Final core7b1b6f90… healthy, forkd225d3fc… clean. Deep stage bridge/ERB/privacy/receipt +66units PASS. Hostname staging8091 guard PASS sau phát hiện registration redirect sai8088. Browser onboarding người dùng đang xác nhận TOTP, chưa browser AI UI PASS; không xóa pending devices hoặc đổi live.

Final UI update: user tự xác nhận TOTP/password BE, actual browser AI Assistant/runb7f292c9… doneQLDAPM_OK và Insights self BE8/insufficient PASS. Screenshots artifacts/ lưu không secret; không Google call mới. Native authorization500 → HTTP anonymous regression RED→GREEN302 đúng8091/login cho AI/Insights/gates, native permission check thay vì skip. Final coreef4d6831…/fork2ce95aa8…; deep stage route/bridge/receipt/ERB/privacy rerun PASS,329 giữ nguyên. Chưa fullqualification lại/newcore upgrade/real5users/Codex/live cutover; pending devices không xóa. Đoạn7b1b6f90… phía trên là giai đoạn giữa, không final image.

| Kiểm tra | Kết quả thực |
|---|---|
| Qualificationc23cabff… | PASS28checks ở lượt12/10; signature valid và candidate unchanged xác minh13/10. Proof24h hết hạn, không rollout bằng proof cũ |
| Paired Docker586050dd… | PASS actual success và injected capability failure/rollback, backup/restore/state selection/fencing; test containers/networks removed, volumes retained. Core schema candidate có sẵn, chưa official→candidate binary upgrade |
| Fresh units | 66Windows PASS/0skip ngày13/10; không sửa source/harness lượt này |
| Google console/key | Đúng lostuinme@gmail.com/gen-lang-client-0020540057; existing key masked1f4g khớp; API Keys Free/Billing No account/Cloud Console not linked; không tạo key/bật billing/acceptToS |
| Fresh quota | Google5RPM/250000inputTPM/20RPD; giữ local3/175000/14. Usage displayed là peak28days, không remaining today |
| Verification provenance | Assistant observed official UI và chạy helper theo user authorization; documentary export private. Không independent human review hoặc automatic billing verification; không reset usage |
| Direct Google smoke | PASS thật countTokens+generateContent/fixed QLDAPM_OK/tools0,1probe; enable staging cùng proof/key |
| Gateway integration Google | PASS `tests.stage_free_smoke --real`:1probe thật qua REST run/poll, replay cùng run, MCP HTTP/stdio initialize/list23/read run, anonymous401. Tổng2probes/4reservations lượt này |
| Actual Free data boundary | PASS REST/MCP project fixture bị GEMINI_FREE_DATA_SCOPE_DENIED; invalidBearer401/forgedHost403. One-off initial assertion dùng sai tên error, runner sửa theo contract rồi PASS; không app patch hoặc Google outbound ở rejected prompts |
| Provider runtime | ON_SMOKE_ONLY, read-only proof mount, Linux count4/14/circuit false, expiry13/10/2026 13:26:11 Asia/Bangkok → fail-closed. Không general-tool/project/personnel Google nghiệm thu |
| Live readback | GET-only329/identity PASS, web/core2beeecac… và gateway7190… healthy/images giữ nguyên; không live cutover hoặc Jira action |
| Còn thiếu | Fresh rollout proof, official→candidate upgrade rehearsal, BE/FE/QA credential/onboarding, người thật TOTP/Codex, operator-approved live cutover và general-data policy |

## Lịch sử staging/AI controls — 2026-10-11

Lịch sử12/10: qualification18363824… FAIL gateway health trong maintenance, không seal. Test HTTP maintenance RED→GREEN và66Windows units PASS/0skip; gateway staging mới1cd1687b…; qualificationc23cabff… sau đó PASS28checks/sealed, đọc expiry hiện hành phía trên.

| Kiểm tra | Kết quả thực |
|---|---|
| Units candidate216b1920… | 65Windows PASS/0skip; Docker65discovered PASS/2OS-specific skip, no-network |
| REST/MCP Free data boundary | RED→GREEN: private/project prompt từ chối trước create run/idempotency, no outbound; không phải arbitrary PII scrubber |
| Structured conclusions | RED→GREEN fixture: scalar/source path/index/type phải khớp, hash source; prose/fake pass/citation/forbidden ranking bị chặn; general-tool Google chưa chạy |
| Whole-run deadline | RED→GREEN REST polling/replay failed_or_unknown; OS process kill thật PASS Windows/Linux, không late write; no automatic retry |
| Main staging transport | PASS real SDK HTTP/stdio, initialize/list23/analyze329/BE identity/anonymous401 |
| Resume main transport TTL | RED401 với synthetic BE token hết hạn24h; cấp token fixture mới qua Linux/native role check → SDK HTTP/stdio PASS, không sửa token thật hoặc tăng TTL |
| Full backup → source comparison | RED trên staging fake vì mode fingerprints lệch; GREEN shared verifier full/source SHA riêng, Subject mutation bị chặn/gate-only cho phép; không bỏ các bảng AI đã có, transaction rollback |
| Native UI/core bridge | PASS signed core→gateway native identity + ERB/privacy/snapshot/provenance fixtures; browser/TOTP người thật chưa chạy |
| Local operator | PASS Linux/private stdin + native BE/QA giả, preview/code confirm/wrong actor/replay; workspace tạm |
| Google official console | Fresh no-billing cùng account/project; fresh Rate Limit unavailable; historical Free/quota không thay thế fresh proof |
| Actual Google smoke | KHÔNG CHẠY lượt này: proof hết hạn, rolling14/14/circuit latched; Gemini OFF, calls0 |
| Qualification/sandbox | First qualification FAIL fixture operator identity UID1000; minimal Docker RED→GREEN, sandbox3suite rerun PASS; chưa seal mới |
| Paired release rehearsal | Sau fix maintenance health, UUID586050dd… PASS success và failure/rollback với private fake DB/assets/credentials; chưa official-to-candidate binary upgrade |
| Resume qualification18363824… | FAIL maintenance gateway health, không seal; bf0ae9f5… trước fix fingerprint FAIL. Qualificationc23cabff… sau đó PASS28checks, nay expired |
| Isolation incident/recovery | Rehearsal setup đã stop/detach DB/cache live do project substitution thiếu. Chưa restore/migrate; original image/volume/network/aliases restored, native329/identity PASS. New UUID/stop-label guard và production-project rejection self-check; không được ghi production unchanged |

## Lịch sử — Single-OS broker state — 2026-10-11

| Kiểm tra | Kết quả thực |
|---|---|
| Old cross-OS path | Reproduction FAIL đúng disk I/O trên SQLite giả; Linux-only control PASS; không chạy probe trên runtime dự án |
| Final candidate units | 60Windows PASS/0skip; Docker final image60discovered PASS/2OS-specific skip |
| Queue/container boundary | PASS real temp process Linux: inspect/claim/finish/audit/revoke/Unicode, queue consistency sau host requests, offline one-shot sau Stop; không HTTP/main gateway restart |
| Local operator/native core | PASS BE/QA giả: issue token/fresh role, wrong role reject, preview/code confirm, wrong actor/replay reject. Chỉ workspace tạm; source329 không bị ghi |
| Failure/security | PASS atomic claim, unknown quarantine, persisted signed receipt khi queue lost, local reconciliation/running-without-receipt reject, wrong mount/timeout/no fallback, maintenance deny, offline token/job execution deny, no arbitrary SQL/credential read/extra fields |
| Release fixture/Manager | PASS5branches + persistent mounts; Manager PS parse PASS |
| Promotion/qualification/live | Chưa chạy; new gateway image1931b53f… chỉ build/test. Main stage gateway cũ exited, production unchanged; old qualification không dùng |

## Lượt tiếp tục ngoài Gemini — 2026-10-11

| Kiểm tra đã chạy | Kết quả/phạm vi |
|---|---|
| Python unit | 54tests Windows PASS/0skip; Docker offline PASS (54discovered/2OS-specific skip); HTTP Google trong test là MockTransport, không request thật |
| Release orchestration fixture | PASS success/migration failure/gateway verification failure/shared signing key/reopening failure; snapshot/rollback/config/pair pin/maintenance/tunnel freeze; sau khả năng mở ghi không rollback mất state mới. Stub Docker/backup, chưa rehearsal Docker |
| Persistent Compose + backup lease | PASS manager/release dùng ui-bridge.yml, temporary restore không mount key live; active lease không copy; PowerShell parse PASS |
| Gate Ruby offline | PASS42valid edges/42wrong-role edges; reviewer/branch/self-approval |
| Insights/receipt Ruby offline | PASS windows/attribution/no-ranking; receipt signature/scope/revision/snapshot; signed gateway infrastructure receipt bị từ chối |
| Native candidate staging | PASS integration/bulk/hierarchy/self-approval/replay; concurrency closed-parent;329SourceID/106AC preserved |
| API5role giả | PASS REST/MCP ASGI identity/read/gate và native API shortcuts422; không real5user/TOTP/network SDK lượt này |
| Staging write contract | PASS proposal/signed UI confirm/create replay/Source immutable+unique/self-approval/stale409/independent reviewer/test pass-fail/revision invalidation/native mutation receipt; fixture378 đã dọn,329nguồn còn nguyên |
| Sandbox signed receipt | PASS3suite thực trong Docker; clonedDB/internal network/nonroot/read-only/resources/noInternet. Broker ký gate-policy/core-integration receipt → native GateActions chấp nhận/automatic snapshot → transaction rollback giữ nguồn; gateway suite không ký ticket evidence. Chưa full broker queue lifecycle |
| Restore candidate mới | PASS33tables/assets/config hashes trên volume fake riêng17ccb077…; temporary stack dừng/volume+backup giữ; stage core healthy sau restore. Không live backup/restore |
| Full pair bridge/qualification/Docker release | CHƯA CHẠY; staging gateway bị chặn khởi động qua tool, candidate core đã nâng riêng |
| Production/Gemini/Jira | Không rollout/call/mutation; Gemini OFF |

Candidate digests/commit và blockers ở đầu `CHECKPOINT.md`. Các kết quả phía dưới là lịch sử.

## Deep AI — lượt hiện hành

**Resume Docker 2026-10-11:** core/db staging restart healthy; expired Freeproof fail-closed/OFF PASS, không Google retry, localusage10/14 không reset. `tests.stage_transport --remote` PASS: temporary synthetic BE gateway candidate5d5c968b…, anonymousHTTPS401, real SDK MCP HTTP initialize/list23tools/analyze329, stdio remote identityBE. Temporary gateway/tunnel stopped; main stage gateway stopped for local verification. Không gửi Google dữ liệu nguồn; Gemini remote thật/browser/TOTP/release chưa chạy,48unit phía dưới là lịch sử không rerun lượt resume.

**Restart anomaly và recovery:** host Windows SQLite inspection khi Linux gateway dùng cùng bind mount gây500/disk I/O; lượt đó FAIL. Restart gateway và chỉ đọc HTTP/SQLite trong Linux: identity200, AIrunQLDAPM_OK, counter10/14 PASS. Chưa giải quyết tận gốc cross-OS WAL; không dùng host SQLite helper khi staging gateway đang chạy, không xóa/reset dữ liệu để retry.

**Five-role native/REST/MCP rerun:** `tests.stage_api` PASS cho5danh tính staging giả lập (BA-PM/PM/BE/FE/QA),329visible mỗi role, DONEshortcut422, non-PMconfiguration403. Sau restart gateway: AIrun vẫn đọcQLDAPM_OK, rolling24hcounter10/14 giữ nguyên, không outbound thêm. Chưa nghiệm thu5người thật/TOTP; không thay roleBA live.

**Docker/Free integration 2026-10-11:** rerun48unit PASS; gateway staging build/deploy digest5d5c968b… với readonly Free proof RW=false. Real REST synthetic BE fixed-smoke PASS, replay cùngrunID; SDK MCP HTTP/stdio initialize+23tools+đọc cùngQLDAPM_OK PASS, anonymous401. Một real probe/hai local reservations, rolling24h10/14, không ticket/code/nhân sự/tools gửi Google. Restart gateway health/BE identity PASS; live image unchanged. Remote HTTPS/browser/TOTP/full release **CHƯA CHẠY**. Các mục DockerOFF bên dưới là lịch sử.

**Kết quả mới nhất 2026-10-11:** real Google fixed-text smoke PASS (countTokens + generateContent, `QLDAPM_OK`); local enable/status PASS, `ON_SMOKE_ONLY`, quota5/250000/20 và limits3/175000/14. Chỉ synthetic data; manual Free/no-billing proof không phải automated billing verification. Docker daemon OFF: container gateway rebuild, readonly proof override và real Gemini REST/MCP integration **CHƯA CHẠY**. Không production/Jira mutation. 48unit PASS bên dưới là lượt trước, không rerun unit suite trong lượt real smoke này.

**Enrollment root cause11/10:**48unit PASS gồm reject1ký tự/no overwrite, hidden replacement không lấy env và invalidates proof. Local credential metadata thực tế length1; user smokeHTTP400/countTokens FAIL. Chưa full key nhập lại hoặc Google API PASS; provider OFF, không real retry/deploy.

**Kết quả cuối lượt diagnostic:**45unit PASS, gồm status báo quota/manual Free/circuit khi OFF và kiểm tra không outbound. REST/MCP fixture đã đồng bộ hoàn tất audit trước cleanup (khắc phục WinError32 của hai lượt trung gian). Provider vẫn OFF; không real retry hoặc thay production.

**Cập nhật smoke11/10:**44unit PASS sau regression diagnostic HTTP/phase/status/reason và chống lộ upstream message/metadata. Operator đã thực hiện Google smoke thật nhưng FAIL tại countTokens; Gemini OFF, circuit giữ nguyên. Manual proof ghi Free/no-billing, quota5RPM/250000inputTPM/20RPD (local3/175000/14); không tự xác minh billing qua Google. Chưa real generateContent PASS, chưa enable/rebuild image staging/promotion. Các kết quả bên dưới trước cập nhật này là lịch sử.

Lượt2026-10-11 Free-only: 41unit PASS; native synthetic5roles/329/REST/MCP initialize/gate deny PASS chạy lại; Docker staging image `f9e802c0…` health/identity/OFF503/anonymous401 PASS. Production image không đổi. Google key/project Free/quota UNKNOWN, API thật **CHƯA CHẠY**; provider OFF. Proof readonly override/rekey/remote Gemini thật **CHƯA CHẠY**, không tự dùng fixture làm chứng minh tier. `GEMINI_FREE_TIER.md` ghi quy trình manual official-console verification và fixed-smoke data scope.

| Phạm vi | Kết quả thực | Giới hạn |
|---|---|---|
| Windows unit | 41PASS | Thêm7Free budget/auth/data-scope/enrollment/REST-MCP polling fixture; không API Gemini thật |
| Human confirmation | REST và MCP chỉ proposal; UI signed confirm/replay/expiry/wrong actor/stale code PASS | Không có tool machine tự confirm; chưa browser người thật |
| Native core UI/Insights | Render ERB/session-route implementation; PM/self privacy, snapshot replay/response, cron timezone, HMAC bridge PASS | Render/runner không chứng minh login/TOTP/CSRF browser E2E |
| Metrics | Windows, first failure/prior-window failure, role/actor, stable-assignee cycle/handoff, missing data/no rank PASS | Chưa đủ baseline commitment/blocker/time-entry/verified bug/complexity |
| Native atomic receipt | API update receipt/provenance và runner Unicode/replay/rollback/journal AI attribution PASS | Create timeout chưa có actor-bound receipt: UNKNOWN/manual reconcile; Source ID collision trả409 |
| Concurrency | Hai code confirmations cùng base: chỉ một ghi; parent REVIEW khóa child trước commit PASS | Chưa mọi tổ hợp bulk/move/reopen/race |
| Test attestation | Python signer/Ruby verifier/synthetic native gate PASS; giả/sai scope/revision/snapshot/result bị từ chối | Chưa full job runner→API evidence end-to-end thật; automatic smoke bị từ chối |
| Native/REST/MCP | 5role giả/329/shortcut denial PASS, schema2 write12groupsPASS/cleanup329 | Vẫn cần qualification mới khóa cả gateway/core |
| SDK remote | HTTPS HTTP+stdio candidate PASS, anonymous401; tunnel test dừng | Không Codex host thật/năm member credential thật |
| Restore | 33tables + attachments + config PASS trên core31f5e9c3…/schema2 cuối | Evidence6b28d71c…; volume restore riêng giữ lại, không live restore/cutover rehearsal |
| Live GET-only | 19PM/20BA,329native type/SourceID/parent/assignee/description/106AC PASS; login200; official/live gateway images giữ nguyên | Không full login/TOTP hoặc live gate write acceptance |
| Response/restore safety | Native streaming8MiB/deadline, transport audit và restore content manifest approval hash implemented; fixturePASS | Không hard global wall-clock/saturation/slowloris E2E guarantee |
| Gemini Free | Fixed harmless probe/no tools; 401/403/404/429/timeout/no paid fallback; atomic shared-project RPM/TPM/RPD persistence fixturePASS; providerOFF | Actual project/tier/quota/key/real smoke chưa xác minh; full project/personnel prompts bị chặn, không dùng attestation/counters làm bảo đảm tài chính |
| Gemini tool/narrative contract | Thought signatures/IDs vẫn PASS offline fixture only | Không bật trên Free; final source validator/sensitive-data filtering chưa hoàn tất |

Chưa qualification/seal/cutover bản này. Cần coupling promotion core/gateway + readonly keys/persistent override, rehearsal release/rollback, Gemini cost/data verification+fresh key, five identities/Codex host/browser và resource/concurrency matrix. Các dòng qualification schema1 bên dưới là lịch sử, không dùng làm release proof cho deep AI.

Đọc `CHECKPOINT.md` để lấy image và trạng thái hiện hành. Các bảng phía dưới là lịch sử, không phải proof/URL cho deep AI candidate. PASS chỉ áp dụng phạm vi đã chạy; không phải nghiệm thu toàn bộ kế hoạch. Staging/sandbox dùng danh tính và database giả, không credential/TOTP production.

| Phạm vi | Kết quả đã quan sát | Bằng chứng / giới hạn |
|---|---|---|
| Unit/auth/workspace/broker | 19 test PASS trên Windows | `unittest discover`; expiry/revoke, redirect, role audit, path/hash, proof giả, UNKNOWN quarantine và queue test/replay |
| Migration | 329 mục/106 AC giữ nguyên; checklist ban đầu unchecked; Subtask 7 trạng thái | Qualification `migration.log`, `release_verify.log`; không đổi trạng thái live |
| Native/bulk/hierarchy | PASS tại đường ghi chung; `save(validate:false)` không bypass | `integration.log`; bao gồm self-approval, contributor, revision, receipt và closed parent |
| Delete | Approval riêng chưa đủ khi cha REVIEW/DONE | Regression `integration.log`; operator phải mở cha trước |
| Concurrency | Race parent REVIEW với child write bị chặn trước commit | `concurrency.log`; chưa phải thử mọi tổ hợp move/bulk/race |
| Workflow policy | 42 edge hợp lệ và 42 wrong-role PASS | `policy.log`; latest failed evidence, scope, reviewer, reason/reference; không chứng minh chất lượng evidence |
| Native API + REST/MCP staging | 5 role PASS; đọc329, native shortcut bị chặn | `api.log`; không phải 5 credential production |
| Write/replay | 11 nhóm regression PASS, fixture được dọn về329 | `write.log`, `cleanup.log`; update/transition timeout chưa có journal tự reconcile |
| Backup lease | Tái hiện lỗi copy file lease đang mở, PASS sau loại trừ | `backup_lease.log`; fixture chạy pipeline Copy thật, không gọi backup live |
| Source comparison | Gate-only được chấp nhận; sửa source bị phát hiện; rollback giữ nguồn | `source_comparison.log`; fingerprint28bảng trên dữ liệu giả |
| Admin | Preview/before-hash/user lock/rollback PASS | `admin.log`; reset/roles/workflow/fields/settings/delete admin còn cần nghiệm thu riêng |
| PM/BA thật | Local REST/MCP/OpenAPI/19tools/329 và business writes503 PASS | `tests.live_read`; giữ token19/20; không đổi password/TOTP |
| PM test job thật | Job trên workspace21 PASS, đúng actor20; queue mới0,28s | `tests.live_job`; không giả danh BE; code version được chụp khi broker bắt đầu |
| PowerShell stdio wrapper | PM20 local và remote initialize/19tools/identity/analyze PASS | `tests.client_wrapper [--remote]`; SDK không phải Codex host thật |
| Sandbox immutable | Gate-policy, gateway và core-integration PASS | Qualification `sandbox.log`; actor workspace21, database clone giả, no Internet/live secret/socket, container/network test được dọn |
| Restore candidate | 28 bảng + synthetic attachment + config PASS | Lượt80fcbf59, restore4c74dc3d-ef18-42fa-8be7-0fbdbc091fae; đúng core image86fee541…, giữ isolated volumes; không restore production |
| HTTPS SDK trên mạng mới | HTTP + stdio staging PASS, anonymous401 | `tests.stage_transport --remote`; URL test đã dừng sau kiểm tra |
| Qualification hoàn chỉnh | 16 check PASS; HMAC/current candidate/restore verify PASS | db3e420e-ac22-4acd-b528-86b141dd87cb, proof24h; không là deploy approval |
| Restore cuối + readiness | 28bảng/assets/config PASS trên đúng image; web healthy trước transport | Restore da249129-4465-405b-8ebd-71db123920bd; isolated volumes retained |
| Gateway remote với người thật | BA-PM19/PM20 REST/OpenAPI/MCP19tools/329 PASS, writes503 | `tests.live_read --remote`; anonymous401, không native live mutation; URL ở checkpoint |

Đọc checkpoint để lấy proof/URL hiện hành. Lượt80fcbf59 fail MCP remote ngay sau web restart; healthy rồi test remote PASS lại. Sau readiness fix, db3e420e đã chạy đủ và seal proof; không seal từ lượt thất bại.

## Chưa nghiệm thu đầy đủ

- BE21/FE22/QA23 thật; UI đổi password/TOTP và WebSocket qua URL mới; Codex host thật.
- Glue cutover/rollback live hoặc rehearsal đầy đủ của chính glue; full-core build ngoài overlay.
- Mọi admin branch, resource exhaustion, toàn bộ host/origin/payload/rate-limit/permission matrix qua REST và MCP. Audit business action/job có sẵn; chưa chứng minh mọi request transport/metadata đều được ghi audit.
- Native response được giới hạn sau buffering; chưa thử upstream trả response cực lớn. Thời gian xử lý ngoài native call và body không có deadline tổng quát.
- Restore proposal chưa khóa manifest nội dung backup bằng approval hash. Move giữa project vẫn fail-closed, chưa có đường approved broker.

Không release chỉ vì unit/staging xanh. Operator phải xem các giới hạn trên, hoàn tất kiểm tra còn thiếu phù hợp rủi ro và duyệt đúng thay đổi local; giữ original image/volumes/backup.

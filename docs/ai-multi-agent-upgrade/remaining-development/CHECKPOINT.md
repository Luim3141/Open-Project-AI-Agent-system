<!-- CURRENT_DEPLOYMENT -->
# Đã triển khai Staging và kiểm tra phục hồi — 2026-10-18T21:50:12.893792+07:00

**STAGING_DEPLOYED_VERIFIED**, Gateway6afb78c4/Core3b09393d; owner đã duyệt hash265ab363… và app-only apply hoàn tất. Sau mất điện do owner báo, 18 container tự phục hồi đúng ID/image, không reapply hoặc chạy lại job. Không còn active/unknown job; SQLite quick_check PASS; manifest/image-lock/key khớp. Đọc remaining-development/STAGING_DEPLOYMENT_REPORT.md và deployment-summary.json trước lịch sử bên dưới.

5 tài khoản thật login/TOTP/Assistant/Control Center/Second Brain PASS qua HTTPS; 5 lượt Supervisor thực qua Rails bridge có plan/trace/model_used=false.35Gateway+7Core hash PASS;372WP và RBAC/credentials/device secrets giữ nguyên, chỉ access/session metadata đổi sau login. Ledger471 không tăng; old receipts/docs giữ nguyên. Backup mới trước/sau và 3SQLite cold restore PASS.520Windows/30Linux/64clonebrowser/13CC là bằng chứng qualification trước, không phải chạy lại sau mất điện.

Không promote Main, không đổi CSDLDPT, không migration hoặc Native fixture writes. Không rotate TOTP; G2 BLOCKED_OWNER_VERIFICATION và20-user DEFERRED_BY_OWNER. Gemini policy/key tự đọc lại từ private config, không cần nhập lại. Quick Tunnel URL có thể đổi sau restart; lấy link tại http://localhost:18090. Clone qualification vẫn stopped; không dùng synthetic credentials cho serving.113task objects nguyên vẹn. **Không chạy lại provision chỉ vì tài liệu lịch sử bên dưới ghi chưa deploy.**
<!-- END_CURRENT_DEPLOYMENT -->

# Remaining development checkpoint

Updated: 2026-10-18T15:54:17.152164+07:00

- Serving Main/Staging Core/Gateway containers unchanged; no real account/TOTP/RBAC change, no public restart/fault. TOTP NOT_APPROVED_DO_NOT_ROTATE, G2 BLOCKED_OWNER_VERIFICATION,20-user DEFERRED_BY_OWNER.
- RD01 reviewed42 mismatches;7 dev/prototype modules excluded from image. Source before snapshots retained. Source-runtime matrix/review notes saved; candidate parity/complete regression still pending.
- Source wired local Supervisor into existing queue/isolated worker/AgentTask/AgentRun/audit with zero provider calls and cooperative cancellation. Scoped native-ID knowledge API, real FTS5, WAL/chunks/update/native ACL+version, corruption/backup fixes. UI Core controller/partials built.
- Candidate Gateway v2 a992fb05, Core f0da1eb6, Quick Tunnel eb4cb5b6 built; v1 metadata retained. New connection-close-on-corruption fix has9focused PASS but requires next Gateway build before final qualification.
-72focused contract/regression PASS and latest9security/persistence tests PASS. Initial broad511tests recorded7failures+15errors; obsolete unsafe demo/style fixtures replaced, real errors fixed; full rerun still required. MockTransport Google URLs are not live calls.
- RD05 VERIFIED: live/rebuilt Quick Tunnel identicalRootFS/entrypoint/binary/script,2026.10.0. Saved manifest corrected metadata-only from vendor binary image to actual a80f54e2; private backup retained. Operator status EXIT0/allhealthy; live container/start/restart unchanged. Source Compose default pinned and provision preserves saved image.
- Isolated qualification: private operator/remaining-qualification-20261018. PG restored Staging backup into new DB;5NEW synthetic users (13PM,14BA-PM,24BE,25FE,26QA), their own new fixtureTOTP only. Existing copied identities untouched; no serving identity changes. Work Package must be created through real canonical UI, not directAR.
- Clone names qldapm-rd-db/core/gateway-20261018, network qldapm-rd-20261018 internal + owned loopback bridge10.254.236.0/28. Existing default address pools exhausted; existing networks preserved. Ports localhost18095/Core18096/Gateway health200. Native identities all5HTTP200 and optionsAPI200; no provider key copied. Gateway fixture config now includes only copied non-secret Native source_field/type_ids/status_ids plus synthetic users; only clone Gateway restarted.
- Running actual browser UAT script remaining_browser_uat.py (session20931); PM login/TOTP + Control Center already PASS, additional cases pending. Read newest browser-uat-*.json; all credential/browser failure contents are private. Do not log passwords/OTP/API keys or raw exceptions.

Next: finish actual browser UAT and fix failures; build Gateway with latest source, verify module hashes/import/HTTP/real worker/SQLite+restart+restore/RBAC/n8n, complete broad regression/Playwright. Build helper qualify_remaining.py has --resume; never run prepare again over existing private directory, never blindly restart serving services. Recheck it before use: source network-creation path still needs explicit nonoverlapping-subnet fallback for full rerun reproducibility. Update remaining reports/UATCSV/backlog. Any serving deployment/fixture mutation there requires exact final approval after reviewable qualification.

## Resume milestone 2026-10-18 16:15+07
- Gateway candidate v3 f46ca63e/source be02fca8:42-module parity PASS (35packaged,7excluded),8critical imports PASS; Linux26tests PASS. Windows514tests PASS,14backup tests PASS after adding actual Second Brain FTS/chunk snapshot regression.
- Fixed null Native assignee href/title in PM/sprint helpers; source dashboard with null fixture PASS. Second Brain backup added optional knowledge.sqlite to existing local_backup.py (running operator already loaded old source; requires approved operator restart/deploy to activate).
- Actual browser first56checks45PASS/11FAIL. v3 retry PM worker PASS but UI result fetch503/timeouts; diagnosed Rails2-thread reentrant bridge deadlock when meta-refresh/manual loads overlap. CloneCore refreshed to8threads/pool9 (booting); servingStage also2threads, sourceCompose change and5-user qualification pending.
- Corrected qualification helper: never open Docker bind SQLite/WAL on Windows. Host pre-refresh check caused clone disk I/O startup failure; old files retained, clean clone restarthealth200, in-container busy check now used. No serving impact.
- Current isolated names/private credentials unchanged; no Google key/call. Browser interrupted consciously after diagnosing low-thread capacity; evidence retained. Next waitcloneCorehealth, rerun actual5-role browser, native/security/knowledge restart/restore/concurrency/n8n and complete reports.

## Latest 2026-10-18 16:43+07
- Final Gateway16d40bc6/source d6d035b1, Core5865533c/source45945993. Native business mode now denies5 sandbox/operator actions at REST/perform/MCP catalog; strict sandbox preserved. New MCP tests PASS.
- Core candidate fixes upstream invalid status→nil.default_done_ratio500 by deferring nil status to Native contract: actual same PATCH now422, no Native lockVersion change;BEdirectPATCH403. Ruby3assertions PASS. Core overlay adds no migration.
- Windows517tests PASS (regression-qualified.json), Linux28tests PASS,35securitycontracts PASS,42module hashparity/35imports PASS. Updated old Level2 denial-reason expectation only for newly required Native operator fence; no-write assertions retained.
- v3 full actual browser64PASS; API29PASS including5realworkers/comments5roles, proposalcrossactor/hash/replay/stale, actor/projectknowledgeACL includingreal actor belonging2projects,physicalbackup5docs/chunks5,Gatewayrestartpersistence/zeroGemini. Final-imageAPI12PASS includingoperatorcatalog,Native403/422,HMACreplay,5realworkers.
-5concurrent final-image browsers allPASS but49–57seconds for full result+dashboard. Core586 now skips duplicate dashboard/report panels on result/proposal pages while keepingfreshNativeACL+ControlCenter. New concurrent measurement running; then repeat64UI checks on finalCore/Gateway.
- Coldbackupverifier accepts knowledge.sqlite and realFTS/chunks logicalhash restore PASS on isolated syntheticLinuxfixture/networknone. Full routine servingStage backup currently running (read-only inputs/newprivate output,no restart); checkpredeployment-backup.json.
- Next finishfinalUI,actual restoredGateway/oldGatewaycopyrollback,n8n final-image replay,resource/security/sourcebundle/docs/CSV/handoff. NoMainDB/accounts/TOTP/RBAC/publictunnelchanges. G2ownerblocked/TOTPnotapproved/20usersdeferred. Never open liveDockerSQLite/WAL fromWindows.

## 2026-10-18T17:29:47.845718+07:00 — Frozen source qualification
- Current Gateway6afb78c4/source042a7cd7;Core3b09393d/sourcec278ffb0. Source frozen after pagination10 and reviewer/provenance fix.520Windows PASS(final-frozen-regression.json),30Linux PASS(linux-frozen-qualified.log),42/35imports+7Corehash PASS.64browser PASS:browser-uat-1792318734.json, immutable screenshots in matching-assets directory.
- Control Center original404CSRF was harness wrongroute; correct observed form/commands gives422. Other12CCcases pass includingrealqueuedcancel/noNativechange. Consolidated control-center-final-qualified.json keeps provenance to original+csrf-qualified.json; failures not deleted.
- Restored current candidate search5roles,old006Gateway reads/history/schema72runs PASS;noCorepairboot claim. RealStagefullbackup2c707...+3SQLite/Native221fingerprints372WP restored.2legacyPGknowledge tables empty;runtimeSQLite4oldrows preserved.
- Source provision nowhas --application-only;21tests+read-onlyComposerender/lineage PASS; only2appservices up and existingbackupwatcherreload. No actual serving apply.
- Remaining: current5concurrent browser+n8n probes running; generate finalCSV/reports/backlog/preview hash/privateSourcebundle, finalserving snapshot and checkpoint. Deployment owner approval required; no further product changes expected.

## FINAL 2026-10-18T17:37:05.130967+07:00
- RD01..RD06 VERIFIED theo qualification; serving deploy BLOCKED_OWNER_APPROVAL. Current Gateway6afb78c4/Core3b09393d; phase5actuala80 retained.520Windows/30Linux/64roleUI/13CC+CSRF/5concurrentcurrentoutputs PASS, currentcandidate rollback/restore8cases PASS. Actualn8ncurrentstatus/model0 PASS.
- Source/pinnedimagehashproof, private before/qualifiedsource ZIP/source-bundle.json, UAT_TEST_RESULTS.csv,9newreports+backlog+sourceReview+preview ready. Original113task objects unchanged. Nativefork notedited; noGitreset/push/merge.
- serving-final.json proves comparedservingcontainersunchanged; data/keys/TOTP/RBAC/Main/publictunnel notmodified. RealStagefullbackup2c707... coldrestoresNative221fingerprints/372WP and3SQLite verified. Existing4knowledge docs preserved.
- Owner action: approve deployment-approval-plan.json hash265ab363875b7ec0610e4ec90fb945382630356118ae46331e46c48609b3020f, then guarded --application-only rollout only2appservices+existingbackupwatcher; freshbackup/preflight again. NoNativebusinesswrites/realTOTP/G2smoke/publicrestart/Mainpromotion authorized.
- Knownlimits: Coreoldpairnotboot-tested, NativepreauthHALError, escapedMarkdownformatting. G2ownerblocked/20userdeferred/TOTPnotapproved. Never open DockerliveWAL viaWindows.


## DEPLOYED / POWER RECOVERY — 2026-10-18T21:50:12.893792+07:00

Owner approval exact265ab363… received; app-only Core3b09393d/Gateway6afb78c4 applied21:29:46+07, backup watcher reloaded. Owner later reported power loss:18servingcontainers recovered by Docker to same IDs/images; no additional apply/restart/cleanup. Finalhealthhealthy, noactivejobs, locksavailable, 35+7runtimehashmatch, key/config+FreeOnly/continuous policy persist.5realrolebrowserlogin/TOTP/UI PASS;5realroleSupervisor bridge tasks done/plan/trace/modelFalse. Old receipts90/proposals34/tokens50/knowledge4 preserved;5newlocalruns only; providerledger471 unchanged.372WP/business/RBAC/security projections preserved; login access timestamps/sessions naturally changed. Backups pre fe118729… / post 41081d60-67e8-4f4a-bd95-5e4061b4d0a5 and cold3SQLite restores PASS.

Resume: read STAGING_DEPLOYMENT_REPORT.md, deployment-summary.json and deployment-final-health.json. Do not rerun deployment or create synthetic serving fixtures. Main/G2liveGoogle/TOTP/publicfault/20users remain outside approved scope. Pending G2 owner verification; no Google call or further approval requested here. Original113tasks unchanged. Qualification clones stopped after power loss; their historical test results remain, no auto-start needed.

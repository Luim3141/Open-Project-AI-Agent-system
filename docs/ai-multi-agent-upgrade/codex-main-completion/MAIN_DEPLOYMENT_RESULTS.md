# Main app/config và Native views — kết quả hiện hành21/10/2026

**DEPLOYED_AND_MAIN_PM_UI_VERIFIED**, chưa đầy đủ product acceptance.

Mainweb/worker/cron hiệnCore `sha256:95da6c8eed2e9cae1bc023b7f29451433bec3e1c68480421be1c4629542ef53f`; Gateway456c38f6… không đổiimage. Exact-image clone Gantt5checks và NativeViews72checksPASS trước đợtCore deploy08:23. Main47/47overlaymatch,5NativeidentityPASS,15other servingcontainers giữidentity/image. Backup được dùng cho Coredeploy là03:00 đã restore/rehearsal; freshbackup08:25 sauCoredeploy được restore vàoNEWDB backup_verify_20261021_082559 và dùng trướcNativeconfig08:27. Phân biệt hai thời điểm này, không mô tả08:25 là trướcCoredeploy.

Nativeconfig thực thi qua PM19:query32,boards10..13,Versions5..8,31creationevents vàsecondapply9PRESERVED_EXISTING. Giữboard8/query29. Khôngmigrations/DBrestart/Stagepromotion/credentialrotation/Googlecalls trongphaseGantt. API/HMAC25checks vàactualOwnerUI Gantt/4Boards/Monitor drag/AutoLayout/Backlog/Sprints/Insights/GatesPASS theo phạm vi trongMAIN_FULL_BROWSER_UAT.md. Roadmap0card vìchưaWPVersionassignment; Main329datesNULL.

MinimalGoogle smoke đượcOwnerduyệt riêng trướcđó đãPASSQLDAPM_OK/2HTTP/24tokens; freshMainreadinessREADY. FullGeminiSupervisor preview mới chưa đượcduyệt,khônggộpphêduyệtoldsmoke. Main1localrun/14events/2ledgerreservations; Staging113AI/23agent/44receipts/517usagegiữnguyên.

Finalreadback09:06:8Mainprotectedtables giữfingerprint so08:25backup;18servingcontainers giữID/image so08:31 vàhealthy. TOTPdevice IDs/secret/config/active/default/ownershipkhôngđổi; riêngdevice2/user19 `last_used_at` tiếnlên doOwnerNative re-login. FullTOTPtablehash vìvậykhôngcònbằngbackup; đã kiểm từngfield qua digest để phânbiệt metadata dùngthật với rotation. `main-totp-usage-readback.json`, `main-final-uat-isolation-readback.json`.

Rollback ứngdụng dùngimmutableCore dde3c32e vàprivateenv/lockbackup; khôngwholeDBrestore/xóaNativeconfig. Clonepre-date dump đượcgiữ; Native dates chỉqualification trênclone vàkhớp329/343,khôngapplyMain. XemFINAL_OWNER_ACCEPTANCE.md cho phầncònchờ.

---

# Historical deployment report — đợt app/config02:12

# Main app/config deployment — 21 Oct 2026

Status: DEPLOYED_HEALTH_NATIVE_READBACK_PASS; authenticated browser UAT pending native Owner login. No claim of full product acceptance.

Main web/worker/cron now Core `sha256:dde3c32ee69af450a6316450ac076d502953610932627ee33ce948f20dfbe459`; Gateway remains `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`. Fixed controller/view context refresh and set Main gateway_mode=native. No migrations. Corrected stale Main image-lock fields to actual immutable images. Compose/provider overlay persists across Docker restarts and Main management Start.

Separately approved enrollment created exactly3nativeAPI tokens forBE/21,FE/22,QA/23; old tokens and credentials preserved. Installed same saved Gemini key/model/Free-only quotas with independent production proof and Main storage. No provider generation, countTokens, readiness probe or billing operation. Readiness remains unverified. No cached Staging readiness/history/usage copied.

Gates:19Windows+19Linux Gateway tests;6controller/31assertions;3actual Rails/view/37assertions;42valid+42wrong-role gate edges. Clone browser:24non-PM checks and14Monitor checks PASS, plus PM readonly checked-consent reproduction. Real native UI/HTTP is distinguished from synthetic model/Native fixtures in the JSON evidence. Clone has no real Gemini key.

Fresh backup backup-20261021-020744:221PGtable/sequence fingerprints restored exactly into a new clone database; SQLite cold integrity and archive hashesPASS. Old and candidate Core images both started on the owned clone, passed health/native identity; WP fingerprint unchanged. See fresh-backup-restore.json and rollback-rehearsal.json.

Post-apply: both Main serviceshealthy; native API identity/project/role verified for all5actors. All329WP rows, users, memberships, roles, role permissions and TOTP tables unchanged.14unrelated serving container IDs/images and protected Main/Stage credential/key files unchanged. No business/date/status/Sprint mutation or history import. Main providerusage/receipts/runs remain0, Stagingusage517/receipts44/runs preserved. Evidence: main-application-deployment.json, runtime-20261021-021442.json.

Main authenticated UI is BLOCKED_OWNER_LOGIN after the previous Edge session expired. Native login tab opened for Owner; no passwords/TOTP/cookies obtained or synthesized. Remaining Gantt/Boards/history/schedule/live-smoke phases continue independently. The system is not yet QLDAPM_MAIN_FULLY_OPERATIONAL.

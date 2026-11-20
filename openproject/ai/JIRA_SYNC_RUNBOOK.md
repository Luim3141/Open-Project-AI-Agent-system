# Jira → OpenProject one-time sync: implementation checkpoint

## Current power-loss recovery

Resume14/10 09:25+07: fresh source fields still match snapshot8edc9e79…, both qualified full backup proofs validate and both primary instances remain329NEW with zero local apply approval receipts.92Windows units PASS. Table/commands below now use NEW immutable previews; old02:32/02:39previews expired. No data/config writes occurred. Local human must approve staging first, inspect independent readback/no conflict/UNKNOWN, then approve live separately. Gemini remainsOFF and source/runtime credentials unchanged.

### Final14/10 — qualification complete, primary apply pending

Both full native rehearsals **PASS**: restore database/all tables+sequences/assets/config, fixed scoped configuration,329content records+2comments+265Simulation time entries, independent readback and replay329without duplicates. Live retains243status differences; staging blocks242and permits1matching transition.89Windows units/23sync tests and image policy42valid+42wrong-role cases PASS. Native stage directDone is denied and imported simulation excluded from Insights. All owned clone resources cleaned; backups/failed receipts retained.

Staging web now runs tested `sha256:8ae2b3513fbc7845c9f2a9cabac2a1c280f189f2c179042a025eb028e8429b37`; installed Insights rollback regression PASS, health good. Gateway1cd… and live2bee…/7190… unchanged. Both primary instances remain329NEW with costs disabled, PM time permissions absent and no Simulation activity. **No primary sync has been applied.** Gemini config remainsOFF; no Google call. Fresh official Jira field re-read PASS after one read timeout/retry; apply must still recheck mutable children before writes.

Qualified previews under `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/jira-sync/2149a4d4-a3f2-4b6e-9642-5138c3c16663`:

| Target | Preview | Exact local approval hash | Expires +07 |
|---|---|---|---|
| Staging8091 | staging-preview-da3f3411-d93c-41cb-8fd1-88dcaf94a304.json |34d50f60a50369c9742c31432bcdbc56e07cc29ba446db8fa2875e98862fca1f|14/10 10:23:40|
| Live8088 | live-preview-8cdbf63f-7931-4c51-b2d7-3d65269a9372.json |b97e969ed477dbe6aeae6780055474b24bd2b1ff0687a61ca6624b317d018de9|14/10 10:21:16|

Human-only approval: inspect the private preview's `rows.before`, `rows.payload`, `rows.skipped`, configuration and backup proof, then run from a normal interactive PowerShell console. Scope: existing329tickets,2comments,265simulation logs; add bundled costs and ONLY two PM permissions with globally inactive/project-only Simulation. No native date writes: preserve344relations/date modes, retain exact Jira dates in source text. No native Gantt/status parity, no actual employee/product-completion claim.

```powershell
Set-Location -LiteralPath 'D:\AI project\QLDAPM chat\openproject\ai'
$syncDir = Join-Path $env:LOCALAPPDATA 'QLDAPM\openproject-ai\operator\jira-sync\2149a4d4-a3f2-4b6e-9642-5138c3c16663'
$stagePreview = Join-Path $syncDir 'staging-preview-da3f3411-d93c-41cb-8fd1-88dcaf94a304.json'
& '.\.venv\Scripts\python.exe' jira_sync.py apply --preview $stagePreview
if ($LASTEXITCODE -ne 0) { throw 'Dừng: xem receipt; không retry/restore tự động.' }
& '.\.venv\Scripts\python.exe' jira_sync.py verify --preview $stagePreview
```

Inspect the report: all329contents/2comments/265logs must read back, no conflict/UNKNOWN/unprocessed rows. Only after stage verification, approve live separately:

```powershell
$livePreview = Join-Path $syncDir 'live-preview-8cdbf63f-7931-4c51-b2d7-3d65269a9372.json'
& '.\.venv\Scripts\python.exe' jira_sync.py apply --preview $livePreview
if ($LASTEXITCODE -ne 0) { throw 'Dừng: xem receipt; không retry/restore tự động.' }
& '.\.venv\Scripts\python.exe' jira_sync.py verify --preview $livePreview
```

If a preview expired before approval, regenerate READ-ONLY preview with the SAME complete snapshot and qualified backup via the command below; inspect/type the NEW hash. Do not change timestamp/hash manually or regenerate an apply after partial writes (could nest source descriptions); reconcile receipts first. Do not run Setup/Stage/seeder or legacy Restore. Docker restart may use `docker start` on the three known existing stage containers; `.env`/image-lock remain older defaults, so do not use a default compose recreate to downgrade the tested stage image.

### Recovery/implementation history (superseded by final state above)

Latest14/10 dependency correction:89units/23sync PASS. Both primary instances have344local relations (343follows/1relates) touching318work packages. Even a manual predecessor date edit recalculates automatic successor versions; full trials caught conflicts and were rejected. Preserve these local-v7 relations/date modes: skip direct date writes for temporal relation endpoints as well as automatic parents, retain source dates in description, and check the native relation fingerprint before apply. This can leave native dates different/empty; it is an explicit non-equivalence, not synchronized Gantt parity. Switching all affected items to manual scheduling or removing dependencies is outside this approved sync and needs a separate plan/approval. New full trials are running; previous trial failure artifacts retained and disposable resources cleaned.

14/10 update:88full units PASS (22sync included). Full native trial exposed automatic parent date roll-up: initial parent PATCH saved descriptions but ignored direct dates. Preview now preserves `scheduleManually=false`, skips direct parent Start/Due with `NATIVE_AUTOMATIC_PARENT_DATES_NOT_DIRECTLY_WRITABLE`, and records Jira dates in the source section. Leaf dates remain native updates. Those failed rehearsal UUIDs were cleaned only after ownership checks; source backups/receipts retained. Fresh full329clone qualification is running; do not treat the rejected trial as PASS.

The latest checkpoint supersedes the historical notes below. Primary live/staging readback is329NEW; no primary sync configuration or business-data apply has occurred. Staging was restarted with its exact existing images, not Setup/seeder.

The CLI now exposes `snapshot`, `preview`, `apply`, `verify`. Primary `apply` and committing configuration require an actual interactive local human to type the exact preview hash; noninteractive invocation is denied. A target-specific OS lock is released automatically on process/power loss. Content, child and status receipts are written before native writes; UNKNOWN stops the remaining run. Do not start another apply after an interruption: use `verify`, inspect the receipts and reconcile before proposing any further writes. The current CLI deliberately refuses automatic resume of an existing approval directory; it cannot distinguish an unacknowledged configuration commit safely without operator reconciliation.

Complete official snapshot: private `operator/jira-sync/2149a4d4-a3f2-4b6e-9642-5138c3c16663/snapshot.json`, hash `8edc9e79a5aaf5679a4e5ea2a28a50215bff231b0b09e4dda9aee5a4adc65f23`:329uniqueSourceIDs,241Done/2InProgress/86NEW,329Start/Due,265worklogs/384SIMULATION hours,2comments,1697source journals,0attachments. Jira Sprint1 is future/undated and contains0issues; no local Sprint is created or started. Proposed local S1–S5 remain private planning metadata.

Full DB/table+sequence/assets/config restore has passed on the earlier two archives. Updated backups include actual private deployment parameters/runtime env: staging `backups/9092cb7a-2f3f-431c-8c1c-3fda4deaec75` and live `backups/91d10fea-86e2-4b8a-8155-b10efbb8962d`. Their checksums verify; full329native restore/import qualification is in progress. A sample1-item native staging import has passed content/Simulation-time-entry/replay/native-Done-denial/Insights exclusion, but sample/default restore proofs cannot authorize primary apply. Qualification checks exact code/image/source snapshot, not just a PASS label.

Native comments retain original Jira IDs/authors/timestamps as source metadata, while native publisher/timestamp are the real local importer/current time. Time-entry comments are capped at native1000characters; full original worklog text is retained in the work-package source section. Source history is documentary text, not backdated native journals or gate evidence. Restricted children are skipped when equivalent visibility cannot be preserved. New attachments stop qualification (current source has none); no arbitrary download URL is followed.

Live official core has no deployed custom hard gate, so all differing source statuses are retained/documented rather than promoted through its ordinary workflow. Staging status changes use its existing schema2 gate, without intermediate transitions, evidence or approvals. Medium priority has no exact native equivalent and is reported, not mapped to Normal. Imported simulation is excluded from staging Insights only with the tested candidate image; candidate8ae2b351… is currently built-only, not promoted.

Commands (run from the AI directory; replace paths with the actual private artifacts):

```powershell
& '.\.venv\Scripts\python.exe' jira_sync_backup.py backup --target staging
& '.\.venv\Scripts\python.exe' jira_sync_backup.py backup --target live
& '.\.venv\Scripts\python.exe' jira_sync_rehearsal.py --snapshot '<snapshot.json>' --backup '<backup-directory>'
& '.\.venv\Scripts\python.exe' jira_sync.py preview --snapshot '<snapshot.json>' --target staging --backup '<qualified-backup-directory>'
& '.\.venv\Scripts\python.exe' jira_sync.py preview --snapshot '<snapshot.json>' --target live --backup '<qualified-backup-directory>'
# Only a human-local console may approve the exact immutable hash:
& '.\.venv\Scripts\python.exe' jira_sync.py apply --preview '<qualified-preview.json>'
& '.\.venv\Scripts\python.exe' jira_sync.py verify --preview '<qualified-preview.json>'
```

Before preview, finish full native329qualification and deploy the qualified Insights image to staging only. `preview` requires a matching full329restore/import proof, source checksum and current scripts/image; historical previews cannot be applied. Preview expires after1hour. Apply rechecks mutable Jira children, source fields/Sprint membership and local config before writes, then source fields per10rows. Data after preview conflicts rather than being overwritten.

Rollback: retain database.dump/assets.tar/config/manifest plus each preview's before-data and receipts. These archives are **not** the legacy `Manage-OpenProject.ps1 Restore` format. Restore them only into an isolated UUID clone first; primary restore or inverse writes need a fresh approved recovery plan and must not overwrite later local changes. No blind restore, ticket/child deletion or credential reset is included in sync.

At this earlier checkpoint87Windows units/21sync tests passed and full qualification was pending. Final state above supersedes this:89units/23sync and full native rehearsal PASS; primary human-approved apply remains pending. Jira/bot/schedules/Gemini/key/counters/billing/live core image remain unchanged.

## Historical state, 2026-10-13 20:47 Asia/Bangkok

Implemented and tested: official-MCP snapshot with complete pagination, interrupted-read checkpoints, private checksum artifacts, and read-only previews for live8088/staging8091. **Not implemented/accepted yet:** apply/verify, receipt reconciliation for writes, backup/restore rehearsal, native comment/history/worklog import, Sprint membership reconciliation and candidate deployment. Do not treat a preview as completed synchronization.

Source snapshot: private runtime `operator/jira-sync/05b81f0c-1dcf-4bb5-972b-d799841c7a69/snapshot.json`, hash `9746b43391ec7c0f5e2f2094c01718b79870fb938f08ae79bc90515276cf11b4`. Official QAG3 read:329uniqueSourceIDs,241Done/2InProgress/86NEW,265worklogs,2comments,1697changelog entries,0attachments, one future/undated Sprint. All329carry simulation classification. Source counts are not product completion or employee performance.

Both targets map329SourceIDs without creation/deletion. Latest previews:

- Live: `live-preview-d7585672-140b-477d-8915-3d06096f9d3d.json`, hash `a81972aa180c3fb9e70553eb3c43c63fcf6e5e2bfc07a84b8397cd5d84e013c8`;329content/date proposals,243status differences. Native workflow validation is still pending; zero custom gate errors must NOT be interpreted as live hard-gate acceptance.
- Staging: `staging-preview-87e3ce50-f61b-4da0-9130-a1b702d2f2b0.json`, hash `60d48b4b0c47000e5cab8c559819e2a07c62ae22855e8f63f911a70fc61b4859`;329content/date proposals,243status differences,242denied by actual core gate preview. No fake intermediate transitions, evidence or approval will be created.

## Blocking configuration decision

User subsequently approved the minimal three-part configuration scope (“okay”). This is scope authority, not a local exact-hash approval or permission to skip backup/restore rehearsal. `core/jira_sync_configuration.rb` now provides a fixed transaction-only operation; there is deliberately no committing runner/public endpoint yet. Its preview includes project activity overrides, so historical configuration hashes above/below must not be reused for a later apply.

Native synthetic staging regression `core/jira_sync_configuration_test.rb` ran RED (missing implementation) → GREEN, including stale hash/no partial write, transaction requirement, idempotent replay, exact two permissions, global-inactive/project-only activity, non-admin PM native time-entry creation contract, and final rollback. This is an in-place rolled-back transaction test, **not** the required isolated backup/restore rehearsal. No persisted module, permission, activity or imported worklog has been changed.

Subsequent isolated **staging database-only** rehearsal PASS: fixed runner dumps the synthetic staging DB, restores it into a private internal network, runs the same regression on core image `sha256:0ab293ea359c1a5869c5bf2ab76299fe71183f518affdb5657e485f49a17f48b`, then removes its UUID containers/network. First run with a raw Windows checkout failed at ERB boot due to CRLF; this configuration-only suite now uses the pinned image, while the existing core-integration suite still mounts its prepared snapshot. No source checkout normalization or unrelated files changed.73 Windows units PASS including rejection of arbitrary suite names before Docker. **Full two-target database/assets/config backups and restore/hash acceptance remain unfinished.**

Safe regression command (synthetic staging only, never a live apply):

```powershell
docker exec qldapm-ai-stage-staging-web-1 bundle exec rails runner /qldapm-core/jira_sync_configuration_test.rb
```

Actual personal PM API `/api/v3/time_entries/form` returns403 in BOTH targets. Fixed read-only core inspection confirms project module `costs` disabled, and PM has neither `log_time` nor `view_time_entries`. Simulation activity is absent. No permissions/module/activity changed.

Minimal proposed delta per project:

1. Add existing bundled `costs` module, without billing/rates or paid services.
2. Add ONLY `view_time_entries` and `log_time` to the existing project-scoped QLDAPM PM role. No edit/delete-time-entry permission, no other roles, no admin grant.
3. Create activity `Simulation`, globally inactive and enabled only in that project.

Fresh fixed configuration previews, no mutation:

- Live project5/PMrole22: `026ac41d3638105d9621afbc5e38a846457353b87763062122893c5cb3c7ad61`.
- Stage project3/PMrole12: `0f40f98c9a129afe027c1c549b56222d4ddd6b93e117a46f98e61e58a064469e`.

This broadens PM's project time-entry access; explicit user authorization and the existing local exact-change approval are required before implementing/applying the privileged change. If rejected, worklogs can only remain documentary source data; do not silently fall back to unclassified actual hours or use bootstrap admin for routine import.

## Historical commands (superseded by qualified commands above)

From `D:/AI project/QLDAPM chat/openproject/ai`:

```powershell
& '.\.venv\Scripts\python.exe' jira_sync.py snapshot
# Interrupted reads may resume the exact private partial.json printed in the checkpoint.
& '.\.venv\Scripts\python.exe' jira_sync.py snapshot --resume '<private-partial.json>'
& '.\.venv\Scripts\python.exe' jira_sync.py preview --snapshot '<private-snapshot.json>' --target live --backup '<qualified-backup-directory>'
& '.\.venv\Scripts\python.exe' jira_sync.py preview --snapshot '<private-snapshot.json>' --target staging --backup '<qualified-backup-directory>'
```

At this historical checkpoint no apply command existed. The current command is described above; do not type historical preview hashes into another approval mechanism or run Setup/bootstrap. Each preview has a new immutable filename. Re-read Jira and local versions before any later write.

## Validation and remaining work

-72Windows unit tests PASS, including6new source/pagination/safety/preview/status-scope tests. Gemini HTTP responses in unit tests are fixtures, not real Google calls.
-Source-only staging Insights regression RED→GREEN, real UpdateService and report interface in rolled-back transaction. New source excludes imported simulation events from performance. Overlay/fork agree; source change NOT built/deployed or newly qualified.
-Live GET-only source verifier PASS329SourceIDs/parents/assignees/original descriptions/106AC and roles19PM/20BA. No work-package changes, credentials changes, Jira writes or Gemini changes.
-Before continuation: resolve configuration authority; implement fixed local approval/apply and the remaining sync actions; test version conflicts/replays/gate refusals through public APIs; backup and rehearse on separate volumes; deploy only tested staging Insights candidate; then obtain exact data previews and apply permitted fields. Keep simulation authorship and original timestamps as attributed source metadata, not impersonated/backdated native events.

Native global status names can collide (`New` versus`NEW`); mapping is restricted to verified project workflow IDs. Other-user status is intentionally hidden from the PM API: preview does not claim those hidden properties were verified; native assignment validation remains mandatory. Medium priority has no exact native-name mapping and is reported rather than guessed. Sprint write/membership support needs native adapter qualification before claiming parity.

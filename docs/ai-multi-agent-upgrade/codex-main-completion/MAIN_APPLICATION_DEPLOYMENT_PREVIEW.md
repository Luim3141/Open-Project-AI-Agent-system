# Main application/config apply — 21 Oct 2026

Scope already authorized by the full takeover request and the separate credential approval “Duyệt cả hai, chưa gọi Google”. No additional approval is requested for this scope.

- Replace Main web/worker/cron Core image bfda82ce… with immutable candidate `sha256:dde3c32ee69af450a6316450ac076d502953610932627ee33ce948f20dfbe459`. Only controller/view context refresh differs in the47Core overlay files. No database migrations.
- Add `gateway_mode=native` to the existing Main configuration; preserve every other config field. Recreate only Main Gateway using the unchanged456c38f6… image and the approved `gemini-free.main.yml` overlay.
- Install the prepared same-key/same-model FREE_ONLY Main enrollment, separate production proof and independent Main usage. Do not copy readiness receipts, histories, tokens or SQLite from Staging. No Google calls. Provider readiness remains unverified until a separately approved live smoke.
- Correct stale Main image-lock AI_IMAGE/CORE_IMAGE entries to the actual selected immutable images. Preserve previous files privately. Main management Compose includes the provider overlay only after Main enrollment exists, keeping later Start operations consistent.

Expected interruption: Main app/Gateway startup, approximately1–3minutes. Main proxy/cache/PostgreSQL/hocuspocus, all Staging services, Quick Tunnel, n8n and CSDLDPT remain running.

Qualification:19Windows+19Linux Gateway tests,6controller tests/31assertions,3real Rails/view tests/37assertions,42valid+42wrong-role native gate edges;24non-PM browser/API checks; PM readonly consent reproduction and14Monitor/graph/replay/responsive checks on isolated clone. Synthetic Native/mock tests are labelled separately from actual native browser/API results. Initial harness failures (CSP unsafe-eval, localized state text, missing API CSRF) are retained as test-development history; CSP/CSRF were never disabled.

Fresh backup `backup-20261021-020744`: all221PG table/sequence fingerprints restored into a new clone database, SQLite cold integrity PASS; private archive hash validation PASS. Actual previous and candidate Core images both started on the isolated clone and passed health/native identity; no WP changes. See fresh-backup-restore.json and rollback-rehearsal.json.

Rollback: select previous immutable Core image and recreate only web/worker/cron through official Compose files. Restore previous Main config/env/image-lock from the private deployment directory if that config is implicated; preserve newly approved Native tokens and all business/audit data. Keep newly enrolled provider files OFF if provider setup cannot be validated. No whole DB/SQLite restore, no volume deletion, no automatic replay. Restore serving availability before further diagnosis.

Not included: Gemini smoke; history import; dates/status/Sprint membership changes; Main public access; Stage changes; capacity20 testing. These continue as separate phases/gates.

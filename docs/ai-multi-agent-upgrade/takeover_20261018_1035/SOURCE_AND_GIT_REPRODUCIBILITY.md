# Source and Git reproducibility

Branch `codex/local-multi-agent-upgrade`, HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`. Exactly **two tracked files**, both v1 workflow JSON. Full porcelain snapshot: **1909 untracked paths** at capture; tracked diff empty. This is not a reproducible product revision. `git-status-full.txt` and `git-ignored-paths.txt` preserve exact inventory; no -uno, clean, stash, reset, checkout, commit or push used.

Nested native fork HEAD `b4fe82644e96f2a941ace41be0ef81599864fef9`,18 dirty paths preserved. Root openproject/.gitignore excludes development/ and ai/.venv; fork changes require pinned fork commit + reviewed patch or explicitly preserved overlay, not an implicit root add. `source-manifest.json` hashes349 relevant AI source/config/test files after local authorization fix. Hashes do not replace versioning. Keep private runtime/secrets/backups, .venv, cache and binary attachments out of commits.

Runtime images: Gateway006b9c6c, Core8a42c7ef, n8n2.43.6 immutabledd580fe1, candidate Tunnel actual ID in runtime.json. Compose chain: stage.yml + deep-ai.stage.yml + gemini-free.stage.yml + local-runtime.stage.yml + quick.stage.yml + backup.stage.yml, project qldapm-ai-stage. `docker compose config --format json` passed with saved .env plus the same image/runtime variables used by provision_local_stage; eight service definitions including seeder, seven serving services. Config command only; seeder never run. A naked .env invocation initially failed because required operator image variables were absent; do not mistake it for serving outage.

Build paths: gateway Dockerfile / Dockerfile.gateway-patch / automation/FreeOnly.Dockerfile; Core core/Dockerfile and automation/DailyCore.Dockerfile; Tunnel automation/QuickTunnel.Dockerfile + shell supervisor. DailyCore currently copies only three files and omits the new Control Center partial: extending a view render without its partial would break new builds. Dependency pins: requirements.lock.txt; native fork Gemfile/lock and frontend lock; n8n pinned digest. Base tags/old layers must be retained or resolved to immutable IDs before a clean rebuild. No image built during takeover.

## Proposed commit sequence — owner approval before commits

1. Safe product baseline: AI gateway, operators, core overlay, manifests/locks and focused tests; secret scan, explicit path allowlist, exclude private files. Record native fork reference/dirty patch separately.
2. Standalone P05–P08 candidate modules and tests clearly marked not deployed; wire/qualify each vertical slice before marking live completion. Capture source-to-image manifest.
3. Runtime/recovery fixes and immutable configuration after qualification; pin deployed pair and backup/restore proof. Never merge/promote Main as part of committing.
4. Current takeover reports and authoritative handoff correction.

Rollback local source fix: original service.py saved privately under operator/takeover-20261018-1035/service.before.py, SHA2569744d3ee4f1e0857779d5ea12bf3ea3379302ea785e98138f3112dc80dbcd299. Only the Control Center authorization block changed; restore that block/file only after checking subsequent edits. No runtime rollback is needed because nothing was deployed. Historical Quick Tunnel rollback instructions using a single Compose file are unsafe for this merged project and must not be executed.

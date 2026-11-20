# P02-10 acceptance — 16 October 2026

Accepted staging Gateway `sha256:bccd1d2c3de9c1a500133103a376f5b179fe2cd1bcb2cfd0b6e0595c4129e412`; previous `9cb63a97...` retained. Native core `1cdd2590...` and its 18 dirty files remain unchanged. Main was not promoted.

Implementation: provider readiness consults durable quota/circuit without a network probe; status exposes WAITING_QUOTA/OFFLINE/BLOCKED_KEY_OR_MODEL separately from authorization. Newly queued intents receive their wait state immediately. Native reporting remains available independently of Gemini. Provider failures retain actual partial tool receipts and never replay writes. Cached native results require fresh permissions/source; unavailable reads show OFFLINE, changed sources STALE, revoked access denies without returning cached content. Existing Rails state/heading/message rendering is reused; no core edit.

Executed validation:

- Windows full regression: **209 tests PASS**, 109.095s; explicit exit0 and final OK checked before deployment. `P02-fallback-regression-final.log`, `P02-fallback-final-test-exit.json`. HTTP messages in unit logs use test transports, not new Google requests. Earlier stale assertion failure was corrected and the entire suite rerun.
- Exact immutable Linux candidate: **43 tests PASS**, 1.287s; read-only root, no network, non-root. `P02-fallback-linux-tests.log`.
- Private cold clone: actual five native identities BA-PM/PM/BE/FE/QA each read335; injected quota keeps five pending intents while native reporting completes. Injected provider503/auth/source change/native503/403 verify WAITING_QUOTA/OFFLINE/BLOCKED_KEY_OR_MODEL/STALE/denial. Zero SDK calls; only GET allowed to actual OpenProject. Faults/450 extra quota rows and temporary bearer tokens exist solely in clone. Original ledger/config untouched. `P02-fallback-live-clone.json`.
- Actual staging after deployment: seven source hashes match workspace; existing key/proof loads, cached READY, caps13RPM/225000TPM/450RPD, usage471, empty pending queue; five real roles read335 with unchanged PM-only-write ceiling. `P02-fallback-live-check.json`.
- Read-only inventories and qualified comparison PASS: all seven active staging services healthy, retired Radmin stopped, all four HTTP endpoints200; DB schemas/counts/roles and Gateway states/ledger/private metadata match exactly. Sole allowed change is Gateway image. `P02-fallback-before.json`, `P02-fallback-after.json`, `P02-fallback-preservation-check.json`.

Rollback: retained prior image and private operator snapshot `local-runtime/before-provision-1792138451612994600`; no migration or data deletion in this task. Prior real backup9ed96831/native221-table/assets/config and Gateway/n8n logical restore evidence remains valid; provisioning also cold-backed up current Gateway before replacement. No Docker Desktop restart, CSDLDPT action, new provider request or billing action.

Limits: clone/API tests do not prove five physical browser clients or sleep/recovery; P09 remains required. Cached READY/owner Free attestation is not a live Google billing check. n8n workflows/Supervisor/context/knowledge are later tasks.

# AS-IS / TO-BE — P00 observed 15/10/2026

| Area | Observed AS-IS | Target / not implemented |
|---|---|---|
| Core/gateway | Exact staging source/image parity PASS; `artifacts/P00-03-parity.json` | No main promotion without qualification + owner approval |
| Data | Main project5/329 work packages, stage project3/335; different schemas/migrations captured in `artifacts/P00-runtime-before.json` | Preserve every existing/user-created item; no seeder/reset |
| Host access | Stage18091/18092 HTTP200; main8088/8090 host-unreachable although containers internally healthy | P01 diagnose main port restoration, no silent READY claim |
| Roles | Native read-only effective-permission matrix proves staging PM-only-write; main legacy non-PM edit still true | Retain stage controls; main upgrade separately approved |
| Gemini | Staging persistent existing key; historical continuing-cost policy conflicts with new scope; provider now OFF with unchanged key/ledger | Free-only fail-closed allowlist/current quota + privacy, shared fair queue |
| Restore | Actual isolated DB/assets/config fingerprints and SQLite backup restore PASS; `artifacts/P00-07-restore-result.json`, `P00-07-sqlite-restore.json` | Not a release/Jira-import qualification |
| Scheduler | OpenProject cron container; no running host broker detected; no n8n instance in Docker inventory | One n8n CE owner on loopback, machine read-only, no duplicate schedules |
| Agents/knowledge | Existing AI worker + SQLite AI runs/proposals; gateway catalog/native bridge exist | Supervisor/role agents/durable task tree/ACL FTS not implemented |
| LAN | Windows network profiles currently Public; Radmin VPN also present; no LAN TLS/5-device acceptance | Trusted Private LAN only, HTTPS CA trust once, no VPN/WAN/public tunnel |
| Resources | ~24GiB host RAM, ~2.85GiB free during audit; Docker ~11.5GiB allocation, i5-12500H/16threads | Measure before additional services; no large model/Redis/HA |

Source references: `openproject/ai/gateway/{gemini,store,service,ai_worker,permissions}.py`, `core/overlay/app/models/qldapm/{rbac,gate_policy}.rb`, `stage.yml`, `deep-ai.stage.yml`, latest DATES/RBAC checkpoints. Handoff/checkpoint counts are historical; do not delete new data to match them.

Not tested/claimed: Docker Desktop engine restart x3, five physical LAN devices/TLS, current provider inference/key validity, fairness/n8n/RAG, sealed release qualification. Existing legacy configuration fixture fails `PM_ROLE_NOT_PROJECT_SCOPED` after Administrator memberships; retained as a qualification blocker, not weakened.

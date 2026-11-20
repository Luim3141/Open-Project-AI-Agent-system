# TEST / LOCAL RELEASE GATES — 5 users, no VPS

## Mandatory evidence matrix

| ID | Scenario | PASS requires |
|---|---|---|
| SYS-START-01 | Windows running, Docker Desktop manually started | Core/Gateway/agent/n8n healthy automatically after prior provision, NO logon/task scheduler auto-start, no terminal commands |
| SYS-START-02 | Docker Desktop engine stop/start 3 times | Volumes, n8n workflow, API credentials, quota ledger, receipts, pending jobs persist; no duplicates |
| SYS-START-03 | Individual container manually stopped | `unless-stopped` exception documented; repair script restores without deleting volumes |
| GEM-01 | Provider verified Free Tier model/project | No billable model, paid route, billing credit, unauthorized key; evidence from actual account/settings |
| GEM-02 | Existing Gemini key after Docker start | No re-entry/setup; minimal approved smoke confirms connectivity if available, accurate READY/DEGRADED states |
| GEM-03 | 5 users share one Gemini project | Aggregate RPM/TPM/RPD/TPD enforced, fairness and backlog, no 5x quota illusion |
| GEM-04 | 429/503/quota exhaustion | UI native functions healthy; retry bounded, no write replay, no paid fallback |
| LAN-01 | 5 distinct accounts on LAN | One secure HTTPS URL after initial trust setup, native login, no shared admin credential |
| LAN-02 | Outside LAN / privileged ports | Firewall blocks WAN/other subnet; DB/Gateway/n8n not exposed; no port forwarding |
| RBAC-01 | PM vs BA/FE/BE/QA | PM-only-write, others read/report/comment; native gates, before-after receipts, no auto approval |
| RBAC-02 | Inject instructions in tickets/comments | Cannot raise rights, read other users' private data, retrieve secrets or execute shell |
| N8N-01 | Single n8n CE admin schedules local reports | 5 end-users see report in QLDAPM, don't gain n8n editor; workflow JSON export available |
| N8N-02 | Missed schedule when Docker stopped | No duplicated jobs or catch-up flood after restart; deterministic default uses no LLM |
| AGENT-01 | Supervisor + PM/BA/QA/DEV/Reviewer | Typed result, scoped tools, delegated only when required; run/task tracing |
| KNOW-01 | Local RAG/FTS across 5 roles | ACL prefilter, citations and versioning; no secret leakage to Google Free API |
| DATA-01 | Backup/restore staging | WAL-consistent gateway/DB/n8n/keys backup and restore evidence; no impact on main |
| PERF-01 | 5 parallel LAN users, bounded AI load | Under measured RAM/CPU limits, UI healthy; long tasks queued; no extra infra needed |
| RELEASE-01 | Local main promotion with owner approval | Core+gateway pair validated, release notes, rollback/test evidence; no VPS/cloud deploy |

## Phase gates

- **P00:** source/dirty snapshot, actual runtime inventory, RBAC freeze, backup/restore, initial no-cost/privacy check.
- **P01:** manual Docker startup auto-recovery + encrypted local LAN URL and persistent Gemini credentials, 5 accounts.
- **P02:** Free-only entitlement and shared quota ledger, provider smoke safe, no charges.
- **P03–P05:** durable run state, n8n CE scheduling and Supervisor/role-safe agents.
- **P06–P08:** local knowledge with ACL, project workflows only (NO GitHub Research), dashboard/approval display.
- **P09:** 5 simultaneous clients, 429/503/restart/privacy test matrix, restore.
- **P10:** owner-approved local main release, full no-touch startup acceptance, final evidence summary.

## Existing known gaps (from snapshot; do not claim resolved)

- Some MCP role tests used expired bearers, legacy BE-write test expectations clash with current policy.
- No sealed staging pair/full local main rollout evidence in handoff.
- No proof n8n/Supervisor/RAG deployed, no current measured quota or Docker startup acceptance.

**Do not use simulated test outcomes as proof of production.** No auto-promotion, no cloud/VPS, no unattended paid upgrade.

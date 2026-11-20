# Milestones / Sprint / Risks — Revised V2 for 5-user local-only system

**Không áp deadline giả.** Dùng quality gates, mỗi sprint 1–2 tuần khi có tốc độ thực tế. Không mở GitHub Research/VPS/HA/Kubernetes trong bất kỳ milestone nào.

| Milestone | Phase | Kết quả demo |
|---|---|---|
| M0 Safe baseline | P00 | AS-IS, dirty source, RBAC, backup/restore, 5 accounts scope |
| M1 Local no-touch Docker | P01 | Mở Docker Desktop một thao tác → services tự phục hồi, LAN secure + persisted key |
| M2 Free Gemini | P02 | 5 users shared Free API quota, fair queue, no extra billing, graceful 429/503 |
| M3 Core runtime | P03 | Durable runs/context/actor-bound, no replay writes |
| M4 n8n local | P04 | One internal n8n admin + deterministic daily report |
| M5 Multiple agents | P05 | Supervisor/PM/BA/QA/DEV/Reviewer trong native business scope |
| M6 Second Brain | P06 | ACL, FTS, cited internal work-package data |
| M7 Project automation | P07 | Local Sprint briefs, deadline, QA readiness, workload flags (no web/GitHub) |
| M8 Control Center | P08 | Quota/status/trace/proposals/waiting states |
| M9 Safe acceptance | P09 | 5 parallel LAN clients, fault/restore/security matrix |
| M10 Local release | P10 | Owner-approved promote main, 3x Docker restart no-touch acceptance |

## Tracking daily

| Signal | Truth source | Expected |
|---|---|---|
| MVP progress | `TASKS.json` | 113 required tasks, only tested evidence counts |
| Phase status | `PROGRESS_DASHBOARD.md` | PASS only if all required phase task DONE |
| Pending / blocked | `TASKS.json` | Every blocker has next action & free fallback |
| Docker engine recover | Runtime logs | Engine manual start → containers auto-recover |
| Gemini quota & billing | AI Studio + gateway ledger | Free tier verified, zero additional charge |
| 5 users / LAN | RBAC + browser test | HTTPS native auth, PM-only-write, gateway private |
| Backups | Restore artifacts | Stage restore drill, secrets separate |
| Host resources | Docker stats & Windows monitor | 5 users supported without scale infrastructure |

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| R01 | Existing Gemini model not free / key invalid | Verify project+model; fail-closed, mock only test; never paid API |
| R02 | Google AI Pro assumed to increase API quota | Explain separate entitlement, no fictitious limits |
| R03 | Free API 429/503 | Fair queue, bounded retry, graceful native UI |
| R04 | Manually stopped Docker container | Document `unless-stopped` and one-command repair |
| R05 | RAM/SSD/machine down | Measure on host; keep runtime light; no HA/VPS |
| R06 | Five user LAN auth over untrusted HTTP | Gate HTTPS/trusted local CA, private firewall |
| R07 | n8n Community licensing/workflow sharing | Internal own-use, 1 editor/admin; no external resale/edit clients |
| R08 | Secret/PII into Free Gemini | Classification, minimization, no provider if restricted |
| R09 | RBAC regression from old tests | Keep native PM-only-write; update tests based on approved policy |
| R10 | Losing progress during Codex sessions | Task ID registry+evidence+PROJECT_STATE.md; merge V1 work by ID |
| R11 | License Docker Desktop not free for given org | Verify eligibility, alternative free Docker Engine/Podman if needed |
| R12 | Router/host IP changes | DHCP reservation/local DNS/TLS setup once, test 5 clients |

**Done MVP:** after initial bootstrap, Docker Desktop start is sole normal manual action; 5-user LAN OpenProject, n8n, Supervisor, free Gemini persisted, Zero-New-Spend tests, reports, gates and rollback all pass. No requirements for runtime when PC/Docker off or provider 429/503.

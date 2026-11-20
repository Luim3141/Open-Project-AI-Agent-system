# Next bounded development plan

No restart of P00–P10 and no bulk status reset. Continue from verified runtime and this separate reconciliation layer.

| Order / ID | Task | Dependency | Acceptance |
|---|---|---|---|
| 1 / TAKEOVER-SEC | Repair TOTP after explicit owner approval | SECURITY_REMEDIATION_PREVIEW | Six actual accounts mapped by login; old revoked, one active/default new device each; saved-key read-back and real login; no secret output |
| 2 / TAKEOVER-RUNTIME | Reconcile Tunnel saved image/provisioner and full Compose chain | Preserve candidate; source review | Immutable image matches live and manifest; readonly ownership/status passes; no serving fault/restart |
| 3 / TAKEOVER-AGENT | Wire Supervisor into one authenticated durable read-only task path | Existing P03 contracts, current local source fix | Native ACL→task/run→selective specialist→review→report→audit through real UI; no extra queues/services, no business write/provider call for deterministic scenario |
| 4 / TAKEOVER-CC | Finish Control Center data/partial packaging and truthful quota/status | Agent path + fail-closed tests | Qualified clone UI; same-role membership removal denies; unknown telemetry never zero/READY; native role ceiling retained |
| 5 / TAKEOVER-KNOWLEDGE | Wire approved source ingestion and retrieval into scoped task/UI | Agent path + persistent storage | Duplicate fixture ingestion idempotent, fresh ACL/source revision citations; clone restart proof; no Native DB destructive change |
| 6 / TAKEOVER-PAIR | Build immutable pair and qualify source/image parity | Above vertical slices | Actual clone tests plus backup/restore; old pair retained; deploy only intended Staging pair; no Main promotion |
| 7 / TAKEOVER-UAT | Complete approved fixture proposal/create/assign/status/comment cases | Owner fixture approval + qualified pair | All5roles; explicit PM approval; exact before/after and one native receipt; non-PM denied |

Keep G2 blocked and capacity20 deferred. Preserve unrelated source, Main, CSDLDPT and Docker disk placement. Do not run old repair/rotation/matrix scripts blindly: some mutate live services or rewrite historical reports. Current audit scripts are read-only except browser session metadata and local artifact generation. No background work is scheduled after this turn.

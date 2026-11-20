# P02-06 acceptance — 16Oct2026

Deployed staging Gateway `2415e4a25898f0d9c741bc65871d6f0207e448f34e717d7fcfca2e93c7e66496` from audited70c723 source-only layer. Main/core unchanged. No Google request during acceptance.

Never-started intents remain queued with WAITING_QUOTA/WAITING_PROVIDER/BLOCKED_KEY_OR_MODEL. Admission checks spend no quota; reserve_gemini remains the atomic hard gate. Interruptible scheduler sleep is at most30s. Expired executing runs retain receipts as failed_or_unknown without replay. Explicit429/503 can retry only the rejected SDK phase under continuous Free-only authorization: at most3attempts, exponential cooldown+jitter, fresh quota reservation and600srun deadline. Valid RetryInfo delay is honored, unknown429 defaults3600s and503 defaults60s. Unknown transport/timeout/auth/malformed errors and the smoke path do not auto-retry. SDK internal retries remain disabled.

- `P02-wait-regression-final.log`:196/196 PASS114.079s, no skips. Initial regression had one old expectation that quota terminates the run; REST/MCP test now checks durable running+WAITING_QUOTA and no token leak.
- `P02-wait-linux-final.log`:29/29 PASS0.537s, final image/network none. Covers fairness, quotas, max attempts/jitter/deadline, policy recheck and actual SDK over mocked HTTP429/503 after a confirmed comment. Exactly one mutation, only rejected provider phase repeated, all5reservations retained.
- `P02-wait-container-final.json`: same disposable container second start retains5waiting users and450fixture ledger rows. Injected reset resumes correct order with5new fixture reservations. No real midnight or provider call claimed.
- `P02-wait-stage-deploy.json`: immutable operator deploy/preflight/private snapshot PASS. `P02-wait-live-check.json`: source parity,5native identities/335visible each, PM-only-write ceiling, cachedREADY, admission currently unblocked and usage471 PASS.
- `P02-wait-preservation-check.json`:19selected containers healthy/intentionally stopped; native schema/roles/counts/prior run-job-proposal-ledger states/private configuration unchanged. Only candidate Gateway image and additive ai_queue differ from resume baseline. Four HTTP ports200.
- `P02-wait-private-backup.json`: backup9ed96831-f114-4a1a-8afd-ec4ad7cb91f2 PASS221tables. `P02-wait-native-restore.json`: isolated221-table/assets/config restore PASS.
- `P02-wait-sqlite-restore.json`: gateway/n8n logical hashes match; ai_queue and original471usage rows restored. `P02-wait-backup-pairing.json`: owner policy/readiness/config/key archive matches exactly.

Backup permits snapshots of never-started queued AI intents while executing/legacy runs and unresolved operator jobs still block. Backup watch reloaded; no Desktop restart or CSDLDPT change. No live restore, main promotion or physical five-browser test claimed.

Official references checked: [Gemini retry strategy](https://ai.google.dev/gemini-api/docs/troubleshooting), [Google RPC RetryInfo](https://docs.cloud.google.com/storage/docs/reference/rpc/google.rpc). Pending resume and phase-only retry are local safety choices.

Previous70c723image, private before-provision-1792122538991921400 and validated9ed968backup retained for operator recovery. Reconcile executing receipts before any downgrade/restore. P02-07/08/10 remain unfinished; P03gate stays closed.

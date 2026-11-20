# QLDAPM Telegram Commander / Agent Observer — 05/11/2026

User-approved implementation specification: attachment `21f610dd-956a-4005-a58b-c6f7aa0c2471/Pasted text.txt`.

## Scope and sequence

1. Capture real Main container identities, source hashes, control state and private backups. Preserve untracked work and current OFF mode.
2. Reuse Gateway authorization, command dispatch, execution monitor, receipts and checkpoints for a shared canonical Observer projection.
3. Embed Agent Studio in existing Rails UI; bounded polling pauses while hidden. No separate website or mock runtime data.
4. Add isolated aiogram/google-genai polling service with numeric-ID pairing, SQLite memory, validated tool schemas and expiring exact-action confirmations.
5. Reconcile verified Observer events into durable recipient outbox; n8n handles outbound delivery and ACK. Never treat Dev success as task acceptance.
6. Run targeted security/behavior tests, image checks, live read smoke and compatibility checks. Add the service to current Compose project and preserve existing services/volumes.
7. Ask Owner to configure secrets locally and pair only after deployable service exists. Record actual Telegram/Gemini/E2E blockers; never substitute mocks for live proof.

## Invariants

- One Task — Multiple Agent Runs. No Adaptive Subtask, second Supervisor or coding provider change.
- Existing actor/project RBAC, Native ACL, exact approval and idempotency remain authoritative.
- Secrets stay outside repository; no GUI; no deletion/reset of data or volumes.
- Owner clarified Gemini model to `gemini-3.5-flash-lite` during implementation; reuse existing key read-only, no paid fallback or Coding Agent provider change.
- No old task replay, new coding run or external message merely to produce a green report.

## Validation and rollback

Use isolated SQLite/unit fixtures and real Gateway read calls. Record source/image hashes and before/after protected-state hashes. Patch images on current immutable image bases. Existing release helper provides idle-OFF guard, worker fence, SQLite snapshots, Compose parity and image rollback; preserve config rather than historical helper policy defaults. Rollback restores image pins and prior source, retains all new databases/outbox for reconciliation, never restores business data automatically.

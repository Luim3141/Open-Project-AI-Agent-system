# P03-05 — durable typed state machine

Accepted staging Gateway `sha256:6ebd8f8a1759a6adc6a962746db8e3df30828a4c8bab0f0f6f7be7543a4ea525`. Atomic actor/project-bound state transitions use BEGIN IMMEDIATE and compare expected state before update. QUEUED may wait for quota/provider/key, then return to QUEUED before execution. RUNNING can finish REVIEW/FAILED/COMPLETED only with a matching typed result; started/terminal runs never return to queue. Expired tasks cannot start. REVIEW is draft output, not native approval. Transitions append state-only audit entries in the same transaction; no prompt/secret log or business execution.

Validation actually run:

-5new state tests PASS0.675s: wait/reopen lifecycle, two connections claim exactly once, interrupted receipt retention, actor/project/scope/state/terminal checks, expired start, no terminal replay.
-229full Windows tests PASS99.604s and exit0+finalOK verified before deployment; P03-states-regression.log/P03-states-test-exit.json.
-63Linux candidate tests PASS2.117s, readonly/non-root/networknone; P03-states-linux.log.
-Same disposable container restarted with private actual-stage cold clone: RUNNING remains RUNNING, explicit failed reconciliation retains synthetic receipt and blocks requeue; all pre-existing rows/471usage preserved. No provider/native calls. P03-states-container-restart.json, tests/container_agent_states.py. This validates metadata durability; executor binding is the next task, not claimed here.
-Actual staging source parity/private config+key predeploy byte match; metadata tables remain empty,79done/11failed AI receipts/471usage unchanged, cachedREADY. P03-states-live-check.json.
-Inventories/qualified comparison PASS: only Gateway image changed; schemas/native roles/counts/legacy ledger/ports/mounts/private metadata preserved,7stagehealthy/4HTTP200. P03-states-after.json/P03-states-preservation-check.json.

Previous3e2a64d5 retained; private source snapshot operator/p03-state-before-20261016 and pre-provision cold backup local-runtime/before-provision-1792139839438502300. No schema migration/core edit/actual provider call/billing change/main promotion/Desktop/CSDLDPT action. Next P03-06 binds typed metadata to the existing single fair executor; no separate scheduler/Redis.

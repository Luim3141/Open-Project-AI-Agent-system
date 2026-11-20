# Final Stabilization Phase 2 Implementation Plan

**Goal:** Repair integrity, retrieval and integration defects on the current MAIN, with evidence tied to actual source and images.

**Spec:** Owner attachment `0e1aba0d-c96b-458c-9551-65a018579c49/Pasted text.txt`.

**Architecture:** Gateway remains the only scheduler and durable authority. Operator calls bind to a persisted worker/claim generation; host process locking protects the shared OpenClaw runtime. External requests retain journals and unknown outcomes require reconciliation. RAG and n8n changes are independently qualified before rollout.

**Constraints:** No Computer Use, Project5 writes, paid generation, destructive reset, merge or history rewrite. At most one new bounded Project6 E2E after final changes. Owner UAT remains pending. Master-key cutover requires successful migration/decrypt/restore/rollback.

## Tasks

- [x] M0 capture current container/image/queue state and private PG/SQLite backup. `M0.json` records live state; older PASS reports remain historical.
- [x] M1 reproduce stale operator and host races in `test_engineering_fencing.py`; bind persisted claim identity in `store.py`, `engineering_fencing.py`, `engineering_operator.py`, `engineering.py`; enforce host tool boundary and singleton in `engineering_worker.py`, preserve `engineering_delivery.py` journals; test stale completion, concurrent claims, late Native reply, POST timeout, process restart and duplicate resume.
- [ ] M2 investigate actual embeddings/chunks; freeze dev/holdout gates; implement minimal RAG fix and measure exact/semantic/ACL/citation/freshness/latency in isolated Qdrant. Agent scope: RAG modules/tests and `rag/`.
- [ ] M3 identify failed master-key mechanism from exact n8n source; prove clone decrypt/restart/rollback and document unresolved cutover; test strict persistence policy without corrupting retry. Agent scope: n8n security and `n8n/`.
- [ ] M4 exercise all 16 published business adapters on isolated n8n and fix actual reporting contract failures; preserve denial for privileged actor19. Agent scope: workflows/reports and `workflows/`.
- [x] M5–7 verify Rails/JS projection contracts, GitHub stacked PR graph, OpenClaw receipts, demo revision, reporting/knowledge source links and Project5 tables read-only.
- [x] M8–9 review changes, record command/time/source hashes/image/environment for each new check, build immutable candidates, stop idle worker, backup/deploy/read-back/rollback qualification, optionally run one bounded E2E, update handoff/UAT guide.

## Review focus

1. Expired worker may already have sent external POST: keep pending receipt; never replay it without read-back.
2. Lease validation must occur in write transaction, including terminal completion; a token check only before network is insufficient.
3. Shared OpenClaw gateway cleanup must not kill a successor: hold exclusive OS lock across host lifetime.
4. Retrieval tuning may fit labels: use fresh holdout, preserve abstention and ACL, state model-authored labels.
5. Master-key migration may change ciphertext yet break deployment DEKs: require vendor decrypt and server restart, not import count alone.

## Rulings

- Owner explicitly orders immediate autonomous implementation and ordinary rollout; proceed without the optional skill plan-review pause.
- Main source is largely untracked at historical git HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`. Preserve it in place and fingerprint exact tested files; never claim that HEAD alone identifies current source or commit unrelated files.
- External fencing cannot retract sent requests. Durable receipts, Git SHA read-back and no automatic replay are mandatory; explicitly report remaining reconciliation limits.

## Final disposition — 2026-11-02 08:05 UTC

M1 fixes deployed and reviewed; M5–7 contract checks/deployment/read-backs done, Human UAT still pending. M8–9 authorized bounded E2E and handoff executed; this checkbox does not certify every system gate. M2 remains unchecked/FAILED-PARTIAL: three candidates failed quality/safety gates, no semantic rollout. M3 remains unchecked/BLOCKED for new-key cutover/history, despite old-key portable restore mitigation. M4 remains unchecked/PARTIAL: adapter checks completed, WF07/WF12 business configuration not accepted. Final live OFF/queue0/provider gatefalse; exact source/images in final-live-verification.json. No further fresh task is authorized within this Phase2.

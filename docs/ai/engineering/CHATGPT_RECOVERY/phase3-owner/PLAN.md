# Phase 3 Owner Control and Live Observability Implementation Plan

> Implement with Superpowers executing-plans plus bounded independent backend/n8n/RAG agents; native tests, no browser automation.

**Goal:** Make Owner commands, GitHub synchronization and durable agent activity visible without page reload, preserving Phase2 integrity.
**Architecture:** Authenticated Rails JSON commands retain CSRF/session/RBAC and return fresh Gateway state. Server-rendered allowlisted live fragments update existing panels. Adaptive single-flight polling reads durable events (3s active, 15s idle, 60s hidden), refreshes on visibility/online, and rejects old generations/revisions. Gateway remains sole scheduler. No SSE service or model call for telemetry.
**Spec:** Owner attachment 6cf62973-de14-4edd-830d-f3f3214af8ac/Pasted text.txt.
**Constraints:** No GUI/Computer Use, Project5 writes, paid provider, auto-merge/history rewrite/reset. Backup/idle/candidate/rollback before MAIN. Final mode OFF. Owner UAT pending. Phase3 fresh E2E max1 only if needed; not yet used.

## Tasks
- [x] P0a Rails/JS request contract: remove invalid RUN_ONCE control calls and swallowed errors; explicit JSON POST once with request UUID, CSRF, correlation and error/unknown outcomes; fresh projection after response. Files qldapm_ai_controller.rb and actual ERB handlers; tests Ruby controller harness and Node VM. Red tests for native/Turbo response mismatch, disabled-on-timeout, stale response order and auth errors before implementation.
- [x] P0b Gateway: durable revisioned feedback/control vs effective state, AUTO idle remains enabled; queue eligibility/block reasons; serialized/idempotent GitHub sync, last successful sync. Files engineering*.py/service.py and fixtures owned backend agent. Verify persisted state + worker claim, not labels.
- [x] P0c Live projections: stable regions for controls/mission/pipeline/workforce/backlog/execution/GitHub/reports/notifications; sanitized events/receipts from Gateway, no fabricated progress. Keep edited knowledge/intake/schedule/modal state. Tests immediate fresh PR/report rendering, no overlapping poll, out-of-order responses, tab/online reconnect, duplicate handlers, inactive interval, disconnected timeout. Owner/browser acceptance remains pending.
- [ ] P1 bounded RAG: classify Native corpus misses, predeclare one new evidence-backed candidate hypothesis and gates, no consumed-holdout retuning/no new model downloads. Agent isolated evidence; deploy only passing quality+safety gates.
- [ ] P1 n8n: read exact principal18/19 mapping; preserve all5-target PARTIAL if guard denial expected. No unsafe master-key cutover/retention. Add ciphertext-copy verification and Owner custody/offhost procedure without secret output. Agent source/tests only.
- [x] Release: fresh live backup+Project5 row snapshot; targeted/full regression tied to exact hashes/images; candidate Core real Rails authenticated request/response and Native clone; Gateway network-none fixture/startup/rollback; review, idle deploy, API read-back, hash parity, Project5 comparison, final OFF and no unknown replay.
- [x] Handoff: acceptance matrix + OWNER_CONTROL_AND_LIVE_OBSERVABILITY_EVIDENCE.md, status/defects/test-index/security/DR/UAT docs; separate source,clone,MAIN and Owner-reported failure statuses.

## Review focus / rulings
- Owner-reported failures authoritative: prior146 tests do not establish browser acceptance.
- Read-only polling must not invoke report generation/provider; unknown POST timeout must not auto retry or fabricate rejection.
- New JSON operations use existing authenticated Rails endpoint, not browser bearer or weakened owner mapping.
- Old poll cannot overwrite newer command projection; reconnect starts bounded refresh without duplicate listeners.
- Ruling: Owner explicitly orders autonomous implementation/deploy; no optional brainstorming/plan approval pause. Existing workspace has thousands of untracked authoritative files; preserve and SHA-snapshot rather than move/reset/commit all.

## Final disposition

P0source/API/clone/release gates executed; Ownerbrowseracceptancepending. P1RAG operational scan isolation deployed,10/10samplecurrent and exactcitationsverified; semanticqualitygate remainsFAILED/PARTIAL and originalstrictcloneassumptionfailuresretained. P1n8nconcreteciphertextchecker/proceduretested, butmaster-key/history/WF07/WF12/offhostDR gatesremainunchecked. NofreshPhase3codingtask;nomerge/reset/Project5write. Finalimagesce047/7649/392,OFF/queue0,17hashmatch,13tablecomparisonunchanged.

<!-- FUNCTIONAL_COMPLETION_27FB7D12 -->
# Functional completion implementation — Owner prompt27fb7d12, 03/11/2026

04/11: tiếp quản phần subagent đã dừng; làm tuần tự, không tạo thêm subagent. Gateway status repair a6fe1d61 deployed;13 immutable-image +72 targeted regression PASS. WP394/run301dbdd8 là coding task duy nhất và đã SUCCEEDED/PR12 OPEN;57tests, Native/knowledge/n8n/GitHub/report read-back.43calls/recovery5; OFF/active0/gatefalse. RAG vẫn FAILED; hai span-ID pilots và grouped-quote pilot đã dừng/reject theo gate. Không có Codex subagent mới.

**Goal:** Command Center business actions → authorized workflow observations, grounded bilingual RAG with abstention, one bounded fresh AI task after source/image gates.
**Architecture:** Preserve Native ACL and existing worker; n8n consumes fixed authenticated commands/events. Add bounded sanitized host observation of16 published workflows and executions, consumed by Gateway Project6 projection; never Docker access inside Gateway. RAG candidate isolated until retrieval/answerability/citation/latency gates pass.
**Spec:** `C:/Users/LUIM/.codex/attachments/27fb7d12-c166-484e-ba57-3601522f19dc/Pasted text.txt`.

Constraints: Project5 read-only; no replay391/385; no PR merge; zero paid usage; existing10RPM/175KTPM and30automation/min unchanged; max one new coding task (planning+coding correlated), schedulerOFF at end. No DR/master-key scope. UI lastresort; human login only, no policy bypass.

- [x] Inspect live images/queue/lease/actual workflows and missing CC callers.
- [x] WF08/09/10 strict Project6 routing with Native identity/approval tests; existing omitted scope unchanged.
- [x] Safe own-source WF14 failed-index→durable retry→receipt→citation; no MAIN vector outage/global fault patch.
- [x] Project6 Automation Status projection of16 workflows with last/current/success/error/correlation/links; safe host snapshot with freshness guards. Source: new workflow_status.py + Corepartial, root engineering.status wiring/collector.
- [ ] RAG extractive answerability candidate in isolated corpus, fresh independent label review packet/locked split, benchmark before deploy. Preserve source hash/span/ACL/version; abstain on insufficient evidence.
- [x] Fresh WorkIntake planning and exactly one new small feature after integration regression+build; unique persisted operation intent, no duplicateunit/WP/PR. Verify all actualroles/tests/GitHub/n8n/knowledge/reports and returnOFF.
- [x] Minimal relevant backups, copy-only immutable candidate images, clone qualification, serving source/pin parity and live read-back; no automaticDBrestore.
- [ ] Human UAT only for interactions not provenAPI; blockedtools do not block backendwork. Finalstatus+16Owneranswers with exact limits.

Review focus: cross-project target injection; untrustedURL/metadata XSS; stale/success status incorrectly overriding business refusal; unknown Native/GitHub write outcome; provider/retry/concurrency budgets. Each owner adds a targeted test at its trust boundary. Existing partly-untrackedsource is preserved in exact scoped snapshots; no git clean/reset/addall.
<!-- END_FUNCTIONAL_COMPLETION_27FB7D12 -->

# Final integration execution plan

Authority: Owner attachment `4b7b8932-ad30-4f03-80b7-e13bd09d6624`. Current MAIN is Gateway `3c065590`, Core `5936d90e`, n8n `05376355`; Project5 snapshot and minimal PG/SQLite backup are in `M0.json` / `native-before.json`. The earlier #391 is complete; never resume it.

1. **RAG:** inspect actual ingestion/search/source hygiene and prior failed experiments. Freeze an independently reviewed source-grounded evaluation split before retrieval scoring; isolate SQLite/Qdrant. Test a retrieval design that distinguishes candidate relevance from answer support, preserves project/actor/version ACL and can abstain. Report validation quality and actual latency; deploy only if the predeclared gates pass.
2. **Demo release:** map PR6–10 to exact base/head commits, build a separate integration candidate, verify Unicode/CSV including spreadsheet formula handling and existing database compatibility. Snapshot Demo SQLite, deploy an explicitly labelled unmerged integration build on port18791, verify read-only business responses and source SHA; preserve rollback. No merge of Owner-pending PRs.
3. **Workflow/event wiring:** inventory actual published definitions and producers, classify intentional human-triggered workflows versus broken event paths, and reuse the existing worker and durable outbox. Exercise real n8n clone and safe MAIN Project6 contracts, including idempotency, failure/recovery and source/read-back. Preserve manual approval boundaries.
4. **GitHub sync:** reconcile PR review/checks/branch/main/release states with existing durable Native journal, no second scheduler; confirm event correlation and UI/report projection. Test repeated sync and unknown external-write reconciliation.
5. **Qualify/deploy:** focused tests, bounded clone and integration tests, image/source parity, minimal prechange backups, idle/lease guards, incremental service rollout and actual read-back. Recheck Project5 fingerprints.
6. **UAT:** only after technical gates are met or remaining blockers are evidenced, use actual Computer Use on scoped local interfaces and record actions/results. Never claim `OWNER ACCEPTED`; no DR work in this phase.

Files/scripts are scoped by component under `integration-final/`, with final status, defects, RAG, workflow matrix, GitHub sync, test JSON, UAT guide and `FINAL_INTEGRATION_ACCEPTANCE.md` updated together. Any unresolved gate stays explicitly FAILED/PARTIAL, not hidden by active flags or HTTP200.

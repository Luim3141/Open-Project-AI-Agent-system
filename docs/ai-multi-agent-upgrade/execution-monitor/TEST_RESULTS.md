# Kiểm thử — evidence theo phương pháp

**COMPLETE_ON_STAGING — 2026-10-19T19:59:52.412347+07:00**. [Serving deployment report](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md);30publicUI/API checksPASS. Qualification evidence below records pre-deployment validation.

Windows regression196tests, Linux immutable candidate127tests, monitor-specific18tests. Xem JSON kết quả và image hash tương ứng trong run folder; không coi test mocks là Google live.

Unit/integration: graph single/multi/parallel; invalid DAG cycles/duplicates/missingdependency; receipts/modes/tokens/errors/retry; exact legacy parsing và ambiguous labels; missingtelemetry; event ordering/dedup/strictschema; actualrunning/failed/terminalinterrupted; ownhistory filters/pagination/SQL injection; crossactor/project; Native versionSTALE, revokeditem/membership; typedoutputscope; no provider calls khi repeatdetail/replay. Planning duration từ exact recorded events; reject raw error text.

Windows cover thêm host provisioning/local-runtime/n8n/knowledge/CC authorization. Linux subset chỉ module có trong image; attempted broader suites failed do host-only operator/prototype modules không ship trong image. Giữ diagnostic riêng, không ship obsolete prototype để làm xanh tests. Runtime final subset PASS; initial test-harness failures không bị gọi là product PASS.

Real Native API + real Rails/Gateway clone + saved live run phục vụ E2E; new generations là MockTransport synthetic, không live Google. Network fault injection được ghi riêng. Native businesswrites0. Backup/restore3SQLite và221PGtables/assets/config PASS. OldGateway opens additive schema PASS. Source-image-clone exact hashes; Native migrations unchanged.

File evidence: windows-regression.json,linux-regression.json,browser-e2e.json,instrumented-mock-success.json,instrumented-mock-failure.json,pagination-fixtures.json,pre-approval-backup.json,cold-sqlite-restore.json,postgres-assets-restore.json,rollback-compatibility.json,serving-preservation.json. Final E2E completion/status phải đọc JSON mới nhất; chưa được ghi READY nếu còn failedcheck.


Final qualification:196Windows/127Linux/18Monitor PASS;22browser+3extra PASS on exact final digests. Missing pending-receipt duration regression was RED(0!=None) before shared observed() fix and GREEN after; no duration invented.


Post-deployment acceptance: [STAGING_DEPLOYMENT_REPORT](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md). Exact servingpair456c38f6/7d76c1eb;30publicchecksPASS, ledger517unchanged. Ownerapproval61e1719f preserved; previewfile remains the immutable approved plan, not current deploymentstate.

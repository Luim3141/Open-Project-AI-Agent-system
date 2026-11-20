# Remaining development backlog

Original P00–P10/113task objects preserved. VERIFIED below refers to isolated qualification, except RD05metadata-only live reconciliation. Serving rollout owner-approved, applied and verified; see STAGING_DEPLOYMENT_REPORT.md.

## RD01 — P0 — VERIFIED / STAGING_DEPLOYED_VERIFIED

- Description: Review/reconcile42modules.
- Root cause: Old image/source drift; dev prototypes advertised as runtime.
- Source: gateway/, .dockerignore, RemainingGateway.Dockerfile.
- Dependencies: none.
- Implemented: Review/classify/retireunsafehelpers;build/hash/import.
- Tests/evidence: candidate-runtime-parity.json, final-frozen-regression.json.
- Remaining gates: G2liveGemini ownerblocked; TOTP notapproved;20-user deferred. Serving evidence: STAGING_DEPLOYMENT_REPORT.md.

## RD02 — P0 — VERIFIED / STAGING_DEPLOYED_VERIFIED

- Description: Multi-Agent application E2E.
- Root cause: Unwired classes and default/static assumptions.
- Source: service.py, store.py, ai_worker.py, supervisor.py, agent_*.
- Dependencies: RD01.
- Implemented: Existingqueue/worker,rolecontext,scopeNativeAPI,cancel/provenance/trace.
- Tests/evidence: MULTI_AGENT_E2E_REPORT.md, browser-uat-1792318734.json.
- Remaining gates: G2liveGemini ownerblocked; TOTP notapproved;20-user deferred. Serving evidence: STAGING_DEPLOYMENT_REPORT.md.

## RD03 — P0 — VERIFIED / STAGING_DEPLOYED_VERIFIED

- Description: Second Brain E2E.
- Root cause: Persistence/chunk/FTS/ACL lacked real route and restore proof.
- Source: knowledge_*,service.py,local_backup.py,check_backup_sqlite.py.
- Dependencies: RD01.
- Implemented: Actor-nativeingest/retrieve,WAL/FTS/dedup/restore.
- Tests/evidence: SECOND_BRAIN_E2E_REPORT.md, rollback-qualification.json.
- Remaining gates: G2liveGemini ownerblocked; TOTP notapproved;20-user deferred. Serving evidence: STAGING_DEPLOYMENT_REPORT.md.

## RD04 — P1 — VERIFIED / STAGING_DEPLOYED_VERIFIED

- Description: Control Center/frontend.
- Root cause: Fake/historicalmetrics,unpackagedviews,threads/paging/UIcontracts.
- Source: core/overlay/,stage.yml,control_center*,quota_panel.py.
- Dependencies: RD02,RD03.
- Implemented: ActualAPIdata,unknownmodelquota,plan/nativeinputlinks,10-rowUI,8threads.
- Tests/evidence: CONTROL_CENTER_COMPLETION_REPORT.md,control-center-final-qualified.json.
- Remaining gates: G2liveGemini ownerblocked; TOTP notapproved;20-user deferred. Serving evidence: STAGING_DEPLOYMENT_REPORT.md.

## RD05 — P1 — VERIFIED / STAGING_DEPLOYED_VERIFIED

- Description: Quick Tunnel reproducibility.
- Root cause: Manifest pointed vendor image instead of running wrapper.
- Source: QuickTunnel.Dockerfile,quick.stage.yml,provision_local_stage.py.
- Dependencies: independent.
- Implemented: Binary/script/RootFSrebuildparity;atomicmetadata-onlyrepair.
- Tests/evidence: quick-tunnel-reconciliation.json.
- Remaining gates: G2liveGemini ownerblocked; TOTP notapproved;20-user deferred. Serving evidence: STAGING_DEPLOYMENT_REPORT.md.

## RD06 — P0 — VERIFIED / STAGING_DEPLOYED_VERIFIED

- Description: Isolated qualification/UAT/readiness.
- Root cause: Candidate integration had no matching live-image proof.
- Source: tests/remaining_*,qualify_remaining.py,provision_local_stage.py.
- Dependencies: RD01..RD05.
- Implemented: Nativeclone+5newroles,actualEdge,backup/restore/rollback/app-onlypreview.
- Tests/evidence: ISOLATED_IMAGE_QUALIFICATION.md,UAT_TEST_RESULTS.csv.
- Remaining gates: G2liveGemini ownerblocked; TOTP notapproved;20-user deferred. Serving evidence: STAGING_DEPLOYMENT_REPORT.md.


## Checklist nghiệm thu candidate (không phải deploy)

- [x] RD01: source/implementation/tests/image evidence đã kiểm tra.
- [x] RD02: source/implementation/tests/image evidence đã kiểm tra.
- [x] RD03: source/implementation/tests/image evidence đã kiểm tra.
- [x] RD04: source/implementation/tests/image evidence đã kiểm tra.
- [x] RD05: source/implementation/tests/image evidence đã kiểm tra.
- [x] RD06: source/implementation/tests/image evidence đã kiểm tra.
- [x] Owner approved exact hash; app-only Staging rollout and power recovery verified.
- [x] Five real browser identities/UI and five real local Supervisor outputs verified; no Native business mutation.
- [ ] G2owner verification/liveGemini (chưa được phép chạy).

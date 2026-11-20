# WF11 — Native QA producer, design preview

Status: **NOT_IMPLEMENTED** alternative contract; no Native write or permission change authorized by this preview.

Current `QLDAPM_QA_EVIDENCE_V1` deliberately requires an actual Native attachment authored by the same QA who authored the manifest activity. Main QA23 currently has an advertised `addComment` link on test375v0, but no `addAttachment` or `update` link. Owner18 and PM19 advertise both. This is read-only discovery, not an attempted upload or a tested upload403. Evidence: `CODEX_WF11_QA_PRODUCER_CAPABILITY_RESULT.json`.

Keep V1 intact. Do not use an Owner attachment as QA proof, impersonate QA with a shared token, or grant broad `edit_work_packages` just to make a test pass.

The smallest proposed alternative is an explicitly versioned manual attestation manifest with a bounded UTF-8 test log embedded in the actual QA-authored Native activity. It would bind exact log bytes/SHA256, actual Native author/activity/time, current WP version, full Native AC lines and unique expected/actual/outcome cases. It must remain `MANUAL_ATTESTATION`, not automated test execution proof. Native activity readback/hash and fresh visibility must be checked before capture, independent human review and any separately approved transition. Unknown schemas and mixed inline/attachment fields must fail closed; V1 records/hashes must not change.

This alternative is not present in the current parser or UI and must not be sent to Main as if supported. Before implementation, add RED tests at the existing Service/HTTP seams for actual Native author/source binding, byte limits/hash, stale/edit/revoked access, incomplete coverage, self/model review and exact-hash replay. Qualify comment/version effects against an isolated Native integration, then deploy a narrowly scoped change with rollback. Any Main activity publication or transition requires a new exact proposal/hash human approval and a genuine QA statement/log; all earlier approvals are consumed.

The existing Core lifecycle requirements remain independent. On371v1, the next Native edge is NEW→IN ANALYSIS; Core currently rejects missing story, AC, scope evidence and scope approval. An accepted QA record does not fill those missing business records or authorize a jump to REVIEW. Automated trusted-runner receipts and full bug closure remain separate acceptance work.

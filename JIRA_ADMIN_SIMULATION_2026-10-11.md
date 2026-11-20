# QAG3 — named-owner simulation policy, 11/10/2026

## Status

**Deployed to the existing development environment, version 2.6.0.** Forge CLI completed with exit 0 / Deployed / version 2.6.0. Manifest SHA256: `837884a1f8829990d99ae9456c56cb1312745f649db8d8c8f6af768cb78c517e`.

Independent supplementary MCP `inspect_workflow(task)` read-back finds all 10 installed validator modules and the changed named-owner simulation descriptions. Task remains workflow v6; `inspect_scheme` confirms QAG3 still uses scheme10003. Deployment is not workflow activation or migration.

Owner explicitly requested admin QA and simulation self-approval. This is a scoped business-rule change, not permission to remove MCP confirmation/activation controls. Official MCP identity/resources/QAG3-2 verified; no browser used. Current owner: `712020:0d04982c-00bf-46af-b3a7-446d0f44edfb`; site `https://luimjiraqldapm.atlassian.net`; cloud `560ef0cc-d24b-4613-98d3-d541afe8f32b`.

## Changed policy

- Only QAG3. No site role/permission change and no grants to arbitrary administrators.
- Real Tester keeps the existing `Result: PASS` path.
- Named owner may use `Result: SIMULATED PASS` on Task/Subtask already labelled `qag3-simulation` before the transition. Fresh structured evidence, Testing source state, checklist and retest consistency remain required.
- Current-QA checks recognize that exact owner's simulated changelog event, not an assertion authored by someone else. Relevant edits/rework still invalidate evidence. Removing the simulation label blocks the simulation path.
- Named owner may approve their own labelled Subtask, including prior assignment, only with explicit simulated evidence. Development retains valid current QA evidence; business review requires fresh `Review result: SIMULATED ACCEPTED`.
- No automatic PASS, fake changelog, employee scores, worklogs, release or real product acceptance. Simulated evidence is never a real QA test report.
- Epic descendants-Done, exact scope, checklist, evidence, change reason, Resolution and workflow graph are untouched. Owner already belongs to the approved PM allowlist.

## Verification

Node predicate fixtures PASS, including owner simulation positive, wrong actor, inactive owner, missing old/current label, real-PASS disguise, stale evidence and self-review negatives. These are synthetic predicates, not transition E2E.

Registered supplementary MCP `inspect_expression_validation`: `allValid=true`, 10/10 Boolean, exact candidate hash; `jiraE2EVerified=false`. Forge lint: no issues. Python Jira regression/stdio: 94 tests PASS.

Read-only analyser accepts this one additional pinned hash and reports `sourceVariant=admin-simulation`; no write allowlist, approval, rollout-evidence or empty-project guard changed.

Post-deployment registered MCP `inspect_expression_runtime` evaluated all 10 modules against the existing committed QAG3-1/2/3 items as the actual owner: evaluationComplete=true, PM gate=true, remaining gates=false on unfinished backlog, no execution exception. This is not a positive simulation-transition test: pendingTransitionFieldsTested=false, jiraE2EVerified=false.

## Deployment / rollback

Target: existing Forge app development only, same 10 validator module keys, no function/storage/egress/API scope, new installation or billing change. No scheme association, issue transition, automation enable or monitor resume in this batch.

Before-policy source saved as `forge/qag3-validator/manifest.before-admin-simulation-2026-10-11.yml`. Rollback restores its content to the manifest, reruns fixtures/lint/type analysis and deploys the restored source through a separately reviewed change. Do not uninstall an app referenced by workflows.

## Remaining

Workflow activation/migration still needs a legitimate bounded qualification route and the applicable tool approvals. The new owner path resolves QA identity/self-review policy only; it does not claim unrestricted platform control or real Jira E2E. Monitor remains paused.

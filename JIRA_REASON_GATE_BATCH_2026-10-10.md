# QAG3 reason gates — approved, saved and MCP read-back VERIFIED

## Execution result

Owner answered **Duyệt lưu lô reason gates inactive** after preview. Fresh MCP versions matched all three before states. Browser admin fallback saved Task, then Epic, then Subtask; each was independently read back through mcp__qag3_admin__inspect_workflow before proceeding. Semantic assertions compared all statuses/layout/paths/actions/conditions and old validators, ignoring only volatile rule object IDs: exact approved additive diff PASS, no other configuration changes.

- Epic now v6/e9bfab73-dc0c-46b1-9304-f5520e12f9a7.
- Task now v5/cd076ba7-57ee-455a-813b-c70e40453171.
- Subtask now v5/1afd7884-4080-4cfc-9a59-f9b789c7edfd.
- Full read-back: jira-bot/qag3-reason-readback-2026-10-10.json.
- Saved proofs: jira-bot/qag3-reason-{epic,task,subtask}-saved-2026-10-10.png.
- inspect_scheme confirms QAG3 remains scheme10003. inspect_automation readComplete=true confirms only A01 DISABLED; A02–A05 absent. Workflows remain Inactive. No Jira issue transition or E2E executed.

The remaining sections describe the reviewed before/proposed batch, now applied. UI drafts are no longer pending; Update buttons disabled after save.

Route: official MCP preflight verified; browser admin fallback because transition-screen administration was not exposed by official MCP. Supplementary MCP read-back collected before and after each save. This is not an official MCP write.

## Exact proposed additions

| Workflow | Before | Transition | Additions |
| --- | --- | --- | --- |
| Epic 5079dd5a-c3a9-4049-a1d7-70c0acc6a365 | v5/ad587970-0156-4760-8a3c-a98a7811470c | Reopen8, Cancel Epic9, Restore10 | Show a screen10011 + installed QAG3 fresh change reason validator |
| Task 9f21c6fc-718d-4f3c-aca9-49ab9c89c899 | v4/3f2d44b0-a179-4149-995e-3e4219cfea7c | Reopen15 | Show a screen10010 + installed QAG3 fresh change reason validator |
| Subtask 7512e21c-34cd-4fc8-baf4-9398f36f3e37 | v4/5a32d28e-8c31-4883-ab57-2989421e45f7 | Reopen6 | Show a screen10010 + installed QAG3 fresh change reason validator |

Validator: existing expression-only development2.1.0 module qag3-fresh-change-reason. Requires Change reason10043 nonblank and different from originalIssue on this transition; entering a reason in an earlier edit alone will not pass. It checks submitted reason freshness, not truth of its content. No new app deployment/scopes/cost actions.

## Preservation and impact

Keep all existing statuses, layout, transition paths, validators, assignee routing, Resolution actions and native conditions. Epic Cancel/Restore and Task Reopen retain existing PM gates. Epic Reopen has no PM restriction in the verified before state; this batch does not add one, so automated reopen policy is not silently changed. The screens expose the existing fields, including Change reason; no field scheme/screen contents are changed.

Save inactive workflows only. No activation, migration329issues, issue values/Parent/assignee, A01–A05 enable, monitor resume or KAN/SAM1 writes. Each workflow save is separate, not an atomic three-workflow transaction; stop on a failure and reconcile, never blindly replay.

## Validation and rollback

88 local Python tests PASS and Node predicate fixtures PASS in this turn. These are not Jira expression-runtime tests or Jira E2E; no claim of Jira updateValidation errors=[] for this UI draft.

Before snapshot: jira-bot/qag3-reason-before-2026-10-10.json. Before saving, compare fresh MCP versions/semantic rules to these before states; changed versions require a new preview. After saving, inspect_workflow must confirm each expected screen and validator and preservation of old configuration. Rollback uses preserved before plus CURRENT version and separate preview/approval; no automatic rollback, no issue deletion or app uninstall.

Proof screenshots: jira-bot/qag3-reason-{epic,task,subtask}-draft-2026-10-10.png. Drafts reside in browser tabs until saved/discarded; this document is not a server-persisted workflow.

## Still blocking migration

Reviewer identity/revision-bound evidence, QA/retest truth and stale approval invalidation, Epic acceptance checklist/readiness, Subtask acceptance gates and real Jira gate/E2E/concurrency tests remain incomplete. Adding these reason gates does not resolve those requirements. A03 automated Epic reopen must be tested with this same-transition reason requirement; editing a reason first is not sufficient and no bypass is authorized. Keep A01 disabled and do not enable A02–A05 before this is resolved.

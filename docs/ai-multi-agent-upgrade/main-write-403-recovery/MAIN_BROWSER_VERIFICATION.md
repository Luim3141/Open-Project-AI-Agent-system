# Main browser verification — 21 October 2026

**MAIN_WRITE_AUTHORIZATION_FIXED_AND_CLONE_NATIVE_VERIFIED.** No new Gemini call and no Main WP creation. Owner's real PM19 session was used through Edge/CUA; no password, TOTP, cookie or session extraction/bypass. Main Native tokens were used only for read/form diagnostics.

| Check | Method and actual outcome | Status / evidence |
|---|---|---|
| Original failure | PM browser checked WRITE, blank scope, exact create-child prompt; generic403 displayed. Serving code + temporary Store + real Native PM identity returned internal403, no run. | Reproduced; main-before-403.png, runtime-reproduction.json |
| Fixed exact create admission | New serving Gateway code, valid signed request, temporary Store, dispatcher disabled, real PM19/parent50/QA23 Native reads; HTTP200, routine_writes_authorized=true, scope[50]. Temporary run is not a Main execution. | PASS; runtime-after-admission.json |
| Main browser checkbox path | Checked WRITE + `Đọc công việc 50` uses deterministic Native route, POST302, visible subject/description in run03961b61-bc6a-4437-874c-21d0874ee439, model_used=false. | PASS; main-checked-read.txt/png; final-evidence.json |
| Main read-only Multi-Agent | PM asks BA+QA about50 with local engine; BA/QA/Reviewer outputs visible, execution complete,17events and real Monitor timeline. Run23353d1f-fc42-402b-b1e9-722a1b5a9dd9; model_used=false. | PASS; main-local-supervisor-visible.txt/png, main-monitor-visible.txt/png |
| Native create permission | Main real Native form validates Subtask/type10/parent50/QA23, empty validationErrors after approved role grant. Form validation does not create a WP. | PASS_NO_CREATE; final-runtime-verification.json |
| Main proposal | Actual PM Native tool form creates one unapproved proposal for `test`, Subtask10, parent50, assignee23. Preview table and both Approve/Reject buttons visible. No model/NLG call. | PASS; main-proposal.png, main-proposal-visible.txt; main-owner-proposal.json |
| Actual Native writes | Chromium + real Rails/HMAC/worker + Native create/readback/approval/rejection on Main clone;2children, both within isolated clone. Provider explicitly mocked. Duplicate same request returns same run and no new child. | PASS; clone-browser-results.json, clone-native-create.png |
| Denials | Four non-PM roles denied403 on clone; invalid CSRF denied. Invalid HMAC/cross-project/actor forgery tested by ASGI/contract tests, not claimed as new five-role Main browser UAT. | PASS; focused-green.log, final-narrow-tests.log |
| Data/provider/isolation | Main329WP,7Sprints,7Versions, entire366-WP global table unchanged; assignees/dates/statuses/relations untouched. Existing20provider receipts/22usage reservations unchanged.16other servingcontainers retain IDs/images/starttimes. | PASS; final-runtime-verification.json, final-evidence.json |

Proposal: http://localhost:8088/projects/qldapm-local/qldapm-ai?proposal_id=5e651070-9dc0-42f8-90f9-5a3909c0925e

At final readback it is pending and expires **2026-10-21T23:21:04.726585+07:00**. Owner may review/approve manually. This work did not click Approve or create `test` on Main. After a later authorized create, expected project count becomes330; do not treat329 as immutable after that approved action. Expired proposals require a fresh explicit request; do not automatically replay.

## Limits and preserved risks

No live Gemini write/NLG validation was run because Owner forbids quota use for this incident. The free-only proof/model/key/billing configuration was not changed. Business write admission and real Native creation are proven separately by production-code admission and clone browser/Native tests. Direct routine writes use the existing Gemini business tools; the read-only specialist Supervisor is not represented as a mutation DAG.

Staging was not restarted/rebuilt/deployed. Its45/47 app files match its image; controller and WorkPackage navigation contain pre-existing hotpatches dated20October, before this incident. They were retained and are outside this fix. Source `/qldapm-core` is an operator mount, not the serving `/app` code; no activation was invoked. See stage-preexisting-code-drift.json.

Backup restored221tables equal and SQLite integrity passed. Main rollback uses immutable digests in release-preparation.json, not `latest`. No Docker Desktop restart, database migration, credentials/TOTP change, Main child create or whole-system regression/capacity test was performed.

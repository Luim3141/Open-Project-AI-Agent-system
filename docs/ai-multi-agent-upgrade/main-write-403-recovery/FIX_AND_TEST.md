# Main WRITE fix and qualification

## Qualified implementation

Exactly five production files changed; compare `source.diff` with private pre-edit snapshots and `release-preparation.json`:

- `gateway/service.py`: write intent/checkbox/scope use the existing business-tool worker; analysis-only Multi-Agent remains for read-only analysis. Infer IDs before routing and validate existing scope with fresh Native access. Non-PM create/update/transition is denied before provider admission.
- `gateway/ai_worker.py`: a new child's parent must be in the run's approved existing scope. Existing PM/native checks, source IDs, idempotent requests and UNKNOWN/no-replay behavior remain.
- Rails controller: strict positive-ID list, per-form stable request ID, actual Gateway HTTP status retained for command errors.
- `ai_bridge.rb`: bounded allowlisted error messages and typed HTTP error; local Supervisor policy denial is not described as service unavailability.
- Assistant view: stable request ID prevents double submit from generating another run; preserve scope input on validation errors.

No new write channel, tool, model, key, billing setting, schema or Supervisor implementation. Checkbox selects the pre-existing **direct routine-write** policy. With checkbox off, the business worker returns an actual proposal with preview/Approve/Reject. Local Supervisor remains advisory. This is not a newly implemented specialist-agent mutation DAG.

## Executed qualification

- `routing-red.log`: original routing failures reproduced; `routing-green.log`: four new routing tests PASS.
- `focused-green.log`:85 Windows test executions PASS; `linux-tests.log`:85 executions PASS on exact Gateway candidate, network disabled. These executions include imported fixture tests, not85 unique test methods.
- `security-followup.log`:27 follow-up executions PASS including foreign-parent rejection and forged actor denial. The fixture import was subsequently narrowed to avoid duplicate discovery; final narrow rerun recorded separately.
- `core-contract.json`:12 strict-scope cases and real Ruby typed-error contract PASS, network disabled.
- `clone-browser-results.json`:22 real Chromium/Rails/Native checks PASS with five existing synthetic accounts. Provider is explicitly `MOCK_PROVIDER_NATIVE_REAL`, not live Gemini. Direct child367 and a second approved child are created **only on clone**, parent50/QA23/type10. Clone329→331. Main writes0.
- Duplicate submits return the same run. Non-PM BA/BE/FE/QA write requests403. Invalid CSRF denied. Scope `2.5`422; local-Supervisor checkbox403 has a clear policy message. Read-only BA/QA/Reviewer graph5nodes is visible; browser console clean.
- Initial Linux harness lacked writable `/state`/disabled app bootstrap, clone startup used an unsupported entrypoint, and clone hostname was wrong. All were isolated harness errors and corrected; logs/containers retained. Initial Native parent denial was a real permission gap. A proposal test initially inspected before Turbo navigation completed; original failure retained, corrected wait and resumed the same proposal rather than recreating writes.

## Release scope authorized by Owner

Candidate Gateway `sha256:e57d07d58118d671352736fde1f20dda404b59db887c54ca7ef99a27e48d78ce`; web Core `sha256:5abec112e69971c9d9a58964fccf717a324a75b96b0d9f83fa7861f66eb7e449`.

Fresh private backup `backup.json`: all221 PostgreSQL tables restored equal to pre-backup snapshot on a **new isolated validation database**, SQLite integrity PASS. Provider/config/credentials saved privately. Assets are outside this code/RBAC change; no assets restore or Main database restore is performed.

Rollback Gateway `sha256:e30a3e3a7e616fa375dd40c0e4c1cb18a34692c3f0eb62b6cfa78bd1f88b6108`; rollback Core `sha256:bbef2e6e6bc3a9e215cb24b96cd046dda356703dda0a0d21924975461e6fc562` captures all47 files actually in serving web, including Gemini's copied controller. Do not use `latest` or reset Git. Restore the privately saved image env/lock values and recreate only Gateway/web if rollback is needed; do not restore business DB for an application rollback.

Owner separately approved exactly role22 +`manage_subtasks`, **no Main Subtask creation**; original preview hash and answer are in `owner-approval.json`. Recheck sole membership PM19/project5 and exact permission diff before apply.

Stage has a read-only *operator source* mount `/qldapm-core`; its serving application uses independent regular `/app` files. The current controller hashes differ, with no symlink, no runtime load from `/qldapm-core` in application config. No Stage activation/test/rebuild/restart is run. Final verification must compare actual `/app` hashes plus serving IDs/images/start times. Main worker/cron, DB, n8n and Quick Tunnel are outside deployment scope.

## Runtime outcome

Pending controlled apply and Main browser verification. Health alone is not acceptance. No Google call or direct Main create is authorized for this incident.


## Final runtime outcome

DEPLOYED_AND_VERIFIED_WITH_EXPLICIT_LIVE_PROVIDER_LIMIT. Main Gatewaye57d07d5/web5abec112 healthy;53Gateway+47Core file hashes match qualified source. Only these two serving services recreated. Owner-approved role22 gains solely manage_subtasks; no membership/other permission removed, no WP create. Backup221-table restore and protected-state readback PASS. Final8narrow regression tests PASS after eliminating duplicate fixture discovery; no production-source change after image qualification. Main browser visible Native result, BA/QA/Reviewer result+Monitor and unapproved create proposal PASS. See MAIN_BROWSER_VERIFICATION.md for exact methods and live-call limits.

Staging image parity check initially failed on two pre-existing hotpatches dated20October; evidence preserved rather than overwriting them or claiming47/47 parity.45matchimage,2oldpatchesretained;16unrelatedservingcontainers unchanged. Initial deploy preflight incorrectly compared the global WP table count to329; readback proved366global/329project5 and unchanged whole-table hash. Guard corrected to distinguish both scopes before any serving mutation. No test expectation was changed to permit a data difference.

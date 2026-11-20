# UAT plan — five actual roles, Staging only

Use UAT_TEST_RESULTS.csv as executable scenario list: Preconditions, Steps, Expected, Actual, Status, Evidence and Defect ID. Only real executed results may become PASS. Stop on authentication failure; do not reset account, rotate key or bypass identity. No Main fixture/mutation; no fake20-user acceptance.

## Data and execution order

1. Baseline native project3 qldapm-local;335 real work packages. Existing read-only data is permitted. Independent browser contexts for PM7, BA-PM6, BE8, FE9, QA10. Private saved native passwords plus saved TOTP, never logs/HAR/trace/login screenshots. Read login→2FA→users/me→visible Work Packages→Assistant→admin-denial→logout. Desktop1280x800, PM mobile390x844; capture authenticated non-secret UI only.
2. Owner first approves exactly one small Staging fixture scope (type/parent/title/assignee/allowed transitions) before PM create/assign/status/proposal/comment tests. Do not create bulk fixtures. Never delete cleanup data without scoped authorization; mark fixture clearly and preserve receipt. Approval and rejection are separate scenarios.
3. PM: hierarchy Epic→Task→Subtask, assignee, allowed/invalid workflow transition, backlog/sprint, dashboard, proposal before/after/hash/reject/approve, native read-back and audit. All writes need approved fixture.
4. BA: assigned work, requirement/AC analysis, scoped knowledge citation, allowed comment/report, deny approval outside role. FE/BE: assigned task/details/comments, technical draft, no admin/operator/PM credential exposure. QA: AC/test draft, report/comment, no self-approval or claim draft tests executed. Comment is a business mutation and also waits for fixture approval.
5. Multi-Agent: real UI request→Gateway→Supervisor→specialist→cited output→proposal/report→UI→durable audit. Verify context actor/project isolation and native revision; no operator tool. Current runtime integration blocker must close before this scenario. Offline mock tests remain separate.
6. Second Brain: approved native fixture indexed twice, dedup, source/native-version citation, PM-only doc denied to FE, cross-project deny, no secrets. Restart only private clone with separate volume and verify hashes; do not restart serving Gateway for convenience.
7. n8n: inspect actual schedule versus manual/startup triggers; match execution→request_key→run_id→actor/day snapshots. Current-day repeats retain one receipt and five snapshots. HMAC/replay faults only isolated clone. No new production trigger needed to prove existing history.
8. Remote: current public HTTPS native login and2FA, session isolation; internal Gateway/n8n/DB and secret paths unavailable. Actual5 people/devices remain PENDING_MANUAL_UAT. Desktop3cycles require explicit owner window; no Quick Tunnel fault/restart under old approval.

Provider smoke is separate and bounded only after required Free-only authorization/eligibility; current audit makes zero live model calls. G2 billing verification remains blocked as requested. G7 capacity20 remains DEFERRED_BY_OWNER, not a prerequisite for basic five-role UAT. No automatic Main release.

# Verified issues and priorities

| ID | Severity | Evidence / user impact | Action / status |
|---|---|---|---|
| TK-01 / DEF-08 | CRITICAL | Old TOTP23–28 active/default;35–40 absent; historically exposed keys still match saved credentials; public login remains reachable | OPEN, owner approval required for new rotation. No automatic rotation. See SECURITY_REMEDIATION_PREVIEW.md |
| TK-02 | BLOCKER |35 missing runtime Gateway modules;7 differ; Core Control Center absent; no business Supervisor caller; no deployed knowledge retrieval | OPEN. Minimal vertical integration on private clone, then staging qualification; do not simply copy all files or count module tests as live proof |
| TK-03 | HIGH | Source Control Center returned200 even after native membership revoked/role changed/outage | FIXED_SOURCE_ONLY; before3FAIL/after25PASS. Deploy only with qualified pair; existing running image does not contain endpoint |
| TK-04 | HIGH | Candidate live vs original cloudflared saved in runtime manifest; repair may refuse/mis-reconcile | OPEN. Preserve current service; reconcile immutable image + provisioner + saved manifest with readonly validation before any recreate |
| TK-05 | HIGH | Historical113DONE includes P10 main-release/3Desktopcycles without matching operational acceptance; HEAD covers two JSON only | OPEN evidence/reproducibility gate. Preserve history and use separate reconciliation layer; no approval token from a unit fixture counts as owner approval |
| TK-06 | MEDIUM | n8n report hardcodes execution18 NEW; DB origin and history show execution8 | Corrected in takeover. Retire old report generator until it derives provenance from history rather than IDs; no data fix needed |
| TK-07 | MEDIUM | Copied credential file has stale passwords for BA-PM/BE/QA/stage-owner; native original passwords for5members remain valid | Workaround verified: reuse private stage/accounts.json in UAT. No native password reset or silent credential overwrite |
| TK-08 | MEDIUM | Quota panel source defaults to different models, uses native project ID where Gemini ledger project differs, hides query errors as zero | OPEN before deployment. Bind to actual validated provider policy/ledger; return unknown on unavailable telemetry; no paid/model change |
| TK-09 | LOW / UX | Browser records authentication-related page errors around navigation/logout; mobile PM has no horizontal overflow | Keep evidence, identify lifecycle origin before claiming console-clean. Initial PM hidden-link selector fixed in test harness; first attempt retained |

G2 remains BLOCKED_OWNER_VERIFICATION; G7 DEFERRED_BY_OWNER. Neither old PASS prose nor all-file hash matches close these gates. No evidence of a Main business mutation in this takeover. Native project3 count remains335; other projects14+23=372 total; do not confuse project and database counts.

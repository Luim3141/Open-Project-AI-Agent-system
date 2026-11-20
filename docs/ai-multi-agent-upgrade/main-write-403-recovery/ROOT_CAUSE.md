**FINAL: fixed on Main; approved permission applied. The BLOCKED preview below is historical; exact approved bytes are in owner-approved-preview.txt. See MAIN_BROWSER_VERIFICATION.md for evidence and limits.**

# Main WRITE 403 — current incident, 21 October 2026

## Confirmed causes

1. **Routing defect, not PM authentication.** Main Gateway `e30a3e3a…` runs native/project5 with `multi_agent.enabled=true`. `Service.start_run` selected the analysis-only Supervisor before inferring write scope, then rejected `allow_routine_writes=true` with HTTP403 `SUPERVISOR_READ_ONLY_EXPLICIT_IDS_REQUIRED`. No run existed at this point. This is POST `/internal/ui` behind Rails POST `/projects/qldapm-local/qldapm-ai/commands`, not Monitor GET polling or Native apply. `AiBridge` hid the reason behind a generic Gateway message.
2. **Separate Native permission gap.** Main role22 `QLDAPM PM` lacks `manage_subtasks`. Native form POST `/api/v3/projects/5/work_packages/form` returns HTTP200 with `validationErrors.parent.errorIdentifier=…PropertyIsReadOnly`. `add_work_packages` and `edit_work_packages` alone do not authorize setting parent. The PM ceiling already permits `manage_subtasks`; the actual role grant is absent.

Evidence: `runtime-before.json`, `runtime-reproduction.json`, `native-permission-before.json`, `main-before-403.png`, `main-before-visible.txt`, structured request logs. Temporary-Store reproduction uses the actual serving image plus real Native read-only PM19 identity: exact response403 above, zero runs, zero Google calls. Browser PM reproduced the same error. Existing audit links actor19/start_ai_run/PermissionError to transport403 within milliseconds; historical run/trace IDs are null because enqueue was never reached. No fabricated trace ID is assigned.

Main parent50 is a visible Task. Native role resolution identifies QA23. Before any mutation, no child named `test` exists under50; Main has329 WP. No new Main child has been created by this incident work.

The scope parser correctly recognizes `task 50` rather than the creation quantity1. The optional scope input's `scan(/\d+/)` was overpermissive for `-50`, `2.5` and prose/dates; candidate accepts only a positive-ID list. HMAC, authenticated actor binding, CSRF, PM-only-write, Native gates, model/key/billing settings remain authoritative.

## Concrete Owner approval preview — Native permission only

**Status: BLOCKED_OWNER_APPROVAL. Do not apply on Main without a new answer.**

- Target: Main PostgreSQL via Native Rails `Role` model, role22 `QLDAPM PM`.
- Exact delta: add **one** permission `manage_subtasks`; retain every other permission.
- Current blast radius, read-only verified: only User19, Project5 uses role22. Recheck immediately before apply; stop if membership or role permissions drift.
- No account/password/TOTP/API token change, no new membership/role, no non-PM grant, no Stage change, no restart required.
- Product behavior: PM can set parent when creating a Subtask through the existing Native form/approval tool. Gateway and Native PM ceilings remain in effect.
- Validation already performed on the isolated Main clone: missing permission reproduced; adding exactly this permission allows Native creation of Subtask367, parent50, assignee23, type10. Duplicate submit returns the same run and does not create another child. Provider is an explicit offline test double; Native API, Rails, HMAC, worker and browser are real.
- Rollback: restore role22's exact saved pre-change permission list through `Role#permissions=`/`save!`, after asserting the only difference is `manage_subtasks`; preserve all other role rows/memberships. Recheck Native form rejects parent again. This does not delete any WP created under later explicit approval.
- Before apply: fresh private backup, exact permission/membership readback, no Main WP mutation. After apply: Native form validation only; keep a proposal for Owner review. **Do not create a Main Subtask as part of this permission approval.**

Approval of application deployment in the Owner's incident request covers the qualified Gateway + Main web fix. It does not imply approval to alter real RBAC or create a Main child. Those actions are separately bounded here.


## Final readback — 23:09+07

Owner approved the exact preview above; permission applied and Native form now has no validation errors. The preview BLOCKED status is historical, not an outstanding approval. Exact approved bytes/hash are retained in `owner-approved-preview.txt` / `owner-approval.json`; do not apply the permission again.

Serving Main now uses qualified Gatewaye57d07d5/Core5abec112. Actual Main PM19 request with checked consent and Native read succeeds; the exact natural-language create admission also returns200 with inferred scope[50] on a temporary Store using the new serving image and real Native PM19 identity, without executing a provider or Main queue. Native create is real on clone; no Main child was created. See `MAIN_BROWSER_VERIFICATION.md` for limits.

Historical transport correlation: Gateway actor19 start_ai_run PermissionError at Unix1792595808.3268, transport403 at1792595808.3618; Rails request45e58390-2b99-46cc-8838-4ce7ad9d05f7 POSTcommands completed15:16:52.811Z with422/duration4697.61ms. Its request interval contains the Gateway denial. Browser displayed the generic403 text, but Rails outer response could be422; the denial originated at Gateway. No fabricated HMAC clock-drift cause is assigned. Copying a controller into a production container is not proof the running Rails process reloaded it; the new web image was qualified and recreated.

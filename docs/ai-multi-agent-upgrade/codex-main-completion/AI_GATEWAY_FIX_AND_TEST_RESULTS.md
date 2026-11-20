# Main Gateway fix and current verification — 21/10/2026

**DEPLOYED_AND_MAIN_PM_UI_VERIFIED** for the identified Native mode and missing POST dashboard context defects. Historical403 request arguments were not logged; its exact original consent flags remain unknown.

Main Core dde3c32e… deployed to web/worker/cron; Gateway456c38f6… unchanged image with native mode. Separate approved Main Native API enrollment21/22/23 is complete. No RBAC/HMAC/CSRF/MFA relaxation. See `main-application-deployment.json`, `native-enrollment-result.json` and `AI_GATEWAY_403_ROOT_CAUSE.md` (its20Oct candidate section is historical).

| Evidence | Method | Result |
|---|---|---|
|19Windows +19Linux Gateway/business-mode checks | Actual Gateway modules with isolated synthetic Native fixtures, no Google | PASS |
|6controller tests /31assertions | Actual Core Ruby, synthetic bridge/base | PASS |
|3Rails controller/view cases /37assertions | Real Rails and cloned Main DB, bridge fixture | PASS |
|42valid +42wrong-role gate edges | Native gate policy qualification | PASS |
|24BA/BE/FE/QA browser/native checks | Isolated clone, synthetic Native logins/TOTP | PASS |
| PM Main identity POST +context | Owner's real existing Native session, actual Main services | PASS; receipt/status and329dashboard retained |
| PM Main Supervisor readonly → UI/Monitor | Actual Main local deterministic execution | PASS;1run,4nodes,14events, PM+Reviewer;0business writes |
| Main provider smoke | Actual Google endpoint, specifically approved fixed public text | PASS;1countTokens +1generateContent; QLDAPM_OK;24total tokens;0retries |

Provider smoke is connectivity evidence, not a full Gemini multi-agent UAT. Main BA/BE/FE/QA browser sessions and Main live specialist orchestration remain unverified. Native API identity for all5roles passed. No history import or schedule/status update has occurred.

`main-browser-uat-readback.json` confirms Main work_packages/members/member_roles/roles/role_permissions/relations unchanged relative to predeployment backup after the local UI UAT. Later smoke only changed Main local provider usage/readiness state. Serving containers were not restarted for this UAT or smoke.

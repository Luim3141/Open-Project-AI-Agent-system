# Main Gateway403 — investigation and confirmed reproduction

20 Oct 2026. Status: CONFIGURATION_DEFECT_REPRODUCED; candidate only.

Actual Main GET Assistant in the Owner's existing native PM session succeeds: Gateway authenticated,329visible work packages, Control Center registry, empty history. Native identity POST also succeeds. HMAC/DNS/project/actor authentication therefore works for these observed requests; health alone was not used as proof.

Historical failure: native request `de65879a-0db5-4a68-93f1-d7440c3ae500`, `2026-10-20T13:47:14.214286Z`, POST `/projects/qldapm-local/qldapm-ai/commands`, QldapmAIController#command, user19, Rails422. Gateway audit `3ae441b6-114c-4a9b-b696-4f2c507bb366` records start_ai_run PermissionError; transport audit `c2976505-be8b-4fa6-bad0-3ffe42147071` records403 at `/internal/ui`. A failed start has no run/correlation receipt; these audit IDs are not falsely presented as a shared correlation ID. Old request consent/engine arguments were not persisted, so exact original triggering input remains unverified.

Main config omits gateway_mode; Service defaults to strict. Staging uses native. Reproduction through actual Gateway middleware/HMAC/Service with isolated SQLite and synthetic Native identities yields403 `RUN_WRITE_CONSENT_REQUIRES_NATIVE_MODE_AND_BOOLEAN` for a readonly count request with checked consent. Native config returns200 and no provider call. Strict also allows operator actions past policy (subsequent argument validation409), while native denies all five sandbox tools403. Changing identity, keys or RBAC would be the wrong fix.

Separate confirmed UI defect: command/confirm render show without assigning connection/dashboard/control_center. Even successful identity renders “Chưa tải được Control Center”. Candidate common readonly context loader fixes success and failure; failure refresh never resubmits the command and never hides its result. Real browser before evidence: pm-identity-post-before.txt/png. Four targeted controller tests fail before patch and pass after.

Separate provider readiness gap: Main has no saved Gemini enrollment or provider proof/environment. No live call was attempted. Moving to native does not create Gemini readiness. Missing BE/FE/QA Native credentials are another independent blocker, requiring the separate credential preview approval. Main empty monitor is consistent with zero actual AI/agent runs, not a fabricated UI failure.

Next gates: clone Rails/browser qualification, security/rollback, fresh backup, targeted Main apply, authenticated readonly post-deploy UAT. Do not claim historical403 fully fixed on Main before applying and verifying.

# Main AI credential readiness — preview, 20 Oct 2026

Runtime evidence: `runtime-baseline.json`. No credential change applied.

Main native identities were verified read-only in PostgreSQL: ba-pm/19 = PM, pm/20 = BA, be/21 = BE, fe/22 = FE, qa/23 = QA; op-owner/18 has no project membership. PM now has active TOTP; old onboarding reports are stale.

Main Gateway credentials.json contains actors 19 and 20 only. Actors 21–23 lack the dedicated native API credentials required by Service.native_actor. Configuring a role without its own native token does not authorize the Gateway to impersonate that user.

Main has no gemini.key, gemini.json, QLDAPM_AI_ENVIRONMENT or QLDAPM_GEMINI_FREE_PROOF. Staging has its own key and saved FREE_ONLY policy. Main must remain provider-blocked until an explicitly authorized Main enrollment reuses the existing key and policy without changing model, quota or billing. A production-target consent/policy is required by the existing adapter; a Staging proof alone does not enable production.

## Proposed credential operation, requiring separate Owner approval

1. Create exactly one native API token for each Main account be/21, fe/22 and qa/23 using the existing native token mechanism. Preserve all existing tokens, password hashes, TOTP devices, memberships and permissions. Store tokens only in the private Main Gateway credential store, never copy Staging tokens. Verify `/api/v3/users/me` and native role for each token without printing it.
2. Enroll Main for the existing Gemini key/model and verified FREE_ONLY limits (15 RPM, 250000 TPM, 500 RPD). Reuse the same saved key; do not rotate it. Save a separately scoped Main configuration/policy and retain independent Main usage/audit storage. No paid fallback, billing, new model, public access, or provider request is included.

Rollback: revoke only the newly created tokens after validating their exact native IDs; restore the previous Main credential file from the private backup; restore previous provider files/config. Never roll back the whole database or overwrite Staging state. Capture file hashes and IDs privately before apply. A real Gemini call still needs its own minimal smoke approval.

Application/controller fixes, config qualification, history inventory and Native Boards/Gantt work continue independently of this approval.

# P00-04 — Secret/config inventory (no secret values)

Observed 15/10/2026 via host file presence and Docker metadata. `P00-runtime-before.json` contains environment variable **names only**, model/project/tier metadata and user/role IDs. No API keys, native tokens, password, TOTP, raw Docker inspect or prompt text exported.

| Name/file | Type/source | Main | Staging |
|---|---|---|---|
| POSTGRES_PASSWORD / DATABASE_URL | Private `.env` -> DB/core environment | Present | Present |
| SECRET_KEY_BASE | Private `.env` -> core environment | Present | Present |
| credentials.json | Private per-native-user credential store -> `/state` | Present | Present |
| ui.key | Signed native UI bridge key | Present | Present |
| gemini.key | Persisted backend API key -> private `stage-ai` | Missing | Present, retained byte-identical |
| gemini.json | Persisted provider enabled/model | No enrollment | OFF after explicit new Free-only requirement |
| QLDAPM_GEMINI_FREE_PROOF | Readonly policy bind mount | Absent | Present |
| operator approval/test-receipt keys | Host-only operator or narrowly mounted receipt key | Existing boundary preserved | Existing boundary preserved |

Existing provider project `gen-lang-client-0020540057`, model `gemini-3.5-flash-lite`. Historical proof claimed Free/no billing/15RPM/250000TPM/500RPD, but continuous authorization permits billing and bypasses normal freshness. This is **historical metadata**, not current quota verification. New Free-only request supersedes that authorization.

Fresh read-only browser observation: exact project listed under the existing QLDAPM Google account in AI Studio with **Free tier**, account shows PRO separately. No API-key page opened, key changed, project created/imported, billing setup or inference submitted. Model has a Free option in [official pricing](https://ai.google.dev/gemini-api/docs/pricing); account-specific limits still require current AI Studio readback. PRO is not API quota evidence.

Mitigation actually executed: verified no active/unknown jobs or running AI, stopped only staging gateway, made byte-verified private snapshot of entire stage-ai (SQLite including available sidecars/config/credentials/key), called existing `free_tier_staging.py disable`, restarted same container/image. **Only gemini.json changed**; key/credentials/SQLite/config unchanged while stopped. Running container `Gemini.settings()` raises ProviderError before outbound network. Evidence `P00-04-provider-off.json`. Native UI/deterministic tools retained; no paid request or provider smoke made.

Do not restore historical enabled/cost consent as an automatic rollback. Re-enable requires Free-only implementation/current eligibility and privacy verification. Secret presence is not key-validity proof.

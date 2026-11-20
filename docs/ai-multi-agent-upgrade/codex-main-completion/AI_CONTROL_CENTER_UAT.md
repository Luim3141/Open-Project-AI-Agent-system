# Control Center — current Main verification 21/10/2026

**PASS: Main authenticated PM read and readonly POST context.** Source/runtime app fix was deployed before this verification. `MAIN_FULL_BROWSER_UAT.md` and `main-identity-post-verified.txt/png` contain actual Main browser evidence.

The UI shows Gateway ok, Native authenticated, mode native,329readable items, configured agents supervisor/pm/ba/dev/qa/reviewer, saved model and15RPM/250000TPM/500RPD. It distinguishes saved policy from live provider verification and states billing has not been checked directly. Daily Brief absent is a legitimate empty state; no hidden provider call was used to populate it.

After one readonly Supervisor submission, history displayed1COMPLETED run belonging to PM19/project5 and linked to the actual graph. That local run used0Gemini calls. Subsequently the separately approved connectivity smoke made exactly2HTTPrequests/24tokens and produced a fresh Mainreadiness receipt. ControlCenter nowshowsREADY and2local dailyreservations (`main-control-center-post-smoke.txt/png`); providerreceipts for agentexecutions remain0. Configured registry, completed local agents, provider connectivity and full liveSupervisor are separate acceptance dimensions; full GeminiSupervisor remains **AWAITING_SEPARATE_APPROVAL**.

No passwords, TOTP, credentials, Main membership, roles or native gates changed during browser UAT. BA/BE/FE/QA Main browser onboarding is not claimed; their current Native API identities and isolated clone browser checks are recorded separately.

MainDailyBrief is not configured end-to-end: private MainGateway state lacks `automation.key`, its automation/DailyBrief tables are empty. Existing n8n is Stage-bound with its own machineauthority; do not reuse its credential or route it to Main. A Main-only enrollment/workflow requires scoped qualification and approval of the new machinecredential, not a database copy or a hidden provider call.

# Vận hành Phase2 continuation

Current scope/status: FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Workspace `D:\AI project\QLDAPM chat`. Current image/backup authority deployment.json; app release demo-service.json, head def9d0a8852af42a407bd42fb0051615a2de9331. No active engineering runs; OFF, gateinactive. No UAT/browser/computer use requested.

## Start / read status without inference

```powershell
Set-Location -LiteralPath 'D:\AI project\QLDAPM chat'
$env:PYTHONPATH='openproject/ai'
Start-ScheduledTask -TaskName QLDAPMEngineeringDelivery
Get-ScheduledTask -TaskName QLDAPMEngineeringDelivery
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('status'))"
wsl -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/local/bin/openclaw gateway health --json
```

OpenProject18088, Gateway18089, n8n5679, OpenClaw18789, root gate18890, app18791. Task is hidden/current user/IgnoreNew, boots only this distro and polls existing queue;10s liveness pulse has no model calls. Agent heartbeat0m, cron and autonomous workshop off. New job requires authorized explicit admission; OFF does not stop shared QLDAPM services.

## Product controls

Project6 Engineering page: /projects/ai-dev-demo/qldapm-ai. Controls are wired to engineering_plan, engineering_run_once, engineering_control, engineering_cancel, engineering_resume. Existing Execution Monitor routes are enabled for Project6 PM and use fresh Native ACL/owned run scope. UI acceptance is deferred.

PM/BA plan reads current #379 version; optional explicit feedback creates one scoped unit/Native child. Existing delivered units are reused. New feedback uses latest verified unit/head, not old main; pending feedback cannot silently fork a stale parallel delivery. Catalog budget12units is bounded; extending scope requires explicit contract work. Planning has two bounded model turns and retains successful candidate outputs.

```powershell
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('control',mode='AUTO'))"
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('control',mode='PAUSED'))"
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('control',mode='OFF'))"
```

OS operator supports `cancel(run_id=...)`, `resume(run_id=...,checkpoint_version=...)`; get version from status. Resume uses same run and verifies current source/known terminal outcome. Agent CLI is polled; pause/cancel closes transport and fences Gateway at bounded boundary. Journal keeps completed context/Dev/review/QA/commit/push/PR/Native/RAG steps. Git commit/push/PR readback prevents duplicates; Native done receipts are reused. Rejected4xx receipts remain recorded; unknown/pending writes cannot replay. Own published source version is accepted only with exact completed Native receipt, current version and description match. External edit still blocks resume.

## Model / persona / skills

One WSL2 OpenClawGateway, Ubuntu24.04; private Node24.22.2 and OpenClaw2026.10.8. Windows Node unchanged. Original installer Node24.19.0 engine failure/rollback logs retained in %APPDATA%/OpenClawTray/Logs/Setup. Do not rerun Windows installer/unregister distro/global WSL shutdown. Only demo repository is mounted; interop/drive automount remain disabled; ext4 worktrees avoid prior drvfs publish problems.

Gemini google/gemini-3.5-flash-lite, no fallback. Real key root-only /root/.qldapm-openclaw/google-key; OpenClaw has local gate token only. Never print auth/.env/config secrets. Shared13RPM/450RPD/225000TPM policy unchanged; bounded wait75s, role allowances12/5/5,3rework passes,5explicit recoveries. Local allowance exhaustion can appear as sign-in error; inspect transport/CLI meta before changing credentials. Costs are provider-reported, not billing-console certification.

PM/BA actual system prompt loads engineering_personas + planning skill. OpenClaw root-owned AGENTS/SOUL contains selected persona and skill procedure; per-role contextInjection=always and final skill allowlist. fs.workspaceOnly remains true; sequential sessions share scoped app cwd and host switches persona before each session. Verify *skill-activation.json and trajectory skills_read, not file existence alone. Original default contextInjection=never remains outside these entries.

## Artifacts / source / app recovery

Run source/evidence: runs/<run-id>/delivery-steps.json, history/, *trajectory.jsonl, *transport.json, *skill-activation.json and JUnit. Root templates /opt/qldapm/agents/<unit>/<role>. Existing SQLite/FTS5/Qdrant/Ollama BGE-M3 remains the shared project knowledge; OpenClaw memory is session context only. New Native plans/results have actual RAG readback. n8n16unchanged; existing WF04 reads owned Project6 trace, not programming commands.

App service qldapm-mini-task-manager.service, data `/home/openclaw/engineering/demo-data/tasks.sqlite`; release `/home/openclaw/engineering/releases/def9d0a8852af42a407bd42fb0051615a2de9331`. Source Windows repo D:/AI project/QLDAPM-demo/mini-task-manager ready branch matches commit. X-QLDAPM-Revision header and normalized-source comparison verify serving revision; Git's existing archive CRLF conversion is recorded in verification hashes. Do not reset application data.

Explicit versioned promotion/rollback to a verified run (OFF/no active job required):

```powershell
& 'openproject/ai/.venv/Scripts/python.exe' -B -m automation.engineering_demo --update-run 3066ed0b-fadb-47c8-8d31-349590b3301b
```

Use an older successful run ID for app rollback; same datafile remains. Main rollback uses exact prior image/config from deployment.json/private continuation backup; restore only Gateway/Core web configuration, no automatic business DB restore. Live SQLite belongs to Linux: never open its bind-mounted WAL/SHM with Windows sqlite3 or delete sidecars. No volume deletion/history rewriting.

Current PRs remain stacked/open; merge is separate authorization. If later approved, merge PR1 first, retarget PR2 to main, review/merge, then retarget each next PR to main after its predecessor merge. Do not confuse deployed feature head with main branch content.

## Handoff

Update state/journal/evidence and run engineering_checkpoint.py after meaningful work. Current source snapshot/manifest is in state.code_snapshot; previous39file snapshot remains baseline only. MAIN source is uncommitted, existing untracked preserved. engineering_finalize_handoff baseline helper is blocked after continuation; use engineering_finalize_continuation only with current successful verification, and never to claim UAT. Physical Windows logon/reboot trigger remains unexercised; regular manual TaskScheduler start/idle is verified.

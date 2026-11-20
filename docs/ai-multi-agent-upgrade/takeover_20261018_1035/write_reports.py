"""Render this takeover's reports from observed evidence; never edits historical audit runs."""
import csv
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]

def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
def write(name,content):(OUT/name).write_text(content.strip()+'\n',encoding='utf-8')

def main():
    browser=read('browser-uat-native-accounts.json')
    assert browser.get('finished_at'), 'WAIT_FOR_BROWSER_TERMINAL_RESULT'
    git=read('git-summary.json'); runtime=read('runtime.json'); gw=read('gateway-storage-and-parity.json')
    url=read('http-probes.json')['current_url']
    rows=[]
    fields=['Test ID','Role','Module','Preconditions','Steps','Expected','Actual','Status','Evidence','Defect ID']
    for account in browser['accounts']:
        for test in account['checks']:
            name=test['name'];ident=f"WEB-{account['login']}-{name}"
            rows.append(dict(zip(fields,[ident,account['login'],'Browser / Native / AI UI',
                'Staging; saved native password verified read-only; existing TOTP; isolated browser context',
                name.replace('_',' '),'Control Center present' if name=='control_center_live' else 'Authenticated native UI and role boundary behave as asserted',
                json.dumps(test.get('actual',{}),ensure_ascii=False),test['status'],'browser-uat-native-accounts.json',
                'TK-02' if name=='control_center_live' else ''])))
    def add(ident,module,steps,expected,actual,status,evidence,defect='',role='Operator'):
        rows.append(dict(zip(fields,[ident,role,module,'Read-only Staging / saved evidence',steps,expected,actual,status,evidence,defect])))
    add('REC-TOTP','TOTP','SELECT devices + compare saved keys in read-only Rails transaction','Old 23–28 disabled; new 35–40 active/default',
        'Old devices still active/default; new IDs absent; stage-owner is user 5, not 13','FAIL','totp-key-readonly-check.json','TK-01')
    add('REC-N8N','n8n','Read execution history and correlate exact run_id/date/receipt','Same-day receipts reused without duplicate actor snapshots',
        'Origin execution 8; 18/19/20 reuse; one receipt + five snapshots, model_calls=0','PASS','n8n-history.json')
    add('REC-SCHEDULE','n8n','Read saved execution 23 trigger node and timestamp','Actual scheduled trigger at 09:00 Asia/Bangkok',
        'Execution 23; Daily 09:00; mode trigger; 2026-10-18T02:00:00.098Z; same receipt','PASS','n8n-history.json')
    add('REC-TUNNEL','Quick Tunnel','Inspect current container and public login; correlate archived recovery logs','Healthy candidate; public HTTPS; internal services not routed',
        'Healthy, restart_count=1, no docker socket, login 200; tested internal/secret paths 404','PASS','http-probes.json')
    add('REC-SOURCE','Deployment','Hash running Gateway/Core vs workspace','Required P05–P08 modules and Control Center deployed',
        f"Missing {len(gw['parity']['missing_runtime'])} Gateway modules; {len(gw['parity']['different'])} differ; Core partial absent",'FAIL','gateway-storage-and-parity.json','TK-02')
    add('REG-AUTH','Control Center','Run 3 regression cases before fix, then focused suite after fix','Revoked/changed role denied; native outage returns 503',
        'Before: 3 FAIL, HTTP 200; after: 25 focused tests PASS. Workspace only','PASS','control-center-after.log','TK-03')
    add('REG-SECRETS','Security','Run existing secret redaction guard','No detected documented credential patterns','2 tests PASS; limited pattern scan, not proof all secrets absent','PASS','secret-guard.log')
    pending=[
      ('PM-CREATE','PM','Native mutation','Create one explicitly approved Epic/Task/Subtask fixture','Correct hierarchy, native permissions and receipt'),
      ('PM-ASSIGN','PM','Native mutation','Assign approved fixture to known member','Assignee persisted; read-back matches'),
      ('PM-STATUS','PM','Native workflow','Transition approved fixture through real allowed statuses','Native gate rejects invalid transition; valid transition persists'),
      ('PM-SPRINT','PM','Sprint/Backlog','View board; move approved fixture only after scope approval','Actual sprint/backlog state matches UI'),
      ('PM-PROPOSAL','PM','AI mutation','Ask on approved fixture; inspect diff; approve once; read back','Bound proposal, explicit consent, one mutation receipt'),
      ('PM-REJECT','PM','AI mutation','Reject fixture proposal','No business mutation; rejection audit'),
      ('BA-ANALYSIS','BA-PM','BA Agent','Analyze fixture requirement and acceptance criteria','Cited output grounded in permitted native data'),
      ('DEV-ANALYSIS','BE/FE','Dev Agent','Request technical breakdown on assigned fixture','Technical draft only; no shell/operator access'),
      ('QA-TESTS','QA','QA Agent','Generate tests from permitted fixture AC','Draft tests; no claim tests executed'),
      ('AGENT-CHAIN','All','Multi-Agent','Trace UI → Gateway → Supervisor → specialist → report/proposal → audit','Real runtime specialist dispatch, scoped context and durable run'),
      ('MEM-SEARCH','All','Second Brain','Search a pre-approved indexed native reference through UI','ACL-bound source citation, no cross-project return'),
      ('MEM-INGEST','PM','Second Brain','Ingest one approved fixture twice','Persistent single document with correct source revision'),
      ('MEM-RESTART','Operator','Second Brain','Restart only isolated qualified clone after baseline','Same hashes and ACL after restart; no serving Gateway restart'),
      ('AI-FAULTS','All','AI status','Use isolated clone to exercise timeout/429/503','Explicit waiting/unavailable state; no blind mutation replay'),
      ('DEVICE-5','All','Remote UAT','Five actual people/devices run scoped checklist','Five real concurrent clients; host browser sessions are not five devices'),
      ('DESKTOP-3','Owner','Recovery','Three owner-approved Desktop stop/start cycles','State and saved keys retained; no recurring prompt'),
    ]
    blocked={'BA-ANALYSIS','DEV-ANALYSIS','QA-TESTS','AGENT-CHAIN','MEM-SEARCH','MEM-INGEST'}
    for ident,role,module,steps,expected in pending:
        status='BLOCKED_DEPLOYMENT' if ident in blocked else 'PENDING_MANUAL_UAT' if ident in {'DEVICE-5','DESKTOP-3'} else 'PENDING_FIXTURE_APPROVAL' if ident.startswith('PM-') else 'NOT_RUN'
        add(ident,module,steps,expected,'Chưa thực hiện; không dùng unit/mock để thay bằng chứng live',status,'NEXT_DEVELOPMENT_PLAN.md','TK-02' if ident in blocked else '',role)
    with (OUT/'UAT_TEST_RESULTS.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    counts=dict(Counter(r['Status'] for r in rows))
    write('CHATGPT_CODEX_TAKEOVER_AUDIT.md',f'''# Codex takeover — observed 18/10/2026

Workspace `{ROOT}` accessible; Docker Desktop accessible. Latest historical audit: `verification_runs/run_20261018_0515`, baseline `run_20261018_0435`. No root README.md; subsystem README and checkpoint exist. Current request supersedes continuation from the old P04 checkpoint. No rebuild, Main restart, provider call or business mutation performed.

## Findings

1. **TK-01 / CRITICAL — DEF-08 remains OPEN.** Queries from both DB container and the actual Rails connection agree: old IDs 23–28 remain active/default, new IDs 35–40 absent. `stage-owner` is user **5**, not 13. Saved TOTP secrets match those existing old devices. No conflicting defaults found among these accounts. Historical rotation log ends `NEW_DEVICE_VERIFY_FAILED: ba-pm`; old-device check also shows true/true. The final markdown claim is contradicted by runtime and its own raw logs. No second rotation attempted.
2. **TK-02 / BLOCKER — source/runtime differ.** Running Gateway006b9c6c lacks **35** workspace modules and differs in **7** others. Core8a42c7ef lacks `_control_center.html.erb`; its show view differs. Agent task/run counts at baseline are zero. Library unit tests cannot prove deployed Supervisor/Second Brain/UI. Source `ai_worker.py` uses the existing Gemini loop; `Supervisor.execute_task` has no business service caller. Wiring and qualification are required before deployment, not merely copying missing files.
3. **n8n corrected, working.** Original receipt `5de5af58-b747-4cbb-b16b-03d51b433df6` created 17Oct19:21:02.958878UTC / 18Oct02:21:02.958878Bangkok, correlating with startup Execution **8** (19:21:02.257UTC). Executions18–20 reuse it; their responses do not contain a `created` boolean. `verify_n8n_idempotency_deep.py` invents NEW/REUSED labels by execution ID. Actual scheduled Execution23 ran **09:00 Bangkok** and reused the same receipt. One receipt and five actor snapshots for 18Oct, 335 items each, zero model calls. Historical report preserved; correction is in this takeover.
4. **Quick Tunnel live/recovery scoped verification.** `{url}` login200, anonymous identity401, tested internal/secret paths404. Candidate healthy, restart_count1, no mounts/socket, stage-front only. Actual binary cloudflared2026.10.0, not the report's 2024.12.0. Archived `/tmp/fault_inject` tests demonstrate supervisor counter/exit→Docker restart, hostname synchronization and HTTPS recovery. They do not simulate all Cloudflare/network/origin failure modes. 123.35s is one reported recovery sample, not a statistical mean. `real_browser_post_autoheal_recovery.log` targets the old hostname; timestamped `qtt_03_playwright_e2e.log` (22:46:17–22:47:16UTC) targets the new hostname, after recovery22:22:36UTC.
5. **TK-04 / HIGH — repair drift.** `quick.stage.yml` selects candidate, but saved stage-runtime manifest still selects original cloudflared. `local_runtime.expected_images/check_owned` can refuse repair. Do not use the historical single-file Compose rollback command; it loses merged project/networks/dependencies.
6. **TK-03 / HIGH — source authorization bug fixed locally.** Control Center swallowed native membership/role/outage errors and returned cached actor data/authority. Three tests reproduced HTTP200 before fix; after removing the fallback, 25 focused tests PASS. No serving runtime changed; it does not currently contain this endpoint.

## Evidence integrity and tests

Historical CSV:42 cases; **39** have raw logs and all39 match CSV hashes and ZIP. Three deferred/blocked cases have no log and are not hash-tested. All **45** archived files match their disk bytes. Integrity is verified, but a hash does not validate the assertions. The saved runner log says40 suites/195 tests PASS in29.557s; it is a selected local suite, not full deployed integration. Business suite source includes mocks; the blanket '6 live E2E' description is inaccurate. Kept historical results; no blanket rerun.

Fresh browser: five independent host Edge contexts with real native login, existing TOTP, identity, Work Packages, Assistant, role boundary and logout. Native saved passwords are valid for all5. The copied `secrets/...json` passwords for BA-PM/BE/QA are stale; originals remain valid in private `stage/accounts.json`. No password reset or primary credential-file overwrite. Initial selector error and stale-credential attempts retained; final authoritative browser evidence is `browser-uat-native-accounts.json`.

UAT result rows: `{json.dumps(counts,ensure_ascii=False)}`. These are checkpoints/scenarios, not a claim of complete business acceptance. Control Center absent for all5 is an actual FAIL. Model/provider business mutation, fixtures and physical five-device checks remain unexecuted.

## Preservation

Main only received anonymous login/health GETs; no Main DB query or restart. No Jira, billing change, credential rotation, Quick Tunnel restart/fault, source cleanup, Git commit/push or skills deletion. Gateway usage ledger stayed471 at baseline. Browser login naturally updates session/2FA metadata; no business mutation was requested. Seven active Staging services were healthy. No claim all native DB rows are byte-identical across login tests.

## Coverage / next action

Read takeover prompt, project instructions/kickoff/session protocol, state/handoff/log, task registry, plan/architecture, subsystem runbooks and latest named reports; inspected linked actual source, CSV, ZIP and raw logs. Historical architecture/README/checkpoints contain superseded statements; current report does not adopt them as deployment proof. Required next action: owner approval for safe TOTP remediation, then bounded integration/qualification tasks in NEXT_DEVELOPMENT_PLAN. No reopening all P00–P10 or changing historical DONE entries to fabricate a new percentage.
''')
    write('SYSTEM_ARCHITECTURE_CURRENT.md',f'''# Current architecture — source and runtime distinguished

```mermaid
flowchart TD
  U[5 Scrum roles / native sessions] --> CF[Cloudflare Quick Tunnel HTTPS]
  CF --> WEB[Staging OpenProject Core 8a42c7ef]
  WEB --> PG[Staging PostgreSQL / native public schema]
  WEB -->|actor-bound HMAC bridge| GW[Gateway 006b9c6c]
  GW -->|fresh native identity and ACL| WEB
  GW --> SQ[Persistent gateway.sqlite / queue / receipts / trace]
  GW -->|saved Free-only policy and key| G[Gemini API]
  N[n8n Community 2.43.6 / one owner] -->|signed machine command| GW
  W[Workspace-only Supervisor / specialists / reports / Control Center] -. qualification and wiring missing .-> GW
  K[knowledge.sqlite / FTS5 / 4 saved docs] -. application retrieval not wired .-> GW
```

## Runtime map

| Component | Source / entrypoint | Storage / network / ingress |
|---|---|---|
| OpenProject | core/overlay controllers, views, gates_api; quick_tunnel_web.rb → prod/web | stage-db + stage-assets; stage + stage-front; localhost18091 redirects to current HTTPS hostname |
| Gateway | gateway/app.py → Service; ai_worker.py → existing Gemini tool loop | /state bind; persistent tokens/proposals/usage/agent trace; localhost18092; private automation alias gateway |
| n8n | local-runtime.stage.yml; manual-status.v2, daily-brief.v2, workflow-errors.v1 | n8n-data volume + persisted encryption key; automation internal; editor through loopback Caddy5678 |
| Tunnel | QuickTunnel.Dockerfile + quick_tunnel_supervisor.sh | stage-front only; no socket or host mounts; internal2000 health/metadata |
| Landing | Quick.Caddyfile | localhost18090; access/index.html + current-url.json; no secret-file mount |
| Backup | local_backup.py via dedicated sidecar | private operator/local-backups; selected RO mounts, stage network; no serving restart |
| Knowledge | knowledge_storage/search/retrieval/ingestion/classifier modules in workspace | SQLite FTS5 file exists; separate PG schema qldapm_knowledge has2 tables; persistent library proof does not imply live retrieval/indexing |

Main remains separate: UI8088, Gateway8090; no P05–P08 promotion demonstrated. Runtime details, mount sources, ports, commands, image IDs and saved Compose file chain are in `runtime.json`; merged configuration is `compose-effective.json`.

Human API: /api/v1/commands, ai-runs, agent-runs, signed /internal/ui. Machine API: /internal/automation/status and signed /internal/automation/commands. Current source adds /api/v1/control-center/state; running app lacks it. Native UI: /projects/qldapm-local/qldapm-ai, native Work Packages/gates/insights. Code paths are under openproject/ai relative to workspace; registry tools are proposed definitions until real business dispatch is integrated. Operator shell/Docker/source tools remain outside BUSINESS_TOOLS.

Identity6=BA-PM,7=PM,8=BE,9=FE,10=QA in project3; stage-owner5 is separate. PM-only AI business writes still require native permission, scope, consent/proposal/hash and read-back. Five sessions on this host do not demonstrate five physical clients. Gemini local policy validates existing project/model15RPM/250KTPM/500RPD with13/225K/450 safety caps; no Google request in takeover, no live billing verification.
''')
    write('UAT_TEST_PLAN.md','''# UAT plan — five actual roles, Staging only

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
''')
    write('OPEN_ISSUES_AND_PRIORITIES.md','''# Verified issues and priorities

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
''')
    write('SOURCE_AND_GIT_REPRODUCIBILITY.md',f'''# Source and Git reproducibility

Branch `{git['branch']}`, HEAD `{git['head']}`. Exactly **two tracked files**, both v1 workflow JSON. Full porcelain snapshot: **{git['status_counts']['??']} untracked paths** at capture; tracked diff empty. This is not a reproducible product revision. `git-status-full.txt` and `git-ignored-paths.txt` preserve exact inventory; no -uno, clean, stash, reset, checkout, commit or push used.

Nested native fork HEAD `{git['nested_head']}`,18 dirty paths preserved. Root openproject/.gitignore excludes development/ and ai/.venv; fork changes require pinned fork commit + reviewed patch or explicitly preserved overlay, not an implicit root add. `source-manifest.json` hashes349 relevant AI source/config/test files after local authorization fix. Hashes do not replace versioning. Keep private runtime/secrets/backups, .venv, cache and binary attachments out of commits.

Runtime images: Gateway006b9c6c, Core8a42c7ef, n8n2.43.6 immutabledd580fe1, candidate Tunnel actual ID in runtime.json. Compose chain: stage.yml + deep-ai.stage.yml + gemini-free.stage.yml + local-runtime.stage.yml + quick.stage.yml + backup.stage.yml, project qldapm-ai-stage. `docker compose config --format json` passed with saved .env plus the same image/runtime variables used by provision_local_stage; eight service definitions including seeder, seven serving services. Config command only; seeder never run. A naked .env invocation initially failed because required operator image variables were absent; do not mistake it for serving outage.

Build paths: gateway Dockerfile / Dockerfile.gateway-patch / automation/FreeOnly.Dockerfile; Core core/Dockerfile and automation/DailyCore.Dockerfile; Tunnel automation/QuickTunnel.Dockerfile + shell supervisor. DailyCore currently copies only three files and omits the new Control Center partial: extending a view render without its partial would break new builds. Dependency pins: requirements.lock.txt; native fork Gemfile/lock and frontend lock; n8n pinned digest. Base tags/old layers must be retained or resolved to immutable IDs before a clean rebuild. No image built during takeover.

## Proposed commit sequence — owner approval before commits

1. Safe product baseline: AI gateway, operators, core overlay, manifests/locks and focused tests; secret scan, explicit path allowlist, exclude private files. Record native fork reference/dirty patch separately.
2. Standalone P05–P08 candidate modules and tests clearly marked not deployed; wire/qualify each vertical slice before marking live completion. Capture source-to-image manifest.
3. Runtime/recovery fixes and immutable configuration after qualification; pin deployed pair and backup/restore proof. Never merge/promote Main as part of committing.
4. Current takeover reports and authoritative handoff correction.

Rollback local source fix: original service.py saved privately under operator/takeover-20261018-1035/service.before.py, SHA2569744d3ee4f1e0857779d5ea12bf3ea3379302ea785e98138f3112dc80dbcd299. Only the Control Center authorization block changed; restore that block/file only after checking subsequent edits. No runtime rollback is needed because nothing was deployed. Historical Quick Tunnel rollback instructions using a single Compose file are unsafe for this merged project and must not be executed.
''')
    write('RELEASE_READINESS.md',f'''# Release readiness — takeover result

**Basic native Staging is available; full Multi-Agent product UAT is BLOCKED. Main/production is NOT APPROVED.** Historical113DONE is retained as a claim, not a new release sign-off.

| Gate | Current decision | Evidence / next condition |
|---|---|---|
| G1 source/regression | PARTIAL / deployment BLOCKED | Existing195-test selected log hash verified; new25focused+2guard PASS;35runtime modules missing; two-file HEAD insufficient |
| G2 Google Billing | BLOCKED_OWNER_VERIFICATION | Actual local policy Free, no billing, existing model/key; no current provider/console check; no paid fallback |
| G3 Quick Tunnel | VERIFIED_WITH_LIMITATIONS | Current HTTPS200; isolated ingress/no socket; archived hook/exit/restart/hostname/HTTPS chain; new-host browser log identified. Repair manifest drift remains open; no new fault injection |
| G4 RBAC/browser | PARTIAL; credential security BLOCKED | Five real browser logins/read/logout, native role ceilings; TOTP rotation claim false; Control Center absent |
| G5 Second Brain | STORAGE_LIBRARY_ONLY | Physical persistent SQLite + historical restart test; module/retrieval missing from live Gateway; no live UI retrieval acceptance |
| G6 n8n | VERIFIED_WITH_PROVENANCE_CORRECTION | Origin8;18–20 reuse; actual09:00 schedule23; one receipt/five snapshots; no model calls |
| G7 capacity20 | DEFERRED_BY_OWNER | No fake users or capacity claim; five host contexts are not five physical clients |

Current public URL: {url}. All serving Staging containers healthy at capture; provider availability remains separate from container health. Five-role native UI UAT can proceed under acknowledged credential risk; a new production-readiness declaration cannot.

Owner actions: approve TOTP remediation preview if desired; later approve exactly one Staging business fixture scope; retain G2 billing verification before release and separate explicit Main approval. No new API key required. Do not supply passwords, TOTP secrets or tokens in chat.
''')
    write('NEXT_DEVELOPMENT_PLAN.md','''# Next bounded development plan

No restart of P00–P10 and no bulk status reset. Continue from verified runtime and this separate reconciliation layer.

| Order / ID | Task | Dependency | Acceptance |
|---|---|---|---|
| 1 / TAKEOVER-SEC | Repair TOTP after explicit owner approval | SECURITY_REMEDIATION_PREVIEW | Six actual accounts mapped by login; old revoked, one active/default new device each; saved-key read-back and real login; no secret output |
| 2 / TAKEOVER-RUNTIME | Reconcile Tunnel saved image/provisioner and full Compose chain | Preserve candidate; source review | Immutable image matches live and manifest; readonly ownership/status passes; no serving fault/restart |
| 3 / TAKEOVER-AGENT | Wire Supervisor into one authenticated durable read-only task path | Existing P03 contracts, current local source fix | Native ACL→task/run→selective specialist→review→report→audit through real UI; no extra queues/services, no business write/provider call for deterministic scenario |
| 4 / TAKEOVER-CC | Finish Control Center data/partial packaging and truthful quota/status | Agent path + fail-closed tests | Qualified clone UI; same-role membership removal denies; unknown telemetry never zero/READY; native role ceiling retained |
| 5 / TAKEOVER-KNOWLEDGE | Wire approved source ingestion and retrieval into scoped task/UI | Agent path + persistent storage | Duplicate fixture ingestion idempotent, fresh ACL/source revision citations; clone restart proof; no Native DB destructive change |
| 6 / TAKEOVER-PAIR | Build immutable pair and qualify source/image parity | Above vertical slices | Actual clone tests plus backup/restore; old pair retained; deploy only intended Staging pair; no Main promotion |
| 7 / TAKEOVER-UAT | Complete approved fixture proposal/create/assign/status/comment cases | Owner fixture approval + qualified pair | All5roles; explicit PM approval; exact before/after and one native receipt; non-PM denied |

Keep G2 blocked and capacity20 deferred. Preserve unrelated source, Main, CSDLDPT and Docker disk placement. Do not run old repair/rotation/matrix scripts blindly: some mutate live services or rewrite historical reports. Current audit scripts are read-only except browser session metadata and local artifact generation. No background work is scheduled after this turn.
''')
    write('SECURITY_REMEDIATION_PREVIEW.md','''# TOTP remediation preview — NOT EXECUTED / requires new owner approval

## Concrete target and observed before state

| Login | Actual user | Current active/default device |
|---|---|---|
| ba-pm |6|27|
| pm |7|24|
| be |8|23|
| fe |9|25|
| qa |10|26|
| stage-owner |5|28|

New IDs35–40 do not exist; allocate actual new IDs during an approved repair, never hardcode those IDs or user13. Existing saved secrets match old active devices. Do not reuse historical approval A as permission to run a new rotation.

## Proposed authorized operation

After owner approves: fix and offline-test the rotation operator for time-window drift (Python OTP is currently generated before a slow Rails boot), correct actual identity mapping, full transaction/failed-attempt cleanup and crash-consistent private credential persistence. First take a verified scoped Staging backup including native devices and private credential recovery material. Prepare new cryptographic keys only in private unmounted storage; verify read-back and key validity before revoking old keys, persist mapping and protect owner/SYSTEM ACL. Preserve original valid passwords from stage/accounts.json for the five members; do not reset passwords or change roles. The stale copied password fields must not be used as proof accounts are broken.

Verify all six old devices inactive/non-default and exactly one active/default new device per actual account; fresh browser2FA for five members and owner access as available; old-key rejection without printing any key/code. Public/internal paths must not serve secret files. Main, API key, billing, tunnel and business data untouched. No public downtime or tunnel restart is part of this approval.

## Impact and recovery

Six users must enroll the new TOTP key once through private delivery. Existing business roles/data/passwords remain. A partially failed operation must retain a usable verified device and private recovery mapping, stop with a checkpoint, and not retry blindly. Do not restore a leaked old key as routine rollback; use the validated new recovery device or an owner-approved forward fix. The serving tunnel remains as requested; while approval is pending the historically exposed old TOTP keys remain a material risk. No credential mutation has been made in this takeover.
''')
    write('CHECKPOINT.md',f'''# Takeover checkpoint

Updated {datetime.now(timezone.utc).isoformat()}. Handoff phases1–5 completed at the bounded scope documented in audit; phase6 source-only authorization fix tested; delivery reports generated. UAT statuses: {json.dumps(counts)}.

Resume here, not historical P04 or113DONE prose. Runtime unchanged: Gateway006/Core8a42,7healthy, Quick Tunnel candidate. Actual old TOTP still active, no new35–40. Original valid native passwords support all5browser roles; copied secret-file passwords stale for3members. No secret printed in new artifacts. TOTP remediation awaits new owner approval; preview is concrete. New source control-center fix has25focused tests PASS and2secret guard PASS, not deployed.

Raw current evidence: runtime/compose-effective/core-parity/gateway-storage-and-parity/n8n-history/totp-key-readonly-check/password-original-readonly-check/http-probes/browser-uat-native-accounts JSON. Source snapshot349files, full Git/ignored inventory, historicalZIP45/45+CSV39/39. No live provider calls or Main mutation; no active task requiring later automatic action. Next dependency order in NEXT_DEVELOPMENT_PLAN. Do not run old rotation or single-file Compose rollback.
''')
    write('README.md',f'''# Codex takeover18Oct2026

Start with [audit](CHATGPT_CODEX_TAKEOVER_AUDIT.md), [release readiness](RELEASE_READINESS.md), [UAT results](UAT_TEST_RESULTS.csv), [issues](OPEN_ISSUES_AND_PRIORITIES.md) and [checkpoint](CHECKPOINT.md).

Five-role browser checkpoints/scenarios: `{json.dumps(counts)}`. TOTP security and deployed multi-agent integration are blocked. No old audit report overwritten, no runtime restart, no new provider request. Source-only authorization fix tested; no commit/deploy.
''')
    print(json.dumps({'uat_rows':len(rows),'statuses':counts,'reports_written':10},ensure_ascii=False))

if __name__=='__main__':main()

"""Save the feature-complete continuation handoff; never requests or certifies UAT."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import zipfile

from automation.engineering_worker import ROOT,operator,save,command
from automation.engineering_checkpoint import refresh

DOCS=ROOT/'docs/ai/engineering'


def read(name):return json.loads((DOCS/name).read_text(encoding='utf-8'))
def write(name,text):(DOCS/name).write_text(text.strip()+'\n',encoding='utf-8')


def finalize():
    live=operator('status');verified=read('CONTINUATION_VERIFICATION.json');demo=read('demo-service.json');deployment=read('deployment.json')
    assert live['mode']=='OFF' and all(r['queue_state']=='finished' for r in live['runs'])
    assert verified['status']=='TARGETED_TECHNICAL_VERIFICATION_PASS' and verified['idle_no_inference']=='PASS'
    assert all(u['state']=='succeeded' for u in live['backlog'])
    assert demo['head_sha']==verified['app_head'] and verified['app_tests']>=19
    latest=next(r for r in live['runs'] if (r['result'] or {}).get('status')=='succeeded' and (r['result'] or {}).get('head_sha'))
    assert latest['id']==verified['run_id'] and latest['result']['head_sha']==demo['head_sha']
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    snapshot=DOCS/('PHASE2_SOURCE_CONTINUATION_'+stamp+'.zip')
    assert not snapshot.exists()
    head=demo['head_sha'];run_id=latest['id'];unit=latest['unit'];tests=verified['app_tests'];pr=latest['result']['pr_url']
    result=latest['result'];child=result['native_readback']['child_id']
    previous=read('IMPLEMENTATION_STATE.json')
    # Preserve the prior mutable handoff before replacing its current instructions.
    archive=DOCS/'handoff-history'/stamp;archive.mkdir(parents=True)
    for name in ['HANDOFF_GEMINI_LATEST.md','IMPLEMENTATION_STATE.json','GEMINI_CONTINUE_PROMPT.md','OPERATIONS_RUNBOOK.md','E2E_EVIDENCE.md']:
        (archive/name).write_bytes((DOCS/name).read_bytes())
    write('FEATURE_COMPLETENESS.md',f'''# Phase 2 — feature implementation complete, UAT deferred

Trạng thái: FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Phạm vi Project6/#379 và engineering children, repo Mini Task Manager. Các baseline pass chỉ là baseline; các gap được triển khai thực dưới đây.

| Feature | Gap đã xử lý / implementation thực tế | Source | Trạng thái / evidence |
|---|---|---|---|
| Supervisor | Atomic ownership/claim, role delegation, immutable unit/dependency/base, bounded rework, receipt handoff/OFF | gateway/engineering.py; engineering_lifecycle.py; automation/engineering_delivery.py | COMPLETE; actual planning/development runs và journal |
| PM/BA | Two bounded Gemini roles with loaded persona/skill; functional spec/API/edges/AC, priorities, reuse Native backlog, assignee coordinator/dependencies, feedback units | engineering_planning.py; engineering_personas.py; engineering_operator.py | COMPLETE; two PUBLISHED planning jobs, Native380–{child}, shared RAG |
| Dev/Reviewer/QA | Scoped worktree/tools, independent sessions, real code/terminal/review/tests and rework | worker/delivery/bootstrap + existing registry | COMPLETE; actual systemPromptReport, skills_read trajectories, exact diff + artifacts |
| Controls/recovery | OFF, RUN ONCE, PAUSE, CANCEL, RESUME, heartbeat/manual wake; known outcomes keep completed steps; unknown/pending writes block replay | engineering_lifecycle.py; worker.agent_process; Core controller/view | COMPLETE; live same-run cancel/resume and13targeted checks; in-flight disruptive cancellation not separately campaigned |
| GitHub/source lifecycle | Commit/push/PR checkpoints, duplicate prevention, stacked bases, latest verified feedback base and Native readback; no merge | delivery.py; planning.feedback_base_unit | COMPLETE; current commit {head}, {pr}; Windows ready branch FF-only |
| Control Center / Monitor | Backlog/task-unit binding, dependencies, stage/agent/progress/errors, cancel/resume, plans/knowledge/usage/commit/PR; existing Monitor with actual role nodes and receipt timeline | engineering.html.erb; controller; engineering_monitor.py | COMPLETE; current serving source parity and live Monitor API |
| Second Brain | Existing actor/project-scoped RAG feeds planning/Dev; Native plans/results/commit/PR evidence indexed and retrieved | operator.context/knowledge; existing knowledge modules | COMPLETE; actual retrieval379/{child}; no second memory store |
| n8n |16existing workflows preserved, existing WF04 owned-run trace consumes Project6 lifecycle; no second coding scheduler | app.project_for_run + existing workflows | COMPLETE; baseline WF04execution2701, fresh16active/published and current trace/Monitor |
| Mini Task Manager | CRUD/status/search/filter/SQLite/web; added network/HTTP/validation errors, loading/empty/retry, stale-response and double-submit handling; corrected demonstrated Unicode search | demo task_manager/app.py; tests | COMPLETE; {tests}directly related app checks, verified release/header; no browser UAT |
| Delivery/startup | Single WSL OpenClaw, private Node, shared Gemini quota/gate, persistent user app service and hidden host delivery task | runtime config; worker; engineering_demo.py | COMPLETE; app current revision, worker ALIVE, OFF idle no inference |
| Preservation/handoff | Main Project5, existing n8n/knowledge/receipts/source preserved; versioned snapshots and current six files | this folder / deployment.json | COMPLETE; no reset/volume deletion/history rewrite |

Không có mandatory feature còn PARTIAL/MISSING trong phạm vi này. Human UAT, visual/browser acceptance, physical Windows reboot/logon và merge/go-live được hoãn hoặc cần yêu cầu riêng. Không suy ra độ tin cậy vô hạn cho mọi yêu cầu tự do từ một demo có scope/budget.
''')
    write('THREE_REPOSITORY_INTEGRATION.md',f'''# Paperclip, Agency Agents, Superpowers — triển khai thực chất

FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Đây là các local adaptations chọn lọc, không cài nguyên upstream servers/rosters. Source paths dưới đây tương đối với openproject/ai. Evidence ở docs/ai/engineering.

| Repository / cơ chế | Phân loại | Source/config thực tế | Runtime evidence / giới hạn kiểm chứng |
|---|---|---|---|
| Paperclip task ownership + claim | IMPLEMENTED | gateway/engineering.py::admit/claim; gateway/store.py::claim_run | Shared ai_queue, actor20/project6, atomic executing lock; baseline và continuation real runs |
| Agent delegation + result gates | IMPLEMENTED | gateway/engineering.py::progress; gateway/engineering_operator.py; automation/engineering_delivery.py | Typed assignment/start/completion events; independent Dev/Reviewer/QA roles; actual PM/BA Native assignments |
| Durable handoff + recovery | IMPLEMENTED | gateway/engineering_lifecycle.py; automation/engineering_delivery.py; gateway/engineering_operator.py::native_once | Same-run planning and Dev resumes preserved completed outputs;5bounded explicit recoveries; own published source version attested by Native receipt |
| Heartbeat + manual wake | IMPLEMENTED | automation/engineering_worker.py::main; gateway/engineering_lifecycle.py::heartbeat/resume | TaskScheduler Running/worker ALIVE; manual RUN ONCE/RESUME wake durable queue; idle requests unchanged. OpenClaw inference heartbeat remains0m/cron off |
| Budget + no duplicate execution | IMPLEMENTED | gateway/live_agents.py::LiveBudget; gateway/gemini.py::reserve_budget; automation/openclaw_provider_gate.py; automation/engineering_delivery.py | Finite12/5/5 role allowances and3rework passes; original shared quota unchanged; no paid/model fallback, no duplicate Native children/PRs |
| Agency Supervisor | IMPLEMENTED | gateway/agent_registry.py::engineering_profile; gateway/engineering_personas.py; gateway/engineering.py; automation/engineering_delivery.py | Host owns claim/dependency/quality/publication/OFF, model_used=false for orchestration; no second Supervisor |
| Agency PM | IMPLEMENTED | gateway/engineering_personas.py::instructions; gateway/engineering_planning.py::generate actual PM system prompt | Actual structured model plan, priorities/dependencies, Native accountable PM20 and virtual Dev handoff; plan outputs persisted |
| Agency BA | IMPLEMENTED | gateway/engineering_personas.py::instructions; gateway/engineering_planning.py::generate actual BA system prompt | Actual functional specification, APIs/edges/AC/citations and feedback mapped into new units |
| Agency Dev / Reviewer / QA | IMPLEMENTED | automation/engineering_bootstrap.py::install/activate; /home/openclaw/.openclaw/openclaw.json entries dev/reviewer/qa | All three successful session reports injected AGENTS/SOUL with full selected procedure and correct single skill catalog; actual skills_read observed in Web recovery trajectories; reviewers isolated from Dev session |
| Superpowers brainstorming / writing plans | IMPLEMENTED | engineering_skills/engineering-planning/SKILL.md; gateway/engineering_planning.py | PUBLISHED planning document includes loaded skill hash and real Native/RAG outputs |
| Superpowers Git worktrees | IMPLEMENTED | automation/engineering_worker.py::prepare; engineering_skills/engineering-development/SKILL.md | Actual linked ext4 worktrees and pinned verified base; latest feedback unit inherits latest successful branch/head |
| Superpowers TDD / systematic debugging | IMPLEMENTED | engineering_skills/engineering-development/SKILL.md; automation/engineering_delivery.py; /opt/qldapm/acceptance/ | Actual red/green and corrections, preserved failed attempts; current {tests}checks. Web recovery candidate was host-assisted, applied/verified by non-root Dev |
| Superpowers receiving feedback / code review | IMPLEMENTED | engineering_skills/engineering-development/SKILL.md; engineering_skills/engineering-review/SKILL.md; automation/engineering_delivery.py | Findings/test failure flow back to Dev; exact revision gate after changes; actual review PASS stored |
| Superpowers verification / QA / finishing branch | IMPLEMENTED | engineering_skills/engineering-qa/SKILL.md; automation/engineering_delivery.py; automation/engineering_worker.py::test_tree | Independent executed QA, actual commit/PR/native/knowledge readback; no auto merge |

Runtime config: /home/openclaw/.openclaw/openclaw.json, agents.entries.dev/reviewer/qa.contextInjection=always, per-role skills=[engineering-development|engineering-review|engineering-qa]. Original default contextInjection=never is retained outside those entries. Templates /opt/qldapm/agents/<unit>/<role>; application-scoped AGENTS/SOUL and selected skill are root-owned and hash-checked. tools.fs.workspaceOnly stays true. Workshop autonomous learning off; root Gemini key remains separate and unreadable by openclaw.

Before continuation: PM/BA were deterministic advisory, bootstrap injection was disabled and old report injectedWorkspaceFiles=[]. After continuation: actual BA/PM Gemini outputs and Dev/Reviewer/QA bootstrap reports + skills_read are saved. These facts distinguish implementation from role/Markdown names.

Evidence: CONTINUATION_VERIFICATION.json, continuation-monitor-live.json, continuation-control-center-final.json, runs/*/*skill-activation.json, *trajectory.jsonl, delivery-steps.json/history, Native requests and PR readbacks. Live queued cancel/resume and terminal-known recovery were exercised; disruptive in-flight cancel and physical reboot were not a separate test campaign. Unknown Native writes remain fenced for read-back reconciliation; no blind replay.

References reused from Phase1: [Paperclip](https://github.com/paperclipai/paperclip), [Agency Agents](https://github.com/msitarzewski/agency-agents), [Superpowers](https://github.com/obra/superpowers). Correct Native relation create route was verified against serving source and [official Relations API](https://www.openproject.org/docs/api/endpoints/relations/); rejected404 history is preserved.
''')
    write('GEMINI_CONTINUE_PROMPT.md',f'''# Gemini tiếp quản — feature implementation complete

Workspace `{ROOT}`. Đọc HANDOFF_GEMINI_LATEST.md, IMPLEMENTATION_STATE.json, PHASE2_CONTINUATION_REQUEST.md, FEATURE_COMPLETENESS.md, THREE_REPOSITORY_INTEGRATION.md, OPERATIONS_RUNBOOK.md và CONTINUATION_VERIFICATION.json. Source/runtime là nguồn thật; đối chiếu Git/image/source hashes trước sửa. Current status FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Không yêu cầu người dùng UAT hoặc chạy browser/computer use/full regression; UAT chỉ khi được yêu cầu riêng.

Giữ existing QLDAPM Supervisor/Gateway/Store/ai_queue/AgentRegistry. PM/BA actual bounded Gemini structured planning qua client/quota cũ. Dev/Reviewer/QA dùng OpenClaw/Gemini, independent sessions và selected role persona/skills bootstrap. Host pulse chỉ delivery liveness, không inference; manual RUNONCE/RESUME wake queue. Không second Supervisor/Paperclip server, duplicate agent registry, OpenAI/Codex/9Router runtime, paid fallback hoặc bulk skill install.

Project6 ai-dev-demo/#379 và children là phạm vi demo, PM20 revalidated Native. Project5 actor20 vẫn BA; không ghi/reset Project5, xóa volumes, mất untracked/source/receipts/SecondBrain/n8n16. Feedback units được đóng băng spec/AC và latest verified base; source Task không tự cấp quyền mới. Current app head {head}, run {run_id}, unit {unit}, Native child {child}, PR {pr}. Windows demo ready branch cùng head, dev/ preserved. Main source chưa commit/push, có source snapshot; không reset/clean branch.

Các runs đã hoàn tất, modeOFF/gateinactive. Không replay để tạo evidence. Terminal-known checkpoint RESUME dùng cùng run/version, completed stages giữ nguyên; pending/unknown external writes cần readback reconciliation.5explicit recoveries/3rework passes và role allowances hữu hạn, shared quota unchanged. Prefix provenance/failed attempts nằm trong journal/history; Web UI recovery có host-assisted candidate thực thi bởi Dev, không được biến thành lời khẳng định LLM tự tác giả toàn bộ.

Tiếp tục chỉ từ yêu cầu mới hoặc lỗi thực tế. Khi có lỗi: source/current actor/version → scoped PM/BA feedback plan → one unit → Dev/review/QA → exact Git/native/RAG readback → OFF. Source already includes new controls, Monitor, Unicode search correction và UI error recovery; không nghiên cứu lại Phase1 hay viết lại các phần này. Giữ six handoff current mỗi milestone bằng engineering_checkpoint.py. Baseline finalizer đã được chặn; finalizer continuation không chứng nhận UAT.
''')
    write('OPERATIONS_RUNBOOK.md',f'''# Vận hành Phase2 continuation

Current scope/status: FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Workspace `{ROOT}`. Current image/backup authority deployment.json; app release demo-service.json, head {head}. No active engineering runs; OFF, gateinactive. No UAT/browser/computer use requested.

## Start / read status without inference

```powershell
Set-Location -LiteralPath 'D:\\AI project\\QLDAPM chat'
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

App service qldapm-mini-task-manager.service, data `/home/openclaw/engineering/demo-data/tasks.sqlite`; release `/home/openclaw/engineering/releases/{head}`. Source Windows repo D:/AI project/QLDAPM-demo/mini-task-manager ready branch matches commit. X-QLDAPM-Revision header and normalized-source comparison verify serving revision; Git's existing archive CRLF conversion is recorded in verification hashes. Do not reset application data.

Explicit versioned promotion/rollback to a verified run (OFF/no active job required):

```powershell
& 'openproject/ai/.venv/Scripts/python.exe' -B -m automation.engineering_demo --update-run {run_id}
```

Use an older successful run ID for app rollback; same datafile remains. Main rollback uses exact prior image/config from deployment.json/private continuation backup; restore only Gateway/Core web configuration, no automatic business DB restore. Live SQLite belongs to Linux: never open its bind-mounted WAL/SHM with Windows sqlite3 or delete sidecars. No volume deletion/history rewriting.

Current PRs remain stacked/open; merge is separate authorization. If later approved, merge PR1 first, retarget PR2 to main, review/merge, then retarget each next PR to main after its predecessor merge. Do not confuse deployed feature head with main branch content.

## Handoff

Update state/journal/evidence and run engineering_checkpoint.py after meaningful work. Current source snapshot/manifest is in state.code_snapshot; previous39file snapshot remains baseline only. MAIN source is uncommitted, existing untracked preserved. engineering_finalize_handoff baseline helper is blocked after continuation; use engineering_finalize_continuation only with current successful verification, and never to claim UAT. Physical Windows logon/reboot trigger remains unexercised; regular manual TaskScheduler start/idle is verified.
''')
    write('E2E_EVIDENCE.md',f'''# Phase2 continuation — implementation evidence

Status FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. No computer use, user login request, new full regression campaign or UAT.

- Actual current run {run_id}, unit {unit}, head {head}, PR {pr}, Native child{child}; source/release/header verified.
- Web recovery run a43376cf-e70a-478d-a28e-067964a5a218: commitd00f8c5/PR3/#382,19checks, actual loaded personas/skills. Two Dev allowance failures retained; host-assisted concrete candidate then non-root Dev actual red/green + independent Reviewer/QA. No claim of independent model authorship for that candidate.
- Current direct application checks: {tests}PASS, no errors/failures/skips in JUnit.13targeted lifecycle checks +1targeted unknown-outcome retry guard PASS. Controller/ERB compile PASS. Prior86/15/17were baseline, not rerun or summed as fresh coverage.
- Existing Monitor API returns actual Dev/Reviewer/QA and BA/PM nodes, receipt usage/timeline, project6owned scope/fresh Native reads. Source parity captured in CONTINUATION_VERIFICATION.json.
- PM/BA plans created/updated Native380–{child}, assignments as PM20 accountable coordinator, real dependencies/comments and shared RAG. Same-run cancel-before-claim/resume and terminal-known recovery exercised. Knowledge-only resume retained19→19 model requests; explicit busy-only retry is bounded. Unknown writes still fence replay.
- n8n16active/published unchanged; baseline WF04execution2701retained. Engineering traces are available through same owned-run integration. Project5 actor20 stillBA; no Project5 engineering writes/reset/volume deletion.
- OFF idle requests {verified['idle_requests_before']}→{verified['idle_requests_after']}; delivery worker ALIVE, provider gateinactive. This does not claim provider billing-console verification.

Sources: CONTINUATION_VERIFICATION.json, continuation-monitor-live.json, continuation-control-center-final.json, demo-service.json, windows-demo-delivery-continuation.json, runs/*/result.json/JUnit/trajectory/activation/history, deployment.json. Early discarded PM candidate before cache fix is not available as raw response; error/usage and later cached outputs are retained. Relation404rejection is preserved and corrected using actual Work Package relation route.

Checks not performed: human/visual UAT, physical Windows logon/reboot, disruptive in-flight cancellation campaign, broad load/security regression, merge/production sign-off. These are not represented as PASS.
''')
    journal=DOCS/'IMPLEMENTATION_JOURNAL.md'
    journal.write_text(journal.read_text(encoding='utf-8')+f'\n19. Continuation final: latest head{head}/PR{pr.rsplit("/",1)[-1]}/Native{child}; current{tests}appchecks,13lifecycle +1retry checks, actual persona/skill activation and Monitor/idle/source parity. All mandatory feature gaps in matrix implemented; UAT deferred. Full regression not rerun; no merge or parentDone. Current snapshot below is separate from baseline39file archive.\n',encoding='utf-8')
    architecture=ROOT/'architecture.md';text=architecture.read_text(encoding='utf-8')
    heading='## Phase 2 continuation — feature completion, UAT hoãn (30/10/2026)'
    if text.startswith(heading):text=text.replace(heading,'## Phase 2 continuation — FEATURE_IMPLEMENTATION_COMPLETE / USER_UAT_DEFERRED',1)
    text=text.replace('Continuation candidate bổ sung','Continuation đã triển khai',1)
    architecture.write_text(text,encoding='utf-8')
    pointer='''<!-- PHASE2_CONTINUATION_CURRENT -->
# Current Phase2 continuation

FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Authority: docs/ai/engineering/HANDOFF_GEMINI_LATEST.md, IMPLEMENTATION_STATE.json, FEATURE_COMPLETENESS.md, THREE_REPOSITORY_INTEGRATION.md and deployment.json. Existing historical image/UAT statements below are baseline, not current serving proof. No computer use or full regression requested. Main source uncommitted; preserve current snapshot/untracked. Read current runbook before any installer/deploy/replay.
<!-- END_PHASE2_CONTINUATION_CURRENT -->

'''
    for name in ['README.md','CHECKPOINT.md']:
        path=ROOT/'openproject/ai'/name;text=path.read_text(encoding='utf-8');path.write_text(pointer+text,encoding='utf-8')
    # Patch snapshot: selected current source, stable operational docs and Git bundle.
    paths={ROOT/f['path'] for f in read('SOURCE_MANIFEST.json')['files']}
    paths.update((ROOT/'openproject/ai/automation').glob('engineering_*.py'))
    paths.update((ROOT/'openproject/ai/gateway').glob('engineering*.py'))
    paths.update(ROOT/p for p in ['openproject/ai/tests/test_engineering_continuation.py','openproject/ai/README.md','openproject/ai/CHECKPOINT.md'])
    paths.update(DOCS/name for name in ['FEATURE_COMPLETENESS.md','THREE_REPOSITORY_INTEGRATION.md','PHASE2_CONTINUATION_REQUEST.md'])
    paths.add(DOCS/'runs'/run_id/'publish.bundle')
    paths.update((DOCS/'runs/a43376cf-e70a-478d-a28e-067964a5a218/operator-handoff').glob('*'))
    manifest=[];secret=re.compile(rb'(?:AIza[0-9A-Za-z_-]{35}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,})')
    for path in sorted(paths):
        assert path.is_file() and path.is_relative_to(ROOT)
        data=path.read_bytes()
        if secret.search(data):raise ValueError('POSSIBLE_SECRET_SNAPSHOT_HOLD')
        manifest.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    write('SOURCE_MANIFEST_CONTINUATION.json',json.dumps({'scope':'current selected source/stable docs/demo bundle; six mutable handoff files remain current on disk','files':manifest},ensure_ascii=False,indent=2))
    with zipfile.ZipFile(snapshot,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for item in manifest:z.write(ROOT/item['path'],item['path'])
        z.write(DOCS/'SOURCE_MANIFEST_CONTINUATION.json','docs/ai/engineering/SOURCE_MANIFEST_CONTINUATION.json')
    with zipfile.ZipFile(snapshot) as z:assert z.testzip() is None
    snapshot_info={'path':str(snapshot),'sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'files':len(manifest),'credentials_included':False}
    write('SOURCE_SNAPSHOT_CONTINUATION.json',json.dumps(snapshot_info,indent=2))
    state=read('IMPLEMENTATION_STATE.json')
    state.setdefault('code_snapshot_history',[]).append(state['code_snapshot'])
    state.update(status='FEATURE_IMPLEMENTATION_COMPLETE',current_stage='FEATURE_IMPLEMENTATION_COMPLETE_USER_UAT_DEFERRED',last_verified_checkpoint='CONTINUATION_FINAL',
        active_run_ids=[],active_openclaw_run_id=None,in_progress=[],blocked=[],remaining=[],
        deferred=['User UAT/browser/visual acceptance until separately requested','Actual Windows logon/reboot trigger test','PR merge/go-live only on separate authorization'],
        ui_uat='DEFERRED_BY_USER',code_snapshot=snapshot_info,deployment_current=deployment,
        next_exact_action='Tiếp nhận yêu cầu tiếp theo hoặc lỗi thực tế. Không replay các completed units; UAT chỉ khi người dùng yêu cầu riêng.',
        feature_matrix='FEATURE_COMPLETENESS.md',repository_integration='THREE_REPOSITORY_INTEGRATION.md')
    state.setdefault('deployment_state_history',[]).append(state.get('deployment_state',[]))
    state['deployment_state']=[deployment,{'demo':demo,'delivery_task':'Running / ALIVE; idle no inference verified; physical logon/reboot deferred'}]
    state['repositories']['demo'].update(head=head,branch='codex/mini-task-manager-ready',dirty=True,tracked_clean=True,untracked_preserved=['dev/'])
    state['openproject'].update(native_children=sorted({*state['openproject'].get('native_children',[]),380,381,382,child}),business_done=False)
    state['openclaw'].update(execution_workspace='/home/openclaw/engineering/'+unit,provider_gate='OFF/inactive; shared quota unchanged; no fallback',personas='Actual BA/PM system prompt and Dev/Reviewer/QA root-owned bootstrap + selected skill reports verified')
    state['demo_artifacts'].update(latest_head_sha=head,latest_pr_url=pr,latest_native_child=child,latest_run_id=run_id,latest_tests=tests)
    state['completed']+=['Continuation feature/three-repository matrices COMPLETE, current source serving parity verified; UAT deferred']
    state['changed_files']=sorted({*state['changed_files'],*[p['path'] for p in manifest]})
    state['test_evidence']=['CONTINUATION_VERIFICATION.json','E2E_EVIDENCE.md','continuation-monitor-live.json','continuation-control-center-final.json','demo-service.json','runs/*/JUnit+activation+trajectory+history']
    write('IMPLEMENTATION_STATE.json',json.dumps(state,ensure_ascii=False,indent=2));refresh()
    print(json.dumps({'status':'FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED','snapshot':str(snapshot),'files':len(manifest),'app_head':head,'application_tests':tests},ensure_ascii=False))


if __name__=='__main__':finalize()

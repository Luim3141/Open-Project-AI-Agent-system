"""Render the evidence index; no service calls and no inferred live mutation success."""
import ast,collections,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
def write(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
matrix=read('matrix.json');tools=read('telegram-tool-schemas.json')
for name in ['get_active_agents','get_blocked_tasks','get_pending_approvals']:
    if not any(r['module']=='Telegram tool' and r['feature']==name for r in matrix):
        matrix.append(dict(id=f'F{len(matrix)+1:03}',module='Telegram tool',feature=name,source='openproject/ai/telegram-ai/app/tools.py',method='Actual read adapter + isolated contract',expected='Scoped current-state Observer response, no history inference',actual='',status='NOT TESTED',evidence=[]))
if not any(r['module']=='Gateway MCP' for r in matrix):
    matrix.append(dict(id=f'F{len(matrix)+1:03}',module='Gateway MCP',feature='97 action tools, filtered by role, /mcp transport',source='openproject/ai/gateway/app.py:142',method='Source inventory + isolated MCP transport tests',expected='Same Service validation/RBAC, no alternate mutation path',actual='',status='PARTIAL',evidence=[]))
live=read('main-integrations.json');live_tools={r['tool'] for r in live['tools'] if r['status']=='READ_RETURNED'}|{'get_active_agents','get_blocked_tasks','get_pending_approvals'}
live_commands={r['action'] for r in live['commands'] if r['status']=='READ_RETURNED'}
live_commands|={'observer_task_progress','observer_active','observer_run_details','list_work_packages','get_work_package','knowledge_search','list_execution_monitors','get_execution_monitor','engineering_report_read'}
extra=read('additional-reads.json')['reads']
live_commands|={r['action'] for r in extra if r['status']=='READ_RETURNED'}
live_tools.add('get_project_options')
denied={r['action'] for r in live['commands'] if r['status']=='FAIL'}
source=ast.parse((ROOT/'openproject/ai/gateway/service.py').read_text(encoding='utf-8-sig'))
mutations=set()
for n in source.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MUTATIONS' for t in n.targets):mutations.update(ast.literal_eval(n.value))
mutations|={'delegated_control','delegated_preview','engineering_report_schedule_set','engineering_notification_read'}
mutations|={'engineering_report_schedule_update','engineering_notifications_dismiss','engineering_report_generate','engineering_github_sync','engineering_plan','engineering_cancel','engineering_resume','reconcile_request'}
writes={'create_task','update_task','request_task_execution','resume_task','pause_task','set_execution_mode','request_github_sync'}
for r in matrix:
    mod=r['module'];feature=r['feature'];status='PARTIAL';level='SOURCE / ISOLATED CONTRACT';evidence=['qualification.json'];actual='Có kiểm kê source; chưa đủ bằng chứng MAIN riêng cho chức năng này.'
    if mod=='Gateway command':
        if feature in live_commands:status='PASS';level='MAIN READ';evidence=['main-integrations.json','semantic-read-checks.json','browser-uat.json','additional-reads.json'];actual='Đã đọc qua actual Gateway/Native hoặc owner bridge; chỉ nghiệm thu read path và phạm vi snapshot.'
        elif feature in denied:status='PARTIAL';level='MAIN DENIAL';evidence=['main-integrations.json'];actual='Dedicated Telegram token nhận 403 ENGINEERING_CAPABILITY_REQUIRED. Không mở rộng quyền; chưa nghiệm thu positive path qua token này.'
        elif feature in mutations:status='BLOCKED BY AUTHORIZATION';level='ISOLATED CONTRACT / NO NEW MAIN WRITE';actual='Không thực hiện mutation mới trên MAIN. Các suites isolated trong REGRESSION_RESULTS không chứng minh live E2E riêng cho action này.'
        else:status='NOT TESTED';level='SOURCE INVENTORY';actual='Chưa có invocation MAIN riêng được lưu trong audit; không suy PASS từ health hoặc suite chung.'
    elif mod=='Telegram tool':
        if feature in live_tools:status='PASS';level='MAIN ADAPTER READ';evidence=['main-integrations.json','semantic-read-checks.json','additional-reads.json'];actual='Actual ToolExecutor → Gateway → Native/Observer; không đồng nghĩa mọi natural-language phrasing đã qua Gemini.'
        elif feature in writes:status='BLOCKED BY AUTHORIZATION';actual='Strict schema/confirmation/idempotency contracts isolated; không gọi mutation MAIN.'
        else:status='NOT TESTED';actual='Declaration có thật, chưa chạy positive MAIN adapter riêng.'
        r['input_schema']=next((t['parameters_json_schema'] for t in tools if t['name']==feature),{})
    elif mod=='Gateway route':
        actual='Route/HTTP contract nằm trong gateway-openapi.json và source; Main evidence chỉ áp dụng request đã ghi nhận.'
        if feature.endswith('/health') or feature.endswith('/api/v1/commands'):status='PASS';level='MAIN READ + ISOLATED ERRORS';evidence=['main-integrations.json','final-smoke.json','qualification.json']
    elif mod=='Gateway MCP':actual='97 names mirror Command enum; isolated StreamableHTTP/session/deny tests. Không dùng session MCP MAIN mới trong audit.'
    elif mod=='n8n workflow':level='DEPLOYED CONTRACT + HISTORICAL EXECUTIONS';evidence=['n8n-inventory.json','n8n-contracts.json'];actual='Active workflow thật; auth/inputs/targets/error/retry contracts + history refs. Không trigger mới từng business branch; history success không tự chứng minh side effect.'
    elif mod=='Telegram':
        evidence=['telegram-live-global.json','telegram-live-postfix.json','final-smoke.json','integrity-final.json']
        if feature in ['poller/token/webhook/one-consumer','Vietnamese multi-turn #398','restart conversation persistence','network/Gateway reconnect','Gemini exact model/quota/tool feedback']:status='PASS';level='ACTUAL OWNER LIVE + MAIN RESTART';actual='Bot35→36 global read/SDK function feedback,32/34 acceptance/count; exact resolved3.5lite; final polling lock and persisted conversation. Reconnect evidence is controlled restart, not arbitrary outage campaign.'
        elif feature=='reply notification397 context':status='PASS';level='HISTORICAL OWNER LIVE';evidence=['../telegram-observer/live-reply-397.json'];actual='Owner19 Reply to completion16 resolved397 despite old memory391; re-read current durable context. Không gửi notification mới.'
    elif mod=='Runtime':level='HISTORICAL REAL EXECUTION + CURRENT READ';evidence=['../agent-studio-v2-stabilization/demo-final.json','../agent-studio-v2-stabilization/demo-tests.json','semantic-read-checks.json'];actual='Actual Nov6 execution398/64tests, current terminal history/canonical acceptance. Không chạy lại hoặc dùng fixture làm live run.'
    elif mod=='Studio':evidence=['browser-uat.json','../agent-studio-v2-stabilization/demo-final.json'];level='MAIN TERMINAL UI + HISTORICAL RUNNING';actual='3 real stage nodes, Dev file/PR15, task393 empty, browser Back/reload398. RUNNING evidence là Nov6; poll/error/mobile không được claim mới đầy đủ.'
    elif mod=='Command Center':evidence=['browser-uat.json'];level='MAIN UI READ';actual='9tabs,6roles, actual loaded run inspector, rendered/raw/export report. Không bấm controls gây mutation.';status='BLOCKED BY AUTHORIZATION' if 'Intake' in feature else 'PASS'
    elif mod=='OpenProject':evidence=['main-integrations.json','integrity-final.json'];level='MAIN READ / ACL';actual='Projects5/6, Native task398v10, unauthorized/cross-project denial; full project5/roles/workflows fingerprints unchanged. Chưa thực hiện CRUD mới.'
    elif mod=='GitHub':evidence=['github-pr15.json','github-pr15.diff','semantic-read-checks.json'];level='MAIN READ + HISTORICAL AI REVIEW';actual='PR15OPEN/head7cea/one test file+17; AI review PASS/QA64. Remote CI checks0, human reviews0; không claim remote CI PASS.'
    elif mod=='RAG':evidence=['rag-main-queries.json','browser-uat.json','rag-recovery-probe.json','semantic-read-checks.json'];level='MAIN RETRIEVAL / UNQUALIFIED ANSWERABILITY';actual='Known398/384/390 và negative lexical queries, live NativeACL/version/citations. Answerability UNVERIFIED_RETRIEVAL, semantic quality gate chưa đạt. Một UAT lượt trước không có results; probe/rerun thành công, root cause chưa chốt.'
    elif mod=='Notifications':evidence=['notification-main-history.json','../telegram-observer/live-reply-397.json','qualification.json'];level='HISTORICAL DELIVERY / ISOLATED FAILURE CONTRACT';actual='7 durable SENT, completion397msg16, awaiting398msg22; không398TASK_COMPLETED. Offline/retry/duplicate contract isolated, không gây outage hay gửi mới.'
    elif mod=='Operations':status='PASS';level='MAIN CONTROLLED RESTART + INTEGRITY';evidence=['bot-deployment.json','core-candidate-v2/deployment.json','integrity-final.json','final-smoke.json'];actual='Image-only controlled rollouts; OFF/idle; same data/config; no replay; default bot tag final qualified image.'
    r.update(status=status,level=level,actual=actual,evidence=evidence)
    r['input_output']='Tool schema: telegram-tool-schemas.json' if mod=='Telegram tool' else ('Command/HTTP schema: gateway-openapi.json; Service validates arguments' if mod.startswith('Gateway') else 'Typed/sanitized evidence packet referenced below')
    r['risk_error']='Current project/RBAC; explicit error/unknown; bounded source window. Mutation requires exact approval; no automatic replay.'
write('matrix.json',json.dumps(matrix,ensure_ascii=False,indent=2))
counts=dict(collections.Counter(r['status'] for r in matrix))
lines=['# Functional matrix — 12/11/2026','',f'{len(matrix)} dòng: {json.dumps(counts,ensure_ascii=False)}. Đây là danh mục coverage, không phải tỷ lệ hoàn thành sản phẩm. PASS chỉ áp dụng evidence level ghi ở dòng tương ứng; không suy PASS live mutation từ isolated tests.','', 'Input/output: [Gateway schema](gateway-openapi.json), [29 Telegram schemas](telegram-tool-schemas.json), [n8n node/auth/error contracts](n8n-contracts.json). Chi tiết source, expected/actual, input/output, risk và evidence của từng dòng: [matrix.json](matrix.json).','', 'MCP có97 action names mirror Command enum; chưa có session MAIN MCP mới. Các read bị token engineering giới hạn403 là expected authorization boundary, không phải quyền để bypass.','', '| ID | Module / chức năng | Kết quả | Mức bằng chứng | Evidence |','|---|---|---|---|---|']
for r in matrix:lines.append('| '+ ' | '.join([r['id'],(r['module']+' / '+r['feature']).replace('|','/'),r['status'],r['level'],', '.join(f'[{Path(e).name}]({e})' for e in r['evidence'])])+' |')
write('FUNCTIONAL_MATRIX.md','\n'.join(lines))
write('BUG_FIXES.md','''# Bug fixes — đã triển khai MAIN

| Lỗi / mức | Repro và root cause | Sửa tối thiểu | Xác minh |
|---|---|---|---|
| F1 P1: false DONE #398 | Owner msg30 gọi “đã làm xong (DONE)” dù AWAITING_OWNER; output LLM chưa ràng buộc business acceptance | engine.py ground kết luận DONE bằng matching live Native business DONE + FULLY_COMPLETED + không source conflicts; lưu câu đã ground vào memory | Baseline immutable 4/5 tests fail; green62; Owner32 nói chưa DONE; telegram-live-postfix.json |
| F2: version27 bị gọi27steps | LLM đọc checkpoint revision như số bước; thiếu typed count/semantics | tools.context_result thêm completed_step_count/version_semantics, giữ khi truncation; system instructions | Actual11steps; Owner34 giải thích đúng revision27/11steps; checkpoint contracts |
| F3 P1: global read loop | GeminiTG-R06 lặp5rounds; registry chỉ có task/current-agent reads, TG-R07 suy noBlocked không state filter | 3 Empty strict tools get_active_agents/get_blocked_tasks/get_pending_approvals → Observer hiện hành, không backend mới | Owner35→functioncall→Gateway→feedback→36 PASS, resolved3.5lite, budget18/20 |
| F3b: global DTO mất root project và quá lớn | MAIN pending3rows443357B bị context truncate; project ở nested system | Explicit authorized project_id + compact task/stage state; giữ source bounds/freshness/conflicts, detail artifacts dùng detail tools | Test fixture omitted project + huge artifacts RED→GREEN; final pending8660B, untruncated; semantic13/13 |
| F4: read errors bị mask503 | Actual report503 quan sát, sau đó cùng report200. Ruby RED chứng minh upstream409/429 bị remap503; chưa biết upstream code của lượt503 đầu | Core private bridge_error_status dùng chung, giữ400..599/Retry-After/requestID cho observer/command/report/execution/history | Report9status cases, execution/history18cases, busy controller; MAIN report render/raw/export PASS. Không claim lượt503 đầu chắc là429 |
| F5: malformed execution offset503 | MAIN offset=bad503, offset negative422 | Integer(exception:false), reject invalid/negative422 trước Gateway | RED log; Ruby no-Gateway-call assertion; final MAIN bad/-1→422,0→200 |

Product files chỉ4: Core qldapm_ai_controller.rb và Telegram engine.py/tools.py/system_instructions.py. Không đổi Gateway, n8n, orchestrator, dependencies, keys, model, caps hoặc acceptance gates. Tests cũ được chỉnh theo current contract: malformed QA422, canonical resume eligibility, extracted Knowledge partial, WF11 legacy readonly input. Không hạ điều kiện production để làm tests xanh.

RAG UI: một lượt không xuất hiện kết quả; probe sau query200~10.55s/direct200~11.09s và full rerun14/14PASS. Chưa xác định root cause của lượt fail; không tune timeout/threshold hoặc xóa evidence để nhận FULL PASS.
''')
write('REGRESSION_RESULTS.md','''# Regression results

Evidence: qualification.json + logs, candidate qualification/deployment files; offline Docker --network none, temporary fixture stores, không credentials/Main mutations.

| Kiểm tra | Kết quả và giới hạn |
|---|---|
| Gateway51modules | 423 tests run,22skipped, exit0 (401 passed,22 skipped). Không gọi đây là423 passed |
| Telegram | 62 tests PASS trên source hiện hành; immutable baseline acceptance5cases có4fail đúng RED |
| Host checkpoint/CommandCenter/Knowledge | 12 tests PASS |
| Node workflow contracts | 6 tests PASS |
| Core deployed candidate | report9upstream codes; execution/history18cases + invalid offset/noGateway; busy bridge PASS. Ruby fixtures, không giả live outage |
| MAIN semantic reads | 13/13assertions TRUE; actual global tools compact/scoped;18original adapters returned |
| MAIN full browser | Final14/14groups PASS, JS errors[];9tabs,workforce/runinspector,report raw/export,RAGcitations,Studioevidence/back/reload. Có lỗi intermittent trước đó, lưu riêng và ghi remaining |
| MAIN final smoke | 6/6assertions TRUE: offsets/auth/onepoller/tag |
| MAIN data/source integrity | 21/21TRUE; see DATA_INTEGRITY |

mutation-contracts.json là lần đầu lỗi import obsolete proposal_aggregation; KHÔNG PASS. Final423 suite bỏ modules legacy proposal_aggregation/control_center/control_center_authorization không còn runtime module, giữ initial logs và ghi gap. Gateway image không chứa7legacy host files; parity kiểm tất cả files deployed, absent set bằng baseline image. Không fabricate full host/runtime parity của modules không triển khai.

Không rerun productionTask, approve398, merge/deployPR15, trigger từng n8n branch, reset quota hay force outage. Natural-language TG-R08/R09/R10 chưa đầy đủ liveGemini vì reserve2/20calls. Static declarations/adapter tests không thay thế những lượt này.
''')
write('E2E_RESULTS.md','''# End-to-end results

Evidence levels: SOURCE; ISOLATED CONTRACT; MAIN READ; HISTORICAL REAL EXECUTION; ACTUAL OWNER LIVE; NEW MAIN MUTATION (không thực hiện). Mỗi PASS giới hạn trong flow thực sự quan sát.

| Flow | Kết quả | Bằng chứng / ranh giới |
|---|---|---|
| A Telegram→Gemini SDK→functioncall→Gateway→Native/Observer→feedback→reply | PASS các lượt Owner thực tế; PARTIAL toàn bộ catalog NL | telegram-live-four-turns.json lưu lỗi ban đầu; postfix32/34 đúng acceptance/count; global35→36 READ_TOOL get_active_agents project6 correlationc9b94dff-c0e2-4009-92eb-98c0fbe5b010, actual resolved3.5lite, no loop. Final DTO-only change có adapter13checks/62contracts, chưa thêm model call |
| B Telegram authorized control/create/update/resume | BLOCKED BY AUTHORIZATION trên MAIN; isolated contracts PASS | 7write declarations strictschema/confirmation/auth/version/idempotency. Không autoapprove/runOnce/AUTO/createUnit để kiếm evidence; không suy live control PASS |
| C BA/PM→Dev→Reviewer→QA→READY | HISTORICAL REAL EXECUTION verified; không newrun | Nov6 plan76f13288→Task398runde391b2f, Dev12/Reviewer1/QA5provider calls,64JUnit/0fail, only tests/test_health_regression.py. Current Nativev10 READY FOR RELEASE/AWAITING_OWNER_APPROVAL. Existing18coding receipts requested3.5lite nhưng historical resolved version không lưu; BA/PM2actualresolved đúng. Demo evidence docs/agent-studio-v2-stabilization/demo-final.json + demo-tests.json |
| D CommandCenter→AgentStudio→Native/artifacts/GitHub | PASS observed MAIN terminal UI; PARTIAL all branches | browser-uat.json14groups/JSerrors0;6roles,3stage nodes, Devfile/PR15,393empty,Back/reload398. Actual RUNNING screenshots làNov6; không gán currentOFF thành running. RAG finalPASS nhưng một lượt trước không results/rootcauseunknown |
| E acceptance→outbox→n8n→Telegram→Reply context | HISTORICAL OWNER LIVE PASS; no fresh proactive send | 397approved→completedmsg16; Owner19Reply16 read397 despite conversation391→reply20 (../telegram-observer/live-reply-397.json). Durable current7SENT allattempt1;398PR21/await22, no398completed. Notification retry/offline/idempotency isolated, không mô phỏng bằng live send mới |

Additional actual integrations: GitHubPR15OPEN/head7cea +17/-0 inonefile; noCI/humanreviewcheckpassed claims. n8n17active workflow contracts/history; không phải17freshE2Epasses. RAG known398/384/390 + negative query/citations/currentNativeACL/version lexical retrieval; answerability gate chưa đạt, không generate answer để bỏ gate.

Controlled bot/Core+Gateway restarts: config hashes/volumes/data giữ nguyên; conversation/pairing/outbox persist, no new agent_runs/tasks/checkpoints, workerOFF/active0; integration-final/mainread evidence khác fixture.
''')
integrity=read('integrity-final.json')
write('DATA_INTEGRITY.md','''# Data integrity — MAIN before/after

21/21 assertions TRUE, fresh fingerprints và full critical SQLite table hashes: [integrity-final.json](integrity-final.json). Snapshot ban đầu: [baseline.json](baseline.json). Không restore database.

- Native project5 + existing project6 WorkPackages/roles/workflows/users/password fingerprints giữ nguyên. Task398id/subject/version10/description/dates/customfields khớp initial read; chưa DONE.
- Gateway original rows/prefixes retained. Full agent_runs/agent_tasks/ai_queue/ai_runs/engineering_checkpoints/plans/unit_definitions/control/owner_commands/tokens bằng pre-Core-release readonly SQLite backup; không replay/history loss.
- Catalog14, modeOFF/active0; engineering receipt count620 giữ nguyên. Bot budget18/20, không reset. Telegram incoming updates/audit/memory/rate/budget có tăng do các lượt đã được phép; không đòi full TelegramDB hash bất biến.
- Pairing/paircodes/confirmations/notification_context/outbox giữ nguyên.7SENT, no398TASK_COMPLETED. Conversation398 và global reply tồn tại sau restart.
- .env/secrets/config hashes bằng baseline;17n8nworkflows/credentials bằng baseline, n8ncontainerID/start unchanged. Chỉ lưu hashes, không credentials.
- Core82deployed files match current host; Telegram deployed source match; Gateway unchanged image/deployed source match.7hostlegacy modules absent in both baseline andcurrentimage, không claim deployed parity cho files không tồn tại.
- Only4product source files đổi. Docker env/mount/network/restart unchanged; only qualified image replacements. Default local bot tag pinned334963; Core/Gateway exact images trong FINAL_REPORT.

Rollback: image-only to previous botbd305 / Coredb29 (original035/d0bdd retained), keep volumes/config/catalog14/current data; use guarded operator manifests and idle check. Không rollback bằng DB snapshot cũ, không delete newly recorded history. Existing product demo head01d765 remains; PR15 notmerged/deployed.
''')
write('REMAINING_ISSUES.md','''# Remaining issues / chưa nghiệm thu đầy đủ

1. **FUNCTIONAL PARTIAL**, không FULL PASS: mutation/control flows trên MAIN chưa được phép thực hiện mới. Không cần người dùng duyệt lại những quyết định đã chốt; nếu muốn nghiệm thu livewrites cần một scope cụ thể mới, không tự đổi gates.
2. RAG lexical retrieval/citations hoạt động, nhưng semantic answerability gate vẫn FAILED/FROZEN/UNVERIFIED_RETRIEVAL theo evidence hiện hành. Không giảm threshold, reindex toàn bộ hay generate answer để che gate.
3. Một UI RAG lượt trước không hiện results; subsequent trace200~11s/full14checksPASS. Chưa có metadata đủ để kết luận abort20s hay rootcause khác. Report503 ban đầu tương tự chưa biết upstreamcode; masking contract đã sửa nhưng không gọi đó là proof initial429.
4. TG-R08/R09/R10 natural-language globalblocked/pending/allartifact wording chưa đủ fresh Gemini/Telegram loops; direct adapters semantic proof có, globalactiveOwner35→36 có. Budget18/20, reserve2; không tăng quota/reset hoặc đổi model.
5. 17n8nactive contracts/history không thay thế fresh trigger+verifiedbusinesssideeffect của từng branch. Offline/retry/duplicate cases dùng isolatedtests; không tạo outage/sendspam để đóng gate.
6. GitHubPR15 có0remoteCIchecks/0humanreviews; local AIReviewerPASS+JUnit64 khác remoteCI.398 vẫn cần Owner acceptance; không tựapprove/merge/deploy.
7. Historical18codingreceipts requested3.5lite nhưng khôngpersist resolvedversion; không backfill dữ liệu giả. New bot receipts có actualresolved3.5lite. Metadata access xác minh đúng3.5lite, không inference thêm.
8. MCP action catalog/source/isolatedtransport verified, chưa dùng newMAINMCPsession qua đủroles. Các legacy modules absent được exclude rõ; commandsNOTTESTED trong matrix giữ nguyên.
9. Performance/multi-tab/tail/mobilefullcampaign DEFERRED ngoài task này; historical p95gate chưa đóng. Không dùng nó để phủ nhận những functional reads đã PASS.

Không còn lỗi P0 đã được tái hiện chưa sửa. Các F1–F5 đã deploy và targeted regression pass; coverage gaps/intermittentRAG vẫn được giữ công khai, không đảm bảo toàn hệ thống không còn lỗi.
''')
images=integrity['containers']
write('FINAL_REPORT.md',f'''# QLDAPM — functional audit & recovery, 12/11/2026

**Kết quả: FUNCTIONAL PARTIAL.** Đã sửa và triển khai các lỗi được chứng minh F1–F5; các read/liveOwner/UI cụ thể PASS. Không tuyên bố FULL PASS cho live mutation, mọi workflow branch hoặc semantic RAG khi chưa đủ bằng chứng. Một agent thực hiện; không GUI/subagents, không task/run/catalog mới.

- Telegram Owner32/34 xác minh chưaDONE và revision27≠11steps;35→36 dùng get_active_agents toànproject6, feedback và câu trả lời đúng, khôngloop. Actual resolved gemini-3.5-flash-lite; budget18/20 giữ reserve2.
- MAIN18readadapters +3global tools và13semanticassertions; unauthorized/crossprojectdenied. Final UI14/14groupsPASS,0JSerror; RunInspector thực sự loaded, Reportsrender/raw/export,RAGcitations,Studio3stages/Devfile/PR15/Back/reload. Intermittent RAG lượt trước chưa xác định rootcause được ghi rõ.
- Isolated regression: Gateway423run/22skip, Telegram62PASS, host12PASS, Node6PASS, CoreRuby status/offset/RetryAfter contractsPASS. MAINfinalsmoke6/6; integrity21/21. Không gộp những suite này thành liveE2E.
- #398 Nativev10 READY FOR RELEASE/AWAITING_OWNER_APPROVAL, historicalNov6Dev/Reviewer/QA64tests, PR15OPEN. SupervisorOFF/idle, catalog14, no newruns/inferenceengineering/nofalsecompletion. #397 historical notification16→OwnerReply19 giữ đúngcontext.
- n8n17active workflow inventory/input-output/auth/error/retry/history;7SENToutboxretained. RAG actuallexicalknown/negativequeries/citations/NativeACLversionPASS; semanticanswerabilitychưaqualified. GitHubPR15readverified; remoteCI0 không gọiPASS.

| Service | Image MAIN sau audit | Thay đổi |
|---|---|---|
| Core | `{images['qldapm-openproject-web-1']['image']}` | Shared HTTP error forwarding và offset validation |
| Gateway | `{images['qldapm-ai-gateway-1']['image']}` | Image/source giữ nguyên; controlled restart cùng Core |
| Telegram | `{images['qldapm-ai-telegram-ai-1']['image']}` | Ground acceptance/count, globalreadtools/compactDTO, resolved model audit |
| n8n | `{images['qldapm-n8n-main']['image']}` | Container/workflows/credentials giữ nguyên |

Only4productfiles đổi; architecture/checkpoint/tests/evidence đi cùng. Rollout manifests [bot](bot-deployment.json), [Corev2](core-candidate-v2/deployment.json), hashes/persistence [integrity](integrity-final.json). No DBrestore, no config/model/key/cap/gate changes. Existing demohead01d765 unchanged, PR15notdeployed. Sourcebase commit`ee4bcf8`; audit commit được ghi ở checkpoint/handoff sau khi gitcommit hoàn tất.

Đọc [ma trận{len(matrix)}dòng](FUNCTIONAL_MATRIX.md), [E2E](E2E_RESULTS.md), [rootcause/fixes](BUG_FIXES.md), [regression](REGRESSION_RESULTS.md), [data integrity](DATA_INTEGRITY.md), [chưa nghiệm thu](REMAINING_ISSUES.md). Machine evidence giữ cả RED/initialfailures, không cherry-pick thành FULL PASS. Chính xác trạng thái coverage: `{json.dumps(counts,ensure_ascii=False)}`.
''')
print(json.dumps({'rows':len(matrix),'status_counts':counts},ensure_ascii=False))

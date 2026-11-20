"""Render evidence-based handoff; statuses deliberately do not promote isolated tests to MAIN."""
import collections,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def write(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
def cell(value):return str(value or '—').replace('|','/').replace('\n',' ')
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(cell(c) for c in row)+' |' for row in rows]])
gold=read('gold.json');evaluated=read('gold-final.json')['results'][0]['rows'];ui=read('browser-uat.json');live=read('main-integrations.json');schema=read('telegram-tool-schemas.json');integrity=read('integrity-after.json');final=read('final-integrity.json');bot=read('bot-deployment.json');release=read('deployment.json');telegram=read('telegram-live-rag.json')
images='\n'.join('- '+name+': `'+image+'`' for name,image in {**release['images'],'telegram':bot['image']}.items())
maps={
 'list_projects':'identity (mỗi project đã pair)', 'get_project_options':'get_project_options',
 'search_tasks':'list_work_packages', 'get_task_details':'get_work_package',
 'search_knowledge':'knowledge_search; mode answer → extract, không inference Gateway',
 **{k:'observer_task_progress' for k in ['get_task_progress','get_task_agent_runs','get_current_agent','get_task_artifacts','get_github_prs','get_review_results','get_qa_results']},
 **{k:'observer_run_details' for k in ['get_run_details','get_run_errors','get_checkpoint_status']},
 **{k:'observer_active(summary_only)' for k in ['get_worker_status','get_queue_status','get_system_health','get_n8n_status']},
 **{k:'observer_active(state/limit=50)' for k in ['get_active_agents','get_blocked_tasks','get_pending_approvals']},
 'create_task':'create_work_package → exact Gateway proposal approval', 'update_task':'update_work_package → exact proposal approval',
 'request_task_execution':'engineering_run_once', 'resume_task':'engineering_resume',
 'pause_task':'engineering_control(PAUSED)', 'set_execution_mode':'engineering_control', 'request_github_sync':'engineering_github_sync'}
assert set(maps)=={t['name'] for t in schema['tools']}
observed={r['tool']:r for r in live['tools']};writes=set(schema['writes']);rows=[]
for tool in schema['tools']:
    name=tool['name'];write_tool=name in writes
    rows.append({'tool':name,'gateway':maps[name],'input':tool['parameters_json_schema'],'permission':'Paired numeric Owner + allowed project → Gateway fresh Native role/ACL; actor/project arguments forbidden',
       'main_status':'BLOCKED BY AUTHORIZATION' if write_tool else observed[name]['status'],
       'contract_status':'PASS isolated 67 Bot tests; Gateway relevant auth/approval/idempotency/fencing tests in 466 suite' if write_tool else 'PASS strict arguments/adapter contracts',
       'correlation_id':None if write_tool else observed[name]['correlation_id'],
       'evidence':'bot-candidate-tests.log; gateway-regression.log' if write_tool else 'main-integrations.json',
       'effect':'Preview/confirmation only until explicit scoped approval; receipt is not execution' if write_tool else 'Read DTO; observation freshness, source bounds and historical vs current semantics retained'})
write('gateway-tool-matrix.json',json.dumps(rows,ensure_ascii=False,indent=2))
mcp_count=len(read('mcp-smoke.json')['reads'][1]['response']['result']['tools'])
write('GATEWAY_TOOL_MATRIX.md',f'''# Gateway / Telegram tool matrix — 13/11/2026

**Gateway reads: PASS trong scope đã chạy; command contracts: PASS cô lập; MAIN mutation: BLOCKED BY AUTHORIZATION.**
29 declarations / 22 read / 7 write, không mở rộng quyền. [Schemas](telegram-tool-schemas.json), [DTO/correlation IDs](main-integrations.json), [matrix đầy đủ input/output/permission](gateway-tool-matrix.json).

{table(['Telegram tool','Gateway action','MAIN evidence'],[(r['tool'],r['gateway'],r['main_status']) for r in rows])}

Gateway có15 REST paths trong [OpenAPI hiện hành](gateway-openapi.json); local MCP session thực initialize/tools-list/identity18/P6/unauth401 đã kiểm, {mcp_count} tools được token này nhìn thấy: [MCP](mcp-smoke.json). Số tool được liệt kê không có nghĩa có quyền thực thi mọi mutation. Chẩn đoán schema lần đầu dùng sai nested arguments/isError được giữ [tại đây](mcp-smoke-schema-diagnostic.json), không tính PASS.

Source routing: `openproject/ai/gateway/app.py`, `catalog.py`, `service.py`; callers `telegram-ai/app/tools.py`, Core controller và AiBridge. REST command body action/arguments/project_id; MCP tools có arguments object và project_id. Error paths giữ typed4xx/5xx, Retry-After/request ID. Controller/Bot không trở thành một control plane khác.

[Semantic read assertions](semantic-read-checks.json): #398 READY FOR RELEASE/AWAITING_OWNER_APPROVAL, current agent null, global active0/OFF, pending có398 không397, checkpoint27=11steps, completed run không resumable; reviewer/QA PASS là lịch sử. GitHub live PR15OPEN, statusCheckRollup rỗng không phải remote CI PASS.

OFF/AUTO/PAUSED/RUN_ONCE, resume-fencing, stale approval, replay/idempotency, role/actor/project spoofing, Native denial, queue/runtime errors và HTTP status contracts được chạy trong suite cô lập. Không click/chạy các mode mới trên MAIN; không cấp quyền thông qua tài liệu. API route inventory/source coverage còn lại kế thừa [206 dòng audit trước](../functional-audit/FUNCTIONAL_MATRIX.md), không nâng tất cả thành PASS mới.
''')
# Preserve all 932 observed nodes; classify equivalent controls without claiming every repeated row was clicked.
inventory=[];unique={}
dom=read('main-dom-inventory.json')['controls'] if (OUT/'main-dom-inventory.json').exists() else ui['dom_inventory']
for index,item in enumerate(dom,1):
    tool=item.get('form_tool');status='NOT TESTED';evidence='DOM/source only; chưa click riêng';endpoint=item.get('href') or item.get('form_action') or 'Client JS/source handler; endpoint chưa chứng minh riêng'
    if item.get('tab'):status='PASS';evidence='browser-uat.json tab_'+item['tab'].removeprefix('tab-');endpoint='Client tab switch; no mutation'
    elif tool in {'knowledge_search','knowledge_file_search'}:
        status='PASS' if tool=='knowledge_search' or (OUT/'main-file-ui.json').exists() else 'NOT TESTED';evidence='browser-uat.json search + Gemini answer' if tool=='knowledge_search' else 'main-file-ui.json file-only extract/citation/readback, no Gemini'
    elif tool in {'sprint_risks','bug_triage'}:status='NOT TESTED';evidence='Không tạo analysis/provider records mới chỉ để click UI'
    elif tool:status='BLOCKED BY AUTHORIZATION';evidence='Không gửi business/index/schedule/control writes trên MAIN'
    row={**item,'dom_index':index,'page':'Command Center project6','endpoint':endpoint,'permission':'Authenticated Native membership / Gateway current role; disabled attribute không thay auth','actual_status':status,'evidence':evidence,'expected_effect':maps.get(tool,tool or item.get('href') or item.get('tab') or item.get('action') or 'Theo source/DOM')}
    inventory.append(row);key=(item['tag'],item['text'],item.get('href'),tool,item.get('tab'),item.get('action'))
    unique.setdefault(key,row)
write('command-center-inventory.json',json.dumps(inventory,ensure_ascii=False,indent=2))
write('COMMAND_CENTER_MATRIX.md',f'''# Command Center — actual MAIN UI / source inventory

**PARTIAL**, không tính mọi nút là PASS chỉ vì được render. Captured {len(inventory)} DOM controls, {len(unique)} unique control signatures; đầy đủ page/component label, endpoint, permission, expected effect, observed/blocked state trong [JSON](command-center-inventory.json). Scope project6, authenticated Owner18; các project/role khác không có authenticated browser session mới trong phase này.

{table(['UI / component','Observed result','Evidence level'],[(x['name'],x['status'],'MAIN headless Chromium clicks') for x in ui['checks']])}

{table(['Unique UI control / tool','Endpoint / effect','Status'],[(r['form_tool'] or r['tab'] or r['text'][:65] or r['action'],r['endpoint'],r['actual_status']) for r in unique.values() if r.get('form_tool') or r.get('tab') or r.get('action')])}

RAG: search/answer choice → actual Rails POST → Gateway selected quotes → rendered blockquotes/citations → pinned file read. [Actual Gemini answer DOM/quotes](browser-uat.json); [visible file-only extract](main-file-extract-visible.png) và [visible pinned read](main-file-read-visible.png) được kiểm không dùng Gemini. Native citations cũng được render trong search. File citations là logical source+checksum; không giả public URL mở được trên điện thoại. Ingest vẫn giới hạn registry/pin, chưa reindex trong phase này.

Mission, Pipeline, Workforce, Backlog, Execution, GitHub, Reports, Knowledge và Integrations đã mở thật. Workforce roles BA/PM/Dev/Reviewer/QA, run inspector/receipts, Reports rendered/raw/export, Studio3nodes398/artifacts/PR15, search393-empty, Back/reload398 đã kiểm. Native business READY FOR RELEASE tách engineering COMPLETED, không coi run COMPLETE là Owner acceptance.

Responsive390px: [visible MAIN bar](main-mobile.json) width284/scroll284, [screenshot](main-rag-mobile-visible.png). Browser harness đầu đo clientWidth trên inline form=0, nên số0x0 trong browser-uat không phải proof mobile; đã dùng visible search-bar bounding box để kiểm lại. [Isolated red→green CSS](mobile-form-red.json) chỉ là fixture thật CSS/Chromium, tách MAIN evidence.

Search và pinned-file read gặp503/network error không khóa UNKNOWN_WRITE; chỉ write transport-unknown mới giữ replay lock. Pinned-file read không xóa search citations hoặc clear pending/unknown của write khác. [File read outage RED→GREEN](file-read-outage-green.log), abort/counter/clear/newquery/stale ordering và CSRF JSON POST/deny/unknown verified bằng actual inline JS VM; không giả là đã ép outage trên MAIN.15UIgroups chạy trước final scopedfile-read fix; file-onlyextract/read được kiểm riêng sau fix, không gọi inference lại để làm mới screenshots. Trong UI navigation burst có429 rồi200 (network trace), rate limit vẫn giữ nguyên. Không chạy p95 campaign.

Task create/edit/approve/run/resume/AUTO/GitHub sync, report generation/schedule, notification dismiss, ingest và delegated actions **BLOCKED BY AUTHORIZATION** hoặc source-only; không phát sinh demoTask mới. Project selector/change-role, mọi repeated historical run/report/link, logout/session-expiry/recovery toàn UI: **NOT TESTED mới**; contracts không thay authenticated UAT.
''')
write('RAG_AUDIT.md','''# Second Brain / RAG audit

Architecture implemented: registered local sources / Native WP+activity ingestion → SQLite document/FTS/chunk store → local Ollama BGE-M3 (1024 dimensions, Cosine) → Qdrant → authorized hybrid RRF(k60) → source/chunk/Native proof validation → optional Gemini quote selection → citations/UI. Không model embedding mới, không dependency/provider/queue/orchestrator mới.

Baseline [metadata](baseline.json), [actual source examples/index audit](corpus-evidence.json), [Native-authorized snapshot](authorized-corpus.json). 484documents=445P5+39P6;2485chunks,2488points. 0emptychunks,0payload/chunk mismatch;3orphan/oldchunk points được validator loại, không xóa để làm sạch số liệu. indexed_vectors_count0 trên collection nhỏ không phải thiếu vectors. Whole point/payload SHA trước/sau c945eb2c94e435359a23f4ed0618b131fe639b96b690fd828938903984cfeba4.

Actor18 current Native visibility/version audit cho341P5/18P6 eligible docs. Không đưa toàn bộ484docs vào tool chỉ vì đã index. Chỉ2registered files hiện hành: P5 main-workflow-contract và P6 project6-integration-qualification; file cũ không có registry bị loại. Không nhận user filesystem paths/arbitrary URLs. Parser/size/DOCX archive/PDF bounded loader giữ nguyên; OCR không hỗ trợ.

Root causes/fixes: generic search bỏ registered files; cutoff0.65 quá cao với calibration; repeated chunks chiếm dense candidate window; lexical fusion ghi đè best file passage; snippet200cắt mất fact; answerNone vô điều kiện; query race/timeout20s/overflowUI. Dense poolmax200 + file poolmax50, dedup/RRF và exact literal reference priority chỉ sau ACL. Source batch proof không bỏ hash guards. No stopword/model/index change.

Default search không inference. Extract chỉ EXTRACTS_AVAILABLE. Web answer dùng existing Free-only Gemini.structured/limiter để chọn nguyên văn, không tools. Backend exact substring + source index + chunk hash + Native version/source pin; post-generation recheck role/ACL/version/activity/pin. Exact quotation không tự bảo đảm entailment/completeness: semantic/answer acceptance còn PARTIAL, không flip global quality gate.

Prompt injection source là untrusted data. Selector không write tools; Bot RAG batch hard-deny writes trước execution và các round sau. Unsafe URI/forged chunk/citation/Native binding fail closed. Runtime/DONE hỏi live cần Observer, không dùng lịch sử source để kết luận hoàn thành. Search outages/empty/denied/stale có reason riêng; provider errors ABSTAIN_PROVIDER. Không tự retry mutation/indexing.

Câu hỏi tài liệu/tri thức rõ ràng bằng tiếng Việt hoặc English được Bot đọc RAG trước model, kể cả hỏi lại câu cũ; không để model tự bỏ qua tool rồi dùng memory. Không có nguồn mới thì NO_EVIDENCE, không gọi model để suy diễn. Source references từ server được giữ ở footer và được gắn nhãn truy hồi, không phải xác nhận runtime. Những intent không rõ ràng vẫn phụ thuộc model routing; không tuyên bố mọi cách diễn đạt đều đã được nghiệm thu.

Public source [code](../../openproject/ai/gateway/knowledge_search.py), [answers](../../openproject/ai/gateway/knowledge_answer.py), [service](../../openproject/ai/gateway/service.py); details test/evaluation trong báo cáo riêng. Không reindex/cập nhật corpus hoặc đổi checksum allowlist trong phase này.
''')
evaluation_rows=[]
indexed={r['id']:r for r in evaluated}
for case in gold['cases']:
    result=indexed.get(case['id']);evaluation_rows.append((case['id'],case['partition'],case['group'],case['question'],', '.join(case['expected_source_ids']),('HIT' if result['hit'] else 'MISS') if result else 'SEPARATE CONTRACT',str(result['answer_fact_pass']) if result else 'NOT MODEL EVAL'))
write('RAG_EVALUATION.md',f'''# RAG evaluation — PARTIAL

[Gold40](gold.json): facts/citations xuất phát từ actual Native/file sources, expected facts assert nguyên văn; 8calibration +32holdout. 36retrieval cases và4runtime/unauthorized contract cases; không bịa positive sources. [Runner](evaluate.py) dùng BGE-M3/Qdrant thật, private SQLite backup và captured Native authorized doc-ID scope; **không phải40 MAIN/API/LLM answers**.

Baseline cutoff0.65:8/36 retrieval hits; final0.45:25/36 (69.4%), calibration6/8, retrieval holdout19/28. Các threshold exploration được giữ, không chọn lại labels để làm đẹp. DENSE_MIN_COSINE0.45 chọn bằng8calibration; cutoff thấp hơn có thể tăng irrelevant hits. Cân bằng source pool và literal reference fix có regression thật; raw RRF score không là probability hay answer confidence.

Naive extract all-fact diagnostic20/36 (55.6%), **không phải Gemini answer accuracy**. Missing cases: {', '.join(r['id'] for r in evaluated if not r['hit'])}. Strict expected-source matching có thể bỏ qua alternative source chứa cùng fact; không sửa labels sau test để ép PASS. Không chạy bulkGeminijudge hoặc40inferences.

Actual MAIN positive answer: browser-uat quotes đúng fixture purpose + “does not certify … Owner acceptance”, pinned source readback khớp; real provider receipt d07c1cb4-5b9e-4e98-9568-4d316d471fe2 resolved exact3.5lite. OwnerTelegram37→38 đúng nội dung nhưng chưa có technical footer. Sau ngày UTC mới, lượt39→40 tái hiện model bỏ tool/dùng memory; giữ failure riêng. Bản sửa67tests bắt buộc freshRAG cho câu hỏi tài liệu; lượt41→42 PASS có fresh search(modeanswer→Gatewayextract), sourcechecksum và resolvedexact3.5lite, chỉ1inference.

First MAIN longquery trước anchor fix: retrieval thiếu file nên Gemini ABSTAIN; preserve [failure](main-read-before-anchor.json), không gọi positivePASS. Final same question Web tìm đúng và supported. NegativeMars ban đầu upstream503→ABSTAIN_PROVIDER ([failure](main-negative-answer-upstream503.json)); không tính là semanticabstentionPASS. Sau6giờ và actualBotprovider success, một lượt negative mới nhận ABSTAIN/model_usedtrue/resolvedexact3.5lite: [packet](main-negative-answer.json). Không retry mù hoặc thay model. Initial MARS noresults→NO_EVIDENCE không cần inference; isolated false/forged/source-change/injection tests PASS.

{table(['ID','Partition','Group','Question','Expected source','Retrieval','Naive extract fact'],evaluation_rows)}

Không công bố FULL RAG PASS: cần representative answer evaluation nhiều nguồn/Vietnamese paraphrase, conflict/longdocument coverage và provider recovery mới. Không inference thêm hoặc nới cap trong phase này.
''')
write('BUG_FIXES.md','''# Proven bugs and changes

| Bug | Root fix / callers | Proof |
|---|---|---|
| Generic search excludes authorized registered files | service scoped file registry/pin/role pre/post, native_ids stays Native-only | integration-red→green; actual MAIN file search/answer/read |
| Answer always None | explicit search/answer/extract; Gemini structured quote selector+validation | answer-red/green; MAIN rendered supported quotes |
| Dense candidate starvation / file passage overwritten | bounded oversample, balanced file pool, dedup, preserve best chunk, batch exact chunk proofs | starvation-red/candidate-starvation; relevant regression |
| Dense cutoff too high | .65→.45 calibrated8cases; holdout separate | baseline8/36→final25/36, not perfect |
| Long exact source reference lost in common words | scoped generic literal reference priority and bypass lexical coverage filter | literal-anchor-red/green42tests; first MAINABSTAIN→same WebSUPPORTED |
| Old answer visible/new query late overwrites | abort + generation guard + clear at start/finally guard | actual inline JS RED→GREEN; no mutation replay change |
| Cold valid search exceeds20s UI timeout | knowledge110s aligns existingRails100s; controls15s unchanged | actual cold MAIN23.42s; JSdeadline regression |
| Search outage mislabelled no evidence/read unknownwrite | typed search status, read/write lock separation | outage-red; offline HTTP/JS contracts |
| Pinned-file read503/network also locks as unknown write | same bounded read-only transport, retains source citations and unrelated pending/unknown mutation locks | file-read-outage-red→green; actual final MAIN file-only extract/read |
| Knowledge mobile controls overflow | scoped wrap/min-width0/flexbasis | actualCSS red545>358→green358; MAINvisible284/284 |
| Retrieved instructions could request a write | pre-scan completebatch, schema+executor read-only RAG turn | injection RED writefirst→GREEN; no old MAIN bypass claim |
| Telegram model omits technical citation | append bounded validated server filechecksum / Nativeversion references | citation RED→67testsGREEN; final Owner41→42 fresh source/footer PASS |
| Repeated document question answered from memory without fresh tool | deterministic pre-model retrieval for explicit document/knowledge intent; empty fresh source abstains without model; same read-only gate/caps | actual39→40 failure; fresh-source RED2fail→67suiteGREEN; final41→42 livePASS |
| Empty-source outage mistaken for no evidence in Bot prefetch | retain SEARCH_UNAVAILABLE versus NO_EVIDENCE, never answer from memory or call model when source absent | telegram-empty-outage-red on prior image;67testsGREEN on finalimage; positive live path unchanged |

11product files changed across existing modules, no new dependency. Server citations distinguish retrieved sources from acceptance proof. Existing DONE guard, confirmation/idempotency and completion gates remain. No historicTask execution replay.

Harness failures retained/declared: initial unittest import aliases; missing hostPlaywright (used installed .venv); mobile new_page(viewport) wrong API corrected then inlineform clientWidth0 corrected to visible bar; MCP nested arguments/isError corrected. No product success inferred from these initial harness outputs. Existing release operator adds blank lines when rewriting .env; exact pre-release backup proves nonempty config lines unchanged except authorizedAI_IMAGE. No cosmetic rewrite of user config.
''')
write('REGRESSION_RESULTS.md','''# Regression / qualification

Immutable final Gateway candidate: **466run,22skip=444passed**,57module names in candidate-regression.json (read actual list; no claim every route live). Bot candidate **67PASS** including citation safety/fresh retrieval/missing-evidence abstention; previous pair qualification64BotPASS before follow-ups. [Candidate](candidate-regression.json), [Gateway log](gateway-regression.log), [final Bot log](bot-candidate-tests.log). FinalCoreonly file-read fix reused unchanged qualifiedGateway image, reran inlineJS/mobilesizing/Erubi/parity; no inflated duplicate Gatewaycount.

Native/project/actor ACL, owner approvals, idempotency/stale/conflicting snapshots, run/resume/fencing/catalog14, workflow/business acceptance, queue/supervisor, GitHub/reporting/notification/n8n lifecycle, knowledge chunk/index/source integrity and injection tests run offline networknone with tempDB.22skips remain skips, notPASS. No new MAIN writes hidden inside suites.

Actual inlineJS Node VM PASS for CSRF/JSON POST, denied/unknown-write handling, request ordering, visibility/reconnect cleanup and added knowledge race/deadline cases. Native RailsErubi both changed templates compile. New RAG isolated red/green cases and mobileCSS green retained. Source/image parity Core82/Gateway115/Bot10,7legacyhostGWmodules absent unchanged.

Actual MAIN:22readtools,9semantic assertions,5MCP assertions,15browser groups,visiblemobile,read422/ACLscope/generation distinction. Before/after13critical checks + final source/corpus/PR invariants. These scoped checks are separate from global quality acceptance.

No p95/stress/security dependency scan campaign, no all-route MAIN mutation, no fresh demoTask/Agent run/Owner398approval. Browser negative role/session expiry not executed fresh; role/source-change contracts are isolated. Real provider503 is retained as failure/abstention behavior, not a flaky test rerun untilPASS.
''')
env=integrity['environment_comparison']
write('DATA_INTEGRITY.md',f'''# Data / configuration preservation

[Before](integrity-before.json), [after](integrity-after.json), [source/index/PR readback](final-integrity.json), [baseline](baseline.json). Actual before/after hashes, not inferred from healthy status.

{table(['Invariant','Verified'],integrity['checks'].items())}

Whole Native398row stable v10; READY FOR RELEASE/AWAITING_OWNER_APPROVAL. Engineering tasks/runs/queue/plans/checkpoints/unit catalog/control/tokens hashes unchanged. Catalog14/14 ceiling preserved, SupervisorOFF/active0; noTask399. Old620provider receipt rows byte-content hash preserved;8new Gateway receipts are purposeknowledge/actor18/runNone (count+generation ×4; one generation503, later explicit negativeABSTAIN). No new AgentRun. Bot bucket20769 used18→20; natural UTC20770 used2/20 (one memoryfailure + one freshfinalPASS), no manual reset/increase or hidden Gatewaymodelcall in Botextract.

All project5 rows / old project6 statuses,roles,membership,workflows,auth,password hashes stable. n8n workflow/credential fingerprint and container/image unchanged; pairing/codes/confirmations/notification contexts/outbox unchanged (7SENThistory), no completion sent for398. PR15freshGitHubOPEN/unmerged, checks0≠CIpassed; deployed mini app head01d765 unchanged.

Corpus metadata/pins/roles/contentlength and2485chunks/2488points unchanged. Whole point/payload fingerprint c945eb2c94e435359a23f4ed0618b131fe639b96b690fd828938903984cfeba4 matches exact baseline normalization.3orphan old points not deleted. No reindex/upsert/collection reset or volume deletion, no DB restore.

Only authorized image pins changed: AI_IMAGE, CORE_IMAGE/bridge image. Gateway config/key/model/caps exact hashes stable, Bot env/mount/network/restart semantic parity. .env whitespace diagnostic: raw-normalized hash changed; exact private pre-release backup matched before fingerprint, **every nonempty line exceptAI_IMAGE identical**; blank lines {env['old_blank_lines']}→{env['new_blank_lines']} from existing text-mode CRLF operator. [Diagnostic](integrity-after-line-ending-diagnostic.json) retained; this is not a secret/config-value change. No user credentials printed.

Source image parity all present files: Core82/Gateway115/Bot10; same7legacyGWabsences. Exact11changed product files in final-integrity.json. Baseline có8507untracked files; chỉ các file được giao trong whitelist được sửa/stage, không addall/clean/reset. Private DB/cookies/keys/cache/operator backup/contexts excluded from handoff commits.
''')
write('E2E_RESULTS.md',f'''# End-to-end evidence by level

{table(['Scenario','Observed','Verdict / boundary'],[
('Web→Rails→Gateway→RAG→Gemini→citations','Actual authenticated query, two correct quotes, source pin readback','PASS one positive; browser-uat.json + provider receipt'),
('Telegram→Commander→tool→Gatewayextract→Commander','FinalOwner41→42, fresh RAG before model,1exact3.5litecall, full sourcepin footer','PASS content/tool/citation for this repeated document question'),
('Negative no-answer model selection','Mars first503 preserved; after availability changed final actualmodelABSTAIN','PASS one semantic negative, not40answerqualityPASS'),
('Search/extract/default/invalid/wrongscope','MAINread200 and semanticassertions; invalidmode/limit/nativeids422; P5nofile6','PASS tested scope'),
('Gateway read adapters/global/checkpoint','22tools actual data,9semantic assertions; pending398 not397;27revision=11steps','PASS tested window, no assertion all projects unlimited'),
('Local MCP/REST parity','initialize/list/identityactor18P6 + auth401','PASS actual read, not JiraMCP'),
('Command Center→Studio/report/inspector','15UIgroups; real3nodes/artifacts/Back/reload/raw/export','PASS exercised; remaining controls PARTIAL'),
('Modes/run/resume/approval/confirmation','Isolated auth/idempotency/fencing contracts','PASS CONTRACT; MAIN BLOCKED BY AUTHORIZATION'),
('GitHub PR15','Fresh read OPEN/unmerged/no checks','PASS read; no merge/sync/deploy mutation'),
('Notifications/n8n','Existing17workflow fingerprints/outbox unchanged','PRESERVED; no fresh notification lifecycle E2E'),
('Provider/network error recovery','Actual503→ABSTAIN_PROVIDER then later newqueryABSTAIN; UI429→200; offline typederror contracts','PASS bounded observed recovery; no outage campaign/model substitution'),
])}

MAIN browser: [network/correlation/UI results](browser-uat.json), [mobile](main-mobile.json). Backend [read packets](main-read.json), [adapter reads](main-integrations.json), [MCP](mcp-smoke.json), [Telegram full sanitized receipt](telegram-live-rag.json). Initial negative/assertion failure retained; do not replace503 with success label.

Telegram final answer correctly explains “This fixture does not certify semantic retrieval quality or Owner acceptance”, and includes file:project6-integration-qualification#sha256=c48bfa4826cdf746703c64aab06177146a7ed7ade1aa59d767554a3e40388901. BOT_REPLY_SENT42 replies input41, freshREAD_TOOL precedes one resolvedexact3.5lite generation. Current naturalUTC20770 budget2/20; historical20769 remains20. Prior37→38 and failing39→40 receipts retained separately. No proactive/fake inbound or task/control mutation sent.

Lượt41→42 chạy Botimage38b5579b821c. Finalimage828cfb8a73dc chỉ sửa nhãn empty/outage SEARCH_UNAVAILABLE ở nhánh không có source;67tests trên exactimage và source/runtimeparity đã kiểm. Positive retrieval/model/citation path không đổi, không inference lặp chỉ để thay timestamp image. FinalCorefileUI đã kiểm sau bản sửa read-only transport.
''')
write('REMAINING_ISSUES.md','''# Remaining issues — explicit acceptance boundaries

| Status | Item / impact | Next bounded verification |
|---|---|---|
| DONE | Unified authorized file+Native search, exact source spans, explicit modes, UI race/functional deadline/wrap, read-only RAGturn, citation footer deployed | Source pins/rollout proofs |
| PASS | One real Web Gemini answer+citation+file read; one real Telegram content/tool answer; scoped reads/MCP/UI/regressions/integrity | Keep level of evidence; not global systemPASS |
| PARTIAL | Retrieval25/36;11strict-source misses; naive extract facts20/36 | Broader semantic/section/multi-source/Vietnamese evidence, no label rewriting |
| PARTIAL | Quote exactness does not guarantee answer relevance/completeness/conflict resolution | Representative factual answer eval; no free-generated-fact claim |
| PASS | Actual503 preserved; later explicit negative answeredABSTAIN by exactmodel; finalTelegram41→42 freshsource/checksum PASS | No inference needed again just to read progress |
| BLOCKED BY QUOTA (historical, resolved naturally) | Bucket20769=20 prevented a footer recheck; UTC20770 has2/20used | No quota override/reset; final live check now completed |
| BLOCKED BY AUTHORIZATION | MAIN create/update/run/resume/AUTO/PAUSED/Owneracceptance398/GitHubsync/indexing/report schedule/notification dismiss | Explicit exact preview approval only when actually needed; no new Task/unit to manufactureE2E |
| NOT TESTED | All RESTwrites/allUIbuttons/all repeatedrows, other project/role browser sessions, freshlogout/expiry/outageUI, freshnotification delivery | Targeted read/isolated/live proof separately, no invented coverage |
| UNSUPPORTED | OCR/image-onlyPDF, arbitrary upload/URL/client filesystem path, public mobile URL for local file citation | Existing source registry intentionally bounded; no new service |

No known new critical business-data regression from this change. No fullRAG/systemfunctional acceptance, no PR15merge or Owner398DONE. Existing env operator expands blank lines on image pin rewrite; semantic content proved unchanged, cosmetic rewrite deferred. Performance p95/stress campaign explicitly deferred by scope.
''')
write('FINAL_REPORT.md',f'''# Phase 4 — implementation deployed, functional acceptance PARTIAL

13/11/2026 Asia/Bangkok, branch `codex/agent-studio-v2-stabilization`, baseline `f3b713a`. Single agent, headless browser only. Source commit reference in [handoff](HANDOFF.md). Existing data/history/docs retained.

| Gate | Verdict |
|---|---|
| RAG | PARTIAL — retrieval25/36; actual grounded Web + real Telegram positive PASS |
| GATEWAY READ | PASS for22tools + actual scopedMCP/semantic reads |
| GATEWAY COMMAND CONTRACT | PASS isolated auth/approval/idempotency/fencing tests |
| MAIN LIVE MUTATION | BLOCKED BY AUTHORIZATION / NOT TESTED |
| COMMAND CENTER | PARTIAL —15UIgroupsPASS, controls not all live-exercised |
| SYSTEM FUNCTIONAL | PARTIAL |

Đã sửa và triển khai11productfiles: registered sources chung searchNative theo quyền/pin; fullchunk citation và boundedhybridranking; longliteralreference priority; explicit Gemini answer với exact quote validation; postgenerationACL/source recheck; typed outage/abstention; Telegram read-onlyRAGturn/technicalcitations; Rails caller/UI mode/clearabort/raceguard/deadline110s/wrap. Search/extract không hiddeninference. Model/key/caps/gates không đổi, không dependency mới.

FinalOwnerTelegram41→42: câu hỏi tài liệu được đọc RAG trước model, có sourcepin/checksum trong footer, trả lời đúng nội dung/khôngOwneracceptance,1resolvedexact3.5litecall. Lượt39→40 trước bản sửa đã tái hiện memoryreuse không freshRAG và được giữ làm failure proof. Bản cuối67Bot testsPASS; quota ngày20770 tự nhiên2/20, không reset/tăng cap (ngày20769 vẫn20).

MAINWeb trả lời đúngfixturepurpose và “does not certify … Owner acceptance”, citations/source pinreadback đúng. No-answerMars đầu tiên503→ABSTAIN_PROVIDER; sau khi provider hoạt động lại, một negativequery mới nhận actualmodelABSTAIN/resolvedexact3.5lite. Gold40 (8cal/32holdout),36retrieval realBGE/Qdrant/privateconsistentSQLite:8/36baseline→25/36final (holdout19/28), naiveextractfacts20/36; không coi là40Geminianswers hoặcFULLRAGPASS.

Gateway:29Bottools/22reads/7writes,15RESTpaths,87MCPtools visible currenttoken; exactactualidentity18/P6verified. ReadDTOsemantic:398AwaitingOwner/currentagentnull, globalactive0/OFF, checkpoint27=11steps. Controls chỉ có isolatedcontracts; không executeMAINmutation. CommandCenter9tabs, runinspector, Reportsraw/export, Studio3nodes/artifacts/Back/reload, RAGanswer/read vàvisiblemobile đã kiểm; everybutton coverage không được giả.

Regression Gateway466run/22skip=444passed; finalBot67PASS, NodeVMtransportPASS, RailsErubiPASS. Data/config/index before/after13checksPASS và sourceparityCore82/GW115/Bot10. Task398v10/catalog14/PR15OPEN/OFF preserved; n8n/pairing/outbox unchanged; old620receiptrows immutable,8authorizedRAGreceiptsnew. NoAgentRun/newTask/approval/merge/productPRdeployment/DBrestore/reindex/volume deletion.

Deployed images:

{images}

Rollback image-only using guarded release private manifests; keep currentDB/catalog/history/volumes. Baseline Core7923304/GW6edeea/Bot334963 retained, prior scopedrelease manifests preserve immediate rollback images. New runtimeproviderreceipts never erased through oldDBrestore. AI_IMAGE/CORE_IMAGE/bridgepins only; .env blank-line rewrite noted with exactsemantic backup proof, keys/configvalues unchanged. No push.

Reports: [RAG audit](RAG_AUDIT.md), [evaluation40cases](RAG_EVALUATION.md), [Gateway29matrix](GATEWAY_TOOL_MATRIX.md), [CommandCenterinventory](COMMAND_CENTER_MATRIX.md), [E2E](E2E_RESULTS.md), [bugs](BUG_FIXES.md), [regressions](REGRESSION_RESULTS.md), [data](DATA_INTEGRITY.md), [remaining](REMAINING_ISSUES.md). Source/API changes add optionalmodeonly; searchdefault compatible. Detailed inputschemas, sourcepins, actualfailures/correlationIDs and screenshots accompanyreports; private secrets/cookies/DB excluded.

Chưa kiểm: mọi livewrite, bulkGeminianswerquality và p95. Rủi ro còn lại: semanticmisses/provideravailability và intent không rõ ràng còn phụ thuộc modelrouting; toàn hệ thống chưa FULL PASS.
''')
print(json.dumps({'reports':10,'gold':len(gold['cases']),'tools':len(rows),'ui_nodes':len(inventory),'unique_ui_signatures':len(unique)},ensure_ascii=False))

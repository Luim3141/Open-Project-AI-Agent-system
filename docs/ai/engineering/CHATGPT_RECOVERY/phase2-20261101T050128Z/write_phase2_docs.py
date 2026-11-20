"""Publish evidence-backed continuation docs; no service/data mutation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
RUN=Path(__file__).parent;DOC=RUN.parent
def read(name):return json.loads((RUN/name).read_text())
manifest=read('source-candidate-final-manifest.json');images=manifest['images']
restore=read('restore-drill-result.json');native=read('native-recovery-drill-result.json')
n8n=read('n8n-clone-result.json');rag=read('rag-corpus-result.json');preview=read('n8n-rollout-preview.json')
parity=read('candidate-final-parity.json');checks=read('final-checks.json');main=read('final-readback.json')
assert restore['status']=='BACKUP_RESTORE_VERIFIED' and native['rollback_core_health']=='PASS'
assert n8n['status']=='CLONE_EVENT_AND_RETENTION_VERIFIED' and len(parity)==15 and all(c['exit_code']==0 for c in checks)
assert 'Ran 182 tests' in (RUN/'linux-final-regression.log').read_text()
source_commit=manifest['qualification_source_commit'];rel=RUN.name
evidence=f'Hiện hành: `{rel}/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.\n\n'
images_table='| Service | Candidate tag | Exact image ID |\n|---|---|---|\n'+''.join(f"| {kind} | `{v['tag']}` | `{v['id']}` |\n" for kind,v in images.items())
proposal={'schema_version':1,'status':'AWAITING_OWNER_APPROVAL','qualification_source_commit':source_commit,
 'images':{k:v['id'] for k,v in images.items()},'worker_sha256':manifest['worker_adapter_sha256'],
 'services_to_restart':['qldapm-n8n-main','qldapm-ai-gateway-1','qldapm-openproject-web-1','QLDAPMEngineeringDelivery'],
 'workflow':{'id':preview['workflow_id'],'expected_active_version':preview['expected_active_version'],'change':'append4 lifecycle nodes; retain original nodes/connections; retention settings none'},
 'configuration':'private n8n_lifecycle enabled=true, fixed local webhook URL, new private64hex signing key; keep all provider/auth policies',
 'required_preconditions':['fresh private backups including n8n before stopping','mode OFF and active queue0','no Native unknown replay','compare exact source/image/workflow version','preserve existing n8n owner/encryption keys and volume'],
 'approved_by_owner':False,'main_applied':False,'bounded_project6_business_e2e_authorized':False,
 'separate_approval':['WP385 replacement and historical correction','demo18791 release','historical n8n purge/credential rotation','fresh provider/native/github writes E2E']}
(RUN/'rollout-proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
proposal_hash=hashlib.sha256((RUN/'rollout-proposal.json').read_bytes()).hexdigest()
files={}
files['N8N_EVENT_PUBLISHER_EVIDENCE.md']='# Gateway lifecycle → n8n — Phase2\n\n'+evidence+f'''`gateway/execution_events.py` enqueue cùng transaction với event gốc. `n8n_lifecycle_outbox.py` giữ stable event ID, atomic lease30s, timeout tổng3s qua cancellable async HTTP, cap ACK8192bytes trong lúc streaming, exponential backoff tối đa300s, DEAD sau5 lần lỗi. Chỉ Project6 và9 event types có thật; payload không có prompt/source/token. work_package_id/unit_id chưa có ở event source nên là null, không bịa mapping.

Dispatcher knowledge hiện hữu gọi publisher; không thêm coding scheduler. WF04 thêm adapter riêng; chữ ký HMAC expiry60s kiểm tại Gateway, cùng actor/project/run/event source. HTTP200 hoặc n8n green thiếu exact OBSERVED ACK vẫn RETRY. Observation dedup theo event_id; execution metadata chỉ giữ execution ID/thời điểm. Lỗi delivery lưu fixed code, không raw remote exception. DEAD visibility hiện qua bảng SQLite, chưa có dashboard riêng; kiểm bằng connection read-only.

Clone cuối `{rel}/n8n-clone-real-gateway-final.log` dùng actual Gateway ASGI lifespan + Service background dispatcher và n8n2.43.6 image mới. AGENT_STARTED được append trước Gateway startup; không gọi thủ công WF04 để giả publisher. Outbox ACKED sau{n8n['automatic_event_delivery']['outbox'][0][1]}attempts (startup readiness retry),1observation, n8n execution1. Callback đi qua actual signed observation route. Source trace read và ACK được đối chiếu; Source event/consumer commit trước publisher crash + expired lease recovery có regression riêng.

Tests: outbox8, adapter1; đều nằm trong182Linux affected tests. Local slow-header/body fixtures chứng minh total deadline; HMAC/expiry/source tamper/cross-project/bearer denial, transaction rollback, duplicate/retry/DLQ/restart đều được thử. Signature sai không tạo observation.

Preview actual published WF04 `{preview['workflow_id']}`, activeVersion `{preview['expected_active_version']}`:4old nodes giữ nguyên, thêm4nodes. Callback URL host.docker.internal:18089 dùng Host localhost:18089 đã có trong allowlist; không nới Host guard. Candidate JSON nằm private theo n8n-rollout-preview.json. MAIN chưa publish/configure/enable. Các WF khác vẫn là adapters theo matrix06; không ép generic commands vào coding Project6.
'''
files['N8N_SECRET_RETENTION_REMEDIATION.md']='# n8n secret retention — candidate đã kiểm thử\n\n'+evidence+f'''P0 confirmed trên MAIN:13interactive workflows từng giữ Authorization và webhook token trong execution_data. Không có bằng chứng truy cập trái phép; không xuất raw headers/DB vào repo.

Clone baseline cho thấy saveDataSuccessExecution=none/saveDataErrorExecution=none/manual=false/progress=false **vẫn chưa đủ** để bảo đảm execution storage không có canary (n8n-retention-before-redaction.json). Sửa tối thiểu tại central execution-persistence.writeData và legacy ExecutionRepository update path. Upstream file SHA guard và unique markers làm build fail closed khi version thay đổi. Không sửa executing input: authentication/working workflow vẫn nhận giá trị gốc; chỉ persisted copy được redact.

Redactor bao gồm header object keys, n8n headerParameters name/value pairs, Authorization Basic/Bearer trong strings và signature/cookie/API-key headers. Giữ cyclic flatted structure và nonsecret status/correlation. Payload malformed fail closed. Independent review tìm header-pair gap; RED→GREEN đã lưu, không chỉ test Bearer object.

Candidate `{images['n8n']['id']}`. Clone actual Gateway→WF04 ACK và canary HTTP success200/error500/CLI execute exit0. Execution_data4rows cùng các execution tables/daemon log được scan: không canary. Disabled HTTP header fixture trong workflowData và Basic error/manual paths được bao phủ. CLI output được redact trước ghi log. Workflow definitions gốc chứa synthetic fixture được giữ private; không dùng synthetic secrets cho serving.

Giới hạn: manual đã thử qua CLI execute, **editor/manual UI: PENDING OWNER MANUAL UAT**. Không coi đây là chứng minh mọi arbitrary source string hoặc một upstream storage backend khác đều được redact. Image pin2.43.6; upgrade phải rebuild/verify hooks/canary. Nguồn chính thức tham khảo: [execution settings](https://docs.n8n.io/hosting/configuration/environment-variables/executions/) và [CLI](https://docs.n8n.io/hosting/cli-commands/); bằng chứng hành vi là clone version cụ thể.

Rollout đề nghị thay image n8n giữ nguyên owner/encryption/env/volume/ports, targeted WF04 retention; không bulk import16workflows. Raw historical executions chưa được xử lý. Sau backup n8n cold-consistent và exact owner approval riêng: inventory bằng fingerprint/boolean, xác định bearer/webhook credentials còn hiệu lực, chuẩn bị replacements private, đổi đúng consumers, test scoped auth, revoke old credentials, rồi purge chỉ affected execution IDs theo retention plan được duyệt. Không rotate Gemini/TOTP/DB hoặc toàn bộ user keys theo suy đoán; không xóa history tự động trong batch này. Backup cũng chứa dữ liệu nhạy cảm nên phải giữ private/access-limited.
'''
files['BACKUP_RESTORE_DRILL.md']='# Isolated restore / code rollback drill\n\n'+evidence+f'''**BACKUP_RESTORE_VERIFIED.** Backup gốc `{restore['backup']}`; PG custom dump signature/TOC đã kiểm, full restore vào PostgreSQL17.11 trên internal Docker network riêng, không shared MAIN volumes/ports. Restore221public tables; Project5=341WP/maxlock4; Project6=7WP/maxlock9; WP379=project6/status7/lock4. Bảng và row-count chi tiết: `{rel}/restore-drill-result.json`.

gateway.sqlite41tables và knowledge.sqlite9tables được copy private, schema và toàn bộ table row counts bằng backup, integrity_check=ok. Engineering receipts/history được đối chiếu qua table counts; không suy count thành outcome correctness. Đây là backup sau WP385 deletion, không chứa record385 và không phục hồi lịch sử đã mất.

Phase2 Core candidate còn được restore/startup lần nữa, tạo replacement bằng official Native API trên clone, read-back parent/project/relation, Project5 fingerprint giữ nguyên. Rollback Core r24 cũng startup healthy trên fresh restored clone. Gateway candidate và rollback r24 đều actual Uvicorn health200 trên network none, no live/private mounts. Gateway startup dùng empty fixture state, không phải diễn tập full live config/traffic cutover. N8n candidate startup và storage canary có drill riêng; chưa restore MAIN n8n history vào clone.

Cleanup chỉ label/UUID-owned disposable resources. main_native_clone kiểm container IDs/images/starttimes trước/sau mỗi drill; không restore đè MAIN. Logs lỗi đầu (fixture Host thiếuport; relation POST saiendpoint) giữ nguyên, lần cuối đã đạt; không đếm lỗi thànhPASS.

Source recovery: private local Git `{source_commit}`,587allowlisted files,1credential-shaped test fixture quarantined. Root repo2tracked/no remote vẫn giữ nguyên. Private Git bundle verified; dependencies/requirements và Docker recipes được version, immutable runtime bases lưu private archive theo base-image-archive.json. Image build dùng snapshot commit307503c; qualification commit mới chỉ thêm host delivery/adapter/tests/architecture,15packaged files vẫn khớp. Không remote/push. Cần backup mới ngay trước approved cutover nếu dữ liệu đã đổi; không dùng backup này rollback business DB cũ lênMAIN.
'''
files['WP385_RECOVERY_PROPOSAL.md']='# WP385 / historical verdict recovery proposal\n\n'+evidence+f'''Kết luận pháp y vẫn như WP385_FORENSICS.md: WP385/journal1091/relation357 đã bị xóa; run b1cca031 forced succeeded mâu thuẫn raw agent FAILED và planning-knowledge checkpoint lỗi. Không tìm thấy Main backup trong create-delete window. Phase2 kiểm archive_mode=off/archive_command disabled, không có configured archived WAL/PITR được xác minh. Không khẳng định mọi backup ngoài máy/VSS đều không tồn tại.

Chọn **replacement WP mới bằng Native API**, không INSERT id385/resetsequence/created_at giả. Proposal cụ thể `{rel}/wp385-replacement-preview.json`: Project6/parent379; original plan/unit forensic reference; AC10 category POST/PATCH, AC11 category filter, AC12 CSV; dependency WP384. Trước MAIN write phải search exact plan+unit forensic marker trongProject6, không có duplicate mới create; nếu ambiguous/timeout thì dừng/read-back, không blind repeatPOST. Fresh Native role/project/parent lock/type options phải còn hợp lệ. Không gán acceptance/Done.

Clone thử bằng user20 nonadmin với token chỉ tạo trong disposable DB: POST /api/v3/work_packages trả201, ID clone{native['replacement']['new_clone_id']} (MAIN chưa có ID này do tác vụ), GET read-back project6/parent379; POST /api/v3/work_packages/<new>/relations + GET relation xác minh follows384. Original385 vẫn absent; Project5 fingerprint không đổi. Script native_recovery_drill.py có CLONE_ONLY guard, không là Main apply script. Log lần đầu wrong relation endpoint fail được giữ; lần cuối đúngAPI đạt.

Historical run: production source chỉ thay owner-facing projection khi persisted succeeded + agent FAILED/CANCELLED → blocked/RECONCILIATION_REQUIRED, giữ persisted_status và raw stored values. Test2cases nằm trong182suite. Đây là phát hiện mâu thuẫn, không phải kết luận đã chữa planning knowledge. Correction đề nghị sau Owner duyệt: append audited reconciliation note gắn original hashes/checkpoint/raw receipts, nêu actual partial plan publication và failed knowledge step; giữ mọi raw record. Không UPDATE status SQL, không tự retry unknown, không recredit success. Rebuild unit mapping/knowledge chỉ sau replacement được duyệt và read-back, để original385 mapping trong evidence.

**MAIN DATA APPROVAL PENDING.** Replacement và audited correction tách khỏi code rollout. Không có record/history nào đã được phục hồi trênMAIN trong batch này.
'''
files['DEMO_RELEASE_CANDIDATE.md']='# Mini Task Manager — exact release candidate\n\n'+evidence+'''Candidate commit `0498ceeda97cd3e856a975129129e71f6c94a3dd`, đã có trong local Git objects, export exact tree bằng git archive; không merge/push/checkout branch của user. Parent chain có health/summary cùng CRUD/search/UI trước đó; remote PR1–6 snapshotPhase1 không thay bằng localbranch assumption.

Application thực là FastAPI/Uvicorn (không dùng giả định Flask từ yêu cầu). Live18791 vẫn release `def9d0a8852af42a407bd42fb0051615a2de9331`, PID/cwd/server command đã đọc ởWSL. GET/healthz404, GET/tasks/summary405 vẫn khớp read-back cuối; PR merged-to-feature không phải deployed.

Candidate:15pytest testsPASS với pinned installed venv + actual Node binary, không skip. Actual HTTP server cổng loopback tạm: health200/summary200, CRUD/search/422/404 và total invariant đạt. Copy SQLite live bằng read-only backup vào private clone, schema/rows giữ sau fixtureCRUD; dữ liệu nguồn hiện0rows nên không chứng minh upgrade một corpus lớn. Persistence được kiểm trong suite, actual HTTP compatibility trong demo-http-compat-result.log. Không đổi server18791/data thật.

Approval boundary riêng: backup demo SQLite/current release manifest; launch candidate on temporary port first; preserve live DB schema/data; switch exact release path/command to chosenSHA only after owner approval; validate health/summary/CRUD read, X-QLDAPM-Revision and persisted row fingerprint; rollback command/release to def9 while preserving data. Không auto-merge PR4–6/force-push; phải recheck selectedSHA/base/dependency chain ở thời điểm cutover. No paid dependency/provider changes.
'''
files['FINAL_PRE_ROLLOUT_ACCEPTANCE.md']='# Phase2 pre-rollout acceptance — candidate, chưa MAIN\n\n'+evidence+f'''**CANDIDATE_TESTED_WITH_LIMITS / AWAITING_OWNER_APPROVAL.** Không công bố full backend/runtime/live/human acceptance. RAG semantic recall còn openP1; actor19 vẫn DENIED đúng guard; fresh OpenClaw/provider execution và Owner UI UAT chưa làm.

{images_table}

Source qualification private commit `{source_commit}`. Worker/adapter full SHA256 và587source entries: `{rel}/source-candidate-final-manifest.json`. Build commit307503c chứa toàn bộ packaged app code; subsequent host-only fixes được kiểm trên snapshot cuối. Root HEAD không đại diện sourceuntracked.15/15host-snapshot-image parity; Docker Compose preview chỉ Gateway/web image/pull_policy thay đổi, rollback configs hợp lệ.

| Gate | Evidence / verdict |
|---|---|
| M1 source + restore | PASS candidate: private Git/bundle, build,221PGtables+2SQLite full restore |
| M2 events + retention | PASS clone actual ASGI→n8n→signed ACK;8outbox+1adapter tests;canary success/error/CLI clean;16workflow matrix giữ classification đúng |
| M3 GitHub | PASS10journal tests real localhost Native HTTP; no real GitHub/Native writes; unknown held/reconciled, concurrent1POST |
| M4 integrity | PASS proposal tested Native clone; original385 not restored; MAIN correction pending |
| M5 reports/RAG | ContractsPASS; real corpus135vectors exact/ACL/fallback/index-deletePASS; VN/EN semantic queriesFAIL documented, no threshold hack; UI pending |
| M6 delivery | PASS7fullDeliveryJournal/Gateway temporaryStore fixtures +2real child-process tests; review/QA rework, known partial/done resume, unknown no-replay/treefence; no fresh real OpenClaw session |
| M7 demo | PASS exactSHA15tests + actual HTTP temporaryserver/SQLite compatibility;18791 unchanged |
| M8 build/startup/rollback | PASS15parity,182Linux affected tests, Ruby/ERB/JS/controller contracts, newCore/Gateway/n8n startup, Core/Gateway rollback smoke; no traffic cutover |
| M9 MAIN/live/UAT | NOT RUN — requires explicit owner approval |

182 is total final affected suite, includes prior130; do not sum130+182. Initial RED/fixture/config failures remainFAIL in history, not added togreen count. Warnings/deprecations retained inlogs; no dependency upgrades. Browser/editor/manual UI **PENDING OWNER MANUAL UAT**.

RAG diagnostics: VN384 maxcos0.569523, EN3840.512619, unrelated backupquery max0.520300; all under current0.65. Lowering one global threshold would trade recall for false positives. Negative email now empty; keep this open calibration limitation rather than fabricate semantic PASS. Need broader labeled relevant/irrelevant corpus before changing policy/model/chunking.

One proposed code/integration rollout: `{rel}/rollout-proposal.json`, SHA256 `{proposal_hash}`. It covers three images, exact host worker+delivery adapter versions, targeted WF04 four-node addition and private lifecycle config; downtime for gateway/core/n8n plus paused worker expected, not measured onlive. Backup and no-active-queue preflight mandatory. Liveprovider writes E2E, WP385data, demo18791 and secret-history cleanup/rotation require scoped authorization separately. Production approval is required by Owner directive A2; no skill adds an extra approval requirement here.

Last read-only MAIN check `{main['at']}`: Project5=341/maxlock4, Project6=7/maxlock9,379status7/lock4,386status1/lock2,385absent; OFF/active0/providerreceipts358. Gateway/Core/n8n/DB IDs/images unchanged versus Phase1 snapshot, health200 forGateway/n8n/Qdrant/Ollama. No agent-triggered Main restart, replay, merge, WP mutation orprovidercall inPhase2.
'''
files['10_DEPLOYMENT_AND_ROLLBACK.md']='# Phase2 rollout / rollback — PREVIEW ONLY\n\n'+evidence+images_table+f'''
Serving rollback: Gateway fcb44c49afb99efd85b4a00297a58e7c5a59d36ab2f2b78e15a6a6d135f5e93e; Core a4fa8150728bc5fc50f8afed22fce898cc52065a55ff0fdb53b803a81d9e1c6b; n8n dd580fe1ab6e99e85bc66f2acf8bc8c5e9409fbe61b2e2803c5024403ef52833. Phase1 candidate r2/r1 are superseded for this rollout; exact Phase2 IDs above are authoritative.

Single approval proposal `{rel}/rollout-proposal.json`, SHA256 `{proposal_hash}`. Expected affected scope: Core/Gateway/n8n availability during recreate and Windows delivery worker while stopped. Clone startup is not a downtime guarantee; allocate maintenance window and health timeout, stop on any mismatch. Preserve data, ports, env, provider/model/quota, owner/TOTP/encryption configuration. No DB service restart/migration or volume deletion.

After exact approval only:

1. Re-read runtime/source/image/WF04activeversion; OFF/active0/worker no active unit; Project5/379/unknown receipts unchanged. Create fresh consistent private backups ofPG/Gateway/knowledge/configs **and n8n data/encryption configuration**. Confirm restore artifacts; if state drift, reconcile before applying.
2. Stop only QLDAPMEngineeringDelivery after idle check. Keep immutable source snapshot and prior worker+engineering_delivery backups. Current host source already changed, old loaded process unverified; restart is required to load reviewed code.
3. Replace n8n image preserving private before Config/HostConfig/Mounts/network/ports in `{preview['private_preview']}`. Target only WF04 `{preview['workflow_id']}` with compare-before activeVersion `{preview['expected_active_version']}`. Private candidate preserves4oldnodes/connections and adds4; use targeted supported n8n CLI import/publish while service stopped, no bulk16workflow import. Keep prechange workflow private for rollback. No historical prune/tokenrotation. Verify startup/canary metadata without exposing realcredential values.
4. Generate private64hex lifecycle signing key and set n8n_lifecycle enabled/url for fixed local `/webhook/qldapm-lifecycle`; keep config copy/permissions. Callback Host localhost:18089 is already allowed; no Host/security guard expansion. Apply only gateway/web images with the existing Compose prefix + candidate overlay; no --build or dependency rollout. Commands below are **not executed**.

```powershell
docker compose -p qldapm-ai --env-file "$env:LOCALAPPDATA\\QLDAPM\\openproject-ai\\.env" -f openproject/ai/compose.yml -f openproject/ai/gemini-free.main.yml -f docs/ai/engineering/CHATGPT_RECOVERY/compose.gateway.candidate.json up -d --no-deps gateway
docker compose -p qldapm-openproject --env-file "$env:LOCALAPPDATA\\QLDAPM\\openproject\\.env" -f openproject/compose.yml -f "$env:LOCALAPPDATA\\QLDAPM\\openproject\\ui-bridge.yml" -f docs/ai/engineering/CHATGPT_RECOVERY/compose.core.candidate.json up -d --no-deps web
```

5. Re-read exact images/15hashes/health, hosts/RBAC, Project5/379 baseline, receipts/queue; start exact Windows task only after hashes match; verify heartbeat/process start after source version. Keep engineering OFF. Authenticated read contracts/reports/RAG and idleoutbox/n8n status next. Fresh business E2E withprovider/GitHub/Native writes needs bounded scope authorization, not implicit in code rollout. Owner UI UAT remains separate.

Rollback: hold OFF/stopidleworker; disable lifecycle config to stopdelivery, preserve outbox/error receipts; restore WF04 exact previous graph/settings; use same Compose commands with compose.gateway.rollback.json / compose.core.rollback.json, restore n8n previous image **with same volume/config/encryption**. Revert host worker and engineering_delivery from reviewed backups if required, then startidle task and readback invariants. Do not restore oldbusinessDB, resetvolume or erase unknown outcomes. Additive SQLite journal/outbox tables may remain; oldimage ignores them. Clone Gateway/Core rollback health tested, not live traffic cutover; n8n originalimage remains available, data downgrade effects require preflight against freshcopy.
'''
files['12_CONTINUATION_HANDOFF.md']='# Phase2 continuation handoff\n\n'+evidence+f'''Đã hoàn tất batch source/candidate tiếp theo, chưa rolloutMAIN. Private qualification commit `{source_commit}`; images/fullhashes tại source-candidate-final-manifest.json. Root repo vẫn2tracked/no remote;587allowlisted files được version private,1credential-shaped test quarantined, verified Gitbundle và baseimagearchive giữ khả năng rebuild.

Đã sửa/test: durable GitHub journal + paginated marker reconciliation; transactional n8n event outbox/signed observations/strict bounded ACK; n8n execution persistence redaction cả headerobjects/name-value/Basic/Bearer; historical inconsistent success projection; ReportReader parser/stale-ID/error handling và controller403/503; bỏ UI hardcoded PASS/PR/lock fallback; worker resume sau completed/partial rework và giữ originalreviewdiff.

Verification cuối:182Linux affected tests (bao gồm130baseline),7deliveryfixture tests nằm trong đó, Ruby/ERB/controller/Node contracts,15file image parity, newcandidate build từ private source, actual ASGI→n8n eventACK/canary,221tablePG+2SQLite restore, candidate/rollback startups. Native clone tạo replacement newID387/follows384 vàread-back, không MAIN. Demo exact0498ceed15tests+actual HTTP200health/summary với cloneSQLite,18791 vẫnoldrelease. Không Computer Use/provider live/Mainrestart/workerrestart/Project5write/merge/deleteWP.

Còn giới hạn có evidence: RAG semantic VN/EN recall gap (score dưới0.65, negativesoverlap; không đổi threshold), actor19 admin=true DENIEDgiữguard; no freshactualOpenClaw/provider session, n8neditor/UI/Owner UAT pending, historicalsecretcleanup/rotation và WP385/Mainverdict correction chưathực hiện. Sourcefixed/candidatetested không là Liveaccepted.

Bước tiếp theo: Owner xem FINAL_PRE_ROLLOUT_ACCEPTANCE.md và duyệt **một** code/integration rollout proposal hash `{proposal_hash}` theo10. Sau duyệt chạyfreshbackup/preflight rồi chỉ3services+idleworker/targetedWF04/privateconfig. Không tự thêm MainbusinessE2E/demo/datarepair vàoapproval này. Nếu không duyệt, giữOFF vàcandidates/evidence; không tựdeploy hoặc replay.

Latest snapshot `{main['at']}`: servingr24 IDs/images nguyên, Project5=341/maxlock4,379status7/lock4,queueOFF/0,providerreceipts358. CURRENT_RUN.txt trỏPhase2; đọc09matrix vàrunlogs, không lặp lại những test đã đạt trừ khi có thayđổi/failure mới.
'''
files['03_DEFECT_REGISTER.md']='# Defect register — Phase2 current\n\n'+evidence+'''| ID | Priority | Current evidence/status |
|---|---|---|
| REC-001/002/003 | P0 | AUTO/owned resume/atomic claim SOURCE_FIXED+CANDIDATE_TESTED; liveworker restart pending |
| REC-004/005/006/007 | P0/P1 | GitHub failures/mapping/cache/UI honesty candidate tested; no live write |
| REC-008/009/010 | P1 | Receipt-derived workforce/factualreports/escaping candidate tested |
| REC-011 | P1 remaining | Wrong one-token negatives fixed; corpus exact/ACL/fallbackPASS, semanticVN/EN recallGAP; current0.65 retained |
| REC-012 | P0 data loss | CONFIRMED; newreplacement proposal testedNativeclone; original385 history not restored; MAIN approval pending |
| REC-013 | P0 historical | Raw verdict corruption preserved; ownerprojection detects contradiction; auditedcorrection pending |
| REC-014 | P0 serving | Redaction candidate+canary clean; MAIN stillunpatched/historycontainssecrets; purge/rotation separately approved |
| REC-015 | P0 integration | Outbox/actualGateway→n8nclone verified; MAINconfig/WF04activation pending |
| REC-016 | P1 | actor19 credentials resolve19/admin=true;DENIEDcorrect; membershipchange notauthorized;PARTIALremainshonest |
| REC-017 | P0 reported UI | Parser/stale-ID/controller contracts fixed/tested; original OwnerUI symptom not accepted; manualUATpending |
| REC-018 | P1 | Durable journal+unknown/concurrent/crashlocalhostHTTP10testsPASS; no blindunknownPOSTreplay |
| REC-019 | P1 boundary | Phase2images built/tested; MAINNOTDEPLOYED; sourceprivateversioned |
| REC-020 | P1 deployment | Demoexact0498candidate15tests/actualHTTPPASS;serving18791still404/405 |
| REC-021 | P1 foundPhase2 | ACKdripheader/body timeout repaired/cap8192; slow-servertestsPASS |
| REC-022 | P1 foundPhase2 | Resumeafterrework revisionmismatch + originaldiff overwrite repaired;7fulljournaltestsPASS |

Phase1 original severity/findings/logs preserved in currentrun/backups/03_DEFECT_REGISTER.md. Scope-specific PASS is not fullsystemacceptance; openMAIN vulnerabilities remain until approveddeployment.
'''
for name,content in files.items():(DOC/name).write_text(content,encoding='utf-8')
updates={
 '06_N8N_16_WORKFLOW_INTEGRATION.md':'''Phase2 current: lifecycle outbox and actual GatewayASGI→n8ncloneACK verified; storage redaction tested beyond noneflags; actor19 identity19/admin=true explainsDENIED. Read N8N_EVENT_PUBLISHER_EVIDENCE.md and N8N_SECRET_RETENTION_REMEDIATION.md. The16workflow inventory/mapping below is the timestamped Phase1 live snapshot, not a fresh run of all16. WF02/03/10/11/13/14/15 remain role-scoped management adapters; no broad coding capabilities/schedule added. MAIN still unchanged; targetedWF04draft only private, noimport/publish.''',
 '07_GITHUB_SYNC_AND_PR_RECONCILIATION.md':'''Phase2 current: engineering_github_sync durable SQLiteoperationjournal; reserveatomic, UNKNOWNbeforePOST, stablemarkerreadback acrosspages, unknownnoautomaticrePOST, explicit4xxrejection retryable. Concurrentrequests1POST; disconnectaftercommit/crashbeforepersist reconcileexistingmarker; legacyexactnoteadopted.10journal tests use real localhostHTTPNative and tempStore; total affected182PASS. RemotePR snapshot below is historical read-only; no newpush/merge/Nativecomment. See phase2 logs and source-candidate-final-manifest.json.''',
 '08_SECOND_BRAIN_AND_REPORTING.md':'''Phase2 current: actual ReaderJS parser/no-store/ID/staleresponse and controller403/404/503 contracts tested; hardcodedPASS/PR/lock fallback removed. NodeplainmockDOM is not GUI acceptance. Real privatecorpus+135vectorcopy/Qdrantclone/localBGE-M3 tested: healthz exact/ACL/fallback/index-deletePASS; VN/ENsemantic misses remain (rag-score-diagnostics.json). No thresholdchangeforfixture. Historicalforcedsuccess projection flaggedRECONCILIATION_REQUIRED; rawDBverdictuntouched. UI PENDING OWNER MANUAL UAT.''',
 '05_OPENCLAW_MULTI_AGENT_VERIFICATION.md':'''Phase2 current: full worker.execute→DeliveryJournal→real temporaryGatewayStore/admit/claim/checkpoint/resume/finish tests7PASS, coveringReviewer/QAfail→rework, knownpartial/completedreworkresume, unknownno-replay/treefence and originaldiff/receiptsretention. Additional2tests use real disposable childprocess to verifyAUTO survivespoll andPAUSE/CANCEL/failedfence terminate. ExternalNative/provider/git/GitHub/acceptanceleaves in7tests arefixtures. No freshliveOpenClaw/Geminisession, loadedliveworker version not proved until authorizedidle restart. Totalfinalaffected182PASS; prior PM/BAreceipt correction below preserved.''',
 '04_CORE_ENGINE_FIXES.md':'''Phase2 current: engineering_delivery.py resume advances pastdone reworkattempts and resumesknown interruptedreworkwithoriginalfeedback. Candidate-N.diff is preserved whenreviewNdone. Initialtreehashfence, terminalknownGatewayguard and no-replayunknown remain. Reviewfoundbothbugs, RED/GREEN+independentre-review savedphase2. Historicalsuccessprojectionadded; no directDBrepair.''',
 '11_OWNER_MANUAL_UAT_GUIDE.md':'''Phase2 status: PENDING OWNER MANUAL UAT. After approvedrollout owner must check reportdetail(nonempty/empty/error/stale), truthfulPR/test/rolebadges, actualNativeparentlock intake, RAG exactandsemanticlimitations, n8neditor/manualredaction andWF04eventexecution link. CLIcanary/NodeDOM/Rubycontracts are automated code evidence, not UI PASS. Do not triggernewbusinessrun before separateboundedscopeapproval.''',
 '01_ARCHITECTURE_AND_SOURCE_AUDIT.md':f'''Phase2 sourceversioning current:587allowlistedfiles/privateGitcommit{source_commit}; no rootremote/push. Final15packagedsourcehashesmatch; hostdelivery/adapter version separatelyrecorded. Actualrestore221PGtables+2SQLite completed. Read FINAL_PRE_ROLLOUT_ACCEPTANCE.md; audit below is baselinePhase1.'''
}
for name,body in updates.items():
    path=DOC/name;old=path.read_text(encoding='utf-8')
    if old.startswith('# Phase2 current — 01/11/2026\n'):
        old=old.split('\n\n---\n\n',1)[1]
    path.write_text('# Phase2 current — 01/11/2026\n\n'+body+'\n\n---\n\n'+old,encoding='utf-8')
matrix=json.loads((RUN/'backups/09_TEST_EXECUTION_RESULTS.json').read_text())
matrix['phase1_status']=matrix['status'];matrix.update(snapshot=datetime.now(timezone.utc).isoformat(),status='PHASE2_CANDIDATE_TESTED_WITH_LIMITS_NOT_DEPLOYED',fix_commit=source_commit,
 note='Private source Git commit, not rootHEAD.182finalaffected includes prior130; do not add totals. UI/manual/providerlive pending. RAGsemantic misses retained asFAIL.')
rows=[('P2-LINUX','182finalaffected tests incl baseline','linux-final-regression.log','PASS',0),
 ('P2-RESTORE','221PGtables+2SQLite schema/count/integrity','restore-drill-result.json','PASS',0),
 ('P2-N8N','actualASGI/lifecyclepublisher/WF04/signedACK + canarysuccess/error/CLI','n8n-clone-result.json','PASS',0),
 ('P2-NATIVE','replacementofficialAPI+relation+readback clone;Corecandidate/rollback','native-recovery-drill-result.json','PASS',0),
 ('P2-GATEWAY','actualstartup+rollbacknetworknone','gateway-startup-rollback.json','PASS',0),
 ('P2-PARITY','15host/snapshot/image','candidate-final-parity.json','PASS',0),
 ('P2-DEMO','15pytest+actualHTTPhealth/summary/CRUD/SQLitecopy','demo-linux-final.log','PASS',0),
 ('P2-RAG','realcorpus exact/ACL/fallback/index-delete;2semanticmisses','rag-corpus-result.json','PARTIAL',0),
 ('P2-UI','ownerbrowser/editor/manualinteraction',None,'PENDING OWNER MANUAL UAT',None),
 ('P2-LIVE','MAINrollout/freshOpenClawprovider/businessE2E',None,'NOT_RUN_APPROVAL_REQUIRED',None)]
for identifier,requirement,log,status,code in rows:
    matrix['suites'].append({'test_id':identifier,'requirement':requirement,'logs':str(RUN/log) if log else None,
     'status':status,'exit_code':code,'fix_commit':source_commit,'phase':'PHASE2','note':'Exit0 diagnostic is not semanticPASS when result saysPARTIAL/FAIL.' if identifier=='P2-RAG' else None})
for c in checks:
    if c['check']=='linux-final-regression':continue
    matrix['suites'].append({'test_id':'P2-'+c['check'],'test_command':c['command'],'logs':str(RUN/c['log']),'exit_code':c['exit_code'],'status':'PASS','phase':'PHASE2','fix_commit':source_commit})
(DOC/'09_TEST_EXECUTION_RESULTS.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
(RUN/'documentation-summary.json').write_text(json.dumps({'updated':list(files)+list(updates)+['09_TEST_EXECUTION_RESULTS.json'],'rollout_proposal_sha256':proposal_hash},indent=2)+'\n')
print(json.dumps({'documents_updated':len(files)+len(updates)+1,'proposal_sha256':proposal_hash,'status':'AWAITING_OWNER_APPROVAL'},indent=2))

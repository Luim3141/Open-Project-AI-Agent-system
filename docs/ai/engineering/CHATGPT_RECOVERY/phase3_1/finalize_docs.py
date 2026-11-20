"""Publish evidence-backed handoff; preserve historical documents and test index."""
import datetime
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).parent
DOC=OUT.parent
ROOT=Path(__file__).resolve().parents[5]
release=json.loads((OUT/'deployment.json').read_text())
live=json.loads((OUT/'final-live-verification.json').read_text())
readback=json.loads((OUT/'main-readback.json').read_text())
clone=json.loads((OUT/'core-clone-result.json').read_text())
gateway=json.loads((OUT/'gateway-candidate-final.json').read_text())
native=json.loads((OUT/'native-after-identity.json').read_text())
assert live['status'].endswith('_PASS') and readback['status']=='PASS' and clone['status']=='PASS'
assert clone['image']==release['images']['core'] and gateway['image']==release['images']['gateway'] and gateway['exit_code']==0
assert native['comparison']['status']=='PASS' and live['engineering']['provider_receipts']==474
assert readback['wp391']['failure']['category']=='PROVIDER_QUOTA_EXHAUSTED'
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(timespec='seconds')
images=release['images']
summary=f'''<!-- PHASE3_1_CURRENT -->
# MAIN — Phase 3.1 Owner UAT recovery

Checkpoint **{stamp}**. Gateway `{images['gateway']}`, Core `{images['core']}`, n8n `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`.

**SOURCE FIXED / CANDIDATE TESTED / DEPLOYED / API VERIFIED; OWNER UAT PENDING.** Core/Gateway healthy, worker ALIVE, mode OFF, active0. Exact21 serving source files và pins đã kiểm tra; worker giữ protocol, nhận cap Gateway bằng một dòng đã có regression. Không Computer Use, không resume/tạo lại #391, không inference/provider probe, không tăng production cap để PASS.

#391: engineering BLOCKED/attempt FAILED; Native business status **NEW**. Ba Dev sessions: 12/12HTTP200, 12/12HTTP200, 11HTTP200+1HTTP429; tổng36 calls. Lượt đầu dừng do cap nội bộ; lỗi gần nhất là upstream429. Checkpointv16 còn nguyên; raw historical result/queue/checkpoint/Native row giữ nguyên hash, provider receipt count474 không đổi. Không có evidence phân biệt RPM/TPM/RPD hoặc thời điểm reset. Resume hiện bị fence `PROVIDER_RECOVERY_REQUIRED`; readiness đã lưu cũ không phải bằng chứng provider phục hồi.

UI: WP ngắn/ngày giờ đầy đủ, search/filter/selection, Current/Recent Work, Agent Current State + Last Activity, summary budget/checkpoint, durable child/run notifications, plan versions, structured sanitized Markdown/TOC/raw/export, health có nguồn/timestamp. #379 là Native **Task**, một record với hai engineering unit references; bỏ nhãn Epic giả, không xóa dữ liệu.

Validation: final immutable Gateway **105 tests PASS** (Owner recovery22 là tập con); final Core actual Rails/Native/login/session/CSRF/full-template clone PASS; Node VM polling/Inspector/reader/filter và Ruby Markdown/XSS/long-document PASS. Host163 PASS thuộc revision trước follow-up, không dùng để chứng nhận toàn source cuối hoặc cộng dồn. MAIN signed Rails→Gateway/API + production ERB read-back PASS; nhãn identity cuối được kiểm trên clone và serving hashes. Project5: toàn cột13 bảng scoped/global không đổi; 341WP/344relations/968journals. Không phải kiểm mọi bảng hoặc whole-image coding E2E.

Remaining: provider429/#391 chưa hoàn tất; Owner Browser UAT/pixel/200%zoom pending; historical checkpoint time không có timestamp đáng tin nên UNKNOWN; OpenClaw/Demo health UNKNOWN do thiếu safe endpoint đã cấu hình. In-app không bảo đảm báo khi đóng web. Semantic RAG FAILED/PARTIAL, n8n master-key/history OPEN/BLOCKED, WF04 retentionOFF, WF07/WF12 PARTIAL, off-host custody/physical DR PENDING giữ nguyên.

Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json`, `phase3_1/main-readback.json`, `FINAL_TEST_RESULTS.json` schema5. Các block cũ bên dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

'''
def prepend(name,content):
    path=DOC/name
    old=path.read_text(encoding='utf-8-sig')
    assert '<!-- PHASE3_1_CURRENT -->' not in old, 'Preserve/review existing current block before rewrite'
    path.write_text(content+old,encoding='utf-8')

report=summary+'''## Root causes và mapping

- Backlog trộn Native record, project anchor và engineering unit; thiếu thời gian/identity dễ đọc. Native379 có một record loại Task, hai unit `crud-search-web-v1` và `create-list-persistence-v1` tham chiếu nó. Native391 là Task riêng. Không phải hai Native records để xóa. Parent anchor và unit/run identity nay tách nhãn; search WP/title/run, filters ALL/ACTIVE/READY/BLOCKED/COMPLETED; ngày giờ `dd/MM/yyyy HH:mm:ss`, Asia/Ho_Chi_Minh; live polling giữ input/selection/details.
- Planning: ID/spec/unit metadata từng đổ ra cùng cấp. Nay summary/BA-PM details, created/published, counts và related run; group theo child WP nếu plan chỉ có một child, giữ source anchor khi nhiều child. Search áp dụng từng plan version, không để một match làm hiện toàn bộ versions của parent379. PUBLISHED không bị đổi thành COMPLETED.
- Workforce chỉ chiếu status hiện tại nên mọi card về STANDBY khi run kết thúc. Projection nay lấy scoped queue→events→role→receipts; giữ last activity riêng từng role, kể cả Dev đã xong khi Reviewer chạy. Historical receipt hoặc Worker ALIVE không tự tạo RUNNING. Failure của rework/AGENT_FAILED có precedence hơn completed step cũ. Cards3/2/1 columns, wrap/min-width0, raw JSON/receipts ở details, có copy full ID.
- Mission/Pipeline hiển thị current/recent/blocked, không dùng Epic IN PROGRESS để nói Agent chạy. Mười execution/integration checkpoints có evidence riêng; tám bước business reference thu gọn, không dùng badge8/8 như trạng thái hoàn tất. Integration success không thay review/QA artifact.
- Inspector dùng cùng summary theo run, tách attempt/engineering/Native status, provider responses và task completion. Timeline nhóm theo role/stage, lọc milestones/errors/model/tools; giữ source/diff/Reviewer/QA/raw và request-token guards.
- Report reader cũ dùng textContent narrative nên hiển thị Markdown thô. Helper dùng Commonmarker có sẵn + Rails sanitization, không raw HTML; link allowlist Native/GitHub, bỏ credential/javascript/foreign URLs. Có headings/lists/tables/code/quotes/TOC, structured factual summary, AI/provenance labels, sections/raw/copy/export; không sửa DB report. Modal riêng scroll/mobile. Pixel/print thật cần Owner kiểm tra.
- Health aggregate chỉ safe GET cố định, không redirect/credential/inference; concurrent deadline2.2s, timeout1.5s, TTL60s. UP chỉ là readiness, authentication/process/business có nhãn độc lập. Read-back: OpenProject/Gateway/n8n/Qdrant/Ollama UP; OpenClaw/Demo UNKNOWN đúng vì thiếu endpoint an toàn đã cấu hình.

## #391: nguyên nhân tiếp tục vẫn bị BLOCKED

Snapshot Owner ban đầu chỉ có một session. Live evidence đã có recovery_count2 trước phiên này: ba sessions, mỗi session12 calls; session3 có một upstream429. `openclaw_provider_gate.py` chỉ ghi receipt HTTP status nhận từ Google; local allowance hết trả403 `ENGINEERING_PROVIDER_BUDGET`, không phải429. Vì vậy lỗi cuối là provider rejection thật; hai lần trước là internal budget chưa đủ để Dev kết thúc. HTTP200 không chứng minh Dev hoàn tất. Reviewer/QA chưa chạy cho #391.

Giữ raw `OPENCLAW_STEP_NOT_COMPLETED` và verdict lịch sử; UI thêm classification từ evidence, không rewrite thành SUCCESS. Checkpointv16 chỉ có completed `context`, `prepare`; không giả các bước Dev/Review/QA đã hoàn tất. 36 calls tích lũy; 11 response200 được xác minh ở lượt mới nhất, một receipt thiếu token usage. Token là số provider đã ghi nhận, không dùng suy chi phí hoặc cam kết billing.

Resume không tạo WP/unit/run/PR mới. Chính sách config `engineering.continuation`: attempt_calls12 (1..12), task_calls72 (1..120), max_continuations5 (0..5), cooldown_seconds60, auto_continuefalse. Không đổi config MAIN để ép #391 PASS. Admission reserve clamp theo remaining task budget, worker dùng cap được cấp. Same checkpoint version/source read-back/unknown external writes/concurrency/mode đều được kiểm lại. OFF không tự bật AUTO; manual Resume được Owner gửi là RUN_ONCE. Pending Resume bị OFF trước claim không tiêu hao thêm continuation khi Owner yêu cầu lại.

429/auth/timeout cần existing key/policy-bound readiness READY mới hơn lỗi, tuổi≤300s; quota/circuit guards vẫn áp dụng. Readiness lấy trước write lock để không self-deadlock SQLite, sau lock so lại timestamp với latest failure; fixture race mới hơn readiness vẫn fence. Không tự phát provider request để tạo chứng cứ. AUTO chỉ opt-in cấu hình rõ ràng, chỉ tiếp tục DEV_BUDGET_EXHAUSTED an toàn/còn cap/cooldown; provider/unknown outcome dừng và yêu cầu Owner. Hành vi failsafe AUTO→OFF khi blocked là có chủ đích, nay ghi policy rõ trên UI.

## Notifications

Durable UUIDv5 theo run/continuation/reason (agent start thêm role), INSERT OR IGNORE, read/dismiss persist. Snapshot backfill có82 unread, không phải82 model-request alerts; poll lại không tăng count/duplicate. Mỗi note có WP/run/severity/code/time/action; resumed failure tìm child từ project6 contract. Blocker note mới ghi đúng child WP thay parent379; note lịch sử không bị xóa/sửa. Chỉ backfill/latest persisted evidence, không bịa notification cho từng lỗi lịch sử thiếu evidence. In-app không bảo đảm khi đóng web; không tự gửi email hoặc bật paid channel.

Đã truy vết callers: engineering notification chỉ persist/list/dismiss trong Gateway, không có external sender gắn với bảng này. Module `notification_delivery.py` hiện báo LOCAL_METADATA_ONLY / BLOCKED_CONFIGURATION và chỉ enqueue Project5; đó không phải channel Project6 engineering. Không suy ra một email/n8n destination đã được cấu hình cho cảnh báo #391, không tự gửi tới địa chỉ chưa xác minh.

## Files và validation

Source allowlist: `phase3_1/source-allowlist.json`; final hashes/pins: `phase3_1/final-live-verification.json`. Gateway thay engineering status/auto/lifecycle/operator/monitor/owner-control/reporting/service và thêm observability/health. Core thay controller report endpoint, helper Markdown và các command-center/live/work/plans/workforce/notifications/reader/integrations partials. Worker chỉ nhận `reservation['calls']`. `architecture.md` cập nhật cùng đợt.

`phase3_1/REVIEW.md`: independent findings đã sửa RED→GREEN; follow-up22tests + newer-failure/readiness race PASS. `gateway-candidate-final.json/log`:105tests trên immutable image không mạng. `core-clone-result.json`: exact final Core/actual Native/session/CSRF/31items/active+blocked/render/Markdown. Node VM và Ruby tests ở `phase3_1/checks/`; malformed/untrusted/long80sections/table tests. Không cộng suites trùng; host163 là evidence revision trước. Một test legacy plain-text reader được cập nhật theo renderer mới; harness controller acronym typo được sửa riêng, không phải production defect.

## Trả lời 13 câu hỏi Owner

| Câu hỏi | Kết quả |
|---|---|
| 1. Vì sao toàn STANDBY? | Projection cũ không giữ last activity; active0 thì STANDBY đúng. Nay role có last run/result/error/checkpoint riêng. |
| 2. Dev thực sự chạy có đúng không? | Chỉ queue executing + latest role-start evidence mới RUNNING. Active Dev/Reviewer handoff fixtures đạt; không tạo fresh coding run MAIN để chứng minh pixel UI. |
| 3. Nhận task mới thế nào? | Backlog WP#short/title/project/full dates/search/filter/current run; live refresh giữ selection, liên kết Native/Inspector. Intake rejected hiển thị lỗi; chỉ có child WP khi planning thực tạo thành công. |
| 4. #391 failed/blocked vì sao? | Hai sessions đầu cap12 chưa hoàn tất; session cuối upstream429. Native vẫn NEW, engineering BLOCKED, attempt FAILED. |
| 5. Budget/checkpoint đã hiện? | Calls12/12, provider20011, cumulative36, checkpointv16/saved/resume reason. Checkpoint timestamp cũ thiếu nên UNKNOWN, không bịa. |
| 6. Blocked notification? | MAIN có ERROR PROVIDER_QUOTA_EXHAUSTED đúng #391/run, repoll dedup; fixture internal-budget/dismiss persist đạt. |
| 7. AUTO tiếp tục theo policy nào? | Opt-in bounded budget/cooldown/checkpoint/source/no-unknown-write; default false, provider error không auto continue, OFF không tự bật. |
| 8. Backlog/Planning/Pipeline? | Short identity, chronology, group versions/child links, expandable technical details; mười checkpoints và business reference phân biệt rõ. |
| 9. Markdown? | Structured CommonMark+sanitize/TOC/raw/export, long/XSS/Rails contracts đạt; Owner kiểm đọc thật. |
| 10. Health thật? | Năm safe HTTP endpoints UP; hai UNKNOWN hợp lệ. Không nói process/business PASS từ readiness. |
| 11. MAIN image/source? | Exact IDs ở đầu tài liệu;21serving hashes và host worker trong final-live-verification. |
| 12. Còn gì? | #391 chưa hoàn tất/provider recovery chưa xác minh; checkpoint time cũ thiếu; known RAG/n8n/WF/DR blockers giữ nguyên; Owner UAT pending. |
| 13. Owner cần thử gì? | Checklist dưới đây, đặc biệt layout1920/1600/1366/tablet/200%, notification/deeplink, report scroll và AUTO/OFF/Sync. |

## Owner manual acceptance

1. Mở Backlog, tìm391/title/run prefix. Xem đầy đủ ngày/giờ, NativeNEW và engineeringBLOCKED, Dev/provider429; đổi filter rồi chờ polling, selection/input không mất.
2. Mở Planning, tìm391; thấy plan liên quan đúng child, thời gian, short ID, related run và units; PUBLISHED không phải COMPLETED. Mở history/spec/WBS khi cần.
3. Mission: không có Agent thực thi, vẫn có #391 blocked/next action. WorkerALIVE và modeOFF không biến thành RUNNING.
4. Workforce: DevSTANDBY, last#391 blocked, 12/12calls, 11provider200, cumulative36. Cards3/2/1 columns, mở full receipts/copy, không tràn ngang.
5. Inspector #391: attemptFAILED/taskBLOCKED/NativeNEW riêng; rawcode giữ nguyên, classification429, checkpointv16, source/recovery fence; thử filters, source/diff/QA/raw. Không nhấn Resume để kiểm layout.
6. Bell/notification ERROR mở đúng run; đánh dấu đọc rồi reload phải giữ; polling không tạo duplicate. Chỉ Owner quyết định dismiss các thông báo thật.
7. Full On-Demand/Daily/Weekly: headings/lists/tables/TOC/sections, source/AI label, Raw/copy/export, mobile scroll; thử zoom200%. Không dùng report AI narrative làm evidence đã xác minh.
8. Integrations: kiểm nguồn/timestamp/latency và UNKNOWN hợp lệ; UP không chứng minh16workflows businessPASS hay DevRUNNING.
9. Nếu Owner chủ động thử controls: AUTO khi queue empty→AUTO_IDLE, OFF có confirmation/persisted state; GitHub Sync một lần→fresh fragments khôngF5/khôngduplicate. Không bắt #391 tiếp tục trước provider readiness mới và checkpoint read-back.

Không có OWNER ACCEPTED, fresh coding E2E hoặc xác nhận semantic/n8n/physical DR hoàn tất trong đợt này.
'''
(DOC/'PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md').write_text(report,encoding='utf-8')
brief=f'''<!-- PHASE3_1_CURRENT -->
# Phase3.1 — current, {stamp}

MAIN Gateway `{images['gateway']}`, Core `{images['core']}`. OFF/active0/workerALIVE; source+pins/API verified, **OWNER UAT PENDING**. #391 vẫn BLOCKED/provider429; không resume trong phiên này. Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json` và `FINAL_TEST_RESULTS.json` schema5. Các mục cũ phía dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

'''
prepend('FINAL_SYSTEM_STATUS.md',summary)
prepend('CONTINUATION_HANDOFF.md',brief+'''Giữ #391 queue/result/checkpointv16/Native row và receipt474; ba sessions36calls, latest11HTTP200+1upstream429, NativeNEW khác engineeringBLOCKED. Chỉ Owner quyết định Resume sau readiness mới/version/source/unknown-write checks. Không tạo lại task, auto-enable, tăng budget để PASS hoặc replay unknown writes. Owner UAT/pixel/200%zoom và provider recovery chưa xác minh; RAG/n8n/WF/DR blockers giữ nguyên. Rollback theo DEPLOYMENT_AND_ROLLBACK; không reset/clean/addall source untracked.

---

''')
prepend('OWNER_MANUAL_UAT_GUIDE.md',brief+'## Owner manual acceptance'+report.split('## Owner manual acceptance',1)[1]+'\n\n---\n\n')
prepend('OWNER_CONTROL_AND_LIVE_OBSERVABILITY_EVIDENCE.md',brief+'''## Evidence Phase3.1

`phase3_1/main-readback.json`: actual signed API/production ERB, #391/role/budget/notification/health. `native-identity.json`: Native379/391 cùng loạiTask,379một record; `wp391-before.json`/`wp391-after-identity.json`: exact protected record hashes/provider474 unchanged. `native-before.json`/`native-after-identity.json`:13tables identical. Candidate/clone/review scopes ở report tập trung; no GUI/provider inference.

---

''')
prepend('FULL_DEFECT_REGISTER.md',brief+'''## Phase3.1 defects

| Defect | Disposition |
|---|---|
| WP identity/date/379 false Epic | FIXED / DEPLOYED; NativeTask vs engineering unit projection, no deletion |
| Workforce loses historical failure, rework shown succeeded | FIXED / DEPLOYED; per-role activity + regression |
| Mission/Pipeline fake active or opaque stages | FIXED / DEPLOYED in tested contracts; active0 does not imply AgentRUNNING |
| Budget generic failure / provider dead-end / nested SQLite write lock | FIXED / DEPLOYED; scoped classification/readiness-before-lock/race fence |
| Duplicate Resume spends continuation without execution | FIXED / DEPLOYED; pending marker/requeue dedup |
| Child blocked note/notification missing or ERROR shown INFO | FIXED / DEPLOYED; correct child/run/level, durable dedup/read |
| Raw Markdown reader / overflow | FIXED / DEPLOYED in Rails/Node/CSS contracts; pixel/print Owner UAT pending |
| Integrations lack sourced health | FIXED;5HTTP UP, OpenClaw/Demo UNKNOWN valid |
| #391 provider429 | OPEN operational block; no new provider/quota recovery evidence; task not complete |
| Semantic/n8n/WF07/12/DR historical blockers | UNCHANGED; not hidden by UX fixes |

---

''')
prepend('DEPLOYMENT_AND_ROLLBACK.md',brief+f'''## Phase3.1 rollout / rollback

`phase3_1/deployment-initial.json`, `deployment-pre-identity.json`, `deployment.json` retain each exact image/source revision. Initial pair backup: private `phase3_1-rollout-20261102T153924`; final backend/UI follow-up: `phase3_1-final-rollout-20261102T154856`; final Core identity-only correction: `phase3_1-core-identity-rollout-20261102`. All below `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/`; PG/SQLite/config before-files retained, no reset/restore. Scripts verify idleOFF/queue0, config image-only parity, candidate tests, worker stop/start, health and rollback.

Immediate rollback: when OFF/idle, stop `QLDAPMEngineeringDelivery`, restore Core image0d647f91 and ui-bridge/image-lock from identity backup, recreate only web, health+source read-back, start worker. This reverses labels/plan grouping only. Whole Phase3.1 rollback uses initial pair ce047/7649 and its three pin/config before-files; restore `engineering_worker.py.before` from initial backup if reversing Gateway protocol expectations. The worker change is reserved cap consumption only; don't casually mix older claim protocols. Do not auto restore databases: new notifications/command receipts would be lost. Unknown writes require reconciliation before retry. n8n/DB/Qdrant/Demo not deployed by this work.

Final immutable IDs: Gateway `{images['gateway']}`, Core `{images['core']}`. Exact hashes at `phase3_1/final-live-verification.json`. API read-back occurred on final Gateway with same controller and Core before final identity-only text/grouping patch; final Core subsequently qualified in Native clone and serving hash/pin verification. No whole-image coding E2E or Browser UAT claim.

---

''')
old_index=DOC/'FINAL_TEST_RESULTS.json'
archive=OUT/'previous-final-test-results-schema4.json'
assert not archive.exists()
archive.write_bytes(old_index.read_bytes())
checks=[]
for path in sorted((OUT/'checks').glob('*.json')):
    record=json.loads(path.read_text(encoding='utf-8-sig'))
    checks.append({'record':str(path.relative_to(DOC)).replace('\\','/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        **{k:record.get(k) for k in ['command','started_utc','finished_utc','environment','tested_image_digests','exit_code','outcome','source_changed_during_check','evidence']},
        'current_serving_component_hash_matches':{k:record.get('source',{}).get('files',{}).get(k)==v for k,v in release['source_files'].items()},
        'scope_note':'Historical/failure entries retained; do not infer final image from host suite or sum overlapping tests.'})
for name in ['gateway-candidate-final.json','core-clone-result.json','gateway-owner-startup-rollback.json','main-readback.json','native-after-identity.json','wp391-after-identity.json','final-live-verification.json']:
    path=OUT/name;checks.append({'record':'phase3_1/'+name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'evidence':json.loads(path.read_text(encoding='utf-8-sig'))})
index={'schema_version':5,'snapshot_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'overall_status':'PHASE3_1_DEPLOYED_API_CLONE_VERIFIED_OWNER_UAT_PENDING; PROVIDER391_AND_PREEXISTING_BLOCKERS_REMAIN',
    'current_images':{**images,'n8n':live['containers']['n8n']['image']},'current_serving_source_manifest':'phase3_1/final-live-verification.json#runtime_source_sha256',
    'aggregation_policy':'Final immutable Gateway105 PASS; Owner recovery22 included, health3 included. Core clone separate. Host163 is prior revision, not complete final-source certification. No overlapping sums; no browser/pixel/whole-image coding E2E.',
    'historical_index':'phase3_1/previous-final-test-results-schema4.json','checks':checks}
old_index.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
architecture=ROOT/'architecture.md'
text=architecture.read_text(encoding='utf-8-sig');start=text.index('## Phase 3.1 — implementation in progress');end=text.index('<!-- CHATGPT_RECOVERY_MAIN_30218AFF -->',start)
text=text[:start]+brief+'''Kiến trúc: Rails AiBridge → Gateway → Store/queue → Windows worker → OpenClaw/provider giữ nguyên. Shared observability projection là nguồn cho task/run/role/budget/checkpoint; Native status độc lập engineering verdict. Durable notifications dedup/read, sanitized CommonMark ở Rails, bounded safe HTTP readiness aggregation; no new provider/framework/scheduler. Continuation opt-in, same run/version/source/fencing/unknown-write guards; readiness-before-lock và recheck latest failure; worker dùng cap Gateway. Không thay n8n/RAG/DB/Demo. Thiết kế và scope: `docs/ai/engineering/CHATGPT_RECOVERY/PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`.

'''+text[end:]
architecture.write_text(text,encoding='utf-8')
print(json.dumps({'status':'DOCUMENTS_UPDATED','current_images':images,'test_records':len(checks),'owner_uat':'PENDING OWNER'}))

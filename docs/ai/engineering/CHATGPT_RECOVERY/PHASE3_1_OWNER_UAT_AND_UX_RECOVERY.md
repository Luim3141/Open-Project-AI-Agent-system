<!-- FINAL_DEMO_CURRENT -->
# Final Demo — 03/11/2026, verified 2026-11-02T21:53:26.525639+00:00

**PARTIAL DEMO ACCEPTANCE: runtime/n8n/provider recovery/DR verified; semantic RAG FAILED; Owner Browser UAT PENDING.** Không coi security defer là PASS hoặc RAG functional failure là được defer.

MAIN images: Gateway `sha256:3c06559033eba39f423a0c6f9474d1f77e3ef2ebd3617e1b37e50147d2d51a31`, Core `sha256:5936d90e450e8af321557e94928807f646dd077e646c1ceb546f858890aef2e8`, n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Exact source/pins: `demo-final/final-live-verification.json`. OFF/active0/workerALIVE/provider gatefalse. OpenClaw READY và Demo UP từ API/CLI nguồn thực (`demo-final/readback-final.json`).

#391 cùng run `b7fd6aec-3357-495f-b9e5-f7ba04d67ad6` SUCCEEDED, checkpoint39, recovery3 (một continuation mới), total45generation calls (9 mới). Dev/Reviewer/QA và37pytest PASS; commit `1914f10d3bd0b2b05459914100c53549f63d0bc5`, [PR10](https://github.com/Luim3141/mini-task-manager/pull/10) OPEN, chưa merge/deploy Demo. Native391 version2, status độc lập engineering success; WP379 chưa Done. Không tạo duplicate WP/unit/run/PR. Probe riêng1generation/24tokens; tổngproviderreceipts474→484.

n8n16/16 bounded business scenarios PASS trên clone, không khẳng định mọi nhánh/approval/generation. WF07/12 MAIN collectors READY4/4, actor19 vẫn bị403; WF12 schedule branch thực thi trên clone, MAIN dùng đúng signed collector contract. WF04 MAIN retained execution3074 SUCCESS chứa exact RUN_COMPLETED event/ACK của #391; 3060 trước đó là replay failure event. Credentials4/4 decrypt vàusers/671execution trước cutover được bảo toàn; master key giữ nguyên; pruning720h/10000.

RAG locked holdout baselineHit@5=3/20,FPR0/20; rejectedcandidate13/20,FPR14/20. Không rollout/tune holdout đã xem, servingthreshold0.65. Exact childcitation/version vàfreshness read-back riêng không chứng minh semantic PASS.

DR **LOCAL_RESTORE_VERIFIED**, kit `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\demo-recovery-20261102T214523Z-final`, ciphertext `a94624d7f2339dc64accfe853e4f87a589a919bdeeddf22d42ad23420a857350`. `demo-final/dr/restore-final.json`, hướng dẫn `demo-final/dr/README.md`. OFF_HOST_COPY_PENDING_OWNER; chưa physical-machine DR. Project5:13table fingerprints identical,341WP/344relations/968journals (`demo-final/native-after.json`).

Fresh coding task0; actual391continuation1/1; noGUI/paidservice/keyrotation/autoPRmerge/productionDBreset. Owner UAT chưa thực hiện.

Phase3.1UIretained; onlyIntegrationscards/healthprojectionupdated, nofullUIrewrite.
<!-- END_FINAL_DEMO_CURRENT -->

<!-- PHASE3_1_CURRENT -->
# MAIN — Phase 3.1 Owner UAT recovery

Checkpoint **2026-11-02T23:14:21+07:00**. Gateway `sha256:b184f91963e53df47cbc884cc353d03b0bce871ee19b45b5dc7a5ca78fd638ab`, Core `sha256:e8474e53c7f56a46cd724f4a938a33f9ba01374fbaeb4bb729499cce4fbd4e84`, n8n `sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795`.

**SOURCE FIXED / CANDIDATE TESTED / DEPLOYED / API VERIFIED; OWNER UAT PENDING.** Core/Gateway healthy, worker ALIVE, mode OFF, active0. Exact21 serving source files và pins đã kiểm tra; worker giữ protocol, nhận cap Gateway bằng một dòng đã có regression. Không Computer Use, không resume/tạo lại #391, không inference/provider probe, không tăng production cap để PASS.

#391: engineering BLOCKED/attempt FAILED; Native business status **NEW**. Ba Dev sessions: 12/12HTTP200, 12/12HTTP200, 11HTTP200+1HTTP429; tổng36 calls. Lượt đầu dừng do cap nội bộ; lỗi gần nhất là upstream429. Checkpointv16 còn nguyên; raw historical result/queue/checkpoint/Native row giữ nguyên hash, provider receipt count474 không đổi. Không có evidence phân biệt RPM/TPM/RPD hoặc thời điểm reset. Resume hiện bị fence `PROVIDER_RECOVERY_REQUIRED`; readiness đã lưu cũ không phải bằng chứng provider phục hồi.

UI: WP ngắn/ngày giờ đầy đủ, search/filter/selection, Current/Recent Work, Agent Current State + Last Activity, summary budget/checkpoint, durable child/run notifications, plan versions, structured sanitized Markdown/TOC/raw/export, health có nguồn/timestamp. #379 là Native **Task**, một record với hai engineering unit references; bỏ nhãn Epic giả, không xóa dữ liệu.

Validation: final immutable Gateway **105 tests PASS** (Owner recovery22 là tập con); final Core actual Rails/Native/login/session/CSRF/full-template clone PASS; Node VM polling/Inspector/reader/filter và Ruby Markdown/XSS/long-document PASS. Host163 PASS thuộc revision trước follow-up, không dùng để chứng nhận toàn source cuối hoặc cộng dồn. MAIN signed Rails→Gateway/API + production ERB read-back PASS; nhãn identity cuối được kiểm trên clone và serving hashes. Project5: toàn cột13 bảng scoped/global không đổi; 341WP/344relations/968journals. Không phải kiểm mọi bảng hoặc whole-image coding E2E.

Remaining: provider429/#391 chưa hoàn tất; Owner Browser UAT/pixel/200%zoom pending; historical checkpoint time không có timestamp đáng tin nên UNKNOWN; OpenClaw/Demo health UNKNOWN do thiếu safe endpoint đã cấu hình. In-app không bảo đảm báo khi đóng web. Semantic RAG FAILED/PARTIAL, n8n master-key/history OPEN/BLOCKED, WF04 retentionOFF, WF07/WF12 PARTIAL, off-host custody/physical DR PENDING giữ nguyên.

Authority: `PHASE3_1_OWNER_UAT_AND_UX_RECOVERY.md`, `phase3_1/final-live-verification.json`, `phase3_1/main-readback.json`, `FINAL_TEST_RESULTS.json` schema5. Các block cũ bên dưới là lịch sử.
<!-- END_PHASE3_1_CURRENT -->

## Root causes và mapping

- Backlog trộn Native record, project anchor và engineering unit; thiếu thời gian/identity dễ đọc. Native379 có một record loại Task, hai unit `crud-search-web-v1` và `create-list-persistence-v1` tham chiếu nó. Native391 là Task riêng. Không phải hai Native records để xóa. Parent anchor và unit/run identity nay tách nhãn; search WP/title/run, filters ALL/ACTIVE/READY/BLOCKED/COMPLETED; ngày giờ `dd/MM/yyyy HH:mm:ss`, Asia/Ho_Chi_Minh; live polling giữ input/selection/details.
- Planning: ID/spec/unit metadata từng đổ ra cùng cấp. Nay summary/BA-PM details, created/published, counts và related run; group theo child WP nếu plan chỉ có một child, giữ source anchor khi nhiều child. Search áp dụng từng plan version, không để một match làm hiện toàn bộ versions của parent379. PUBLISHED không bị đổi thành COMPLETED.
- Workforce chỉ chiếu status hiện tại nên mọi card về STANDBY khi run kết thúc. Projection nay lấy scoped queue→events→role→receipts; giữ last activity riêng từng role, kể cả Dev đã xong khi Reviewer chạy. Historical receipt hoặc Worker ALIVE không tự tạo RUNNING. Failure của rework/AGENT_FAILED có precedence hơn completed step cũ. Cards3/2/1 columns, wrap/min-width0, raw JSON/receipts ở details, có copy full ID.
- Mission/Pipeline hiển thị current/recent/blocked, không dùng Epic IN PROGRESS để nói Agent chạy. Mười execution/integration checkpoints có evidence riêng; tám bước business reference thu gọn, không dùng badge8/8 như trạng thái hoàn tất. Integration success không thay review/QA artifact.
- Inspector dùng cùng summary theo run, tách attempt/engineering/Native status, provider responses và task completion. Timeline nhóm theo role/stage, lọc milestones/errors/model/tools; giữ source/diff/Reviewer/QA/raw và request-token guards.
- Report reader cũ dùng textContent narrative nên hiển thị Markdown thô. Helper dùng Commonmarker có sẵn + Rails sanitization, không raw HTML; link allowlist Native/GitHub, bỏ credential/javascript/foreign URLs. Có headings/lists/tables/code/quotes/TOC, structured factual summary, AI/provenance labels, sections/raw/copy/export; không sửa DB report. Modal riêng scroll/mobile. Pixel/print thật cần Owner kiểm tra.
- Health aggregate chỉ safe GET cố định, không redirect/credential/inference; concurrent deadline2.2s, timeout1.5s, TTL60s. UP chỉ là readiness, authentication/process/business có nhãn độc lập. Read-back: OpenProject/Gateway/n8n/Qdrant/Ollama UP; OpenClaw/Demo UNKNOWN đúng vì thiếu endpoint an toàn đã cấu hình.

## #391: nguyên nhân tiếp tục vẫn bị BLOCKED

Snapshot Owner ban đầu chỉ có một session. Live evidence đã có recovery_count2 trước phiên này: ba sessions, mỗi session12 calls; session3 có một upstream429. `openclaw_provider_gate.py` chỉ ghi receipt HTTP status nhận từ Google; local allowance hết trả403 `ENGINEERING_PROVIDER_BUDGET`, không phải429. Vì vậy lỗi cuối là provider rejection thật; hai lần trước là internal budget chưa đủ để Dev kết thúc. HTTP200 không chứng minh Dev hoàn tất. Reviewer/QA chưa chạy cho #391.

## Saved provider diagnostics

Đã kiểm thêm saved `dev-0-result.json`, `dev-0-trajectory.jsonl` và transport của đúng run: có code **RESOURCE_EXHAUSTED** cùng429, không tìm thấy quota metric/Quota ID/RetryDelay trong các artifacts này. Bản trích chỉ giữ code/count/hash, không xuất raw prompt/token: `phase3_1/provider-diagnostic-artifacts.json`. Vì vậy không đoán RPM/TPM/RPD hoặc giờ reset.

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

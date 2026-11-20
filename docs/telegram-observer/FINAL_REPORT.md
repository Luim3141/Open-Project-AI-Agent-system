# QLDAPM MAIN — Telegram Commander, Agent Observer và Agent Studio

Snapshot bàn giao: 06/11/2026, Asia/Bangkok. **LOCAL FUNCTIONAL VERIFIED; fresh business E2E qua Owner acceptance, Telegram completion và live reply/Gateway/Gemini đã xác minh.** Đây không phải chứng nhận toàn hệ thống production-ready. Các mục dưới phân biệt execution thật, fixtures và phần chưa xác minh.

## A. Tổng quan

Đã triển khai vào MAIN hiện hữu: service Telegram aiogram long polling + Gemini `gemini-3.5-flash-lite`, validated Tool Adapter, Observer dùng chung dữ liệu runtime, Agent Studio trong Rails, durable notification outbox và outgoing workflow n8n. Pairing Owner thật, function calling và Telegram delivery đã chạy thực tế. Không tạo Supervisor/runner mới, Adaptive Subtask hoặc đổi provider/key của Coding Agents.

Fresh E2E được Owner duyệt: Task397, plan run `8f93d0a1-8115-49b5-bc73-2487e778a7cd`, coding run `a3f592fc-b91e-4f57-a812-a930bb20e079`. BA/PM đã công bố kế hoạch và dependency; Dev/Reviewer/QA đã chạy thật, Native publication và knowledge read-back xong. Owner đã duyệt scope và nghiệm thu: business DONE/v11, runtime/acceptance COMPLETED, cả8gates PASS. TASK_COMPLETED được n8n gửi thật, Telegram message16/attempt1/SENT.

Mô tả ban đầu ghi `/health`, nhưng route health hiện có là `/healthz`; Dev chỉ bổ sung tests cho `/healthz`, không thay ứng dụng. Owner đã chấp nhận khác biệt này, cho chuẩn hóa tên Task thành “Regression tests GET /healthz” và chuyển đúng397 sang DONE. Approval, exact PR head và current Native version được kiểm trước mutation; `owner-approval.json` và `owner-acceptance-result.json` giữ audit, không giả approval từ runtime.

## B. Source code

- Repository local: `D:\AI project\QLDAPM chat`; branch `codex/telegram-agent-observer`; feature commit **`4f2810b`**, journal/notification security patch **`3d3027c`**, reply provenance **`cfd2cb9`**.
- Source chính: `openproject/ai/telegram-ai/`; Gateway `agent_observer.py`, `telegram_notifications.py`, service/catalog; Rails observer/controller/routes/acceptance/permission mapping; Compose và manager Start; n8n generator/installer; rollout helper và tests.
- Repo trước thay đổi có hầu hết source chưa tracked. Commit chỉ ghi các module liên quan (47files), không gom toàn bộ untracked docs/artifacts của người dùng. Đây là commit trên codebase local hiện có, không phải standalone baseline của toàn repo. Không push/merge remote.
- `git diff --check` có warnings whitespace đã tồn tại trong các module/architecture trước khi được track; không gọi check này PASS. Không dọn unrelated whitespace làm drift source/image đang phục vụ.
- Quét exact staged source47files bằng patterns key Google, token Telegram, GitHub PAT/private key: không phát hiện giá trị secret. Đây là targeted scan, không tuyên bố audit toàn repo.

## C. Docker và auto-start

| Thành phần | Image đã deploy |
|---|---|
| Gateway | `sha256:15a98224c2163b65c1068504a69cbf889f13f7535919eee06cee38e98dc9d923` |
| Rails Core | `sha256:5d65e5739028457829858b4b58c732565b878db20749703937c4c1e4bda4e16f` |
| Telegram | `sha256:ca69e909db64ad02c1d547252df78c91e56b22cc895d9e1efec930e2ca12ec3e` |
| n8n, giữ image cũ | `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269` |

Telegram trong project/network `qldapm-ai`/`qldapm-ai_ai`, không host inbound port/Docker socket; non-root10001, rootfs read-only, cap-drop, resource limits và state bind mount riêng. Gateway/Core giữ Compose parity và networks hiện có. Rollout dùng immutable base, exact source hashes, idle/OFF guard, host worker fence, private SQLite backup và image rollback; không restore business DB.

Controlled restart riêng Telegram: PASS, giữ pairing/memory/processed updates/outbox/reply context; không inference khi startup. `unless-stopped` đã kiểm. Sau Docker Desktop restart do môi trường bên ngoài lúc khoảng02:38 ngày06/11, đã quan sát Core/Gateway phục hồi healthy và Telegram trở lại POLLING với outbox còn nguyên. Không gọi đây là controlled Desktop/Windows reboot test do agent thực hiện; Windows reboot chưa kiểm.

`candidate-v8/deployment.json`, `bot-image-tests.json`, `compatibility-final.json` và `service-restart.json` là bằng chứng. Hai trường reporter kế thừa `github_sync_enabled:false`/`n8n_integration_enabled:false` trong deployment JSON không mô tả config thực; helper Telegram giữ nguyên config bằng deepcopy và hash verification xác minh config không đổi.

## D. Telegram và Gemini

- Bot [@qldapm_commander_bot](https://t.me/qldapm_commander_bot), private chat; numeric Owner `1916909968` đã pair projects5/6, token không xuất hiện trong repo/log/chat.
- Mã pair ngẫu nhiên, một lần, TTL5phút, tối đa5attempts; revoke và private-chat checks. Đây là single-Owner binding qua dedicated bearer principal18, không giả Native identity cho nhiều người.
- Owner nhập key Gemini riêng local và xác nhận Free Tier chưa bật billing. Exact model locked `gemini-3.5-flash-lite`; metadata và real function calling đã kiểm. Coding credentials/config byte hashes giữ nguyên. Không provider/model fallback; model routing mismatch khóa inference.
- Bot budget20 requests/ngày tính mỗi attempt, bounded rounds/calls/context/output; chỉ một retry HTTP5xx. Không tự gọi inference khi startup/health. Gateway liveness không phải provider READY; model READY có TTL.
- SQLite memory giữ project/task/run, recent16messages, historical excerpts5k, pending confirmations và notification reply context. Mỗi câu hỏi status lấy dữ liệu Gateway mới; memory/RAG không chứng minh live state.
- Câu hỏi thực của Owner về391 bị lỗi default-project lúc đầu; đã sửa chỉ tìm trong paired+configured projects khi exact Task403/404. Lần read lại thật đã trả lời qua Telegram message9. Reply thực “Dev đã làm gì ở Task này” vào notification gặp503maintenance lúc rollout; giữ context391, retry đúng câu đọc sau maintenance đã dùng live Gateway/Gemini và gửi message12. Đây là **operator retry của input thật**, không gọi là toàn bộ poller conversation E2E pass không cần can thiệp.
- Lượt live sau bàn giao đã qua poller → Gateway fresh read → Gemini, nhưng target thực là391 (correlation `dc44c649-7dd7-4c12-83ab-1f27de1e8937`), chưa xác minh context397 mong đợi. Mapping message16→397 trong SQLite đúng. Vì bản cũ chưa audit reply-to ID, không kết luận user chọn tin khác hay parser nhận reply khác. Đã thêm metadata incoming reply/context và actual outgoing message ID, không đổi quy tắc chọn Task; test qua aiogram dispatcher chứng minh reply16 ưu tiên397 trước memory391. Proof `live-followup-initial.json` giữ nguyên lượt cũ; kết quả lượt xác minh mới ở dưới.
- **Lượt xác minh cuối PASS:** incoming message19 có `reply_to_message_id:16`, notification mapping397, memory cũ391. Poller dùng đúng run `a3f592fc-b91e-4f57-a812-a930bb20e079`, fresh Gateway `get_task_progress(task_id=397)` với correlation `5edab356-7ba8-4372-8ff1-c90921c3219f`; Gemini exact `gemini-3.5-flash-lite` thành công, trả đúng file/commit/status397, Telegram ACK actual message20 trả lời input19. Memory chuyển sang397 từ reply context, không có operator retry hoặc sửa memory thủ công. Proof `live-reply-397.json`. Nguyên nhân lượt cũ vẫn không thể truy hồi từ metadata chưa được ghi; không gọi việc bổ sung audit là đã sửa được nguyên nhân đó.
- Writes cần confirmation một lần TTL180s + current revision; create/update Project5 còn cần exact Gateway proposal approval ở bước hai. Project6 generic create/update và independent review/QA execution không có backend API nên bị từ chối, không dựng orchestrator bù. Fixture tests kiểm confirmation/replay/unknown outcomes; chưa chứng nhận mọi write callback bằng live E2E.

## E. Observer và Visualizer

Một projection canonical từ AgentTask/AgentRun, event/receipt/checkpoint, runtime result và Native ACL. Owner có quyền xem actor khác chỉ khi Native role/capability hiện hành xác minh được; mọi referenced Work Package phải đọc được. Không gọi đường đọc có thể expire queue. Legacy schema/missing historical references hiện UNKNOWN có source conflict, không ép success hoặc làm sập danh sách.

Agent Studio: [mở tại MAIN](http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai/observer). Chọn Task/run, graph stages thực, timeline, artifacts và freshness; no fake percentage. Bounded polling10s, pause khi hidden, timeout/backoff và Turbo cache rebind.

Main Edge headless login Owner thật: PASS HTML/live list, JSON cùng canonical snapshot, graph3stages/run1/timeline121events cho391, mobile390px không tràn container, cross-project403/404 và reload. Final397 cũng PASS trên Corev8: acceptance COMPLETED,3stages/1run/51events, desktop/mobile/reload/project denial. Screenshots `agent-studio-main.png`, `agent-studio-mobile.png`, `agent-studio-task397.png`, `agent-studio-task397-mobile.png`; proofs `ui-smoke.json`, `ui-smoke-397.json` đều `css_preview_only:false`. Preview CSS riêng không được dùng thay bằng chứng deploy cuối.

Fresh397 đã ghi snapshot từ QUEUED → dev RUNNING → reviewer/qa hoàn tất → runtime COMPLETED/AWAITING_OWNER_APPROVAL → DONE/acceptance COMPLETED sau quyết định Owner. Stages/roles không có dữ liệu không được dựng giả. BA/PM của pipeline hiện có chạy ở plan parent379 và có plan/run linkage; Task397 giữ coding stages thực, không biến mỗi role thành một Task mới.

## F. Notifications

Workflow [QLDAPM Telegram Agent Notifications](http://127.0.0.1:5679/workflow/bDpuIXfCgEkVOb7B) đã publish; dedicated2credentials mới, 16workflow/4credentials cũ giữ hash nguyên trước fresh E2E. Không Telegram Trigger/getUpdates trong n8n; poller duy nhất ở service Telegram.

Observer candidates → SQLite outbox unique(event_id,chat_id) → n8n validate current lease/recipient/preferences và đọc lại Native Task/project ACL → native Telegram Send Message → actual message_id ACK → SENT + reply context. TASK_COMPLETED còn được kiểm lại acceptance hiện hành trước send authorization. Lease/backoff, tối đa6attempts, at-least-once. Không báo SENT khi chỉ HTTP200 hoặc workflow đã kích hoạt.

| Event thực | Telegram proof | Ý nghĩa |
|---|---|---|
| DELIVERY_TEST cho391 | message8, SENT/attempt1 | Kiểm thử kênh trung lập, không phải Task completed |
| TASK_BLOCKED cho plan379 | message13, SENT/attempt1 | Lỗi Native lost ACK thật; đã giữ checkpoint/đối soát/resume |
| AWAITING_APPROVAL cho397 | message14, SENT/attempt1 | Runtime xong, Owner chưa nghiệm thu |
| PR_CREATED cho397 | message15, SENT/attempt1 | Actual PR14 creation evidence |
| TASK_COMPLETED cho397 | **message16, SENT/attempt1** | Actual8gates + Owner journal1251; không phải fixture/test event |

Sáu business event types được hỗ trợ: TASK_COMPLETED, TASK_BLOCKED, AGENT_FAILED, QA_FAILED, AWAITING_APPROVAL, PR_CREATED. Completion cần runtime delivery, actual stages, commit, independent review exact revision, QA exit0, Native handoff và final DONE journal của PM/Owner hiện hành. Header/ACK auth và revoke/preferences được kiểm lại lúc gửi; outbox không làm Task execution thất bại.

## G. Tests và evidence

| Kiểm tra đã chạy | Kết quả | Phạm vi |
|---|---|---|
| Gateway/Observer/security/regression host | **103 PASS** | unittest, isolated fixtures; rerun sau controller permission regression |
| Gateway immutable candidate-v4 | **92 PASS, 2 SKIP / 94** | Hai case host-only trên Linux; source Gateway sau đó không đổi |
| Bot production image | **38 PASS** | Actual Python3.13 image, network none; gồm Native revoke-after-enqueue, completion recheck và aiogram reply dispatch |
| Bot host pytest | **38 PASS** | Python3.14 có SDK deprecation warning; production3.13 |
| Ruby Native journal projection | **3 tests/7 assertions PASS** | Final transition, comment/reopen, association default ordering |
| Node client cache regression/syntax; Ruby/ERB syntax | **PASS** | Prior cache failure reproduced RED, current GREEN |
| Main authenticated desktop/mobile UI | **PASS** | Actual localhost18088, no business writes/model calls |
| Real Gateway snapshot | **PASS** | 13historicaltasks, explicit UNKNOWN legacy, no inference/business write |
| Pairing/Gemini/read reply/n8n neutral + blocked event | **VERIFIED** | Actual numeric pairing, function calls, delivery ACK IDs |
| Controlled Telegram restart | **PASS** | Persistence + no startup inference |
| Fresh coding397 | **63 pytest PASS; review/QA/Owner gates PASS** | Real BA/PM, Dev, Reviewer, QA; PR14/head045c95a; actual completion delivery16 |
| Live reply notification397 | **PASS** | Actual input19→reply16→397, memory cũ391, fresh Gateway/Gemini, actual Telegram answer20 |

Fixtures kiểm revoke/role changes/project denial, malformed schemas, memory truncation/secret filtering, stale state, model fallback refusal, budget/retry accounting, callback expiry/replay/concurrent claim/version changes, proposal second approval, notification dedup/lease/preferences/failure/ACK handling. Không cộng các suite overlap thành một con số unique tests hoặc gọi fixtures là Main E2E.

Lost ACK của plan dependency: Native relation366 đã tồn tại đúng396→397; one-shot read-back xác minh current Owner scope/source/payload/unique relation, backup rồi CAS đúng receipt pending. Native writes0, không sửa runtime success. Resume checkpoint thật, không gọi lại POST hoặc replay BA/PM outputs. Proof `planning-relation-readback.json`, `real-e2e-plan-resume.json`.

Real final acceptance phát hiện thêm association `journals` có default ASC: `.order(DESC)` nối sau ASC làm reverse đọc ngược. Đã sửa một dòng sang `.reorder`, test RED→GREEN, read-only Rails replay trên397 chứng minh false→verified true, rồi deployCorev8 và kiểm Native/Observer/UI thật. Journal1251/actor18 được đọc đúng; không đổi dữ liệu hoặc bỏ gate để ép notification. `journal-order-readback.json` là candidate-process evidence, còn `ui-smoke-397.json` và final Observer snapshots chứng minh serving Main.

## H. Compatibility

Trước fresh E2E, protected-state verification PASS:126queue rows,229runs,975requests,577coding receipts,28checkpoints, original251tokens nguyên byte-hash; chỉ thêm1dedicated token. Gateway config, credentials, coding Gemini key/policy và bridge/automation keys không đổi. Native business/config12/13scope hashes giữ nguyên; scope users riêng có auth delta sau failed/successful UI login, chưa chứng minh toàn bộ delta.

Trong E2E mới, chỉ append runs/receipts/checkpoints/requests hợp lệ. `compatibility-final.json` so sánh toàn bộ prefix rows cũ và original config/key hashes, không chỉ counts. Existing rows đều PASS; các số mới không bị giả thành “hệ thống không thay đổi”. Project6 plan có thêm task397, notes/dependency và publication theo existing backend. Không reset dữ liệu/volumes/workflows, không sửa coding budget/model, không replay391/396 hoặc merge/deploy PR14.

## I. Giới hạn và quyết định còn lại

1. Owner đã nghiệm thu `/healthz` và397; business completion và notification-context397/live reply đều PASS. Lượt hỏi cũ từng đi vào391 chưa có reply metadata nên nguyên nhân lịch sử chưa được xác định. Lượt mới chứng minh ưu tiên reply397 trước memory391 và đã có tracing để điều tra nếu tái diễn; không quy lỗi cho user hoặc tuyên bố đã sửa một nguyên nhân chưa chứng minh.
2. Generic Project6 CRUD/independent review/QA writes chưa có backend API; unsupported được báo rõ. Live callback coverage chưa đầy đủ; các confirmation/security branches đã có fixtures.
3. Full Native users baseline hash khác sau auth; Gateway credentials/config nguyên hash nhưng không tuyên bố toàn bộ Native security rows không đổi. Không reset counter/password để ép PASS.
4. Observer bounded200run scan / max50selected task history / UI20results, có truncated marker; chưa load/performance qualification lớn. Polling không phải streaming.
5. Laptop offline thì bot offline. At-least-once notification có thể trùng khi Telegram nhận nhưng ACK mất. Bearer30ngày cần enrollment lại theo quyền thật.
6. RAG algorithm qualification/những giới hạn toàn hệ thống trước phiên này không được sửa hoặc chứng nhận bởi tính năng mới. Native lost-ACK đã reconcile, không có auto replay unknown writes.

## J. Hướng dẫn

Xem `INSTALLATION.md` và `OPERATIONS.md` để cài additive/start/check/pair/revoke, cấu hình secret local, commands, troubleshooting, backup và rollback. Owner mở bot, hỏi bằng tiếng Việt hoặc reply notification; mở Agent Studio cùng tài khoản OpenProject để đối chiếu. Khi thao tác ghi, đọc phạm vi project và exact confirmation; nếu pending/unknown thì đối soát receipt trước thao tác tiếp.

Source commit đã có; evidence/docs được ghi bằng commit bàn giao riêng sau khi hoàn tất quyết định Owner. Các private `.env`, UAT credential, SQLite/n8n backups và mã pair không nằm trong commit.

# Agent Studio V2 Stabilization — bàn giao 12/11/2026

## A. Tổng quan

**Đã triển khai bản sửa; nghiệm thu tổng thể PARTIAL.** Những lỗi Explorer no-op, navigation trắng, attempt edges ngược, Retry-After bị bỏ qua, runtime RUNNING bị che bởi kết quả cũ và read path quá nặng đã được sửa. Admission bảo vệ Puma callbacks đã được kiểm chứng bằng HTTP component test và triển khai MAIN. Không tuyên bố đạt toàn bộ performance/multi-tab gate.

Phiên resume chỉ một agent, không GUI, không tạo Task hoặc gọi inference mới. MAIN chạy đúng source đã qualification, Core/Gateway healthy; bot/n8n không rebuild. Task #398 giữ READY FOR RELEASE / AWAITING_OWNER_APPROVAL; PR #15 OPEN. Những báo cáo V1/V2 trước đây giữ nguyên, không dùng image lịch sử làm bằng chứng hiện tại.

## B. Root Cause Analysis và bản sửa

| Vấn đề | Bằng chứng / nguyên nhân | Bản sửa và kiểm chứng |
|---|---|---|
| Task list và #379 rất chậm | List cũ 831,889 B/18.20s; profile379 có18 Native calls/72 SQLite opens | Native metadata batch với ACL hiện hành; SQLite RO connection/cache trong từng request; list nhẹ, graph summary, details lazy/paged. Không cache quyền xuyên request. |
| HTTP503 khi tải đồng thời | MAIN ghi OPENPROJECT_UNAVAILABLE/REQUEST_DEADLINE; Rails chờ~12s trong khi Observer~0.8–1.3s. Isolated Puma4threads/4bridge requests tái hiện4HTTP503 | Nonblocking admission trong shared AiBridge, theo từng Puma worker: tối đa half threads (4→2), chừa callback capacity. Cùng component sau sửa2HTTP200+2HTTP429, ~203ms. Không tự retry mutation. Không khẳng định mọi503 lịch sử có cùng nguyên nhân. |
| Explorer click no-op | Authenticated baseline click không focus search | Click focus/scroll thật, MAIN entry từ Command Center và mobile touch đã có bài kiểm tra riêng. |
| Back/Forward trắng Studio | React island ghi history state làm mất metadata Turbo | Preserve history state và cleanup listeners/request theo generation; fixture và authenticated navigation/back/forward/reload. |
| Dagre chạy lại theo status | Geometry dựng trong mỗi graph projection | Cache topology/direction tối đa16, memo node; fixture status-only refresh không tăng layouts/render. MAIN có2layouts sau thay đổi viewport direction. |
| Retry-After1 bị chờ5s | Retry cũ chỉ nhận một error code/không xử lý header chung | Parse seconds và HTTP-date cho429/503; Rails forward header hợp lệ; positive jitter, tối đa3retries. Invalid/missing dùng bounded backoff;401/403/404/409/422 không tự retry. Hint quá lớn ngoài browser timer budget giữ lỗi, không retry sớm. |
| Attempts/newest-first/timestamp ties | UI dùng thứ tự trang mới nhất; SQL chỉ timestamp không tie-break | UI theo canonical run order; SQL created_at/queue_created_at và rowid sequence, không sort UUID; pagination giữ global order. Equal event timestamps giữ sequence hoặc stable input. Retry/resume không tạo attempt giả. |
| RUNNING bị hiện QUEUED/COMPLETED cũ | Chỉ suy từ final results của attempt trước | Dùng current_agent/events durable kể cả rework; không thêm BA/PM child coding runs vào parent plan. |
| UI deadline ảnh hưởng Telegram | Named UI views và full canonical read dùng chung budget | UI view DB8s/client10s; legacy no-view full read60s. Full packet giữ details/limits/acceptance, không biến truncated thành complete. |

Resume thêm đúng hai bản sửa có RED→GREEN: generic Retry-After/forwarding và SQL timestamp tie-break. Không đổi dependencies, models, keys, call caps, RBAC hoặc completion gates. Chronology/detail page tests bổ sung ở cùng seam hiện có.

## C. Performance MAIN

Nguồn: [main-api.json](main-api.json), [tail-analysis.json](tail-analysis.json), [main-browser.json](main-browser.json). 21 authenticated reads/scenario, gồm1mẫu đầu và20warm, 6scenarios =126requests. Mẫu đầu **không được gọi là cold OS/cache**; không flush/restart để tạo cold giả. Percentile nearest-rank trên20warm; sample p99 là max, chưa đại diện production tail.

| Scenario | Warm n | p50 ms | sample p95 ms | sample p99/max ms | Verdict |
|---|---:|---:|---:|---:|---|
| List20 |20|316.474|1559.810|2025.522|Đạt mục tiêu p95<2s trong mẫu này|
| #397 |20|343.573|1269.991|1470.351|Đạt p95<3s|
| #379 parent/many runs |20|624.013|4987.904|5915.008|PARTIAL: chưa đạt3s|
| #391 historical |20|400.534|1631.898|2938.779|Đạt3s trong mẫu|
| #398 new demo history |20|357.854|1564.239|3857.209|Đạt p95; tail còn cao|
| #393 no telemetry |20|370.020|1564.715|4938.429|UNKNOWN đúng; tail còn cao|

API tuần tự:126HTTP200,0HTTP429,0HTTP503,0timeout. List19Tasks trả8,919B, giảm98.93% so với baseline831,889B; list latency baseline18.20s là một mẫu, không phải baseline p95.

MAIN UI navigation: #379939ms, #391890ms, #3974503ms, #398917ms; hover39.8ms. Inspector typed output1897ms gồm lazy HTTP, không được coi là đạt loaded-panel<300ms. Command Center→Studio DOM~8.94s gồm page entry. 41Observer responses:31HTTP200/10intentional429,0unexpected503; UI phục hồi. Một long task85ms,1245DOM nodes, heap chưa GC~104.9MB. Không khẳng định không có freeze trên mọi máy.

Trace tail #379 request `9f53f252-85d6-4351-8762-79fd229301c9`:5915ms total,5882ms Rails bridge,790ms Gateway,349ms Observer. Request `a8013a4d-1f03-4b41-b122-455a0040ef25`:4988ms total,4893ms Gateway,349ms Observer. Phần chậm nằm cả ngoài Gateway handler timing lẫn ngoài Observer. **Queue wait/auth/audit/transport/scheduler chưa được instrument riêng**, không gọi phần trừ còn lại là pure queue time hoặc kết luận chắc CPU/database là nguyên nhân.

Lượt3tab đầu không tải được #391 trong20s; không bỏ qua failure này khi đánh giá reliability. Một lượt tiếp theo vào đủ3tabs và qua301s hidden emulation nhưng explicit refresh sau restore timeout15s. [stress-prior-failures.json](stress-prior-failures.json) giữ cả hai failures; harness cũ chưa lưu request arrays nên không dựng lại số từ trí nhớ. Bài cuối lưu cả dữ liệu lỗi và controlled visibility. Chưa có căn cứ giảm admission protection hoặc tăng concurrency. 429/latency multi-tab vẫn là mục cần theo dõi, không đánh FULL PASS chỉ vì503 trở thành429.

## D. Implementation và runtime

Branch `codex/agent-studio-v2-stabilization`; starting HEAD `a41b1233cef4f09d67fa5f1dc73479aef7927905`. Commit triển khai `6dc86ed86dde25ea6fd71a174f28398b7d949c5c`; [FINAL_COMMIT.txt](FINAL_COMMIT.txt) lưu tham chiếu commit báo cáo. Không push/merge branch trong phiên này.

| Thành phần | MAIN immutable image |
|---|---|
| Core | `sha256:d0bdd4d82bf06394704b299cca9edc5619e52f65b47f5e815304e607a2b1d651` |
| Gateway | `sha256:6edeea411e079bb8b2cb8242b4a79673cd74734943536e965d69bbbfbd61cef0` |
| Telegram (giữ nguyên) | `sha256:035d9bf662ff92b8783ccb0a3cb94b5e03d0458b4b8abf34fc6e42c862199146` |
| n8n (giữ nguyên) | `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269` |

API giữ route/signed bridge; `view=list`, `view=graph`, `view=details&section=...&offset=...&limit=25`; tối đa50/page. Source window tối đa50runs/200events mỗi run được ghi rõ, Run Details giữ trace riêng. Private read-only metadata endpoint validate selectors/bounds, wildcard escape và Native project/task visibility. Access denied không fallback sang dữ liệu rộng hơn.

[protected-source-check.json](protected-source-check.json):181/193baseline sources unchanged,12intentional changes đúng whitelist,0unexpected; source mới cũng được pin/parity. Parity10Core+6Gateway files đã đối chiếu trong [final-state.json](final-state.json); build JS SHA256 `da7d6a478f24213a21b8d53c7b6783f9b4bb418508ff0b6aa27be1c495823c6c`. [resume-qualification.json](resume-qualification.json) pin đúng sourcehashes trước rollout; release read-back xác nhận exact images và không DB restore. Không sửa runtime/business data để ép kết quả test.

## E. E2E thật Task #398

Đúng1demo đã được Owner duyệt, catalog giữ14/14. Planning `76f13288-6055-400b-a615-e3f7600a3344` SUCCEEDED/PUBLISHED, BA+PM2generate calls. Delivery `de391b2f-e5f2-4bc3-be10-54ab11d73099` SUCCEEDED: Dev12/Reviewer1/QA5 generate calls, không resume/replay. [demo-final.json](demo-final.json), [demo-tests.json](demo-tests.json), [plan-provider-receipts.json](plan-provider-receipts.json).

JUnit thực64tests,0failure/error/skip,14.008s ngày06/11. Commit `7ceac4e6b2b9103b18e1a8be37e15f3c05b8de70`; [PR #15](https://github.com/Luim3141/mini-task-manager/pull/15) OPEN, chỉ+17lines `tests/test_health_regression.py`, POST/PUT/DELETE/PATCH `/healthz`405 và task list không đổi. Base feature branch `codex/openclaw-feedback-d8b7006b5cff1bc4`, không phải main/deployment.

Live browser06/11 thật:117samples Dev/Reviewer và37samples QA trong live-watch398 reports/screenshots. Ngày12/11 chỉ đọc history/receipts và terminal/current state; **không gọi đó là quan sát RUNNING live mới**. BA/PM history/receipts có bằng chứng, không chụp được live RUNNING BA/PM trước khi kết thúc. Model requested luôn `gemini-3.5-flash-lite`; BA/PM receipts có exact resolved provider version;18proxy delivery receipts không persist resolved version, ghi nhận coverage gap này thay vì khẳng định đã kiểm version từng call.

Native hiện v10 READY FOR RELEASE, acceptance AWAITING_OWNER_APPROVAL; runtime COMPLETED không bằng Owner DONE. Notification candidates chỉ AWAITING_APPROVAL/PR_CREATED, không TASK_COMPLETED. Parent379 hiện có Native relationship thật; không suy diễn chỉ từ input. Không Task399, không tăng15, không tự approve/merge/deploy PR15.

## F. Kiểm thử và phạm vi bằng chứng

| Lớp | Kết quả thực tế | Giới hạn |
|---|---|---|
| Resume Node model/request |16PASS|Ordering, retry/status/header/cancellation; không phải MAIN UI|
| Resume immutable Gateway |55PASS|Observer/read path/runtime/catalog/notification contracts; network disabled, không inference|
| Resume immutable Core Ruby |1test/10assertions PASS|Admission slots, error release, Retry-After forwarding|
| Prior final Gateway |98tests,2skips,0fail|Source không đổi ngoài resume delta; không cộng suite overlap thành unique tổng|
| Native/Core isolated PG restore |3tests/12assertions PASS|ACL/batch/list wildcard; không gọi là MAIN data write test|
| Puma HTTP isolated callback |Before4x503; after2x200+2x429|4threads; no MAIN data, same callback chain component|
| Fixture browser |10groups PASS|403stop/clear, explicit recovery, status no-relayout, runs expand, history, cleanup; fixture có nhãn|
| MAIN authenticated browser |10checks PASS|CommandCenter entry, tasks, UNKNOWN, Native popup, RunDetails return, history/reload/projects/4widths|
| MAIN intentional faults |4checks PASS|Maintenance503 báo đúng, exact config restore, same-session recovery, offline finite error/recovery|
| MAIN performance |126/126HTTP200|Tuần tự; không suy thành mọi load profile đều ổn|

403/timeouts có unit/fixture coverage và Native ACL read smoke, không sửa quyền tài khoản MAIN chỉ để test. Không làm destructive stress hoặc thay production API response bằng fixtures để tính PASS. Viewport widths1440/1280/768/390; mobile touch và3tab visibility có artifact riêng. [final-interactions.json](final-interactions.json):7checks PASS trên MAIN, mobile390 touch pan/zoom/Inspector/Explorer và không overflow. Burst4requests:200/200 trong739/590ms,429/429 trong47/45ms với Retry-After1;0HTTP503. Một lượt harness mobile ban đầu dùng nhãn welcome-only trên Task đã mở nên locator timeout; sửa locator thành Ẩn/Mở explorer hiện có rồi PASS, không sửa app.

## G. Compatibility và toàn vẹn

[final-state.json](final-state.json) kiểm12invariants: Native project5 toàn rows; old project6 fields<=397; roles/members/member_roles/workflows/statuses/users/password hashes; settings/secret file fingerprints; n8n workflows/credentials; tất cả Telegram table hashes; unrelated bot/n8n containers; original Gateway row prefixes+config; idle/OFF; source parity; #398 stages/acceptance/no false completion.

Gateway full `observer_task_progress` thật qua bearer/Native ACL đọc được stages, run details, notifications và acceptance #398. Không gửi Telegram test spam, không đổi pairing/User ID/memory/outbox. Bot healthy, n8n readiness200;16workflow hashes giữ nguyên. Supervisor heartbeat tươi, active_run=null, OFF/queue0. Provider receipts620 giữ nguyên trong resume; không phát sinh inference để đo performance. Không đổi Gemini model/key/caps, command policies hoặc completion gates.

## H. Rollback và release safety

Resume đã hai lần bị strict Demo release read-back chặn khi loopback WSL18791 không reachable trong lúc worker stopped; operator tự rollback, không restoreDB. Đọc lại runtime sau rollback, giữ WSL distro sống bằng read-only sleep rồi rollout exact qualified images thành công; không sửa hoặc bỏ gate. Chỉ xác nhận quan sát transport/read-back, chưa kết luận đầy đủ nguyên nhân WSL lifecycle.

Safe pre-resume images (đã có ceiling14 và toàn bộ records mới):

- Core `sha256:3b0200f13bd3d401370fb45c08c1421c7722a91d990cc390b9f765b04187e3ac`.
- Gateway `sha256:2cbbe095c52883b36aa9225488fcb067def39e22bd702564e1b589087bf4bfa5`.

Nếu rollback cần thiết: bảo đảm OFF/active0, pin exact pair trên bằng operator hiện hành, giữ bind mounts/config/volumes; kiểm health, Native read-back, parity theo source tương ứng và #398/ceiling14. Không dùng baseline cap13, không restore database cũ, không xóa catalog để giảm14. Backup riêng có đường dẫn trong deployment artifact private; chưa thực thi rollback sau khi resume đã nghiệm thu. Giữ image/source hashes, không dựa tag mutable. Không đụng bot/n8n.

## I. Remaining Issues / trạng thái nghiệm thu

- **DONE:** Các bản sửa trên đã build/qualified/deploy; Retry-After, attempt ordering, UI/full Telegram deadline separation, admission component, navigation/Explorer, canonical runtime projection và data preservation có bằng chứng.
- **PARTIAL:** #379 warm sample p95~4.99s>3s; #398/#393 tail vài giây, inspector lazy~1.90s; multi-tab first load từng timeout và rapid navigation10/41busy responses. Chưa chứng minh polling/admission không ảnh hưởng mọi tab. Cần instrument queue/admission/auth/audit/transport riêng trước khi sửa scheduling/performance sâu hơn; giữ protection hiện có.
- **AWAITING_OWNER_APPROVAL:** Chỉ business acceptance #398/PR15; không phải blocker để bàn giao kỹ thuật.
- **NOT TESTED:** OS-native tab hide/mobile hardware gestures, cold-cache controlled benchmark, production-scale p99/load, long-duration leak soak; resolved provider version toàn bộ18proxycalls chưa được persist.
- **BLOCKED:** Không có blocker credential/model/approval cho các kiểm thử kỹ thuật đã thực hiện. Performance gate chưa đóng là kết quả chưa đạt, không đổi thành FULL PASS.

Các thử nghiệm headless document.visibilityState là emulation rõ ràng, không bằng OS visibility. Không tăng concurrency/đổi admission khi chưa có trace chứng minh nguyên nhân. Performance/scheduling còn mở và cần kiểm chứng riêng, chưa có bản sửa được chứng minh cho tail/multi-tab. Báo cáo này lưu các failure cùng pass, không rerun percentile để chọn số đẹp.

### Số đo detail UI

[main-detail-measurements.json](main-detail-measurements.json) trích request timings của cùng MAIN browser run:7event pages đều200, TTFB289–1008ms; runs page200/~346ms; overview200/~311ms và1busy429. Đây là network response-start, không phải full paint/end-to-end panel latency. Artifact typed output đã được đối chiếu ở Inspector và full canonical packet; đo riêng artifact page ở lượt bổ sung dưới đây, không dùng overview timing làm số đo endpoint artifact page. Graph visible/task switching đo bằng DOM data-task, chưa có instrumentation riêng cho time-to-first-interactive graph. Refresh/no-relayout có fixture và MAIN controls, không gán một percentile chưa đo.

### Phạm vi Git / static check

Chỉ stage whitelist source/tests/docs/evidence của stabilization; các file untracked không liên quan đã có sẵn vẫn giữ nguyên, không add-all/stash/reset/clean. Một số module nguồn hiện hành trước đó chưa tracked nên commit ghi snapshot đầy đủ của đúng module chạm tới; đây không phải chứng nhận clean checkout đã chứa mọi nền tảng untracked của workspace. Không nhập toàn bộ nền tảng đó vào commit này. Không có dependency mới. Secret scan đối chiếu giá trị private hiện hành và token/key patterns không tìm thấy secret trong whitelist.

Default git diff --check báo2blank lines có trailing whitespace ở execution.html.erb đã có trong source/image hiện hành; không sửa cosmetic rồi rebuild MAIN. `git -c core.whitespace=-blank-at-eol diff --cached --check` PASS. Không claim default whitespace check hoàn toàn sạch.

### Kiểm tra3tab cuối (giữ nguyên hai failures trước)

[stress-uat.json](stress-uat.json), [stress-summary.json](stress-summary.json):3tabs MAIN #398/#391/#397 load và restore PASS ở lượt cuối. Headless visibility emulation301.062s,0reads từ tab398 trong lúc hidden; hai tabs còn lại tiếp tục polling. Tổng59requests:49HTTP200/10intentional429/0HTTP503,0page errors. Restore đọc đúng398. Đây không phải OS-native backgrounding và không chứng minh mọi lần mở3tabs thành công; hai failures trước vẫn giữ ở stress-prior-failures.json.

Sau forced GC, heap tab39833,036,716→33,582,712B (+545,996B/~1.65%); DOM nodes3213→3213, event listeners608→608. Không thấy tăng DOM/listener trong cửa sổ5phút này; chưa kết luận không leak dài hạn. Snapshot CPU/RAM là sample tức thời, không gán khác biệt pre/post thành benchmark do pre-release gồm startup.

### Chốt MAIN read-back

[read-details-uat.json](read-details-uat.json): artifact page thật #398 có typed test evidence, click→visible973.0ms; explicit refresh→graph HTTP200649.6ms, giữ đúng Task. Không response interception. [final-service-health.json](final-service-health.json):Core/Gateway/bot healthy, n8n readiness200, Supervisor heartbeat~7s, OFF/active_run=null, provider receipts620. [pr15-final.json](pr15-final.json) đọc lại GitHub PR15OPEN, mergedAt=null, exact head7ceac4e6. [final-state.json](final-state.json) chạy lại sau tất cả UAT:12checksTRUE, Native/config/Telegram/n8n/original Gateway prefixes giữ nguyên,10+6files parity, #398 vẫn chờ Owner.

[final-resources.json](final-resources.json): qldapm-openproject-web-1: CPU19.68%, RAM1.797GiB / 11.54GiB; qldapm-ai-gateway-1: CPU60.51%, RAM243.9MiB / 384MiB. Snapshot tức thời, không phải CPU/memory percentile hay matched-load before/after. Trong một sample trước đó Gateway~109.7%CPU (nhiều hơn một core), cần xét saturation khi điều tra tail; chưa đủ chứng minh root cause.

### Test gates cuối

| Gate | Verdict | Phạm vi |
|---|---|---|
| P0 Explorer/navigation trắng | PASS trong MAIN/fixture đã chạy | Entry/back/forward/reload/native/run links |
| P0 loading hữu hạn | PASS single-tab/fault; PARTIAL multi-tab | Hai timeouts trước, lượt3tab cuối PASS; không chứng nhận mọi load profile |
| P0 unexpected503 callback repro | PASS component + sampled MAIN | Old4x503→new2x200+2x429;126sequential+59stress+4burst không503 |
| P0 Retry-After/ACL fail-closed | PASS targeted contracts/clone/read smoke | Không sửa MAIN permissions để tạo test |
| P1 attempts/runtime/no unnecessary layout | PASS tests + recorded runtime | Actual live39806/11 và resume history; fixtures ghi nhãn |
| P1 latency/scheduling/reliability | PARTIAL | #379p954.99s, busy retries và prior3tabfailures chưa giải quyết triệt để |
| P1 bounded error recovery | PASS đơn tab; PARTIAL độ ổn định nhiều tab | Fault/offline phục hồi; lượt3tab cuối restorePASS |
| Compatibility/data/gates/ceiling14 | PASS checks hiện có | Protected hashes/full Telegram query; không có send/inference mới |
| Owner completion398 | AWAITING_OWNER_APPROVAL | Không tự DONE/approve/merge |
| OS visibility/hardware/long soak/production p99 | NOT TESTED | Headless emulation và20warm samples không thay thế các mục này |

Bàn giao kỹ thuật và commit đã hoàn tất trong phạm vi đo được; **performance/reliability gate vẫn mở**. Không có blocker cần key/model/ceiling approval mới. Việc xử lý tail/multi-tab tiếp theo cần trace phân đoạn riêng và tái hiện có request IDs, không tăng load hoặc thay gate để ép PASS.

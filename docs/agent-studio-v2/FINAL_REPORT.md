# Bàn giao Agent Studio V2 — MAIN local

**Đã triển khai và kiểm chứng trong phạm vi V2, ngày06/11/2026.** Một Codex agent thực hiện; không GUI computer-use, không tạo/replay coding Task hoặc gọi thêm model.

Mở **AI Command Center → Agent Studio → chọn Task**. [Task397](http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai/observer?task_id=397), [Command Center](http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai). Route Observer cũ tiếp tục hoạt động, có back link, deep link và reload. Source commit **`7461c66`**, branch `codex/agent-studio-v2`; checkpoint hardening V1 trước đó `52fa710`. Không push/merge repository này.

## V1 và thay đổi thực tế

V1 của route Agent Studio không import/mount React Flow: vanilla DOM render cards, không graph viewport/dependency edges hoặc inspector có cấu trúc, JSON xuất hiện trực tiếp. Chỉ đổi CSS không giải quyết được các vấn đề này. [SOURCE_PROOF.md](SOURCE_PROOF.md) chỉ rõ từng file/component mới và nguồn nghiên cứu.

V2 dùng React Flow12.10.1, Dagre1.1.8, React19.2.0, esbuild0.25.12, package lock có integrity. `Studio`, `AgentNode`, `EvidenceEdge`, `Inspector`, typed `Output`, `Events`, `ArtifactList` được bundle local trong Core. Không CDN, app/port mới, Supervisor hoặc backend Observer mới. CSS scope theo island, dark/light tokens, container queries, reduced motion và native select override. Lifecycle Turbo/DOM removal hủy React/timers/requests; ResizeObserver được cleanup.

Graph đọc stage từ canonical Task và edges từ actual run monitor. Arrowheads có hướng; Dagre tự layout LR desktop/TB mobile. Không gán tọa độ theo Task ID. Stage expansion giữ attempts, checkpoint và run history; ATTEMPT_ORDER không bị gọi nhầm là handoff/resume thành công. Animation chỉ biểu thị destination stage RUNNING với source freshness FRESH, không mô phỏng message truyền liên tục. Tooltip ghi rõ contract dependency và không tạo timestamp handoff khi chưa có event.

Hover/click không gọi Gemini. Inspector trình bày files/commit, Review verdict/revision/findings, QA command/exit/report, artifacts/GitHub publication receipt, errors/checkpoint và Owner gates. JSON chỉ ở Technical Details. PR receipt lịch sử không được gọi là current PR/deployment state. Task397 có Dev/Reviewer/QA, không thêm BA/PM của parent379.

Actual Main UAT phát hiện và đã sửa hai lỗi integration: tab handler cũ chặn anchor Studio vì `preventDefault()` trước khi kiểm `data-tab`; CSS native làm dropdown Project chữ quá nhạt. Navigation handler nay chỉ bắt `[data-tab]`, palette select chỉ override bên trong Studio.

## API và realtime

Giữ Rails route `/projects/:project_id/qldapm-ai/observer`, signed bridge và Native ACL. GET JSON chọn `observer_active`, `observer_task_progress` hoặc `observer_run_details`; các actions Gateway hiện hành không sửa. Chỉ mở validation controller cho list limit1..50, mặc định20. ID/title search, Recent/Active/Blocked/Completed và load more20→40→50 có giới hạn; đổi Task clear state, abort request và generation guard.

Không thấy Observer/Gateway event stream hiện hành. Rails bridge đồng bộ; không giữ Puma threads bằng một loop polling giả SSE. V2 dùng **adaptive bounded polling**, không tuyên bố streaming:3s cho RUNNING/FRESH,15s terminal, backoff tối đa60s, timeout90s; không overlap, tạm dừng tabẩn. Canonical source timestamp/TTL120s quyết định freshness, không dùng lần GET thành công để ghi LIVE. STALE/UNKNOWN không pulse. Viewport/selection được giữ qua refresh.

Read bounds hiện hành: tối đa50runs/Task,300timeline events,100artifacts; list scan tối đa200run gần nhất. Lịch sử cũ ngoài giới hạn không được gọi là đầy đủ vô hạn.

## Runtime thật và test fixture

**Runtime thật:** Main Owner18 đăng nhập bằng tài khoản local/2FA hiện hành; Task391 và397 lấy qua signed Observer, đối chiếu canonical JSON. Task397: business DONE, acceptance COMPLETED,3stages,1coding run,51events; actual Owner journal1251 và các gates hiện hành. Không thay business status để làm đẹp graph. Task391 giữ trạng thái/checkpoint theo nguồn thật.

**Fixtures:** RUNNING/BLOCKED/FAILED/UNKNOWN/STALE, reduced motion, HTTP503, multiple attempts và lifecycle được inject trong isolated browser ở domain test; ảnh luôn có banner TEST FIXTURE. Đây không phải một execution mới của Task397. Không tạo Task mới đang chạy chỉ để quay demo, không bật lại Task391/397.

## Kết quả kiểm thử

| Nhóm | Kết quả thực chạy | Bằng chứng |
|---|---|---|
| Adapter/boundary/layout |5tests PASS: real stage/edge mapping, Dagre không overlap, attempts, freshness/animation, malformed input, URL/summary | `core/agent-studio-v2/model.test.mjs` |
| Frontend production build |PASS, React Flow/Dagre inputs thật, local JS/CSS + manifest/license | `core/agent-studio-v2/build-proof.json` |
| Browser fixtures |17nhóm checks PASS,0uncaught errors | [fixture-browser.json](fixture-browser.json) |
| Authenticated MAIN final |13checks PASS,0Studio uncaught errors,0business writes/model calls | [main-uat.json](main-uat.json) |
| Gateway/Observer/notifications/ACL |53tests PASS | [REGRESSION_RESULTS.json](REGRESSION_RESULTS.json) |
| Integrity/workflow/runtime/supervisor/trace |28tests PASS | `REGRESSION_RESULTS.json` |
| Telegram |54pytest +16subtests PASS,1host SDK deprecation warning | `REGRESSION_RESULTS.json` |
| Existing Command Center JS |3Node VM suites PASS: filters/inspector escaping/transport/CSRF/reconnect/cleanup | `REGRESSION_RESULTS.json` |
| Immutable final Core |Controller và hai ERB templates compile PASS;7serving source hashes đúng image | [verification.json](verification.json) |
| Unrelated code/state |187source cũ unchanged; protected Gateway tables/config exact hashes unchanged | [unrelated-source-parity.json](unrelated-source-parity.json), `verification.json` |
| Telegram/n8n preservation |10SQLite tables, config/secrets và container identity/start time giữ hash;17workflows/6credentials n8n giữ nguyên | [preservation-after.json](preservation-after.json) |

Không cộng fixtures/subtests/các suite overlap thành một con số unique E2E. Legacy tests mở production Store/queues không được chạy để làm regression; lần import một legacy suite lỗi module path chưa thực thi test, không sửa đường dẫn để kích hoạt nó.

## Checklist18tiêu chí bắt buộc

| # | Tiêu chí | Trạng thái và chứng cứ |
|---|---|---|
|1|Mở từ Command Center|PASS · actual click navigation |
|2|Interactive graph library thật|PASS · production ReactFlow mount,3nodes/2edges |
|3|Directed arrows|PASS · monitor dependencies/marker-end, browser |
|4|Verified active animation|PASS implementation/fixtures · FRESH RUNNING gate; chưa new real-running execution |
|5|Agent hover có work/status/result/evidence|PASS · real Main hover + screenshot |
|6|Click inspector|PASS · real Dev/Reviewer/QA, keyboard fixture |
|7|Raw JSON không là nội dung chính|PASS · `pre:visible` bằng0 trước khi mở Technical Details |
|8|UI đọc được, không overflow|PASS · four widths, native palette, bounds và visual review |
|9|Timeline/artifacts|PASS ·51events/4artifacts real397, typed inspector |
|10|Observer thật|PASS · canonical read-back391/397 |
|11|Update không reload page|PASS · refresh/state fixtures và Main viewport/selection giữ nguyên |
|12|Freshness/stale|PASS · source TTL,503/recovery/stale fixtures, Main historicalSTALE |
|13|Không Subtasks|PASS · read-only UI, protected state unchanged |
|14|Không đổi Supervisor/Gateway không cần thiết|PASS · Gateway image và all Python hashes giữ nguyên |
|15|Telegram/n8n hoạt động|PASS · bot POLLING/CONNECTED,5SENT; unchanged n8n containers/config |
|16|Navigation test|PASS · Command Center→Studio→Task→back→deep link→reload |
|17|MAIN screenshot QA|PASS ·1440/1280/768/390 đã mở kiểm tra ảnh |
|18|Regression không có critical mới đã biết|PASS trong phạm vi suite/UAT trên; giới hạn bên dưới |

## Screenshots đã kiểm tra

Ảnh **MAIN thật, image cuối**, khác với fixtures:

- [Command Center entry point](main-command-center.png).
- [Desktop1440](main397-desktop.png), [laptop1280](main397-laptop.png), [tablet768](main397-tablet.png), [mobile390](main397-mobile.png).
- [Agent hover/inspector](main397-hover-inspector.png), [Review evidence](main397-review-evidence.png), [edge hover](main397-edge-hover.png), [recorded attempt](main397-attempts.png), [Task391](main391-history.png).

Interaction viewports là1440×1100/1280×1000/768×1024/390×844. OpenProject cuộn trong pane riêng; full-content screenshots tạm tăng chiều cao ở cùng chiều rộng để không cắt phần graph. Inspector/timeline có vùng cuộn riêng. Đã kiểm graph đủ nodes, arrowheads, layout/contrast và không horizontal overflow; không gọi một ảnh fixture là Main execution.

[RUNNING fixture](fixture-running.png), [BLOCKED fixture](fixture-blocked.png), [FAILED fixture](fixture-failed.png), [STALE fixture](fixture-stale.png), [multiple-attempt fixture](fixture-multiple-attempts.png) đều có nhãn TEST FIXTURE. Dark/light được kiểm riêng.

## Images, integrity và rollback

| Thành phần | Image đang phục vụ |
|---|---|
|Core V2|`sha256:784a641f79cdbb6e82fcccfd2b7abd800b0deeb555509fdb187dbbeace76694d`|
|Gateway giữ nguyên|`sha256:dbd6fca4c8f8efc559b7b266eb569d64d43af348ec2c180dbcc084d6be4e7381`|
|Telegram giữ nguyên|`sha256:035d9bf662ff92b8783ccb0a3cb94b5e03d0458b4b8abf34fc6e42c862199146`|
|n8n giữ nguyên|`sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`|

[Final manifest](candidate-v8/manifest.json), [deployment](candidate-v8/deployment.json), [qualification](qualification.json), [original baseline](baseline.json), [verification](verification.json), [final runtime/health](final-runtime.json). Build chỉ COPY7overlay files, dùng immutable base và source guard. Gateway giữ exact image, không thêm instance; Telegram/n8n không restart. Mode OFF/queue0 cuối, không inference. Bot POLLING/CONNECTED; n8n `/healthz` HTTP200 (container này không có Docker healthcheck). Model/key/pairing/memory/outbox/notification logic/completion gates giữ nguyên. Operator `demo_release` là read-back của release cũ, không phải deploy mini-task-manager trong lượt V2.

Rollout có image-only Compose parity, worker fence, SQLite integrity backups và rollback image/config nếu lỗi trước mở maintenance. Không tự restore business DB. Backup của bước cuối: `%LOCALAPPDATA%\QLDAPM\openproject-ai\operator\integration-pair-ea6e3d78a3b249cf83d52687d86c9901`; bước trước trong deployment manifests.

Muốn rollback sau bàn giao: giữ OFF/queue0, fence worker, dùng Compose prefix trong manifest; restore Core image cùng `CORE_IMAGE`/`ui-bridge.yml`/image-lock từ private backup của mốc cần quay lại, rồi `up -d --no-deps web` và read-back health/source. V1 gốc trước V2 là Core `sha256:bcbccefa237906fa7a0c8867ff16d6d826c025ce81748b9fb3f6a1399601dc27`, backup chỉ ở [deployment bước đầu](candidate-v6/deployment.json). Giữ Gateway image trên. Không restore DB hoặc xóa volume để rollback UI. Hướng dẫn này không có nghĩa đã thực hiện một destructive rollback sau khi mở MAIN.

## Giới hạn còn lại

- RUNNING/BLOCKED/FAILED mới chỉ qualification bằng controlled fixtures; real UAT dùng historical391/completed397. Chưa thực hiện một coding execution mới, benchmark multi-user/large DAG, Windows reboot hoặc Safari/Firefox. Không phát sinh yêu cầu trả phí.
- Đây là polling, không SSE; giới hạn latency và history như trên. Historical completed Task vẫn có source freshness STALE nếu telemetry đã cũ; không giả LIVE.
- Có2HAL authentication errors từ native Angular/login trước khi vào Studio; `main-uat.json` giữ stack, Studio phase0uncaught errors và auth/ACL thực PASS. Không tuyên bố đã sửa toàn bộ native auth; không đổi credentials/MFA. Một cold Rails runner timeout120s trước đăng nhập, rerun với300s đã PASS.
- Không merge/deploy mini-task-manager, sửa Telegram/n8n/Gemini, thay Supervisor hoặc completion gates trong V2. Những phần frozen/legacy ngoài đặc tả không được tự đánh dấu hoàn thành.

# Stabilization — kế hoạch thực hiện một agent

## Baseline và repro

HEAD a41b123 (docs),7461c66 (React implementation),52fa710 (hardening). Images khớp handoff; protected config/DB baseline mới lưu trước thay đổi. `probe.py` RED: list5 và parent379 timeout15s;397~9s/40KB. `browser_probe.py` RED: Explorer click không focus,379không hiện25s. Profile read-only:37916monitors,18Native calls~3.56s,72SQLite connects/132executes~2.25s;397warm~0.8–1.7s nên load/concurrency phải được phân biệt, không quy mọi request đều9s. Chưa gán nguyên nhân lịch sử503 nếu không có correlation.

## Thứ tự sửa và phạm vi

1. Bổ sung diagnostics metadata, correlation/timings và probe phân loại503/auth/maintenance; không log bearer/body.
2. `gateway/agent_observer.py` và module read scope: request-scoped read-only SQLite connection, Native metadata batch có Native ACL thật; không global cache quyền. List metadata không hydrate toàn bộ Tasks/health integrations. Graph summary có edges từ monitor và không tải details trước render. Existing default canonical calls của Telegram giữ contract/gates.
3. Rails read-only metadata endpoint trong `gates_api.rb` + service nhỏ; native batch fallback chỉ404, không fallback khi403. Rails bridge observer-specific timeout/error classification/Server-Timing, không đổi mutation semantics.
4. Read detail sections/pagination rõ truncation, related parent link có Native evidence; full output chỉ fetch khi inspector/Technical Details được mở. Unit/contract RED→GREEN cho ACL/readonly/legacy/partial/history/limits.
5. React: request scheduler với loading/refresh/error/timeout/cancel/empty/partial states, Retry hữu hạn và dừng403/404; snapshot summary hiện trước details; giữ generation/viewport, layout cache theo topology (Dagre không chạy tick5s), memo Agent nodes, timeline page nhỏ; Explorer click focus/scroll thật và Work Package/Run Details return context. Frontend profiles trước/sau, không remount graph.
6. Source candidate, immutable Core/Gateway tests, bounded authenticated UI matrix1/3tabs, rapid switches, stale response,503/timeouts/restart/5minhidden/network recovery, Project/back/forward, mobile vàlarge/history/legacy; record DOM/longtasks/heap/latency samples và trạng thái từng trường hợp, không ép p99 từ ít samples.
7. Owner đã duyệt catalog13→14 và1demo test HTTP methods `/healthz`, không đổi app/merge/deploy. Thực hiện qua runner/gates hiện hành sau read path ổn; đối chiếu runtime→Observer→UI từ queued tới terminal. Không sửa391/397; runtime terminal không tự là DONE. Nếu providerblock thì báoPARTIAL, không fixturethaylive.
8. Deploy final guarded images khi qualified; preserve volumes/config/bot/n8n/qdrant/checkpoints, source parity và hashprefix cũ. Báo cáo mới trong thư mục này, không overwrite handoff cũ; architecture cập nhật cùng change.

## Safety / rollback

Native ACL luôn current, không cache cross-user/project; readonly query_only ở Observer scope. Không migration destructive. Backups/config/image pins theo paired release helper; chỉ images có thay đổi được build/deploy. Đã có Owner approval duy nhất cho ceiling14vàdemo; chưa tự approve final Native DONE. Runtime rows mới được giữ; integrity check dùng prefix cũ + whitelist append, không sửa dữ liệu để ép hash.

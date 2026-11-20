# Agent Studio V2 — design và triển khai

Đặc tả Owner 06/11/2026 là phạm vi đã duyệt. Một agent thực hiện tuần tự; không tạo coding Task hay gọi model. Baseline V1 hardening được checkpoint tại `52fa710`.

## Thiết kế

React island dùng React Flow + Dagre, bundle local bằng esbuild; Rails route, Native ACL và signed Observer bridge hiện hữu. Dashboard tối mặc định, theme sáng tùy chọn; typography hệ thống, cyan cho hoạt động, green cho hoàn thành, màu kèm text/icon. Graph trung tâm, task browser bên trái, inspector bên phải và timeline phía dưới. Mobile chuyển browser/inspector thành các panel nối tiếp, graph vẫn pan/zoom độc lập.

Edges lấy từ `observer_run_details.edges` và node dependencies thực tế; không suy diễn chuỗi role từ thứ tự card. Dependency contract khác handoff event: chỉ hiển thị timestamp khi event nguồn chứng minh. BA/PM parent không thêm vào coding Task. Stage expand tạo attempts từ các run monitor, quan hệ thứ tự attempt được ghi rõ không phải handoff. JSON sau Technical Details.

Không thấy SSE trong Observer/Gateway route; Rails signed bridge hiện request/response đồng bộ. Không giữ Puma thread bằng vòng polling server giả SSE. Adaptive polling tuần tự 3s khi runtime fresh RUNNING, 15s terminal, backoff tối đa60s, dừng tabẩn; request AbortController, task-generation guard và source TTL120s. Transport khỏe không đồng nghĩa runtime FRESH. Viewport và selection giữ qua snapshot refresh; task đổi xóa state cũ ngay.

## Các bước và kiểm chứng

1. Pin baseline image/source/protected state. Đọc real391/397 và monitor schema; kiểm tra parity V1.
2. `core/agent-studio-v2/`: package lock, adapter + tests cho mapping/unknown/stale/attempt/edge semantics, React components và CSS scope. Build JS/CSS vào `core/overlay/public/qldapm-agent-studio-v2/`; không CDN.
3. Replace observer view bằng mount root và local asset tags, cleanup Turbo/DOM lifecycle. Command Center link chính thức + back link và task URL. Controller limit1..50 cho load-more đã được canonical API hỗ trợ; giữ ACL.
4. Build + unit tests. Fixture browser states có nhãn TEST FIXTURE; không thêm fixture route sản xuất.
5. Core-only source patch bằng paired release guard hiện hữu (Gateway source không đổi), backup/rollback exact images/config, queueOFF/0; giữ Telegram/n8n untouched. Chứng minh source/image parity.
6. Headless authenticated Main: click Command Center→Studio→Task→back; real391/397, graph controls/hover/inspector/attempts/timeline/ACL, transientfailure/recovery, responsive1440/1280/768/390 và screenshot QA. Fixture chạy trong browser intercept, ghi rõ không phải execution thật.
7. Regression Observer/native gates và pin protected config/runtime/bot/n8n. Ghi báo cáo PASS/NOT DONE theo bằng chứng; không tự gọi một fixture RUNNING là real-running UAT.

## Rollback

Pin Core/Gateway immutable image trước release; operator có rollback image/env theo manifest, không restore DB tự động. Không migration/business mutation. Source commit V1 còn nguyên; revert V2 view/assets/nav nếu cần.

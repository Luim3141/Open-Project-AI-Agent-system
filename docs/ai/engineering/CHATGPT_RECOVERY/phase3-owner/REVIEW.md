# Phase3 independent source review

Snapshot: 2026-11-02; review diễn ra đồng thời với fixes. Không deploy, không tạo task, không gọi provider, không Computer Use. Baseline MAIN Gateway8359/Corea6; Git HEAD không đại diện source đang chạy. Áp dụng ai-tech-team và ponytail-review; chỉ ghi tài liệu này.

Thay đổi cung cấp authenticated JSON command/read-back, durable owner receipts và polling các vùng HTML do Rails render, cùng persisted agent telemetry. Gateway vẫn là scheduler duy nhất. OWNER UAT chưa thực hiện.

## Findings

Không phát hiện Critical trong phạm vi đã đọc. Các Important dưới đây đã gửi trực tiếp cho implementer trước rollout:

1. **Lost-response không thể reconcile một số mutations.** `service.py` engineering dispatch ban đầu không persist request-correlated receipt cho GitHub sync, planning, reports, schedule, notification dismiss; UI chỉ so `last_command`. Lost successful sync response khóa mọi controls mãi dù poll thành công. Node VM tái hiện `sync_unknown_lock=true;post_count=1`. Backend đã bổ sung receipts, UI đã tìm `recent_commands`; regression mới cần đi kèm source cuối.

2. **Revision conflict bị hiển thị thành thành công.** `engineering.control` trả `accepted:false`/`ENGINEERING_STATE_REVISION_CONFLICT`; controller ban đầu tạo message theo requested mode và HTTP200, JS ưu tiên message. Node VM tái hiện feedback “Đã cập nhật ... AUTO” cho rejected receipt. Implementer sửa controller HTTP409 và JS kiểm tra `accepted===false`; transport test mới PASS độc lập.

3. **Inspector gắn nhầm evidence khi responses đảo thứ tự.** Click run A rồi B, A trả sau làm render A vào modal còn header run B. Implementer thêm request-token guard cho cả success/error và `cache:no-store`. `test_run_inspector_request.js` PASS độc lập.

4. **Request UUID chưa là durable idempotency identity.** Tại thời điểm review, `engineering_*` dispatch bỏ qua `Store.begin/finish`; `command_result` chỉ chèn UUID vào document, không reserve/dedup/bind arguments. Isolated fixture: AUTO(key=same-request) → OFF(new key) → AUTO(same-request) tạo command_id mới, revision1→3 và bật lại AUTO. Implementer đã dùng `Store.begin/finish`, namespace `owner6:` và bind exact action/project/arguments; fresh authorization trước cached return. Regression AUTO/OFF/replay giữ OFF, cùng UUID khác payload bị từ chối; concurrent report một effect, pending duplicate không chạy lại và completed duplicate trả exact response. **Đã sửa và retest PASS.**

5. **Notifications không có live region.** JS liệt kê `qcc-live-notifications`, nhưng section ban đầu thiếu cả id và `data-qcc-live`; poll không thay bar sau report/schedule update. Implementer đã bổ sung hai attributes và durable dismiss form. **Source đã kiểm tra lại.**

6. **Stable modal form vẫn khóa sau reconcile.** Resolver ban đầu chỉ clear global unknown flag. Intake/schedule nằm ngoài live fragments nên giữ `qccSubmitting=true`, request UUID và disabled button sau lost response đã xác nhận. Implementer giữ original form/button/request info, unlock riêng UUID khớp ACK. **Targeted transport regression PASS.**

7. **JSON500 bị coi là outcome đã biết và cho gửi lại UUID mới.** `known=true` ban đầu được gán trước kiểm tra HTTP status; server có thể đã commit effect rồi lỗi audit/render. VM JSON500 không có durable receipt tái hiện `unknownRequest:null`, `buttonDisabled:false`, `requestIdPreserved:false`. Implementer giữ unknown/UUID cho HTTP>=500 hoặc409 không có receipt mang request_id khớp và accepted boolean. **Source đã kiểm tra, regression JSON500 PASS độc lập.**

Thêm mismatch nhỏ đã sửa: RUN ONCE chọn backend `eligible===true`; initial control revision lấy từ root dataset, tránh bỏ revision fence trước poll đầu.

## Evidence và checks thực chạy

- Đọc controller/ERB, engineering status/admit/control/auto/lifecycle/monitor, service dispatch/worker loop, GitHub journal/read-back, telemetry và tests/callers liên quan.
- `node openproject/ai/tests/test_owner_live_transport.js`: PASS lần cuối sau mọi UI fixes, gồm accepted:false, JSON500 unknown lock, recent receipt recovery và stable-modal unlock.
- `node openproject/ai/tests/test_run_inspector_request.js`: PASS, late success/error không ghi nhầm run.
- `node openproject/ai/tests/test_command_center_interactions.js`: PASS lần cuối; source vẫn không chứa các literal trạng thái giả đã bị loại trước đó.
- Venv Python: `python -m unittest discover -s tests -p test_engineering_owner_controls.py -v`, workdir `openproject/ai`, PYTHONPATH project ai: **12 tests PASS trên source cuối**, gồm same-key replay/OFF preservation, changed-payload conflict và concurrent report reservation/cache.
- Hai Node VM experiments bổ sung tái hiện lost-sync lock và accepted:false success message trước fixes.
- Isolated Python fixture tái hiện duplicate request key reactivating AUTO; không dùng runtime data.
- Chạy `engineering_telemetry.snapshot` trực tiếp trên **read-only** prechange `gateway.sqlite` qua SQLite URI `mode=ro`; không gọi setup/write. WP390/run447d4fd9-fd03-4a41-9468-09bad8629d48 nối đúng plan8751d17a-4c6c-4f5f-b00c-6e1239f5353c: Dev/Reviewer/QA dùng persisted revision/test-log/head artifacts, Native child390/project6/version2, RAG child citation, 13 provider receipts và 13 n8n ACKs. Pipeline PASS đúng artifact có thật; Reports UNKNOWN. WP389 schema cũng tương thích. Cursor1990, bounded100 events. Planning Native/RAG khác schema được giữ UNKNOWN, không gán PASS giả.
- Không thấy thêm đường XSS mới trong fragments đã đọc: ERB mặc định escape, report JSON `json_escape`, dynamic inspector escape/textContent. Telemetry mới chỉ project IDs/codes/hashes, không chứa private prompt/payload trong canary test. Đây là source review, không là penetration test toàn hệ thống.

## Verdict cuối source review

**Ship qua release qualification đã định nghĩa.** Không còn Critical/Important chưa sửa trong phạm vi source review này; #1–#7 đã có source fix và targeted regression/source read-back. Root cũng sửa parent status dạng String/Hash ở mission panel sau tái hiện fixture. Một chỗ table cũ đọc `parent['status']['name']` đã báo lại để tránh blank label với String; không ảnh hưởng mutation/authorization.

Authentication/CSRF thực Rails clone, source/image parity, queue/lease/backup/rollback và rollout do root kiểm tra riêng trước deploy. Verdict này không xác nhận MAIN đã deploy hoặc OWNER ACCEPTED. Unknown requests thiếu receipt sau process crash vẫn phải giữ fail-closed; UI recent-command lookup giới hạn10, nên outcome quá cũ/không có receipt có thể cần operator reconciliation, tuyệt đối không tự replay.

Chưa kiểm tra: physical browser interaction/Owner UAT, deployment parity hoặc mọi n8n business E2E. Rủi ro còn lại: unknown writes phải luôn giữ trạng thái không replay nếu không có receipt đủ xác nhận.

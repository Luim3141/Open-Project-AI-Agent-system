# QLDAPM — UAT đã thực thi, 2026-10-18T22:52:55.637123+07:00

Kết quả: Staging đã triển khai và kiểm chứng bản sửa UAT-01 theo đúng phê duyệt Gateway-only. Các chức năng local đã thử có kết quả UI thật; **chưa nghiệm thu live Gemini, chưa promote Main**. Hồ sơ này tiếp nối triển khai trước, không kiểm toán lại 113 task.

Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); trang lấy URL hiện tại tại [localhost:18090](http://localhost:18090). Quick Tunnel không bị restart; URL có thể đổi sau lần khởi động bình thường khác.

| Chức năng | Trạng thái | Đã hoạt động/đã thử thật | Bằng chứng và giới hạn |
|---|---|---|---|
| 18 containers và cấu hình khôi phục | PASS | Read-only Docker inspect: tất cả running, healthcheck khỏe nếu có; giữ restart policy. Chỉ Gateway đổi ID/image; 17 container còn lại giữ ID/image/StartedAt/RestartCount | final-runtime-checks.json; không fault/restart hệ thống trong UAT này |
| Login/logout/TOTP 5 vai trò | PASS | Chromium/MS Edge, account thật PM7/BA6/FE9/BE8/QA10, HTTPS và session Native API | serving-browser.json, 75 assertions; không tạo/rotate TOTP |
| Dashboard, Work Packages | PASS | UI thật và link dữ liệu Native, không chỉ HTTP200 | serving-browser.json |
| Backlog, Sprint | PASS phần đọc | 5 vai trò xem card và bảng đủ S1–S5, không có lỗi hiển thị; quyền lifecycle chỉ PM | post-fix-serving-ui.json, native-sprint-permissions.json; không start/finish Sprint hiện hữu |
| AI Assistant/Control Center | PASS phần local đã thử | UI form, Run history, role-aware tools và trace; 5 account tự gửi Supervisor và nhận report/plan/citation trên UI | serving-browser.json; UI thêm paging/refresh/responsive trên clone trong browser-uat-1792335729.json |
| Supervisor → specialists → UI | PASS local deterministic | Worker thật, plan có thứ tự phụ thuộc, specialist/reviewer, tổng hợp và receipt model_used=false | 5 serving UI runs trên6afb, 5 concurrent clone API; PM+FE regression trên477. Không lấy backend done thay cho UI output |
| Proposal/approve/reject/audit | PASS explicit PM flow | Clone: UI preview không ghi, reject không ghi; PM approve tạo fixture451, Native readback và receipt/audit | fixture-business-chain.json; PM dùng tool form rõ ràng, chưa có tự chuyển draft thành canonical proposal |
| Second Brain | PASS phạm vi fixture | UI ingest/search/citation Native; API stale/reindex/deindex/ACL/actor/project deny và restore | fixture-business-chain.json, api-uat-1792336053.json; serving4 tài liệu cũ không bị index lại |
| n8n Daily Brief | PASS | 5 role xem fresh Native digest/source; 2 workflow thật trong clone có durable receipt/0model; serving API lịch sử trigger success | serving-panels.json, n8n-workflows.json; không kích hoạt lịch hoặc workflow mới trên serving |
| n8n execution history | PASS | Existing owner login, UI Executions có10link; API đọc20history entries | n8n-ui-qualified.json + serving-panels.json; editor localhost, owner không cấp cho nhân viên |
| PM-only-write/no business shell | PASS phạm vi đã thử | Role-aware UI 5roles; clone forged-actor/stale/hash/replay/other-project denials; Native writes chỉ fixture | serving-browser.json, browser-uat-1792335729.json, api-uat-1792336053.json |
| Gemini thật | BLOCKED | Chỉ đọc policy/quota guard và mock provider; không gọi Google | provider-offline-tests.json; G2 owner verification chưa đủ |

## Phạm vi và phiên bản bằng chứng

- Gateway trước sửa `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`, Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`:75 serving UI/API checks;64 clone browser checks;29 clone API/integration checks;9 clone business-chain checks. Đây là những lượt đã chạy trong UAT, không lấy520tests lịch sử làm lượt mới.
- Gateway sau sửa `sha256:47751dc25b5d8a091946a5371452a07f599f02f15357d2a8ba40626a8b452219`:2 clone regression checks và7 serving checks (5 Backlog/Sprint, PM read-only, FE mixed-write). Không khẳng định đã chạy lại cả bộ64/29 trên477.
- Thêm5 Daily Brief UI,1 serving history API,1 history UI và2 real workflow CLI: tổng **195 assertions chức năng cuối cùng**. Mỗi assertion không đồng nghĩa một feature hoặc một role/device độc lập.
- Unit/offline tách riêng:60Windows (41domain +19operator),41Linux network-none và58mock provider. Lượt Windows41 trước đó trùng subset60 nên không cộng lại. CSV có269dòng, phân bố{"PASS": 265, "BLOCKED": 4}; gồm permission queries, aggregate suites, system checks và4ca BLOCKED, không phải269end-to-end UI.
-5account thật chạy trên một máy qua public HTTPS, không phải5thiết bị vật lý. Chỉ fixture clone được ghi Native; serving chỉ thêm session/login timestamps và local runtime/audit metadata của7Supervisor runs.

## UAT-01: nguyên nhân và bản sửa đã triển khai

Regex cũ thấy “thay đổi” dù câu nói “không ghi thay đổi”, tạo nhãn proposal/PM review sai. Sửa `gateway/planner.py` bỏ qua động từ bị phủ định ngay tại chỗ; một động từ ghi khẳng định khác vẫn phải PROPOSAL_WRITE/REVIEW.5negation subcases RED trước sửa;41targeted tests GREEN trên Windows/Linux. Không dùng phrase “read only” để miễn gate toàn câu.

Owner đã duyệt `af53a2f8f8ce29096e111901877a3bfdc47bc1ed2b4a63c8dc48f46bf678db1f` bằng “Duyệt bản sửa, chỉ thay Gateway Staging”. Backup trước `f5ceb95d-90a1-4e07-89e7-9b4ae7788b5a`; apply22:42:39–22:42:49+07, chỉ staging-gateway; hậu kiểm UI PM c7a66217… READ_ONLY/COMPLETED và FE b00f10b7… PROPOSAL_WRITE/REVIEW, WP38 lockVersion không đổi. Khoảng apply là thời gian lệnh, không phải downtime đo liên tục. Không rollback vì hậu kiểm PASS. Backup sau `31b07c1e-d4fc-45ba-8401-503d44965d8c`; cả hai3SQLite cold restore PASS, không mở runtime WAL trên Windows.

## Đối soát bảo toàn

48module Gateway đã đóng gói khớp byte với source/candidate;7Core files khớp.7file prototype/demo được loại rõ bởi .dockerignore, không phải module runtime bị mất. Image-lock/manifest đúng cặp477/Core3b.221Native fingerprints:217giữ nguyên;4thay đổi đúng session/users/TOTPlast-used/sequences do đăng nhập.12user giữ mọi field trừ last_login_on/last_failed_login_on/updated_at (failed-login timestamp từ lượt diagnostic lỗi trước); password/token/role/membership/device secret+active/default không đổi.372WP giữ nguyên; ledger471 giữ nguyên;34proposal và4knowledge docs cũ giữ nguyên.9private files được hash guard (xem con số thực trong final-runtime-checks.json). Main/CSDLDPT không bị deploy hoặc restart.4clone đã dừng, dữ liệu/bind/network được giữ.

## Những lượt thất bại của test harness được giữ lại

- `backlog-diagnostic.json`: login chưa được xác nhận,401không chứng minh lỗi product. `backlog-authenticated-diagnostic.json` không có API/page error; trường visible_error_count cũ thực ra đếm hidden template. Chỉ dùng `.is_visible()` ở lượt cuối.
- `backlog-five-role-before-selector-fix.json` và `backlog-five-role-qualified.json` là attempts chưa đạt: heading regex/PM-only edit link; lượt sau có3timeout và QA bị dừng trước kết quả. File tên qualified không đồng nghĩa PASS.5role đọc đủ Sprint đã được rerun bằng `post-fix-serving-ui.json`, dùng table All sprints và actual S1–S5 links. Không sửa Core/RBAC vì lỗi selector này.
- `serving-panels.json` có1n8n UI FAIL do chờ thiếu; `n8n-ui-qualified.json` rerun thành công sau chờ navigation thật. History API bị helper gắn nhãn UI_REAL; CSV sửa thành API_REAL_EXISTING_OWNER.
- Raw screenshot/HTML/execution log ở private operator folder, không đưa credentials/session/HMAC vào báo cáo. Ảnh PM/FE receipt và QA Sprint đã được xem trực tiếp để kiểm tra kết quả hiển thị.

Các giới hạn/sửa tiếp xem FUNCTIONAL_GAPS.md, OPEN_BUGS.md, NEXT_ACTION_PLAN.md. Không tự đóng G2 hoặc DEF-08 từ tài liệu lịch sử.

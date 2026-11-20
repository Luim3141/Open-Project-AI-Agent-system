# Nghiệm thu Gemini Multi-Agent trên Staging

**GEMINI_LIVE_STAGING_VERIFIED** — cập nhật 2026-10-19T07:24:51.120587+07:00.

Truy cập [QLDAPM Staging](https://therapeutic-price-various-marking.trycloudflare.com). Khi Quick Tunnel đổi URL, lấy liên kết tại [landing local](http://localhost:18090).

Gateway đang chạy `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`. Core giữ nguyên image `3b09393d`; Main và CSDLDPT không thay đổi.

## Kết quả thực tế

| Chức năng | Kết quả | Phương pháp và bằng chứng |
|---|---|---|
| PM phân tích Sprint/rủi ro | PASS | Gemini thật, kết quả trên Web; [UAT](run_20261019_0013/live-web-uat-retest.json) |
| BA phân tích yêu cầu và acceptance criteria | PASS | Gemini thật, 10 công việc được giao; [UAT](run_20261019_0013/live-web-uat-retest.json) |
| QA đề xuất test cases | PASS | Gemini thật, Native #38, kết quả trên Web; [UAT](run_20261019_0013/live-web-uat-retest.json) |
| Supervisor → BA → Developer → QA → Reviewer → Web | PASS | Gemini lập plan và gọi ba specialist, tổng hợp hiển thị; [UAT](run_20261019_0013/live-web-uat-final.json) |
| BE nhận phân tích Developer | PASS | Gemini thật, kết quả trên Web; [UAT](run_20261019_0013/live-web-uat-final.json) |
| FE và BA không được ghi nghiệp vụ | PASS | UI từ chối HTTP403 trước provider, không tạo run hoặc tăng ledger; [UAT](run_20261019_0013/live-web-uat-final.json) |
| Login/TOTP/logout, Control Center và lịch sử riêng | PASS | Chromium/Edge với năm tài khoản thật; [UI trên image cuối](run_20261019_0013/final-ui-checks-acl.json) |
| Không đọc được kết quả của actor khác | PASS | BA mở run của PM bị HTTP403; cùng bằng chứng UI ở trên |
| Kiểm tra lại nguồn của progress/partial results | PASS | Native ACL/version readback; partial cũ thiếu provenance trả STALE, lịch sử gốc giữ nguyên; [API](run_20261019_0013/acl-live-readback.json) |
| PM preview → approval → Native API → receipt | PASS với provider MOCK | UI/API thật trên fixture clone #451, version1→2; [bằng chứng](run_20261019_0013/clone-browser-final.json) |
| Source/image/runtime thống nhất | PASS | 49 Gateway modules và 43 Core overlay files; [hash đối chiếu](run_20261019_0013/source-image-runtime-acl.json) |
| Dữ liệu, tài khoản, RBAC, TOTP, key và hệ thống khác | PASS | 18 container khỏe, 17 container khác không đổi; 372 Work Packages và 8 private files giữ nguyên; [đối chiếu](run_20261019_0013/final-preservation-acl.json) |
| Backup và cold restore ba SQLite | PASS | Backup `ba33c28b-2cf2-4ad7-b9b8-c50c69ad08df`; [backup](run_20261019_0013/post-acl-backup.json), [restore](run_20261019_0013/post-acl-restore.json) |

**178 tests Windows** trên source cuối và **63 tests Linux** trong immutable image PASS. Các test quota, timeout, 429/503, cancellation, schema, citation và phân quyền dùng transport offline/mock, được tách khỏi live UAT. [Regression](run_20261019_0013/acl-final-regression.json), [Linux](run_20261019_0013/linux-qualification.json).

Có **19 generation attempts / 38 HTTP phases** trong budget20, kể cả smoke và attempt lỗi. Không reset quota. Các response thành công dùng đúng `gemini-3.5-flash-lite`; key/project cũ, FREE_ONLY và không paid fallback. Provider remaining quota chưa biết. [Usage metadata](run_20261019_0013/quota-final.json).

[CSV đầy đủ](LIVE_GEMINI_UAT_RESULTS.csv) giữ nguyên bốn FAIL lịch sử và các lần kiểm tra lại. Các ca A/B/C được gọi trên image7ffee; D/BE trên1c4. Sau bản sửa riêng về ACL readback, cả năm tài khoản mở lại giao diện/kết quả trên image40cb. SDK và live-agent execution modules không đổi hash; không gọi thêm Google sau bản sửa này. Không gọi mọi attempt là chạy trên cùng một image.

## Giới hạn và công việc còn lại

- Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án; không có kiểm tra Console/billing API mới và không cam kết chi phí tuyệt đối bằng0.
- Phân tích AI là bản dự thảo cần người dùng thẩm định. Reviewer local kiểm tra citation, version, scope và mâu thuẫn trạng thái rõ ràng; không thay nghiệm thu ngữ nghĩa hoặc PM approval.
- Caption “Agents local” và cách trình bày Markdown cũ là UX gap P3. Core chưa được sửa hoặc restart; cần phạm vi triển khai Core riêng nếu xử lý.
- Một Developer response cũ không hợp lệ có output gần cap1800. Cap được lưu hiện là3000, diagnostics mới ghi finish reason và validation error. MAX_TOKENS chỉ là suy luận cho attempt cũ; schema/provider failures vẫn có thể xảy ra và phải hiện đúng là thất bại.
- Không thử model đề xuất rồi ghi vào dữ liệu Staging hiện hữu. Luồng approval/Native write chỉ dùng fixture clone và provider MOCK, ghi rõ trong bảng.
- Không chạy mới full restart Docker Desktop hoặc gây live429/503. Có bằng chứng key được dùng lại qua Gateway recreate, restart policies được giữ và các kiểm thử lỗi offline; phục hồi mất điện trước đó là bằng chứng lịch sử.
- Capacity20: **DEFERRED_BY_OWNER**. Main chưa promote; không xoay vòng TOTP; không thêm GitHub Research, VPS hoặc dịch vụ trả phí.

Các tiêu chí live Gemini Staging trong yêu cầu đã đạt theo phạm vi trên. Bước tiếp theo là người dùng UAT chất lượng nội dung; mọi promotion Main hoặc ghi dữ liệu hiện hữu ngoài fixture cần phê duyệt riêng. Không cần nhập lại API key hoặc mở lại G2 vì tài liệu lịch sử còn chữ BLOCKED.

[Checkpoint tiếp tục](run_20261019_0013/CHECKPOINT.md) ghi runtime, backup, giới hạn, nguồn bằng chứng và các thao tác không được phát lại.

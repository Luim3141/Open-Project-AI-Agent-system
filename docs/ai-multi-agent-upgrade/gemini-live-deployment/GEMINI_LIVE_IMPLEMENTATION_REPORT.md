# Gemini live Staging — kết quả triển khai

Thời điểm: 2026-10-19T07:24:51.120587+07:00. Trạng thái: **GEMINI_LIVE_STAGING_VERIFIED**.
Staging Gateway `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`; Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` giữ nguyên.
Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); lấy lại Quick Tunnel URL tại [landing local](http://localhost:18090).
Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án, không phải kiểm tra mới từ Google Cloud Console hoặc cam kết chi phí tuyệt đối bằng 0.


Người dùng có thể chọn Gemini trên AI Assistant, gửi yêu cầu phân tích và nhận kết quả thật trên Web. Gateway hiện có nhận typed task, xếp hàng, lấy dữ liệu Native theo actor, dùng Supervisor/registry hiện có, gọi model được lưu và trả kết quả/plan/citations/usage qua Core signed bridge. Không tạo Gateway thứ hai, không thêm framework hoặc dependency.

## Phạm vi source

- `gateway/live_agents.py`: JSON contracts, grounded citations, bounded model planning + specialist dispatch, local Reviewer, tổng hợp kết quả và pending PM previews.
- `gemini.py`, `store.py`: tái sử dụng SDK, private key, FREE_ONLY/shared quota; receipt metadata bền vững, giới hạn retry và ghi usage cả response không hợp lệ.
- `service.py`, `supervisor.py`, PM/BA/DEV/QA handlers: nối engine Gemini với task/queue/worker hiện có; Native ACL/version và PM-only-write trước provider; result readback actor-bound.
- `native.py`, planner, registry, Control Center/quota: Native Sprint context, negation đúng, provider capability và observed usage. `architecture.md` cập nhật cùng thay đổi.

49 module Gateway và toàn bộ 43 Core overlay files khớp source/runtime: [source-image-runtime-acl.json](run_20261019_0013/source-image-runtime-acl.json). 7 development prototypes trong `.dockerignore` không phải runtime entrypoint.

## Kiểm chứng thực thi

178 Windows tests PASS trên source cuối; 63 tests PASS trong immutable Linux image/network none. Đây là offline/mock tests, không gộp thành số live Google calls. Xem [acl-final-regression.json](run_20261019_0013/acl-final-regression.json) và [linux-qualification.json](run_20261019_0013/linux-qualification.json).

A/B/C/D/E cùng ca BE và BA-deny đạt lần kiểm tra mới nhất; thất bại ban đầu vẫn được giữ trong CSV. 5 tài khoản thật login/TOTP/logout, Control Center/history riêng, cross-actor read bị HTTP403: [final-ui-checks-acl.json](run_20261019_0013/final-ui-checks-acl.json). PM approve→Native API→readback/receipt đã thử bằng UI thật trên fixture clone451, provider ghi rõ MOCK_TEST: [clone-browser-final.json](run_20261019_0013/clone-browser-final.json).

## Lỗi đã xử lý trong UAT

1. `safe_text` thiếu import trong complete Service path: regression RED→GREEN trước lần deploy đầu.
2. Citation ngoài nguồn: model schema nay chỉ cho phép ID Native được cấp, server vẫn kiểm tra riêng. Không lưu response sai hoặc tự sửa/replay nó.
3. Reviewer nhận nhầm điều kiện READY/không có lỗi thành trạng thái thực tế: chỉ so các khẳng định trạng thái rõ gắn đúng ID, vẫn từ chối citation/version sai và mâu thuẫn trực tiếp. Kiểm định ngữ nghĩa đầy đủ vẫn thuộc người dùng.
4. Bài kiểm thử FE đòi raw internal error code: sửa assertion theo UI HTTP403 thực tế, đồng thời đối chiếu không có run/provider call/Native mutation.
5. Một Developer response không hợp lệ, usage output gần cap1800: tăng cap được lưu lên3000 trong hard limit hiện có. Không khẳng định đã chứng minh MAX_TOKENS vì attempt cũ chưa ghi finishReason; receipt mới ghi loại lỗi/finishReason, đồng bộ INVALID_RESPONSE lên UI và giữ usage. Luồng đa agent sau đó PASS.

Không thay Main, Core, DB, n8n, tunnel, account/TOTP/RBAC; serving business writes=0. 4 clone đã dừng, dữ liệu được giữ. Không promote Main, không chạy capacity20.

## Bổ sung ACL readback cuối — 2026-10-19T07:24:51.120587+07:00

Gateway40cb4806 mang context fingerprint qua progress/notify/failure, revalidates Native ACL/version cả partial output. Regression RED→GREEN;178Windows/63LinuxPASS. Hai legacy failedpartial không đủ source proof nay trả STALE, nội dung không lộ; raw history giữ. Saved LIVE_GEMINI outputs vẫn hiển thị qua5roleUI thật. [ACL API evidence](run_20261019_0013/acl-live-readback.json); [Gateway-only deploy](run_20261019_0013/acl-fix-deployment-receipt.json). Không thêm Googlecalls (vẫn19), không đổi successful generation modules. PMapprove trênclone/providerMOCK đã thử trước ACL-only fix trên1c4; latest40cb clone contract read/preview PASS, không ghi fixture lần nữa.

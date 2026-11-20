# Security và RBAC

Thời điểm: 2026-10-19T07:24:51.120587+07:00. Trạng thái: **GEMINI_LIVE_STAGING_VERIFIED**.
Staging Gateway `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`; Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` giữ nguyên.
Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); lấy lại Quick Tunnel URL tại [landing local](http://localhost:18090).
Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án, không phải kiểm tra mới từ Google Cloud Console hoặc cam kết chi phí tuyệt đối bằng 0.


Serving business mutation=0. FE9 và BA6 gửi yêu cầu đổi trạng thái, UI HTTP403, không tạo run và không tăng provider ledger; Native38version giữ nguyên. NonPM mutation bị từ chối trước queue/provider, không cấp quyền bằng prompt/modelplan. PM model operations chỉ thành canonical preview, recheckNative role/version; explicit approval/gates/receipt vẫn authoritative.

5 real roles login/TOTP/logout PASS; history/receipt actor-bound, BA đọc PMrun bị403. Business UI/registry không có operator/shell/Docker/code execution tool; model analysis không nhận executabletools. Clone PM approved fixture451 qua UI và Native readback version1→2; model phần này MOCK_TEST, không giả đó là live Gemini business write. [clone-browser-final.json](run_20261019_0013/clone-browser-final.json).

[final-preservation-acl.json](run_20261019_0013/final-preservation-acl.json):221 Native fingerprints,217 business/security fingerprints nguyên vẹn; chỉ sessions/users/deviceusage/sequences thay do login.372WP không đổi.8 private key/account/config files có hash nguyên vẹn, Gemini originalsettings giữ ngoại trừ subtree multi_agent đã duyệt. Existing tokens/TOTP security projections không đổi;12users giữ mọi trường ngoài access timestamps: [user-security-preservation-acl.json](run_20261019_0013/user-security-preservation-acl.json). Không tạo/vô hiệu hóa/rotate TOTP. Historical old23–28/new35–40 discrepancy không được hợp thức hóa thành rotation thành công.

Native authorization trước context, freshACL/version khi đọc result/retrieval; source/model text là untrusted data. Citation numericenum theo đúng NativeinputIDs và servercheckđộc lập; plan không tự mở rộng roles/agents. Safe_text/secretsPII guard được giữ. Không lưu raw model business content/OTP/cookies/token vào publicartifacts. Private screenshots/receipts ở thư mục operator ngoài repo; chỉ metadata và evidence filenames được bàn giao.

Không đổi Main/CSDLDPT container, identity/RBAC, native gates, n8n owner/machine key, Cloudflare tunnel hoặc paid configuration. Reviewer xác minh provenance/explicit conflicts, không thay nghiệm thu ngữ nghĩa hoặc PM approval.

## Bổ sung ACL readback cuối — 2026-10-19T07:24:51.120587+07:00

Gateway40cb4806 mang context fingerprint qua progress/notify/failure, revalidates Native ACL/version cả partial output. Regression RED→GREEN;178Windows/63LinuxPASS. Hai legacy failedpartial không đủ source proof nay trả STALE, nội dung không lộ; raw history giữ. Saved LIVE_GEMINI outputs vẫn hiển thị qua5roleUI thật. [ACL API evidence](run_20261019_0013/acl-live-readback.json); [Gateway-only deploy](run_20261019_0013/acl-fix-deployment-receipt.json). Không thêm Googlecalls (vẫn19), không đổi successful generation modules. PMapprove trênclone/providerMOCK đã thử trước ACL-only fix trên1c4; latest40cb clone contract read/preview PASS, không ghi fixture lần nữa.

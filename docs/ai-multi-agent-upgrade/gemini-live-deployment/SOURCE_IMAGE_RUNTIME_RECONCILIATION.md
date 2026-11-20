# Đối chiếu source, image và runtime

Thời điểm: 2026-10-19T07:24:51.120587+07:00. Trạng thái: **GEMINI_LIVE_STAGING_VERIFIED**.
Staging Gateway `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`; Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` giữ nguyên.
Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); lấy lại Quick Tunnel URL tại [landing local](http://localhost:18090).
Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án, không phải kiểm tra mới từ Google Cloud Console hoặc cam kết chi phí tuyệt đối bằng 0.


[source-image-runtime-acl.json](run_20261019_0013/source-image-runtime-acl.json):49/49 Gateway modules trong image/container khớp source;43/43 Core overlayfiles khớp, Core image không thay. Gateway source manifest SHA256 `6e16eaea2b576bdc1983130cf134f6eee6a0da2aae21f1142990a7e99b265673`; modulehashmanifest ở [candidate-image.json](run_20261019_0013/candidate-image.json). Dependency runtime tái sử dụng immutable parent; không cài library mới.

Chuỗi serving Gateway:47751dc2→0d46ba40→7ffee823→1c4ac606→40cb4806. Candidate khác chỉ build, không deploy. Mỗi serving change chỉ `staging-gateway` qua existing provision Gateway-only với freshbackup/coldrestore, sourcequalification và preflight; receipts retained, không reset/reapply sau gián đoạn.

18servingcontainers healthy,17container còn lại giữ ID/image/start/restart từ baseline; Main/CSDLDPT không thay. [final-preservation-acl.json](run_20261019_0013/final-preservation-acl.json). Clone4container đã stop, binddata/networks giữ. Source bundle hash được ghi trong source-bundle-final-acl.json sau cập nhật kiến trúc/checkpoint.

Branch codex/local-multi-agent-upgrade, HEADde7fe8f10ed23bb392b6661b0c7ccf9967524b4e; workspace có nhiều untrackedfiles sẵn. Không commit/push/reset/clean; hash manifest/bundle là căn cứ version, không gọi HEAD cũ là source đã deploy.

## Bổ sung ACL readback cuối — 2026-10-19T07:24:51.120587+07:00

Gateway40cb4806 mang context fingerprint qua progress/notify/failure, revalidates Native ACL/version cả partial output. Regression RED→GREEN;178Windows/63LinuxPASS. Hai legacy failedpartial không đủ source proof nay trả STALE, nội dung không lộ; raw history giữ. Saved LIVE_GEMINI outputs vẫn hiển thị qua5roleUI thật. [ACL API evidence](run_20261019_0013/acl-live-readback.json); [Gateway-only deploy](run_20261019_0013/acl-fix-deployment-receipt.json). Không thêm Googlecalls (vẫn19), không đổi successful generation modules. PMapprove trênclone/providerMOCK đã thử trước ACL-only fix trên1c4; latest40cb clone contract read/preview PASS, không ghi fixture lần nữa.

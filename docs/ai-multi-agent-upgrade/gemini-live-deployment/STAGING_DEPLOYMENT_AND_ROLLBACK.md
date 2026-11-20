# Triển khai và recovery

Thời điểm: 2026-10-19T07:24:51.120587+07:00. Trạng thái: **GEMINI_LIVE_STAGING_VERIFIED**.
Staging Gateway `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`; Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` giữ nguyên.
Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); lấy lại Quick Tunnel URL tại [landing local](http://localhost:18090).
Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án, không phải kiểm tra mới từ Google Cloud Console hoặc cam kết chi phí tuyệt đối bằng 0.


Owner attachment SHA256 `dbfab6c22b749b73bf4c117bf41ac3f44ce35fae90b6b814c8b3e3a364255e78` cho phép existing-model/key livecalls và Gateway-only Staging recreate sau backup/preflight; không cần xin lại cho phạm vi đó. Không triển khai Core/n8n/DB/Tunnel/Main.

Deploy receipts: [deployment-receipt.json](run_20261019_0013/deployment-receipt.json) (0d46), [uat-fix-deployment-receipt.json](run_20261019_0013/uat-fix-deployment-receipt.json) (7ffee), [receipt-fix-deployment-receipt.json](run_20261019_0013/receipt-fix-deployment-receipt.json) (1c4ac606). Mỗi receipt có thời điểm, exactimage, service-selection và keyretention.

Backup trước initial:fa032ec5-a634-494c-a799-1dab83c36fe3; trước grounded-schemafix:0c9cebc0-7039-4bf4-8ff9-fa8761b74685; trước receiptfix:c6758b3c-ff63-4c7c-9a6c-56cd7989ffd3. Backup cuối **ba33c28b-2cf2-4ad7-b9b8-c50c69ad08df**,221Nativefingerprints/assets/config/privatekeys và Gateway/knowledge/n8n SQLite. [post-acl-backup.json](run_20261019_0013/post-acl-backup.json) và [post-acl-restore.json](run_20261019_0013/post-acl-restore.json): archive/hash/integrity/coldSQLiterestore PASS. Không restore hoặc ghi đè servingDB.

Rollback đã chuẩn bị, chưa thực hiện: dừng nhận lượtAI mới và xác nhận queue idle; lưu config hiện tại; khôi phục phần multi_agent từ private gemini-settings-before.json nếu quay477; dùng Gateway-only apply với image47751dc25b5d8a091946a5371452a07f599f02f15357d2a8ba40626a8b452219; health/publiclogin/Nativeidentity/keyhash readback. Không rollback DB hoặc xóa additive receipt table. [rollback-compatibility.json](run_20261019_0013/rollback-compatibility.json) đã chứng minh oldimage mở additive SQLite coldcopy/networknone; parentimages giữ nguyên.

Không tự rollback vì historical failure đã có terminalreceipt và latestscenarioPASS. Nếu cần xử lý mới, đối chiếu actor/run/trace trước; tuyệt đối không replay unknown mutation hoặc resetquota. Credentials/TOTP không nằm trong recovery action được duyệt.

Docker manual startup: restartpolicies/persistentmounts/config/image-lock giữ; các Gateway recreates đã reusekey thật. Chưa chạy mới Docker Desktop fullrestart vì sẽ tác động hệ thống khác. Quick Tunnel có thể cấp URL mới sau restart; landing18090 là điểm tìm link.

## Bổ sung ACL readback cuối — 2026-10-19T07:24:51.120587+07:00

Gateway40cb4806 mang context fingerprint qua progress/notify/failure, revalidates Native ACL/version cả partial output. Regression RED→GREEN;178Windows/63LinuxPASS. Hai legacy failedpartial không đủ source proof nay trả STALE, nội dung không lộ; raw history giữ. Saved LIVE_GEMINI outputs vẫn hiển thị qua5roleUI thật. [ACL API evidence](run_20261019_0013/acl-live-readback.json); [Gateway-only deploy](run_20261019_0013/acl-fix-deployment-receipt.json). Không thêm Googlecalls (vẫn19), không đổi successful generation modules. PMapprove trênclone/providerMOCK đã thử trước ACL-only fix trên1c4; latest40cb clone contract read/preview PASS, không ghi fixture lần nữa.

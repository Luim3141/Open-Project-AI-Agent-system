# Quota, budget và lỗi provider

Thời điểm: 2026-10-19T07:24:51.120587+07:00. Trạng thái: **GEMINI_LIVE_STAGING_VERIFIED**.
Staging Gateway `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`; Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` giữ nguyên.
Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); lấy lại Quick Tunnel URL tại [landing local](http://localhost:18090).
Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án, không phải kiểm tra mới từ Google Cloud Console hoặc cam kết chi phí tuyệt đối bằng 0.


Owner-configured Free Tier:15RPM /250000TPM /500RPD. Existing local90% ceiling:13RPM /225000TPM /450RPD; không đặt lại usage, không vượt bằng key/project khác. AI Pro không tăng API quota.

[quota-final.json](run_20261019_0013/quota-final.json): 18 pipeline generation attempts +1smoke = **19/20** budget phiên;36 pipeline HTTP phases +2smoke=38, ledger471→509. Một INVALID_RESPONSE vẫn được tính quota/usage. Tổng usage pipeline: `{"promptTokenCount": 39133, "candidatesTokenCount": 6825, "thoughtsTokenCount": 8599, "totalTokenCount": 54557}`; smoke231total tokens. Đây là observed provider metadata của các calls đã thấy, không phải số dư/quota tổng của Google.

Shared limiter reserve trước mọi HTTP phase, exact rowid được settle sang actual prompt count; unknown outcome không được hoàn quota. CountTokens cũng được tính conservative vào local request budget. UI ghi input token reservations, không giả totalTPM hoặc token balance. Provider remaining quota = unavailable; client khác ngoài Gateway không được quan sát.

Per-run: tối đa5 generations kể cả retries;12HTTP attempts;3 specialist agents;300s live budget sau khi Native context được lấy;90s call budget;retry≤1; output≤3000; context≤32000chars; knowledge≤3. Worker outer timeout600s; không gọi300s là bound toàn bộ thời gian lấy context+chờ browser. Single-domain một call, cross-domain bốn calls thường lệ.

178 Windows/63Linux offline tests bao gồm429,503,timeout,invalidJSON,quotaexhaustion,cancel/deadline/callbudget,planexpansion/citation/RBAC,sharedqueue/providerwait/resetclasses. Không tạo live429/503 hoặc outage Google để đốt quota. Một live invalid response đã dừng, giữ receipts, không native write. Bằng chứng test ở [acl-final-regression.json](run_20261019_0013/acl-final-regression.json), [linux-qualification.json](run_20261019_0013/linux-qualification.json).

G2 được owner cho phép tiếp tục dưới attestation; không mở Console, bật billing hoặc gọi paidfallback. Không có bằng chứng thanh toán/provider billing API mới; không khẳng định chi phí tuyệt đối0.

## Bổ sung ACL readback cuối — 2026-10-19T07:24:51.120587+07:00

Gateway40cb4806 mang context fingerprint qua progress/notify/failure, revalidates Native ACL/version cả partial output. Regression RED→GREEN;178Windows/63LinuxPASS. Hai legacy failedpartial không đủ source proof nay trả STALE, nội dung không lộ; raw history giữ. Saved LIVE_GEMINI outputs vẫn hiển thị qua5roleUI thật. [ACL API evidence](run_20261019_0013/acl-live-readback.json); [Gateway-only deploy](run_20261019_0013/acl-fix-deployment-receipt.json). Không thêm Googlecalls (vẫn19), không đổi successful generation modules. PMapprove trênclone/providerMOCK đã thử trước ACL-only fix trên1c4; latest40cb clone contract read/preview PASS, không ghi fixture lần nữa.

# Provider và cấu hình được lưu

Thời điểm: 2026-10-19T07:24:51.120587+07:00. Trạng thái: **GEMINI_LIVE_STAGING_VERIFIED**.
Staging Gateway `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`; Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` giữ nguyên.
Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); lấy lại Quick Tunnel URL tại [landing local](http://localhost:18090).
Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án, không phải kiểm tra mới từ Google Cloud Console hoặc cam kết chi phí tuyệt đối bằng 0.


Project `gen-lang-client-0020540057`, exact model `gemini-3.5-flash-lite`, key hiện có ở `%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\gemini.key`. Key chỉ backend đọc, không nằm trong source/UI/artifacts. Không tạo key/project khác hoặc đổi billing/model.

`stage-ai/gemini.json` giữ nguyên cấu hình gốc, thêm `multi_agent` được lưu: `{"enabled": true, "max_model_calls": 5, "max_http_attempts": 12, "max_agents": 3, "max_output_tokens": 3000, "max_context_chars": 32000, "timeout_seconds": 300, "call_timeout_seconds": 90, "retry_limit": 1, "max_knowledge_items": 3}`. Model/provider proof/continuous-free-only authorization và key binding tiếp tục được xác minh trước mỗi attempt. Khi cấu hình không hợp lệ hoặc thay đổi giữa lượt chạy, hệ thống dừng; không paid fallback.

Luồng HTTP: existing Google SDK → countTokens → shared SQLite reservation → generateContent với JSON schema → server validation. Không tool declarations trong model analysis. Mỗi response metadata có actor/run/agent/model/phase/status/usage/time; không lưu prompt/source body/key. Invalid schema/finish reason không có repair loop. 429/503 chỉ retry trong budget/deadline hiện có, shared cooldown và queue không bị bypass.

Single-domain: một specialist model call, local Reviewer. Cross-domain rõ BA/Developer/QA: một real Gemini plan + tối đa3 specialist calls. Reviewer không gọi model và không phê duyệt thay người dùng. Tổng hợp là các góc nhìn được gắn nhãn + kết quả validation, không phải thêm một lượt model synthesis.

Chính thức: [structured output](https://ai.google.dev/gemini-api/docs/structured-output) hỗ trợ numeric enum và yêu cầu application validation; [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) phân biệt quota project/model. Nguồn này xác nhận cơ chế API, không thay thế owner attestation về Free Tier của key hiện tại.

Gateway-only recreates đã tự đọc lại key/config và gọi thành công, không nhập lại key. 18 containers giữ restart `unless-stopped`. Không chủ động restart Docker Desktop toàn hệ thống trong lần này; bằng chứng phục hồi mất điện trước đó nằm trong remaining-development, không gọi đó là một power-cycle test mới cho image cuối.

## Bổ sung ACL readback cuối — 2026-10-19T07:24:51.120587+07:00

Gateway40cb4806 mang context fingerprint qua progress/notify/failure, revalidates Native ACL/version cả partial output. Regression RED→GREEN;178Windows/63LinuxPASS. Hai legacy failedpartial không đủ source proof nay trả STALE, nội dung không lộ; raw history giữ. Saved LIVE_GEMINI outputs vẫn hiển thị qua5roleUI thật. [ACL API evidence](run_20261019_0013/acl-live-readback.json); [Gateway-only deploy](run_20261019_0013/acl-fix-deployment-receipt.json). Không thêm Googlecalls (vẫn19), không đổi successful generation modules. PMapprove trênclone/providerMOCK đã thử trước ACL-only fix trên1c4; latest40cb clone contract read/preview PASS, không ghi fixture lần nữa.

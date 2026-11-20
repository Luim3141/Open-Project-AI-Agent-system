# Provider / retention contracts đã kiểm tra

Gateway đọc quota proof/config hiện tại, không lấy limits bảng công khai làm quota thực của Project. Policy hiện có ghi15RPM/250000TPM/500RPD; engineering headroom dự kiến10RPM/175000TPM, RPD giữ mức đã được chứng minh. Chỉ áp dụng sau deployment.json.

Google xác định quota theo Project, với các chiều RPM/inputTPM/RPD; RPD reset Pacific midnight, actual capacity có thể khác limits. Vì vậy HTTP429 cũ không có quota metric/id không đủ phân biệt RPM/TPM/RPD. Không thay API key/model để tránh quota. [Google rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

Transport mới reserve từng request trong shared SQLite ledger; idempotent request IDs + claim/session/task caps; usage settlement; retry đúng known429/503 tối đa2outbounds, Retry-After/RetryInfo/backoff+jitter và cooldownpersist. Timeout/unknown body không retry tool work. AUTO opt-in chỉ continuation khi checkpoint/source/unknownwrite/budget/mode guards và **fresh readiness** đạt; hết cooldown không tạo bằng chứng thành công. Invalidkeylatch, OwnerOFF/PAUSE/CANCEL tôn trọng. Probe public cố định một generation là thao tác riêng, không phát qua health polling; một intent exclusive ngăn chạy lặp.

n8n retention phân biệt success/error/progress/manual settings. Pruning dùng age/count bounded trên execution data, không xóa Native business history. [n8n executions configuration](https://docs.n8n.io/hosting/configuration/environment-variables/executions/). Bản2.43.6 cài đặt và clone tests là bằng chứng áp dụng thực, không chỉ tài liệu chung.

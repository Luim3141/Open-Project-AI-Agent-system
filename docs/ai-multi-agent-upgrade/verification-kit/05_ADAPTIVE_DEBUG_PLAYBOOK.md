# 05 — ADAPTIVE DEBUG / ROOT-CAUSE / FIX LOOP

Đây không phải checklist cố định chạy cho đủ. Mỗi phát hiện phải phân tích ranh giới thất bại và chọn test đúng tầng. Tránh sửa 5 module chỉ để làm một test xanh.

## Kỷ luật 4 bước
1. **Xác định hành vi kỳ vọng** từ yêu cầu chính thức; giải thích environment.
2. **Tái hiện trước khi sửa** với dữ liệu an toàn, log/trace từng boundary, hypothesis duy nhất.
3. **Viết regression test RED** tại lớp gần nguyên nhân nhất; sửa tối thiểu, không phá RBAC.
4. **GREEN + smoke + affected regressions**; nếu lỗi còn, quay lại root cause. Sau 2–3 thử nghiệm không thành công, dừng và xem lại giả định/kiến trúc.

## Cây quyết định theo triệu chứng
| Triệu chứng | Cần kiểm tra | Hướng fix khi có chứng cứ |
|---|---|---|
| Docker chạy nhưng UI 502 | `docker inspect` health, Caddy upstream, network aliases, process logs; DB migrations | Thứ tự readiness/dependencies; sửa config/connection; không tạo DB mới |
| Mở Docker nhưng container không tự lên | `unless-stopped`, trạng thái manually stopped, actual compose project, Windows Docker launch | Chỉnh restart/recovery runbook, không ép Windows auto-run |
| Quick Tunnel URL không vào được | `cloudflared` runtime, hostname hiện tại, DNS, TLS, reverse proxy upstream, Cloudflare edge logs | Refresh URL share flow, restart tunnel có kiểm soát hoặc sửa upstream; KHÔNG gỡ tunnel |
| URL đổi sau Docker restart | Cloudflare Quick Tunnel sinh random hostname | Cập nhật runbook và chỉ dẫn phân phối URL, không coi là bug khi sản phẩm không cam kết URL cố định |
| Redirect loop/login qua tunnel | X-Forwarded-Proto/Host trust, cookie Secure/SameSite, CSRF origin, Caddy headers | Fix allowlisted proxy-header handling/session URL, E2E auth test |
| n8n editor lộ public | Caddy routes, tunnel target, reverse proxy paths, bindings | Thu hẹp route allowlist, editor bind local, giữ app remote working |
| 1 user xem task user khác | Rails auth/native filters, gateway actor scope, RAG ACL, cache keys | Fix authorization ở server, không chỉ UI |
| BA ghi được WP | Rails core mutation concern, Gateway/MCP host check, token actor mapping | Deny server-side + native; assert readback unchanged |
| 2 lần tạo task sau timeout | idempotency/receipts, unknown write reconciliation, replay keys | Host transaction+readback, stable request ID, no blind replay |
| 429 Gemini | Verify true quota  RPM/TPM/RPD và Retry-After; clock | Budget queue, backoff, WAITING_QUOTA, deterministic fallback; không đổi API key bypass |
| 503 Gemini | Provider unavailability/network/timeout, circuit-breaker path | bounded retry+jitter, progress state; không tăng tải vô hạn |
| 20 user test fail sau user10 | DB connection pool, Python worker, SQLite contention, n8n queue, RAM/swap | Measure p95, lock time, memory; sửa bottleneck tối thiểu |
| n8n trigger duplicate | Webhook events IDs, retry, mutable state, ack semantics | Idempotent event key+receipt; recovery test |
| Second Brain trả dữ liệu cũ | ingest freshness, ACL metadata, source revisions, cache | Add per-project/user filter, invalidation, provenance check |
| Long response được báo là success nhưng không có mutation | receipts, native readback, partial errors | UI success state must derive from validated receipts |
| CLI test run pass nhưng app browser fail | mocks, fixtures, wrong compose target, API assumptions | Add isolated browser E2E; don't call unit success whole system success |

## Quy tắc lựa chọn công nghệ
- Dùng built-in Python `unittest`, OpenProject integration tests, Postgres indexed queries trước khi thêm dependencies.
- Nếu cần full-text search nhỏ, PostgreSQL FTS có thể đủ; pgvector/embedding chỉ khi có use case và local cost phù hợp, không ép.
- Nếu SQLite concurrent writer conflict thật và cần queue bền vững: cân nhắc current store/DB isolation, rồi mới Redis tùy chi phí RAM.
- Nếu Quick Tunnel không hỗ trợ SSE: phát hiện bằng browser network traces; UI polling fallback có giới hạn nếu đúng nhu cầu; WebSocket phải E2E riêng.
- Nếu có library/CVE: ưu tiên upstream patch nhỏ tương thích và test; không mass-upgrade toàn bộ OpenProject/Gemini/n8n.

## Log defect có giá trị
`DEF-XXX: severity, reproducibility, expected, actual, environment, commit, timestamp, root-cause hypothesis, minimal repro, test RED evidence, patch diff, test GREEN evidence, regression, rollback, remaining risk, reviewer`.

## Những điều tuyệt đối không làm
- Chỉ đổi acceptance test cho pass / add `skip` / giảm assertion / hardcode 20 mock users rồi tuyên bố E2E PASS.
- Thay đổi auth/RBAC để load nhanh; cho service machine API quyền PM không phân biệt actor.
- Public `DATABASE_URL`, env secrets, local `operator_state`, Docker socket qua tunnel.
- Tự chuyển từ Gemini free sang paid API, gọi 20 live LLM liên tục trong load test.
- Xóa WAL/SHM, chạy DB restore/migration main mà chưa backup+owner approval.

# ZERO INCREMENTAL SPEND — Google AI Pro hiện có + Gemini API Free Tier

## Quy tắc phân biệt gói Pro và API

- **Google AI Pro** là thuê bao ứng dụng/quyền lợi coding đủ điều kiện (ví dụ Antigravity theo chính sách hiện hành). Nó **không cấp quota Gemini API backend không giới hạn hoặc tự nâng RPM/RPD/TPM**.
- **Gemini API Free Tier** là một tier riêng, phụ thuộc **Google AI Studio project, model, chính sách free và hạn mức tại thời điểm triển khai**. Nhiều agent/API keys dùng chung quota theo project/model. Không tự giả định model trong source `gemini-3.5-flash-lite` free/khả dụng.
- Kế hoạch này chỉ tiêu thụ Free Tier có mức phí 0 và phần mềm self-host được phép sử dụng miễn phí; không sử dụng Google Cloud credit, prepay, paid API, paid n8n, paid monitoring/VPS. Gói Pro là khoản người dùng đã có, không được tự yêu cầu mua Codex subscription/add-on.

## HARD GATE — no extra spending

1. Trong project Gemini được dùng, xác minh tier **Free** hoặc phương thức phát lệnh có **zero-billed guarantee thực sự**. Nếu không chứng minh được, cấm live provider call và chạy deterministic/queue mode.
2. `FREE_ONLY`, `PAID_API_DISABLED`, `AUTO_ENABLE_BILLING=false` là chính sách cần được **triển khai+test**, không phải env vars đã tồn tại. Cấu hình model/project phải allowlist đã verify; no silent fallback to paid model, no auto-upgrade.
3. Chỉ dùng 1 project/key chính thống đang có; không xoay API keys/projects/consumer session để né rate limit. Không dùng OAuth/Antigravity browser token như API nội bộ.
4. Kiểm tra điều khoản Gemini Free Tier về dữ liệu dùng để cải thiện sản phẩm; role/project ACL và PII phải được phép gửi trước, nếu không phải dùng deterministic local hoặc redacted text. Không in secret trong debug/evidence.
5. Không có guarantee API hoạt động 24/7 hay có free model mãi mãi. Khi quota/model thay đổi, tự dừng gọi provider không hợp lệ, dashboard báo `BLOCKED_CONFIG/WAITING_QUOTA`, native OpenProject vẫn chạy.

## Dùng GẦN TỐI ĐA quota hợp lệ nhưng không vượt

- Verify mỗi model: `RPM`, `TPM`, `RPD` và nếu có `TPD`, current tier, timezone reset, telemetry. Không hardcode 13 RPM / 225K TPM / 450 RPD từ snapshot như quota Google thật.
- Shared token bucket/leaky bucket **per (project, model, dimension)**, sử dụng 85–95% ngưỡng xác minh để chừa margin cho race/clock drift, adaptive từ 429, không gửi 100% tuyệt đối gây thất bại. Chọn margin theo evidence; hệ thống hỗ trợ 1–20 actors trong mạng LAN cục bộ (`MAX_ACTIVE_USERS=20`), concurrency ra Gemini API được chặn cứng ở mức nhỏ (mặc định 1–2 Gemini calls in flight) để bảo vệ Free Tier limit.
- Scheduler công bằng theo 1–20 actors và workflow type: đưa request vượt giới hạn vào `ai_queue`, điều phối round-robin tránh starvation; ưu tiên chat tương tác, phần quota còn lại dành báo cáo; quota chưa dùng có thể mượn theo deadline, không tạo 20 quota riêng giả. Max tool turns/calls mỗi user turn. Nếu hết daily quota thì pending sang reset provider, KHÔNG retry liên tục/không mất task.
- Không gọi LLM nếu native query xử lý được (đếm task/overdue/status). Supervisor routing bằng code trước, invoke reviewer/model thêm chỉ khi cần. Cache read-only ACL scoped + native version/TTL; input context trimmed, batching work where free capability safely allows; không assume free Batch API.
- 429 => `WAITING_QUOTA`; 503 => bounded retry exponential backoff/jitter/circuit breaker; outage => native UI vẫn chạy. Per-actor fairness/priority/audit. Không fake AI output bằng mock như kết quả thật.
- Gemini credential hiện có phải được đọc từ private persisted runtime sau restart, tự khởi tạo provider client khi Gateway healthy; kiểm tra minimal free API smoke một lần khi thích hợp, không dùng healthcheck gọi model liên tục.

## Công nghệ dùng trong bản MVP

| Thành phần | Free-only được chọn | Giới hạn |
|---|---|---|
| OpenProject | Giữ phiên bản và license hiện có | Native schema/core phải kiểm tra trước khi sửa; phục vụ 1–20 LAN users |
| Gemini | Official Gemini API SDK, verified Free Tier model/project | Shared quota cho 1–20 users; hạn chế dữ liệu và availability |
| n8n | Self-host Community Edition trong Docker | Một người nội bộ quản lý workflows; tối đa 20 người dùng nhận output qua QLDAPM; không n8n Projects/SSO/sharing paid |
| Container | Docker Desktop + WSL2 hiện có nếu đủ điều kiện license | Free cho personal/education/doanh nghiệp nhỏ dưới ngưỡng của Docker; nếu không phù hợp cần free compatible runtime khác |
| DB & queue | Existing Postgres, SQLite & local async worker | Không cần Redis cluster hoặc cloud queue |
| Knowledge | PostgreSQL FTS (pgvector chỉ nếu thực sự lợi ích/resource) | Local ACL/source provenance |
| Trace | Structured JSON logs/traces/metrics local | Không Langfuse cloud trả phí |

## Xác minh định kỳ từ nguồn chính thức

- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/billing
- https://one.google.com/about/google-ai-plans/
- https://docs.n8n.io/deploy/host-n8n/community-edition-features
- https://support.n8n.io/article/can-i-use-your-license-for-my-use-case
- https://docs.docker.com/desktop/setup/install/windows-install/
- https://docs.docker.com/engine/containers/start-containers-automatically/

**Nếu điều khoản hoặc quyền lợi thay đổi, cập nhật tài liệu và chặn tính năng không còn miễn phí; không phát sinh phí để cố đáp ứng checklist.**

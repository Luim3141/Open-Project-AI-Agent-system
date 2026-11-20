# Gemini Free Quota Playbook — 5 accounts, 1 API project

## 1. Thiết lập lần đầu (ưu tiên reuse)

- Đọc implementation `gateway/gemini.py`, `gateway/store.py`, `openproject/ai/README.md`, kiểm tra nguồn **private** key/project hiện có bằng trạng thái (`PRESENT`, `MISSING`, `INVALID`), **không in key**. Không đòi người dùng nhập lại nếu key đã lưu hợp lệ.
- Kiểm tra ở Google AI Studio một lần: project ID, billing tier, model ID free/available, RPM/TPM/RPD/TPD. Không tự đổi model chỉ vì tên 'Flash'; không tính quota Google AI Pro consumer thành API quota.
- Viết file allowlist runtime private: model→is_free_verified + observed_limits + checked_at + policy_terms; fail-closed khi chưa verify.
- Chạy một free smoke request **rất nhỏ** sau provision ban đầu, có throttle/consent, lưu trạng thái kết nối; không đưa project business content vào smoke.

## 2. Mức ưu tiên và fairness đề xuất (không đồng nghĩa mua quota)

| Priority | Class | Default approach |
|---|---|---|
| 0 | Native UI / read / RBAC / deterministic | 0 LLM calls |
| 1 | 5 users interactive | Ưu tiên chia lượt công bằng |
| 2 | User-requested supervisor work | Chỉ agent cần thiết, max depth |
| 3 | n8n daily/weekly reports | Deterministic default, optional AI khi quota spare |
| 4 | Maintenance/reindex | Chỉ local CPU/SQL |

Quy định bandwidth là **logical scheduler**, không phân 5 API keys, không chia project để né giới hạn. Nếu observed quota cao hơn thì nâng dynamic cap **trong giới hạn provider và không vượt ngưỡng an toàn**. Nếu quota thấp thì serialization và informative wait.

## 3. State và lỗi

- `READY`: cấu hình key/model Free đã verify, provider capability kiểm chứng còn hợp lệ theo freshness policy.
- `WAITING_QUOTA`: rate/daily limit, giữ task pending, chỉ retry khi thời gian phù hợp, reset theo Pacific/Google policy.
- `PROVIDER_UNAVAILABLE`: timeout/503, bounded retry và circuit breaker, không biến thành `KEY_INVALID`.
- `KEY_INVALID` / `FREE_MODEL_UNAVAILABLE`: chặn LLM và thông báo admin trên dashboard, **không tự bật paid**. Không thể hứa auto-fix credential vĩnh viễn nếu Google thu hồi.
- `PRIVACY_BLOCKED`: nội dung cần gửi không được phép; câu trả lời deterministic/redacted hoặc từ chối gửi.

**Không đặt provider healthcheck để gọi model 30 giây/lần**. Công cụ health liveness nội bộ nhanh và không tốn quota; provider readiness có TTL dài và một lần smoke nhẹ nếu cần.

## 4. Tests bắt buộc

- 5 agents cùng model/project → tổng RPM/TPM/RPD không vượt audited limits.
- 5 người cùng spam 20 prompts → mọi người được phục vụ theo fair scheduling, idle budget được tái sử dụng; UI hiển thị wait.
- 429/503/credential revoked/reset midnight PT → không phát sinh paid API calls/không retry loop.
- Docker restart → key/config/private usage ledger/pending work còn nguyên, không setup lại.
- User không có quyền đọc dữ liệu X → LLM prompt không chứa X kể cả lấy từ cache/RAG.
- Daily report khi hết quota → vẫn hiển thị deterministic summary, không mock 'Gemini đã phân tích'.


##16Oct2026 implementation — P02-06

Never-started intents wait durably before dispatch when shared project RPM/TPM/RPD or provider circuit is exhausted. This admission check spends no API quota; reserve_gemini remains the hard atomic gate. Queue wait has no created-time expiry. No new provider health probes or paid routes. Safe explicit429/503 retry is confined to the rejected SDK phase, never the run/tool loop; maximum3attempts with exponential backoff+jitter, fresh budget reservation, policy checks and existing600s hard deadline. Valid structured RetryInfo is honored; unknown429 conservatively waits3600s,50360s. A wait beyond the remaining run deadline stops that executing run with receipts; other never-started requests remain pending. Smoke/unknown transport/timeout/auth/permanent errors do not auto-retry. SDK automatic retries remain attempts=1 to avoid invisible quota use.

Official references checked16Oct2026: [Gemini retry strategy](https://ai.google.dev/gemini-api/docs/troubleshooting), [Google RPC RetryInfo](https://docs.cloud.google.com/storage/docs/reference/rpc/google.rpc). Local tests use synthetic HTTP/error payloads, not actual provider outages or private business data. Controlled reset tests change synthetic fixture timestamps only; real project usage is never cleared.

# QLDAPM AS-IS → TO-BE — Single Windows Host / 1–20 LAN Users (CR-USER-CAPACITY-20)

## AS-IS theo handoff 15/10/2026 (không giả định runtime đã verify)

- Workspace `D:\AI project\QLDAPM chat`. Main OpenProject 17.9.1 UI 8088 / Gateway 8090; staging UI 18091 / gateway 18092. Core overlay, native RBAC/gates và Gemini business tool loop đang có theo checkpoint staging; chưa coi là đã promote main.
- `openproject/ai/gateway/{app,service,permissions,native,bridge,gemini,ai_worker,store}.py`; `source/OPENPROJECT_GEMINI_AI_HANDOFF_2026-10-15.md` trong package. OpenProject Postgres là nguồn sự thật nghiệp vụ. Gateway SQLite chứa idempotency/audit/proposals/AI runs.
- Existing API key/private runtime có mô tả trong handoff; **ưu tiên sử dụng lại**, không in/copy key, không mặc định key có hiệu lực cho Free Tier. Chưa xác minh n8n, Supervisor, RAG tại runtime.

## TO-BE tối thiểu (1–20 Users, Zero Incremental Cost)

```text
1–20 USER ACCOUNTS (Multi-user per role: PM, BA, FE, BE, QA) — Thiết bị LAN
                 | HTTPS (single LAN reverse proxy + native login)
                 v
       EXISTING OPENPROJECT CORE + DB (pool=20)
                 | signed actor-bound bridge / project ACL
                 v
          EXISTING PYTHON GATEWAY (Uvicorn ASGI)
         permissions + consent + receipts
                 |                 ^
                 v                 | signed internal task API
   SMALL SUPERVISOR + AGENT RUNTIME <- n8n COMMUNITY (1 admin, local only)
       | PM, BA, FE/BE Analysis, QA, Reviewer           | scheduled project workflows
       v
    SHARED GEMINI FREE API ROUTER (Fair queue / Round-Robin across up to 20 actors)
       | Max in-flight: 1-2 calls | 15 RPM Free limit | No paid billing
       v
  LOCAL KNOWLEDGE (Postgres schema qldapm_knowledge + FTS/ACL)
       |
       v
   LOCAL CONTROL CENTER: runs / approvals / quota / errors / trace
```

## Single-host runtime behavior & Concurrency Boundaries

- **Tách rõ các ranh giới đồng thời:**
  - *Registered Users:* 1–20 tài khoản (`MAX_ACTIVE_USERS=20`).
  - *Active Sessions:* 1–20 phiên đăng nhập độc lập qua LAN.
  - *Concurrent UI/API Requests:* Xử lý qua Puma worker/thread pool (pool=20 trong compose) và ASGI Uvicorn.
  - *Concurrent AI Requests:* Chặn cứng ở mức 1 (hoặc tối đa 2) để tuân thủ 15 RPM Free Tier.
  - *Queued AI Requests:* Xếp hàng bền vững trong SQLite queue, điều phối công bằng round-robin giữa các actor.
  - *Gemini API Quota:* Giám sát tập trung (15 RPM, 500 RPD, 250k TPM); hết quota chuyển `WAITING_QUOTA`, native OpenProject không bị ảnh hưởng.
- **Sau provision ban đầu:** người dùng mở Docker Desktop → Docker engine phục hồi các containers `restart: unless-stopped` đã đang chạy trước khi daemon tắt; DB volumes & Gemini private credential vẫn còn; health/reconciliation tự chạy. Không phải tự khởi động Docker khi login Windows.
- `unless-stopped` **không tự bật container đã dừng thủ công**: vận hành dùng `Repair-QLDAPM-Local.ps1` một lần khi có stop/manual-down. Không được quảng cáo là Docker cứ bật thì mọi tình huống đều tự sửa.
- Không check Gemini bằng request tốn token mỗi vài giây; health local + startup single throttled provider smoke khi được phép; trạng thái provider độc lập: READY/WAITING_QUOTA/UNAVAILABLE/KEY_INVALID.
- 1–20 user LAN được truy cập OpenProject qua reverse proxy có HTTPS nếu provision được trust once. N8n editor, DB, gateway, RAG, operator chỉ loopback/private Docker network. Không WAN/public ports/tunnel/VPS.
- Dùng existing Postgres/SQLite và 1 n8n Community instance, 1 bounded queue, limited worker; **không Redis cluster, không Kubernetes, không Ollama requirement, không GitHub crawler/research**.

## Trust & approvals

- PM-only-write native; BA/FE/BE/QA đọc/phân tích/comment theo policy, không sửa nghiệp vụ. LLM không giữ service admin credentials và không bypass approvals, gates, replay receipts.
- n8n chỉ schedule, không làm generic direct OpenProject writes; machine identity read-only. Mọi write đề xuất rồi PM thật xác nhận qua UI actor-bound.
- Second Brain RAG prefilter theo actor/project; đưa vào provider chỉ dữ liệu được phép theo Gemini Free privacy policy. Không đồng bộ secrets, logs, tài liệu mật lên cloud.
- Release local main chỉ sau stage qualification + restore + explicit owner approval. Không tự promote khi stage test pass.

## Tránh tạo mới framework vô ích

Giữ nguyên gateway/source; thêm `agent_runtime/`, `knowledge/`, `automation/` từng lát sau kiểm toán. Nếu LangGraph không phù hợp với version đang có, dùng typed internal state machine. Redis, Langfuse cloud, external SaaS không bắt buộc. Không tác động tới branch/dirty files bằng reset/stash/clean mù.

# KIẾN TRÚC VẬN HÀNH THỰC TẾ HỆ THỐNG (ACTUAL RUNTIME ARCHITECTURE)
## DỰ ÁN: QLDAPM MAIN — PHASE 3.1 RECOVERY RUNTIME AUDIT

---

### 1. Tổng quan cấu trúc đa tầng (Multi-Tier Architecture)

Hệ thống QLDAPM MAIN vận hành trên môi trường container hóa (Docker Compose) kết hợp máy chủ ảo hóa cục bộ WSL2:

```mermaid
graph TD
    UserBrowser["Browser / Client (Playwright / Chromium)"] -->|HTTP / Hotwire Turbo Streams :18088| OpenProjectWeb["OpenProject Core (Rails 7 / Puma Monolith)"]
    OpenProjectWeb -->|PostgreSQL Protocol :5432| PostgresDB["PostgreSQL (DB: openproject)"]
    OpenProjectWeb -->|HMAC SHA256 Internal Bridge :8090| AIGateway["QLDAPM AI Gateway (FastAPI / Python 3.12)"]
    AIGateway -->|Local State / Receipts / Runs| SQLiteState["SQLite DB (/state/gateway.sqlite)"]
    AIGateway -->|Vector Similarity :6333| QdrantDB["Qdrant Vector DB"]
    AIGateway -->|HTTPS REST API (Free Tier)| GoogleGemini["Google Gemini API (gemini-3.5-flash-lite)"]
    AIGateway -->|HTTP / WebSocket :18789| OpenClawWSL["OpenClaw Runtime Sandbox (WSL2 / Node 24)"]
    OpenClawWSL -->|Local Git Worktrees| Worktrees["Isolated Git Worktrees"]
```

---

### 2. Chi tiết các thành phần vận hành (Runtime Components)

#### 2.1. Tầng Giao diện & Điều phối Core: `qldapm-openproject-web-1`
- **Công nghệ nền tảng:** Ruby 3.3.4, Rails 7.1.x, Puma 8.0.2 Cluster (Master + Worker).
- **Giao diện AI Command Center:**
  - Route: `/projects/:identifier/qldapm-ai`
  - Controller: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
  - View Partial: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
  - Cơ chế Client: Hotwire Turbo Drive + Turbo Streams kết hợp CSP Unobtrusive JavaScript.
  - Image ID: `qldapm-core:engineering-continuation-r20-20261031` (SHA256: `c15c5bb7a8370b39c70df077d2e2987a5b5fd0a66789a7c10daa2e9a3c3fc173`).

#### 2.2. Tầng Cầu nối Bảo mật (UI AI Bridge)
- **Cơ chế xác thực:** Chữ ký số HMAC SHA256 dựa trên khóa chia sẻ bảo mật `/qldapm-ui/ui.key`.
- **Đích đến:** `http://gateway:8090/internal/ui` (Private Docker Network, không mở ra Internet).
- **Quyền hạn RBAC:**
  - Xác thực phiên bằng cookie `_open_project_session` lưu trong PostgreSQL table `sessions`.
  - Phân quyền theo thời gian thực (Fresh RBAC lookup): `Qldapm::Rbac.role(@project, User.current, fresh: true)`.
  - Chỉ các vai trò `PM` hoặc `AI_SYSTEM_OWNER` mới có quyền dispatch các tác vụ điều khiển engineering.

#### 2.3. Tầng Xử lý AI Gateway: `qldapm-ai-gateway-1`
- **Công nghệ nền tảng:** Python 3.12, FastAPI, Uvicorn (Port container: 8090, Host: 18089).
- **Cơ sở dữ liệu trạng thái:** `/state/gateway.sqlite` (Dung lượng: ~14.3 MB).
  - Bảng `ai_runs`: Lưu trữ lịch sử thực thi và kết quả của các phiên chạy.
  - Bảng `receipts`: Lưu trữ **325 biên lai thực thi** của mô hình `gemini-3.5-flash-lite`.
  - Bảng `engineering_reports`: Lưu trữ các bản báo cáo tiến độ và snapshot tạo tức thời.
  - Bảng `engineering_schedules`: Lưu cấu hình lịch báo cáo tự động (múi giờ `Asia/Ho_Chi_Minh` UTC+7).
  - Bảng `engineering_github_sync_cache`: Lưu vết hash đồng bộ 5 PRs trên GitHub.

#### 2.4. Tầng Thực thi Tác nhân Cô lập: OpenClaw Sandbox (WSL2)
- **Môi trường:** Ubuntu 24.04 LTS trên WSL2, Node.js v24.22.2.
- **Cổng giao tiếp:** `127.0.0.1:18789`.
- **Bộ nhớ tác nhân (Agent Memory):** Các tệp SQLite cục bộ trong `~/.openclaw/agents/`:
  - `dev`: 15 sessions, 313 events, 377 transcript items, 144 memory chunks.
  - `reviewer`: 5 sessions, 37 events, 33 transcript items, 79 memory chunks.
  - `qa`: 4 sessions, 44 events, 48 transcript items, 8 memory chunks.
- **Chính sách an toàn:** Chặn hoàn toàn các quyền truy cập ra internet bên ngoài (`sessions_spawn`, `web_search`, `gateway` bị deny hoàn toàn); thực thi file I/O trên git worktrees cô lập.

---

### 3. Ma trận kết nối & Cổng mạng (Network & Port Bindings)

| Container / Service | Cổng nội bộ | Cổng Host | Mục đích | Bảo vệ an ninh |
|---|---|---|---|---|
| `qldapm-openproject-web-1` | 8080 | 18088 | Web GUI, OpenProject REST API | Session Cookie, CSRF Nonce, Strict CSP |
| `qldapm-ai-gateway-1` | 8090 | 18089 | Gateway RPC, AI Execution | HMAC SHA256 Signature, Internal Network |
| `OpenClaw Daemon (WSL2)` | 18789 | 18789 | Agent Tool Execution & Sandbox | Localhost only, Bearer Token |
| `qdrant` | 6333 | 16333 | Vector DB cho RAG Knowledge | Internal Docker Network |
| `openproject-db` | 5432 | 15432 | PostgreSQL Database chính | Trust Auth nội bộ container |

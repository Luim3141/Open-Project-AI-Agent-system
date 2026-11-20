# MA TRẬN TÍCH HỢP HỆ THỐNG ĐANG HOẠT ĐỘNG THẬT (LIVE INTEGRATION MATRIX — 7 LAYERS)

> **Tài liệu:** `03_LIVE_INTEGRATION_MATRIX.md`  
> **Dự án:** QLDAPM MAIN  
> **Thời điểm xác minh:** 31/10/2026  
> **Phương pháp:** Kiểm tra trực tiếp endpoint sống, thu thập HTTP status, response body và business side effects.

---

## 1. LAYER A — OPENPROJECT CORE API & POSTGRESQL

| Endpoint / Giao diện | Giao thức / Port | Phương thức | Kết quả kiểm tra | Bằng chứng thực tế |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v3/projects/6` | HTTP / 18088 | GET | `200 OK` | Trả về thông tin dự án `ai-dev-demo`, lock_version: 1 |
| `/api/v3/work_packages/379` | HTTP / 18088 | GET | `200 OK` | Parent WP #379: lock_version 4, status: IN PROGRESS |
| `/api/v3/work_packages/386` | HTTP / 18088 | GET | `200 OK` | Child WP #386: lock_version 2, liên kết PR #6 |
| `PostgreSQL 17.0` | Socket nội bộ | TCP 5432 | `CONNECTED` | Project 5: 341 WPs, max lock 4; Project 6: 7 WPs |

---

## 2. LAYER B — QLDAPM AI GATEWAY

| Endpoint | Chức năng | Xác thực | Kết quả kiểm tra | Bằng chứng thực tế |
| :--- | :--- | :--- | :--- | :--- |
| `/healthz` | Kiểm tra sức khỏe dịch vụ Gateway | Không yêu cầu | `200 OK` | Trả về `{"status":"ok","version":"1.0.0"}` |
| `/gateway/bridge` | Cầu nối điều hành AI nội bộ | HMAC-SHA256 (`ui.key`) | `200 OK` | Tiếp nhận và thực thi các lệnh từ Rails controller |
| `/gateway/knowledge/search` | Tìm kiếm tri thức Second Brain | HMAC-SHA256 | `200 OK` | BM25 FTS5 + Dense embeddings BGE-M3 |
| `/gateway/reports/generate` | Tạo báo cáo vận hành AI | HMAC-SHA256 | `200 OK` | Tạo báo cáo 6 phần Markdown hơn 3.300 ký tự |
| `/gateway/executions/:id` | Trả về telemetry chi tiết Run | HMAC-SHA256 | `200 OK` | Trả về đầy đủ 21 trường telemetry |

---

## 3. LAYER C — AI COMMAND CENTER WEB UI

| Tab / Thành phần UI | URL / Selector | Chức năng | Hành vi quan sát được |
| :--- | :--- | :--- | :--- |
| **Header Status Bar** | `#eng-mode-badge`, `#worker-status` | Hiển thị chế độ & trạng thái worker | Hiển thị chính xác `MODE: OFF` / `RUN_ONCE` và nhịp tim worker |
| **Intake Center** | `#intake-form`, `#intake-text` | Gửi yêu cầu tính năng / feedback | Gửi thành công, tạo kế hoạch PM/BA và WP con |
| **Execution Center** | `#btn-run-once`, `#btn-auto`, `#btn-pause` | Điều khiển vòng đời kỹ thuật | Chuyển đổi trạng thái mượt mà, không kẹt process |
| **Backlog & Units Matrix**| `#units-table`, `.unit-row` | Theo dõi tiến độ 6 đơn vị kỹ thuật | Cập nhật động tỷ lệ `{delivered}/{total}` (6/6 units delivered) |
| **Run Inspector Modal** | `.btn-inspect-run`, `#run-modal` | Phân tích chi tiết từng lần chạy | Mở modal ngay lập tức, hiển thị DAG, logs, traces |
| **Reports Center** | `#btn-generate-report`, `#report-modal` | Đọc và kết xuất báo cáo vận hành | Hiển thị báo cáo chi tiết đầy đủ định dạng |
| **Second Brain Search** | `#rag-search-input`, `#rag-results` | Tra cứu tri thức dự án | Tìm kiếm chính xác với trích dẫn `/work_packages/:id` |

---

## 4. LAYER D — OPENCLAW WSL2 RUNTIME & GEMINI FREE TIER

| Thành phần | Đường dẫn / Cổng | Cấu hình | Trạng thái thực tế |
| :--- | :--- | :--- | :--- |
| **OpenClaw Gateway** | `127.0.0.1:18789` | Node.js v24.22.2, port 18789 | `HEALTHY` (`/health` trả ok: true) |
| **Provider Gate** | `127.0.0.1:18890` | Root-owned transport gate, port 18890 | `ACTIVE` (Hỗ trợ tự động retry khi gặp HTTP 503) |
| **Gemini Model** | `gemini-3.5-flash-lite` | Google AI Studio Free Tier API Key | `100% FREE TIER` ($0.00 chi phí, token theo dõi chuẩn) |
| **Worktree Isolation** | `/home/openclaw/engineering/{unit}` | Git worktree riêng biệt cho từng unit | `VERIFIED` (6 worktrees độc lập, không xung đột mã) |

---

## 5. LAYER E — N8N AUTOMATION ENGINE (PORT 5679)

| Workflow ID | Tên quy trình tự động | Trạng thái | Bằng chứng kiểm toán |
| :--- | :--- | :--- | :--- |
| `X2O2QdPY6QLOrWqL` | **WF01: Local Document Ingestion** | `ACTIVE` | Đã kiểm toán qua CLI n8n trong container |
| `Anl8LNdN4NNTKRpe` | **WF02: OpenProject Event Sync** | `ACTIVE` | Lắng nghe webhook từ OpenProject |
| `XoP4M520TMG3WgeY` | **WF03: Natural Language Request Orchestrator** | `ACTIVE` | Điều phối yêu cầu ngôn ngữ tự nhiên |
| `elfapV5D2PTnLiHW` | **WF04: Multi-Agent Execution Tracking** | `ACTIVE` | Theo dõi trạng thái đa agent |
| `xCZFw45fmDQG5gNq` | **WF05: Native API Approval Workflow** | `ACTIVE` | Phê duyệt thay đổi cấu hình quan trọng |
| `Jq18aFSqfuUybEic` | **WF06: Native API Execution & Verification** | `ACTIVE` | Xác minh kết quả ghi Native API |
| `BpCQrGR866vg4BqQ` | **WF07: Daily Project Brief** | `ACTIVE` | Báo cáo tóm tắt dự án hàng ngày |
| `RXWjVUL8ozqhjY4w` | **WF08: Sprint Risk** | `ACTIVE` | Cảnh báo rủi ro tiến độ sprint |
| `tOyBIPw6sGjgzjtU` | **WF09: Bug Lifecycle Automation** | `ACTIVE` | Tự động hóa vòng đời lỗi phần mềm |
| `tOY7QUa9SrWPOe9e` | **WF10: Task Orchestration & Decomposition** | `ACTIVE` | Phân rã công việc tự động |
| `LeRVT3LWNBkJ2iz3` | **WF11: QA Gate Transition** | `ACTIVE` | Chuyển đổi trạng thái cổng QA |
| `ZkgS8RZbPRA2zbhQ` | **WF12: Weekly Summary** | `ACTIVE` | Tổng kết tuần tự động |
| `2tr0jpqaaAiq9IOU` | **WF13: Second Brain RAG Re-indexing** | `ACTIVE` | Tái đánh chỉ mục tri thức Second Brain |
| `8ycOUQy9gtT60nkN` | **WF14: Durable RAG Recovery** | `ACTIVE` | Tự phục hồi tri thức bị lỗi index |
| `NLugfE3U8dBS88Wg` | **WF15: Reconciliation & Drift Detection** | `ACTIVE` | Phát hiện độ lệch dữ liệu giữa các kho lưu trữ |
| `5FRYNPSot18UDpKa` | **WF16: Main Health Monitoring** | `ACTIVE` | Giám sát nhịp tim toàn hệ thống |

---

## 6. LAYER F — SECOND BRAIN RAG & EMBEDDING STORAGE

| Kho dữ liệu | Vị trí lưu trữ | Công nghệ | Dữ liệu kiểm toán |
| :--- | :--- | :--- | :--- |
| **Knowledge FTS5** | `/state/knowledge.sqlite` | SQLite FTS5 Full-Text Search | 14 tài liệu Project 6, BM25 rank |
| **Vector Database** | Qdrant / Local In-Memory | BGE-M3 Dense Vector Embeddings | Phục vụ truy vấn ngữ nghĩa sâu |
| **Ingestion Logs** | Bảng `knowledge_sync` | SQLite ACID transaction | Ghi vết đầy đủ idempotency key |

---

## 7. LAYER G — DEMO APPLICATION & GITHUB PULL REQUESTS

| Hạng mục | Vị trí / Địa chỉ | Nhánh Git / Commit | Trạng thái thực tế |
| :--- | :--- | :--- | :--- |
| **Demo Repository** | `D:\AI project\QLDAPM-demo\mini-task-manager` | `codex/mini-task-manager-ready` | HEAD đồng bộ với remote |
| **PR #1** | GitHub `Luim3141/mini-task-manager` | `codex/openclaw-create-list-persistence-v1` | `MERGED` |
| **PR #2** | GitHub `Luim3141/mini-task-manager` | `codex/openclaw-crud-search-web-v1` | `MERGED` |
| **PR #3** | GitHub `Luim3141/mini-task-manager` | `codex/openclaw-feedback-283138e910432528` | `OPEN` (Chờ Owner UAT) |
| **PR #4** | GitHub `Luim3141/mini-task-manager` | `codex/openclaw-feedback-4d13e695555a8d44` | `OPEN` (Chờ Owner UAT) |
| **PR #5** | GitHub `Luim3141/mini-task-manager` | `codex/openclaw-health-check-v1` | `OPEN` (Chờ Owner UAT) |
| **PR #6** | GitHub `Luim3141/mini-task-manager` | `codex/openclaw-feedback-bb9a628fe5b7be67` | `OPEN` (Chờ Owner UAT) |

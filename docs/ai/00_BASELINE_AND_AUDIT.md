# GIAI ĐOẠN 0: BASELINE VÀ AUDIT TOÀN BỘ HỆ THỐNG
**Dự án:** QLDAPM MAIN — Unified Multi-Agent AI + Real Vector RAG + Native OpenProject API + n8n Automation  
**Thời điểm audit:** 2026-10-22  
**Trạng thái Git:** Branch `codex/local-multi-agent-upgrade` (Commit `de7fe8f`)  
**Môi trường:** Windows 11, PowerShell, Docker Desktop 4.90.0 (Engine 29.7.2)  

---

## 1. PHẦN CỨNG VÀ TÀI NGUYÊN HỆ THỐNG

| Thông số | Bằng chứng runtime | Đánh giá & Ràng buộc |
|---|---|---|
| **GPU** | NVIDIA GeForce RTX 3050 Laptop GPU (4096 MiB VRAM) | Driver 610.88, CUDA 13.3. VRAM sử dụng hiện tại: 294 MiB. Dung lượng VRAM 4GB rất hạn chế: chỉ chạy model embedding `bge-m3` local, batch size khởi điểm = 2, worker = 1. Không load thêm chat LLM local vào GPU. |
| **RAM Hệ thống** | Total: ~24.8 GB (`24,862,776 KB`), Free: ~2.43 GB (`2,429,456 KB`) | **Cảnh báo dung lượng RAM khả dụng thấp (~2.4 GB free)**. Cần kiểm soát chặt chẽ memory limit của Docker container và process embedding, không chạy multi-worker ngốn RAM. |
| **CPU** | 12th Gen Intel Core i5-12500H (12 Cores, 16 Threads) | CPU đa nhân hiệu năng tốt, có thể hỗ trợ tính toán CPU khi cần. |
| **Ổ đĩa** | Ổ D: 299.5 GB khả dụng | Đủ dung lượng cho Docker images, volumes, Qdrant vectors và backups. |

---

## 2. AUDIT RUNTIME CONTAINER VÀ DỊCH VỤ

### 2.1. OpenProject Main (`qldapm-openproject`)
- **Trạng thái:** `RUNNING` (7 containers).
  - `qldapm-openproject-proxy-1`: Port `127.0.0.1:8088->80/tcp` (Up 2 hours).
  - `qldapm-openproject-web-1`: Up 2 hours (healthy), cổng nội bộ 8080.
  - `qldapm-openproject-worker-1`: Up 2 hours.
  - `qldapm-openproject-cron-1`: Up 2 hours.
  - `qldapm-openproject-db-1`: PostgreSQL 13, Up 2 hours (healthy), volume `qldapm-openproject_pgdata`.
  - `qldapm-openproject-cache-1`: Memcached, Up 2 hours.
  - `qldapm-openproject-hocuspocus-1`: Up 2 hours.
- **Xác minh API v3:**
  - Endpoint `http://localhost:8088/api/v3` phản hồi 401 Unauthorized khi chưa truyền auth (hợp lệ).
  - Xác thực Basic Auth `apikey:<token_user_19>` tới `/api/v3/users/me`: Phản hồi `HTTP 200`, User ID `19` (`QLDAPM BA-PM`).
  - Dự án ID `5`: Identifier `qldapm-local`, Name `QLDAPM — Local Community`.
  - Tổng số Work Packages: **332** items.
  - Types: `Task (1)`, `Milestone (2)`, `Summary task (3)`, `Feature (4)`, `Epic (5)`, `User story (6)`, `Bug (7)`, `Subtask (10)`. (Loại `Bug` đã có sẵn trong hệ thống với ID 7).
  - Sprints/Versions: `Sprint 1` đến `Sprint 7` (Versions 5, 6, 7, 8, 9, 10, 11).
  - Statuses: Đầy đủ 12+ statuses từ `NEW (1)`, `IN PROGRESS (7)`, `IN TESTING (9)`, `READY (33)`, `REVIEW (34)`, `DONE (35)`, `CANCELLED (36)`, `IN ANALYSIS (37)`, `READY FOR DEV (38)`, `CODE REVIEW (39)`, `READY FOR TEST (40)`, `READY FOR RELEASE (41)`.

### 2.2. AI Gateway Main (`qldapm-ai`)
- **Trạng thái:** `RUNNING` (1 container).
  - `qldapm-ai-gateway-1`: Port `127.0.0.1:8090->8090/tcp` (Up 2 hours, healthy).
  - Health check: `http://localhost:8090/health` -> `{"status": "ok"}`.
  - Mounts:
    - `/state` -> `C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway`
    - `/workspaces` -> `C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/workspaces`
    - `/qldapm-policy/free-tier-proof.json` -> `C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/operator/gemini-main/free-tier-proof.json`
  - Cấu hình (`config.json`): `gateway_mode: "native"`, `openproject_url: "http://web:8080"`, `project_id: 5`, Users: `19: PM`, `20: BA`, `21: BE`, `22: FE`, `23: QA`.
  - Storage SQLite (`gateway.sqlite`): Chứa các bảng `tokens`, `audit`, `requests`, `jobs`, `proposals`, `ai_runs`, `agent_tasks`, `agent_runs`, `automation_runs`, `execution_events`.

### 2.3. Ollama Embedding Service
- **Trạng thái:** `MISSING` (Chưa cài đặt trên Windows host).
- `ollama` không có trong `$env:PATH`, `http://localhost:11434` timeout.
- Gói chính thức `Ollama.Ollama` v0.40.8 có sẵn trên `winget`.
- Kế hoạch: Cài đặt qua winget, pull model `bge-m3`, cấu hình phục vụ cổng `11434`.

### 2.4. Qdrant Vector Database
- **Trạng thái:** `MISSING` (Chưa có container Qdrant trong Docker).
- Kế hoạch: Bổ sung container Qdrant (`qdrant/qdrant:latest`) chạy port 6333, gắn volume lưu trữ persistent độc lập trên ổ đĩa.

### 2.5. n8n Automation Engine trên Main
- **Trạng thái:** `MISSING` trên stack Main (Chỉ có instance n8n trên staging chạy port 15678; staging hoàn toàn không được đụng tới).
- Có sẵn 5 file workflow JSON mẫu trong `openproject/ai/automation/workflows/`.
- Kế hoạch: Khởi tạo instance n8n Main độc lập (SQLite/PostgreSQL riêng biệt, persistent volume, encryption key riêng, kết nối mạng nội bộ tới Gateway 8090).

---

## 3. BẢNG KIỂM KÊ CHỨC NĂNG VÀ MỨC ĐỘ SẴN SÀNG

| STT | Thành phần / Chức năng | File nguồn liên quan | Trạng thái | Đánh giá & Bằng chứng |
|---|---|---|---|---|
| 1 | **OpenProject Main Core** | `openproject/compose.yml` | `EXISTS_AND_VERIFIED` | 7 container chạy ổn định trên port 8088. API v3 phản hồi tốt với 332 work packages, dự án ID 5. |
| 2 | **Native API Adapter** | `openproject/ai/gateway/native.py` | `EXISTS_AND_VERIFIED` | Hỗ trợ `/api/v3/`, phân trang 1000 items, parse roles 5 actors, kiểm tra project identifier, bảo vệ `lockVersion`. |
| 3 | **AI Gateway FastMCP & REST** | `openproject/ai/gateway/app.py`, `service.py` | `EXISTS_AND_VERIFIED` | Chạy trên port 8090, `/health` trả HTTP 200, quản lý RBAC, tool permissions, Starlette middleware bảo mật. |
| 4 | **Multi-Agent Supervisor** | `openproject/ai/gateway/supervisor.py` | `EXISTS_AND_VERIFIED` | Thực thi bounded DAG plan, 5-actor isolation (`pm`, `ba`, `dev`, `qa`, `reviewer`), tổng hợp evidence và proposal gating. |
| 5 | **Specialist Agents** | `pm_agent.py`, `ba_agent.py`, `dev_agent.py`, `qa_agent.py`, `reviewer_agent.py` | `EXISTS_AND_VERIFIED` | Các class agent chuyên trách đã cài đặt logic phân tích, trích xuất mã task, sinh test case, review tiêu chí nghiệm thu. |
| 6 | **Gemini Provider Client** | `openproject/ai/gateway/gemini.py` | `EXISTS_AND_VERIFIED` | Bounded client, model `gemini-3.5-flash-lite`, Free-only policy, schema validation, rate-limiting & backoff. |
| 7 | **Second Brain Lexical FTS5** | `knowledge_storage.py`, `knowledge_search.py` | `EXISTS_AND_VERIFIED` | Lưu trữ SQLite FTS5 `knowledge.sqlite`, BM25 search, ACL pre-filtering theo project và role. Unit test pass. |
| 8 | **Second Brain Real Vector RAG** | Chưa có | `MISSING` | Chưa có Ollama embedding client, chưa có Qdrant client, chưa có pipeline dense vector + RRF hybrid retrieval. |
| 9 | **RBAC & Approval Gating** | `permissions.py`, `store.py`, `service.py` | `EXISTS_AND_VERIFIED` | Ma trận quyền 5 role (PM, BA, BE, FE, QA), bảng `proposals`, xác nhận 2 bước `confirm` trước khi ghi native. |
| 10 | **Audit & Tracing** | `agent_trace.py`, `execution_events.py`, `execution_monitor.py` | `EXISTS_AND_VERIFIED` | Ghi log từng native action, tool calls, bảng `audit`, `execution_events`, bảng `agent_runs`. |
| 11 | **n8n Automation Engine Main** | Chưa triển khai trên Main | `MISSING` | Container n8n Main chưa chạy; các webhook production chưa được cấu hình trên Main. |
| 12 | **Automation Workflows** | `openproject/ai/automation/workflows/` | `PARTIAL` | Đã có 5 workflow JSON (`daily-brief`, `manual-status`, `indexing-hook`, `workflow-errors`); cần mở rộng thành 16 workflows bắt buộc. |
| 13 | **Execution UI & Dashboard** | `openproject/ai/gateway/presentation.py`, `proposal_ux.py` | `EXISTS_AND_VERIFIED` | UI bridge qua `/internal/ui`, màn hình monitor và proposal confirm đã tích hợp trong gateway. |
| 14 | **Unit Test Suite** | `openproject/ai/tests/` | `EXISTS_AND_VERIFIED` | Đầy đủ test suite cho storage, permissions, supervisor, daily_brief, chạy thành công bằng Python 3.14. |

---

## 4. XÁC MINH AN TOÀN VÀ BACKUP TRƯỚC KHI TRIỂN KHAI

1. **Thư mục State của Gateway:**
   - Đã sao lưu toàn bộ từ: `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway`
   - Sang thư mục an toàn: `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway-backup-pre-master-phase0`
   - Xác minh: 13 files bao gồm `gateway.sqlite` (1.3 MB), `knowledge.sqlite` (110 KB), `credentials.json`, `config.json`, `gemini.json`, `gemini.key`, `ui.key` đều nguyên vẹn.
2. **Quy tắc an toàn dữ liệu Main:**
   - Nghiêm cấm `docker compose down -v` hoặc `docker volume prune`.
   - Giữ nguyên volume `qldapm-openproject_pgdata` và `qldapm-openproject_opdata`.
   - Mọi thao tác ghi OpenProject bắt buộc qua API v3 (`native.py`), có `lockVersion` và verification.
   - Không can thiệp, không khởi động, không sửa đổi stack Staging (`qldapm-ai-stage`).
3. **Kế hoạch Rollback:**
   - Nếu Gateway bị lỗi: Phục hồi state files từ `gateway-backup-pre-master-phase0`.
   - Nếu dịch vụ vector bị gián đoạn: Fallback về SQLite FTS5 lexical retrieval hiện hành để đảm bảo hệ thống không bị ngừng trệ.

---

## 5. KẾT LUẬN GIAI ĐOẠN 0 VÀ HÀNH ĐỘNG TIẾP THEO

- **Giai đoạn 0 đã hoàn thành với đầy đủ bằng chứng thực nghiệm.**
- Nền tảng OpenProject Main (với 332 task, 7 Sprints) và AI Gateway (với Multi-Agent Supervisor 5 roles) đang chạy ổn định.
- Khoảng trống kỹ thuật chính cần giải quyết:
  1. Xây dựng Real Vector RAG (Ollama BGE-M3 + Qdrant + SQLite FTS5 + RRF Hybrid).
  2. Bổ sung Ingestion Engine cho dữ liệu local và OpenProject.
  3. Triển khai n8n Main độc lập và nạp 16 workflows automation.
  4. Hợp nhất Multi-Agent Supervisor dùng chung Tool Registry và RAG tools.
  5. Thiết lập End-to-End Tracing và nghiệm thu toàn diện.

Sẵn sàng chuyển sang **Giai đoạn 1: Chốt Kiến trúc Đích & Tài liệu Thiết kế Kỹ thuật**.

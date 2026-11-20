# MA TRẬN RANH GIỚI TÍCH HỢP (INTEGRATION BOUNDARY MATRIX) — PHASE 2.9.2
**Hệ thống:** QLDAPM MAIN Multi-Subsystem Engineering Stack  
**Ngày lập:** 2026-10-31  
**Mục tiêu:** Định nghĩa rõ ranh giới giao tiếp, giao thức, cơ chế bảo mật, định dạng dữ liệu và phương án xử lý lỗi khi mất kết nối giữa các phân hệ.

---

## 1. BẢNG TỔNG KẾT RANH GIỚI KẾT NỐI (SUBSYSTEM INTERFACES)

| Phân hệ nguồn | Phân hệ đích | Giao thức / Port | Phương thức xác thực | Dữ liệu trao đổi (Payload) | Cơ chế chịu lỗi / Timeout | Trạng thái Phase 2.9.2 |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Browser UI** | **OpenProject Rails** | HTTP/HTTPS (Port 18088) | Session Cookie + Rails CSRF Token | Form POST / JSON Polling GET | Retry 3 lần, Toast cảnh báo nếu rớt mạng | **VERIFIED** |
| **OpenProject Rails** | **AI Gateway** | HTTP / Unix Socket (Port 18089) | Shared Internal HMAC Token | Action command JSON (`engineering_*`) | Timeout 15s; fallback thông báo người dùng | **VERIFIED** |
| **AI Gateway** | **PostgreSQL (OP DB)** | TCP (Port 5432) | Database User / Password | Truy vấn WP #379–#384 Project 6 | Connection pool; READ-ONLY trên Project 5 | **VERIFIED** |
| **AI Gateway** | **GitHub API** | HTTPS (Port 443) | GitHub Personal Access Token | PR metadata, commits, branches, CI checks | Rate-limiting cache, fallback dữ liệu local | **VERIFIED** |
| **AI Gateway** | **OpenClaw / Gemini** | HTTPS / REST (Port 18789 / 443) | Gemini API Key / Bearer | Prompts phân tích WBS, sinh code, QA test | Idempotent execution, exponential backoff | **VERIFIED** |
| **AI Gateway** | **n8n Automations** | HTTP Webhooks (Port 5679) | Webhook Secret Header | Trigger Daily Brief, Sync & Error events | Queue retry; không block luồng chính nếu n8n bận | **VERIFIED** |
| **AI Gateway** | **Second Brain (Qdrant)**| HTTP/REST (Port 6333) | Internal API Key | Vector search, embeddings tài liệu kỹ thuật | Fallback sang Keyword search nếu vector fail | **VERIFIED** |

---

## 2. CHI TIẾT CÁC RANH GIỚI QUAN TRỌNG

### 2.1. Ranh giới 1: OpenProject Web <-> AI Gateway (Command & Control Bridge)
- **Cơ chế:** Giao tiếp qua `Qldapm::AiBridge.call`.
- **Đảm bảo tính toàn vẹn:**
  - Rails Controller serialize danh tính người gọi (`user_id`, `roles`, `project_identifier`).
  - Gateway xác minh danh tính và kiểm tra quyền trong `service.py`.
  - Mọi action mutation (`engineering_run_once`, `engineering_control`, v.v.) đều sinh mã `operation_id` duy nhất và ghi vết audit.
  - Phản hồi từ Gateway luôn có cấu trúc: `{ "status": "ok"|"error", "result": {...}, "message": "..." }`.

### 2.2. Ranh giới 2: AI Gateway <-> GitHub Repository (`mini-task-manager`)
- **Cơ chế:** Tương tác qua script `engineering_github_sync.py`.
- **Ràng buộc an toàn:**
  - Chỉ đồng bộ đọc (Read/Inspect) trạng thái của các Pull Requests (#1 đến #5) và branches tương ứng.
  - **TUYỆT ĐỐI KHÔNG TỰ ĐỘNG MERGE:** Các Pull Request phải giữ nguyên trạng thái mở để chờ Chủ dự án và QA Lead trực tiếp review và phê duyệt.
  - Báo cáo rõ ràng: số PRs đã tạo (5/5), số commit trên từng branch, trạng thái CI checks (`NO_CI_CHECKS_CONFIGURED`), số lượng review threads.

### 2.3. Ranh giới 3: AI Gateway <-> n8n & Qdrant Second Brain
- **Cơ chế:**
  - n8n duy trì 16 workflows đang active tại port 5679 (`http://localhost:5679`).
  - Qdrant lưu trữ vector Second Brain tại port 6333 (`http://localhost:6333/dashboard`).
- **Ràng buộc cách ly:**
  - Lỗi xảy ra trên n8n hoặc Qdrant chỉ làm giảm cấp tính năng phụ trợ (Graceful Degradation), không được phép làm treo hoặc crash giao diện điều khiển AI Command Center trên OpenProject.
  - Tích hợp fallback báo cáo trực tiếp trong trường hợp dịch vụ phụ trợ tạm thời offline.

### 2.4. Ranh giới 4: Ranh giới Dữ liệu Dự án (Project 6 vs Project 5)
- **Project 6 (`ai-dev-demo` - ID: 6):**
  - Là môi trường phát triển AI Engineering đang hoạt động.
  - Chứa Work Packages từ #379 đến #384 (1 Epic gốc + 5 Backlog Units).
  - Trạng thái Work Package #379: Duy trì `IN PROGRESS` theo đúng cam kết vòng đời.
- **Project 5 (`qldapm-local` - ID: 5):**
  - Là tài sản nghiệp vụ gốc của hệ thống.
  - **BẤT BIẾN TUYỆT ĐỐI:** Đúng 341 Work Packages, max `lock_version: 4`, thời gian `updated_at` đóng băng tại `2026-10-29T10:08:56Z`.
  - Nghiêm cấm mọi thao tác ghi, cập nhật, xóa hoặc tái lập dữ liệu trên Project 5.

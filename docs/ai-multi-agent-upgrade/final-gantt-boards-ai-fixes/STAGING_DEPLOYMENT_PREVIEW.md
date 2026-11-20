# QLDAPM — BÁO CÁO TỔNG QUAN TRIỂN KHAI VÀ VẬN HÀNH STAGING (DEPLOYMENT PREVIEW)

> **Dự án**: Quản lý Dự án Phần mềm Hướng Đại lý AI (QLDAPM)  
> **Môi trường**: OpenProject Staging Runtime (`qldapm-ai-stage`)  
> **Thời điểm thẩm định**: 2026-10-20  
> **Địa chỉ phục vụ**:  
> - Staging Trực tiếp: `http://localhost:18091`  
> - Quick Tunnel URL: `https://foo-bodies-albert-gabriel.trycloudflare.com` (Được cấp phát động từ Cloudflare Tunnel Service)  
> - AI Gateway: `http://localhost:18092` (Nội bộ `stage-net`)  

---

## 1. ĐỐI CHIẾU DOCKER IMAGES & PHÊ DUYỆT CÓ ĐIỀU KIỆN

Toàn bộ quá trình triển khai tuân thủ tuyệt đối phê duyệt có điều kiện của Chủ dự án:

| Dịch vụ Container | Image ID Thực Tế (Inspect) | Trạng Thái Image | Ghi Chú Giữ Nguyên |
| :--- | :--- | :---: | :--- |
| **OpenProject Core (Web)** | `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` | **ĐÚNG 100% CANDIDATE** | Chứa toàn bộ nâng cấp Graph Drag & Drop, Layout Fix & 404 Resolution |
| **Python AI Gateway** | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` | **GIỮ NGUYÊN 100%** | Baseline gốc, không thay đổi, bảo vệ toàn vẹn logic Multi-Agent |
| **PostgreSQL DB** | `sha256:2d2b8998ad0635da2e718105742617df9a96e8e89f81cb4ecb53d6ab173003a2` | **HEALTHY** | Lưu trữ toàn bộ 372 work packages và 4 bảng Agile |

---

## 2. TỔNG HỢP CÁC NÂNG CẤP ĐÃ TRIỂN KHAI THÀNH CÔNG

### 2.1. Giải quyết triệt để lỗi 404 cho `stage-owner` (Issue 4)
- **Tập tin can thiệp**: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
- **Cấu hình định danh**: Đồng bộ `stage-ai/config.json` (`"5": "PM"`) và cấp OpenProject API token cho User 5 trong `stage-ai/credentials.json`.
- **Cơ chế an toàn**:
  - Gán User 5 (`stage-owner`) là Member của Dự án 3 (`qldapm-local`) với role `QLDAPM PM` (Role ID: 12).
  - Controller cầu nối cho phép Admin xem giao diện chat và 9 executions thông qua PM context (`actor_user`).
  - Chặn đứng mọi hành vi ghi/đột biến từ Admin (`return head :forbidden if User.current.admin? && User.current.id == 5`), ngăn ngừa xung đột bảo mật với Gateway.
- **Bằng chứng**: Truy cập `/projects/qldapm-local/qldapm-ai` và `/executions` trả về `HTTP 200 OK`.

### 2.2. Khắc phục bố cục Gantt bị co rúm & Cây phân cấp WBS (Issues 1 & 3)
- **Tập tin can thiệp**: `openproject/ai/core/overlay/app/views/qldapm_work_packages/_navigation.html.erb`
- **Cấu hình Rails Core**: `Setting.per_page_options = '20, 100, 500'` (cho phép nạp 500 dòng một trang).
- **Public Saved Query**: Tạo mới Query ID #37 (`QLDAPM — Scrum Roadmap theo Epic`) với timeline bật và nhóm theo phân cấp WBS.
- **Cơ chế Client-side**: Tự động thêm tham số `pp=500` vào URL chuyển hướng khi mở Gantt Chart và kích hoạt MutationObserver tự động thu gọn 11 Root Epics ban đầu.
- **Bằng chứng**: Khởi tạo ban đầu hiển thị đủ 11 Root Epics thu gọn, không còn khoảng trắng 787px; click mở rộng Epic 38 bung 3 Tasks (#49, #50, #51); mở rộng Task 49 bung các Subtasks; thu gọn lại trả về 11 Epics mượt mà.

### 2.3. Lập Kế hoạch Điều phối 1 Task = 1 Tuần (Issue 2 — Gate B)
- **Tập tin bàn giao**: `docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/SCRUM_GANTT_1WEEK_PROPOSAL.csv`
- **Quy tắc điều phối**:
  - 1 Task = 1 tuần làm việc (5 ngày làm việc liên tục Mon–Fri).
  - Subtask được phân bổ nối tiếp theo luồng BA -> BE -> FE -> QA -> PM.
  - Epic tự động bao phủ (rollup) toàn bộ khoảng ngày của các Task con.
  - 4 Sprint chu kỳ, mỗi Sprint kéo dài đúng 2 tuần (10 ngày làm việc).
- **Trạng thái an toàn**: **GANTT_DATE_PROPOSAL_AWAITING_OWNER** — Dữ liệu ngày trong Database chưa bị thay đổi, cờ `schedule_manually` được bảo toàn 100% (212 false, 58 true), nghiêm túc chờ phê duyệt Gate B từ Chủ dự án.

### 2.4. Hoàn thiện 4 Bảng Agile Boards Chuẩn (Issue 5)
- **Tập tin kết quả**: `docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/BOARDS_IMPLEMENTATION_RESULTS.md`
- **Danh sách 4 bảng**:
  1. Board #19: `QLDAPM — Main Scrum Kanban Board` (7 cột trạng thái Scrum).
  2. Board #20: `QLDAPM — Team Workload & Assignee Board` (6 cột thành viên + Chưa phân công).
  3. Board #21: `QLDAPM — Epic Breakdown & Subtasks Board` (5 cột phân rã Epic #38..#42).
  4. Board #22: `QLDAPM — Roadmap & Milestone Board` (4 cột Sprint 1..4).
- **Bằng chứng**: Playwright quét qua cả 4 bảng trả về `HTTP 200 OK` với đầy đủ thẻ và widget host.

---

## 3. DANH MỤC ĐƯỜNG DẪN TRUY CẬP PHỤC VỤ BẢO VỆ ĐỒ ÁN

| Phân Hệ / Chức Năng | Đường Dẫn Staging (Local) | Đường Dẫn Quick Tunnel (Công Khai) |
| :--- | :--- | :--- |
| **Đăng Nhập Hệ Thống** | `http://localhost:18091/login` | `https://foo-bodies-albert-gabriel.trycloudflare.com/login` |
| **Gantt Chart Roadmap** | `http://localhost:18091/projects/qldapm-local/gantt` | `https://foo-bodies-albert-gabriel.trycloudflare.com/projects/qldapm-local/gantt` |
| **Gantt View Theo Epic (#37)** | `http://localhost:18091/projects/qldapm-local/gantt?query_id=37` | `https://foo-bodies-albert-gabriel.trycloudflare.com/projects/qldapm-local/gantt?query_id=37` |
| **Agile Boards (Kanban/Scrum)** | `http://localhost:18091/projects/qldapm-local/boards` | `https://foo-bodies-albert-gabriel.trycloudflare.com/projects/qldapm-local/boards` |
| **Trợ Lý AI Trò Chuyện** | `http://localhost:18091/projects/qldapm-local/qldapm-ai` | `https://foo-bodies-albert-gabriel.trycloudflare.com/projects/qldapm-local/qldapm-ai` |
| **Giám Sát Multi-Agent** | `http://localhost:18091/projects/qldapm-local/qldapm-ai/executions` | `https://foo-bodies-albert-gabriel.trycloudflare.com/projects/qldapm-local/qldapm-ai/executions` |

---

## 4. TÀI KHOẢN TRUY CẬP ĐÃ XÁC THỰC

1. **Quản trị viên Staging (`stage-owner`)**:
   - Username: `stage-owner`
   - TOTP Device: #31 (Khôi phục thành công, `active: true`)
   - Quyền hạn: Quản trị hệ thống, xem giám sát điều phối Multi-Agent.
2. **Quản lý Dự án (`pm`)**:
   - Username: `pm`
   - TOTP Device: #24 (`active: true`)
   - Quyền hạn: Quản trị dự án, điều phối Gantt, thao tác bảng Agile Boards.
3. **Kỹ sư Backend (`be`)**:
   - Username: `be`
   - TOTP Device: #23 (`active: true`)
   - Quyền hạn: Thành viên phát triển backend.

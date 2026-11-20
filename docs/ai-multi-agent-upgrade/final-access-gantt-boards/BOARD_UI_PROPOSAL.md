# ĐỀ XUẤT NÂNG CẤP & CHUẨN HÓA BỘ AGILE BOARDS (BOARD UI PROPOSAL)

**Dự án:** QLDAPM — Local Community (`qldapm-local`, ID: 3)  
**Trạng thái Gate C:** `BOARD_UI_CANDIDATE_AWAITING_DEPLOYMENT_APPROVAL` (CHỜ CHỦ DỰ ÁN PHÊ DUYỆT TRIỂN KHAI)  
**Thời gian lập:** 2026-10-20 06:15 UTC+7  
**Người thực hiện:** Senior OpenProject Administrator & Scrum Project Manager  

---

## 1. MỤC TIÊU & BỐI CẢNH

Sau khi hoàn thành kiểm toán hành vi native của OpenProject Grids Engine (ghi nhận trong `BOARDS_NATIVE_AUDIT.md`), tài liệu này đề xuất cấu hình chuẩn hóa bộ bảng Agile Boards phục vụ báo cáo đồ án và vận hành thực tế cho nhóm 5 thành viên (PM, BA, BE, FE, QA).

**Cam kết an toàn:**
- Không tự ý sửa đổi cơ sở dữ liệu Staging hoặc triển khai image mới khi chưa có lệnh phê duyệt của Chủ dự án.
- Mọi cấu hình đề xuất đều sử dụng 100% tính năng native của OpenProject Community, không yêu cầu add-on trả phí hay sửa đổi backend Core/Gateway.

---

## 2. ĐỀ XUẤT 4 BẢNG AGILE CHUẨN HÓA (STANDARD BOARD SUITE)

### 2.1. Board 1: "QLDAPM — Main Scrum Kanban Board" (Status Action Board)
- **Mục đích:** Theo dõi tiến độ vòng đời chuẩn của Work Packages trong Sprint hiện hành.
- **Loại:** Status Action Board (`type: "action", attribute: "status"`).
- **Cấu hình 7 cột trạng thái theo luồng Scrum:**
  1. `NEW` (Mới tạo / Chờ thực hiện)
  2. `IN PROGRESS` (Đang triển khai)
  3. `CODE REVIEW` (Đang kiểm tra mã nguồn)
  4. `READY FOR TEST` (Sẵn sàng kiểm thử)
  5. `IN TESTING` (Đang kiểm thử)
  6. `REVIEW` (Chờ PM / Lead duyệt)
  7. `DONE` (Hoàn thành)
- **Giá trị mang lại:** Thể hiện trực quan toàn bộ tiến trình công việc, cho phép kéo thả card cập nhật trạng thái tự động chuẩn xác.

### 2.2. Board 2: "QLDAPM — Team Workload & Assignee Board" (Assignee Action Board)
- **Mục đích:** Cân bằng tải công việc và theo dõi phân công trách nhiệm của 5 vai trò.
- **Loại:** Assignee Action Board (`type: "action", attribute: "assigned_to"`).
- **Cấu hình 6 cột thành viên:**
  1. `Chưa phân công (Unassigned)`
  2. `PM (Project Manager)` — Quản trị phạm vi, kế hoạch, acceptance
  3. `BA-PM (Business Analyst)` — Yêu cầu nghiệp vụ, User Story, AC
  4. `BE (Backend Engineer)` — Logic nghiệp vụ, Database, API
  5. `FE (Frontend Engineer)` — Giao diện, trải nghiệm người dùng, form
  6. `QA (QA/Tester)` — Kịch bản kiểm thử, bug report, retest
- **Giá trị mang lại:** Giúp PM phát hiện ngay nút thắt cổ chai về phân bổ nhân sự (workload imbalance) chỉ qua một cái nhìn.

### 2.3. Board 3: "QLDAPM — Epic Breakdown & Subtasks Board" (Parent-Child Board)
- **Mục đích:** Giám sát các hạng mục công việc con (Tasks/Subtasks) của từng phân hệ chính.
- **Loại:** Subtasks Action Board (`type: "action", attribute: "subtasks"`).
- **Cấu hình các cột cha (Multi-Parent Columns):**
  - Cột 1: `Epic #38: Tài khoản & Role`
  - Cột 2: `Epic #39: Quản lý Project`
  - Cột 3: `Epic #40: Backlog`
  - Cột 4: `Epic #41: Sprint`
  - Cột 5: `Epic #42: Task / User Story`
- **Khắc phục triệt để hiểu lầm 1 cột:** Thay vì chỉ tạo 1 cột cho Epic 38 như Board 18 cũ, cấu hình chuẩn sẽ kích hoạt 5 cột song song cho 5 Epic cốt lõi của Sprint 1 & Sprint 2, thể hiện rõ cấu trúc phân rã công việc WBS.

### 2.4. Board 4: "QLDAPM — Roadmap & Milestone Board" (Version Action Board)
- **Mục đích:** Theo dõi tiến độ bàn giao theo từng mốc Sprint/Phiên bản.
- **Loại:** Version Action Board (`type: "action", attribute: "version"`).
- **Cấu hình 4 cột Sprint:**
  1. `Sprint 1: Nền tảng xác thực & Khởi tạo dự án`
  2. `Sprint 2: Quản lý yêu cầu & Kế hoạch làm việc`
  3. `Sprint 3: Bảng trực quan, Tiến độ & Quản trị lỗi`
  4. `Sprint 4: Giao tiếp nhóm, Báo cáo & Nghiệm thu`

---

## 3. TRẠNG THÁI GATE C & QUY TRÌNH KÍCH HOẠT DỰ KIẾN
- **Trạng thái Gate C:** `BOARD_UI_CANDIDATE_AWAITING_DEPLOYMENT_APPROVAL`.
- **Kế hoạch triển khai khi được Chủ dự án phê duyệt:**
  1. Chạy migration script tạo 4 Boards chuẩn hóa thông qua `Boards::*BoardCreateService` native.
  2. Kiểm thử Playwright tự động xác thực hiển thị đủ các cột của 4 Boards.
  3. Chụp ảnh màn hình kiểm chứng kết quả hoàn tất.

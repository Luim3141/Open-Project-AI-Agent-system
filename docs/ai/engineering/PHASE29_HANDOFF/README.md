# SỔ TAY VẬN HÀNH QLDAPM AI COMMAND CENTER (PHASE 2.9)
## HƯỚNG DẪN DÀNH CHO OWNER VÀ PROJECT MANAGER

> **Dự án:** QLDAPM MAIN  
> **Phiên bản:** Phase 2.9 (Command Center Revision r18)  
> **Đối tượng sử dụng:** System Owner (User 18), Project Manager (User 20), Tech Lead & Developers  
> **Ngôn ngữ:** Tiếng Việt

---

## 1. TRUY CẬP VÀ ĐIỀU HƯỚNG NHANH

### 1.1. Địa chỉ truy cập
- **Đường dẫn chuẩn:**  
  `http://127.0.0.1:18088/projects/qldapm-stage/qldapm-ai/engineering`
- **Quyền truy cập:**
  - `User 18 (AI_SYSTEM_OWNER)`: Toàn quyền quan sát, điều khiển, cấu hình lịch trình, chạy chế độ tự động và kích hoạt đồng bộ.
  - `User 20 (BA-PM)`: Quyền quan sát, lập kế hoạch, kích hoạt báo cáo và tra cứu cơ sở tri thức.
  - `User 19 (Guest)`: Bị chặn truy cập theo cơ chế RBAC (HTTP 403 Forbidden chuẩn mực).

### 1.2. Cơ chế chuyển đổi giao diện linh hoạt (Dual-Mode)
Command Center được trang bị cơ chế chuyển đổi dự phòng 1-click để đảm bảo tính an toàn tuyệt đối:
- **Giao diện hiện đại (Mặc định):** Truy cập bình thường hoặc thêm tham số `?ui=modern`.
- **Giao diện cổ điển (Classic Fallback):** Nhấp nút **"Classic View"** trên góc phải Header hoặc thêm tham số `?ui=classic`.
- **Ghi nhớ phiên làm việc:** Trạng thái giao diện được lưu trong Rails Session; người dùng không cần nhập lại tham số khi chuyển trang.

---

## 2. HƯỚNG DẪN SỬ DỤNG 8 PHÂN HỆ ĐIỀU HÀNH (NAVIGATION TABS)

Giao diện Command Center được tổ chức thành 8 Navigation Tabs tại thanh điều hướng bên trái (Sidebar):

### Tab 1: Mission Control (Tổng hành dinh)
- **4 Thẻ chỉ số Hero (KPIs):**
  - *Active Units:* Số lượng đơn vị công việc trong pipeline (5 units).
  - *Stacked PRs:* 5 Pull Requests đồng bộ với GitHub repo.
  - *Test Coverage:* Tỷ lệ test đạt chuẩn (100% PASS - 21/21 tests).
  - *System Mode:* Trạng thái chế độ hiện tại (`OFF` / `RUN ONCE` / `PAUSED`).
- **Khối nút điều khiển tác vụ (Command Actions):**
  - `RUN ONCE`: Kích hoạt một chu trình thực thi đơn lẻ có giám sát.
  - `PAUSE`: Tạm dừng các tác vụ đang xếp hàng.
  - `OFF`: Tắt hoàn toàn chế độ tự động (Trạng thái an toàn khuyến nghị).
  - `GITHUB SYNC`: Kích hoạt đồng bộ hai chiều tức thì với GitHub.
  - `REFRESH`: Tải lại nhanh các chỉ số mới nhất từ AI Gateway.
- **Ma trận tình trạng dịch vụ (Service Health):** Hiển thị trạng thái của 7 dịch vụ cốt lõi (OpenProject, Gateway, OpenClaw, n8n, Qdrant, Ollama, Demo App).

### Tab 2: Pipeline Stages (Quy trình 8 chặng kỹ thuật)
- Cho phép người quản trị theo dõi tiến độ một công việc từ lúc nhận yêu cầu đến khi bàn giao:
  1. *WP Intake & Scope Analysis:* Phân tích nghiệp vụ từ Work Package.
  2. *Architecture & Decomposition:* Bóc tách kiến trúc và lập kế hoạch kỹ thuật.
  3. *Workspace Provisioning:* Cấp phát môi trường làm việc cô lập (Isolated Git Worktree).
  4. *TDD Implementation:* Lập trình mã nguồn theo phương pháp Test-Driven Development.
  5. *Code Review & Security:* Rà soát mã độc lập và kiểm toán an ninh.
  6. *QA Automation:* Kiểm thử tự động hóa, kiểm tra độ tươi và hồi quy.
  7. *Git Commit & PR Publication:* Đóng gói commit và mở Pull Request xếp tầng.
  8. *Second Brain Vectorization:* Trích xuất vector và lập chỉ mục tri thức.

### Tab 3: Agent Workforce (Đội ngũ 6 Persona AI)
- Minh bạch hóa vai trò, nhiệm vụ và công cụ của từng Agent:
  - **BA Agent:** Bóc tách yêu cầu, thiết lập tiêu chí chấp nhận (Acceptance Criteria).
  - **PM Agent:** Quản lý phụ thuộc, điều phối thứ tự ưu tiên và lịch trình.
  - **Dev Agent:** Viết mã nguồn nghiệp vụ, tuân thủ nguyên tắc Ponytail và TDD.
  - **Reviewer Agent:** Rà soát code độc lập, phát hiện lỗ hổng và kiểm tra chuẩn mực repo.
  - **QA Agent:** Thiết kế test cases, thực thi kiểm thử và ký xác nhận chất lượng.
  - **Delivery Agent:** Quản lý Git branches, mở PR và đồng bộ hóa tài liệu bàn giao.

### Tab 4: Native Backlog (Quản lý Work Packages)
- Hiển thị cấu trúc cây Work Packages của OpenProject liên kết trực tiếp với dự án demo:
  - `WP #379` (Epic/Feature): Quản lý công việc chính — Trạng thái: `IN PROGRESS`.
  - `WP #380` (Task): Hạ tầng phát triển & Test framework — Trạng thái: `REVIEW`.
  - `WP #381` (Task): Task Model & Validation logic — Trạng thái: `REVIEW`.
  - `WP #382` (Task): Giao diện Web tương tác — Trạng thái: `REVIEW`.
  - `WP #383` (Task): Báo cáo thống kê công việc — Trạng thái: `REVIEW`.
  - `WP #384` (Task): Kiểm toán & Nghiệm thu tự động — Trạng thái: `DELIVERED_PR_OPEN`.

### Tab 5: Execution Terminal (Lịch sử chạy & Console)
- Bảng nhật ký ghi nhận mọi lượt thực thi của các Agent:
  - Run ID, thời gian bắt đầu, thời lượng thực thi.
  - Mã thoát (Exit Code) và trạng thái hoàn tất (`SUCCESS`, `FAILED`, `ABORTED`).
  - Danh mục Artifacts đã sinh ra (bản ghi âm, nhật ký, patch diffs).

### Tab 6: GitHub Integration (Minh bạch 5 PRs)
- Theo dõi trạng thái của 5 Pull Requests trên repository demo:
  - Phân loại rõ ràng nhánh đích: Nhánh chính (`main`) vs Nhánh tính năng (`codex/mini-task-manager-ready`).
  - Ghi nhận đầy đủ thông tin kiểm thử nội bộ: Nhãn `Local AI Review: PASS`.
  - Cung cấp liên kết trực tiếp mở PR trên trình duyệt.

### Tab 7: Reports & Analytics (Báo cáo tự động)
- **Kích hoạt tức thì:** 3 nút tạo báo cáo `Daily Report`, `Weekly Report`, `On-Demand Audit`.
- **Cấu hình lịch trình tự động:** Xem chi tiết tại Mục 3.
- **Thẻ tóm tắt báo cáo:** Hiển thị số liệu thực tế về tiến độ, dòng lệnh, test cases và rủi ro phát hiện được.

### Tab 8: Knowledge & RAG (Second Brain Tra cứu)
- **Công cụ tìm kiếm thông minh:** Nhập từ khóa hoặc câu hỏi kỹ thuật (ví dụ: `task validation`, `state transition`, `WP 384`).
- **Kết quả tra cứu:** Trả về các đoạn trích dẫn chính xác kèm liên kết trực tiếp đến Work Package hoặc tài liệu trong cơ sở tri thức Qdrant.

---

## 3. HƯỚNG DẪN CẤU HÌNH LỊCH BÁO CÁO DAILY (SCHEDULE CONFIG MODAL)

Hệ thống hỗ trợ phát báo cáo tự động mỗi ngày theo múi giờ Việt Nam (`Asia/Ho_Chi_Minh` UTC+7):

1. Chuyển sang **Tab 7: Reports & Analytics**.
2. Nhấp vào nút **"Configure Schedule"** (có biểu tượng đồng hồ bấm giờ).
3. Hộp thoại cấu hình xuất hiện:
   - **Bật/Tắt lịch trình:** Đánh dấu chọn ô *Enable Daily Automated Report*.
   - **Thời gian chạy:** Chọn giờ và phút mong muốn (ví dụ: `08:00` hoặc `18:00`).
   - **Múi giờ:** Mặc định cố định là `Asia/Ho_Chi_Minh (UTC+7)`.
4. Nhấp nút **"Save Schedule"** để lưu cấu hình vào cơ sở dữ liệu SQLite của AI Gateway.
5. Để hủy lịch: Mở modal, bỏ chọn ô kích hoạt và nhấp "Save Schedule".
6. Để đóng modal: Nhấp vào dấu **X** ở góc phải hoặc nhấp vào vùng đen bên ngoài hộp thoại.

---

## 4. CÁC NGUYÊN TẮC AN TOÀN VẬN HÀNH BẮT BUỘC

1. **Chế độ Vận hành Mặc định là `OFF`:**
   - Hệ thống được cấu hình mặc định ở chế độ `OFF`. Chỉ bật chế độ `RUN ONCE` khi cần thực thi một tác vụ cụ thể có sự giám sát của kỹ sư.
   - Tránh để chế độ `AUTO` chạy liên tục mà không có người theo dõi.
2. **Cô lập tuyệt đối Project 5 (`qldapm-local`):**
   - Mọi thử nghiệm, chạy tự động và tạo PR chỉ được phép thực hiện trên Project 6 (`qldapm-stage`) và kho mã nguồn demo.
   - Tuyệt đối không trỏ lệnh AI Engineering vào Project 5.
3. **Quy tắc Hợp nhất Pull Requests:**
   - Các PRs (#1, #3, #4, #5) đang ở trạng thái `OPEN` để chờ Chủ dự án rà soát thủ công.
   - Không được tự ý nhấp "Merge" trên GitHub khi chưa có phê duyệt chính thức.
4. **Trạng thái Work Package #379:**
   - Giữ nguyên trạng thái `IN PROGRESS` của WP #379 cho đến khi toàn bộ giai đoạn Phase 2 được nghiệm thu tổng thể.

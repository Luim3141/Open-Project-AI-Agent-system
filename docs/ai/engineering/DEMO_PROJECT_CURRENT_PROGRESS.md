# BÁO CÁO TIẾN ĐỘ THỰC TẾ MINI TASK MANAGER & KỊCH BẢN THỬ NGHIỆM WORK INTAKE
## Đối Soát Hiện Trạng 5 Đơn Vị Phát Triển, Trạng Thái WP #379–#385 & Hướng Dẫn Tự Kiểm Thử Dành Cho Project Owner

**Dự án Demo:** `Luim3141/mini-task-manager`  
**Dự án Quản lý:** OpenProject Project 6 (`ai-dev-demo`)  
**Tài khoản Kho lưu trữ:** `Luim3141` (Project Owner: Mạc Đăng Hiệp)

---

## 1. Bảng Phân Định Trạng Thái Thực Tế Toàn Bộ Đơn Vị Kỹ Thuật

Dưới đây là ma trận tiến độ đối soát đa chiều (Code Base, Git Branch, GitHub REST API, Test Sandbox và OpenProject Database):

| Mã WP | Tên Tính năng / Đơn vị kỹ thuật | GitHub PR | Nhánh nguồn / Nhánh đích | Trạng thái Code & PR | Đánh giá QA / Reviewer | Trạng thái Bàn giao |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: |
| **#380** | Khởi tạo bảng công việc SQLite & REST API cơ bản | [PR #1](https://github.com/Luim3141/mini-task-manager/pull/1) | `codex/openclaw-create-list-persistence-v1` → `main` | **MERGED TO MAIN** (Manual by Owner) | Reviewer: PASSED<br>QA: 4/4 Passed | **DEPLOYED** |
| **#381** | Giao diện Web, chức năng Sửa/Xóa/Trạng thái/Tìm kiếm | [PR #2](https://github.com/Luim3141/mini-task-manager/pull/2) | `codex/openclaw-crud-search-web-v1` → `codex/openclaw-create-list-persistence-v1` | **MERGED TO BRANCH** (Manual by Owner) | Reviewer: PASSED<br>QA: 6/6 Passed | **MERGED** |
| **#382** | Bổ sung Component Web UI, Trợ lý Request & Hỗ trợ a11y | [PR #3](https://github.com/Luim3141/mini-task-manager/pull/3) | `codex/openclaw-feedback-283138e910432528` → `codex/openclaw-crud-search-web-v1` | **OPEN / IN REVIEW** | Reviewer: PASSED<br>QA: 8/8 Passed | **PR_OPEN** |
| **#383** | Hỗ trợ tìm kiếm chuỗi Unicode tiếng Việt (`str.casefold`) | [PR #4](https://github.com/Luim3141/mini-task-manager/pull/4) | `codex/openclaw-feedback-4d13e695555a8d44` → `codex/openclaw-feedback-283138e910432528` | **OPEN / IN REVIEW** | Reviewer: PASSED<br>QA: 10/10 Passed | **PR_OPEN** |
| **#384** | Bổ sung route giám sát `GET /healthz` & Unit Test | [PR #5](https://github.com/Luim3141/mini-task-manager/pull/5) | `codex/openclaw-health-check-v1` → `codex/openclaw-feedback-4d13e695555a8d44` | **OPEN / IN REVIEW** | Reviewer: PASSED<br>QA: 12/12 Passed | **PR_OPEN** |
| **#385** | Bổ sung danh mục (Category), lọc dữ liệu & xuất CSV | *Chưa tạo PR* | *Backlog Item mới tạo từ Work Intake* | **SPECIFIED** (AC10, AC11, AC12) | Chờ điều phối chạy | **QUEUED** |

> [!NOTE]
> **Trạng thái Epic WP #379:** Tiếp tục giữ trạng thái **IN PROGRESS** (Đang triển khai).  
> Theo quy tắc an toàn đã cam kết, hệ thống tuyệt đối không tự ý đóng hoặc chuyển WP #379 sang CLOSED/RESOLVED khi các PR #3, #4, #5 vẫn đang ở trạng thái OPEN trên kho GitHub.

---

## 2. Giải thích Kiến trúc Chuỗi Nhánh Stacked PR (PR #1 → PR #5)

Dự án sử dụng chiến lược **Stacked Pull Requests** chuẩn mực của các nhóm kỹ sư cấp cao:
- **PR #1** được merge trực tiếp vào `main`.
- **PR #2** được merge vào nhánh của PR #1.
- **PR #3, #4, #5** xếp chồng lên nhau nhằm đảm bảo mỗi PR là một đơn vị thay đổi nguyên tử (Atomic Change), dễ dàng review và rollback nếu cần.
- Việc merge PR #3, #4, #5 vào `main` cần sự quyết định và thao tác thủ công của Project Owner trên GitHub Web UI khi toàn bộ chu trình kiểm thử hoàn tất.

---

## 3. Kịch bản Thử nghiệm Thực tế Dành Cho Owner: Giao việc qua Work Intake

Để chứng minh hệ thống AI hoạt động end-to-end với quy trình tiếp nhận công việc thực tế, Project Owner hãy tự mình thực hiện bài test sau đây **(Hệ thống KHÔNG tự ý thực thi thay Owner)**:

### 3.1. Đề bài tính năng mới đề xuất
Yêu cầu AI phát triển thêm tính năng: **Đánh dấu công việc quan trọng (Priority Flag & Starred Tasks)** cho Mini Task Manager.

### 3.2. Nội dung Prompt chuẩn bị sẵn để Owner copy-paste
Owner chỉ cần sao chép toàn bộ đoạn văn bản dưới đây và dán vào ô nhập liệu **AI Work Intake** tại Tab **Backlog & Tasks**:

```text
Yêu cầu tính năng mới: Thêm tính năng Đánh dấu công việc quan trọng (Priority & Starred)

1. Mô tả nghiệp vụ:
Người dùng cần phân loại công việc theo mức độ ưu tiên (LOW, MEDIUM, HIGH, URGENT) và có thể gắn ngôi sao (is_starred: boolean) để ghim công việc lên đầu danh sách.

2. Yêu cầu kỹ thuật:
- Cập nhật cơ sở dữ liệu SQLite: Thêm cột `priority` (TEXT, default 'MEDIUM') và `is_starred` (INTEGER, default 0) vào bảng tasks.
- Bổ sung tham số truy vấn trong API GET /tasks: `?priority=HIGH` và `?starred=true` để lọc công việc.
- Cập nhật API POST /tasks và PUT /tasks/<id> để hỗ trợ lưu và cập nhật 2 trường dữ liệu trên.
- Viết unit test tự động bằng pytest kiểm tra: tạo task có priority, cập nhật trạng thái starred, và truy vấn lọc chính xác.

3. Tiêu chí nghiệm thu (Acceptance Criteria):
- AC-01: Mặc định task mới tạo có priority là 'MEDIUM' và is_starred là 0 (false).
- AC-02: Cho phép gọi PUT /tasks/<id>/star để bật/tắt cờ ghim quan trọng.
- AC-03: Tất cả các pytest cũ (12 tests) và test mới phải PASS 100%.
```

### 3.3. Các bước Owner trực tiếp thao tác trên giao diện:
1. Truy cập: `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`
2. Mở Tab **Backlog & Tasks**.
3. Cuộn xuống khối **AI Work Intake (Tiếp nhận & Lập kế hoạch Yêu cầu mới)**.
4. Dán đoạn prompt trên vào khung văn bản.
5. Nhấn nút **Giao việc mới cho AI (Tạo Backlog Unit)**.
6. Quan sát Toast thông báo màu xanh hiển thị thành công:  
   `Đã tiếp nhận yêu cầu tính năng mới. Tác nhân PM & BA đang lập kế hoạch và bóc tách đặc tả kỹ thuật...`
7. Mở Tab **Execution Center** hoặc Tab **Backlog & Tasks** để thấy một Work Package mới được tạo lập tự động trên OpenProject kèm theo mã Run ID giám sát.

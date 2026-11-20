# HƯỚNG DẪN PROJECT OWNER TỰ KIỂM THỬ TÍNH NĂNG TIẾP THEO: "PRIORITY & STARRED TASKS"

> **Tài liệu:** `10_OWNER_NEXT_TASK_GUIDE.md`  
> **Dành cho:** Project Owner trực tiếp giao việc cho AI Agents và kiểm chứng tính năng mới  
> **Tính năng mục tiêu:** Đánh dấu ưu tiên và gắn sao công việc (Priority & Starred Tasks)  
> **Mục đích:** Hướng dẫn từng bước từ việc nhập đề bài đến khi AI tự động viết code, kiểm thử và mở GitHub Pull Request #7.

---

## 1. MỤC TIÊU VÀ ĐỀ BÀI DÀNH CHO AI AGENTS

Tính năng tiếp theo được thiết kế để Owner có thể tự kiểm tra toàn bộ năng lực tự hành của hệ thống:

- **Tên tính năng:** Đánh dấu ưu tiên và gắn sao công việc (`priority` & `is_starred`).
- **Mục tiêu kỹ thuật:**
  1. Thêm trường `priority` (chuỗi: `"low"`, `"medium"`, `"high"`, mặc định `"medium"`) vào bảng `tasks` trong SQLite.
  2. Thêm trường `is_starred` (kiểu boolean: `true` / `false`, mặc định `false`).
  3. Cho phép cập nhật qua `PATCH /tasks/{id}`.
  4. Hỗ trợ lọc qua `GET /tasks?priority=high&is_starred=true`.
  5. Cập nhật giao diện HTML trên trang chủ (`GET /`) có nút click gắn sao ⭐ và chọn mức ưu tiên.
  6. Viết bộ kiểm thử pytest trong `tests/test_tasks.py` chứng minh chức năng hoạt động đúng.

---

## 2. QUY TRÌNH 5 BƯỚC THAO TÁC TRỰC TIẾP TRÊN TRÌNH DUYỆT

### Bước 1: Mở AI Command Center và Tab Work Intake
1. Mở trình duyệt và truy cập:
   ```text
   http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern
   ```
2. Nhấp vào tab **Intake** (hoặc cuộn đến phần **Work Intake Center**).

### Bước 2: Nhập Yêu Cầu Tính Năng Mới
Sao chép và dán chính xác đoạn văn bản sau vào ô nhập liệu:

```text
Yêu cầu bổ sung tính năng Priority và Starred Tasks cho Mini Task Manager theo thẻ QLDAPM-FEAT-STARRED-TASKS:
1. Bổ sung trường priority ('low', 'medium', 'high', mặc định 'medium') và is_starred (boolean, mặc định false) trong cơ sở dữ liệu SQLite.
2. Cho phép PATCH /tasks/{id} cập nhật priority và is_starred.
3. Cho phép GET /tasks?priority=...&is_starred=... lọc công việc theo priority và trạng thái gắn sao.
4. Hiển thị biểu tượng ngôi sao ⭐ trên giao diện web để người dùng có thể click bật/tắt gắn sao nhanh chóng.
5. Viết pytest kiểm thử toàn diện các trường hợp trên trong tests/test_tasks.py.
```

Nhấn nút **Gửi yêu cầu (Submit Feedback / Plan)**.

### Bước 3: Quan Sát AI PM & BA Lập Kế Hoạch Tự Động
1. Trong vòng 5-10 giây, AI PM & BA Agents sẽ phân tích yêu cầu.
2. Hệ thống sẽ tự động tạo một Work Package con mới (dự kiến là **WP #387**) dưới Parent WP #379 trong OpenProject.
3. Một đơn vị kỹ thuật mới (dynamic unit) sẽ xuất hiện trong bảng danh sách **Backlog & Engineering Units** với trạng thái `PLANNED`.

### Bước 4: Kích Hoạt Thực Thi Kỹ Thuật (RUN ONCE)
1. Tại hàng của unit mới vừa xuất hiện trong bảng Backlog, nhấp nút **RUN ONCE**.
2. Hệ thống sẽ kích hoạt luồng tự động:
   - Chuyển `MODE` sang `RUN_ONCE`.
   - WSL2 OpenClaw tạo worktree cô lập.
   - Dev Agent thực thi code và tests.
   - Reviewer Agent đối soát diff.
   - QA Agent chạy bộ test pytest.
   - Tự động tạo git commit và đẩy lên nhánh mới trên GitHub.
3. Owner có thể mở nút **Inspect** để theo dõi trực tiếp tiến độ DAG từ `context` đến `pull-request`.

### Bước 5: Kiểm Tra Kết Quả Trên GitHub (Pull Request #7)
1. Khi trạng thái unit chuyển sang `succeeded`, truy cập GitHub repo:
   ```text
   https://github.com/Luim3141/mini-task-manager/pulls
   ```
2. Bạn sẽ thấy **Pull Request #7** được mở tự động với toàn bộ mã nguồn và bộ kiểm thử đã được AI hoàn thiện và ký nhận.
3. Xem diff trên GitHub để thẩm định và tự quyết định merge vào `main` khi hài lòng!

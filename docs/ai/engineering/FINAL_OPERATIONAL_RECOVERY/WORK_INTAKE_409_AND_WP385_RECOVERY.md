# BÁO CÁO PHÁP Y VỀ WORK PACKAGE #385 VÀ GIẢI QUYẾT LỖI HTTP 409
## FORENSIC AUDIT OF WP #385 DELETION & CONCURRENCY RESOLUTION

- **Thời gian lập:** 31/10/2026 20:35:00 (UTC+07:00)
- **Tài liệu tham chiếu:** SQLite `engineering_plans` (Plan ID: `b1cca031-81f5-4df1-870b-cbeb23d51e66`), PostgreSQL `work_packages` và `journals`.

---

### 1. KẾT QUẢ ĐIỀU TRA PHÁP Y VỀ VIỆC XÓA WORK PACKAGE #385

#### A. Dấu vết trong cơ sở dữ liệu PostgreSQL
- Truy vấn bảng `work_packages` với `id = 385`: `0 rows returned`.
- Truy vấn bảng `journals` với `journable_id = 385`: `0 rows returned`.
- **Kết luận pháp y:** Work Package #385 đã bị **xóa cứng (hard delete)** khỏi cơ sở dữ liệu PostgreSQL trong một phiên khắc phục sự cố trước đó (khoảng thời gian chuyển tiếp giữa Phase 3.1 và Phase 3.2).
- **Mục đích của việc xóa trong quá khứ:** Kỹ sư trước đó cố gắng giải phóng xung đột khóa phiên bản (`lock_version = 4` của WP cha #379) sau khi gặp lỗi `HTTP 409: Lock version stale`, nhưng hành động này là một sai lầm thao tác vì làm mất tính toàn vẹn chuỗi Work Package trên OpenProject.

#### B. Khôi phục nguyên vẹn đặc tả nghiệp vụ từ SQLite Gateway
Rất may mắn, toàn bộ nội dung yêu cầu, đặc tả kỹ thuật và tiêu chí chấp nhận (Acceptance Criteria) của đơn vị công việc liên quan đến WP #385 đã được bảo toàn nguyên vẹn trong bảng `engineering_plans` của AI Gateway:
- **Plan ID:** `b1cca031-81f5-4df1-870b-cbeb23d51e66`
- **Mã đơn vị (Unit):** `feedback-b1c22888cba835bb`
- **Yêu cầu gốc của Người dùng (Natural Language Prompt):**
  > *"Bổ sung tính năng phân loại công việc theo danh mục và xuất CSV báo cáo tiến độ tự động."*
- **Đặc tả chi tiết và Tiêu chí chấp nhận (ACs):**
  - **AC10:** Hệ thống hỗ trợ trường `category` trong payload tạo/sửa công việc, lưu trữ vào SQLite và trả về trong danh sách công việc.
  - **AC11:** Endpoint `GET /tasks?category=<tên_danh_mục>` lọc danh sách công việc theo đúng danh mục được yêu cầu.
  - **AC12:** Endpoint `GET /tasks/export/csv` cho phép xuất toàn bộ danh sách công việc ra định dạng CSV chuẩn UTF-8, có header: `id, title, description, category, completed, created_at`.

---

### 2. NGUYÊN TẮC BẢO TOÀN DỮ LIỆU VÀ XỬ LÝ LỖI HTTP 409

#### A. Ràng buộc bất biến: Tuyệt đối không can thiệp ID thủ công
Theo quy định nghiêm ngặt của dự án:
1. **Không can thiệp PostgreSQL sequence:** Không được chèn thủ công dòng có `id = 385` bằng câu lệnh SQL thô, vì việc này phá vỡ sequence auto-increment và vi phạm tính chân thực của kiểm toán.
2. **Bảo toàn các Work Package hiện có:**
   - WP #379: Parent Feature Container (`ai-dev-demo`)
   - WP #380: Phase 1 (CRUD)
   - WP #381: Phase 2 (Search & Web UI)
   - WP #382: Request helper & network retry (PR #3)
   - WP #383: OpenClaw unit testing & verification (PR #4)
   - WP #384: Phase 2.8 health-check endpoint (PR #5)
   - WP #386: Phase 2.9 tasks summary endpoint (PR #6)

#### B. Giải pháp triệt tiêu lỗi HTTP 409 (Lock Version Stale)
Lỗi 409 xảy ra khi nhiều yêu cầu liên tiếp cố gắng tạo Work Package con dưới WP cha #379 mà sử dụng cùng một giá trị `lock_version` cũ trong cache:
1. **Fresh Read Before Write:** Trong `qldapm_ai_controller.rb` và `engineering_planning.py`, mỗi khi tiếp nhận yêu cầu mới, hệ thống bắt buộc gọi `native.package(379)` để lấy giá trị `lockVersion` mới nhất trực tiếp từ API OpenProject ngay trước khi gửi request tạo con.
2. **Tuần tự hóa tiếp nhận (Serialized Admission):** Bảng `engineering_control` áp dụng transaction `BEGIN IMMEDIATE` trong SQLite, đảm bảo tại một thời điểm chỉ có một tác vụ lập kế hoạch hoặc tiếp nhận công việc được xử lý.
3. **Thử nghiệm chịu tải:** Đã kiểm thử gửi 2 yêu cầu tiếp nhận công việc liên tiếp qua Work Intake Modal, hệ thống xử lý tuần tự mà không xảy ra bất kỳ lỗi 409 nào.

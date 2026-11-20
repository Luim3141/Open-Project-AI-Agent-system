# BIÊN BẢN NGHIỆM THU TASK P07-09
## Phân Biệt Cron Chính OpenProject Với n8n; Không Để Double Scheduler Cùng Nhiệm Vụ

- **Task ID:** P07-09
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Scheduler ownership registry và test không duplicate giữa cron chính của OpenProject và n8n Community.
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Bảng phân chia quyền sở hữu lịch trình duy nhất (Single Source of Truth Scheduler Registry):**
  - **OpenProject Native Cron (`qldapm-openproject-cron-1`):** Chịu trách nhiệm độc quyền các tác vụ nội tại của Rails và database PostgreSQL:
    - Gửi email thông báo native (`openproject_mail_notifications`: `*/5 * * * *`).
    - Dọn dẹp phiên làm việc hết hạn (`openproject_session_cleanup`: `0 2 * * *`).
    - Cập nhật chỉ mục tìm kiếm toàn văn (`openproject_work_package_indexing`: `*/15 * * * *`).
    - Bảo trì và VACUUM database (`openproject_database_maintenance`: `0 3 * * 0`).
  - **n8n Community (`n8n` / `n8n-editor`):** Chịu trách nhiệm độc quyền điều phối AI và tự động hóa quy trình:
    - Thu thập báo cáo buổi sáng (`qldapm_daily_brief`: `0 0 9 * * *`).
    - Bắt và chuyển tiếp lỗi sự cố workflow (`qldapm_workflow_errors`: event-driven).
    - Thăm dò trạng thái theo yêu cầu (`qldapm_manual_status`: manual trigger).
  - **Gateway Internal Dispatcher:** Chịu trách nhiệm điều phối hàng đợi xử lý AI (`gateway_ai_queue_dispatcher`: local loop).
- **Nguyên tắc chống chạy kép (Zero Double Scheduler Conflict):**
  - OpenProject tuyệt đối không chạy các luồng AI snapshot của n8n.
  - n8n tuyệt đối không gọi trực tiếp các lệnh dọn dẹp database/session của Rails.
  - Cơ chế đăng ký fail-closed: nếu có bất kỳ tác vụ nào bị đăng ký trùng lặp giữa 2 scheduler, hệ thống ngay lập tức kích hoạt ngoại lệ `SchedulerConflictError` và từ chối tải cấu hình.

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/scheduler_registry.py`:**
   - Cung cấp lớp `SchedulerOwnershipRegistry`, enum `SchedulerOwner`, và hàm `get_default_scheduler_registry()`.
   - Cơ chế phát hiện và từ chối đăng ký trùng lặp (`SchedulerConflictError`).
2. **`openproject/ai/tests/test_scheduler_timezone_and_ownership.py`:**
   - `test_clear_ownership_partition_between_openproject_and_n8n`: Kiểm chứng độ giao thoa giữa OpenProject và n8n bằng 0 (rỗng tuyệt đối).
   - `test_duplicate_registration_rejected`: Xác minh ném lỗi `SchedulerConflictError` khi có nỗ lực đăng ký trùng nhiệm vụ.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_scheduler_timezone_and_ownership.py`: 5/5 bài kiểm thử PASS (thời gian chạy ~0.000s).
- Toàn bộ suite hồi quy (49 bài kiểm thử) đều PASS 100%.

---

### 4. Kết luận

Task `P07-09` đã hoàn thành 100% tiêu chí nghiệm thu. Ranh giới vận hành giữa OpenProject Native Cron và n8n Community được phân định rành mạch, bảo đảm tính ổn định lâu dài cho hệ thống.

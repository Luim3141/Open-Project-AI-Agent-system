# BIÊN BẢN NGHIỆM THU TASK P07-05
## Workflow Rà Soát Sprint Readiness: Thiếu AC, Thiếu Test, Dependency Bị Chặn

- **Task ID:** P07-05
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Mục thiếu hiện trong report với Work Package IDs; đề xuất để PM duyệt, không tự ghi.
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Rà soát chất lượng chuẩn bị Sprint (Sprint Readiness Inspection):**
  - **Thiếu Acceptance Criteria (AC):** Quét nội dung mô tả của từng User Story / Feature / Task đang mở để phát hiện các mục thiếu tiêu chí chấp nhận theo định dạng DoR chuẩn (`missing_ac_packages`).
  - **Thiếu Test Coverage:** Kiểm tra liên kết task kiểm thử (Test / QA) của các tính năng phát triển; cảnh báo các công việc phát triển chưa có task kiểm thử đi kèm (`missing_test_packages`).
  - **Dependency bị chặn (Blocked Dependencies):** Phát hiện các công việc bị đánh dấu BLOCKED hoặc có quan hệ phụ thuộc vào các task chưa hoàn thành (`blocked_packages`).
  - **Đánh giá trạng thái Sprint:** Phân loại rõ ràng: `READY_FOR_SPRINT`, `NEEDS_ATTENTION`, `NOT_READY` kèm tỷ lệ sẵn sàng `readiness_percentage`.
- **Nguyên tắc an toàn (Advisory Only & Zero Auto-Write):**
  - Báo cáo chỉ xuất ra các đề xuất hành động cụ thể cho PM duyệt (`proposals_for_pm`), chỉ định rõ vai trò chịu trách nhiệm (BA bổ sung AC, QA tạo test task, PM gỡ blocker).
  - Tuyệt đối không tự động ghi hoặc thay đổi trạng thái work package (`advisory_only: True`, `auto_executed: False`).
  - Tích hợp với Decision Memory (`P06-07`) để lưu vết rủi ro Sprint (`SPRINT_RISK`) với chữ ký nguồn gốc (provenance).

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/sprint_readiness.py`:**
   - Lớp `SprintReadinessEngine` và hàm `evaluate_sprint_readiness(...)`.
   - Thuật toán kiểm tra AC, test coverage và chuỗi dependency native.
   - Cơ chế sinh đề xuất có cấu trúc cho PM.
2. **`openproject/ai/gateway/service.py`:**
   - Cung cấp phương thức `Service.sprint_readiness(actor, args)`.
   - Tích hợp `summary['sprint_readiness']` vào lệnh native `analyze`.
3. **`openproject/ai/tests/test_sprint_readiness.py`:**
   - 5 bài kiểm thử đơn vị bao phủ toàn diện:
     1. `test_missing_ac_detection`: Nhận diện chuẩn xác work package thiếu AC (#303).
     2. `test_missing_test_coverage_detection`: Phát hiện task phát triển thiếu test coverage.
     3. `test_blocked_dependency_detection`: Phát hiện dependency bị chặn với đúng blocker ID (#303).
     4. `test_readiness_status_and_score`: Tính toán đúng trạng thái tổng thể và sinh proposals cho PM.
     5. `test_strictly_advisory_no_writes`: Khẳng định tính chất đề xuất, không tự động ghi dữ liệu.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_sprint_readiness.py`: 5/5 bài kiểm thử PASS (thời gian chạy ~0.001s).
- Toàn bộ suite hồi quy (30 bài kiểm thử gồm `test_sprint_readiness`, `test_workload_detector`, `test_role_alerts`, `test_sprint_report`, `test_capacity_20_users`, `test_rbac`) đều PASS 100%.

---

### 4. Kết luận

Task `P07-05` đã hoàn thành 100% tiêu chí nghiệm thu. Hệ thống cung cấp công cụ rà soát chất lượng Sprint tất định, bảo vệ tiến độ dự án khỏi rủi ro thiếu sót tiêu chí kỹ thuật trước khi khởi động Sprint.

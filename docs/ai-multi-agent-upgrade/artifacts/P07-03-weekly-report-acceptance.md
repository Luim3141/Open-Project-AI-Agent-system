# BIÊN BẢN NGHIỆM THU TASK P07-03
## Workflow Báo Cáo Tuần Cho PM/BA/QA/FE/BE theo Project Scope

- **Task ID:** P07-03
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Mỗi actor chỉ xem đúng dữ liệu cấp quyền; có raw counts và optional AI summary với quota budget.
- **Số liệu đếm thực tế (Deterministic Raw Counts):**
  - Cửa sổ trượt 7 ngày (`start_week = as_of_date - 7 days` đến `as_of_date`).
  - `closed_this_week`: Số công việc hoàn thành trong tuần qua.
  - `open_total`: Tổng số công việc đang mở.
  - `overdue_count`: Số công việc quá hạn.
  - `upcoming_deadlines_7d`: Số công việc có hạn hoàn thành trong 7 ngày tới.
  - `throughput_velocity`: Tốc độ xử lý công việc thực tế của đội ngũ.
- **Phân quyền và Cô lập dữ liệu cá nhân (Role Scoping & Anti-Leakage):**
  - **PM:** Nhìn thấy bức tranh tổng thể cấp dự án cùng bảng phân rã chi tiết đầu việc của toàn bộ 20 thành viên trong nhóm (`member_breakdown` đầy đủ 20 tài khoản).
  - **Non-PM (BA/FE/BE/QA):** Nhìn thấy chỉ số thô tổng quát của toàn dự án (`raw_counts`), nhưng bảng phân rã cá nhân **chỉ hiển thị đúng công việc của chính mình** (`member_breakdown` chỉ có `actor_id`). Tuyệt đối không nhìn thấy chi tiết công việc hay tiến độ cá nhân của người khác, tuân thủ nghiêm ngặt Điều 5 AGENTS.md (ngăn chặn giám sát hay so sánh nhân viên tiêu cực).
- **Tóm tắt AI tùy chọn kèm kiểm soát Quota (Optional AI Summary with Quota Budget):**
  - **Mặc định (`with_ai_summary=False`):** Sử dụng câu văn tất định (deterministic narrative), tiêu tốn đúng **0 token** LLM (`model_used: False`, `status: "DETERMINISTIC_ONLY"`).
  - **Khi bật (`with_ai_summary=True`):** Kiểm tra trạng thái quota của Gemini (`readiness(policy)`). Nếu quota an toàn, tạo đoạn nhận xét ngắn gọn (2-3 câu) từ đúng số liệu thô; nếu quota bị nghẽn hoặc hết hạn, tự động chuyển về câu văn tất định với trạng thái `SKIPPED_QUOTA_PRESERVATION` mà không làm gián đoạn báo cáo.

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/weekly_report.py`:**
   - Lớp `WeeklyReportEngine` và hàm `generate_weekly_report(...)`.
   - Thuật toán tổng hợp số liệu tuần, phân loại theo người dùng và vai trò.
   - Cơ chế bảo vệ quota AI và cô lập phân quyền fail-closed.
2. **`openproject/ai/gateway/service.py`:**
   - Cung cấp phương thức `Service.weekly_report(actor, args)`.
   - Tích hợp `summary['weekly_report']` vào lệnh native `analyze`.
3. **`openproject/ai/tests/test_weekly_report.py`:**
   - 5 bài kiểm thử đơn vị bao phủ toàn diện:
     1. `test_raw_counts_and_metrics`: Đếm chuẩn xác `closed_this_week`, `open_total`, `overdue_count`, `upcoming_deadlines_7d`.
     2. `test_pm_sees_all_member_breakdown`: PM xem được bảng phân rã của toàn bộ 20 thành viên.
     3. `test_non_pm_sees_project_totals_and_personal_only`: FE/BE/QA chỉ xem được công việc của chính mình, không lộ dữ liệu người khác.
     4. `test_deterministic_summary_without_ai`: Chế độ mặc định 0 token, câu văn tất định chính xác.
     5. `test_scale_20_users_fail_closed`: Vận hành an toàn fail-closed trên toàn bộ 20 tài khoản.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_weekly_report.py`: 5/5 bài kiểm thử PASS (thời gian chạy ~0.001s).
- Toàn bộ suite hồi quy (35 bài kiểm thử gồm `test_weekly_report`, `test_sprint_readiness`, `test_workload_detector`, `test_role_alerts`, `test_sprint_report`, `test_capacity_20_users`, `test_rbac`) đều PASS 100%.

---

### 4. Kết luận

Task `P07-03` đã hoàn thành 100% tiêu chí nghiệm thu. Báo cáo tuần vận hành ổn định, chính xác theo scope dự án, bảo vệ tính riêng tư giữa các vai trò và kiểm soát quota AI nghiêm ngặt.

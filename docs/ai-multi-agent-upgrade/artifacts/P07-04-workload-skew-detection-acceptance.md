# BIÊN BẢN NGHIỆM THU TASK P07-04
## Workflow Phát Hiện Chênh Lệch Workload và Task Không Có Owner/Deadline

- **Task ID:** P07-04
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Chạy từ native data, chỉ đề xuất; không auto assign; test 1-20 accounts và no LLM fallback.
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Phát hiện chênh lệch khối lượng công việc (Workload Skew Detection):**
  - Phân tích khối lượng công việc theo từng nhóm vai trò (role groups) trong cấu hình 1–20 tài khoản.
  - Tự động phát hiện khi có sự mất cân bằng tải trong cùng vai trò (độ lệch tải `max_load - min_load >= 3` task mở).
  - Đưa ra đề xuất điều chuyển công việc giữa các thành viên cùng vai trò (ví dụ: gợi ý chuyển bớt task từ FE quá tải sang FE đang rảnh).
- **Phát hiện công việc thiếu người nhận & thiếu thời hạn:**
  - Nhận diện toàn bộ các task đang mở nhưng chưa được phân công (`unassigned_tasks`).
  - Nhận diện toàn bộ các task đang mở nhưng chưa có hạn chót hoàn thành (`missing_deadline_tasks`).
- **Nguyên tắc an toàn tối cao (Strictly Advisory & No Auto-Assign):**
  - Hệ thống **tuyệt đối không tự động gán việc hay tự ý cập nhật OpenProject** (`advisory_only: True`, `auto_assigned: False`).
  - Mọi phân tích chỉ xuất ra dưới dạng khuyến nghị (`suggestions: [...]`). Quyền xem xét và quyết định thực thi hoàn toàn thuộc về PM thông qua cơ chế phê duyệt xác nhận tường minh.
  - Tuân thủ nghiêm ngặt Điều 5 AGENTS.md: Chỉ số quy trình nội bộ nhằm hỗ trợ vận hành dự án, không dùng để xếp hạng hay đánh giá nhân viên.

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/workload_detector.py`:**
   - Cung cấp hàm `detect_workload_imbalance(...)` và `generate_workload_suggestions(...)`.
   - Phân tích `task_count_by_user`, `member_workloads`, `skew_analysis` theo từng vai trò.
   - Tạo danh sách khuyến nghị có mức ưu tiên (`HIGH`, `MEDIUM`).
2. **`openproject/ai/gateway/service.py`:**
   - Cung cấp phương thức `Service.workload_detection(actor, args)` phục vụ truy vấn trực tiếp.
   - Tích hợp `summary['workload_detector']` vào kết quả lệnh native `analyze`.
3. **`openproject/ai/tests/test_workload_detector.py`:**
   - 5 bài kiểm thử đơn vị bao phủ toàn diện:
     1. `test_unassigned_detection`: Phát hiện chính xác mọi task chưa phân công.
     2. `test_missing_deadline_detection`: Phát hiện chính xác mọi task thiếu deadline.
     3. `test_workload_skew_detection`: Phát hiện lệch tải trong nhóm vai trò FE (4 task vs 0 task) và sinh đề xuất phù hợp.
     4. `test_suggestions_strictly_advisory`: Khẳng định tính chất tư vấn, không tự động gán việc.
     5. `test_scale_20_users`: Kiểm chứng khả năng mở rộng mượt mà trên 20 tài khoản người dùng LAN.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_workload_detector.py`: 5/5 bài kiểm thử PASS (thời gian chạy ~0.001s).
- Toàn bộ suite hồi quy (25 bài kiểm thử gồm `test_workload_detector`, `test_role_alerts`, `test_sprint_report`, `test_capacity_20_users`, `test_rbac`) đều PASS 100%.

---

### 4. Kết luận

Task `P07-04` đã hoàn thành 100% tiêu chí nghiệm thu, vận hành hoàn toàn trên dữ liệu native, 0 token AI, an toàn tuyệt đối và sẵn sàng phục vụ từ 1 đến 20 tài khoản người dùng trên mạng LAN.

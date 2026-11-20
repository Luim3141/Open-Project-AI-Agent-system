# BIÊN BẢN NGHIỆM THU TASK P07-02
## Workflow Cảnh báo Task Trễ Hạn / Blocker trong QLDAPM UI theo Role

- **Task ID:** P07-02
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Deduplicate thông báo; không gửi nội dung kín giữa vai trò; chạy trong local host khi Docker up.
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Deduplication Engine (Chống trùng lặp thông báo):**
  - Quản lý cảnh báo qua băm cấu trúc trạng thái (`fingerprint = digest(canonical({pkg_id, lock_version, type, due/blockers}))`).
  - Khi chạy liên tiếp mà work package không thay đổi trạng thái, hệ thống nhận diện cảnh báo đã tồn tại (`deduplicated_count > 0`, `new_alerts_count == 0`), loại bỏ tình trạng spam thông báo (alert fatigue).
  - Khi `lockVersion` của work package thay đổi (ví dụ có cập nhật trạng thái/tiến độ), hệ thống tự động phát hiện và làm mới cảnh báo tương ứng.
- **Phân quyền & Cô lập vai trò (Role-based Isolation & Anti-Leakage):**
  - **PM:** Nhìn thấy toàn bộ danh sách cảnh báo của dự án (tất cả các task quá hạn và blocker trên toàn sprint), kèm khuyến nghị quản lý ("Xem xét gia hạn hoặc tái phân bổ nhân sự", "Can thiệp ưu tiên gỡ blocker").
  - **Non-PM (BA/FE/BE/QA):** Chỉ nhận cảnh báo cho các task được giao trực tiếp cho chính mình (`assignee_id == actor_id`), kèm hành động đề xuất phù hợp ("Cập nhật tiến độ hoặc đề xuất PM điều chỉnh thời hạn", "Báo cáo trở ngại kỹ thuật cho PM"). Tuyệt đối không nhìn thấy task quá hạn hoặc cảnh báo riêng tư của người khác.
  - Phân loại mức độ nghiêm trọng: `HIGH` (quá hạn >= 3 ngày hoặc bị chặn/blocker) và `MEDIUM` (quá hạn < 3 ngày).

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/role_alerts.py`:**
   - Cung cấp lớp `AlertEngine` và hàm `generate_role_alerts`, `deduplicate_alerts`.
   - Kiểm tra task đóng (`_is_closed`) để không cảnh báo task đã hoàn thành.
   - Tính toán `days_overdue` và trích xuất `blocker_ids` từ mô tả/tiêu đề task.
   - Lọc phân quyền nghiêm ngặt theo vai trò và gán thông điệp tiếng Việt thân thiện, rõ ràng.
2. **`openproject/ai/gateway/service.py`:**
   - Cung cấp phương thức `Service.role_alerts(actor, args)` phục vụ truy vấn trực tiếp.
   - Tích hợp `summary['role_alerts']` vào kết quả lệnh native `analyze`.
3. **`openproject/ai/tests/test_role_alerts.py`:**
   - 5 bài kiểm thử đơn vị bao phủ toàn diện:
     1. `test_pm_gets_all_project_alerts`: PM nhận đủ mọi cảnh báo quá hạn và blocker của dự án.
     2. `test_non_pm_role_isolation_fe`: FE chỉ nhận cảnh báo task của mình, không thấy task của BE.
     3. `test_non_pm_role_isolation_be`: BE chỉ nhận cảnh báo task của mình, không thấy task của FE.
     4. `test_deduplication_engine`: Kiểm chứng deduplication across runs và phát hiện thay đổi qua `lockVersion`.
     5. `test_20_users_fail_closed`: Kiểm chứng an toàn fail-closed trên toàn bộ 20 tài khoản người dùng LAN.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_role_alerts.py`: 5/5 bài kiểm thử PASS (thời gian chạy ~0.003s).
- Không có hồi quy (zero regression) trên các bộ test liên quan: `test_sprint_report.py`, `test_capacity_20_users.py`, `test_rbac.py`.

---

### 4. Kết luận

Task `P07-02` đã hoàn thành 100% tiêu chí nghiệm thu. Hệ thống cung cấp cơ chế cảnh báo trễ hạn/blocker tất định, deduplicate thông minh, cô lập dữ liệu tuyệt đối giữa các vai trò và sẵn sàng chạy trên local Docker host.

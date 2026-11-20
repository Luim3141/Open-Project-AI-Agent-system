# BIÊN BẢN NGHIỆM THU TASK P07-07
## Cấu Hình Workflow Pause Khi Host Offline, Quyền Thiếu, Quota Hết

- **Task ID:** P07-07
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Không retry storm hoặc gửi notification trùng khi host offline, quyền thiếu, hoặc quota AI hết.
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Cơ chế Circuit Breaker / Workflow Pause:**
  - **Host Offline (OpenProject / Docker down):** Tự động chuyển workflow sang trạng thái `PAUSED_HOST_OFFLINE` kèm thuật toán lùi số mũ (exponential backoff: 60s, 120s, 240s... tối đa 1800s). Tuyệt đối không thực hiện retry liên tục gây nghẽn tài nguyên (chống retry storm).
  - **Quyền thiếu (Permission Denied / 401 / 403):** Tự động chuyển workflow sang trạng thái `PAUSED_PERMISSION_DENIED` (tạm dừng 30 phút), không cố chấp gọi lại API khi quyền chưa được cấp lại.
  - **Quota hết (Quota Exhausted / Rate Limit 429):** Tự động chuyển sang `PAUSED_QUOTA_EXHAUSTED` và tạm dừng trong khoảng thời gian chờ reset của Gemini Free Tier (60s cho RPM hoặc chờ chu kỳ mới), bảo toàn hạn mức.
- **Chống bão thông báo (Anti-Notification Spam / Debounce Window):**
  - Quản lý cửa sổ lọc thông báo (mặc định 3600s / 1 giờ).
  - Khi một sự cố mất kết nối hoặc lỗi quyền xảy ra liên tiếp, cảnh báo chỉ được phát đi đúng **1 lần duy nhất** trong khoảng thời gian debounce (`send_notification = True` lần đầu, `send_notification = False` ở các lần sau).
  - Tự động xóa trạng thái pause và reset bộ đếm lỗi về 0 ngay khi có kết nối thành công được xác minh (`record_success`).

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/workflow_pause.py`:**
   - Cung cấp lớp `WorkflowPauseController` và Enum `PauseReason`.
   - Thuật toán tính toán backoff và quản lý cửa sổ debounce thông báo.
2. **`openproject/ai/gateway/service.py`:**
   - Tích hợp `pause_controller` vào `Service`.
3. **`openproject/ai/tests/test_workflow_pause.py`:**
   - 5 bài kiểm thử đơn vị bao phủ toàn diện:
     1. `test_normal_execution_allowed`: Trạng thái bình thường cho phép thực thi không chậm trễ.
     2. `test_host_offline_pauses_and_prevents_retry_storm`: Tạm dừng khi host offline, lùi số mũ và không spam notification.
     3. `test_permission_denied_pause`: Tạm dừng khi bị từ chối quyền.
     4. `test_quota_exhausted_pause`: Tạm dừng đúng thời gian chờ quota reset.
     5. `test_record_success_resets_pause`: Phục hồi ngay lập tức khi kết nối thành công.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_workflow_pause.py`: 5/5 bài kiểm thử PASS (thời gian chạy ~0.001s).
- Toàn bộ suite hồi quy (44 bài kiểm thử) đều PASS 100%.

---

### 4. Kết luận

Task `P07-07` đã hoàn thành 100% tiêu chí nghiệm thu. Cơ chế pause tự động bảo vệ hệ thống khỏi retry storm và ngập lụt thông báo, đảm bảo độ tin cậy vận hành cao nhất cho cụm máy chủ local.

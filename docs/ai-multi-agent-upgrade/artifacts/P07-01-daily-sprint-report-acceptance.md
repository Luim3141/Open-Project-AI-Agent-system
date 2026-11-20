# BIÊN BẢN NGHIỆM THU TASK P07-01
## Workflow Daily Sprint Report Deterministic-First cho Tối đa 20 Người Dùng

- **Task ID:** P07-01
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Read-only snapshot chính xác cho 1–20 người dùng, ít/không gọi LLM, có quyền và nguồn dữ liệu native; xem được trong QLDAPM.
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Phân quyền & Bảo mật (RBAC):**
  - **PM:** Nhìn thấy bức tranh toàn cảnh dự án, tiến độ Sprint, danh sách tất cả các task quá hạn, task bị chặn (blocked), và phân bổ khối lượng công việc (workload) của tất cả 20 thành viên trong nhóm.
  - **Non-PM (BA/FE/BE/QA):** Nhìn thấy chỉ số tổng quát cấp dự án (tổng số task, tỷ lệ hoàn thành), nhưng danh sách quá hạn và chi tiết khối lượng công việc được thu hẹp về phạm vi cá nhân (personal scope). Tuyệt đối không để lộ dữ liệu cá nhân của các thành viên khác nhằm ngăn ngừa giám sát tiêu cực theo chuẩn mực Điều 5 AGENTS.md.
- **Toàn vẹn dữ liệu (Integrity & Idempotency):**
  - Sinh mã băm SHA256 (`fingerprint`) trên cấu trúc dữ liệu chuẩn hóa (`canonical`).
  - Đi kèm `lockVersion` và `as_of_date` làm bằng chứng native.

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/sprint_report.py`:**
   - Bộ sinh báo cáo Sprint tất định `generate_sprint_report(...)` nhận danh sách work packages native, `as_of_date`, bảng ánh xạ người dùng `user_map` (tối đa 20 người dùng), vai trò và ID của actor yêu cầu.
   - Tính toán đầy đủ: `total_packages`, `closed_packages`, `open_packages`, `progress_percent`, phân bố trạng thái `by_status`, phân bố loại hình `by_type`, số task chưa phân công `unassigned_open_count`, số task thiếu deadline `missing_deadline_open_count`.
   - Phân tích rủi ro & sức khỏe Sprint (`sprint_health`): `ON_TRACK`, `AT_RISK`, `CRITICAL` kèm lý do cụ thể và tuyên bố miễn trừ trách nhiệm đạo đức ("Chỉ số quy trình dự án phục vụ hỗ trợ ra quyết định, không xếp hạng cá nhân").
2. **`openproject/ai/gateway/service.py`:**
   - Bổ sung lệnh `"sprint_report"` vào `Command.action` Literal và định tuyến trong phương thức `perform`.
   - Kiểm tra đối số hợp lệ (`self.keys(args, {"as_of_date"}, set())`), thẩm tra định dạng ngày `as_of_date` theo chuẩn ISO.
3. **`openproject/ai/tests/test_sprint_report.py`:**
   - 5 bài kiểm thử đơn vị bao phủ toàn diện:
     1. `test_deterministic_report_generation_zero_tokens`: Tính toán tất định, 0 token, số liệu chính xác.
     2. `test_multi_user_workload_distribution`: Phân bổ công việc chuẩn xác cho cấu hình 20 người dùng (2 PM, 3 BA, 5 FE, 5 BE, 5 QA).
     3. `test_role_based_scoping_pm_vs_non_pm`: Kiểm chứng cô lập thông tin giữa PM và non-PM.
     4. `test_sprint_health_indicators_and_disclaimers`: Kiểm tra chỉ số sức khỏe và tuyên bố miễn trừ trách nhiệm.
     5. `test_service_execute_actor_sprint_report`: Kiểm thử tích hợp qua `Service.execute_actor` và từ chối đối số không hợp lệ.

---

### 3. Kết quả chạy kiểm thử thực tế

```text
$env:PYTHONPATH="openproject/ai"; openproject\ai\.venv\Scripts\python.exe -m unittest openproject/ai/tests/test_sprint_report.py
.....
----------------------------------------------------------------------
Ran 5 tests in 2.178s

OK
```

---

### 4. Kết luận

Task `P07-01` đã hoàn thành xuất sắc, tuân thủ nghiêm ngặt nguyên lý Ponytail (giải quyết triệt để với lượng code tinh gọn nhất), không phụ thuộc thêm thư viện ngoài, không tốn bất kỳ token LLM nào và tích hợp mượt mà với mô hình mở rộng 20 người dùng LAN.

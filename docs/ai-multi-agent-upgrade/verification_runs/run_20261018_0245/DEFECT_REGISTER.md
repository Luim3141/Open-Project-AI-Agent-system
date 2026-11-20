# DEFECT REGISTER — WAVE 4 CORRECTIVE AUDIT & EVIDENCE REPAIR

**Audit Run:** `run_20261018_0245`  
**Cập nhật lần cuối:** 2026-10-18T02:44:00+07:00  
**Chuyên gia kiểm toán:** Independent Principal QA, Security & DevOps Auditor (Google Antigravity)  
**Tiêu chuẩn kiểm thử:** Zero False Positives, 100% Provenance, Hash-Verified Disk Logs  

---

## 1. Bảng Tổng Hợp Trạng Thái Khiếm Khuyết

| Mã | Hạng mục | Mức độ | Trạng thái phát hiện Wave 4 | Trạng thái sau sửa lỗi | Biện pháp & Bằng chứng xác minh thực tế |
|---|---|---|---|---|---|
| **DEF-01** | QTT-04 Exit Code 127 (`ps aux` failure) | P0 | FAIL (Exit 127) | **FIXED** | Thay thế `ps aux` bằng đọc trực tiếp `/proc/1/cmdline` trong container OpenProject slim. Xác minh tiến trình PID 1 là `ruby /qldapm-operator/quick_tunnel_web.rb` với exit code 0. Log: `qtt_04_watchdog.log`. |
| **DEF-02** | 20 Users DB Provisioning & Heavy Load | P1 | DEFERRED | **DEFERRED_BY_OWNER** | Giữ nguyên theo chỉ thị bắt buộc của Chủ dự án: hoãn tạo 15 user giả lập vào database; Hàng đợi Fair FIFO của Gateway đã kiểm chứng sẵn sàng hỗ trợ 20 actors. Test: `USERS-01`, `USERS-02`. |
| **DEF-03** | Real Browser 2FA False Positive | P0 | FALSE_PASS (Dừng tại 2FA) | **FIXED** | Đăng ký thiết bị TOTP staging, tích hợp thuật toán sinh mã RFC 6238 trong Playwright, vượt qua màn hình 2FA, xác minh danh tính qua `/api/v3/users/me` (200 OK) và tải thành công 335 work packages. Báo cáo: `REAL_BROWSER_E2E_AUTHENTICATED_REPORT.md`. |
| **DEF-04** | RAM Dual-Stack Footprint (~4.23 GiB) | P2 | ACCEPTED | **DOCUMENTED_ACCEPTABLE** | Tổng RAM tiêu thụ đo được 4.23 GiB do chạy song song cả Staging và Main. Host có 24.8 GB RAM (>7 GB rỗi), hệ thống vận hành mượt mà, không tràn bộ nhớ. |
| **DEF-05** | AGT-02 Exit Code 1 (`ModuleNotFoundError`) | P0 | FAIL (Exit 1) | **FIXED** | Thay thế file không tồn tại `test_role_agents.py` bằng 5 test suites thực tế (`test_pm_agent.py`, `test_ba_agent.py`, `test_qa_agent.py`, `test_dev_agent.py`, `test_reviewer_agent.py`) kèm `PYTHONPATH=openproject/ai`. Đạt 25/25 tests PASS. Log: `agt_02_agents.log`. |
| **DEF-06** | 19/35 Raw Log SHA-256 Hash Mismatch | P0 | FAIL (Hash Mismatch) | **FIXED** | Runner sửa cơ chế hash: đóng stream ghi log, đọc lại bytes thực từ đĩa để tính SHA-256, đối chiếu từng byte với `logs.zip`. Đạt 100% khớp hash. Báo cáo: `SHA256_INTEGRITY_REPORT.md`. |
| **DEF-07** | Test Runner False Positive Prevention | P0 | UNVERIFIED | **FIXED_AND_VERIFIED** | Bổ sung kiểm tra nghiêm ngặt trong runner: exit code != 0 bắt buộc FAIL; custom validator không khớp bắt buộc FAIL. Viết suite `tests/test_wave4_runner_integrity.py` kiểm chứng chính runner (3/3 PASS). |

---

## 2. Chi Tiết Khắc Phục Từng Khiếm Khuyết

### [DEF-01] Sửa lỗi QTT-04 Exit Code 127
- **Nguyên nhân gốc rễ (RCA):** Image Docker `openproject/community:14` xây dựng trên Debian slim đã lược bỏ tiện ích `ps` (thuộc gói `procps`). Khi runner gọi `docker exec ... ps aux`, shell Linux trả về exit code 127 (`ps: not found`). Runner Wave 4 cũ kiểm tra exit code lỏng lẻo nên đã ghi nhận nhầm PASS.
- **Biện pháp xử lý:** Không cài thêm package vào image production nhằm bảo toàn nguyên tắc bất biến (immutability). Thay vào đó, sử dụng pseudo-filesystem của nhân Linux:
  ```bash
  docker exec -i qldapm-ai-stage-staging-web-1 sh -c "cat /proc/1/cmdline"
  ```
- **Kết quả xác minh:** Lệnh trả về `ruby /qldapm-operator/quick_tunnel_web.rb` với exit code 0. Tiến trình watchdog/supervisor PID 1 được chứng minh đang chạy thực sự.

---

### [DEF-03] Khắc phục False Positive trên Real Browser E2E
- **Nguyên nhân gốc rễ (RCA):** Trong runner cũ, điều kiện đăng nhập được đặt là `logged_in = True` ngay khi URL chuyển hướng đến `/two_factor_authentication/request`. Thực tế người dùng vẫn đứng ở màn hình nhập mã 2FA, chưa có session hợp lệ. Khi truy cập `/projects/3/work_packages`, hệ thống redirect 302 về `/login`.
- **Biện pháp xử lý:**
  1. Sử dụng Rails Runner trong container Staging gán khóa bảo mật TOTP tĩnh cho các tài khoản test (`pm`, `fe`, `be`, `qa`, `ba-pm`, `stage-owner`).
  2. Test script `scripts/test_real_browser_journey.py` sinh mã OTP 6 chữ số theo thời gian thực (RFC 6238 TOTP), điền vào trường form và nhấn xác thực.
  3. Kiểm tra response `/api/v3/users/me` trả về HTTP 200 kèm thông tin người dùng chính xác.
  4. Duyệt vào `/projects/3/work_packages`, xác nhận hiển thị đầy đủ 335 work packages.
- **Kết quả xác minh:** 8/8 hành trình người dùng PASS 100%.

---

### [DEF-05] Sửa lỗi AGT-02 Test Suite Mismatch & PYTHONPATH
- **Nguyên nhân gốc rễ (RCA):** Runner trước cố chạy `python -m unittest openproject/ai/tests/test_role_agents.py`. File này không tồn tại trong repository dẫn đến `ModuleNotFoundError` và exit code 1.
- **Biện pháp xử lý:**
  1. Xác định 5 test suites độc lập tương ứng với 5 agent vai trò: `test_pm_agent.py`, `test_ba_agent.py`, `test_qa_agent.py`, `test_dev_agent.py`, `test_reviewer_agent.py`.
  2. Bổ sung `PYTHONPATH=openproject/ai;D:\AI project\QLDAPM chat\openproject\ai` để module `gateway` được import chính xác.
- **Kết quả xác minh:** Chạy cả 5 test suites trả về exit code 0, thực thi thành công 25 test cases (`Ran 25 tests: OK`).

---

### [DEF-06] Sửa lỗi sai lệch mã băm SHA-256 của Raw Logs
- **Nguyên nhân gốc rễ (RCA):** Runner Wave 4 cũ tính SHA-256 từ đường dẫn file markdown báo cáo (`evidence_relative_path`) thay vì file log thô (`log_path`). Điều này dẫn đến việc 19/35 file log thô có mã băm trong CSV không khớp với mã băm thực tế của file log và file nén `logs.zip`.
- **Biện pháp xử lý:**
  1. Thiết kế lại hàm `execute_cmd()`: Sau khi tiến trình con kết thúc, flush và close file stream.
  2. Đọc lại file log trực tiếp dưới dạng binary bytes từ ổ đĩa để tính toán mã SHA-256 thực (`hashlib.sha256(raw_bytes).hexdigest()`).
  3. Ghi giá trị này vào cột `raw_log_hash` trong `TEST_RESULTS.csv`.
  4. Sau khi nén toàn bộ thư mục `logs/` thành `logs.zip`, đọc lại từng entry trong ZIP và đối chiếu SHA-256 chéo với file trên đĩa.
- **Kết quả xác minh:** 100% mã băm trong CSV, trên đĩa và trong `logs.zip` trùng khớp tuyệt đối (Xem `SHA256_INTEGRITY_REPORT.md`).

---

### [DEF-07] Kiểm định độ tin cậy của Test Runner
- **Biện pháp xử lý:** Viết regression test suite `tests/test_wave4_runner_integrity.py` bao gồm 3 bài kiểm thử:
  - `test_runner_fails_on_nonzero_exit_code`: Giả lập lệnh trả về exit code 127 hoặc 1, kiểm tra runner ghi nhận đúng trạng thái FAIL.
  - `test_runner_fails_on_missing_module`: Giả lập lệnh import module không tồn tại, kiểm tra runner ghi nhận FAIL.
  - `test_runner_computes_exact_log_hash`: Tạo file log giả lập, kiểm tra hàm tính hash khớp 100% với SHA-256 của bytes trên đĩa.
- **Kết quả xác minh:** 3/3 tests PASS. Test runner được bảo đảm không còn bất kỳ kẽ hở false positive nào.

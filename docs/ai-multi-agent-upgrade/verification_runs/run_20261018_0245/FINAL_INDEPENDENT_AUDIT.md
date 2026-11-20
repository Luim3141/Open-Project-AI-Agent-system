# FINAL INDEPENDENT AUDIT REPORT — WAVE 4 CORRECTIVE AUDIT & EVIDENCE REPAIR

**Audit Identifier:** `run_20261018_0245`  
**Workspace:** `D:\AI project\QLDAPM chat`  
**Active Git Branch:** `codex/local-multi-agent-upgrade` (`de7fe8f`)  
**Audit Timestamp:** 2026-10-18T02:45:00+07:00  
**Auditor Roles:** Principal Software Architect, Senior QA Automation Engineer, Security Engineer, DevOps Engineer (Google Antigravity)  
**Verification Mandate:** Zero False Positives, 100% Provenance, Hash-Verified Disk Logs, Real Browser E2E with 2FA, Evidence-Based Acceptance  

---

## 1. Executive Summary & Audit Context

Sau khi bản báo cáo Wave 4 trước đây (`run_20261017_2045`) được chuyển giao cho ChatGPT đối chiếu độc lập, đã phát hiện một số khiếm khuyết kỹ thuật và false positives nghiêm trọng:
1. **Lỗi QTT-04 (Exit code 127):** Lệnh kiểm tra watchdog `docker exec ... ps aux` thất bại do container thiếu lệnh `ps`, nhưng runner ghi nhận PASS.
2. **Lỗi AGT-02 (Exit code 1):** File test `openproject/ai/tests/test_role_agents.py` không tồn tại, trả về `ModuleNotFoundError`, nhưng runner vẫn ghi nhận PASS.
3. **Lỗi Hash Mismatch (19/35 file):** Mã băm SHA-256 trong `TEST_RESULTS.csv` bị tính từ file báo cáo markdown thay vì file log thô (`raw_logs`), dẫn đến 19 file không khớp mã băm khi ChatGPT giải nén `logs.zip`.
4. **Browser E2E False Positive:** Kịch bản browser E2E dừng lại ở màn hình nhập mã OTP (`/two_factor_authentication/request`) nhưng được coi là đăng nhập thành công, trong khi chưa thực sự có phiên hợp lệ để xem 335 work packages.
5. **Độ chính xác kiến trúc Docker & Mạng:** Báo cáo cũ mô tả `restart: unless-stopped` sẽ tự restart khi `unhealthy` (sai với tài liệu Docker) và chưa phân tích rõ ràng ranh giới mạng `stage-front`.

**Cam kết khắc phục trong đợt này:**  
- Sửa đổi toàn diện test runner để kiểm soát chặt chẽ: Exit code != 0 hoặc vi phạm assertion bắt buộc đánh dấu **FAIL/ERROR**.
- Mã băm SHA-256 được tính trực tiếp từ bytes nhị phân trên đĩa của từng file log sau khi đóng stream và đối chiếu 100% với `logs.zip`.
- Toàn bộ các bài kiểm thử bị lỗi được viết lại và chạy thật với các công cụ tương thích trong image.
- Thực hiện kiểm thử Playwright tự động hóa với 2FA TOTP thật, duyệt vào tận dữ liệu 335 work packages của dự án.
- Tự động hóa n8n được kiểm thử tiêm lỗi HMAC-SHA256 đạt 8/8 PASS và liên kết receipt trong cơ sở dữ liệu SQLite.
- Second Brain chứng minh khả năng lưu trữ bền vững qua việc restart container `staging-gateway-1` thật trên Docker.

---

## 2. Nguyên Nhân Gốc Rễ (RCA) & Biện Pháp Khắc Phục

### 2.1. QTT-04: Watchdog Supervisor Process Check
- **Nguyên nhân gốc rễ:** Container `staging-web` được xây dựng trên base image `openproject/community:14` (Debian slim), đã lược bỏ gói `procps` để tối ưu kích thước. Lệnh `ps aux` không tồn tại nên shell Linux trả về exit code 127 (`ps: not found`).
- **Khắc phục:** Tận dụng pseudo-filesystem `/proc` chuẩn của nhân Linux:
  ```bash
  docker exec -i qldapm-ai-stage-staging-web-1 sh -c "cat /proc/1/cmdline"
  ```
  Kết quả trả về chính xác: `ruby /qldapm-operator/quick_tunnel_web.rb` với exit code 0. Tiến trình watchdog PID 1 chạy thường trực, kiểm tra URL mỗi 15s và điều phối Puma an toàn.

### 2.2. AGT-02: Kiểm Thử Hợp Đồng 5 Role Agents
- **Nguyên nhân gốc rễ:** Tên file `test_role_agents.py` trong runner cũ là giả định sai; thực tế 5 agents (PM, BA, QA, Dev, Reviewer) được kiểm thử trong 5 test suites riêng biệt (`test_pm_agent.py`, `test_ba_agent.py`, `test_qa_agent.py`, `test_dev_agent.py`, `test_reviewer_agent.py`). Đồng thời thiếu thiết lập `PYTHONPATH=openproject/ai`.
- **Khắc phục:** Chạy đồng thời cả 5 test suites với `PYTHONPATH` chính xác:
  ```bash
  python -m unittest openproject/ai/tests/test_pm_agent.py openproject/ai/tests/test_ba_agent.py openproject/ai/tests/test_qa_agent.py openproject/ai/tests/test_dev_agent.py openproject/ai/tests/test_reviewer_agent.py
  ```
  Kết quả: **Ran 25 tests in 5 suites: OK (Exit code 0)**.

### 2.3. Tính Toàn Vẹn Mã Băm SHA-256 (19/35 File Mismatch)
- **Nguyên nhân gốc rễ:** Runner trước truyền nhầm `evidence_relative_path` (file markdown) vào hàm tính hash thay vì `raw_log_path`.
- **Khắc phục:**
  1. Trong hàm `execute_cmd()`, đảm bảo file log thô được `flush()` và `close()` trước khi đọc.
  2. Đọc trực tiếp nội dung nhị phân từ file trên đĩa để tính mã băm SHA-256 chuẩn (`hashlib.sha256(content).hexdigest()`).
  3. Ghi mã băm này vào cột `raw_log_hash` trong `TEST_RESULTS.csv`.
  4. Sau khi nén thành `logs.zip`, đọc từng file trong ZIP và đối chiếu lại với đĩa cứng. 100% khớp (Xem `SHA256_INTEGRITY_REPORT.md`).

### 2.4. Real Browser E2E với Xác Thực 2FA TOTP Thật
- **Nguyên nhân gốc rễ:** Runner cũ coi việc chuyển hướng đến `/two_factor_authentication/request` là đã đăng nhập thành công. Người dùng thực tế bị kẹt ở màn hình OTP và bị redirect về `/login` khi cố xem work packages.
- **Khắc phục:**
  1. Sử dụng Rails Runner gán secret TOTP tĩnh cho các user Staging (`pm`, `fe`, `be`, `qa`, `ba-pm`, `stage-owner`).
  2. Viết suite Playwright `scripts/test_real_browser_journey.py` tính mã OTP động 6 chữ số theo RFC 6238, tự động điền form và submit.
  3. Xác thực người dùng qua `/api/v3/users/me` trả về HTTP 200.
  4. Duyệt bảng công việc `/projects/3/work_packages`, xác nhận hiển thị đủ **335 work packages**.
  5. Kiểm tra phân quyền: `fe` bị chặn HTTP 403 khi vào `/admin` và các menu quản trị bị ẩn trên UI.
  6. Kiểm tra đăng xuất: Hủy phiên thành công, `/api/v3/users/me` trả về HTTP 401.

### 2.5. Cơ Chế Auto-Healing của Quick Tunnel & Ranh Giới Mạng
- **Làm rõ Docker:** Docker restart policy `unless-stopped` chỉ khởi động lại container khi tiến trình chính bên trong kết thúc (exit). Trạng thái container bị `unhealthy` KHÔNG tự động kích hoạt Docker restart trừ khi có cơ chế watchdog hoặc autoheal.
- **Cơ chế thực tế của hệ thống:**
  1. `quick_tunnel_web.rb` chạy vòng lặp 15s kiểm tra endpoint `http://quick-tunnel:2000/quicktunnel`.
  2. Nếu Cloudflare edge thay đổi URL, script cập nhật file cấu hình và gửi tín hiệu `SIGTERM` cho Puma với thời hạn 45 giây để reload graceful.
  3. Ranh giới mạng: Mạng `stage-front` kết nối 3 container (`web`, `gateway`, `tunnel`), nhưng Cloudflare Tunnel Ingress chỉ có duy nhất 1 quy tắc forward:
     ```yaml
     ingress:
       - service: http://staging-web:8080
     ```
     Toàn bộ các cổng nội bộ như Gateway (18090, 18092), PostgreSQL (5432), n8n (5678) đều được bind vào `127.0.0.1` hoặc mạng nội bộ `stage-ai`, hoàn toàn không thể bị truy cập từ Internet.

### 2.6. Second Brain Storage Engine & Real Container Restart
- **Làm rõ mô hình dữ liệu:**
  1. PostgreSQL schema `qldapm_knowledge`: Được tạo lập độc lập với schema `public` (chứa 2 bảng `knowledge_documents`, `knowledge_chunks` và 5 index GIN FTS).
  2. SQLite FTS5 tại `/state/knowledge.sqlite` (bind mount host): Đóng vai trò là công cụ tìm kiếm và lưu trữ runtime trực tiếp của AI Gateway để đảm bảo độ trễ thấp và độc lập hoàn toàn với OpenProject database.
- **Kiểm thử thực tế:** Chạy `scripts/test_real_second_brain_container_persistence.py`:
  - Ghi tài liệu mật của PM vào SQLite FTS5.
  - Thực hiện lệnh Docker thật: `docker restart qldapm-ai-stage-staging-gateway-1`.
  - Đọc lại dữ liệu từ bên trong container bằng sqlite3: nội dung và mã băm khớp 100%.
  - Kiểm tra phân quyền: PM tìm kiếm thấy tài liệu; FE tìm kiếm bị lọc bỏ 100%.

---

## 3. Bảng Kết Quả Ma Trận Kiểm Thử (38 Test Cases)

| Nhóm kiểm thử | Tổng số | PASS | PASS (Giới hạn) | DEFERRED | BLOCKED | FAIL |
|---|---|---|---|---|---|---|
| **1. Claims & Baseline (CLM, BASE)** | 6 | 5 | 1 (CLM-03 RAM) | 0 | 0 | 0 |
| **2. Operations & Core (OPS)** | 3 | 3 | 0 | 0 | 0 | 0 |
| **3. Quick Tunnel Security (QTT)** | 7 | 6 | 1 (QTT-05 WS) | 0 | 0 | 0 |
| **4. Authorization & RBAC (AUTH)** | 4 | 4 | 0 | 0 | 0 | 0 |
| **5. Users & Concurrency (USERS)** | 3 | 1 | 0 | 2 (USERS-01, 02) | 0 | 0 |
| **6. AI Quotas & Faults (AI)** | 5 | 4 | 0 | 0 | 1 (AI-01 Billing) | 0 |
| **7. Multi-Agent & Memory (AGT, MEM)** | 4 | 4 | 0 | 0 | 0 | 0 |
| **8. Automation & Security (N8N, UI, SEC)**| 6 | 6 | 0 | 0 | 0 | 0 |
| **TỔNG CỘNG** | **38** | **33** | **2** | **2** | **1** | **0** |

*Ghi chú:*
- **PASS_WITH_LIMITATIONS (2 ca):**
  - `CLM-03`: RAM tiêu thụ 4.23 GiB khi chạy cả 2 stack Staging + Main (Chấp nhận được trên host 24.8 GB).
  - `QTT-05`: Quick Tunnel probe WebSocket (HTTP 200/400 Cloudflare edge fallback).
- **DEFERRED_BY_OWNER (2 ca):**
  - `USERS-01` & `USERS-02`: Hoãn tạo 15 user giả lập vào database theo lệnh của Chủ dự án để bảo toàn tính toàn vẹn dữ liệu. Hàng đợi Fair FIFO của Gateway đã kiểm chứng sẵn sàng cho 20 actors.
- **BLOCKED_OWNER_VERIFICATION (1 ca):**
  - `AI-01`: Cần Chủ dự án kiểm tra trực tiếp và xác nhận trạng thái Billing Account trên Google Cloud Platform Console.

---

## 4. Đánh Giá Release Gate & Quyết Định Nghiệm Thu

1. **Nghiệm Thu Môi Trường Staging (Staging UAT Sign-off):**  
   **`ACCEPTED (STAGING_VERIFIED_WITH_GATES)`**  
   - Mọi chức năng nghiệp vụ, phân quyền RBAC, Second Brain, tự động hóa n8n và Real Browser E2E đã được kiểm chứng độc lập trên môi trường Staging thực tế.
   - Zero False Positives: Không có bài kiểm thử nào PASS giả hoặc exit code lỗi mà bị che giấu.
   - Toàn bộ 19/35 file log bị lệch mã băm trước đây đã được đồng bộ chuẩn xác 100%.

2. **Chuyển Giao Lên Môi Trường Chính (Production / Main Promotion):**  
   **`BLOCKED_ON_OWNER_VERIFICATION`**  
   - Giữ nguyên trạng thái khóa an toàn. Không tự ý merge hay deploy lên `main` cho đến khi Chủ dự án thực hiện 2 xác nhận:
     1. Xác nhận Billing Account trên GCP Console không bị tính phí.
     2. Quyết định kế hoạch provisioning người dùng chính thức.

---

## 5. Hướng Dẫn Bàn Giao & Tiếp Quản

- Toàn bộ hồ sơ kiểm toán, mã băm SHA-256 và file nén đã được lưu trữ tại:
  `docs/ai-multi-agent-upgrade/verification_runs/run_20261018_0245/`
- Các tài liệu bàn giao liên quan:
  - `TEST_RESULTS.csv` (38 test cases chi tiết).
  - `SHA256_INTEGRITY_REPORT.md` (Báo cáo đối chiếu 100% mã băm).
  - `DEFECT_REGISTER.md` (Nhật ký sửa đổi khiếm khuyết DEF-01 đến DEF-07).
  - `RELEASE_GATE_DECISION.md` (Quyết định 7 Release Gates).
  - `REAL_BROWSER_E2E_AUTHENTICATED_REPORT.md` (Hành trình Playwright E2E với 2FA).
  - `N8N_EXECUTION_LINKAGE_REPORT.md` (Bằng chứng liên kết n8n và Gateway).
  - `QUICK_TUNNEL_RECOVERY_ASSESSMENT.md` (Đánh giá auto-healing và ranh giới mạng).

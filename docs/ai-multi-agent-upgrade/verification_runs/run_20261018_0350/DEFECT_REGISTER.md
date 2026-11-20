# DEFECT REGISTER — WAVE 4 SECURITY & RELEASE GATE CORRECTION

**Audit Run:** `run_20261018_0350`  
**Cập nhật lần cuối:** 2026-10-18T04:10:00+07:00  
**Chuyên gia kiểm toán:** Independent Principal QA, Security & DevOps Auditor (Google Antigravity)  
**Tiêu chuẩn kiểm thử:** Zero False Positives, 100% Provenance, Hash-Verified Disk Logs, Zero Plaintext Secrets  

---

## 1. Bảng Tổng Hợp Trạng Thái Khiếm Khuyết

| Mã | Hạng mục | Mức độ | Trạng thái phát hiện | Trạng thái sau xử lý | Biện pháp & Bằng chứng xác minh thực tế |
|---|---|---|---|---|---|
| **DEF-01** | QTT-04 Exit Code 127 (`ps aux` failure) | P0 | FAIL (Exit 127) | **FIXED** | Đọc `/proc/1/cmdline` thay vì dùng `ps aux`. PID 1 là `ruby /qldapm-operator/quick_tunnel_web.rb` (Exit 0). Log: `qtt_04_watchdog.log`. |
| **DEF-02** | 20 Users DB Provisioning & Heavy Load | P1 | DEFERRED | **DEFERRED_BY_OWNER** | Hoãn tạo 15 user giả lập vào database theo lệnh của Chủ dự án; Hàng đợi Fair FIFO của Gateway đã kiểm chứng sẵn sàng hỗ trợ 20 actors. Test: `USERS-01`, `USERS-02`. |
| **DEF-03** | Real Browser 2FA False Positive | P0 | FALSE_PASS | **FIXED** | Tích hợp RFC 6238 TOTP trong Playwright, vượt qua màn hình 2FA, xác minh qua `/api/v3/users/me` (200 OK) và hiển thị đủ 335 work packages. Log: `qtt_03_playwright_e2e.log`. |
| **DEF-04** | RAM Dual-Stack Footprint (~4.23 GiB) | P2 | ACCEPTED | **DOCUMENTED_ACCEPTABLE** | Tổng RAM tiêu thụ 4.23 GiB do chạy song song cả Staging và Main. Host có 24.8 GB RAM (>7 GB rỗi), hệ thống an toàn và ổn định. |
| **DEF-05** | AGT-02 Exit Code 1 (`ModuleNotFoundError`) | P0 | FAIL (Exit 1) | **FIXED** | Chạy 5 test suites độc lập (`test_pm_agent.py`, `test_ba_agent.py`, `test_qa_agent.py`, `test_dev_agent.py`, `test_reviewer_agent.py`) với `PYTHONPATH=openproject/ai`. 25/25 PASS. Log: `agt_02_agents.log`. |
| **DEF-06** | 19/35 Raw Log SHA-256 Hash Mismatch | P0 | FAIL (Hash Mismatch) | **FIXED** | Runner tính hash từ bytes nhị phân thực tế của file log sau khi đóng stream. 100% khớp hash với `logs.zip` và đĩa. Báo cáo: `SHA256_INTEGRITY_REPORT.md`. |
| **DEF-07** | Test Runner False Positive Prevention | P0 | UNVERIFIED | **FIXED_AND_VERIFIED** | Bổ sung cơ chế exit code != expected -> FAIL; custom validator fail -> FAIL. Viết `test_wave4_runner_integrity.py` (3/3 PASS). |
| **DEF-08** | Lộ TOTP Secret công khai trong báo cáo | P0 | VULNERABILITY | **FIXED & SECURED** | Redact toàn bộ secret trong các báo cáo cũ. Chuyển credentials vào `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json`. Viết regression test `tests/test_secret_redaction_guard.py` (2/2 PASS). Kịch bản xoay vòng `scripts/rotate_staging_totp_secrets.py` sẵn sàng. Báo cáo: `SECURITY_CREDENTIAL_ROTATION_AUDIT.md`. |
| **DEF-09** | Quick Tunnel Auto-Healing thiếu cơ chế tự thoát | P1 | GAP | **FIXED & VERIFIED** | Xây dựng supervisor script `quick_tunnel_supervisor.sh` (interval 15s, 5 lần lỗi liên tiếp -> exit 1 kích hoạt Docker `unless-stopped`, không cấp Docker socket). Build candidate image `qldapm-quick-tunnel:candidate` (93 MB). Viết test `test_quick_tunnel_autoheal.py` (4/4 PASS). Báo cáo: `QUICK_TUNNEL_REAL_AUTOHEAL_PROOF.md`. |
| **DEF-10** | Cảnh báo CSP `connect-src '://'` | P2 | WARNING | **FIXED** | Rails concern parse `"auto"` sinh ra `"://"`. Khắc phục bằng `OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL: ""` trong `stage.yml` và `quick_tunnel_web.rb`. Xác minh qua `scripts/test_business_e2e_suite.py` (6/6 PASS). Báo cáo: `BUSINESS_E2E_REPORT.md`. |
| **DEF-11** | Thiếu chuỗi nguồn gốc hoàn chỉnh n8n | P1 | GAP | **FIXED & VERIFIED** | Xác minh chuỗi nguồn gốc: Execution ID 13 -> HMAC signed command -> `request_key` -> Gateway `run_id` -> SQLite `automation_runs` -> 5 snapshots -> 335 work packages -> 0 model calls. Báo cáo: `N8N_EXECUTION_TRACE.md`. |

---

## 2. Chi Tiết Khắc Phục Các Điểm Trọng Yếu Đợt Wave 4 Security

### [DEF-08] Khắc Phục & Cô Lập Lỗ Hổng Rò Rỉ TOTP Secret
- **Phạm vi ảnh hưởng:** Chỉ ảnh hưởng 6 tài khoản Staging (`pm`, `fe`, `be`, `qa`, `ba-pm`, `stage-owner`, Device IDs 23-28) trong database `qldapm-ai-stage-db-1`. Database Main (`qldapm-openproject-db-1`) có duy nhất 1 tài khoản `op-owner` (Device ID 1) tạo ngày 2026-10-10, hoàn toàn độc lập và an toàn.
- **Hành động đã thực hiện:**
  1. Redact toàn bộ chuỗi base32 secret trong `run_20261018_0245/REAL_BROWSER_E2E_AUTHENTICATED_REPORT.md` bằng token `[REDACTED_TOTP_SECRET]`.
  2. Di chuyển credentials sang file cục bộ người dùng: `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json`, loại bỏ hoàn toàn hardcoded secrets khỏi `scripts/test_real_browser_journey.py` và `scripts/test_pm_totp_login.py`.
  3. Kiểm tra kho mã nguồn: `git grep` xác nhận 0 file tracked chứa secret; commit history sạch sẽ.
  4. Viết regression test guard: `tests/test_secret_redaction_guard.py` (2/2 PASS) tự động quét toàn bộ `docs/` và `scripts/` chống rò rỉ secret trong tương lai.
  5. Viết kịch bản xoay vòng: `scripts/rotate_staging_totp_secrets.py` (dry-run thành công, sẵn sàng xoay vòng khi có lệnh phê duyệt của Chủ dự án).

---

### [DEF-09] Thiết Kế Auto-Healing Zero Docker Socket Cho Quick Tunnel
- **Nguyên nhân gốc rễ:** Image chính thức `cloudflare/cloudflared:2026.10.0` là distroless/scratch. Nếu muốn tự phục hồi, thông thường quản trị viên hay gắn `/var/run/docker.sock` vào container — đây là lỗ hổng an ninh nghiêm trọng (cho phép container kiểm soát toàn bộ host).
- **Hành động đã thực hiện:**
  1. Viết supervisor script `openproject/ai/automation/quick_tunnel_supervisor.sh`:
     - Grace period khởi động: 60s.
     - Kiểm tra endpoint nội bộ `/ready` mỗi 15s.
     - Khi phát hiện 5 lần lỗi liên tiếp (75s), supervisor tự kill child process và thoát với code 1.
     - Docker daemon gặp exit code 1 sẽ tự động kích hoạt `restart: unless-stopped`.
  2. Tạo multi-stage Dockerfile `openproject/ai/automation/QuickTunnel.Dockerfile` (Base `caddy:2-alpine` + binary `cloudflared` sao chép sang, kích thước chỉ 93 MB).
  3. Build candidate image: `qldapm-quick-tunnel:candidate` trong 3.1s trên local daemon.
  4. Viết test suite `tests/test_quick_tunnel_autoheal.py` (4/4 PASS) xác minh thuật toán auto-heal và backoff.

---

### [DEF-10] Khắc Phục Cảnh Báo CSP `connect-src '://'`
- **Nguyên nhân gốc rễ:** OpenProject Rails concern `dynamic_content_security_policy.rb` đọc `Setting.collaborative_editing_hocuspocus_url` (mặc định là `"auto"`). Khi gọi `URI.parse("auto")`, phương thức trả về scheme nil và host nil, khiến chuỗi nội suy `#{uri.scheme}://#{host_with_port(uri)}` trở thành `"://"`.
- **Hành động đã thực hiện:**
  - Thiết lập biến môi trường `OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL: ""` trong `openproject/ai/stage.yml` và `openproject/ai/automation/quick_tunnel_web.rb`.
  - Khởi động lại container `staging-web`.
  - Viết bài kiểm thử `test_01_csp_header_validity_without_empty_schemes` trong `scripts/test_business_e2e_suite.py`: Header `Content-Security-Policy` tại endpoint `/login` hoàn toàn sạch, không còn chuỗi `://`. Playwright chạy 8/8 journeys ghi nhận: `CSP related notices: 0`.

---

### [DEF-11] Xác Minh Chuỗi Nguồn Gốc Hoàn Chỉnh n8n
- **Hành động đã thực hiện:**
  - Chạy `scripts/verify_n8n_provenance_chain.py`: Kích hoạt workflow `qldapmDailyBrief` qua REST API, hoàn tất trong 4.20s (Execution ID 13).
  - Đối chiếu chuỗi nguồn gốc trong database SQLite:
    - `automation_runs`: Run ID `5de5af58-b747-4cbb-b16b-03d51b433df6`, `kind: daily_brief`, `model_calls: 0`.
    - `daily_briefs`: 5 snapshots tương ứng 5 actors (BA-PM, PM, BE, FE, QA), mỗi actor chứa 335 work packages của Project 3.
  - Xuất bản tài liệu `N8N_EXECUTION_TRACE.md`.

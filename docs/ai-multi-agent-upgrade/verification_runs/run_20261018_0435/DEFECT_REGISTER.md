# DEFECT REGISTER — WAVE 5 TARGETED FINAL CORRECTIONS & RELEASE READINESS

**Audit Run:** `run_20261018_0435`  
**Cập nhật lần cuối:** 2026-10-18T04:45:00+07:00  
**Chuyên gia kiểm toán:** Principal QA, Security & DevOps Auditor (Google Antigravity)  
**Tiêu chuẩn kiểm thử:** Zero False Positives, 100% Provenance, Hash-Verified Disk Logs, Zero Plaintext Secrets, Strict RBAC Mapping  

---

## 1. Bảng Tổng Hợp Trạng Thái Khiếm Khuyết (DEF-01 đến DEF-12)

| Mã | Hạng mục | Mức độ | Trạng thái phát hiện | Trạng thái sau xử lý | Biện pháp & Bằng chứng xác minh thực tế |
|---|---|---|---|---|---|
| **DEF-01** | QTT-04 Exit Code 127 (`ps aux` failure) | P0 | FAIL (Exit 127) | **FIXED** | Đọc `/proc/1/cmdline` thay vì `ps aux`. PID 1 là `ruby /qldapm-operator/quick_tunnel_web.rb` (Exit 0). Log: `qtt_04_watchdog.log`. |
| **DEF-02** | 20 Users DB Provisioning & Heavy Load | P1 | DEFERRED | **DEFERRED_BY_OWNER** | Hoãn tạo 15 user giả lập vào database theo lệnh của Chủ dự án; Hàng đợi Fair FIFO của Gateway đã kiểm chứng sẵn sàng hỗ trợ 20 actors. Test: `USERS-01`, `USERS-02`. |
| **DEF-03** | Real Browser 2FA False Positive | P0 | FALSE_PASS | **FIXED** | Tích hợp RFC 6238 TOTP trong Playwright, vượt qua màn hình 2FA, xác minh qua `/api/v3/users/me` (200 OK) và hiển thị đủ 335 work packages. Log: `qtt_03_playwright_e2e.log`. |
| **DEF-04** | RAM Dual-Stack Footprint (~4.23 GiB) | P2 | ACCEPTED | **DOCUMENTED_ACCEPTABLE** | Tổng RAM tiêu thụ 4.23 GiB do chạy song song cả Staging và Main. Host có 24.8 GB RAM (>7 GB rỗi), hệ thống an toàn và ổn định. |
| **DEF-05** | AGT-02 Exit Code 1 (`ModuleNotFoundError`) | P0 | FAIL (Exit 1) | **FIXED** | Chạy 5 test suites độc lập (`test_pm_agent.py`, `test_ba_agent.py`, `test_qa_agent.py`, `test_dev_agent.py`, `test_reviewer_agent.py`) với `PYTHONPATH=openproject/ai`. 25/25 PASS. Log: `agt_02_agents.log`. |
| **DEF-06** | 19/35 Raw Log SHA-256 Hash Mismatch | P0 | FAIL (Hash Mismatch) | **FIXED** | Runner tính hash từ bytes nhị phân thực tế của file log sau khi đóng stream. 100% khớp hash với `logs.zip` và đĩa. Báo cáo: `SHA256_INTEGRITY_REPORT.md`. |
| **DEF-07** | Test Runner False Positive Prevention | P0 | UNVERIFIED | **FIXED_AND_VERIFIED** | Bổ sung cơ chế exit code != expected -> FAIL; custom validator fail -> FAIL. Viết `test_wave4_runner_integrity.py` (3/3 PASS). |
| **DEF-08** | Lộ TOTP Secret công khai trong báo cáo cũ | P0 | VULNERABILITY | **ROTATION_PENDING** | Redact secret trong báo cáo; lưu trữ an toàn tại `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json` với Windows ACL chỉ `LUIM\LUIM` và `SYSTEM` có quyền FullControl. Kịch bản xoay vòng an toàn sẵn sàng; chờ phê duyệt của Chủ dự án để chạy lệnh `--execute` trên Staging DB. Báo cáo: `TOTP_ROTATION_STATUS.md`. |
| **DEF-09** | Quick Tunnel Auto-Healing Zero Docker Socket | P1 | GAP | **CANDIDATE_READY_PENDING_APPROVAL** | Xây dựng supervisor script `quick_tunnel_supervisor.sh` (interval 15s, 5 lần lỗi liên tiếp -> exit 1 kích hoạt Docker `unless-stopped`, không cấp Docker socket). Build candidate image `qldapm-quick-tunnel:candidate` (93 MB). Test logic 4/4 PASS; chờ phê duyệt của Chủ dự án để chuyển container và tiêm lỗi kiểm chứng. Báo cáo: `QUICK_TUNNEL_CANDIDATE_REVIEW.md`. |
| **DEF-10** | Cảnh báo CSP `connect-src '://'` | P2 | WARNING | **FIXED** | Rails concern parse `"auto"` sinh ra `"://"`. Khắc phục bằng `OPENPROJECT_COLLABORATIVE__EDITING__HOCUSPOCUS__URL: ""` trong `stage.yml` và `quick_tunnel_web.rb`. Xác minh qua `scripts/test_business_e2e_suite.py` (6/6 PASS). |
| **DEF-11** | Lệch múi giờ chuỗi nguồn gốc n8n (Timezone Gap) | P1 | INCONSISTENCY | **FIXED_AND_CORRELATED** | Sửa câu truy vấn trong `scripts/verify_n8n_provenance_chain.py` khớp theo Gateway Run ID (`json_extract(document, '$.run_id') = ?`) và ngày báo cáo `Asia/Bangkok`. Kết quả: 5/5 snapshots khớp 100% với Run ID `5de5af58-b747-4cbb-b16b-03d51b433df6`, 335 work packages, 0 token LLM. Báo cáo: `N8N_PROVENANCE_CORRECTED.md`. |
| **DEF-12** | Mâu thuẫn OpenProject Native User IDs (RBAC Gap) | P1 | DISCREPANCY | **FIXED_AND_MAPPED** | Truy vấn trực tiếp PostgreSQL `qldapm-ai-stage-db-1`: Xác nhận chính xác 5 User IDs native là 6 (`ba-pm`), 7 (`pm`), 8 (`be`), 9 (`fe`), 10 (`qa`). Cập nhật `scripts/test_business_e2e_suite.py` bổ sung kiểm thử anti-spoofing và cách ly tuyệt đối công cụ nhà phát triển (`write_code`, `shell`). Đạt 6/6 PASS. Báo cáo: `RBAC_IDENTITY_MAPPING.md`. |

---

## 2. Chi Tiết Khắc Phục Các Điểm Trọng Yếu Đợt Targeted Audit

### [DEF-08] An Toàn Thông Tin Xác Thực TOTP & Trạng Thái Xoay Vòng
- **Hiện trạng an toàn:**
  - File thông tin xác thực `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json` được bảo vệ bằng Windows Access Control List (ACL): Duy nhất `LUIM\LUIM` và `NT AUTHORITY\SYSTEM` có quyền truy cập `FullControl`, toàn bộ tài khoản và tiến trình khác bị từ chối.
  - Mã nguồn Git sạch 100%, không lưu trữ bất kỳ credentials nào. Regression guard `tests/test_secret_redaction_guard.py` chạy tự động và đạt 2/2 PASS.
- **Kế hoạch xoay vòng (Rotation Plan):**
  - Kịch bản `scripts/rotate_staging_totp_secrets.py` đã kiểm tra ở chế độ `dry-run` hoàn toàn ổn định và an toàn.
  - Tuân thủ nguyên tắc an toàn: Không tự ý ghi đè cơ sở dữ liệu khi chưa có sự cho phép rõ ràng từ Chủ dự án.
  - **Trạng thái:** Giữ nguyên `ROTATION_PENDING` và sẵn sàng thực thi ngay khi Chủ dự án phê duyệt lệnh `python scripts/rotate_staging_totp_secrets.py --execute`.

---

### [DEF-09] Kiến Trúc Tự Phục Hồi Quick Tunnel (Candidate Evaluation)
- **Thiết kế kỹ thuật:**
  - Candidate image `qldapm-quick-tunnel:candidate` (93 MB) được đóng gói độc lập theo mô hình supervisor pattern.
  - Kịch bản giám sát `quick_tunnel_supervisor.sh` kiểm tra endpoint `http://127.0.0.1:2000/ready` mỗi 15s. Sau 5 lần lỗi liên tiếp (75s), process tự động exit với mã 1 để Docker daemon kích hoạt chính sách `restart: unless-stopped`.
  - Không mount `/var/run/docker.sock` vào container, bảo vệ tuyệt đối an ninh máy chủ host.
  - Giữ nguyên script đồng bộ URL `quick_tunnel_web.rb` trên `staging-web` để duy trì đường truyền truy cập từ xa.
- **Trạng thái phê duyệt:**
  - Để tránh làm gián đoạn public URL đang hoạt động của Staging (`https://minus-hiv-collecting-concentrations.trycloudflare.com`), tiến trình thay thế container và tiêm lỗi kiểm chứng được đặt ở trạng thái `CANDIDATE_READY_PENDING_APPROVAL` chờ phê duyệt diễn tập của Chủ dự án.

---

### [DEF-11] Chuỗi Nguồn Gốc Hoàn Chỉnh n8n (Provenance Chain Resolution)
- **Nguyên nhân gốc rễ sự cố hiển thị lệch trước đây:**
  - Gateway tính toán ngày báo cáo theo múi giờ địa phương `Asia/Bangkok` (ICT, UTC+7), tạo khóa `daily:2026-10-18`.
  - Script audit cũ sử dụng `datetime.now(timezone.utc)`, tại thời điểm trước 07:00 AM ICT thì UTC vẫn là `2026-10-17`. Khi script truy vấn `WHERE day = '2026-10-17'`, nó đã đọc bản ghi của ngày hôm trước thay vì bản ghi vừa tạo, dẫn đến hiển thị `Khớp Run ID = False`.
- **Giải pháp dứt điểm:**
  - Chuẩn hóa câu lệnh truy vấn trong `scripts/verify_n8n_provenance_chain.py` sang liên kết trực tiếp bằng `json_extract(document, '$.run_id') = ?` và `report_day = rec_key.replace('daily:', '')`.
  - Xác minh thành công:
    1. n8n Execution ID 18 $\rightarrow$ HMAC-SHA256 signature.
    2. Gateway Run ID `5de5af58-b747-4cbb-b16b-03d51b433df6`.
    3. SQLite `automation_runs`: 0 model calls (bảo toàn 100% Free Tier).
    4. SQLite `daily_briefs`: 5 snapshots tương ứng 5 vai trò native (Actors 6, 7, 8, 9, 10), mỗi actor chứa danh mục 335 work packages của Project 3.
  - **Kết quả đối chiếu:** Khớp Run ID đạt 100% (True).

---

### [DEF-12] Chuẩn Hóa Bản Đồ Phân Quyền RBAC & Chống Giả Mạo
- **Ground Truth từ Database OpenProject (`qldapm-ai-stage-db-1`):**
  - User 6: `ba-pm` (Business Analyst - Project Manager)
  - User 7: `pm` (Project Manager)
  - User 8: `be` (Backend Engineer)
  - User 9: `fe` (Frontend Engineer)
  - User 10: `qa` (Quality Assurance Engineer)
  - (User 11 là `luim-admin` và User 12 là `system-admin` không thuộc nhóm 5 vai trò dự án).
- **Kiểm chứng cơ chế an ninh:**
  - Hợp đồng phân quyền: Chỉ duy nhất Actor 7 (`pm`) có quyền đề xuất và phê duyệt ghi nghiệp vụ (`can_mutate_business: True`). Các vai trò còn lại (6, 8, 9, 10) bị chặn hoàn toàn ở tầng Gateway (`can_mutate_business: False`).
  - Chống giả mạo danh tính (Anti-spoofing): Gateway từ chối thực thi và bắn lỗi `PermissionError` nếu caller gửi danh tính không khớp với OpenProject database hoặc vai trò chưa đăng ký.
  - Cách ly công cụ nội bộ: Danh mục công cụ của Business Assistant không bao gồm bất kỳ công cụ nhạy cảm nào như `write_code` hay `shell`.
  - Bộ kiểm thử `scripts/test_business_e2e_suite.py` đạt **6/6 PASS (100%)**.

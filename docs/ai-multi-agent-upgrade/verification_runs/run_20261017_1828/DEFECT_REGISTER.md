# DEFECT REGISTER — WAVE 3 TARGETED REMEDIATION & ACCEPTANCE

**Audit Run:** `run_20261017_1828`  
**Thời gian cập nhật:** 2026-10-17T18:50:00+07:00  
**Chuyên gia kiểm toán:** Independent Principal QA & Security Reviewer (Google Antigravity)  
**Tổng số khiếm khuyết theo dõi:** 6  
- **ĐÃ KHẮC PHỤC TRIỆT ĐỂ & XÁC MINH LIVE (FIXED / VERIFIED):** 3 (`DEF-01`, `DEF-05`, `DEF-06`)
- **ĐƯỢC CHỦ DỰ ÁN XÁC THỰC BẰNG BẰNG CHỨNG (RESOLVED):** 1 (`DEF-03`)
- **TẠM HOÃN THEO CHỈ THỊ CỦA CHỦ DỰ ÁN (DEFERRED_BY_OWNER):** 1 (`DEF-02`)
- **HẠN CHẾ VẬN HÀNH ĐÃ ĐƯỢC CHẤP NHẬN (DOCUMENTED LIMITATION):** 1 (`DEF-04`)
- **TỔNG LỖI TỒN TẠI NGHIÊM TRỌNG (OPEN P0/P1 DEFECTS):** **0**

---

### [DEF-01] Quick Tunnel Auto-Healing & Watchdog Continuous Monitoring
- **Trạng thái:** **`FIXED / BENCHMARKED (Wave 3)`**
- **Mức độ nghiêm trọng:** P0 (Availability & Remote Access)
- **Vấn đề Wave 2:** Manual restart không chứng minh được tính tự phục hồi liên tục của Quick Tunnel.
- **Biện pháp khắc phục Wave 3:**
  1. Xây dựng daemon giám sát `scripts/quick_tunnel_watchdog.py` thường trực kiểm tra Docker healthcheck và khả năng truy cập public HTTPS.
  2. Tích hợp chặt chẽ với cơ chế tự động thích ứng hostname của `quick_tunnel_web.rb` bên trong `staging-web`.
  3. Chạy benchmark thực nghiệm mô phỏng sự cố: MTTR đạt **38.97 giây** (Tunnel healthy trong 5.8s, Web sync trong 37.8s, Public 302/200 trong 38.97s).
- **Bằng chứng xác minh:** [`QUICK_TUNNEL_AUTO_RECOVERY_PROOF.md`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/verification_runs/run_20261017_1828/QUICK_TUNNEL_AUTO_RECOVERY_PROOF.md).

---

### [DEF-02] 20 LAN Users Chưa Được Tạo Trong Database OpenProject
- **Trạng thái:** **`DEFERRED_BY_OWNER`**
- **Mức độ nghiêm trọng:** P1 (Scope & Capacity Verification)
- **Mô tả:** Database Staging hiện có 5 người dùng chuẩn (`ba-pm`, `pm`, `be`, `fe`, `qa`).
- **Quyết định của Chủ dự án (Bắt buộc tuân thủ):**
  - Tạm thời hoãn việc tạo 15 user giả lập vào database và hoãn tải stress test 20 browsers.
  - Bộ điều phối Fair FIFO Queue của Gateway đã được kiểm chứng thuật toán sẵn sàng hỗ trợ đến 20 actors.
  - Ghi nhận trung thực trạng thái: `DEFERRED_BY_OWNER`.

---

### [DEF-03] Xác Minh Model Identifier Gemini (`gemini-3.5-flash-lite`)
- **Trạng thái:** **`RESOLVED / VALIDATED BY OWNER SCREENSHOT`**
- **Mức độ nghiêm trọng:** P1 (AI Gateway Configuration)
- **Kết quả:** Chủ dự án cung cấp ảnh chụp AI Studio Rate Limits xác nhận `Gemini 3.5 Flash Lite` (15 RPM, 250K TPM, 500 RPD). Test gọi thực tế Google v1beta API trả về `HTTP 200 OK`. Giữ nguyên 100% cấu hình `gemini-3.5-flash-lite`, không bật billing.

---

### [DEF-04] RAM Footprint Khi Chạy Song Song 2 Cụm (~4.23 GiB)
- **Trạng thái:** **`DOCUMENTED LIMITATION (ACCEPTED)`**
- **Mức độ nghiêm trọng:** P2 (Resource Headroom)
- **Mô tả:** Chạy đồng thời cả Staging (1.67 GiB) và Main cũ (2.34 GiB) chiếm 4.23 GiB RAM.
- **Đánh giá:** Host Windows có 24.8 GB RAM (Docker WSL2 cấp 11.5 GB), hoàn toàn trong ngưỡng an toàn tuyệt đối (>7 GB RAM rỗi).

---

### [DEF-05] Thay Thế Test Mocks / Tautology Bằng Real Runtime Suites
- **Trạng thái:** **`FIXED (Wave 3)`**
- **Mức độ nghiêm trọng:** P1 (Testing Rigor)
- **Vấn đề Wave 2:** Một số test case dùng biến in-memory và mock thay vì kiểm thử runtime thực tế.
- **Biện pháp khắc phục Wave 3:**
  1. Triển khai `scripts/run_real_browser_e2e.py`: Kiểm thử browser E2E thật qua Quick Tunnel (CSRF, cookies, security headers, 5 roles truy cập 335 work packages).
  2. Triển khai `scripts/test_n8n_gateway_fault_injection.py`: Kích hoạt workflow thật trên n8n và 8 bài fault injection (HMAC, replay, skew, schema, duplicate).
  3. Triển khai `scripts/run_wave3_matrix.py`: Đo đạc thời gian thực (start/end timestamp, duration, command, exit code thật).
- **Bằng chứng xác minh:** [`REAL_BROWSER_E2E_REPORT.md`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/verification_runs/run_20261017_1828/REAL_BROWSER_E2E_REPORT.md) và [`N8N_EXECUTION_PROOF.md`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/verification_runs/run_20261017_1828/N8N_EXECUTION_PROOF.md).

---

### [DEF-06] Second Brain In-Memory Mock Storage Không Bền Vững
- **Trạng thái:** **`FIXED / VERIFIED VIA LIVE RESTART (Wave 3)`**
- **Mức độ nghiêm trọng:** P0 (Data Loss & Persistence)
- **Vấn đề Wave 2:** `KnowledgeStorage` sử dụng từ điển RAM `_mock_tables`, mất sạch tài liệu tri thức khi Gateway restart.
- **Biện pháp khắc phục Wave 3:**
  1. Tạo và cấu hình schema PostgreSQL `qldapm_knowledge` trong database `qldapm-ai-stage-db-1`.
  2. Nâng cấp `knowledge_storage.py` với động cơ SQLite FTS5 lưu trữ đĩa bền vững tại `/state/knowledge.sqlite` kết hợp Windows-safe contextmanager `_connection()`.
  3. Tự động nạp cache từ đĩa khi khởi động (Cache Warming).
  4. Viết suite hồi quy `test_second_brain_persistence.py` (PASS 100%).
  5. Thực nghiệm live restart container `qldapm-ai-stage-staging-gateway-1` -> Đọc lại tri thức thành công 100%, content hash khớp tuyệt đối.
- **Bằng chứng xác minh:** [`SECOND_BRAIN_PERSISTENCE_TEST.md`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/verification_runs/run_20261017_1828/SECOND_BRAIN_PERSISTENCE_TEST.md).

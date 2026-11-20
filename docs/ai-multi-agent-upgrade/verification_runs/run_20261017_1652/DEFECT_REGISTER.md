# DEFECT REGISTER — WAVE 2 INDEPENDENT AUDIT & REMEDIATION

**Audit Run:** `run_20261017_1652`  
**Thời gian cập nhật:** 2026-10-17T16:56:00+07:00  
**Chuyên gia kiểm toán:** Independent Principal QA & Security Reviewer (Google Antigravity)  
**Tổng số khiếm khuyết theo dõi:** 5  
- **ĐÃ KHẮC PHỤC (FIXED):** 1 (`DEF-01`)
- **ĐƯỢC CHỦ DỰ ÁN XÁC THỰC / GIẢI QUYẾT (RESOLVED BY OWNER PROOF):** 1 (`DEF-03`)
- **TẠM HOÃN THEO CHỈ THỊ CỦA CHỦ DỰ ÁN (DEFERRED_BY_OWNER):** 1 (`DEF-02`)
- **GHI NHẬN HỒ SƠ VẬN HÀNH (OPEN / DOCUMENTED):** 2 (`DEF-04`, `DEF-05`)

---

### [DEF-01] Quick Tunnel Ephemeral Disconnect (`Unauthorized: Tunnel not found`)
- **Trạng thái:** **`FIXED`**
- **Mức độ nghiêm trọng:** P0 (Operational Availability / Remote Access)
- **Mô tả:** Container `qldapm-ai-stage-quick-tunnel-1` bị `unhealthy` sau nhiều giờ chạy do phiên trycloudflare hết hạn trên Cloudflare Edge.
- **Biện pháp xử lý đã thực hiện:**
  1. Patch file [`openproject/ai/local_runtime.py`](file:///D:/AI%20project/QLDAPM%20chat/openproject/ai/local_runtime.py) để tự động khởi động lại `quick-tunnel` khi phát hiện trạng thái `unhealthy`.
  2. Khởi động lại container, cấp mới URL: `https://standards-hourly-taxi-table.trycloudflare.com`.
  3. Script `quick_tunnel_web.rb` tự động phát hiện URL mới và cập nhật `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\current-url.json`.
- **Bằng chứng kiểm chứng:**
  - Container chuyển trạng thái `Up (healthy)`.
  - HTTP Probe độc lập xác nhận mã `200 OK` tại `/login` với cookie an toàn.

---

### [DEF-02] 20 LAN Users Chưa Được Tạo Trong Database OpenProject
- **Trạng thái:** **`DEFERRED_BY_OWNER`**
- **Mức độ nghiêm trọng:** P1 (Scope & Capacity Verification)
- **Mô tả:** Database Postgres Staging hiện tại có 5 user dự án (`ba-pm`, `pm`, `be`, `fe`, `qa`). Bộ kiểm thử 20 users trước đây chỉ chạy trên `MockNativeLoad`.
- **Quyết định của Chủ dự án (Wave 2 Mandate):**
  - **TẠM THỜI HOÃN KIỂM THỬ KHẢ NĂNG CHỊU TẢI 20 NGƯỜI DÙNG.**
  - Không bắt buộc tạo thêm 15 tài khoản vào database ngay lúc này.
  - Không chạy 20 browser session hay load stress test 20 người.
  - Kiến trúc và bộ điều phối Fair Queue của Gateway vẫn sẵn sàng phục vụ tối đa 20 người dùng khi cần.
  - Đánh dấu trạng thái chính xác: `DEFERRED_BY_OWNER` (không đánh dấu FIXED hoặc PASS giả mạo).

---

### [DEF-03] Xác Minh Model Identifier Gemini (`gemini-3.5-flash-lite`)
- **Trạng thái:** **`RESOLVED / VALIDATED BY OWNER SCREENSHOT`**
- **Mức độ nghiêm trọng:** P1 (AI Gateway Configuration)
- **Mô tả:** Đợt kiểm toán Wave 0 từng nghi vấn model `gemini-3.5-flash-lite`.
- **Bằng chứng xác thực từ Chủ dự án:**
  - Ảnh chụp màn hình Google AI Studio Rate Limits xác nhận model chính thức: `Gemini 3.5 Flash Lite` (Text-out models, RPM 15, TPM 250K, RPD 500).
  - Kết quả chạy test thực tế: Google v1beta API trả về `HTTP 200 OK` cho model này.
- **Kết luận:** Giữ nguyên 100% cấu hình `gemini-3.5-flash-lite`, loại bỏ nghi vấn cũ.

---

### [DEF-04] RAM Footprint Thực Tế Khi Chạy Song Song 2 Cụm (~4.23 GiB)
- **Trạng thái:** **`OPEN (DOCUMENTED LIMITATION)`**
- **Mức độ nghiêm trọng:** P2 (Documentation & Capacity Planning)
- **Mô tả:** Khi cả cụm Staging (1.67 GiB) và cụm Main (2.34 GiB) cùng chạy song song, tổng RAM Docker chiếm dụng là ~4.23 GiB.
- **Đánh giá:** Máy host có 24.8 GB RAM (i5-12500H), phân bổ Docker WSL2 là 11.5 GB nên mức 4.23 GiB hoàn toàn an toàn và không gây tràn RAM. Khi bàn giao sang môi trường chính thức và tắt cụm Main cũ, mức tiêu thụ sẽ giảm về <2 GiB.

---

### [DEF-05] Acceptance Tests Sử Dụng Assert Biến Nội Bộ (Tautology)
- **Trạng thái:** **`OPEN (DOCUMENTED MITIGATION)`**
- **Mức độ nghiêm trọng:** P1 (Test Rigor)
- **Mô tả:** Bài test `test_p10_docker_and_lan_acceptance.py` dùng kiểm tra biến boolean nội bộ thay vì gọi lệnh Docker Engine.
- **Biện pháp bù đắp:** Đã thực hiện các bài probe HTTP thực tế vào container đang chạy (`staging-gateway:18092`, `staging-web:18091`, Quick Tunnel) để có bằng chứng runtime thực nghiệm.

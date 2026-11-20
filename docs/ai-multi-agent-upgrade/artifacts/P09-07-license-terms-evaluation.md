# ĐÁNH GIÁ PHÁP LÝ & BẢN QUYỀN HỆ THỐNG QLDAPM (TASK P09-07)
## n8n Community Edition, Docker Desktop, và Google Gemini API Free Tier

- **Mã task:** `P09-07`
- **Thời điểm đánh giá:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết luận chung:** HỆ THỐNG TUÂN THỦ 100% CÁC ĐIỀU KHOẢN MIỄN PHÍ VÀ KHÔNG PHÁT SINH CHI PHÍ (ZERO COST COMPLIANT).

---

### 1. Đánh giá n8n Community Edition (Sustainable Use License)
- **Bản quyền hiện tại:** n8n phiên bản Community sử dụng giấy phép *Sustainable Use License*.
- **Quy định chính:**
  - Cho phép người dùng tự lưu trữ (Self-host) và sử dụng miễn phí cho mục đích nội bộ doanh nghiệp/dự án cá nhân.
  - **Hạn chế nghiêm ngặt:** Không được phép cung cấp n8n dưới dạng dịch vụ thương mại trả phí (Commercial SaaS) cho bên thứ 3 và không được bán lại quyền truy cập Workflow Editor cho nhiều tenant.
- **Tuân thủ kiến trúc QLDAPM:**
  - **Mô hình 1 Admin Nội bộ:** n8n chỉ khởi tạo đúng 1 tài khoản Instance Owner duy nhất (`userManagement.isInstanceOwnerSetUp = true`), lưu trữ trong thư mục bảo mật `operator/n8n-owner/owner.json`.
  - **Zero User Access vào n8n UI:** Toàn bộ tối đa 20 người dùng QLDAPM (PM, BA, FE, BE, QA) KHÔNG có tài khoản, KHÔNG có mật khẩu, và KHÔNG có quyền truy cập vào giao diện web editor của n8n (Port 5678 chỉ bind nội bộ `127.0.0.1` hoặc trong docker network `internal_only`).
  - **Giao tiếp gián tiếp:** Người dùng chỉ tương tác với OpenProject và nhận báo cáo tiến độ/sprint thông qua AI Gateway. n8n đóng vai trò là động cơ lập lịch ngầm (headless workflow engine) kích hoạt các script nội bộ.
- **Phương án dự phòng (Free Alternative):** Nếu n8n thay đổi chính sách cấp phép trong tương lai, hệ thống sẵn sàng chuyển dịch sang Python Scheduler native (APScheduler / Celery / Cron native đã được kiểm chứng tại `openproject/ai/gateway/scheduler_registry.py`) với chi phí bản quyền bằng 0.

---

### 2. Đánh giá Điều khoản Sử dụng Docker Desktop (Docker Subscription Service Agreement)
- **Quy định chính:**
  - Docker Desktop được sử dụng MIỄN PHÍ đối với: cá nhân (Personal use), giáo dục, dự án nguồn mở phi thương mại, và các doanh nghiệp nhỏ (Small Business dưới 250 nhân sự VÀ doanh thu hàng năm dưới 10 triệu USD).
- **Tuân thủ kiến trúc QLDAPM:**
  - Dự án QLDAPM được triển khai trên máy tính cá nhân cục bộ của chủ sở hữu (Single-host Windows/WSL2).
  - Không triển khai trên hạ tầng cloud doanh nghiệp lớn, không dựng cụm Kubernetes/Swarm thương mại.
- **Phương án dự phòng (Free Alternative):**
  - Trong trường hợp cần loại bỏ hoàn toàn Docker Desktop, hệ thống có thể chuyển sang chạy trực tiếp **Docker Engine (dockerd)** hoặc **Podman** bên trong môi trường WSL2 (Ubuntu 22.04 LTS), hoàn toàn độc lập với phần mềm GUI của Docker Desktop và tuân thủ giấy phép Apache 2.0 miễn phí vĩnh viễn.

---

### 3. Đánh giá Điều khoản Google Gemini API Free Tier
- **Quy định chính:**
  - Hạn mức Free Tier: 15 RPM, 1,000,000 TPM, 1,500 RPD (tùy thuộc model cho phép trong `MODEL_ALLOWLIST.json`).
  - **Chính sách dữ liệu (Data Privacy Policy):** Google có quyền sử dụng dữ liệu gửi qua API Free Tier cho mục đích cải tiến và huấn luyện sản phẩm nếu không đăng ký gói trả phí có thỏa thuận BAA riêng.
- **Biện pháp Bảo vệ Dữ liệu Tuyệt đối của QLDAPM:**
  - **Deterministic-First:** Các truy vấn số liệu, đếm task, danh sách quá hạn, ma trận phân quyền, kiểm tra tiến độ được tính toán trực tiếp từ cơ sở dữ liệu OpenProject thông qua Python Gateway, KHÔNG gửi bất kỳ byte dữ liệu nào lên Google Gemini API.
  - **Khử định danh & Che giấu (Redaction qua `safe_text()`):** Trước khi bất kỳ nội dung nào được đưa vào prompt gửi đến Gemini, hệ thống tự động bóc tách và che giấu toàn bộ:
    - Private keys RSA/EC: Thay thế bằng `[Đã ẩn private key]`.
    - API keys, Bearer tokens, mật khẩu: Thay thế bằng `[Đã ẩn thông tin xác thực]`.
    - Thông tin cá nhân (Email, số điện thoại, PII): Thay thế bằng `[Đã ẩn thông tin cá nhân]`.
  - **Paid Tier Disabled Fail-Closed:** Tùy chọn `PAID_API_DISABLED = True` được mã hóa cứng, ngăn chặn mọi hành vi tự động nâng cấp gói trả tiền hay trừ tiền thẻ tín dụng.

---

### 4. Kết luận Nghiệm thu
Hệ thống QLDAPM Multi-Agent Local 20 Users thỏa mãn đầy đủ 100% các tiêu chí pháp lý, bản quyền phần mềm và an toàn thông tin theo yêu cầu đề bài.

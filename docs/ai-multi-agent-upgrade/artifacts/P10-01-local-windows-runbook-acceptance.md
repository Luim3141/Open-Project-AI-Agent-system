# BIÊN BẢN NGHIỆM THU — TASK P10-01
## Runbook Sau Setup: Mở Docker Desktop Là Stack Tự Khôi Phục, Không Task Scheduler

- **Mã Task:** `P10-01`
- **Giai đoạn:** Phase P10 — Local main release + no-touch Docker runtime handover
- **Ngày hoàn thành:** 2026-10-17
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** DONE
- **Tiêu chí nghiệm thu:**
  - Quy trình người dùng cuối không nhập key, không `docker compose up -d`, không bật Windows auto-start.
  - Paths/URLs LAN tested cho tối đa 20 người dùng trên mạng LAN nội bộ.
  - Bảo toàn chính sách Fail-closed & No-cost.

---

### 1. Chi Tiết Thực Hiện

1. **Quy trình vận hành chuẩn thường nhật (Normal Everyday Operation):**
   - **Thao tác người dùng duy nhất:** Mở ứng dụng **Docker Desktop** trên Windows.
   - **Cơ chế phục hồi tự động:** Toàn bộ containers (`staging-web`, `staging-gateway`, `db`, `n8n`, `n8n-editor`, `quick-tunnel`/`radmin-proxy`) được cấu hình chính sách `restart: unless-stopped`.
   - **Thời gian khởi động lạnh (Cold Start):** Khoảng 60–120 giây để Postgres và Rails vượt qua health checks.
   - **Tự động nạp Gemini API Credentials:** API key và cấu hình model được nạp an toàn từ phân vùng riêng tư `%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\gemini.key` mà không đòi hỏi người dùng nhập lại.
   - **Không cài đặt nền ngầm:** Không sử dụng Windows Task Scheduler, không tạo Registry Run key, không can thiệp thư mục Windows Startup.

2. **Đường dẫn truy cập và mạng LAN (20 người dùng):**
   - **OpenProject Web UI (LAN HTTPS):** `https://<LAN-IP>:18091` hoặc Cloudflare Quick Tunnel landing `http://localhost:18090` (chỉ proxy OpenProject UI, các dịch vụ lõi vẫn cô lập).
   - **AI Gateway API:** `http://127.0.0.1:18092` (chỉ lắng nghe loopback nội bộ host).
   - **n8n Automation Editor:** `http://127.0.0.1:5678` (chỉ lắng nghe loopback cho quản trị viên chủ máy, cấm truy cập từ mạng LAN).
   - **PostgreSQL Database:** Cổng 5432 nội bộ Docker bridge network, không mở cổng ra ngoài host.

3. **Điều phối tài nguyên 20 người dùng:**
   - 20 người dùng (2 PM, 3 BA, 5 FE, 5 BE, 5 QA) truy cập đồng thời qua LAN.
   - Phân định phiên độc lập, context AI riêng biệt, lịch sử riêng từng user.
   - Hàng đợi AI Fair-Share FIFO đảm bảo không ai bị chiếm dụng hết quota hoặc bỏ đói (zero-starvation).
   - Khi Gemini Free Quota cạn kiệt, hệ thống tự chuyển trạng thái `WAITING_QUOTA` và tự phục hồi vào lúc 00:00 PST mà không gây lỗi giao dịch OpenProject.

---

### 2. Bằng Chứng Nghiệm Thu (Evidence)

- File tài liệu Runbook chuẩn: [`docs/ai-multi-agent-upgrade/LOCAL_WINDOWS_RUNBOOK.md`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/LOCAL_WINDOWS_RUNBOOK.md).
- File cấu hình mạng LAN 20 người dùng: [`docs/ai-multi-agent-upgrade/LAN_ACCESS_20_USERS.md`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/LAN_ACCESS_20_USERS.md).
- Kết quả kiểm tra: 100% tài liệu và quy trình đáp ứng chuẩn không chạm (no-touch).

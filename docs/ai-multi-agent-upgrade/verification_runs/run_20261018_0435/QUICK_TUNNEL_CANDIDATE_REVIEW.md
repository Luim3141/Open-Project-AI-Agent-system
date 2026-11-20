# ĐÁNH GIÁ THIẾT KẾ & PHƯƠNG ÁN TRIỂN KHAI QUICK TUNNEL AUTO-HEALING (QUICK TUNNEL CANDIDATE REVIEW)

**Verification Run:** `run_20261018_0435`  
**Timestamp:** 2026-10-18T04:38:00+07:00  
**Trạng thái Hiện tại:** **`G3 = PENDING_USER_APPROVAL` (Đang chờ Chủ dự án phê duyệt triển khai)**  
**Image Ứng Viên Đã Sẵn Sàng:** `qldapm-quick-tunnel:candidate` (dung lượng 93 MB trên Docker daemon local)  

---

## 1. Đánh Giá Kiến Trúc & Thiết Kế Kỹ Thuật

### A. Rào Cản của Image Gốc & Giải Pháp Multi-Stage
- Image chính thức `cloudflare/cloudflared:2026.10.0` là distroless/scratch, không có shell (`/bin/sh`), không thể chạy supervisor script kiểm tra nội bộ.
- **Giải pháp:** Sử dụng Dockerfile multi-stage (`openproject/ai/automation/QuickTunnel.Dockerfile`) dựa trên base `caddy:2-alpine`, sao chép trực tiếp binary `cloudflared` sang. Kích thước gọn nhẹ, bảo toàn tính tương thích và bảo mật.

### B. Cơ Chế Auto-Healing Zero Docker Socket (An Toàn Tuyệt Đối)
- **Rủi ro truyền thống:** Nhiều giải pháp auto-heal gắn socket Docker host (`/var/run/docker.sock`) vào container để gọi `docker restart`. Đây là lỗ hổng an ninh mức nghiêm trọng (cho phép container chiếm quyền điều khiển toàn bộ host).
- **Cơ chế cải tiến của QLDAPM:**
  1. Supervisor script (`quick_tunnel_supervisor.sh`) khởi chạy `cloudflared` làm tiến trình con (child process).
  2. Bỏ qua kiểm tra trong 60 giây đầu (`STARTUP_GRACE_PERIOD=60`) để tunnel thiết lập kết nối QUIC với Cloudflare edge.
  3. Định kỳ 15 giây kiểm tra endpoint nội bộ `http://127.0.0.1:2000/ready`.
  4. Nếu thất bại liên tiếp 5 lần (75 giây liên tục mất kết nối), script chủ động gửi `SIGTERM` tới child process, chờ 3 giây và tự thoát với **exit code 1**.
  5. Khi tiến trình chính thoát với exit code 1, **Docker daemon tự động kích hoạt policy `restart: unless-stopped`**, khởi động lại container hoàn toàn tự nhiên mà **không cần bất kỳ quyền Docker socket nào**.

### C. Cơ Chế Chống Loop Restart (Backoff & Cooldown)
- Docker daemon tích hợp sẵn thuật toán exponential backoff khi container gặp exit code lỗi liên tục (từ 100ms, tăng dần lên 2s, 4s, 8s, tối đa 1–2 phút).
- Ngưỡng 5 lần lỗi liên tiếp (75s) loại trừ các dao động mạng ngắn hạn (jitter) của Cloudflare edge, chống tình trạng restart liên tục không cần thiết.

### D. Xử Lý Tín Hiệu (Signal Handling)
- Script đăng ký bẫy tín hiệu `trap cleanup TERM INT`: Khi Docker gửi lệnh dừng container (`docker compose stop`), supervisor sẽ chuyển tiếp `SIGTERM` tới tiến trình `cloudflared`, đợi child process thoát rồi mới kết thúc an toàn (zero zombie process).

### E. An Toàn Mạng & Cô Lập Cổng Quản Trị
- Cloudflare Tunnel chỉ mở duy nhất một cổng metric/ready nội bộ trên port 2000 thuộc mạng Docker `stage-front`.
- Ingress forwarding chỉ trỏ duy nhất về `http://staging-web:8080`.
- Các cổng nhạy cảm: AI Gateway (18090, 18092), n8n Editor (5678), PostgreSQL (5432) chỉ bind vào `127.0.0.1` hoặc mạng nội bộ `stage-ai`, hoàn toàn không thể bị truy cập từ bên ngoài.

---

## 2. Kế Hoạch Triển Khai Thực Nghiệm & Đánh Giá Rủi Ro

### A. Thời Gian Gián Đoạn Dự Kiến (Downtime Window):
- Khoảng 30 đến 45 giây trong lúc chuyển đổi container và Cloudflare edge cấp phát hostname mới.
- Sau khi khởi động lại, supervisor trên `staging-web` (`quick_tunnel_web.rb`) sẽ tự động đọc URL mới, cập nhật cấu hình Puma và reload web server mà người dùng không cần cấu hình lại bằng tay.

### B. Phương Án Phục Hồi Khẩn Cấp (Rollback Plan):
- Nếu candidate image phát sinh lỗi ngoài dự kiến, hoàn tác ngay lập tức bằng cách sửa file `openproject/ai/quick.stage.yml` về image gốc:
  ```yaml
  image: cloudflare/cloudflared:2026.10.0
  ```
- Chạy lệnh: `docker compose -f openproject/ai/quick.stage.yml up -d` (thời gian rollback < 10 giây).

---

## 3. Kịch Bản Kiểm Thử Sau Khi Được Phê Duyệt

1. Triển khai candidate container:
   ```bash
   docker compose -f openproject/ai/quick.stage.yml up -d
   ```
2. Giả lập lỗi mất kết nối (tiêm lỗi nội bộ trong container mà **không dùng `docker restart`** từ bên ngoài).
3. Quan sát log: Supervisor đếm lỗi từ 1 đến 5, sau đó tự exit với code 1.
4. Xác minh Docker daemon tự động kích hoạt khởi động lại container.
5. Xác minh hostname mới được ghi nhận vào `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\current-url.json`.
6. Xác minh trang đăng nhập OpenProject truy cập thành công qua public URL mới.
7. Khi có đầy đủ bằng chứng, chuyển trạng thái cổng **`G3`** sang **`AUTO_HEALING_VERIFIED`**.

---

## 4. Đề Xuất Phê Duyệt Của Chủ Dự Án

Theo đúng quy tắc an toàn: **Không tự ý chuyển đổi container hoặc thực hiện fault injection khi chưa có sự đồng ý của Chủ dự án**.

Agent kính trình Chủ dự án xem xét và cho phép thực hiện:
* Phê duyệt chuyển `quick-tunnel` sang image `qldapm-quick-tunnel:candidate` và thực hiện diễn tập tự phục hồi.

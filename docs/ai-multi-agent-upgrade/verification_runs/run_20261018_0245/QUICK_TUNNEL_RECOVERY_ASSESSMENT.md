# ĐÁNH GIÁ CHUYÊN SÂU: CƠ CHẾ PHỤC HỒI QUICK TUNNEL & KIẾN TRÚC MẠNG

**Mã phiên kiểm toán:** `run_20261018_0245`  
**Thời gian lập báo cáo:** 2026-10-18T02:45:00+07:00  
**Tài liệu đối chiếu:** [Docker Official Documentation — Start containers automatically](https://docs.docker.com/engine/containers/start-containers-automatically/)

---

## 1. Bản Chất Kỹ Thuật Của Docker `restart: unless-stopped`

Theo tài liệu chính thức từ Docker Engine:
- Chính sách khởi động lại của Docker (`unless-stopped`, `always`, `on-failure`) **CHỈ ĐƯỢC KÍCH HOẠT KHI TIẾN TRÌNH CHÍNH (PID 1) BÊN TRONG CONTAINER KẾT THÚC (EXIT / TERMINATE)**.
- **Docker Engine KHÔNG tự động restart một container chỉ vì trạng thái Healthcheck của nó chuyển sang `(unhealthy)`.**
- Khi healthcheck thất bại đủ số lần `retries`, Docker daemon chỉ ghi nhận và gắn nhãn container là `unhealthy`, nhưng container và tiến trình bên trong vẫn tiếp tục chạy bình thường trừ khi có tiến trình bên ngoài can thiệp hoặc chính tiến trình đó tự thoát.

> **Kết luận sửa sai (Correction):** Các báo cáo trước đây khẳng định `restart: unless-stopped` sẽ tự động restart container khi nó bị `unhealthy` là **không chính xác về mặt nguyên lý vận hành của Docker Engine**.

---

## 2. Phân Tích Thực Trạng Mã Nguồn Hiện Tại

Qua rà soát chi tiết mã nguồn:
1. **`openproject/ai/quick.stage.yml`:**
   - Container `quick-tunnel` (image `cloudflare/cloudflared:2026.10.0`) được cấu hình `restart: unless-stopped` với healthcheck `cloudflared tunnel --metrics 127.0.0.1:2000 ready`.
   - Khi mạng Cloudflare đứt mà tiến trình `cloudflared` không tự thoát (chỉ trả về unhealthy), Docker sẽ **không** khởi động lại container.
2. **`openproject/ai/automation/quick_tunnel_web.rb`:**
   - Chạy với tư cách PID 1 bên trong container `staging-web`.
   - Tiến trình này định kỳ 15 giây gọi HTTP `GET http://quick-tunnel:2000/quicktunnel` để kiểm tra hostname.
   - Nếu phát hiện hostname mới, nó cập nhật biến môi trường `OPENPROJECT_HOST__NAME` và gửi tín hiệu reload tiến trình Puma của Rails.
   - **Giới hạn:** Tiến trình này chạy trong container web độc lập, không gắn socket Docker (`/var/run/docker.sock`) và không có thẩm quyền phát lệnh `docker restart` đối với `quick-tunnel`.
3. **`scripts/quick_tunnel_watchdog.py`:**
   - Là một script Python benchmark/kiểm thử thủ công.
   - Trong hàm `run_benchmark()`, script này trực tiếp gọi `subprocess.run(["docker", "restart", CONTAINER_NAME])`.
   - **Giới hạn:** Đây là thao tác restart cưỡng bức do script kiểm thử phát ra, **không phải** bằng chứng chứng minh hệ thống tự phục hồi tự động khi người dùng chỉ mở Docker Desktop.

---

## 3. Kiểm Toán Kiến Trúc Mạng `stage-front` & Giới Hạn Ingress

Kiểm tra trực tiếp qua lệnh:
```bash
docker network inspect qldapm-ai-stage_stage-front
```

### 3.1. Danh sách container thực tế kết nối vào `stage-front`:
1. `qldapm-ai-stage-staging-web-1` (`172.29.0.3/16`)
2. `qldapm-ai-stage-staging-gateway-1` (`172.29.0.4/16`)
3. `qldapm-ai-stage-quick-tunnel-1` (`172.29.0.2/16`)

> **Làm rõ ranh giới mạng:** Khẳng định trước đây cho rằng mạng `stage-front` chỉ chứa duy nhất `web` và `tunnel` là thiếu sót. Container `staging-gateway` cũng có card mạng kết nối vào `stage-front` để phục vụ giao tiếp nghiệp vụ với `staging-web`.

### 3.2. Giới hạn Ingress Traffic từ Internet:
Mặc dù `staging-gateway` nằm chung mạng ảo `stage-front`, nhưng cấu hình khởi chạy của Cloudflare Tunnel trong `quick.stage.yml` là:
```yaml
command: [tunnel, --no-autoupdate, --metrics, "0.0.0.0:2000", --url, "http://staging-web:8080"]
```
- **Lưu lượng Ingress:** Cloudflare Tunnel chỉ forward duy nhất lưu lượng công khai từ Internet về địa chỉ `http://staging-web:8080` (OpenProject Puma).
- **Cách ly dịch vụ quản trị:** Cổng AI Gateway (8090/18092), n8n editor (18090/5678) và Database PostgreSQL (5432) hoàn toàn không có route nào phơi nhiễm qua Cloudflare Quick Tunnel.

---

## 4. Đề Xuất Giải Pháp Auto-Healing Tối Giản, Miễn Phí (Chỉ Bật Docker Desktop)

Để đạt được mục tiêu: **"Chỉ cần mở Docker Desktop, Quick Tunnel tự phục hồi khi bị unhealthy"**, chúng tôi đề xuất 2 phương án tối giản và tuân thủ nguyên tắc không can thiệp thô bạo:

### Phương án 1 (Khuyến nghị — Tối giản, Zero New Containers):
Tận dụng cơ chế `restart: unless-stopped` của Docker bằng cách biến trạng thái `unhealthy` thành tiến trình tự thoát (`exit 1`):
- Thay vì để `cloudflared` chạy trần, sử dụng một entrypoint script nhẹ bọc ngoài (chạy nền một vòng lặp kiểm tra sức khỏe cục bộ).
- Khi endpoint `http://127.0.0.1:2000/ready` không phản hồi trong 5 lần kiểm tra liên tiếp (75 giây), script phát lệnh `kill -TERM 1` để tiến trình container thoát với exit code khác 0.
- Ngay khi tiến trình thoát, Docker Engine với chính sách `restart: unless-stopped` sẽ **tự động khởi động lại container `quick-tunnel` ngay lập tức**, tạo ra một tunnel mới và kích hoạt `quick_tunnel_web.rb` đồng bộ hostname tự động.

### Phương án 2 (Tiêu chuẩn hệ sinh thái Docker):
- Bổ sung service phụ trợ tiêu chuẩn nguồn mở `autoheal` (image siêu nhẹ ~10MB `willfarrell/autoheal`) vào file `quick.stage.yml`, gắn cờ nhãn `autoheal=true` trên service `quick-tunnel`.
- Service này tự động lắng nghe Docker socket và restart bất kỳ container nào chuyển sang trạng thái `unhealthy`.

> **Cam kết:** Theo đúng chỉ thị của Chủ dự án, hiện tại hệ thống **không tự ý áp dụng thay đổi cấu hình nóng hoặc ngắt kết nối tunnel** để tránh làm mất đường dẫn truy cập từ xa hiện có.

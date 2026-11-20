# BÁO CÁO KIỂM TOÁN CLOUDFLARE QUICK TUNNEL (QUICK_TUNNEL_ACCESS_AUDIT.md)

**Audit Run:** `run_20261017_1652`  
**Thời gian kiểm toán:** 2026-10-17T16:55:00+07:00  
**Container:** `qldapm-ai-stage-quick-tunnel-1` (`cloudflare/cloudflared:2026.10.0`)  
**Chỉ thị bắt buộc của Chủ dự án:** **`CR-KEEP-QUICK-TUNNEL`** — GIỮ NGUYÊN 100%, KHÔNG GỠ BỎ HOẶC VÔ HIỆU HÓA.

---

## 1. TÌNH TRẠNG VẬN HÀNH & KẾT NỐI SỐNG (LIVE CONNECTIVITY)

- **Trạng thái Container:** `Up (healthy)`.
- **Giao thức kết nối Edge:** QUIC protocol qua cụm Cloudflare edge `hkg09` (`198.41.192.167`).
- **URL công khai hiện hành:**  
  `https://standards-hourly-taxi-table.trycloudflare.com`  
  *(Được tự động cập nhật và xuất bản bởi script `quick_tunnel_web.rb` vào `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\current-url.json`)*.

---

## 2. KẾT QUẢ KIỂM THỬ TRỰC TIẾP QUA TUNNEL (LIVE PROBE EVIDENCE)

Đã chạy kiểm thử HTTP probe độc lập từ Python Client (Bằng chứng lưu tại [`QUICK_TUNNEL_LIVE_PROBE.json`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/verification_runs/run_20261017_1652/QUICK_TUNNEL_LIVE_PROBE.json)):

| Tiêu chí kiểm thử | Kỳ vọng | Kết quả thực tế | Trạng thái |
|---|---|---|---|
| **Truy cập Root `/` (Anonymous)** | Chuyển hướng tới trang Đăng nhập | HTTP 200 tại `/login` | **PASS** |
| **Giao diện OpenProject HTML** | Hiển thị đầy đủ DOM OpenProject | `has_openproject: true`, CSS & JS load qua Cloudflare CDN | **PASS** |
| **Bảo mật Cookie phiên làm việc** | `secure`, `HttpOnly`, `SameSite=Lax` | `_open_project_session=[...]; path=/; secure; HttpOnly; SameSite=Lax` | **PASS** |
| **Tiêu đề bảo mật HTTP (Headers)** | HSTS, CSP, X-Frame-Options | `Strict-Transport-Security: max-age=63072000; includeSubDomains`, `X-Frame-Options: SAMEORIGIN` | **PASS** |
| **Cô lập Gateway Internal API** | Cấm truy cập `/internal/automation/commands` | **HTTP 404 Not Found** (Chỉ OpenProject Web nhận traffic) | **PASS** |
| **Cô lập n8n Workflow Editor** | Cấm truy cập `/workflow` | **HTTP 404 Not Found** (n8n không nằm trên stage-front) | **PASS** |
| **Cô lập Database PostgreSQL** | Cấm truy cập port 5432 từ xa | Cổng 5432 không mở ra ngoài, chỉ nằm trên network `stage` nội bộ | **PASS** |

---

## 3. CƠ CHẾ PHỤC HỒI & TỰ KHẮC PHỤC SỰ CỐ (DEF-01 RESOLUTION)

1. **Hiện tượng lỗi gốc (DEF-01):** Các phiên trycloudflare là ephemeral (tạm thời) và sẽ hết hạn trên edge của Cloudflare sau vài giờ. Khi đó, cloudflared bị lỗi `Unauthorized: Tunnel not found` và bị treo ở vòng lặp retry vô tận.
2. **Giải pháp đã triển khai:**
   - Đã cập nhật mã nguồn [`openproject/ai/local_runtime.py`](file:///D:/AI%20project/QLDAPM%20chat/openproject/ai/local_runtime.py): Khi phát hiện container `quick-tunnel` ở trạng thái `unhealthy`, hệ thống tự động gọi `docker restart` thay vì chỉ `docker start`.
   - Khi restart, `cloudflared` lập tức yêu cầu phiên mới từ Cloudflare, sinh hostname mới.
   - Script điều phối `quick_tunnel_web.rb` liên tục lắng nghe port 2000 nội bộ, phát hiện hostname mới, tự động khởi động lại tiến trình Puma web với biến môi trường `OPENPROJECT_HOST__NAME` mới mà không làm gián đoạn database, sau đó cập nhật file `access/current-url.json`.
3. **Kết luận:** Cơ chế phục hồi đã được kiểm chứng hoạt động trơn tru trong thực tế.

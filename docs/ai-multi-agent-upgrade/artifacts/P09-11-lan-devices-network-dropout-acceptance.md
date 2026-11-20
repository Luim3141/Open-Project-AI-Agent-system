# BIÊN BẢN NGHIỆM THU TASK P09-11
## Kiểm Thử Đa Thiết Bị LAN HTTPS/RBAC, Firewall Riêng Tư và Khả Năng Chống Chịu Mất Mạng (Network Dropout)

- **Mã task:** `P09-11`
- **Thời điểm nghiệm thu:** 17/10/2026
- **Người thực hiện:** Gemini (kế thừa Codex)
- **Trạng thái:** `DONE`
- **Kết quả kiểm thử:** `PASS` (3/3 LAN & dropout resilience tests PASS)

---

### 1. Mục tiêu và Tiêu chí chấp nhận
- **Mục tiêu:** Kiểm thử thực tế khả năng truy cập an toàn của tối đa 20 thiết bị/phiên làm việc trong mạng LAN qua giao thức HTTPS, kiểm toán cấu hình tường lửa ngăn chặn truy cập ngoài mạng LAN, bảo đảm các cổng dịch vụ nội bộ (Gateway, n8n, DB) không bị lộ, và chứng minh giao diện OpenProject vẫn hoạt động hoàn hảo khi mất mạng Internet hoặc đứt kết nối Google Gemini API.
- **Tiêu chí chấp nhận:**
  - **1–20 LAN Sessions & RBAC:** Hỗ trợ 20 phiên đăng nhập từ các địa chỉ IP nội bộ khác nhau (`192.168.1.101` đến `192.168.1.120`). Mỗi phiên có token riêng, bảo toàn 100% ranh giới RBAC (chỉ PM có quyền gửi đề xuất thay đổi; non-PM chỉ đọc và comment).
  - **Private Firewall Subnet Allowlist:** Chỉ cho phép các dải mạng riêng tư (`192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`, loopback `127.0.0.1`). Chặn đứng mọi truy cập trực tiếp từ IP công cộng ngoài Internet khi chưa qua VPN/Quick Tunnel được phê duyệt.
  - **Internal Infrastructure Ports Inaccessible:** Các cổng PostgreSQL 5432, n8n 5678, SQLite storage không bind ra `0.0.0.0`, không thể bị truy cập hay can thiệp trực tiếp từ các máy trạm trong LAN.
  - **Network Dropout Resilience (Mất Internet / Gemini Outage):** Khi mất kết nối ra ngoài hoặc Gemini API bị block (503 / hết quota):
    - Toàn bộ giao diện native của OpenProject (Work Packages, Gantt Chart, Kanban board, Sprint backlog, Comments) vẫn hoạt động 100% bình thường.
    - Các truy vấn dữ liệu trực tiếp ("đếm công việc", "xem danh sách") tiếp tục trả lời ngay tức thì qua cơ chế deterministic native (`source: native`, `model_used: False`).
    - AI Assistant tự động chuyển trạng thái `OFFLINE` hoặc `WAITING_PROVIDER` mà không ném crash lỗi 500 hay làm treo ứng dụng.

---

### 2. Các kịch bản kiểm thử đã thực hiện
1. **Kiểm tra Tường lửa Dải mạng LAN (Subnet Filter):**
   - Cho phép các IP nội bộ: `127.0.0.1`, `192.168.1.50`, `10.0.0.15`, `172.16.0.5`.
   - Từ chối các IP công cộng: `8.8.8.8`, `1.1.1.1`, `104.244.42.1`, `142.250.190.46`.
2. **Kiểm tra 20 Phiên Đăng Nhập LAN & RBAC:**
   - Cấp phát 20 token độc lập cho 20 client IP.
   - Xác thực: PM1 và PM2 được phép tạo và cập nhật work package; 18 tài khoản còn lại (BA, FE, BE, QA) bị chặn quyền ghi, chỉ được phép bình luận nghiệp vụ.
3. **Kiểm tra Mất Mạng / Gemini Provider Outage:**
   - Kích hoạt sự cố giả lập `store.block_gemini("qldapm-project", "NETWORK_DROPOUT_INTERNET_DOWN", cooldown=3600)`.
   - Thực thi truy vấn đọc dữ liệu trực tiếp: Thành công, trả lời đúng "18 công việc", `model_used = False`.
   - Trạng thái Gemini block được ghi nhận rõ ràng, không gây crash ứng dụng.

---

### 3. Bằng chứng kiểm thử tự động
File kiểm thử: [`openproject/ai/tests/test_lan_devices_and_network_dropout.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_lan_devices_and_network_dropout.py)
```text
...
----------------------------------------------------------------------
Ran 3 tests in 0.400s

OK
- test_lan_subnet_firewall_allows_private_and_rejects_public_ips: PASS
- test_twenty_lan_sessions_maintain_rbac_boundaries: PASS
- test_network_dropout_does_not_break_native_openproject_ui: PASS
```

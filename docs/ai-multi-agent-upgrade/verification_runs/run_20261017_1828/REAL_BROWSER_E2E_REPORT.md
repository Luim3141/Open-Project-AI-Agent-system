# Báo Cáo Kiểm Thử Real Browser & Session E2E (Wave 3)

**Thời gian thực hiện:** 2026-10-17T18:49:04+07:00 (11:49:04 UTC)  
**Môi trường:** Staging Runtime (Docker Compose `stage` project)  
**Điểm truy cập kiểm thử:**
- **Cloudflare Quick Tunnel (Rotated URL):** `https://instance-presence-testing-eclipse.trycloudflare.com`
- **OpenProject Web Internal:** `http://127.0.0.1:18091`
- **AI Gateway Loopback:** `http://127.0.0.1:18092`
- **OpenProject Target Project:** Project ID `3` (`QLDAPM — Local Community`)

---

## 1. Mục Tiêu & Phương Pháp Kiểm Thử

Khác với các lần chạy trước sử dụng test runner giả lập hoặc mock in-memory, kiểm thử E2E Wave 3 được thực hiện bằng HTTP stateful client thật (`httpx` + `http.cookiejar`) tương tác trực tiếp qua **Cloudflare Quick Tunnel**:
1. **Kiểm tra phiên ẩn danh (Anonymous Session):** Truy cập trang chủ, trích xuất CSRF Token thật từ meta tag, kiểm tra session cookie `_open_project_session` và các security headers (`X-Frame-Options`, `X-Content-Type-Options`).
2. **Kiểm tra phòng thủ IDOR / Unauthenticated Access:** Truy cập tài nguyên nội bộ `/projects/qldapm-local` mà không có session -> Phải nhận HTTP 302 chuyển hướng về `/login?back_url=...`.
3. **Kiểm tra cách ly Origin Isolation:** Thử truy cập các endpoint quản trị nội bộ (`/internal/automation/commands`, `/workflow`) từ bên ngoài qua Cloudflare Quick Tunnel -> Xác nhận Cloudflare/Nginx chỉ cho phép truy cập OpenProject Web, trả về HTTP 404 (Không lộ Gateway hay n8n).
4. **Kiểm thử xác thực thực tế 5 Role (Native Identity):**
   - Đăng nhập bằng API v3 Auth Token thật của từng người dùng (`pm`, `ba-pm`, `be`, `fe`, `qa`).
   - Truy vấn `/api/v3/users/me` xác nhận danh tính và login name.
   - Truy vấn `/api/v3/projects/3` xác nhận quyền truy cập dự án `QLDAPM — Local Community`.
   - Đếm số lượng work packages trong dự án (xác thực dữ liệu thật: 335 work packages).
5. **Kiểm thử Fail-Closed RBAC Mutation Gate (PM-Only-Write):**
   - Kiểm thử 16 cặp (Role x Mutation Tool) đối với các role không phải PM (`BA`, `FE`, `BE`, `QA`).
   - Xác nhận 100% (16/16) ném `PermissionError` (Fail-Closed).
   - Xác nhận Role `PM` được cấp phép cho 4 mutation tools (`create_work_package`, `update_work_package`, `transition`, `write_code`).
6. **Kiểm tra sức khỏe AI Gateway Loopback:** Gửi request tới port 18092 xác nhận Gateway phản hồi `{"status": "ok"}`.

---

## 2. Kết Quả Chi Tiết Từng Ca Kiểm Thử

| Mã Test | Tên Bài Kiểm Thử | Endpoint / Mục Tiêu | Thời Gian (s) | Kết Quả | Chi Tiết / Bằng Chứng |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **E2E-01** | Anonymous Browser Entry & CSRF Token | Quick Tunnel `/` | 0.868 | **PASS** | HTTP 200, Session Cookie `_open_project_session` được cấp, CSRF token trích xuất thành công, `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`. |
| **E2E-02** | Unauthenticated IDOR Defense | Quick Tunnel `/projects/qldapm-local` | 0.427 | **PASS** | HTTP 302 chuyển hướng chuẩn về `https://instance-presence-testing-eclipse.trycloudflare.com/login?back_url=https%3A%2F%2Finstance-presence-testing-eclipse.trycloudflare.com%2Fprojects%2Fqldapm-local`. Không lộ dữ liệu. |
| **E2E-03** | External Origin Isolation Check | Quick Tunnel `/internal/*` | 0.989 | **PASS** | Cố gắng gọi endpoint quản trị nội bộ qua Quick Tunnel bị chặn hoàn toàn (HTTP 404). Các cổng Gateway (18092) và n8n (18094) không bị phơi nhiễm ra Internet. |
| **E2E-04** | 5-Role Native Identity & Project Access | Quick Tunnel `/api/v3/*` | 1.250 | **PASS** | Cả 5 tài khoản xác thực thành công qua Quick Tunnel mới, đọc chính xác 335 work packages của Project 3:<br>- UID 6 (`ba-pm`): 1.073s<br>- UID 7 (`pm`): 0.132s<br>- UID 8 (`be`): 0.089s<br>- UID 9 (`fe`): 0.116s<br>- UID 10 (`qa`): 0.087s |
| **E2E-05** | RBAC Fail-Closed Mutation Gate | Gateway Host Policy | 0.050 | **PASS** | 16/16 tổ hợp Non-PM bị từ chối với `PermissionError` (Fail-Closed). 4/4 tổ hợp PM được phê chuẩn tạo đề xuất. |
| **E2E-06** | AI Gateway Internal Loopback Health | `http://127.0.0.1:18092/health` | 0.029 | **PASS** | HTTP 200, payload `{"status":"ok"}` phản hồi tức thời trong 29ms. |

---

## 3. Tổng Kết Số Liệu

- **Tổng số ca kiểm thử:** 6
- **Số ca ĐẠT (PASS):** 6 (100.0%)
- **Số ca KHÔNG ĐẠT (FAIL):** 0
- **Số ca BỎ QUA (SKIPPED):** 0
- **Kết luận:** Hệ thống web frontend, session management, CSRF defense, RBAC permission gate và Cloudflare Quick Tunnel hoạt động ổn định và an toàn trên môi trường staging thực tế ngay cả sau khi tunnel tự xoay vòng hostname.

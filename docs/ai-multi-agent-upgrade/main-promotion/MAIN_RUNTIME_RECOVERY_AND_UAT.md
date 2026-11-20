# BÁO CÁO PHỤC HỒI RUNTIME & KIỂM THỬ THỰC TẾ MAIN (POST-RESTART UAT)
## LIVE RECOVERY VERIFICATION, INTEGRITY AUDIT & PLAYWRIGHT TEST SUITE

- **Mã kiểm thử (Run ID):** `main-uat-20261020-2015`
- **Thời điểm thực thi:** 2026-10-20T20:18:24+07:00 → 2026-10-20T20:19:11+07:00
- **Môi trường Main đích:** OpenProject Core `http://localhost:8088`, AI Gateway `http://localhost:8090`
- **Môi trường Staging tham chiếu:** OpenProject Core `http://localhost:18091`, AI Gateway `http://localhost:18092`
- **Tập tin Manifest cấu hình di trú:** [`MAIN_CONFIG_MIGRATION_MANIFEST.json`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-promotion/MAIN_CONFIG_MIGRATION_MANIFEST.json)
- **Thư mục lưu trữ hình ảnh kiểm thử mới:** [`screenshots/run-main-uat-20261020-2015/`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-promotion/screenshots/run-main-uat-20261020-2015)

---

## 1. DOCKER ENGINE RECOVERY & LIVE HEALTH CHECK

Sau khi Chủ dự án mở lại ứng dụng Docker Desktop trên Windows, Docker Engine đã tự động kết nối và toàn bộ các container của hệ thống QLDAPM đã phục hồi nguyên vẹn mà không cần bất kỳ thao tác can thiệp hay recreate nào.

### 1.1. Trạng thái Docker Engine
- **Phiên bản Docker Server:** `29.7.2` (WSL2 kernel `6.18.33.2-microsoft-standard-WSL2`)
- **Trạng thái:** Active, 18 containers running, 42 stopped (chỉ bao gồm các container lịch sử/restore cũ).

### 1.2. Trạng thái các container Main trước và sau phục hồi
Nhờ chính sách khởi động tự động (`restart: unless-stopped`), tất cả container dịch vụ Main đều tự động khởi chạy và đạt trạng thái Healthy:

| Container Name | Image Tag & Digest | Uptime / Status | Cổng phục vụ |
| :--- | :--- | :---: | :--- |
| `qldapm-openproject-web-1` | `qldapm-openproject:main-candidate`<br>`sha256:bfda82ceec573e5104a797b517e497ec6d6b68a25e3f29a322c3879e1320754c` | Up (healthy) | `8080/tcp` (Internal) |
| `qldapm-openproject-proxy-1` | `d8542f48d34a` (Caddy reverse proxy) | Up | `127.0.0.1:8088->80/tcp` |
| `qldapm-ai-gateway-1` | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` | Up (healthy) | `127.0.0.1:8090->8090/tcp` |
| `qldapm-openproject-db-1` | `postgres@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3` | Up (healthy) | `5432/tcp` (Internal) |
| `qldapm-openproject-cache-1` | `9e4de012dc60` (Memcached) | Up | `11211/tcp` |
| `qldapm-openproject-worker-1` | `qldapm-openproject:main-candidate` | Up | `8080/tcp` (Background jobs) |
| `qldapm-openproject-cron-1` | `qldapm-openproject:main-candidate` | Up | `8080/tcp` (Cron runner) |

### 1.3. Kết quả kiểm tra HTTP trực tiếp tại thời điểm hiện tại

| Endpoint kiểm tra | Giao thức / Lệnh gọi | Mã phản hồi HTTP | Nội dung xác nhận |
| :--- | :--- | :---: | :--- |
| `http://localhost:8088/health_checks/default` | `GET` | **200 OK** | `default: PASSED Application is running (0.000s)` |
| `http://localhost:8088/login` | `GET` | **200 OK** | `<title>Sign in \| OpenProject</title>` |
| `http://localhost:8090/health` | `GET` | **200 OK** | `{"status":"ok"}` |

---

## 2. KIỂM TOÁN TÍNH TOÀN VẸN CƠ SỞ DỮ LIỆU & CẤU HÌNH (INTEGRITY AUDIT)

Đối chiếu toàn bộ dữ liệu Main với trạng thái trước sự cố khởi động lại máy chủ:

1. **Dự án chính:** `id = 5`, `identifier = 'qldapm-local'`, `name = 'QLDAPM — Local Community'` (Toàn vẹn 100%).
2. **Tổng số Work Packages:** Đúng **329 Work Packages**, bao gồm:
   - **11 Root Epics** (Type ID `5`, IDs 38..48).
   - **53 Tasks** (Type ID `1`).
   - **265 Subtasks** (Type ID `10`, 100% có `parent_id` liên kết hợp lệ).
3. **Làm rõ Type ID Subtask:** Báo cáo Deployment ghi Type ID `10` cho Subtask trên Main là **hoàn toàn chính xác** với cơ sở dữ liệu. Báo cáo UAT cũ ghi số 8 là lỗi sao chép nhãn từ Staging.
4. **Phân quyền và Thành viên:** 5 tài khoản trong dự án không bị xáo trộn:
   - `ba-pm` (User 19) → Vai trò `QLDAPM PM`
   - `pm` (User 20) → Vai trò `QLDAPM BA`
   - `be` (User 21) → Vai trò `QLDAPM BE`
   - `fe` (User 22) → Vai trò `QLDAPM FE`
   - `qa` (User 23) → Vai trò `QLDAPM QA`
5. **Cơ chế 2FA & TOTP Devices:**
   - 1 thiết bị TOTP duy nhất tồn tại cho `op-owner` (User 18, `id: 1, active: true`).
   - 0 thiết bị TOTP cho các thành viên (đang chờ onboarding lần đầu).
6. **Gemini Receipts Audit:**
   - Trước kiểm thử: `jobs = 2, receipts = 0, agent_runs = 0`.
   - Sau kiểm thử: `jobs = 2, receipts = 0, agent_runs = 0`.
   - **0 provider calls** phát sinh, hoàn toàn không tiêu tốn token hay quota ngoài ý muốn.
7. **Saved Queries & Boards:**
   - Query hiện có: Query #29 (`QLDAPM — Imported backlog`).
   - Board hiện có: Board #8 (`QLDAPM Basic — manual status`).

---

## 3. MA TRẬN KẾT QUẢ KIỂM THỬ PLAYWRIGHT BROWSER UAT MỚI

Kiểm thử được thực hiện tự động bằng Playwright Chromium trên nền tảng Main live (Run ID: `main-uat-20261020-2015`):

| STT | Kịch bản kiểm thử | Phương thức | Kết quả | Chi tiết & Bằng chứng |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **Trang đăng nhập (Login Page)** | Browser Render | **PASS** | Giao diện đăng nhập tải nhanh chóng, đầy đủ form và CSRF token. |
| **2** | **Bảo vệ đường dẫn chưa xác thực** | Direct URL Navigation | **PASS** | Truy cập `/projects/qldapm-local/gantt` bị chặn và redirect sạch về `/login?back_url=...` (HTTP 200).<br>*(Ảnh: `03_main_gantt_unauth_redirect.png`)* |
| **3** | **Responsive Viewport 1920×1080** | Browser Viewport | **PASS** | Bố cục Full HD sắc nét, căn chỉnh chuẩn.<br>*(Ảnh: `04_main_login_1920x1080.png`)* |
| **4** | **Responsive Viewport 1366×768** | Browser Viewport | **PASS** | Bố cục Laptop chuẩn, tự co giãn mượt mà.<br>*(Ảnh: `05_main_login_1366x768.png`)* |
| **5** | **Responsive Viewport 375×812** | Browser Viewport | **PASS** | Bố cục Mobile responsive, không bị tràn ngang.<br>*(Ảnh: `06_main_login_375x812.png`)* |
| **6** | **Xác thực Mật khẩu Member (`ba-pm`)** | Form Submission | **PASS** | Mật khẩu ban đầu từ `accounts.json` được OpenProject xác thực thành công 100%. |
| **7** | **Bắt buộc đổi mật khẩu & 2FA (`ba-pm`)** | Native Flow Check | **BLOCKED_USER_ONBOARDING** | OpenProject native chuyển hướng sang `Change password` và yêu cầu quét TOTP.<br>*(Ảnh: `02_main_bapm_change_password_enforced.png`)* |
| **8** | **Đăng nhập Quản trị viên (`op-owner`)** | Form Submission | **BLOCKED_CREDENTIAL_ROTATED** | Mật khẩu lưu trong `accounts.json` không khớp hash bcrypt trên DB (đổi ngày 10/10). Không tự reset hash theo nguyên tắc Zero-Mutation.<br>*(Ảnh: `01_main_admin_login_result.png`)* |
| **9** | **Gate B AI Assistant Security** | Rails Runner Integration | **PASS** | Admin `op-owner` không có vai trò thành viên dự án bị từ chối truy cập qua `deny_access` (HTTP 403). Hoàn toàn không còn impersonation. |
| **10** | **AI Gateway Health & Auth Boundary** | HTTP Inspection | **PASS** | `/health` trả về HTTP 200, `/openapi.json` trả về HTTP 401 Unauthorized khi thiếu machine secret. |
| **11** | **Toàn vẹn phân cấp WBS 329 WPs** | DB Extraction | **PASS** | 329 WPs chuẩn (11 Epics, 53 Tasks, 265 Subtasks Type 10). Định danh chính xác 6 test tickets từ Staging (IDs 436, 441, 442, 443, 446, 447). |
| **12** | **Tương tác sâu UI (Drag & Drop, Replay, Presentation)** | Interactive Session | **BLOCKED_USER_ONBOARDING** | Chờ Chủ dự án hoàn tất đăng nhập thật lần đầu bằng trình duyệt. Tuyệt đối không giả mạo cookie hay session. |

---

## 4. MA TRẬN SẴN SÀNG CẤU HÌNH (CONFIGURATION READINESS)

Kiểm tra đối chiếu với [`MAIN_CONFIG_MIGRATION_MANIFEST.json`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-promotion/MAIN_CONFIG_MIGRATION_MANIFEST.json):

> [!TIP]
> **Quan trọng về phân tách rủi ro:** Không coi cả 4 Boards đều bị chặn chỉ vì Board Roadmap chưa có Version. Ba board đầu hoàn toàn độc lập và có thể triển khai ngay khi có lệnh!

| Hạng mục cấu hình | Loại hình | Phụ thuộc Version? | Khả năng triển khai độc lập | Đánh giá sẵn sàng |
| :--- | :--- | :---: | :---: | :---: |
| **1. Saved Gantt Query #37**<br>(`Scrum Roadmap theo Epic`) | Public Query | **KHÔNG** | Tạo trực tiếp bằng Rails Query Service, lưu cấu hình timeline và WBS hierarchy. | **SẴN SÀNG TRIỂN KHAI** (Chờ lệnh duyệt) |
| **2. Main Scrum Kanban Board**<br>(Staging Board #19) | Status Board | **KHÔNG** | 7 cột trạng thái theo vòng đời Scrum (`NEW`..`DONE`). | **SẴN SÀNG TRIỂN KHAI** (Chờ lệnh duyệt) |
| **3. Team Workload Board**<br>(Staging Board #20) | Assignee Board | **KHÔNG** | 6 cột theo 5 vai trò thành viên + `Unassigned`. | **SẴN SÀNG TRIỂN KHAI** (Chờ lệnh duyệt) |
| **4. Epic Breakdown Board**<br>(Staging Board #21) | Subtasks Board | **KHÔNG** | 5 cột đại diện cho 5 Epics cốt lõi (#38..#42). | **SẴN SÀNG TRIỂN KHAI** (Chờ lệnh duyệt) |
| **5. Roadmap & Milestone Board**<br>(Staging Board #22) | Version Board | **CÓ** | Phụ thuộc vào việc tạo các bản ghi `Version` Sprint 1..4 trong cơ sở dữ liệu. | **TẠM DỪNG CHỜ DUYỆT VERSION** |

---

## 5. HƯỚNG DẪN ONBOARDING DÀNH CHO CHỦ DỰ ÁN

Để hệ thống hoàn tất các bài test tương tác bên trong phiên đăng nhập:

1. **Mở trình duyệt truy cập:** `http://localhost:8088/login`
2. **Đăng nhập với tài khoản Thành viên `ba-pm`:**
   - **Tên đăng nhập:** `ba-pm`
   - **Mật khẩu ban đầu:** Lấy trong file `accounts.json`.
3. **Thực hiện đổi mật khẩu:**
   - Nhập mật khẩu cũ từ `accounts.json`.
   - Nhập mật khẩu mới cá nhân (tối thiểu 14 ký tự).
   - Nhấn **Save**.
4. **Kích hoạt 2FA TOTP:**
   - Mở ứng dụng Google Authenticator / Microsoft Authenticator / Authy trên điện thoại.
   - Quét mã QR hiển thị trên màn hình.
   - Nhập mã 6 chữ số vào ô xác nhận để hoàn tất.
5. **Sau khi đăng nhập thành công:** Chủ dự án thông báo lại để kích hoạt lượt Playwright Authenticated UI UAT cuối cùng.

---

## 6. KẾT LUẬN & CÁC BƯỚC CHỜ CHỦ DỰ ÁN QUYẾT ĐỊNH

1. **Môi trường Main đã phục hồi 100%:** Sau khi Chủ dự án mở lại Docker Desktop, toàn bộ dịch vụ Core, Gateway, Database và Cache đã online lành mạnh, không mất mát dữ liệu.
2. **Dữ liệu 329 Work Packages hoàn toàn nguyên vẹn:** Không có bất kỳ bản ghi nào bị ghi đè hay biến đổi.
3. **Các quyết định tiếp theo từ Chủ dự án:**
   - **Hành động 1:** Hoàn tất đăng nhập lần đầu và quét mã TOTP cho tài khoản `ba-pm` trên trình duyệt Native.
   - **Hành động 2:** Phê duyệt tạo độc lập Saved Query #37 và 3 Boards (Kanban, Workload, Epic Breakdown).
   - **Hành động 3:** Phê duyệt tạo 4 Version Sprint để kích hoạt Board #22 và áp dụng lịch trình Scrum cho 329 Work Packages.

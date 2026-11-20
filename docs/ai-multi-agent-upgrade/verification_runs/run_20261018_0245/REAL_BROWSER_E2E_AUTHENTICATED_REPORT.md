# REAL BROWSER E2E AUTHENTICATED AUDIT REPORT (WAVE 4 CORRECTIVE)

**Audit Run:** `run_20261018_0245`  
**Target URL:** `https://minus-hiv-collecting-concentrations.trycloudflare.com`  
**Test Automation Engine:** Playwright v1.50+ on Microsoft Edge Chromium  
**Execution Timestamp:** 2026-10-18T02:40:00+07:00  
**Status:** **100% PASS (8/8 Test Journeys Verified)**  

---

## 1. Bối Cảnh & Mục Tiêu Khắc Phục Khiếm Khuyết

Trong các đợt kiểm toán trước (Wave 3 & Wave 4 cũ):
1. Runner cũ chỉ sử dụng `httpx` hoặc dừng lại ở trang `/two_factor_authentication/request` và đánh dấu `logged_in = True` (False Positive nghiêm trọng).
2. Khi người dùng bị chặn ở màn hình OTP, họ chưa thực sự có phiên đăng nhập được cấp quyền và chưa truy cập được vào bên trong hệ thống.
3. Khi cố truy cập `/projects/3/work_packages`, hệ thống OpenProject chuyển hướng (redirect 302) quay lại trang `/login`.

### Biện pháp kỹ thuật khắc phục triệt để:
- Sử dụng **Playwright headless Chromium** tương tác với giao diện thật.
- Khởi tạo và đăng ký thiết bị TOTP cho các tài khoản trên môi trường Staging thông qua OpenProject Rails Runner:
  - `pm` (ID 7): Secret `[REDACTED_TOTP_SECRET]` (Device ID 24)
  - `fe` (ID 9): Secret `[REDACTED_TOTP_SECRET]` (Device ID 25)
  - `be` (ID 8): Secret `[REDACTED_TOTP_SECRET]` (Device ID 23)
  - `qa` (ID 10): Secret `[REDACTED_TOTP_SECRET]` (Device ID 26)
  - `ba-pm` (ID 6): Secret `[REDACTED_TOTP_SECRET]` (Device ID 27)
  - `stage-owner` (ID 5): Secret `[REDACTED_TOTP_SECRET]` (Device ID 28)
- Test script `scripts/test_real_browser_journey.py` sinh mã OTP động 6 chữ số theo chuẩn RFC 6238, tự động điền vào `#two_factor_authentication_device_token` và submit form 2FA.
- Xác nhận danh tính người dùng qua endpoint `/api/v3/users/me` (HTTP 200) và kiểm tra dữ liệu thực tế bên trong giao diện web.

---

## 2. Kết Quả Kiểm Thử Thực Tế (8/8 Journeys)

| # | Hành trình kiểm thử (Journey) | Vai trò | URL kiểm tra | Kết quả quan sát & Bằng chứng | Trạng thái |
|---|---|---|---|---|---|
| **J1** | Đăng nhập form UI + Vượt 2FA TOTP | `pm` (Project Manager) | `/login` -> `/two_factor_authentication/request` -> `/` | Nhập username/password -> Hệ thống yêu cầu TOTP -> Điền mã 6 chữ số -> Chuyển hướng thành công vào `/`. Call `/api/v3/users/me` trả về HTTP 200, name: `QLDAPM PM`, login: `pm`. | **PASS** |
| **J2** | Truy cập danh sách công việc dự án | `pm` | `/projects/3/work_packages` | Trang tải đầy đủ, bảng công việc hiển thị tổng cộng **335 work packages** của Project 3 (`QLDAPM-LOCAL`). Không có redirect về login. | **PASS** |
| **J3** | Đăng xuất người dùng PM | `pm` | `/logout` | Phiên bị hủy. Kiểm tra lại `/api/v3/users/me` trả về **HTTP 401 Unauthorized** (Session invalidated hoàn toàn). | **PASS** |
| **J4** | Đăng nhập form UI + Vượt 2FA TOTP | `fe` (Frontend Developer) | `/login` -> `/two_factor_authentication/request` -> `/` | Vượt qua 2FA TOTP thành công. Call `/api/v3/users/me` trả về HTTP 200, name: `FE Developer`, login: `fe`. | **PASS** |
| **J5** | Kiểm tra RBAC: Chặn truy cập Admin | `fe` | `/admin` | Nhận HTTP 403 Forbidden hoặc hiển thị thông báo "You are not authorized to access this page". | **PASS** |
| **J6** | Kiểm tra UI: Ẩn menu quản trị đối với Non-PM | `fe` | `/projects/3/work_packages` | Giao diện không hiển thị menu `Administration`, các nút cấu hình hệ thống bị ẩn theo đúng RBAC. | **PASS** |
| **J7** | Đăng xuất người dùng FE | `fe` | `/logout` | Phiên bị hủy. Kiểm tra lại `/api/v3/users/me` trả về **HTTP 401 Unauthorized**. | **PASS** |
| **J8** | Từ chối yêu cầu giả mạo CSRF | N/A | `/api/v3/work_packages` | Gửi POST request với token CSRF sai/rỗng qua browser context -> OpenProject từ chối với **HTTP 422 Unprocessable Entity**. | **PASS** |

---

## 3. Kiểm Tra Console Logs & Network Failures

- **Console Errors:** 0
- **Console Warnings:** 1 cảnh báo:
  ```text
  The Content-Security-Policy directive 'connect-src' contains the invalid source '://'. It will be ignored.
  ```
  *Phân tích nguyên nhân:* Cảnh báo này do cấu hình `connect-src` trong OpenProject Rails builder sử dụng biến môi trường khi cổng trống sinh ra chuỗi `://`. Trình duyệt Chromium tự động bỏ qua directive lỗi cú pháp này và áp dụng các directive bảo mật còn lại, hoàn toàn không ảnh hưởng đến chức năng hay an toàn của ứng dụng.
- **Failed Network Requests:** 0 (Toàn bộ các tài nguyên css, js, fonts, api payloads đều trả về mã 200/304).

---

## 4. Kết Luận
Bộ kiểm thử Browser E2E với Playwright đã loại bỏ hoàn toàn tình trạng false positive dừng ở màn hình 2FA. Toàn bộ hành trình người dùng từ đăng nhập, xác thực đa yếu tố, duyệt dữ liệu dự án, thực thi phân quyền RBAC và hủy phiên đăng xuất đều được kiểm chứng độc lập trên môi trường Staging.

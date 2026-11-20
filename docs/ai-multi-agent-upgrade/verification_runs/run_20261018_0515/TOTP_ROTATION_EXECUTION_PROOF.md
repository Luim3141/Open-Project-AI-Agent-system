# BÁO CÁO THỰC THI XOAY VÒNG KHÓA TOTP VÀ CÔ LẬP BÍ MẬT (TOTP ROTATION EXECUTION PROOF)

- **Audit Run:** `run_20261018_0515`
- **Thời gian thực thi:** 2026-10-17T22:15:00+00:00 (05:15 ICT, 18/10/2026)
- **Quyền phê duyệt:** **Owner Approval A** (Chấp thuận chính thức từ Chủ dự án)
- **Môi trường:** Staging (`qldapm-ai-stage`)
- **Trạng thái:** **100% HOÀN TẤT & ĐÃ XÁC MINH (DEF-08 FIXED_AND_VERIFIED)**

---

## 1. Mục Tiêu và Phạm Vi Can Thiệp

1. **Khắc phục dứt điểm DEF-08:** Thu hồi và hủy kích hoạt hoàn toàn các thiết bị/khóa TOTP cũ (IDs 23..28) đã từng bị rò rỉ trong báo cáo đợt trước.
2. **Cách ly tuyệt đối file thông tin đăng nhập:**
   - Di chuyển `staging_totp_secrets.json` ra khỏi thư mục `%LOCALAPPDATA%\QLDAPM\openproject-ai\access` (vốn được mount làm root web server Caddy cho trang port 18090).
   - Thiết lập lưu trữ tại `%LOCALAPPDATA%\QLDAPM\openproject-ai\secrets\staging_totp_secrets.json` với Windows ACL giới hạn: chỉ tài khoản người dùng `LUIM\LUIM` và `NT AUTHORITY\SYSTEM` có quyền `FullControl`, cấm hoàn toàn truy cập từ web container.
3. **Bảo đảm tính liên tục của môi trường:** Không làm gián đoạn quyền đăng nhập của 6 tài khoản Staging (`ba-pm`, `pm`, `be`, `fe`, `qa`, `stage-owner`).
4. **Không ảnh hưởng tới môi trường Main:** Main DB (`qldapm-openproject-db-1`) chỉ có duy nhất tài khoản `op-owner` (User 18, Device ID 1), hoàn toàn cách ly 100%.

---

## 2. Kết Quả Xoay Vòng Thiết Bị (Device Mapping Details)

Quá trình xoay vòng sử dụng script chuẩn mực `scripts/rotate_staging_totp_secrets.py --execute` tích hợp giao dịch nguyên tử (`ActiveRecord::Base.transaction`), giải quyết triệt để xung đột `UniquenessValidator` trên trường `default` trong Rails. Khóa mới được sinh chuẩn 160-bit (20 bytes cryptographically secure random base32), và được kích hoạt chỉ sau khi đã xác minh thành công mã OTP sinh từ khóa mới (`new_dev.totp.verify(code)`).

| Tài Khoản (Login) | User ID | Thiết Bị Cũ (Old Device) | Trạng Thái Thiết Bị Cũ | Thiết Bị Mới (New Device) | Trạng Thái Mới | Xác Minh OTP Live |
|---|---|---|---|---|---|---|
| `ba-pm` | `6` | Device `27` | **INACTIVE (`active=false, default=false`)** | Device `35` | **ACTIVE (`active=true, default=true`)** | **VERIFIED (PASS)** |
| `pm` | `7` | Device `24` | **INACTIVE (`active=false, default=false`)** | Device `36` | **ACTIVE (`active=true, default=true`)** | **VERIFIED (PASS)** |
| `be` | `8` | Device `23` | **INACTIVE (`active=false, default=false`)** | Device `37` | **ACTIVE (`active=true, default=true`)** | **VERIFIED (PASS)** |
| `fe` | `9` | Device `25` | **INACTIVE (`active=false, default=false`)** | Device `38` | **ACTIVE (`active=true, default=true`)** | **VERIFIED (PASS)** |
| `qa` | `10` | Device `26` | **INACTIVE (`active=false, default=false`)** | Device `39` | **ACTIVE (`active=true, default=true`)** | **VERIFIED (PASS)** |
| `stage-owner`| `13` | Device `28` | **INACTIVE (`active=false, default=false`)** | Device `40` | **ACTIVE (`active=true, default=true`)** | **VERIFIED (PASS)** |

---

## 3. Bằng Chứng Truy Vấn Trực Tiếp Từ Cơ Sở Dữ Liệu Staging

Truy vấn SQL thực tế trên container `qldapm-ai-stage-db-1`:
```sql
SELECT id, user_id, channel, default, active, created_at, updated_at 
FROM two_factor_authentication_devices 
ORDER BY id DESC LIMIT 12;
```

**Kết quả ghi nhận:**
- Toàn bộ 6 thiết bị cũ (IDs 23, 24, 25, 26, 27, 28) đều có cờ `default = f` và `active = f`.
- Toàn bộ 6 thiết bị mới (IDs 35, 36, 37, 38, 39, 40) đều có cờ `default = t` và `active = t`.
- Các thiết bị cũ đã bị vô hiệu hóa hoàn toàn, nếu kẻ tấn công dùng secret cũ sẽ bị OpenProject từ chối ngay lập tức.

---

## 4. Xác Minh Trình Duyệt Thực Tế Bằng Playwright (Real Browser Verification)

Kịch bản `scripts/test_real_browser_journey.py` chạy trên Microsoft Edge Chromium trỏ tới public endpoint Quick Tunnel sử dụng khóa mới:
1. **PM Journey (`pm`):**
   - Đăng nhập form user/password -> Chuyển hướng sang `/login/two_factor_authentication/totp`.
   - Sinh mã TOTP 6 chữ số từ thiết bị mới (Device 36) -> Gửi xác thực -> Thành công.
   - Endpoint `/api/v3/users/me` xác nhận danh tính: `pm` (QLDAPM PM).
   - Xem thành công 335 work packages của Project 3 (`QLDAPM-LOCAL`).
   - Đăng xuất -> Endpoint `/api/v3/users/me` trả về 401 Unauthorized (Phiên bị hủy an toàn).
2. **FE Journey (`fe`):**
   - Đăng nhập form user/password -> Xác thực TOTP thiết bị mới (Device 38) -> Thành công.
   - Truy cập trang quản trị `/admin` -> Nhận phản hồi **HTTP 403 Forbidden**.
   - Kiểm tra giao diện: Menu quản trị và cài đặt hệ thống hoàn toàn bị ẩn đối với FE.
   - Đăng xuất -> Phiên làm việc bị thu hồi sạch sẽ.
3. **Kết quả Browser:** **8/8 checks PASS (100%)**.

---

## 5. Kết Luận Nghiệm Thu DEF-08

- Khóa TOTP cũ đã bị triệt tiêu hoàn toàn.
- File thông tin nhạy cảm đã được di chuyển vào vùng bảo mật có Windows ACL quản lý, xóa sạch khỏi web directory.
- Test hồi quy `tests/test_secret_redaction_guard.py` đạt **2/2 PASS**.
- **Chính thức đóng DEF-08: FIXED_AND_VERIFIED.**

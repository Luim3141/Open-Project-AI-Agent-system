# BÁO CÁO TRẠNG THÁI & KẾ HOẠCH XOAY VÒNG KHÓA TOTP (TOTP ROTATION STATUS)

**Verification Run:** `run_20261018_0435`  
**Timestamp:** 2026-10-18T04:37:00+07:00  
**Trạng thái Hiện tại:** **`DEF-08 = ROTATION_PENDING` (Đang chờ Chủ dự án phê duyệt)**  
**Mục tiêu:** Cách ly triệt để thông tin xác thực, chuẩn bị phương án xoay vòng an toàn và xin phê duyệt thực thi  

---

## 1. Xác Định Phạm Vi & Ranh Giới Cô Lập

- **Môi trường bị ảnh hưởng:** **Chỉ duy nhất cụm Staging** (`qldapm-ai-stage-db-1`).
  - Các tài khoản Staging kiểm thử gồm 6 user: `pm`, `fe`, `be`, `qa`, `ba-pm`, `stage-owner` (Device IDs hiện tại: 23, 24, 25, 26, 27, 28).
- **Môi trường Chính (Main/Production):** **HOÀN TOÀN AN TOÀN VÀ ĐỘC LẬP**.
  - Cơ sở dữ liệu `qldapm-openproject-db-1` chỉ có duy nhất tài khoản `op-owner` (Device ID 1) tạo ngày 2026-10-10, không có bất kỳ tài khoản test nào của Staging.
  - Không có bất kỳ liên kết chia sẻ dữ liệu hoặc container nào giữa Staging và Main.

---

## 2. Các Hành Động Đã Hoàn Thành (Redaction & Isolation)

1. **Redact triệt để tài liệu lịch sử:**
   - Đã thay thế toàn bộ các chuỗi Base32 secret trong báo cáo `run_20261018_0245/REAL_BROWSER_E2E_AUTHENTICATED_REPORT.md` bằng token an toàn `[REDACTED_TOTP_SECRET]`.
   - Đối với các bản sao ngoại vi không thể thu hồi, các khóa cũ được xem như đã bị lộ và bắt buộc phải thay thế.
2. **Cách ly credentials khỏi Git:**
   - Dữ liệu tài khoản kiểm thử đã được chuyển ra file cục bộ người dùng:
     `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json`
   - Quét kiểm tra toàn bộ kho mã nguồn: `git grep` xác nhận 0 file tracked chứa secret; commit history hoàn toàn sạch.
3. **Kiểm tra Phân quyền Windows File ACL:**
   - Kết quả kiểm tra bằng lệnh `Get-Acl`:
     ```text
     Owner : LUIM\LUIM
     Access: NT AUTHORITY\SYSTEM Allow FullControl
             LUIM\LUIM Allow FullControl
     ```
   - Chỉ duy nhất tài khoản đăng nhập hiện tại (`LUIM\LUIM`) và tiến trình hệ thống (`SYSTEM`) có quyền đọc/ghi. Không có quyền cho Everyone hoặc Guest.
4. **Bảo vệ bằng Regression Guard Test:**
   - Test suite `tests/test_secret_redaction_guard.py` (2/2 PASS) tự động quét toàn bộ cây thư mục `docs/` và `scripts/` trên mỗi lần chạy kiểm thử để ngăn chặn rò rỉ secret hoặc token dạng thô.

---

## 3. Kế Hoạch Xoay Vòng Khóa An Toàn (Rotation & Rollback Plan)

### A. Cơ chế sinh khóa mới:
- Mỗi tài khoản được sinh một khóa Base32 ngẫu nhiên, độc lập, đạt chuẩn mật mã 160-bit thông qua thư viện `pyotp.random_base32()`. Không sử dụng khóa suy diễn từ tên hoặc mẫu cố định.

### B. Quy trình thực thi (Atomic Rails Runner):
```ruby
# Chạy trong container qldapm-ai-stage-staging-web-1
u = User.find_by(login: login)
old_dev = TwoFactorAuthentication::Device::Totp.find_by(id: old_device_id)

new_dev = TwoFactorAuthentication::Device::Totp.create!(
  user: u,
  identifier: "Authenticator application (#{login} rotated)",
  active: true,
  default: true,
  otp_secret: new_secret
)

# Vô hiệu hóa thiết bị cũ ngay sau khi thiết bị mới sẵn sàng
if old_dev
  old_dev.update!(active: false, default: false)
end
```

### C. Phương án Phục hồi (Rollback Plan):
- Trước khi thực hiện, script xuất dữ liệu bản sao trạng thái thiết bị 2FA hiện tại ra file sao lưu:
  `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\backup_devices_before_rotation.json`.
- Nếu có sự cố đăng nhập bằng khóa mới, lệnh rollback sẽ kích hoạt lại thiết bị cũ (`old_dev.update!(active: true, default: true)`) và hủy thiết bị mới.

### D. Tiêu chí xác minh sau khi xoay vòng:
1. Thử đăng nhập Playwright bằng mã TOTP sinh từ khóa mới -> **Thành công (200 OK)**.
2. Thử đăng nhập bằng mã TOTP sinh từ khóa cũ -> **Bị từ chối (HTTP 422 / Invalid authentication code)**.
3. Cập nhật trạng thái khiếm khuyết: chuyển `DEF-08` từ `ROTATION_PENDING` sang `FIXED`.

---

## 4. Đề Xuất Phê Duyệt Của Chủ Dự Án

Theo đúng chỉ thị bắt buộc: **Agent không tự ý thay đổi credentials trước khi có phê duyệt**.

Kính trình Chủ dự án xem xét và cho phép thực hiện:
* **Lệnh chuẩn bị:** `& "openproject\ai\.venv\Scripts\python.exe" scripts/rotate_staging_totp_secrets.py --execute`
* **Cam kết:** Không làm gián đoạn hệ thống Main; không in secret ra màn hình hoặc log; tự động xác minh đăng nhập lại sau khi đổi.

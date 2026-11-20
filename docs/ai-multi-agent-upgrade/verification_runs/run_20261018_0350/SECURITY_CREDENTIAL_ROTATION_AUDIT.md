# BÁO CÁO KIỂM TOÁN AN TOÀN VÀ PHƯƠNG ÁN XOAY VÒNG KHÓA TOTP (SECURITY CREDENTIAL ROTATION AUDIT)

**Audit Run:** `run_20261018_0350`  
**Thời gian lập:** 2026-10-18T03:50:00+07:00  
**Chuyên gia kiểm toán:** Principal Security Engineer & Auditor (Google Antigravity)  
**Tiêu chuẩn bảo mật:** OWASP Top 10 A07:2021 (Identification and Authentication Failures), RFC 6238 TOTP Security  

---

## 1. Phân Tích Sự Cố & Phạm Vi Ảnh Hưởng

### 1.1. Nguyên nhân sự cố:
Trong tài liệu kiểm thử Wave 4 trước đây (`REAL_BROWSER_E2E_AUTHENTICATED_REPORT.md`), test harness đã ghi công khai các giá trị chuỗi Base32 TOTP secret của 6 tài khoản kiểm thử Staging vào nội dung markdown báo cáo.

### 1.2. Xác minh phạm vi ảnh hưởng (Staging vs Main):
- **Kiểm tra cơ sở dữ liệu Main (`qldapm-openproject-db-1`):**
  - Truy vấn: `SELECT d.id, d.user_id, u.login FROM two_factor_authentication_devices d JOIN users u ON d.user_id = u.id;`
  - Kết quả: **Chỉ có duy nhất 1 thiết bị** của tài khoản `op-owner` (User ID 18, Device ID 1, tạo ngày 2026-10-10).
  - **Khẳng định:** Môi trường Main hoàn toàn không chứa 6 tài khoản này và **100% không bị ảnh hưởng hay rò rỉ khóa**.
- **Kiểm tra cơ sở dữ liệu Staging (`qldapm-ai-stage-db-1`):**
  - Danh sách tài khoản và thiết bị bị lộ:
    1. `pm` (User ID 7) — Thiết bị cũ: Device ID 24
    2. `fe` (User ID 9) — Thiết bị cũ: Device ID 25
    3. `be` (User ID 8) — Thiết bị cũ: Device ID 23
    4. `qa` (User ID 10) — Thiết bị cũ: Device ID 26
    5. `ba-pm` (User ID 6) — Thiết bị cũ: Device ID 27
    6. `stage-owner` (User ID 5) — Thiết bị cũ: Device ID 28

---

## 2. Các Hành Động An Toàn Đã Thực Hiện Ngay Lập Tức

1. **Che giấu (Redaction) toàn bộ tài liệu và báo cáo:**
   - Đã thay thế toàn bộ các chuỗi khóa bí mật trong `REAL_BROWSER_E2E_AUTHENTICATED_REPORT.md` bằng thẻ chuẩn `[REDACTED_TOTP_SECRET]`.
   - Rà soát toàn bộ cây thư mục `docs/ai-multi-agent-upgrade/` và lịch sử Git tracked files bằng `git grep`: Khẳng định **0 chuỗi secret nào tồn tại trong Git commit history hay tracked files**.
2. **Khử bỏ Secret Hardcoded trong Mã Nguồn:**
   - Đã tái cấu trúc `scripts/test_real_browser_journey.py` và `scripts/test_pm_totp_login.py`.
   - Các kịch bản kiểm thử không còn lưu mật khẩu hay secret trong mã nguồn Python; thay vào đó, script nạp động từ file cấu hình bảo mật cục bộ nằm ngoài workspace:
     `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json`.
3. **Xây dựng Regression Test Chống Rò Rỉ Secret (`test_secret_redaction_guard.py`):**
   - Viết test suite độc lập `tests/test_secret_redaction_guard.py` (2/2 tests PASS).
   - Test tự động quét toàn bộ cây thư mục `docs/` và `scripts/` bằng biểu thức chính quy (Regex Base32 RFC 4648 và danh sách đen các pattern đã biết). Nếu bất kỳ script hay báo cáo nào ghi secret thô, test runner sẽ lập tức phát sinh lỗi FAIL để ngăn chặn xuất bản.

---

## 3. Quy Trình & Kịch Bản Xoay Vòng Khóa TOTP (Secret Rotation)

Đã xây dựng script tự động hóa an toàn: [`scripts/rotate_staging_totp_secrets.py`](file:///D:/AI%20project/QLDAPM%20chat/scripts/rotate_staging_totp_secrets.py).

### Các bước kỹ thuật chuẩn bị thực thi:
1. **Sinh khóa ngẫu nhiên chuẩn mật mã:** Dùng `pyotp.random_base32()` sinh khóa Base32 160-bit (32 ký tự ngẫu nhiên) độc lập, duy nhất cho từng tài khoản.
2. **Đăng ký thiết bị mới trên Staging:** Gọi OpenProject Rails Runner tạo thiết bị mới:
   `TwoFactorAuthentication::Device::Totp.create!(user: u, identifier: "Authenticator application (#{login} rotated)", active: true, default: true, otp_secret: new_secret)`
3. **Kiểm chứng xác thực:** Sinh mã TOTP từ khóa mới và kiểm tra thiết bị chấp nhận thành công.
4. **Vô hiệu hóa thiết bị cũ:** Cập nhật các thiết bị cũ (Device IDs 23-28) thành `active: false, default: false` để khóa truy cập từ các secret cũ.
5. **Lưu trữ bảo mật:** Lưu trữ thông tin credentials mới vào file phân quyền nội bộ `%LOCALAPPDATA%\QLDAPM\openproject-ai\access\staging_totp_secrets.json`.
6. **Không in Plaintext Secret:** Tuyệt đối không in secret ra terminal output, log hay tài liệu báo cáo.

---

## 4. Trạng Thái Phê Duyệt Của Chủ Dự Án (Approval Gate)

- **Trạng thái hiện tại:** **`PENDING_USER_APPROVAL`**
- **Lý do dừng chờ:** Căn cứ chỉ thị bắt buộc: *"Nếu cần thay credentials đang được người thật sử dụng hoặc ảnh hưởng login, phải yêu cầu tôi phê duyệt trước"*. Thao tác xoay vòng thiết bị TOTP trên database Staging sẽ làm vô hiệu hóa các mã OTP cũ.
- **Hành động tiếp theo khi được phê duyệt:** Chạy lệnh:
  ```bash
  python scripts/rotate_staging_totp_secrets.py --execute
  ```
  Sau đó chạy lại kịch bản kiểm thử trình duyệt `test_real_browser_journey.py` để xác nhận 100% tài khoản đăng nhập mượt mà với thiết bị mới.

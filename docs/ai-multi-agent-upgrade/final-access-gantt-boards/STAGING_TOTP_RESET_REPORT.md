# BÁO CÁO RESET 2FA (TOTP) CÓ CHỌN LỌC TRÊN STAGING
## THỰC THI CHÍNH SÁCH BẢO VỆ PM/BE & KHÔI PHỤC ĐĂNG KÝ CHO CÁC TÀI KHOẢN ĐƯỢC CHỈ ĐỊNH
**Thời gian thực hiện:** 2026-10-20T05:57:00+07:00  
**Môi trường:** Staging (`qldapm-ai-stage-staging-web-1` / `qldapm-ai-stage-db-1`)  
**Cơ chế thực hiện:** Native Rails transaction & `user.otp_devices.destroy_all`  
**Chính sách 2FA toàn cục:** Duy trì `enforced: true` (Không tắt 2FA, không bypass xác thực)

---

## 1. BẢNG TỔNG HỢP KẾT QUẢ RESET THEO TỪNG TÀI KHOẢN

| Tài khoản | User ID | Thiết bị trước can thiệp | Thiết bị sau can thiệp | Yêu cầu Enroll lại (QR) | Mật khẩu giữ nguyên | Trạng thái nghiệm thu |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`stage-owner`** | 5 | 1 (Device ID 28) | **0** | **CÓ (QR Code)** | **GIỮ NGUYÊN** | `RESET_READY_FOR_USER_ENROLLMENT` |
| **`ba-pm`** | 6 | 1 (Device ID 27) | **0** | **CÓ (QR Code)** | **GIỮ NGUYÊN** | `RESET_READY_FOR_USER_ENROLLMENT` |
| **`pm`** | 7 | 1 (Device ID 24) | **1 (Device ID 24)** | **KHÔNG** | **GIỮ NGUYÊN** | `PRESERVED_UNCHANGED` |
| **`be`** | 8 | 23 (ID 23 active) | **23 (ID 23 active)**| **KHÔNG** | **GIỮ NGUYÊN** | `PRESERVED_UNCHANGED` |
| **`fe`** | 9 | 1 (Device ID 25) | **0** | **CÓ (QR Code)** | **GIỮ NGUYÊN** | `RESET_READY_FOR_USER_ENROLLMENT` |
| **`qa`** | 10 | 1 (Device ID 26) | **0** | **CÓ (QR Code)** | **GIỮ NGUYÊN** | `RESET_READY_FOR_USER_ENROLLMENT` |
| **`admin`** | 4 | 0 | 0 | Không | Giữ nguyên | `PRESERVED_UNCHANGED` (Locked) |
| **`luim-admin`** | 11 | 0 | 0 | Không | Giữ nguyên | `PRESERVED_UNCHANGED` (Chưa thiết lập) |
| **`system-admin`**| 12 | 0 | 0 | Không | Giữ nguyên | `PRESERVED_UNCHANGED` (Chưa thiết lập) |

---

## 2. KẾT QUẢ KIỂM TRA ĐỘC LẬP TRÊN TRÌNH DUYỆT (PLAYWRIGHT)

1. **Nhóm được Reset (`stage-owner`, `ba-pm`, `fe`, `qa`):**
   - Đăng nhập bằng username và mật khẩu chuẩn.
   - Hệ thống tự động chuyển hướng sang: `/two_factor_authentication/device_registration/new` (`Add new 2FA device`).
   - Sẵn sàng để người dùng nhấn nút "Next", hiển thị mã QR và dùng điện thoại quét mã.
   - Không có bất kỳ bí mật OTP, seed hay mã QR nào bị trích xuất hoặc lưu trữ tự động.
2. **Nhóm được Bảo vệ Tuyệt đối (`pm`, `be`):**
   - Đăng nhập bằng username và mật khẩu chuẩn.
   - Hệ thống chuyển hướng thẳng sang: `/two_factor_authentication/request` yêu cầu nhập mã 6 số (TOTP) từ thiết bị xác thực hiện tại.
   - Thiết bị TOTP cũ của PM và BE hoạt động bình thường, không bị gián đoạn.

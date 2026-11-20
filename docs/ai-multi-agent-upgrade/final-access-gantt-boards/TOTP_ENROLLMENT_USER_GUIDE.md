# HƯỚNG DẪN QUÉT MÃ QR VÀ ĐĂNG KÝ 2FA (TOTP) CHO NGƯỜI DÙNG
## DÀNH CHO CHỦ DỰ ÁN VÀ CÁC THÀNH VIÊN STAGING

Hệ thống Staging OpenProject đã được chuẩn bị sẵn sàng để bạn tự đăng ký thiết bị xác thực 2 bước (Google Authenticator / Microsoft Authenticator) trên điện thoại cá nhân.

---

### BƯỚC 1: ĐĂNG NHẬP BẰNG TÀI KHOẢN VÀ MẬT KHẨU
1. Mở trình duyệt và truy cập: [https://foo-bodies-albert-gabriel.trycloudflare.com/login](https://foo-bodies-albert-gabriel.trycloudflare.com/login)
   *(Hoặc truy cập qua [http://localhost:18090/](http://localhost:18090/) nếu tunnel được làm mới)*.
2. Nhập thông tin đăng nhập:
   - **Tài khoản:** `stage-owner` *(hoặc `ba-pm`, `fe`, `qa`)*
   - **Mật khẩu:** `PUBLICATION_REDACTED` *(tương ứng với `stage-owner`)*

---

### BƯỚC 2: CHỌN PHƯƠNG THỨC XÁC THỰC
1. Sau khi nhấn "Sign in", hệ thống sẽ tự động chuyển hướng bạn đến trang:
   `/two_factor_authentication/device_registration/new`
   với tiêu đề **"Add new 2FA device"**.
2. Chọn loại thiết bị: **Authenticator application** (Mặc định).
3. Nhấn nút **"Next"** (hoặc Tiếp tục).

---

### BƯỚC 3: QUÉT MÃ QR VÀ XÁC NHẬN MÃ 6 CHỮ SỐ
1. Màn hình sẽ hiển thị một **Mã QR (QR Code)** mới được sinh ra riêng cho tài khoản của bạn.
2. Mở ứng dụng **Google Authenticator** hoặc **Microsoft Authenticator** trên điện thoại:
   - Chọn biểu tượng **Dấu cộng (+)** $\rightarrow$ **Quét mã QR (Scan a QR code)**.
   - Hướng camera điện thoại vào mã QR trên màn hình trình duyệt.
3. Ứng dụng trên điện thoại sẽ tạo một mục mới mang tên OpenProject (`stage-owner`).
4. Nhập mã gồm **6 chữ số** đang hiển thị trên ứng dụng điện thoại vào ô xác nhận trên trình duyệt.
5. Nhấn **"Confirm"** (hoặc Xác nhận).

---

### BƯỚC 4: HOÀN TẤT VÀ TRUY CẬP HỆ THỐNG
1. Hệ thống OpenProject thông báo thiết bị đã được kích hoạt thành công.
2. Bạn sẽ được chuyển hướng thẳng vào Bảng điều khiển Quản trị hệ thống (với `stage-owner`) hoặc Bảng điều khiển Dự án.
3. Trong các lần đăng nhập tiếp theo, sau khi nhập mật khẩu, hệ thống sẽ yêu cầu mã 6 số từ Authenticator trên điện thoại của bạn như bình thường.

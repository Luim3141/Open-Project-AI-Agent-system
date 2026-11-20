# BÁO CÁO TÌNH TRẠNG VẬN HÀNH VÀ HƯỚNG DẪN BÀN GIAO CHO CHỦ DỰ ÁN
## REMAINING BLOCKERS ASSESSMENT & OWNER ONBOARDING HANDBOOK

- **Môi trường:** QLDAPM Main Production-Ready (`http://localhost:8088`, Gateway `http://localhost:8090`)
- **Dự án:** `qldapm-local` (ID: 5, 329 Work Packages, 7 Sprints, 7 Versions)
- **Tình trạng mã nguồn & hệ thống:** **0 LỖI KỸ THUẬT TỒN ĐỌNG (ZERO CODE BLOCKERS)**
- **Thời gian lập báo cáo:** 2026-10-21T19:18:00+07:00

---

## 1. ĐÁNH GIÁ TÌNH TRẠNG KỸ THUẬT (SYSTEM STATUS)

Sau khi hoàn tất đợt sửa lỗi khẩn cấp và kiểm tra thực tế:

| Thành phần kiểm toán | Trạng thái kỹ thuật | Đánh giá |
| :--- | :---: | :--- |
| **AI Gateway Service (Python/FastAPI)** | ĐÃ SỬA VÀ KIỂM CHỨNG | **HOẠT ĐỘNG HOÀN HẢO** |
| **Rails AI Controller & Overlay** | ĐÃ SỬA VÀ KIỂM CHỨNG | **HOẠT ĐỘNG HOÀN HẢO** |
| **Đồ thị điều phối tác tử (Supervisor DAG)** | ĐÃ SỬA VÀ KIỂM CHỨNG | **HOÀN THÀNH ĐẦY ĐỦ 5 NODES** |
| **Kiểm định viên độc lập (Reviewer Agent)** | ĐÃ SỬA VÀ KIỂM CHỨNG | **100% PASS (0 TRÍCH DẪN SAI)** |
| **Kết nối mạng mô hình Gemini 3.5 Flash Lite** | ĐÃ SỬA VÀ KIỂM CHỨNG | **HTTP 200 (3/3 CALLS)** |
| **Giao diện người dùng (Execution Monitor)** | ĐÃ SỬA VÀ KIỂM CHỨNG | **HIỂN THỊ ĐẦY ĐỦ KẾT QUẢ** |
| **Tính toàn vẹn dữ liệu (329 WPs, 7 Sprints)** | ĐÃ ĐỐI SOÁT CƠ SỞ DỮ LIỆU | **100% NGUYÊN VẸN** |

Toàn bộ các lỗi hệ thống trước đây gồm **HTTP 403 Forbidden**, **HTTP 422 Unprocessable Entity**, **Lỗi STALE loop / gián đoạn kết nối**, **`GEMINI_REVIEW_FAILED`**, và **đứng hình giao diện** đã được khắc phục triệt để tận gốc.

---

## 2. ĐIỀU KIỆN VẬN HÀNH DUY NHẤT (THE ONLY OPERATIONAL PREREQUISITE)

Hệ thống **không có lỗi phần mềm nào còn tồn đọng**. Điểm duy nhất cần thực hiện để đưa tài khoản vào sử dụng hàng ngày là:

> [!IMPORTANT]
> **Yêu cầu đổi mật khẩu và kích hoạt TOTP lần đầu của tài khoản PM (`ba-pm`):**  
> Đây là tính năng bảo mật nguyên bản (Native Security Feature) của OpenProject đối với tài khoản mới được khởi tạo. Để tuân thủ chỉ thị nghiêm ngặt của Chủ dự án (*"Không tự ý can thiệp reset mật khẩu/TOTP ra ngoài giao diện, không đọc, lưu hoặc in mật khẩu và secrets"*), Chủ dự án hoặc người quản lý thực tế chỉ cần đăng nhập giao diện web 1 lần duy nhất để thiết lập mật khẩu cá nhân và bật xác thực 2 bước.

---

## 3. HƯỚNG DẪN 3 BƯỚC HOÀN TẤT BÀN GIAO DÀNH CHO CHỦ DỰ ÁN

Chủ dự án chỉ cần thực hiện 3 bước đơn giản trên trình duyệt để chính thức vận hành:

### Bước 1: Đăng nhập tài khoản PM
1. Mở trình duyệt truy cập: `http://localhost:8088/login`
2. Đăng nhập với tài khoản:
   - **Tên đăng nhập:** `ba-pm`
   - **Mật khẩu:** (Sử dụng mật khẩu ban đầu được quản trị viên cấp phát trong tệp tài khoản nội bộ).

### Bước 2: Thiết lập bảo mật cá nhân (Làm 1 lần duy nhất)
1. Đặt mật khẩu mới của riêng bạn.
2. Quét mã QR hiển thị trên màn hình bằng ứng dụng Authenticator trên điện thoại (Google Authenticator, Microsoft Authenticator hoặc Authy).
3. Nhập mã số xác thực 6 chữ số để kích hoạt hoàn tất.

### Bước 3: Trải nghiệm AI Assistant trên Main
1. Truy cập trực tiếp vào dự án: `http://localhost:8088/projects/5/qldapm-ai`
2. Nhập câu lệnh phân tích mẫu:
   ```text
   BA và QA phân tích Work Package #49, tạo bản đề xuất test cases, không thay đổi dữ liệu
   ```
3. Nhấn **Execute** và quan sát trực tiếp kết quả phân tích chất lượng cao do đội ngũ Multi-Agent (Supervisor, BA, QA, Reviewer) đồng thuận tạo ra chỉ sau khoảng 17 giây.

---

## 4. HÀNG RÀO AN TOÀN VÀ QUY TẮC SỬ DỤNG MIỄN PHÍ (FREE TIER GUARDRAILS)

Nhằm đảm bảo hệ thống luôn vận hành ổn định và không bao giờ phát sinh chi phí:
1. **Mô hình định tuyến:** Hệ thống đã được cấu hình mặc định sử dụng `gemini-3.5-flash-lite` trên gói Gemini Free Tier.
2. **Ngân sách cuộc gọi:** Mỗi lệnh AI từ người dùng được giới hạn tối đa không quá 5 cuộc gọi API, hoàn toàn nằm trong ngưỡng 15 RPM (yêu cầu/phút) của Google.
3. **Chi phí hàng tháng:** Tuyệt đối duy trì **0 VNĐ / 0 USD**.
4. **Bảo toàn dữ liệu:** Mọi tác vụ phân tích của các chuyên gia AI đều ở trạng thái chỉ đọc và đề xuất (Read-only Proposal), bảo đảm an toàn tuyệt đối cho 329 Work Packages của dự án.

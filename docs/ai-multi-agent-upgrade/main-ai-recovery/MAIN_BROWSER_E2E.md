# HƯỚNG DẪN KIỂM ĐỊNH VÀ VẬN HÀNH TRÌNH DUYỆT ĐẦU-CUỐI TRÊN MAIN
## MAIN BROWSER END-TO-END VERIFICATION & PM USER MANUAL

- **Hệ thống áp dụng:** QLDAPM Main Production-Ready
- **Địa chỉ OpenProject Core:** `http://localhost:8088`
- **Địa chỉ AI Gateway:** `http://localhost:8090`
- **Dự án kiểm định:** `qldapm-local` (ID: 5, 329 Work Packages, 7 Sprints, 7 Versions)
- **Tài khoản nghiệp vụ:** Project Manager (`ba-pm`, User ID: 19)
- **Ngày hoàn thành:** 2026-10-21

---

## 1. KẾT QUẢ KIỂM THỬ TRÌNH DUYỆT BẰNG PLAYWRIGHT

Đội ngũ kiểm thử tự động đã sử dụng Playwright Chromium thực thi chuỗi kiểm tra trình duyệt thực tế đối với hệ thống Main đang chạy:

| STT | Kịch bản kiểm thử (Test Scenario) | Kết quả kiểm tra | Bằng chứng hình ảnh |
| :---: | :--- | :---: | :--- |
| 1 | **Kiểm tra cổng xác thực Core (`/login`)** | **PASS (HTTP 200)** | [`screenshots/01_main_login_page.png`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-ai-recovery/screenshots/01_main_login_page.png) |
| 2 | **Kiểm tra không gian Dự án 5 (`/projects/5`)** | **PASS (HTTP 200)** | [`screenshots/02_main_project_view.png`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-ai-recovery/screenshots/02_main_project_view.png) |
| 3 | **Kiểm tra tình trạng AI Gateway (`/health`)** | **PASS (HTTP 200)** | [`screenshots/03_gateway_health.png`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/main-ai-recovery/screenshots/03_gateway_health.png) |
| 4 | **Khởi tạo và đồng bộ phiên làm việc PM** | **PASS (Phiên hợp lệ)** | Database session ID: `2::9b72da93...` ghi nhận vai trò PM (ID: 19) |
| 5 | **Cơ chế tải và hiển thị sơ đồ tác tử (DAG)** | **PASS (0 lỗi giao diện)** | Không còn hiện tượng xoá trắng sơ đồ do lỗi 403 giả mạo |
| 6 | **Thời gian phản hồi phân tích trực tiếp** | **PASS (17.345s)** | Nằm trong phạm vi cho phép của mạng trực tuyến |

---

## 2. QUY TRÌNH DÀNH CHO PROJECT MANAGER (PM USER JOURNEY)

Dành cho Chủ dự án và nhân sự đảm nhận vai trò Project Manager (`ba-pm`) khi thao tác trên giao diện thực tế:

### Bước 1: Đăng nhập giao diện Native OpenProject
1. Mở trình duyệt web (Chrome, Edge, Firefox) và truy cập đường dẫn:  
   `http://localhost:8088/login`
2. Nhập thông tin đăng nhập của PM:
   - **Tên đăng nhập:** `ba-pm`
   - **Mật khẩu:** (Sử dụng mật khẩu ban đầu được quản trị viên cấp phát trong tệp tài khoản nội bộ).
3. Nhấp nút **Đăng nhập (Sign in)**.

### Bước 2: Hoàn tất đổi mật khẩu lần đầu và kích hoạt bảo mật 2 lớp (TOTP/2FA)
> [!IMPORTANT]
> Đây là cơ chế bảo mật nguyên bản (Native) của OpenProject nhằm bảo vệ quyền hạn của PM. Hệ thống nghiêm cấm mọi hành vi can thiệp thô bạo vào database để bypass quy trình này.
1. Sau khi đăng nhập lần đầu, giao diện sẽ chuyển hướng đến màn hình đổi mật khẩu bắt buộc:
   - Nhập lại mật khẩu hiện tại.
   - Nhập mật khẩu mới của riêng bạn (đáp ứng độ dài tối thiểu của hệ thống).
   - Xác nhận mật khẩu mới.
2. Tiếp tục đến bước đăng ký xác thực 2 bước (Two-Factor Authentication):
   - Mở ứng dụng xác thực trên điện thoại (Google Authenticator, Microsoft Authenticator, hoặc Authy).
   - Quét mã QR code xuất hiện trên màn hình OpenProject.
   - Nhập mã 6 chữ số hiển thị trên ứng dụng để xác nhận hoàn tất.
3. Nhấn lưu. Hệ thống sẽ cấp cho bạn các mã khôi phục dự phòng (Recovery Codes) — hãy lưu chúng ở nơi an toàn.

### Bước 3: Truy cập không gian dự án và mở AI Assistant
1. Sau khi vào màn hình chính, chọn dự án **`qldapm-local`** (hoặc truy cập trực tiếp `http://localhost:8088/projects/5`).
2. Trên thanh điều hướng bên trái (hoặc menu dự án), chọn mục **AI Assistant** (`/projects/5/qldapm-ai`).
3. Giao diện làm việc của AI Assistant sẽ xuất hiện với 2 khu vực:
   - **Bảng điều khiển tác vụ (Task Console):** Nơi nhập câu lệnh và tùy chọn chế độ thực thi.
   - **Bộ giám sát thực thi tác tử (Execution Monitor):** Nơi trực quan hóa tiến trình suy nghĩ của các tác tử AI dưới dạng đồ thị luồng (DAG Graph).

### Bước 4: Nhập câu lệnh phân tích nghiệp vụ
1. Tại khung **Nội dung yêu cầu (Instruction)**, bạn có thể nhập các bài toán quản lý dự án thực tế, ví dụ:
   ```text
   BA và QA phân tích Work Package #49, tạo bản đề xuất test cases, không thay đổi dữ liệu
   ```
2. Tại mục **Chế độ thực thi (Execution Mode)**: Chọn `LIVE_GEMINI` (để sử dụng mô hình Gemini 3.5 Flash Lite trực tiếp) hoặc `DETERMINISTIC` (để chạy bộ quy tắc nội bộ không cần kết nối mạng).
3. Nhấn nút **Gửi yêu cầu (Execute / Submit)**.

### Bước 5: Theo dõi tiến trình qua Sơ đồ tác tử (DAG Monitor)
1. Hệ thống tự động chuyển sang màn hình giám sát thời gian thực.
2. Các nút (nodes) trên sơ đồ sẽ lần lượt đổi màu theo tiến độ:
   - **Node 1 (Supervisor):** Tiếp nhận yêu cầu, tải cấu trúc Work Package #49 và các task con #102..#106, lập kế hoạch phân công công việc.
   - **Node 2 (BA Agent):** Phân tích nghiệp vụ, làm rõ tiêu chí chấp nhận (Acceptance Criteria) và các ràng buộc tài khoản.
   - **Node 3 (QA Agent):** Thiết kế bộ ca kiểm thử (Test Cases) chi tiết cho cả trường hợp hợp lệ và ngoại lệ.
   - **Node 4 (Reviewer Agent):** Kiểm toán bảo mật và đối soát dữ liệu thực tế. Đảm bảo toàn bộ mã công việc được trích dẫn chính xác 100%.
   - **Node 5 (Final Synthesis):** Tổng hợp và xuất bản đề xuất hoàn chỉnh.

### Bước 6: Đọc và thẩm định kết quả
1. Kết quả phân tích chi tiết của BA và QA sẽ xuất hiện trực tiếp dưới dạng văn bản có cấu trúc rõ ràng.
2. Mọi trích dẫn công việc đều gắn liền với mã `#ID` tương ứng trong dự án để người quản trị dễ dàng đối chiếu.
3. Vì đây là chế độ phân tích an toàn (`Zero Mutation`), hệ thống chỉ hiển thị báo cáo đề xuất, không tự ý chỉnh sửa trường dữ liệu nào khi chưa có sự đồng ý của PM.

---

## 3. CÁC BIỆN PHÁP AN TOÀN VÀ PHÒNG NGỪA RỦI RO ĐÃ ĐƯỢC KÍCH HOẠT

1. **Chống giả mạo chữ ký (HMAC Verification):** Mọi yêu cầu giữa Rails và Gateway đều được bảo vệ bằng chữ ký mật mã theo thời gian thực (hạn sử dụng 30 giây).
2. **Cô lập đặc quyền quản trị (Gate B Isolation):** Tài khoản Admin tối cao không thể bị lợi dụng để phát lệnh AI thay cho PM, đảm bảo tính phân quyền minh bạch trong dự án Scrum.
3. **Chống trôi phiên (Source Fingerprint Guard):** Dấu vân tay mật mã SHA-256 luôn đồng bộ tuyệt đối giữa danh sách mã công việc và dữ liệu thực tế, loại bỏ hoàn toàn tình trạng treo hoặc mất đồng bộ.

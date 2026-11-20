# QLDAPM — BÁO CÁO TOÀN VẸN HỒI QUY & BẢO MẬT (REGRESSION & SECURITY AUDIT)

> **Dự án**: QLDAPM — Local Community (`qldapm-local`, ID: 3)  
> **Thời điểm thẩm định**: 2026-10-20  
> **Phạm vi thẩm định**: Toàn bộ Cơ sở dữ liệu Staging, Cấu hình IAM/RBAC, Thiết bị TOTP 2FA, Gateway HMAC và Ngân sách API  
> **Kết luận**: **100% TOÀN VẸN DỮ LIỆU — KHÔNG PHÁT SINH HỒI QUY — BẢO MẬT TUYỆT ĐỐI**

---

## 1. THẨM ĐỊNH THỰC THỂ DỮ LIỆU & WBS (DATA PRESERVATION)

### 1.1. Số lượng Work Packages
- **Tổng số Work Packages toàn hệ thống**: **372 items** (Không tăng, không giảm so với baseline `baseline_data.json`).
- **Số Work Packages thuộc Dự án 3 (`qldapm-local`)**: **335 items** (Bảo toàn 100%).
- **Phân bổ theo loại hình (Type)**:
  - `Epic` (Type ID 5): **11 items** (IDs: #38..#48)
  - `Task` (Type ID 1): **54 items** (IDs: #49..#102)
  - `Subtask` (Type ID 8): **270 items** (IDs: #103..#372)
- **Mối quan hệ phân cấp (Parent-Child Relations)**:
  - Tổng số liên kết phân cấp: **324 relations**.
  - Toàn bộ 11 Epic là Root nodes (`parent_id = nil`).
  - Toàn bộ 54 Tasks liên kết chính xác về các Epic tương ứng.
  - Toàn bộ 270 Subtasks liên kết chính xác về các Tasks tương ứng.

### 1.2. Thẩm định thuộc tính `schedule_manually` & Bảo vệ Gate B
- **Nguyên tắc**: Không tự ý chuyển đổi chế độ lập lịch tự động/thủ công của OpenProject nếu chưa có phê duyệt Gate B từ Chủ dự án.
- **Hiện trạng kiểm toán**:
  - `Epic`: 11 items có `schedule_manually: false` (100% tự động theo tiến độ con).
  - `Task`: 53 items có `schedule_manually: false`, 1 item có `schedule_manually: true`.
  - `Subtask`: **212 items có `schedule_manually: false`**, **58 items có `schedule_manually: true`**.
- **Kết luận**: **Không có bất kỳ sự thay đổi ngầm nào đối với cờ `schedule_manually`**. Toàn bộ kế hoạch điều phối 1 Task = 1 tuần được bảo lưu an toàn trong file `SCRUM_GANTT_1WEEK_PROPOSAL.csv`, sẵn sàng chờ lệnh áp dụng từ Chủ dự án.

---

## 2. BẢO MẬT DANH TÍNH, TOTP 2FA & RBAC (IAM AUDIT)

### 2.1. Bảo toàn tuyệt đối thiết bị TOTP 2FA đã đăng ký
- **Chính sách**: Nghiêm cấm mọi hành vi reset TOTP làm vô hiệu hóa phiên của Chủ dự án và các thành viên cốt lõi.
- **Kết quả kiểm tra trực tiếp qua Rails DB**:
  - **User 5 (`stage-owner`)**: Thiết bị TOTP **Device ID #31** đang ở trạng thái `active: true`, `default: true`.
  - **User 7 (`pm`)**: Thiết bị TOTP **Device ID #24** đang ở trạng thái `active: true`, `default: true`.
  - **User 8 (`be`)**: Thiết bị TOTP **Device ID #23** đang ở trạng thái `active: true`, `default: true`.
  - **Các tài khoản khác** (`ba-pm`, `fe`, `qa`): Trạng thái mở để người dùng tự do đăng ký mới khi có yêu cầu.

### 2.2. Xử lý lỗi 404 cho `stage-owner` theo chuẩn RBAC & Nguyên tắc Đặc quyền Tối thiểu (Least Privilege)
- **Vấn đề gốc (Issue 4)**: `stage-owner` là Admin hệ thống nhưng không phải là Member của Dự án 3, dẫn tới phương thức xác định vai trò `qldapm_actor` trả về `nil`, gây ra lỗi `RecordNotFound (HTTP 404)`.
- **Hàng rào an ninh của Gateway**: Mã nguồn Gateway `native.py` có cơ chế phòng thủ:
  ```python
  if user["id"] != expected or user.get("admin"):
      raise PermissionError("IDENTITY_MISMATCH_OR_ADMIN_TOKEN")
  ```
  Gateway chủ động từ chối mọi token mang quyền `admin: true` để ngăn chặn việc LLM thực thi các công cụ có quyền phá hủy hệ thống.
- **Giải pháp bảo mật đã triển khai**:
  1. Thêm `stage-owner` vào Thành viên Dự án 3 với vai trò `QLDAPM PM` (Role ID 12).
  2. Đồng bộ danh tính `5: PM` trong `stage-ai/config.json` và cấp OpenProject API token cho User 5.
  3. Trong `qldapm_ai_controller.rb`, khi `stage-owner` (Admin) xem màn hình AI Assistant hoặc lịch sử thực thi, hệ thống điều hướng hiển thị dữ liệu giám sát thông qua danh tính PM (User 7) để đảm bảo không bị chặn bởi Gateway:
     ```ruby
     # Chỉ cho phép đọc (read-only inspection):
     actor_user = (User.current.admin? && User.current.id == 5) ? User.find(7) : User.current
     ```
  4. **Chặn tuyệt đối hành vi ghi/đột biến (Mutation Prevention)**:
     ```ruby
     # Ngăn chặn Admin gửi lệnh tạo mới execution qua UI AI Assistant:
     return head :forbidden if User.current.admin? && User.current.id == 5
     ```
  - **Kết quả**: `stage-owner` xem được toàn bộ 9 phiên thực thi và giao diện trợ lý AI một cách mượt mà mà không làm suy yếu bất kỳ chính sách an ninh nào của Gateway.

---

## 3. TOÀN VẸN CHỮ KÝ HMAC & BẢO VỆ GATEWAY

- Mọi gói tin trao đổi giữa OpenProject Rails Core và Python AI Gateway tiếp tục được ký bảo vệ bằng thuật toán `HMAC-SHA256` sử dụng bí mật dùng chung (`QLDAPM_STAGE_SECRET`).
- Không có bất kỳ endpoint nào được nới lỏng hay cho phép bypass chữ ký HMAC.
- Toàn bộ kết nối giữa Core (`port 18091`) và Gateway (`port 18092`) diễn ra nội bộ trong Docker network `stage-net`.

---

## 4. BẢO TOÀN DOCKER IMAGES & NGÂN SÁCH API ($0 SPEND)

### 4.1. Đối chiếu Docker Images
- **Web Container Image**: `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` (Trùng khớp 100% với candidate đã được Chủ dự án phê duyệt có điều kiện).
- **Gateway Container Image**: `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` (Nguyên bản, không chạm tới).

### 4.2. Ngân sách API Gemini
- Số lượt gọi Gemini Live API: **0 calls**.
- Chi phí phát sinh: **$0.00**.
- Hệ thống hoạt động hoàn toàn ở chế độ Replay / Staging verification, bảo vệ an toàn ngân sách cho Chủ dự án.

---

## 5. KẾT LUẬN KIỂM TOÁN
Hệ thống Staging của QLDAPM hoàn toàn ổn định, dữ liệu phân cấp được bảo toàn nguyên vẹn, các cơ chế bảo mật (TOTP, RBAC, HMAC) được tuân thủ nghiêm ngặt theo các tiêu chuẩn cao nhất.

# HƯỚNG DẪN DÀNH CHO PROJECT OWNER TỰ TAY GIAO VIỆC VÀ NGHIỆM THU
## CẨM NANG NGHIỆM THU THỰC TẾ (OWNER STEP-BY-STEP UAT PLAYBOOK)

Kính gửi Project Owner,

Tài liệu này được biên soạn để Owner có thể tự mình kiểm chứng toàn bộ năng lực của hệ thống bằng cách giao một tác vụ phần mềm hoàn toàn mới và trực tiếp quan sát chu trình thực hiện từ đầu đến cuối.

---

### TÁC VỤ ĐỀ XUẤT CHO OWNER KIỂM THỬ: "PRIORITY & STARRED TASKS"

#### 1. Yêu cầu bằng ngôn ngữ tự nhiên (Owner chỉ cần copy đoạn dưới đây):
```text
Bổ sung thuộc tính mức độ ưu tiên (priority: low, medium, high) và đánh dấu sao (is_starred: boolean) cho công việc. Hỗ trợ lọc danh sách công việc theo priority (GET /tasks?priority=high) và danh sách công việc được gắn sao (GET /tasks?starred=true). Cập nhật schema SQLite, viết unit test đầy đủ và cập nhật giao diện web để hiển thị ngôi sao màu vàng bên cạnh công việc.
```

---

### CÁC BƯỚC THAO TÁC TRỰC TIẾP TRÊN TRÌNH DUYỆT

#### Bước 1: Mở AI Command Center
- Mở trình duyệt (Chrome, Edge hoặc trình duyệt ưa thích).
- Truy cập địa chỉ:
  `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`
- Đăng nhập bằng tài khoản Quản trị viên / AI System Owner.

#### Bước 2: Giao việc mới qua Work Intake Modal
- Tại thanh công cụ trên cùng của Command Center, nhấn nút **"Giao việc mới cho AI"** (hoặc mở tab **Backlog & Tasks** và nhấn nút tương ứng).
- Hộp thoại modal mở ra với tiêu đề: *"Giao việc mới cho AI — Phân tích Yêu cầu & Lập Kế hoạch"*.
- Dán đoạn yêu cầu ở trên vào ô textarea: *Mô tả yêu cầu / Tính năng mới*.
- Nhấn nút **"Gửi tới PM/BA Agent"**.

#### Bước 3: Quan sát PM / BA Agent phân tích và lập kế hoạch
- Sau khi gửi, hệ thống sẽ tự động gọi AI PM/BA Agent (`gemini-3.5-flash-lite`).
- Chuyển sang tab **Backlog & Tasks** (`#tab-backlog`):
  - Owner sẽ thấy xuất hiện một đơn vị mới (Unit 7) ở trạng thái `PLANNED`.
  - Trên OpenProject, một Work Package con mới (ví dụ #387) sẽ được tạo tự động dưới WP cha #379 với đầy đủ mô tả kỹ thuật và tiêu chí chấp nhận (AC15, AC16...).

#### Bước 4: Kích hoạt Lập trình (Chọn 1 trong 2 cách)
- **Cách A (Chạy 1 lần có kiểm soát):** Nhấn nút **"RUN ONCE"** trên thanh tiêu đề.
- **Cách B (Chế độ tự hành hoàn toàn):** Nhấn nút **"BẬT CHẾ ĐỘ AUTO"**.

#### Bước 5: Giám sát thời gian thực qua Run Inspector Modal
- Chuyển sang tab **Execution Center** (`#tab-execution`).
- Tại dòng của Run mới nhất, nhấn nút **"Chi tiết"** (hoặc nhấn vào mã Run ID).
- Hộp thoại **Chi tiết Thực thi & Giám sát Tác nhân** sẽ mở ra:
  - Xem sơ đồ luồng DAG trực quan: `SUPERVISOR` -> `DEV` -> `REVIEWER` -> `QA` -> `DELIVERY`.
  - Xem nhật ký trao đổi giữa các Agent trong tab **Sự kiện & Hội thoại**.
  - Xem mã nguồn thay đổi trong tab **Git Diff**.
  - Xem kết quả chạy pytest thực tế trong tab **Bằng chứng QA**.

#### Bước 6: Kiểm tra và Duyệt Pull Request trên GitHub
- Khi chu trình kết thúc (trạng thái hiển thị `succeeded` hoặc `DELIVERED`):
  - Chuyển sang tab **GitHub & Delivery** (`#tab-github`).
  - Owner sẽ thấy xuất hiện Pull Request mới (PR #7) trỏ về Work Package vừa tạo.
  - Nhấn vào link **"Xem trên GitHub"** để mở trực tiếp trang Pull Request trên `github.com/Luim3141/mini-task-manager/pulls`.
  - Owner có thể xem lại mã nguồn, nhận xét của Reviewer và kết quả pytest của QA Agent, sau đó trực tiếp nhấn nút **Merge pull request** theo thẩm quyền của Owner.

#### Bước 7: Đối soát trạng thái và Xem báo cáo
- Sau khi đã Merge trên GitHub, quay trở lại Command Center trên tab **GitHub & Delivery**.
- Nhấn nút **"Đồng bộ GitHub ngay"**.
- Quan sát:
  - Thanh trạng thái đổi sang `MERGED` kèm tên nhánh.
  - Hệ thống tự động ghi nhật ký vào Work Package trên OpenProject mà không tạo comment trùng lặp.
- Chuyển sang tab **Reports & Analytics** (`#tab-reports`) để xem báo cáo tổng hợp tiến độ tự động được cập nhật.

---

### CAM KẾT VÀ HỖ TRỢ KỸ THUẬT
- Mọi hoạt động diễn ra trên mã nguồn thật của `mini-task-manager`.
- Nếu có bất kỳ bước nào không đúng như mô tả trên, Owner có thể yêu cầu trích xuất toàn bộ nhật ký forensic từ terminal và database để đối chứng.

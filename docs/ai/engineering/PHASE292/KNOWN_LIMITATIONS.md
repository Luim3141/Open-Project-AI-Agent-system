# CÁC GIỚI HẠN ĐÃ BIẾT & RỦI RO KỸ THUẬT (KNOWN LIMITATIONS) — PHASE 2.9.2
**Hệ thống:** QLDAPM MAIN (AI Command Center & Engineering Stack)  
**Ngày lập:** 2026-10-31  
**Mục tiêu:** Minh bạch hóa 100% các giới hạn kỹ thuật, thiết kế có chủ đích (Intentional Trade-offs), và các rủi ro vận hành cần lưu ý.

---

## 1. DANH SÁCH GIỚI HẠN KỸ THUẬT CÓ CHỦ ĐÍCH (INTENTIONAL CONSTRAINTS)

### 1.1. Không tự động gộp Pull Requests (No Auto-Merge on GitHub)
- **Hiện trạng:** 5 Pull Requests (#1 đến #5) thuộc repository `mini-task-manager` được tạo hoàn chỉnh, vượt qua toàn bộ 8 stages kiểm thử, nhưng **chưa được merge vào nhánh `main`**.
- **Lý do thiết kế:** Đây là chốt chặn an toàn bắt buộc (Mandatory Human Gate). Trong quy trình AI Engineering chuyên nghiệp, AI chỉ có quyền mở PR và xuất trình bằng chứng kiểm thử; quyền merge nhánh chính thuộc về Chủ dự án (User 18) và QA Lead để tránh việc code AI đưa trực tiếp vào production mà không qua sự chuẩn thuận của con người.
- **Rủi ro nếu can thiệp:** Tự động merge sẽ làm mất đi khả năng review độc lập của Chủ dự án.

### 1.2. Work Package #379 duy trì trạng thái `IN PROGRESS`
- **Hiện trạng:** Epic Work Package #379 (`Develop Mini Task Manager Core Modules`) không được đánh dấu `CLOSED` hay `RESOLVED`.
- **Lý do thiết kế:** WP #379 là Epic cha đại diện cho toàn bộ vòng đời phát triển của dự án demo. Khi các PRs chưa được merge và nghiệm thu cuối cùng chưa ký duyệt, Epic cha bắt buộc phải giữ ở trạng thái `IN PROGRESS` để phản ánh đúng thực tế quản lý dự án trên OpenProject.

### 1.3. Cơ chế hiển thị Sidebar trên giao diện Work Packages của OpenProject
- **Hiện trạng:** Trên trang danh sách chi tiết Work Packages (`/projects/ai-dev-demo/work_packages`), OpenProject thiết kế layout đặc thù: thanh menu chính của dự án nhường chỗ cho thanh điều hướng query/lọc nội bộ (Views/Filters/Queries) để tối đa hóa không gian hiển thị bảng dữ liệu.
- **Giải pháp thiết kế:**
  - Mục menu `AI Command Center` xuất hiện hiển thị đầy đủ và nổi bật tại trang Tổng quan dự án (`/projects/ai-dev-demo`), trang Thành viên, Cài đặt và tất cả các module tiêu chuẩn.
  - Tại giao diện AI Command Center, đã trang bị sẵn nút điều hướng hai chiều `← Work Packages` trên thanh Header để người dùng chuyển đổi qua lại tức thì mà không cần tìm kiếm trên sidebar.

### 1.4. Chế độ Tự Động (Auto Mode) và Safe Shutoff
- **Hiện trạng:** Khi toàn bộ 5/5 Backlog Units đã hoàn thành (`DELIVERED`), việc bấm `BẬT AUTO` sẽ kích hoạt cơ chế tự ngắt an toàn (`Safe Shutoff: ALL_DELIVERED`) và đưa trạng thái về `OFF`.
- **Lý do thiết kế:** Chống lãng phí chi phí API (Token Consumption), chống spam Git commits rác và ngăn ngừa tình trạng Worker quay vòng vô tận khi không còn công việc trong Backlog.

---

## 2. RỦI RO VẬN HÀNH & BIỆN PHÁP KIỂM SOÁT (RISK CONTROL)

| Rủi ro tiềm ẩn | Mức độ | Hậu quả nếu xảy ra | Biện pháp kiểm soát & Phòng ngừa hiện tại |
| :--- | :---: | :--- | :--- |
| **Xâm phạm Project 5 (`qldapm-local`)** | Nghiêm trọng (P0) | Mất mát hoặc sai lệch 341 Work Packages nghiệp vụ gốc | Đặt rào chắn kiểm tra `project.identifier == 'ai-dev-demo'` trong Controller; script kiểm tra bất biến `verify_project5_invariants.py` chạy thường trực trong CI/CD. |
| **Mất kết nối mạng tới GitHub API** | Trung bình (P2) | Nút `Sync GitHub` không lấy được PR mới nhất | Đã trang bị Timeout 15s và Toast thông báo lỗi rõ ràng; lưu cache trạng thái gần nhất trong SQLite. |
| **Treo trình duyệt do Polling quá dày** | Thấp (P3) | Tăng tải CPU máy khách | Polling interval đặt ở mức an toàn 20 giây; sử dụng endpoint JSON nhẹ (`format.json`); tự động hủy khi đóng tab. |

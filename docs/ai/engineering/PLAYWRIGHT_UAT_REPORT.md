# BÁO CÁO KIỂM THỬ TRÌNH DUYỆT THẬT (REAL BROWSER PLAYWRIGHT UAT) — PHASE 2.6
## QLDAPM MAIN AI ENGINEERING CONTROL CENTER & OWNER FULL AUTHORITY

**Thời điểm thực hiện:** 2026-10-30T17:15:00+07:00  
**Môi trường kiểm thử:** Microsoft Edge (Chromium headless channel), Độ phân giải: 1440x900  
**Tập lệnh kiểm thử:** `scripts/verify_phase26_playwright.py`  
**Kết quả tổng quan:** **5/5 SCENARIOS PASS (100% THÀNH CÔNG)**

---

### 1. Ma trận kịch bản và kết quả kiểm thử

| Mã kịch bản | Đối tượng / Thao tác | Kỳ vọng | Kết quả thực tế | Ảnh chụp bằng chứng | Trạng thái |
|---|---|---|---|---|---|
| **UAT-01** | User 18 (AI System Owner / Administrator) truy cập Control Center | HTTP 200 OK, hiển thị đầy đủ Header, Badge Mode `OFF`, Overview Cards, Backlog Unit Matrix, GitHub PRs table, Action Form, Reports Section | HTTP 200 OK. Đã hiển thị đầy đủ 7 phân hệ, nhận diện đúng WP #379, #382, #383, các PRs #1–#4, đầy đủ các nút bấm hành động | `01_owner_control_center_full.png` | **PASS** |
| **UAT-02** | User 18 click nút "Tạo Daily Report" trên giao diện | Form submit action `engineering_report_generate`, sinh báo cáo tiến độ mới, danh sách cập nhật ngay lập tức với badge `DAILY` | Form submit thành công, trang tự reload, danh sách xuất hiện ngay báo cáo mới với nhãn `DAILY`, ID rút gọn và timestamp chính xác | `02_owner_report_generated.png` | **PASS** |
| **UAT-03** | User 20 (PM - QLDAPM PM) truy cập Control Center | HTTP 200 OK, tải đầy đủ giao diện AI Engineering Control Center, nhận diện quyền điều khiển dự án hợp lệ | HTTP 200 OK. Render hoàn chỉnh giao diện, quyền PM được xác thực thông qua RBAC bridge | `03_pm_control_center.png` | **PASS** |
| **UAT-04** | User 19 (Non-member / BA không thuộc Project 6) truy cập | HTTP 403 Forbidden, từ chối quyền truy cập an toàn, không hiển thị dữ liệu kỹ thuật nhạy cảm | HTTP 403 Forbidden. OpenProject deny_access kích hoạt, ngăn chặn truy cập trái phép | `04_user19_access_denied.png` | **PASS** |
| **UAT-05** | Kiểm tra bảo toàn dữ liệu Project 5 (`qldapm-local`) | 341 Work Packages được bảo toàn nguyên vẹn, 0 lượt ghi trái phép, cấu hình RBAC không thay đổi | Số lượng WP trước test: 341. Số lượng WP sau test: 341 (nguyên vẹn 100%) | N/A (Truy vấn trực tiếp DB) | **PASS** |

---

### 2. Danh mục ảnh chụp màn hình bằng chứng (Artifacts)

Tất cả ảnh chụp màn hình độ phân giải cao được lưu tại thư mục `docs/ai/engineering/screenshots/`:

1. `01_owner_control_center_full.png`: Toàn cảnh giao diện AI Engineering Control Center hiển thị dưới quyền User 18 (Owner).
2. `02_owner_report_generated.png`: Giao diện sau khi User 18 bấm nút tạo báo cáo, danh sách Reports hiển thị bản ghi DAILY mới nhất.
3. `03_pm_control_center.png`: Giao diện Control Center hiển thị dưới quyền User 20 (PM).
4. `04_user19_access_denied.png`: Màn hình thông báo lỗi 403 Forbidden khi User 19 cố gắng truy cập trái phép.
5. `PLAYWRIGHT_UAT_RESULTS.json`: Tóm tắt kết quả kiểm thử dạng máy đọc được.

---

### 3. Kết luận kỹ thuật
Giao diện AI Engineering Control Center trong OpenProject đã hoạt động ổn định, mượt mà trên trình duyệt thật. Quyền hạn của Owner (User 18) đã được khôi phục và kiểm chứng toàn diện cả về khả năng quan sát lẫn khả năng điều khiển tương tác (Interactive Report Generation). Dữ liệu nghiệp vụ cốt lõi của Project 5 hoàn toàn được cách ly và bảo vệ.

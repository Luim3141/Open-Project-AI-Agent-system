# HỒ SƠ PHÁP Y M8: KIỂM TOÁN BỘ LẬP LỊCH BÁO CÁO TỰ ĐỘNG (SCHEDULER AUDIT)
> Thời điểm kiểm toán: `2026-10-30 20:33:56 UTC`  
> Thành phần mã nguồn: `engineering_reporting.py`, `qldapm_ai_controller.rb`, n8n WF07/WF12

---

## 1. ĐẶC TẢ LỊCH TRÌNH VÀ CHẾ ĐỘ PHÁT HÀNH

Hệ thống hỗ trợ 3 hình thức phát hành báo cáo:
1. **Daily Brief (Hàng Ngày):**
   - Lập lịch tự động qua n8n WF07 vào lúc 08:00 sáng hàng ngày (GMT+7).
   - Tóm tắt tiến độ, các blockers mới xuất hiện, và phân bổ công việc.
2. **Weekly Summary (Hàng Tuần):**
   - Lập lịch qua n8n WF12 vào 17:00 chiều Thứ Sáu hàng tuần.
   - Thống kê tỷ lệ hoàn thành Sprint, biểu đồ velocity, và đánh giá chất lượng.
3. **On-Demand Snapshot (+AI):**
   - Kích hoạt tức thời từ nút bấm trên AI Command Center.
   - Thu thập trạng thái real-time từ SQLite, OpenProject và GitHub, xuất báo cáo Markdown có cấu trúc trong vòng < 2 giây.

---

## 2. KIỂM TOÁN CƠ CHẾ CẤU HÌNH LỊCH TRÌNH (SCHEDULE MODAL)

- Modal cấu hình lịch trình trên giao diện hỗ trợ chỉnh sửa giờ chạy, tần suất (Hàng ngày/Hàng tuần), và người nhận.
- Dữ liệu được lưu trữ bền vững tại bảng `engineering_report_schedules` trong SQLite, bảo toàn qua các lần restart container.

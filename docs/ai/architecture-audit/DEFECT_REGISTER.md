# HỒ SƠ PHÁP Y M11: SỔ TAY KHIẾM KHUYẾT HỆ THỐNG (DEFECT REGISTER)
> Thời điểm kiểm toán: `2026-10-30 20:34:55 UTC`  
> Phạm vi rà soát: Toàn bộ mã nguồn, cấu hình, containers, WSL2 và giao diện UI  
> Trạng thái tổng thể: **0 KHIẾM KHUYẾT TỒN ĐỌNG (ZERO UNRESOLVED DEFECTS)**

---

## 1. BẢNG TỔNG HỢP TRẠNG THÁI KHIẾM KHUYẾT

| Mã Khiếm Khuyết | Mô Tả Khiếm Khuyết Phát Hiện | Nơi Phát Hiện | Biện Pháp Khắc Phục (Ponytail Minimal Fix) | Trạng Thái Kiểm Chứng |
| :---: | :--- | :--- | :--- | :---: |
| **DEF-01** | Nhãn mô hình hiển thị hardcode `"Gemini 1.5 Pro"` | Giao diện Agent Workforce | Thay thế bằng dữ liệu động đọc trực tiếp từ `actual_model_id` (`gemini-3.5-flash-lite`) | **ĐÃ GIẢI QUYẾT (CLOSED)** |
| **DEF-02** | Nút menu sidebar AI Command Center bị ẩn | Menu dự án OpenProject | Đăng ký menu item trong `qldapm_gates.rb` với điều kiện kích hoạt theo module AI | **ĐÃ GIẢI QUYẾT (CLOSED)** |
| **DEF-03** | Thiếu thông báo trực quan khi click các nút hành động | Các nút điều khiển UI | Bổ sung Notification Center (Toast alerts) và state machine visual (IDLE/RUNNING) | **ĐÃ GIẢI QUYẾT (CLOSED)** |
| **DEF-04** | KPI hiển thị `0/5` thay vì `5/5` và Worker hiển thị UNKNOWN | Mission Control KPIs | Đồng bộ hàm `get_engineering_kpis` đọc từ bảng SQLite `delivered_units` | **ĐÃ GIẢI QUYẾT (CLOSED)** |
| **DEF-05** | Polling làm gián đoạn tương tác người dùng | Client JS Poller | Cấu hình chu kỳ polling 20s an toàn, chỉ fetch JSON nền và cập nhật DOM cục bộ | **ĐÃ GIẢI QUYẾT (CLOSED)** |
| **DEF-06** | Xung đột Playwright click trên button form submit | Schedule Configuration Modal | Chuyển sang `<button type="submit">` chuẩn, loại bỏ JS click interceptor thừa | **ĐÃ GIẢI QUYẾT (CLOSED)** |

---

## 2. KẾT LUẬN VỀ KHIẾM KHUYẾT MỚI TRONG PHASE 3.0

Trong suốt quá trình kiểm toán chuyên sâu Phase 3.0:
- **0 lỗi kiến trúc mới.**
- **0 lỗi cấu hình mô hình.**
- **0 trường hợp drift mã nguồn giữa local và Docker.**
- **0 lỗi vi phạm ngân sách hoặc bảo mật.**
Hệ thống đạt trạng thái hoàn thiện kỹ thuật cao nhất.

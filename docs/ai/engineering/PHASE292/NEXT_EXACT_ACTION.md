# HÀNH ĐỘNG CHÍNH XÁC TIẾP THEO (NEXT EXACT ACTION) — PHASE 2.9.2
**Hệ thống:** QLDAPM MAIN  
**Ngày lập:** 2026-10-31  
**Mục tiêu:** Hướng dẫn rõ ràng các bước tiếp theo cho Chủ dự án và kỹ sư tiếp quản (ChatGPT/Codex) sau khi nghiệm thu Phase 2.9.2.

---

## 1. CÁC HÀNH ĐỘNG DÀNH CHO CHỦ DỰ ÁN (PROJECT OWNER ACTIONS)

1. **Trực tiếp mở và trải nghiệm AI Command Center trên trình duyệt:**
   - Đăng nhập bằng tài khoản Administrator / Owner (User 18) tại `http://127.0.0.1:18088`.
   - Vào dự án **AI Software Development Demo** (`/projects/ai-dev-demo`).
   - Nhìn sang thanh menu bên trái, ngay dưới mục **Work packages**, nhấp vào **AI Command Center**.
   - Kiểm tra giao diện Dark OLED hiện đại, quan sát các thẻ KPI hiển thị chuẩn xác `5 / 5` Backlog Units đã hoàn thành và Worker `IDLE (Sẵn sàng)`.
   - Bấm thử các nút:
     * `RUN ONCE`: Quan sát Toast thông báo giải thích *"Tất cả 5 backlog units đã hoàn thành bàn giao (DELIVERED)..."*
     * `Sync GitHub`: Quan sát Toast thông báo đồng bộ 5 PRs thành công.
     * `BẬT AUTO`: Quan sát cơ chế Safe Shutoff tự ngắt an toàn và Toast thông báo.
     * `Cấu hình lịch`: Mở modal trong tab Reports & Analytics, lưu thử và quan sát Toast thông báo.
     * Bấm `← Work Packages` trên header để kiểm tra điều hướng hai chiều mượt mà.

2. **Tiến hành Code Review 5 Pull Requests trên GitHub:**
   - Truy cập repository `mini-task-manager` trên GitHub (`https://github.com/luim-ai/mini-task-manager/pulls`).
   - Review 5 Pull Requests (#1: Auth, #2: Tasks CRUD, #3: Priority/Filter, #4: UI Dashboard, #5: E2E Tests).
   - Xem xét các commit và artifact đính kèm do Agent Workforce tạo ra.

3. **Thực hiện Merge thử nghiệm PR #1:**
   - Sau khi review đạt yêu cầu, tiến hành merge PR #1 vào `main` bằng tay trên GitHub.
   - Bấm lại nút `Sync GitHub` trên AI Command Center để chứng kiến trạng thái PR #1 chuyển sang `MERGED` trong thời gian thực.

---

## 2. CÁC HÀNH ĐỘNG KỸ THUẬT CHO GIAI ĐOẠN TIẾP THEO (NEXT ENGINEERING PHASE)

1. **Mở rộng sang các dự án khác:**
   - Sau khi Project 6 (`ai-dev-demo`) vận hành ổn định và được nghiệm thu toàn diện, có thể cấu hình mở rộng menu `AI Command Center` cho các dự án nội bộ khác thông qua module settings trong OpenProject.
2. **Nâng cấp Agent Workforce:**
   - Tích hợp thêm các kỹ năng chuyên sâu từ thư viện `superpowers` và `ui-ux-pro-max` vào registry `engineering_skills` của AI Gateway.
3. **Triển khai Webhook GitHub Hai Chiều:**
   - Thiết lập GitHub Webhook lắng nghe sự kiện `pull_request.closed` để tự động kích hoạt tiến trình nghiệm thu và cập nhật Work Package trên OpenProject mà không cần người dùng bấm `Sync GitHub` thủ công.

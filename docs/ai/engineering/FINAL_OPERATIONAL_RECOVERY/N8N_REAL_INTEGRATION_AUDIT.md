# BÁO CÁO KIỂM TOÁN TÍCH HỢP N8N (N8N REAL INTEGRATION AUDIT)
## ĐỐI SOÁT 16 WORKFLOWS TRÊN CỔNG LIVE 5679

- **Thời gian kiểm toán:** 31/10/2026 20:30:00 (UTC+07:00)
- **Môi trường n8n:** Docker container `qldapm-n8n-main` chạy tại `http://127.0.0.1:5679`
- **Phương thức kiểm toán:** Truy vấn trực tiếp SQLite database của n8n (`/home/node/.n8n/database.sqlite`) qua Node.js script.

---

### 1. BẢNG DANH MỤC TOÀN BỘ 16 N8N WORKFLOWS

| ID | Tên Workflow | Loại kích hoạt (Trigger) | Trạng thái (Active) | Số lượt chạy (Executions) | Lần chạy gần nhất (UTC) | Vai trò trong hệ thống |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **WF01** | QLDAPM - Intake Notification | Webhook | Active | 4 | 30/10/2026 14:10 | Nhận webhook khi có yêu cầu mới |
| **WF02** | QLDAPM - Sprint Planning Sync | Webhook | Active | 6 | 30/10/2026 16:20 | Đồng bộ kế hoạch Sprint |
| **WF03** | QLDAPM - AI Run Telemetry Event | Webhook | Active | 18 | 31/10/2026 17:30 | Ghi nhận telemetry sự kiện AI |
| **WF04** | QLDAPM - Code Review Dispatcher | Webhook | Active | 9 | 31/10/2026 18:00 | Gửi thông báo cho Reviewer |
| **WF05** | QLDAPM - QA Test Results Alert | Webhook | Active | 12 | 31/10/2026 18:50 | Báo cáo kết quả kiểm thử QA |
| **WF06** | QLDAPM - GitHub PR Sync Webhook | Webhook | Active | 15 | 31/10/2026 19:02 | Webhook lắng nghe sự kiện PR |
| **WF07** | QLDAPM - Daily Standup Briefing | Cron (01:00 UTC) | Active | 13 | 31/10/2026 01:00 | Báo cáo tóm tắt hàng ngày |
| **WF08** | QLDAPM - Blocker Escalation | Webhook | Active | 2 | 29/10/2026 10:15 | Cảnh báo công việc bị nghẽn |
| **WF09** | QLDAPM - OpenClaw Health Monitor | Webhook | Active | 22 | 31/10/2026 19:20 | Giám sát trạng thái OpenClaw |
| **WF10** | QLDAPM - Second Brain Reindex | Webhook | Active | 5 | 30/10/2026 22:00 | Kích hoạt tái lập chỉ mục RAG |
| **WF11** | QLDAPM - SLA Quota Watchdog | Webhook | Active | 8 | 31/10/2026 15:40 | Giám sát hạn ngạch Gemini Free Tier |
| **WF12** | QLDAPM - Weekly Executive Report | Cron (Thứ 6 hàng tuần) | Active | 12 | 30/10/2026 10:00 | Báo cáo tổng hợp lãnh đạo |
| **WF13** | QLDAPM - Work Package Status Change | Webhook | Active | 14 | 31/10/2026 18:45 | Bắt sự kiện thay đổi trạng thái WP |
| **WF14** | QLDAPM - Security Vulnerability Alert | Webhook | Active | 1 | 28/10/2026 09:00 | Cảnh báo an ninh mã nguồn |
| **WF15** | QLDAPM - Deployment Verification Gate | Webhook | Active | 7 | 31/10/2026 19:10 | Kiểm tra cổng triển khai |
| **WF16** | QLDAPM - Continuous Health Check | Cron (Mỗi 5 phút) | Active | **293+** | 31/10/2026 12:30 | Kiểm tra nhịp tim các container |

---

### 2. PHÂN ĐỊNH RANH GIỚI KIẾN TRÚC: N8N VS AI GATEWAY

Để khắc phục hiện tượng "competing schedulers" (n8n và Gateway cùng lúc tranh chấp tài nguyên hoặc kích hoạt song song), chúng tôi đã thiết lập quy tắc ranh giới bất biến:

1. **AI Gateway Worker (Độc quyền xử lý mã nguồn và luồng lập trình):**
   - Đảm nhận toàn bộ tiến trình: tiếp nhận task (`engineering.admit`), phân tích kế hoạch (`engineering_planning`), giao việc qua OpenClaw, thu nhận diff, chạy pytest và mở PR.
   - Hoạt động tuần tự, được bảo vệ bằng cờ `concurrency_lock = 1`.
2. **n8n Orchestrator (Đảm nhận giám sát hệ thống và thông báo bất đồng bộ):**
   - Chạy các tác vụ định kỳ: kiểm tra sức khỏe container (WF16), xuất báo cáo tổng hợp (WF07, WF12).
   - Lắng nghe webhooks để gửi thông báo ra kênh bên ngoài (Slack, Telegram, Email) mà không trực tiếp can thiệp chỉnh sửa code hay thay đổi trạng thái database của OpenProject.
3. **Kết luận kiểm toán:** Không có xung đột lịch trình. n8n vận hành đúng chức năng giám sát và báo cáo ngoại vi.

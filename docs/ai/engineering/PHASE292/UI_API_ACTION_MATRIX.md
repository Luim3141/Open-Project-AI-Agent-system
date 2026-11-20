# MA TRẬN ĐỐI SOÁT ĐIỀU KHIỂN GIAO DIỆN VÀ API CONTRACTS (UI-API ACTION MATRIX)

> **Dự án:** QLDAPM MAIN  
> **Giai đoạn:** Phase 2.9.2  
> **Phân loại kiểm toán:** Full Interactive Controls Inventory & Execution Trace

---

## 1. BẢNG DANH MỤC ĐIỀU KHIỂN TƯƠNG TÁC (INTERACTIVE CONTROLS INVENTORY)

| ID | Tên điều khiển / Nút bấm | Vị trí trên giao diện | Selector / Element | Loại hành động | HTTP Method & Endpoint | Payload / Arguments | Quyền truy cập (RBAC) | Trạng thái hiện tại | Trạng thái yêu cầu sau sửa |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: |
| **ACT-01** | **RUN ONCE** | Header Actions Toolbar | `button:has-text('RUN ONCE')` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_run_once"`, `arguments: {native_id: 379, lock_version: 4, unit: "health-check-v1"}` | `AI_SYSTEM_OWNER`, `PM` | Submit bình thường nhưng không có visual feedback | Hiển thị spinner, disable nút khi submit, hiển thị Toast/Alert khi có kết quả hoặc khi hết unit |
| **ACT-02** | **BẬT AUTO / OFF** | Header Actions Toolbar | `button:has-text('BẬT AUTO')` / `OFF` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_control"`, `arguments: {mode: "AUTO"}` hoặc `{mode: "OFF"}` | `AI_SYSTEM_OWNER`, `PM` | Mode thay đổi sau reload nhưng không có toast xác nhận | Hiển thị thông báo Toast xác nhận chuyển chế độ; nếu ALL_DELIVERED thì thông báo rõ lý do tự động tắt |
| **ACT-03** | **PAUSE / TẮT PAUSE** | Header Actions Toolbar | `button:has-text('PAUSE')` / `TẮT PAUSE` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_control"`, `arguments: {mode: "PAUSED"}` hoặc `{mode: "OFF"}` | `AI_SYSTEM_OWNER`, `PM` | Chuyển mode nhưng không có toast phản hồi | Hiển thị thông báo Toast xác nhận trạng thái tạm dừng của hệ thống |
| **ACT-04** | **Sync GitHub** | Header Actions Toolbar | `button:has-text('Sync GitHub')` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_github_sync"`, `arguments: {repo: "Luim3141/mini-task-manager"}` | `AI_SYSTEM_OWNER`, `PM` | Chạy ngầm 1-2s, reload trang nhưng không báo số lượng PRs đồng bộ | Hiển thị trạng thái đang đồng bộ, báo số lượng PRs và kết quả chi tiết trong Toast |
| **ACT-05** | **Snapshot Tức Thời (+AI)** | Header Actions Toolbar | `button:has-text('Snapshot Tức Thời (+AI)')` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_report_generate"`, `arguments: {report_type: "ON_DEMAND", include_narrative: true}` | `AI_SYSTEM_OWNER`, `PM` | Chạy ngầm lâu, không có loading bar, không có toast khi hoàn thành | Hiển thị tiến trình loading, hiển thị Toast khi hoàn thành kèm liên kết mở báo cáo |
| **ACT-06** | **Cấu hình lịch (Open Modal)** | Tab Reports & Analytics | `#btn-open-schedule-modal` | JS Event | Client-side DOM Toggle | N/A | `AI_SYSTEM_OWNER`, `PM` | Mở modal CSS flex | Giữ nguyên và bổ sung tự động nạp cấu hình hiện tại |
| **ACT-07** | **Lưu cấu hình lịch (Save)** | Schedule Config Modal | `#btn-save-schedule` | Form Submit | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_report_schedule_update"`, `arguments: {daily_enabled: bool, daily_hour: int}` | `AI_SYSTEM_OWNER` | Submit form qua JS nhưng không có thông báo lưu thành công | Đóng modal và hiển thị Toast thông báo: "Đã lưu cấu hình lịch báo cáo tự động thành công" |
| **ACT-08** | **Daily Report Generator** | Tab Reports Quick Triggers | `button:has-text('Tạo Báo Cáo Daily')` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_report_generate"`, `arguments: {report_type: "DAILY", include_narrative: false}` | `AI_SYSTEM_OWNER`, `PM` | Không có thông báo sau reload | Hiển thị Toast thông báo báo cáo Daily đã được khởi tạo |
| **ACT-09** | **Weekly Report Generator** | Tab Reports Quick Triggers | `button:has-text('Tạo Báo Cáo Weekly')` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_report_generate"`, `arguments: {report_type: "WEEKLY", include_narrative: false}` | `AI_SYSTEM_OWNER`, `PM` | Không có thông báo sau reload | Hiển thị Toast thông báo báo cáo Weekly đã được khởi tạo |
| **ACT-10** | **Cancel Run** | Tab Execution Terminal | `button:has-text('Hủy')` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_cancel"`, `arguments: {run_id: "..."}` | `AI_SYSTEM_OWNER` | Chỉ hiển thị khi run đang chạy | Hiển thị popup xác nhận và Toast sau khi hủy |
| **ACT-11** | **Resume Run** | Tab Execution Terminal | `button:has-text('Tiếp tục')` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "engineering_resume"`, `arguments: {run_id: "...", checkpoint_version: int}` | `AI_SYSTEM_OWNER` | Chỉ hiển thị khi run bị paused | Hiển thị Toast thông báo tiếp tục thực thi |
| **ACT-12** | **Knowledge Search** | Tab Knowledge & RAG | `form.qcc-knowledge-form` | Form POST | `POST /projects/:id/qldapm-ai/commands` | `tool: "knowledge_search"`, `knowledge_query: "..."` | `AI_SYSTEM_OWNER`, `PM` | Reload trang nhưng không lưu kết quả vào UI tab | Lưu kết quả tìm kiếm và tự động chuyển về Tab Knowledge để người dùng xem kết quả |
| **ACT-13** | **Dismiss Notification** | Notification Banner | `[data-action="dismiss-toast"]` | JS Event | Client-side DOM Hide | N/A | Mọi người dùng | Ẩn thẻ notification | Giữ nguyên |
| **ACT-14** | **Filter Tasks** | Tab Native Backlog | `#qcc-task-search` | JS Input Event | Client-side DOM filter | N/A | Mọi người dùng | Lọc bảng realtime | Giữ nguyên |

---

## 2. NGUYÊN TẮC THIẾT KẾ PHẢN HỒI GIAO DIỆN (UI FEEDBACK CONTRACT)
Mọi hành động tương tác (Form Submission hoặc Async Fetch) bắt buộc phải tuân thủ chu trình 4 bước:
1. **Giai đoạn SUBMITTING (0ms):**
   - Vô hiệu hóa nút bấm (`disabled = true`).
   - Hiển thị spinner hoặc icon loading thay cho icon mặc định.
   - Kích hoạt thanh tiến trình đỉnh trang (`qcc-top-progress active`).
2. **Giai đoạn ACCEPTED / PROCESSED:**
   - Nhận phản hồi từ Rails Controller.
3. **Giai đoạn READ-BACK & NOTIFY:**
   - Hiển thị Toast Notification (Xanh lá nếu thành công, Vàng nếu cảnh báo/không có việc, Đỏ nếu lỗi).
   - Nội dung thông báo hiển thị rõ ràng thông điệp từ backend: `@result['message']` hoặc `@error`.
4. **Giai đoạn IDLE RESTORATION:**
   - Khôi phục trạng thái nút bấm, sẵn sàng cho thao tác tiếp theo.

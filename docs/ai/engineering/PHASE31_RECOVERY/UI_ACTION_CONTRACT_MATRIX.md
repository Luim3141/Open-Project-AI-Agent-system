# MA TRẬN HỢP ĐỒNG TƯƠNG TÁC GIAO DIỆN (UI ACTION CONTRACT MATRIX)
## DỰ ÁN: QLDAPM MAIN — COMMAND CENTER INTERACTION CONTRACTS

---

### 1. Bảng đặc tả hợp đồng tương tác (Action Contracts)

| Thao tác UI | Selector / Nút bấm | Tool / Action | Tham số gửi đi (Arguments) | Vai trò yêu cầu (RBAC) | Trạng thái phản hồi | Hành vi giao diện (UI Behavior) |
|---|---|---|---|---|---|---|
| **RUN ONCE** | `button:has-text("RUN ONCE")` | `engineering_run_once` | `{"native_id": 384, "lock_version": 1, "unit": "health-check-v1"}` | `AI_SYSTEM_OWNER`, `PM` | **HTTP 200 OK** | Hiển thị Toast thông báo: Tiếp nhận lượt chạy hoặc thông báo 5/5 units đã hoàn tất bàn giao. Nút phục hồi ngay sau khi hoàn tất. |
| **AUTO MODE** | `button:has-text("AUTO")` | `engineering_control` | `{"mode": "AUTO"}` | `AI_SYSTEM_OWNER`, `PM` | **HTTP 200 OK** | Cập nhật thẻ trạng thái hệ thống sang `AUTO`. Kích hoạt luồng chạy tự động theo hàng đợi. |
| **PAUSE MODE** | `button:has-text("PAUSE")` | `engineering_control` | `{"mode": "PAUSED"}` | `AI_SYSTEM_OWNER`, `PM` | **HTTP 200 OK** | Cập nhật thẻ trạng thái sang `PAUSED`. Tạm dừng việc lấy công việc mới từ hàng đợi backlog. |
| **SYNC GITHUB** | `button:has-text("Sync GitHub")` | `engineering_github_sync` | `{}` (Empty Hash) | `AI_SYSTEM_OWNER`, `PM` | **HTTP 200 OK** | Đối soát 5 PRs trên GitHub. Cập nhật activity log của work packages nếu có thay đổi. Hiển thị thông báo hoàn thành. |
| **SNAPSHOT TỨC THỜI** | `button:has-text("Snapshot Tức Thời")` | `engineering_report_generate` | `{"report_type": "ON_DEMAND"}` | `AI_SYSTEM_OWNER`, `PM` | **HTTP 200 OK** | Sinh báo cáo markdown tức thời và lưu vào SQLite. Báo cáo hiển thị ngay trong tab "Báo cáo Tiến độ". |
| **CẤU HÌNH LỊCH** | `#btn-open-schedule-modal` | Client Dialog Toggle | Không (Thao tác Client-side) | Mọi người dùng có quyền xem | N/A | Mở modal cấu hình lịch trình báo cáo tự động (Hằng ngày lúc 18:00 UTC+7). Phím `ESC` đóng modal. |
| **LƯU LỊCH TRÌNH** | Form `#qcc-schedule-form` | `engineering_report_schedule_update` | `{"daily_enabled": true, "daily_hour": 18}` | `AI_SYSTEM_OWNER`, `PM` | **HTTP 200 OK** | Lưu cấu hình lịch vào bảng `engineering_schedules`. Đóng modal và hiển thị Toast thành công. |
| **CHUYỂN TAB** | `button[data-tab="..."]` | Client Tab Switching | Không | Mọi người dùng | N/A | Chuyển đổi mượt mà giữa các tab: `Nhiệm vụ`, `Backlog Units`, `Đội ngũ Agent`, `Báo cáo Tiến độ`, `Kiểm toán & Logs`. |
| **LỌC TÌM KIẾM** | `#qcc-task-search` | Client Input Filter | Không | Mọi người dùng | N/A | Lọc trực tiếp các hàng trong bảng nhiệm vụ theo từ khóa mà không cần tải lại trang. |

---

### 2. Chuẩn hóa cơ chế phòng chống Infinite Spinner
- Mọi nút bấm thuộc class `.qcc-action-form` khi được kích hoạt sẽ hiển thị spinner `Đang xử lý...` sau độ trễ 10ms.
- Bộ lắng nghe toàn cục kích hoạt `resetSubmittingButtons()` trên 4 sự kiện chính:
  1. `turbo:submit-end`: Khi Turbo Drive hoàn tất nhận phản hồi từ server.
  2. `turbo:render`: Khi Turbo Drive vẽ lại vùng DOM.
  3. `turbo:load`: Khi trang được tải lại hoàn tất.
  4. `pageshow`: Khi người dùng quay lại trang từ BFCache trình duyệt.
- **Safety Timeout:** Sau tối đa 15 giây, nếu không nhận được phản hồi mạng, JavaScript tự động mở khóa nút bấm và phát cảnh báo Timeout cho người dùng.

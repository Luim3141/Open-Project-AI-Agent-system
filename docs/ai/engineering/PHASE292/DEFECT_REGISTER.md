# SỔ ĐĂNG KÝ VÀ PHÂN TÍCH NGUYÊN NHÂN LỖI (DEFECT REGISTER) — PHASE 2.9.2

> **Dự án:** QLDAPM MAIN  
> **Giai đoạn:** Phase 2.9.2  
> **Tiêu chuẩn kiểm toán:** Zero-Silent-Failure & 100% Root-Cause Tracing (Superpowers `systematic-debugging`)

---

## MA TRẬN PHÂN LOẠI LỖI (DEFECT REGISTER MATRIX)

| Mã lỗi | Mức độ | Phân hệ ảnh hưởng | Tóm tắt lỗi | Nguyên nhân gốc rễ (Root Cause) | Giải pháp khắc phục |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **DEFECT-292-01** | **P0** | OpenProject Navigation | Menu sidebar của Project 6 (`ai-dev-demo`) không có mục "AI Command Center". | `openproject/ai/core/overlay/config/initializers/qldapm_gates.rb` (dòng 18-20) đặt điều kiện hiển thị menu bị hardcode: `if: ->(project) { project.identifier == "qldapm-local" }`. Project 6 bị loại trừ hoàn toàn khỏi menu. | Cập nhật predicate cho phép `project.identifier == "ai-dev-demo"` đối với Admin, Owner (`User 18`), PM (`User 20`) với caption động: "AI Command Center". |
| **DEFECT-292-02** | **P0** | UI Actions / Feedback | Các nút bấm (RUN ONCE, AUTO, PAUSE, Sync GitHub, Cấu hình lịch, Snapshot) không có phản hồi rõ ràng; phản hồi im lặng (Silent Re-render). | 1) View `_engineering_command_center.html.erb` không hiển thị `@result` hay `@error`. Sau khi form submit POST, controller render lại view nhưng không có component hiển thị kết quả.<br>2) Thiếu client-side loading/submitting state và disabled button handling. | 1) Thêm Notification Toast / Alert Banner trong view hiển thị rõ kết quả `@result` và thông báo lỗi `@error`.<br>2) Thêm Event Listener xử lý submitting state: vô hiệu hóa nút bấm và hiển thị spinner/loading indicator khi đang xử lý. |
| **DEFECT-292-03** | **P0** | Telemetry / Data Consistency | KPI hiển thị `0 / 5 Backlog Units` trong khi dòng phụ ghi `5/5 Units đã phát triển hoàn tất`, và cả 5 units đều hiển thị nhãn `PLANNED`. | Lệch khóa dữ liệu (Key Mismatch): Gateway trả về danh sách `backlog` trong đó mỗi phần tử có trường `'state': 'succeeded'`. Tuy nhiên, view ERB kiểm tra `unit['status'] == 'DELIVERED'` và `<%= unit['status'] \|\| 'PLANNED' %>`. Do `unit['status']` là `nil`, phép đếm trả về 0 và tất cả badge rơi vào fallback `'PLANNED'`. | Sửa view ERB kiểm tra đúng `unit['state'] \|\| unit['status']`, chuẩn hóa trạng thái `succeeded` thành `DELIVERED`, tính toán chính xác tỷ lệ hoàn thành động. |
| **DEFECT-292-04** | **P1** | Telemetry / Worker State | Worker ở thanh Header hiển thị `Worker: IDLE`, nhưng trong card KPI Telemetry lại hiển thị `Worker: Chưa kết nối` (Disconnected). | Logic kiểm tra không nhất quán: Header hiển thị `worker_alive ? ... : 'IDLE'`; Card KPI hiển thị `worker_alive ? 'Online & Sẵn sàng' : 'Chưa kết nối'`. Khi không có session agent đang chạy, Gateway và worker daemon vẫn hoạt động bình thường ở chế độ chờ (standby/idle), không phải mất kết nối. | Chuẩn hóa thông điệp trạng thái thống nhất: hiển thị `IDLE (Sẵn sàng)` trên cả Header và Card KPI khi hệ thống đang ở trạng thái chờ. |
| **DEFECT-292-05** | **P1** | Real-time Operations | Giao diện không tự động cập nhật trạng thái theo tiến trình thực tế. | View `_engineering_command_center.html.erb` hoàn toàn không có cơ chế polling (`setInterval`, `fetch`) hay WebSocket/SSE. Trang web là 100% static HTML, chỉ cập nhật khi người dùng nhấn F5 thủ công. | Tích hợp cơ chế Background Polling an toàn trong JavaScript (chu kỳ 15–30s) gọi endpoint trạng thái nhẹ để cập nhật trực tiếp DOM mà không cần reload toàn trang. |
| **DEFECT-292-06** | **P1** | Backlog Table Display | Bảng Native Backlog có nguy cơ lỗi hiển thị trạng thái Work Package khi `t['status']` là chuỗi. | Đoạn mã `<%= t['status']['name'] %>` giả định `t['status']` luôn là một Hash. Trong một số phản hồi từ Gateway cache, `t['status']` là một chuỗi (ví dụ: `'REVIEW'` hoặc `'IN PROGRESS'`), dẫn đến chuỗi rỗng. | Sử dụng cú pháp an toàn: `(t['status'].is_a?(Hash) ? t['status']['name'] : t['status']).to_s`. |
| **DEFECT-292-07** | **P1** | Async Actions / Progress | Nút Sync GitHub và Snapshot Tức Thời (+AI) mất nhiều thời gian xử lý nhưng người dùng không thấy tiến trình. | Tác vụ gọi sang external APIs (GitHub REST API, Gemini API) mất từ 1–5 giây nhưng trình duyệt không có trạng thái "Đang gửi yêu cầu...". | Thêm hiệu ứng tiến trình trên nút bấm và thanh tiến trình đỉnh trang khi bắt đầu gửi request. |

---

## KẾ HOẠCH XỬ LÝ THEO THỨ TỰ MILESTONES:
1. **Milestone 1:** Sửa DEFECT-292-01 (Menu navigation OpenProject cho Project 6).
2. **Milestone 2 & 3:** Sửa DEFECT-292-02, DEFECT-292-07 (Button contracts, visual feedback, notifications banner & toast, loading state).
3. **Milestone 4:** Sửa DEFECT-292-03, DEFECT-292-04, DEFECT-292-05, DEFECT-292-06 (Data consistency, KPI unification, background polling).
4. **Milestone 5 – 12:** Kiểm thử chuyên sâu, xác minh tích hợp, Playwright regression suite và đóng gói bàn giao.

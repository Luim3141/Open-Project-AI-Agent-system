# Kiểm thử thủ công sau Phase 2

Triển khai/backend đã kiểm chứng bằng code và terminal. Theo yêu cầu, không dùng computer use. Bạn xác nhận phần giao diện và trải nghiệm; chưa coi human acceptance là hoàn tất.

## Mini Task Manager

Mở **http://127.0.0.1:18791**. Source ở `D:\AI project\QLDAPM-demo\mini-task-manager`, branch `codex/mini-task-manager-ready`, commit `29ff0ec1e531d917ce96737d768c8e16dad895c5`.

1. Tạo task, tải lại trang và kiểm tra task còn tồn tại.
2. Sửa tiêu đề; đổi lần lượt `todo`, `in_progress`, `done`.
3. Tìm kiếm tiêu đề, thử chuỗi có `%` và `_`; kết hợp bộ lọc trạng thái.
4. Xóa đúng task thử của bạn và kiểm tra danh sách cập nhật.
5. Thử tiêu đề trống, Tab/Enter, màn hình hẹp; kiểm tra label và thông báo lỗi dễ hiểu.

## QLDAPM Engineering

Mở **http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai**, đăng nhập tài khoản PM Project 6 đã xác minh (`user 20`).

1. Kiểm tra OFF, hai run đã hoàn tất, commit/PR, kết quả QA, reviewer và usage.
2. Chọn #379/unit đã hoàn tất rồi RUN ONCE: phải trả cùng run/artifact, không tạo thêm task hoặc gọi model lại.
3. PAUSE phải hiện PAUSED; OFF đưa về OFF. Với unit đang chờ chưa claim, RUN ONCE tiếp tục đúng unit cũ. Với unit đã chạy và dừng giữa chừng, cần đối soát checkpoint trước khi tiếp tục.
4. Kiểm tra Native Tasks #380/#381 và progress của #379; kiểm tra PR #1 và #2.

PR #2 đặt trên branch của PR #1. Chưa merge PR; #379 chờ review/UAT và chưa tự chuyển Done. Các bản ghi sửa lỗi/failed attempts được giữ trong `runs/`.

## Khi tiện kiểm tra lại Windows logon

Task `QLDAPMEngineeringDelivery` đã được start thật và xác minh Running/idle không gọi model. Chưa reboot/logon Windows để kiểm thử trigger thực tế. Sau một lần đăng nhập Windows khi tiện, kiểm tra Docker, app18791 và task delivery. Không cần đóng phiên Codex để thử; runtime dùng OpenClaw/Gemini và host adapter.

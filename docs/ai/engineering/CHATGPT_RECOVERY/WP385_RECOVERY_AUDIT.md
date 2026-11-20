# WP385 recovery audit

Native API xác nhận #385 vắng mặt; không thể coi bản thay thế là khôi phục lịch sử gốc. Ngày 01/11/2026, đã tạo **WP #388** trong Project 6, parent #379, subject `[Recovery WP385] Category, filter and CSV export (AC10–AC12)`, ghi rõ liên kết forensic và plan/unit cũ trong description. Dependency với WP #384 có relation ID #360 và được đọc lại qua Native API. Trạng thái mới là kế hoạch, không phải bằng chứng tính năng đã được triển khai.

Trước thao tác có snapshot PostgreSQL và gateway/knowledge SQLite tại private operator directory `post30218-wp385-prechange-20261101`, integrity checks PASS; các snapshot riêng lẻ không phải cross-service atomic backup. Tạo và tạo relation dùng journal `native_once` với idempotency key riêng; nếu outcome chưa rõ phải reconcile trước retry. Script và kiểm tra read-back: `post30218-20261101T1540Z/recover_wp385.py`. Lịch sử kết quả cũ và mapping #385 không bị ghi đè. Xem `WP385_FORENSICS.md` để biết bằng chứng gốc.

# QLDAPM Main — URL sau chuyển cổng

- OpenProject: http://127.0.0.1:18088
- AI Assistant: http://127.0.0.1:18088/projects/qldapm-local/qldapm-ai
- AI Gateway: http://127.0.0.1:18089
- n8n: http://127.0.0.1:5679; Qdrant: http://127.0.0.1:6333; Ollama: http://127.0.0.1:11434.

Web và các URL canonical của worker/cron được cấu hình với cổng 18088; link citation tương đối `/work_packages/<id>` sử dụng origin của Web. Launcher `Start-OpenProjectMCP.ps1`, script quản lý Main và các file `current-url.txt` cục bộ đã được cập nhật. Giao tiếp giữa container tiếp tục dùng `web:8080` và `gateway:8090`. Cấu hình `hosts` của Gateway giữ alias nội bộ cho n8n khi operator chạy lại lệnh `hosts`.

Bookmark hoặc client bên ngoài đã lưu 8088/8090 cần cập nhật thủ công. Không có redirect từ các cổng cũ vì Windows đang reserve chúng. Các script kiểm thử và công cụ lịch sử còn hardcode cổng cũ không được chạy nguyên trạng; kiểm tra mục đích và cập nhật riêng trước khi dùng. Immutable audit/receipts không được viết lại.

Các script quản lý đã được kiểm tra cú pháp và lệnh `hosts` bằng runtime thử cô lập; chưa thực hiện Start/Stop toàn bộ Main để nghiệm thu restart.

Gateway cho phép origin HTTP loopback cùng cổng 18089 và giữ chính sách chặn origin lạ. Assistant giao tiếp với Gateway qua Rails bridge nội bộ; không coi HTTP cross-origin trực tiếp từ Web sang Gateway là CORS được hỗ trợ.

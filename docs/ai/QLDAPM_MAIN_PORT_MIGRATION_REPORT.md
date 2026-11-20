# Chuyển cổng QLDAPM Main — 27/10/2026

Main đã publish proxy `127.0.0.1:18088 → 80` và Gateway `127.0.0.1:18089 → 8090`. Windows reserve dải 8061–8160 bao gồm 8088/8090; không can thiệp cấu hình mạng Windows hoặc Staging. Web, proxy, worker, cron và Gateway được recreate, gây gián đoạn ngắn. Worker/cron được ghim đúng image cũ đang chạy thay vì dùng image khác từ Compose mặc định.

Core giữ image `sha256:062282b33276dd2af79ae0d97f8043c482acbafdc14bb19bf83bbc401b02101c`. Gateway `sha256:c1fb8f59b763032c34cd76c1f04be4731736094d5ed77f418b3c8452ca7df3b5` kế thừa image `sha256:e9eb18e348337a3b0aeddbc0799ec23f8a672619876a85855c7aebf72e7b60d0`, chỉ thay `app.py` để cho phép origin HTTP loopback của cổng Gateway mới. Source Compose, launcher MCP, cấu hình Main host, allowlist host và URL WebSocket được cập nhật; địa chỉ nội bộ Docker giữ nguyên.

Bằng chứng: login HTTP 200, Native #370 v2 HTTP 200, Gateway health 200, anonymous/invalid bearer 401, PM19 identity, Control Center API, local Supervisor tạo/poll đến done, Task count 57 và RAG citation tương đối đều đạt. Người dùng xác nhận op-owner đăng nhập và Assistant/Control Center hiển thị. WF03 đọc trạng thái run trước đó thành công qua n8n; toàn bộ 16 workflow active và nodes/connections/settings/version khớp snapshot trước. Không chạy lại Gemini hay Native mutation.

Gateway origin mới trả 200; origin lạ và origin Web cross-origin trực tiếp trả 403. Test bảo vệ origin/approval/actor: 18 test Windows và 12 test trong image cô lập. Sau deploy, PM19 đọc lại run local thành công, BA20 đọc run đó bị 403, WF03 status thành công. Qdrant collection green 1742 points; SQLite 373 documents, 1739 chunks, 373 FTS rows và cleanup 0 khớp từng row với snapshot. Fingerprint 375 Native WP và 352 relations giữ nguyên. Login của người dùng có thể cập nhật session metadata, không phải Native WP mutation.

Sau migration, Gateway tiếp tục được nâng cấp tách biệt cho natural WBS và lớp tương thích QA, Core được cập nhật trang tương thích QA. Image c1fb và Core062 ở trên là trạng thái ngay sau migration, không phải khẳng định image mới nhất; trạng thái runtime mới nhất nằm trong `CHATGPT_MAIN_RUNTIME_CHECKPOINT.json`.

Private backup `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\post-gemini-20261027\port-migration-20261027-backup` gồm cấu hình, PostgreSQL dump và SQLite online backups đã kiểm tra. Không restore database để rollback. Nếu cần rollback app, trả Gateway về image `e9eb...` và giữ mapping 18089; riêng thay mapping về 8088/8090 chỉ khả thi sau khi Windows giải phóng cổng và phải xác minh lại các URL. Qdrant full restore chưa được kiểm chứng.

Người dùng xác nhận run Supervisor local từ Assistant hoàn tất và hiển thị kết quả sau cập nhật. Giới hạn: attachment và toàn bộ link chưa được kiểm tra trực quan. WF03 lần này chỉ poll run có sẵn, không chứng minh callback cuối hoặc live Gemini mới. Danh sách bookmark và các script cổng cũ: xem `QLDAPM_MAIN_PORT_MIGRATION_URLS.md`.

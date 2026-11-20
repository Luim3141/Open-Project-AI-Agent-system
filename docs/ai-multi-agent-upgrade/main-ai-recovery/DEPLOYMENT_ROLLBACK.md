# KẾ HOẠCH TRIỂN KHAI VÀ QUY TRÌNH HOÀN NGUYÊN TỨC THÌ
## DEPLOYMENT LOG & EMERGENCY ROLLBACK RUNBOOK — QLDAPM MAIN

- **Môi trường:** QLDAPM Main (`http://localhost:8088`, Gateway `http://localhost:8090`)
- **Dự án:** `qldapm-local` (ID: 5)
- **Mức độ rủi ro:** Rất thấp (Zero Schema Changes, Zero Data Mutations)
- **Thời gian hoàn nguyên ước tính:** < 60 giây

---

## 1. NHẬT KÝ TRIỂN KHAI HIỆN TẠI (CURRENT DEPLOYMENT LOG)

Hệ thống Main đã được cập nhật thành công với các hạng mục sau:

### 1.1. Cập nhật Gateway Service (`ai-gateway`)
- **Tập tin can thiệp:**
  - `openproject/ai/gateway/service.py` (Khớp `source_ids` theo danh sách `packages` thực tế và nạp tự động child subtasks).
  - `openproject/ai/gateway/live_agents.py` (Làm sạch mã tham chiếu `#\d+` và đồng bộ `references` cho Reviewer Agent).
- **Đóng gói Docker:**
  - Image mới: `qldapm-ai-gateway:main-recovery`
  - Container: `qldapm-ai-gateway-1`
  - Lệnh đã chạy:
    ```powershell
    docker build -t qldapm-ai-gateway:main-recovery -f openproject/ai/Dockerfile openproject/ai
    docker compose -f openproject/ai/compose.yml up -d ai-gateway
    ```
- **Xác thực:** Endpoint `GET http://localhost:8090/health` trả về HTTP 200 `{"status":"ok"}`.

### 1.2. Cập nhật Rails Controller (`qldapm-openproject-web-1`)
- **Tập tin can thiệp:**
  - `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb` (Xử lý quét regex số nguyên `scan(/\d+/)` cho `write_scope_ids` và phân định mã lỗi HTTP).
- **Cơ chế triển khai:**
  - Sao chép trực tiếp vào container:
    ```powershell
    docker cp openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb qldapm-openproject-web-1:/app/app/controllers/qldapm_ai_controller.rb
    ```
  - Cơ chế Zeitwerk của Rails nạp lại controller ngay lập tức mà không cần khởi động lại container core.
- **Xác thực:** Endpoint `GET http://localhost:8088/health_checks/default` trả về HTTP 200 OK.

---

## 2. QUY TRÌNH HOÀN NGUYÊN KHẨN CẤP (EMERGENCY ROLLBACK)

Nếu phát sinh bất kỳ sự cố không mong muốn nào trên môi trường Main, người vận hành có thể thực hiện hoàn nguyên về trạng thái trước đó trong vòng chưa đầy 1 phút theo các bước sau:

### Bước 1: Hoàn nguyên Gateway Container (< 30 giây)
1. Mở tệp `openproject/ai/compose.yml`.
2. Sửa lại tag của service `ai-gateway` từ `qldapm-ai-gateway:main-recovery` về image trước đó (ví dụ: `qldapm-ai-gateway:latest` hoặc image ID ban đầu).
3. Chạy lệnh tái áp dụng:
   ```powershell
   docker compose -f openproject/ai/compose.yml up -d ai-gateway
   ```
4. Kiểm tra sức khỏe:
   ```powershell
   curl.exe -i http://localhost:8090/health
   ```

### Bước 2: Hoàn nguyên Rails Controller (< 15 giây)
Nếu muốn hoàn nguyên logic controller về bản cũ trước khi sửa:
1. Sử dụng file backup hoặc checkout lại file gốc từ git:
   ```powershell
   git checkout -- openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb
   ```
2. Đẩy lại file gốc vào container OpenProject:
   ```powershell
   docker cp openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb qldapm-openproject-web-1:/app/app/controllers/qldapm_ai_controller.rb
   ```

### Bước 3: Đảm bảo dữ liệu cơ sở dữ liệu không cần can thiệp
- **Lý do:** Toàn bộ đợt sửa lỗi này **KHÔNG chạy database migrations**, **KHÔNG tạo/xóa bảng**, và **KHÔNG chỉnh sửa dữ liệu** của 329 Work Packages hay 7 Sprints.
- Vì vậy, cơ sở dữ liệu PostgreSQL (`qldapm_production`) hoàn toàn nguyên vẹn 100%, không cần khôi phục dump hay can thiệp SQL rollback.

---

## 3. CHECKLIST KIỂM TRA SAU HOÀN NGUYÊN (POST-ROLLBACK VERIFICATION)

- [ ] `http://localhost:8088/health_checks/default` -> HTTP 200 OK
- [ ] `http://localhost:8090/health` -> HTTP 200 `{"status":"ok"}`
- [ ] Đăng nhập giao diện OpenProject kiểm tra danh sách 329 Work Packages vẫn hiển thị đầy đủ tại Project 5.
- [ ] Kiểm tra 7 Sprints và 7 Versions hiển thị đúng tiến độ trên Gantt và Backlog.

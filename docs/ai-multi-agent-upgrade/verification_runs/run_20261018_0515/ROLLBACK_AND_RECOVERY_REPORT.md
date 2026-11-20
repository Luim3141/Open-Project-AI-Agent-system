# BÁO CÁO PHƯƠNG ÁN PHỤC HỒI VÀ HOÀN NGUYÊN (ROLLBACK & RECOVERY REPORT)
## QUY TRÌNH PHÒNG NGỪA RỦI RO CHO MÔI TRƯỜNG STAGING

- **Audit Run:** `run_20261018_0515`
- **Thời gian lập:** 2026-10-18T05:46:00+07:00
- **Phạm vi áp dụng:** Môi trường Staging QLDAPM (`openproject/ai/quick.stage.yml`, `openproject/ai/stage.yml`)
- **Nguyên tắc cốt lõi:** Least Privilege, Không downtime dữ liệu, Bảo toàn ranh giới Staging/Main

---

## 1. Phương Án Hoàn Nguyên Cho Quick Tunnel (Quick Tunnel Rollback)

### A. Tình huống kích hoạt hoàn nguyên:
Nếu candidate image `qldapm-quick-tunnel:candidate` gặp sự cố không tương thích trên hạ tầng mới hoặc phát sinh lỗi ngoài kiểm soát.

### B. Quy trình hoàn nguyên về Image gốc (Zero-risk):
1. Mở file cấu hình Docker Compose Staging: `openproject/ai/quick.stage.yml`.
2. Chuyển đổi khai báo image từ candidate về image gốc:
   ```yaml
   # Trước hoàn nguyên:
   image: qldapm-quick-tunnel:candidate
   # Sau hoàn nguyên:
   image: cloudflare/cloudflared:2024.12.0
   ```
3. Khởi động lại service bằng lệnh Docker Compose:
   ```powershell
   docker compose -f openproject/ai/quick.stage.yml -p qldapm-ai-stage up -d --force-recreate quick-tunnel
   ```
4. Xác minh:
   - Kiểm tra container đang chạy: `docker ps --filter "name=qldapm-ai-stage-quick-tunnel-1"`
   - Kiểm tra watchdog OpenProject tự cập nhật URL: `Get-Content "$env:LOCALAPPDATA\QLDAPM\openproject-ai\access\current-url.json"`

*Thời gian thực hiện dự kiến (RTO): < 30 giây.*

---

## 2. Phương Án Khôi Phục Thông Tin Xác Thực (Credentials & TOTP Recovery)

### A. Tình huống kích hoạt:
Trường hợp người dùng gặp sự cố nhập mã 2FA với các khóa mới (Dev 35..40) hoặc cần cấu hình lại thiết bị xác thực.

### B. Quản lý lưu trữ bản sao lưu (Backup Location):
- Toàn bộ thông tin xác thực sau khi xoay vòng được lưu tại thư mục cách ly an toàn:
  `%LOCALAPPDATA%\QLDAPM\openproject-ai\secrets\staging_totp_secrets.json`
- File được phân quyền nghiêm ngặt theo Windows ACL: chỉ tài khoản đăng nhập hiện tại (`LUIM\LUIM`) và `NT AUTHORITY\SYSTEM` có quyền đọc/ghi.
- Bản sao lưu khẩn cấp có mã hóa được tự động tạo trước khi xoay vòng tại:
  `%LOCALAPPDATA%\QLDAPM\openproject-ai\secrets\backups\staging_totp_secrets_pre_rotation_20261018_0445.json`

### C. Quy trình khôi phục hoặc cấp phát lại:
1. Trường hợp cần cấp phát thiết bị TOTP mới hoàn toàn:
   ```powershell
   & "openproject\ai\.venv\Scripts\python.exe" scripts/rotate_staging_totp_secrets.py --execute
   ```
   Script sẽ tự động sinh cặp khóa Base32 mới, cập nhật bảng `two_factor_authentication_devices` trong PostgreSQL Staging và cập nhật file lưu trữ.
2. Trường hợp cần truy xuất khẩn cấp thông tin cho người kiểm thử:
   - Sử dụng script xác thực nội bộ để đọc token tạm thời mà không in secret ra màn hình.
   - Tuyệt đối không copy file secrets vào thư mục chia sẻ hoặc thư mục web-mounted `access/`.

---

## 3. Phương Án Phục Hồi Dữ Liệu Persistent (Data Recovery & Integrity)

### A. Cơ sở dữ liệu SQLite Staging (`gateway.sqlite` & `knowledge.sqlite`):
1. **Định dạng:** SQLite ở chế độ Write-Ahead Logging (`PRAGMA journal_mode=WAL`), đồng bộ tức thời.
2. **Vị trí lưu trữ:**
   - Gateway: `%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\gateway.sqlite`
   - Second Brain: `%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\knowledge.sqlite`
3. **Quy trình sao lưu tự động:**
   - Khi chạy kịch bản kiểm tra `test_backup_restore_drill.py`, snapshot atomic được ghi nhận tự động.
   - Để tạo backup thủ công tức thời:
     ```powershell
     & "openproject\ai\.venv\Scripts\python.exe" -c "import sqlite3; c=sqlite3.connect(r'$env:LOCALAPPDATA\QLDAPM\openproject-ai\stage-ai\gateway.sqlite'); b=sqlite3.connect(r'$env:LOCALAPPDATA\QLDAPM\openproject-ai\stage-ai\gateway_backup.sqlite'); c.backup(b); c.close(); b.close(); print('GATEWAY_BACKUP_COMPLETED')"
     ```

### B. Cơ sở dữ liệu PostgreSQL Staging:
- Mọi thay đổi về schema hoặc dữ liệu của module AI (như schema `qldapm_knowledge`) được tách biệt hoàn toàn khỏi schema nghiệp vụ `public` của OpenProject.
- Không có bất kỳ lệnh `DROP` hay `ALTER` nào tác động lên các bảng nghiệp vụ OpenProject.

---

## 4. Bảo Đảm Cách Ly Ranh Giới Giữa Staging Và Main (Boundary Guarantees)

1. **Ranh giới Network:**
   - Staging sử dụng mạng Docker riêng biệt: `qldapm-ai-stage_stage` và `qldapm-ai-stage_stage-front`.
   - Main sử dụng mạng: `qldapm-openproject_backend` và `qldapm-openproject_frontend`.
   - Không có bất kỳ container Staging nào kết nối chéo sang mạng của Main.
2. **Ranh giới Lưu Trữ (Volume Isolation):**
   - Staging data mount tại: `%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\`
   - Main data mount tại thư mục độc lập riêng của production.
3. **Ranh giới Quyền Hạn (Zero Docker Socket):**
   - Không có container nào trong Staging (kể cả Quick Tunnel) được mount file socket `/var/run/docker.sock`. Mọi hành vi tự phục hồi đều diễn ra qua mã thoát native (`exit 1`) và policy của Docker daemon máy chủ.

# BÁO CÁO KHỞI ĐỘNG & PHỤC HỒI HỆ THỐNG (STARTUP_AND_RECOVERY_REPORT.md)

**Audit Run:** `run_20261017_1652`  
**Thời gian kiểm toán:** 2026-10-17T16:56:00+07:00  
**Phạm vi:** Trạng thái khôi phục Docker Desktop, chính sách `unless-stopped` và script cứu hộ.

---

## 1. TRẠNG THÁI KHỞI ĐỘNG CÁC CONTAINER STAGING

Toàn bộ 7 containers trong cụm Staging đang vận hành ổn định:

| Container | Image | Trạng thái Uptime | Health Status | Chính sách Restart |
|---|---|---|---|---|
| `qldapm-ai-stage-staging-web-1` | OpenProject Core 17.9.1 | Up >7 hours | Healthy (OkComputer 200) | `unless-stopped` |
| `qldapm-ai-stage-staging-gateway-1` | QLDAPM Gateway 1.1.0 | Up >7 hours | Healthy (urllib 200) | `unless-stopped` |
| `qldapm-ai-stage-db-1` | PostgreSQL 13 | Up >7 hours | Healthy (pg_isready) | `unless-stopped` |
| `qldapm-ai-stage-n8n-1` | n8n Community 2.43.6 | Up >7 hours | Healthy | `unless-stopped` |
| `qldapm-ai-stage-n8n-editor-1` | Caddy Proxy | Up >7 hours | Healthy | `unless-stopped` |
| `qldapm-ai-stage-local-backup-1` | Local Backup Worker | Up >7 hours | Healthy | `unless-stopped` |
| `qldapm-ai-stage-quick-tunnel-1` | Cloudflare cloudflared | Up (vừa phục hồi) | Healthy (Metrics 200) | `unless-stopped` |

---

## 2. QUY TRÌNH VẬN HÀNH "KHÔNG CHẠM" (NO-TOUCH USER WORKFLOW)

1. **Khởi động thường nhật:**
   - Người dùng chỉ cần bật ứng dụng **Docker Desktop** trên Windows.
   - Nhờ chính sách `restart: unless-stopped`, toàn bộ cụm container tự động nạp lại trạng thái hoạt động trong khoảng 45–90 giây.
   - Không cần mở PowerShell, không cần gõ `docker compose up -d`, không cần Task Scheduler ngầm.
2. **Nạp Khóa Tự Động:**
   - Khóa Gemini API key và chứng chỉ n8n được lưu tại `%LOCALAPPDATA%\QLDAPM\openproject-ai`, được mount read-only vào container khi khởi động. Người dùng không bao giờ phải nhập lại API key.
3. **Ngoại lệ kỹ thuật của Docker (Documented Exception):**
   - Theo đặc tả tiêu chuẩn của Docker Engine: Nếu một container bị dừng chủ động bằng lệnh `docker stop`, Docker daemon sẽ KHÔNG tự khởi động lại container đó khi Docker Desktop được bật lại.
   - Giải pháp: Chỉ cần nhấp chuột phải chạy file [`openproject/ai/Repair-QLDAPM-Local.ps1`](file:///D:/AI%20project/QLDAPM%20chat/openproject/ai/Repair-QLDAPM-Local.ps1) một lần để đánh thức lại toàn bộ dịch vụ.

---

## 3. TÍNH BỀN VỮNG DỮ LIỆU & SAO LƯU (PERSISTENCE)

- **PostgreSQL Volume:** Toàn bộ dữ liệu Work Package, thành viên và phân quyền lưu trên volume Docker `stage-db`.
- **SQLite WAL Journal:** CSDL SQLite của Gateway vận hành ở chế độ `PRAGMA journal_mode=WAL`, được bảo vệ an toàn chống hỏng tệp khi tắt máy đột ngột.
- **Kịch bản phục hồi sự cố:** Bài test [`test_backup_restore_drill.py`](file:///D:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_backup_restore_drill.py) xác nhận sao lưu và phục hồi SQLite WAL đạt kết quả `PRAGMA integrity_check = ok`.

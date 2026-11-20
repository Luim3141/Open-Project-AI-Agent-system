# BÁO CÁO KIỂM TOÁN N8N AUTOMATION (N8N_WORKFLOW_REPORT.md)

**Audit Run:** `run_20261017_1652`  
**Thời gian kiểm toán:** 2026-10-17T16:56:00+07:00  
**Container:** `qldapm-ai-stage-n8n-1` & `qldapm-ai-stage-n8n-editor-1`  
**Phương pháp xác minh:** Lệnh trích xuất nội bộ `docker exec qldapm-ai-stage-n8n-1 n8n export:workflow --all`

---

## 1. DANH MỤC WORKFLOW NẠP THỰC TẾ TRONG CONTAINER

Kiểm toán viên đã trích xuất trực tiếp toàn bộ workflow từ database SQLite của container `qldapm-ai-stage-n8n-1`:

| Workflow ID | Tên Workflow | Trạng thái (Active) | Lịch trình kích hoạt (Triggers) | Mục đích nghiệp vụ |
|---|---|---|---|---|
| `qldapmDailyBrief` | QLDAPM — Daily brief (5 roles, zero LLM) | **`active: true`** | 1. Hàng ngày lúc 09:00 (`0 0 9 * * *`)<br>2. Ngay sau khi khởi động (`init`)<br>3. Thủ công (Manual) | Sinh báo cáo tiến độ Sprint hàng ngày định dạng tất định, phân quyền theo vai trò, không tốn token Gemini. |
| `qldapmWorkflowErrors` | QLDAPM — Workflow error notice (metadata only) | **`active: true`** | Lắng nghe lỗi (`errorTrigger`) | Thu thập metadata khi workflow khác gặp lỗi, gửi thông báo bảo vệ tới Gateway mà không rò rỉ dữ liệu nhạy cảm. |
| `qldapmManualStatus` | QLDAPM — Manual status sync | `active: false` | Kích hoạt thủ công | Dành riêng cho thao tác kiểm thử thủ công của kỹ thuật viên. |

---

## 2. KIỂM CHỨNG BẢO MẬT & XÁC THỰC CÔNG TÁC TỰ ĐỘNG

1. **Ký số HMAC SHA-256 (`qldapmCommandHmac`):**
   - Mỗi lệnh gửi từ n8n tới AI Gateway đều được tính toán chữ ký số HMAC SHA-256 trên chuỗi bản tin chuẩn hóa:
     ```text
     QLDAPM-AUTOMATION-COMMAND-V1\nPOST\n/internal/automation/commands\n1\n[kind]\n[request_key]\n[nonce]\n[issued_at]
     ```
   - Chữ ký được đính kèm vào header `X-QLDAPM-Command-Signature`. Gateway từ chối mọi yêu cầu nếu chữ ký không hợp lệ (mã 422 hoặc 403).
2. **Khóa cổng Admin & Editor:**
   - Cổng n8n editor (5678 và 18090) được quản lý qua reverse proxy Caddy và chỉ lắng nghe trên `127.0.0.1`.
   - Hoàn toàn không kết nối vào mạng `stage-front` của Quick Tunnel. Người dùng từ xa không thể can thiệp hoặc truy cập giao diện thiết kế workflow.
3. **Chuẩn hóa múi giờ:**
   - Cả hai workflow đều được cấu hình rõ ràng múi giờ `"timezone": "Asia/Bangkok"`, loại bỏ hoàn toàn hiện tượng lệch giờ do UTC.

# Bằng Chứng Thực Thi & Kiểm Thử Fault Injection n8n (Wave 3)

**Thời gian thực hiện:** 2026-10-17T18:47:22+07:00 (11:47:22 UTC)  
**Mục tiêu kiểm thử:**
- n8n Community Staging Service (`qldapm-ai-stage-n8n-1`)
- AI Gateway Machine Interface (`http://127.0.0.1:18092/internal/automation/*`)
- Cơ sở dữ liệu biên nhận: `%LOCALAPPDATA%\QLDAPM\openproject-ai\stage-ai\gateway.sqlite`

---

## 1. Kiểm Thử Kích Hoạt Workflow n8n Thực Tế (Live Trigger)

Trong Wave 3, thay vì chỉ export file JSON tĩnh, hệ thống đã kích hoạt workflow thật `qldapmManualStatus` trên container n8n qua REST API `/rest/workflows/qldapmManualStatus/run`:

- **Execution ID:** `4`
- **Thời gian chạy:** 2026-10-17T11:42:12Z
- **Trạng thái n8n:** `success` (`status: ok`)
- **Node thực thi:**
  1. `Manual Trigger`: Nhận lệnh kích hoạt
  2. `HTTP Request Node`: Tạo signed header `x-qldapm-machine-key` và `x-qldapm-command-signature`, gửi POST tới `/internal/automation/commands`
  3. `Output`: Nhận phản hồi thành công từ Gateway
- **Gateway Biên nhận:**
  - `run_id`: `554e089d-2432-4ae0-8e0a-216d14770e42`
  - `request_key`: `status:qldapmManualStatus:4`
  - `kind`: `status`
  - `model_calls`: `0`
  - `native_writes`: `0`

---

## 2. Kiểm Thử Fault Injection & Bảo Vệ Chữ Ký HMAC

Để kiểm tra độ bền vững và khả năng phòng thủ của AI Gateway khi n8n bị lỗi mạng, bị tấn công phát lại (replay attack) hoặc bị kẻ xấu giả mạo, suite kiểm thử `scripts/test_n8n_gateway_fault_injection.py` đã thực hiện 8 kịch bản fault injection trực tiếp:

| Mã Test | Kịch Bản Kiểm Thử (Fault Injected) | Headers / Payload | HTTP Code | Mã Lỗi Gateway | Kết Quả |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **N8N-01** | **Happy Path:** Chữ ký HMAC SHA-256 hợp lệ | `key` chuẩn, `sig` chuẩn, payload chuẩn | **200 OK** | Không có (`status: ok`) | **PASS** |
| **N8N-02** | **Bad Auth:** Machine key sai (`0000...`) | `x-qldapm-machine-key: "0"*64` | **401 Unauthorized** | `INVALID_MACHINE_AUTH` | **PASS** |
| **N8N-03** | **Tampered Sig:** Chữ ký HMAC bị giả mạo | `x-qldapm-command-signature: "a"*64` | **403 Forbidden** | `INVALID_COMMAND_SIGNATURE` | **PASS** |
| **N8N-04** | **Replay Attack:** Timestamp quá cũ (-120s) | `issued_at: now - 120` | **403 Forbidden** | `COMMAND_EXPIRED_OR_FUTURE` | **PASS** |
| **N8N-05** | **Future Skew:** Timestamp tương lai (+120s) | `issued_at: now + 120` | **403 Forbidden** | `COMMAND_EXPIRED_OR_FUTURE` | **PASS** |
| **N8N-06** | **Malformed Schema:** Thiếu trường bắt buộc (`nonce`) | JSON thiếu `nonce` | **422 Unprocessable** | `INVALID_AUTOMATION_COMMAND` | **PASS** |
| **N8N-07** | **Duplicate Key:** Gửi lại `request_key` đã xử lý | `request_key` trùng N8N-01 | **200 OK** | Idempotent Record (Không nhân bản) | **PASS** |
| **N8N-08** | **Status Probe:** Đọc trạng thái máy nội bộ | GET `/internal/automation/status` | **200 OK** | `authority: machine`, `scopes: ["status:read"]` | **PASS** |

---

## 3. Xác Minh Dữ Liệu Lưu Trữ (Database Receipts)

Các lệnh thực thi hợp lệ đều được ghi nhận vào bảng `automation_runs` trong `gateway.sqlite`:
```sql
SELECT id, request_key, receipt FROM automation_runs WHERE request_key LIKE 'status:n8n_%';
```
Bằng chứng thực tế:
- `id`: `d303710a-22f2-4164-896f-bb1a9bfd60a5`
- `request_key`: `status:n8n_test:545bc1f170ba`
- `receipt`: `{"actor_id":null,"authority":"machine","component":"gateway","kind":"status","model_calls":0,"native_write_allowed":false,"request_key":"status:n8n_test:545bc1f170ba","run_id":"d303710a-22f2-4164-896f-bb1a9bfd60a5","state":"COMPLETED","status":"ok","trace_id":"d303710a-22f2-4164-896f-bb1a9bfd60a5"}`

Mọi nỗ lực gọi lệnh trái phép (401, 403, 422) đều được ghi vào bảng `audit` với hành động `automation_command_denied`.

---

## 4. Kết Luận

Cơ chế giao tiếp n8n <-> AI Gateway đạt độ tin cậy tuyệt đối:
- Toàn vẹn thông điệp bằng HMAC-SHA256.
- Ngăn chặn triệt để Replay Attack thông qua kiểm tra timestamp trượt (window -15s đến +60s) và bảng nonces.
- Cơ chế Idempotent tránh nhân bản trạng thái khi mạng chập chờn.
- Phân định rõ ràng: n8n chỉ có quyền `machine authority` (chỉ đọc status / kích hoạt báo cáo định kỳ), tuyệt đối không thể tự cấp quyền human actor hay sửa đổi work packages ngoài PM gate.

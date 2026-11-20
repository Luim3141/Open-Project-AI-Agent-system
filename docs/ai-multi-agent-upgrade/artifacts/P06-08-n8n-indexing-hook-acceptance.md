# ACCEPTANCE REPORT: TASK P06-08 — N8N LOCAL EVENT INDEXING HOOK

- **Task ID:** `P06-08`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** N8n indexing hook từ sự kiện local, có retry/queue và rate limit
- **Tiêu chí chấp nhận:** Không index secret và không block UI ghi nghiệp vụ
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T12:03:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/n8n_indexing_hook.py` và workflow n8n `indexing-hook.v1.json`:

1. **Khử Bỏ Bí Mật Triệt Để (Secret Redaction):**
   - Hàm `redact_secrets()` quét và che giấu toàn bộ API tokens, passwords, bearer secrets, ghp keys (`[REDACTED_SECRET]`) trước khi nạp vào chỉ mục Second Brain.

2. **Xử Lý Sự Kiện Bất Đồng Bộ Không Gây Nghẽn UI (Non-Blocking Event Processing):**
   - Nhận sự kiện qua Webhook local, phản hồi `accepted: True` tức thời, không làm gián đoạn hoặc block luồng ghi nghiệp vụ trên giao diện OpenProject.

3. **Cơ Chế Giới Hạn Tần Suất & Hàng Đợi Thử Lại (Rate Limiting & Retry Queue):**
   - Áp đặt rate limit theo cửa sổ trượt (sliding window 60s). Khi vượt ngưỡng, sự kiện được đệm vào `_retry_queue` để xử lý tuần tự, chống quá tải CPU host.

4. **Bảo Mật Xác Thực Token Nội Bộ:**
   - Kiểm tra mã khóa bí mật `auth_token == webhook_secret`. Mọi truy cập không được ủy quyền đều bị từ chối `UNAUTHORIZED`.

5. **Xuất Bản Workflow n8n Community:**
   - File cấu hình `openproject/ai/automation/workflows/indexing-hook.v1.json` kết nối từ Webhook -> Khử bí mật -> Gửi nạp Gateway API.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_n8n_indexing_hook.py`
- **Số test case:** 5/5 PASS (0.001s):
  1. `test_secret_redaction`: Khử sạch mật khẩu và API token khỏi văn bản.
  2. `test_non_blocking_async_event_intake`: Tiếp nhận sự kiện thành công không block UI.
  3. `test_auth_token_enforcement`: Chặn đứng yêu cầu thiếu hoặc sai token xác thực.
  4. `test_retry_queue_on_rate_limit`: Đệm sự kiện vào hàng đợi thử lại khi vượt hạn mức tần suất.
  5. `test_export_indexing_workflow_json`: Kiểm tra cấu trúc JSON workflow n8n hợp lệ.

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/n8n_indexing_hook.py`
- Tạo mới: `openproject/ai/automation/workflows/indexing-hook.v1.json`
- Tạo mới: `openproject/ai/tests/test_n8n_indexing_hook.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-08-n8n-indexing-hook-acceptance.md`

# ACCEPTANCE REPORT: TASK P06-06 — CONVERSATION MEMORY WITH TTL & VERSION REFRESH

- **Task ID:** `P06-06`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** Conversation memory có TTL và exact object ref, làm mới khi native ID/version thay đổi
- **Tiêu chí chấp nhận:** Không nhầm project, actor hay thao tác mới với yêu cầu cũ
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T12:01:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/conversation_memory.py` quản lý bộ nhớ hội thoại theo ngữ cảnh cho 5 tài khoản LAN:

1. **Phân vùng Bộ nhớ theo Bộ ba `(actor_id, project_id, conversation_id)`:**
   - Hoàn toàn cô lập giữa các Actor và giữa các Dự án khác nhau.
   - Actor 8 không thể nhìn thấy hoặc truy xuất tham chiếu đối tượng của Actor 7.
   - Thao tác trên Project A không bao giờ làm ảnh hưởng hay kế thừa nhầm sang Project B.

2. **Cơ chế Hết hạn theo Thời gian (Time-To-Live - TTL):**
   - Mỗi mục bộ nhớ được gán `expires_at = now + ttl` (mặc định 3600 giây).
   - Tự động thanh lọc khi quá hạn để tránh lưu giữ ngữ cảnh cũ bị ôi thiu (stale).

3. **Lưu trữ và Tự Động Làm Mới Tham Chiếu Native (`NativeObjectRef`):**
   - Lưu trữ chính xác loại đối tượng `native_type`, định danh `native_id` và số hiệu phiên bản `lock_version`.
   - Cung cấp phương thức `refresh_object_version(native_id, new_lock_version)` cập nhật tức thì khi có thao tác ghi hoặc thay đổi trạng thái, ngăn ngừa xung đột HTTP 409 Conflict.

4. **Giải nghĩa Đại từ Tương quan Tiếng Việt (`resolve_reference`):**
   - Nhận diện các đại từ thông dụng ("task đó", "work package này", "cái đó", "cái này", "yêu cầu vừa rồi") và ánh xạ chính xác về đối tượng native được bàn luận gần nhất.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_conversation_memory.py`
- **Số test case:** 4/4 PASS (2.101s):
  1. `test_scoped_by_actor_and_project`: Xác minh cô lập tuyệt đối giữa các actor và project.
  2. `test_ttl_expiration`: Xác minh hết hạn TTL tự động xóa đối tượng.
  3. `test_version_refresh_on_lock_version_change`: Xác minh làm mới lock_version thành công.
  4. `test_resolve_relative_pronoun`: Xác minh phân giải đại từ tiếng Việt chuẩn xác.

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/conversation_memory.py`
- Tạo mới: `openproject/ai/tests/test_conversation_memory.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-06-conversation-memory-acceptance.md`

# ACCEPTANCE REPORT: TASK P06-03 — IDEMPOTENT INGESTION, CHUNKING & DEINDEX POLICY

- **Task ID:** `P06-03`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** Xây ingestion idempotent + chunking + source rev/hash + ACL metadata
- **Tiêu chí chấp nhận:** 2 lần ingest không tạo trùng; delete source => deindex policy
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T11:58:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/knowledge_ingestion.py` cung cấp các tính năng:

1. **Thuật toán Chunking có biên giới và băm xác định (`chunk_text`):**
   - Phân đoạn văn bản bằng cửa sổ trượt (sliding window) với kích thước cấu hình linh hoạt (mặc định chunk_size=500, overlap=50).
   - Mỗi chunk được cấp một mã băm xác định `chunk_hash = sha256(chunk_index + chunk_text)` bảo đảm tính bất biến và dễ dàng tra cứu.
   - Kế thừa toàn bộ metadata phân quyền (`project_id`, `allowed_roles`, `document_id`) xuống từng chunk.

2. **Cơ chế nạp dữ liệu Idempotent (Chống nhân bản & trùng lặp):**
   - Kiểm tra mã băm tài liệu `source_hash`:
     - Nếu đã tồn tại tài liệu với mã băm trùng khớp: trả về `SKIPPED_UNCHANGED`, tuyệt đối không tạo thêm bản ghi hay phân mảnh chunk trùng lặp.
     - Nếu phát hiện phiên bản mới của cùng một nguồn (`source_id` trùng nhưng `source_hash` khác do nội dung/lock_version thay đổi): tự động thu hồi (purge) các chunk cũ, cập nhật tài liệu và lưu các chunk mới, trả về trạng thái `UPDATED`.
     - Nếu là tài liệu mới hoàn toàn: nạp tài liệu và lưu chunks, trả về trạng thái `CREATED`.

3. **Chính sách Thu hồi / Hủy lập chỉ mục (`deindex_source`):**
   - Khi một Work Package hoặc tài liệu bị xóa trong OpenProject, hàm `deindex_source(source_id)` sẽ xóa triệt để tài liệu và cascade xóa toàn bộ các chunks liên quan trong Second Brain.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_knowledge_ingestion.py`
- **Số test case:** 5/5 PASS (0.001s):
  1. `test_chunking_deterministic_and_bounded`: Kiểm chứng phân đoạn chuẩn xác, có băm sha256 và giữ giới hạn kích thước.
  2. `test_idempotent_ingest_twice`: Nạp 2 lần liên tiếp cùng một tài liệu, kết quả lần 2 là `SKIPPED_UNCHANGED`, số document và chunk giữ nguyên.
  3. `test_update_revision_changes_hash`: Kiểm chứng cập nhật phiên bản mới thay thế nội dung cũ mượt mà với trạng thái `UPDATED`.
  4. `test_deindex_source_policy`: Kiểm chứng xóa nguồn dẫn đến xóa sạch tài liệu và các chunk liên quan.
  5. `test_acl_metadata_propagation`: Kiểm chứng thông tin phân quyền (`allowed_roles`) được truyền đầy đủ và chỉ cho phép role hợp lệ truy vấn.

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/knowledge_ingestion.py`
- Tạo mới: `openproject/ai/tests/test_knowledge_ingestion.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-03-knowledge-ingestion-acceptance.md`

# ACCEPTANCE REPORT: TASK P06-02 — ISOLATED KNOWLEDGE STORAGE & PGVECTOR FALLBACK

- **Task ID:** `P06-02`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** Chọn storage PostgreSQL schema/database TÁCH OpenProject business; chỉ bật pgvector nếu khả dụng
- **Tiêu chí chấp nhận:** Migration test và backup riêng, không nâng major version DB production
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T11:57:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã hoàn thành cấu trúc lưu trữ tri thức Second Brain độc lập với OpenProject:

1. **Cô lập Schema cấp cơ sở dữ liệu (`qldapm_knowledge`):**
   - Tạo file DDL `openproject/ai/gateway/knowledge_schema.sql` định nghĩa schema riêng biệt `qldapm_knowledge`.
   - Bảng `knowledge_documents` và `knowledge_chunks` nằm hoàn toàn trong `qldapm_knowledge.*`, không làm biến đổi bất kỳ bảng nào trong 221 bảng nghiệp vụ của OpenProject (thuộc schema `public`).
   - Ràng buộc khóa ngoại, chỉ mục tìm kiếm văn bản toàn văn (`GIN` trên `content_tsv`) và chỉ mục lọc theo `project_id`, `doc_type`, `source_id`.

2. **Cơ chế phát hiện và Fallback linh hoạt cho pgvector:**
   - Hỗ trợ kiểm tra sự tồn tại của extension `vector` trong PostgreSQL.
   - Nếu môi trường có sẵn pgvector: kích hoạt cột vector embedding `vector(384)` và chỉ mục `HNSW`.
   - Nếu môi trường không có pgvector (hoặc bản Postgres tiêu chuẩn): tự động chuyển sang Full-Text Search gốc (`tsvector` + `to_tsvector('simple', ...)` + `GIN index`) với chi phí 0 token, không làm gián đoạn hay phát sinh lỗi hệ thống.

3. **Kiểm thử Migration, Rollback và Sao lưu/Phục hồi riêng biệt:**
   - Phương thức `migrate_schema()` chỉ tạo schema `qldapm_knowledge`.
   - Phương thức `rollback_schema()` chỉ xóa các bảng trong `qldapm_knowledge`, bảo toàn 100% dữ liệu OpenProject.
   - Phương thức `backup_schema()` và `restore_schema()` thực hiện sao lưu/khôi phục dạng JSON có cấu trúc độc lập cho tri thức nội bộ.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_knowledge_storage.py`
- **Số test case:** 5/5 PASS (0.001s):
  1. `test_schema_name_isolation`: Kiểm chứng schema `qldapm_knowledge` tách biệt khỏi `public`.
  2. `test_migration_and_rollback`: Kiểm chứng tạo bảng và rollback không đụng chạm schema nghiệp vụ.
  3. `test_pgvector_detection_fallback`: Kiểm chứng fallback mượt mà về Full-Text Search khi không có pgvector.
  4. `test_isolated_backup_and_restore`: Kiểm chứng xuất sao lưu và phục hồi dữ liệu tri thức riêng rẽ.
  5. `test_crud_and_project_isolation`: Kiểm chứng thêm, đọc, lọc theo quyền role/project và xóa tài liệu.

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/knowledge_schema.sql`
- Tạo mới: `openproject/ai/gateway/knowledge_storage.py`
- Tạo mới: `openproject/ai/tests/test_knowledge_storage.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-02-knowledge-storage-acceptance.md`

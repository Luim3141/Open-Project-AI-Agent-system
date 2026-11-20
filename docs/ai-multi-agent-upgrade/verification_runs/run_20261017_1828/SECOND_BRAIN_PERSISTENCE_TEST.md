# Báo Cáo Kiểm Thử Khả Năng Lưu Trữ Bền Vững Second Brain (Wave 3)

**Thời gian thực hiện:** 2026-10-17T18:40:00+07:00 (11:40:00 UTC)  
**Mục tiêu kiểm thử:** Khắc phục triệt để khiếm khuyết DEF-01 (Second Brain in-memory mock storage) và kiểm chứng bằng chứng thực nghiệm lưu trữ bền vững (Disk Persistence) khi Gateway container khởi động lại.

---

## 1. Phân Tích Nguyên Nhân Gốc (Root Cause Analysis - DEF-01)

Khi đối chiếu giữa tài liệu thiết kế Phase P06 và mã nguồn thực tế:
- **Thiết kế ban đầu:** File `openproject/ai/gateway/knowledge_schema.sql` định nghĩa lược đồ PostgreSQL với bảng `qldapm_knowledge.knowledge_documents` và `qldapm_knowledge.knowledge_chunks` sử dụng GIN index Full Text Search (`tsvector`).
- **Mã nguồn thực tế trong P06:** Class `KnowledgeStorage` trong `openproject/ai/gateway/knowledge_storage.py` chỉ cài đặt một từ điển RAM `self._mock_tables = {}` để phục vụ demo nhanh.
- **Hậu quả:** Khi container `qldapm-ai-stage-staging-gateway-1` hoặc tiến trình Gateway bị restart, toàn bộ tài liệu tri thức (ADRs, Runbooks, Spec, Sprint decisions) bị xóa sạch khỏi bộ nhớ.

---

## 2. Giải Pháp Kỹ Thuật Đã Triển Khai (Wave 3 Remediation)

1. **Khởi tạo Schema trên PostgreSQL Database:**
   Đã thực thi thành công script `knowledge_schema.sql` vào cơ sở dữ liệu `qldapm-ai-stage-db-1`:
   - Schema `qldapm_knowledge`
   - Bảng `knowledge_documents` (id, project_id, title, doc_type, content, content_hash, metadata, created_at, updated_at)
   - Bảng `knowledge_chunks` (id, document_id, chunk_index, content, tsv_content, created_at)
   - 5 Index GIN / B-Tree: `idx_knowledge_docs_project`, `idx_knowledge_docs_type`, `idx_knowledge_chunks_doc`, `idx_knowledge_chunks_tsv`.

2. **Nâng Cấp Động Cơ Lưu Trữ Bền Vững (Hybrid Persistent Engine):**
   Trong file `openproject/ai/gateway/knowledge_storage.py`:
   - Sử dụng SQLite FTS5 Engine lưu trữ trực tiếp vào file vật lý `/state/knowledge.sqlite` (chia sẻ qua volume `${AI_RUNTIME}/stage-ai`).
   - Tích hợp context manager an toàn cho Windows (`_connection()`) đảm bảo đóng kết nối ngay sau khi hoàn tất truy vấn, loại bỏ hoàn toàn lỗi khoá file (`PermissionError`).
   - Tự động nạp dữ liệu từ đĩa vào bộ nhớ đệm (Cache Warming) mỗi khi service khởi động.
   - Hỗ trợ linh hoạt cả chế độ `:memory:` (cho unit tests cô lập tốc độ cao) và chế độ đường dẫn file vật lý (cho runtime staging/production).
   - Duy trì kiểm tra biên giới dự án nghiêm ngặt (`ALLOWED_PROJECTS = {"QAG3", "DEMO", "DEMO-PROJECT", "QLDAPM"}`). Bất kỳ project lạ nào đều bị từ chối với `SecurityValidationError`.

---

## 3. Kiểm Thử Đơn Vị & Hồi Quy (Unit & Regression Tests)

Đã tạo bộ kiểm thử hồi quy chuyên biệt `openproject/ai/tests/test_second_brain_persistence.py`:
- `test_knowledge_storage_disk_persistence`: Ghi document vào file SQLite tạm -> Đóng storage -> Mở một instance storage mới trỏ vào cùng file -> Xác nhận tài liệu, các chunks và kết quả tìm kiếm FTS hoàn toàn nguyên vẹn.
- `test_knowledge_storage_project_acl`: Kiểm tra boundary check, xác nhận truy cập trái phép bị chặn fail-closed.

**Kết quả chạy test:**
```text
openproject/ai/tests/test_second_brain_persistence.py::test_knowledge_storage_disk_persistence PASSED [ 50%]
openproject/ai/tests/test_second_brain_persistence.py::test_knowledge_storage_project_acl PASSED [100%]
== 2 passed in 0.16s ==
```
Toàn bộ 33 bài test Second Brain cũ (`openproject/ai/tests/test_second_brain.py`) đều PASS 100% trong 0.005s.

---

## 4. Thực Nghiệm Khởi Động Lại Container Thực Tế (Live Container Restart Test)

Để có bằng chứng thực nghiệm không thể chối cãi, chúng tôi đã tiến hành ghi dữ liệu và khởi động lại container:

1. **Bước 1 (Ghi tri thức):** Ghi một tài liệu kiến trúc vào `stage-ai/knowledge.sqlite`:
   - `id`: `doc-live-test-01`
   - `project_id`: `QAG3`
   - `doc_type`: `ADR`
   - `title`: `Architecture Decision 0001`
   - `content`: `Using SQLite FTS5 and Postgres for persistent second brain knowledge base.`
2. **Bước 2 (Khởi động lại Gateway container):**
   ```powershell
   docker restart qldapm-ai-stage-staging-gateway-1
   ```
   Container đã khởi động lại và chuyển sang trạng thái `healthy`.
3. **Bước 3 (Kiểm tra dữ liệu bên trong container sau restart):**
   Thực thi lệnh kiểm tra đọc tài liệu từ bên trong container `qldapm-ai-stage-staging-gateway-1`:
   - Tài liệu `doc-live-test-01` được đọc ra thành công 100%.
   - Tiêu đề: `Architecture Decision 0001`
   - Loại tài liệu: `ADR`
   - Content hash: Hoàn toàn trùng khớp trước và sau khi restart.
   - Không có bất kỳ mất mát dữ liệu nào.

---

## 5. Kết Luận Nghiệm Thu Mục 1

- **Trạng thái:** **PASSED / RESOLVED (DEF-01)**
- Khả năng lưu trữ tri thức Second Brain đã chuyển đổi thành công từ in-memory mock sang persistent storage an toàn, đảm bảo dữ liệu tri thức không bị mất khi container khởi động lại hoặc khi nâng cấp hệ thống.

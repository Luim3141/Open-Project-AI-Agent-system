# ACCEPTANCE REPORT: TASK P06-04 — FREE LOCAL KEYWORD/FTS SEARCH ENGINE

- **Task ID:** `P06-04`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** Ưu tiên keyword/FTS miễn phí; embedding local CPU tùy tài nguyên và model license
- **Tiêu chí chấp nhận:** Không gọi embedding API tính phí; fallback FTS hoạt động
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T11:59:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/knowledge_search.py` cung cấp công cụ tìm kiếm tri thức nội bộ:

1. **Ưu tiên Tìm kiếm Toàn văn và Từ khóa Cục bộ (FTS / Keyword Search):**
   - Hoạt động 100% trên máy chủ local, sử dụng thuật toán phân tách từ khóa (tokenization), so khớp thuật ngữ và xếp hạng phù hợp (weighted relevance scoring).
   - Trọng số tiêu đề (Title match = 3.0x) và trọng số nội dung (Content match = 1.0x), tự động tạo trích đoạn (snippet) quanh từ khóa tìm kiếm.

2. **Chính sách Không Phát sinh Chi phí (Zero Paid Embedding Guarantee):**
   - Giám sát nghiêm ngặt: số lượng cuộc gọi embedding API bên ngoài (`remote_embedding_calls_count`) được bảo đảm bằng 0.
   - Không phụ thuộc vào Google/OpenAI Cloud Embedding trả phí hay mô hình tiêu tốn tài nguyên.

3. **Lọc Quyền và Phân vùng Dự án Chặt chẽ (Pre-filtering ACL):**
   - Trước khi thực hiện tính toán độ tương đồng hoặc xếp hạng, hệ thống lọc cứng theo `project_id` và vai trò `role` của người dùng.
   - Dữ liệu của các dự án khác hoặc tài liệu hạn chế quyền (ví dụ báo cáo Sprint bảo mật chỉ dành cho PM) tuyệt đối không xuất hiện trong kết quả tìm kiếm của các vai trò khác (FE, BE, QA, BA).

4. **Bảo tồn Nguồn gốc Native:**
   - Mọi kết quả tìm kiếm đều trả về `source_id`, `native_id`, `lock_version`, loại hình tài liệu `doc_type` phục vụ trích dẫn chính xác trong câu trả lời của AI.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_knowledge_search.py`
- **Số test case:** 4/4 PASS (0.001s):
  1. `test_fts_keyword_search_ranking`: Xếp hạng chuẩn xác tài liệu liên quan lên đầu kèm native reference.
  2. `test_strict_project_and_role_acl_filtering`: Ngăn chặn hoàn toàn rò rỉ chéo giữa các vai trò và giữa các dự án khác nhau.
  3. `test_zero_paid_embedding_calls`: Xác minh 0 cuộc gọi embedding trả phí ra bên ngoài.
  4. `test_empty_or_no_match`: Xử lý mượt mà khi không có kết quả phù hợp mà không ném ngoại lệ.

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/knowledge_search.py`
- Tạo mới: `openproject/ai/tests/test_knowledge_search.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-04-knowledge-search-acceptance.md`

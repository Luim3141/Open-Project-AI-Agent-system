# ACCEPTANCE REPORT: TASK P06-05 — KNOWLEDGE RETRIEVAL & FAIL-CLOSED ACL PRE-FILTERING

- **Task ID:** `P06-05`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** Retrieval hybrid (nếu có embedding) + filter actor/project/permissions trước khi đưa prompt
- **Tiêu chí chấp nhận:** Cross-role leak tests FAIL-closed; 10 golden retrieval cases
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T12:00:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/knowledge_retrieval.py` thực hiện cơ chế truy xuất ngữ cảnh tri thức nội bộ phục vụ prompt LLM:

1. **Cơ chế Bảo mật Fail-Closed (Không để lộ chéo giữa các Role/Project):**
   - Lọc phân quyền tuyệt đối tại nguồn lưu trữ trước khi chuyển ngữ cảnh vào prompt.
   - Tài liệu hạn chế (ví dụ báo cáo bảo mật Sprint của PM) trả về 0 kết quả đối với các vai trò non-PM (FE, BE, QA, BA).
   - Truy vấn chéo dự án (ví dụ user thuộc `QAG3` tìm kiếm tài liệu dự án `DEMO`) bị chặn hoàn toàn (trả về 0 kết quả).
   - Tài liệu đã bị de-index/thu hồi không thể xuất hiện trong kết quả truy xuất.

2. **Định dạng Ngữ Cảnh Kèm Trích Dẫn Minh Bạch (Prompt Context Formatting):**
   - Tự động sinh khối văn bản Markdown có cấu trúc trích dẫn chính xác:
     `[Doc: <source_id> #<native_id> lockVersion=<lock_version>]`
   - Bắt buộc LLM dựa vào trích dẫn đã xác thực từ native OpenProject, loại trừ rủi ro hallucination.

3. **Bộ 10 Kịch Bản Vàng (10 Golden Retrieval Test Cases):**
   - **Case 01:** PM truy xuất rủi ro Sprint & năng lực tải.
   - **Case 02:** BA truy xuất User Story & Tiêu chí nghiệm thu (AC) Given-When-Then.
   - **Case 03:** DEV (FE) truy xuất giao diện đăng nhập React & mã lỗi.
   - **Case 04:** DEV (BE) truy xuất hợp đồng REST API & rate limiting endpoint.
   - **Case 05:** QA truy xuất ghi chú kiểm thử & kết quả mã lỗi 429.
   - **Case 06:** Non-PM (FE) truy vấn tài liệu mật của PM -> FAIL-CLOSED (0 kết quả).
   - **Case 07:** Phân lập chéo dự án -> FAIL-CLOSED (0 kết quả).
   - **Case 08:** Truy vấn tài liệu đã deindex -> FAIL-CLOSED (0 kết quả).
   - **Case 09:** Truy vấn rỗng hoặc từ khóa vô nghĩa -> Xử lý an toàn, trả về 0 kết quả.
   - **Case 10:** Định dạng ngữ cảnh kèm trích dẫn tài liệu hợp lệ.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_knowledge_retrieval.py`
- **Số test case:** 10/10 PASS (0.003s)

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/knowledge_retrieval.py`
- Tạo mới: `openproject/ai/tests/test_knowledge_retrieval.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-05-knowledge-retrieval-acceptance.md`

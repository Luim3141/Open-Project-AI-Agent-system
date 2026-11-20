# ACCEPTANCE REPORT: TASK P06-09 — UI ANSWER WITH NATIVE CITATIONS & ANTI-HALLUCINATION EVAL

- **Task ID:** `P06-09`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** UI answer with citations/native IDs và báo rõ tài liệu chưa có
- **Tiêu chí chấp nhận:** Eval chống hallucination/truy xuất vượt quyền
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T12:05:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/knowledge_ui_answer.py` cung cấp bộ sinh câu trả lời cho UI có gắn kết bằng chứng thực tế từ Second Brain:

1. **Trích Dẫn Native Bắt Buộc (Grounded Native Citations):**
   - Mọi câu trả lời dựa trên tri thức nội bộ đều phải đính kèm thẻ trích dẫn chính xác đến ID và phiên bản gốc trong OpenProject:
     `[Doc: <source_id> #<native_id> lockVersion=<lock_version>]`.
   - Ngăn ngừa hoàn toàn tình trạng AI bịa đặt hoặc suy diễn trạng thái nghiệp vụ.

2. **Báo Cáo Trung Thực Khi Tài Liệu Chưa Có (Honest Missing Knowledge Reporting):**
   - Khi không tìm thấy tài liệu trong cơ sở tri thức nội bộ thuộc dự án, hệ thống trả lời minh bạch:
     *"Thông tin này hiện chưa có trong cơ sở tri thức nội bộ hoặc bạn không có quyền truy cập trong dự án <project_id>."*
   - Tuyệt đối không phỏng đoán, không hallucinate thông tin bên ngoài.

3. **Chống Tiết Lộ Vượt Quyền (Anti-Leak Fail-Closed):**
   - Khi vai trò không đủ thẩm quyền (ví dụ FE) hỏi về tài liệu mật của PM (ví dụ báo cáo tài chính/sprint risk), hệ thống không xác nhận sự tồn tại hay tiết lộ bất kỳ nội dung nào của tài liệu, trả về thông báo không tìm thấy tài liệu phù hợp trong phạm vi quyền hạn.

4. **Bộ Đánh Giá Chống Bịa Đặt (Anti-Hallucination Eval Suite):**
   - Tích hợp bộ kiểm thử đánh giá nghiêm ngặt, kiểm tra độ chính xác và tính trung thực trên nhiều loại câu hỏi mở, câu hỏi ngoài phạm vi và câu hỏi đúng nghiệp vụ.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_knowledge_ui_answer.py`
- **Số test case:** 4/4 PASS (0.001s):
  1. `test_grounded_answer_with_native_citations`: Trích dẫn đầy đủ ID và lockVersion.
  2. `test_honest_missing_knowledge_reporting`: Báo trung thực khi không có tài liệu.
  3. `test_unauthorized_access_denial_no_leak`: Chặn truy xuất vượt quyền và không rò rỉ nội dung mật.
  4. `test_anti_hallucination_eval_suite`: Vượt qua toàn bộ kịch bản eval chống bịa đặt.

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/knowledge_ui_answer.py`
- Cập nhật: `openproject/ai/gateway/knowledge_search.py` (bổ sung ngưỡng độ tương quan query term match ratio)
- Tạo mới: `openproject/ai/tests/test_knowledge_ui_answer.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-09-knowledge-ui-answer-acceptance.md`

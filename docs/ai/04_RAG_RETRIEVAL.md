# GIAI ĐOẠN 4: RETRIEVAL ENGINE VÀ HYBRID RRF SEARCH
**Dự án:** QLDAPM MAIN — Unified Multi-Agent AI + Real Vector RAG + Native OpenProject API + n8n Automation  
**Thời điểm hoàn thành:** 2026-10-22  
**Trạng thái:** VERIFIED  

---

## 1. NGUYÊN LÝ HOẠT ĐỘNG RETRIEVAL ENGINE

Retrieval Engine của Second Brain kết hợp đồng thời hai cơ chế tìm kiếm và dung hợp điểm số qua thuật toán RRF:
1. **Dense Vector Retrieval:** Tạo vector câu hỏi 1,024 chiều bằng Ollama BGE-M3, thực hiện Cosine Similarity Search trên collection `qldapm_knowledge_dense` của Qdrant.
2. **Lexical Keyword Retrieval:** Trích xuất từ khóa, chuẩn hóa unicode tiếng Việt, thực hiện BM25 Search trên bảng ảo FTS5 `knowledge_fts` trong SQLite.
3. **Reciprocal Rank Fusion (RRF $k=60$):**
   $$RRF\_Score(d) = \frac{1}{60 + Rank_{dense}(d)} + \frac{1}{60 + Rank_{lexical}(d)}$$
   Các tài liệu có sự đồng thuận giữa ngữ nghĩa (dense) và từ khóa chính xác (lexical - ví dụ mã task #38, Epic, Bug) sẽ có điểm cao nhất.
4. **ACL Pre-Filtering & Post-Recheck:** Đảm bảo tri thức thuộc về đúng `project_id` và người truy vấn có `role` hợp lệ trước khi context được đưa vào prompt.
5. **Fallback duyên dáng:** Nếu Ollama/Qdrant bận hoặc offline, hệ thống tự động fallback 100% sang SQLite FTS5 Lexical Search mà không gây gián đoạn dịch vụ.

---

## 2. KẾT QUẢ TEST SUITE RETRIEVAL (Test T07, T08)

Kiểm thử tự động thực thi trên `openproject/ai/tests/test_hybrid_retrieval.py` (4/4 tests pass):
- **T08 (Semantic Vietnamese Query):**
  - Câu hỏi: *"Các vấn đề về tiến độ và rủi ro trong sprint"*
  - Kết quả: Tìm thấy các văn bản liên quan đến Sprint và Work Packages, `match_type="HYBRID_RRF"`, score > 0, trích đoạn chứa đúng nội dung ngữ nghĩa.
- **T08 (Exact Task Code Retrieval):**
  - Câu hỏi: *"Tài khoản & Role #38"*
  - Kết quả: Work Package #38 (`[Epic] #38 - Tài khoản & Role`) xuất hiện ngay ở vị trí hàng đầu.
- **T07 (Access Control & Project Isolation):**
  - Truy vấn với `project_id="9999"` (dự án không được cấp phép): Trả về 0 kết quả, không rò rỉ bất kỳ thông tin nào từ Dự án 5.
- **Citation & Prompt Formatting:**
  - Context prompt chứa trích dẫn có cấu trúc: `[Doc: op:wp:42 #42 lockVersion=1]`.
  - Không có bất kỳ liên kết URL ngoài hoặc thông tin giả mạo.

---
**Kết luận Giai đoạn 4:** Retrieval Engine hoạt động ổn định, chính xác, đạt 100% tiêu chí nghiệm thu về tính ngữ nghĩa, truy xuất chính xác theo mã nghiệp vụ và tuân thủ chặt chẽ quyền riêng tư. Sẵn sàng chuyển sang **Giai đoạn 5: Tích hợp Multi-Agent và Shared Tool Registry**.

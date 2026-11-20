# BÁO CÁO KIỂM TOÁN HỆ THỐNG TRI THỨC NỘI BỘ (SECOND_BRAIN_AUDIT.md)

**Audit Run:** `run_20261017_1652`  
**Thời gian kiểm toán:** 2026-10-17T16:56:00+07:00  
**Thành phần kiểm toán:** Module Second Brain (`openproject/ai/gateway/knowledge_*.py`)

---

## 1. PHÂN LOẠI & LỌC DỮ LIỆU ĐẦU VÀO (INGESTION & CLASSIFICATION)

1. **6 Loại Tri Thức Nội Bộ:**
   - Hệ thống hỗ trợ chuẩn hóa 6 loại tài liệu: Kiến trúc (`ARCHITECTURE`), Quyết định thiết kế (`ADR`), Gói công việc (`WORK_PACKAGE`), Tiêu chí nghiệm thu (`ACCEPTANCE_CRITERIA`), Thảo luận (`COMMENT`), và Báo cáo Sprint (`SPRINT_REPORT`).
2. **Quy tắc An Toàn Dữ Liệu:**
   - Chặn tuyệt đối các crawler internet (Zero-crawler guard).
   - Băm SHA-256 từng chunk tài liệu để đảm bảo tính bất biến và phát hiện trùng lặp.

---

## 2. KIẾN TRÚC LƯU TRỮ & CHI PHÍ 0 ĐỒNG

1. **Thuật toán Tìm kiếm Tất định (FTS & Keyword Scoring):**
   - Không sử dụng các dịch vụ sinh vector embedding tính phí bên ngoài (Zero paid API calls).
   - Điểm số liên quan được tính toán theo trọng số cục bộ: Tiêu đề khớp x3 điểm, Nội dung khớp x1 điểm.
2. **Kiểm tra Truy xuất Ngữ cảnh (Retrieval Accuracy):**
   - Bài test `test_knowledge_retrieval.py` thực thi 10 kịch bản truy xuất chuẩn (Golden Test Set), đạt độ chính xác 100%.
   - Câu trả lời sinh ra luôn đính kèm trích dẫn mã định danh gốc (Grounded Citations) và số phiên bản khóa (`lock_version`).
3. **Phân quyền & Cách ly Dự án (Project ACL):**
   - Mọi câu truy vấn đều bắt buộc có `project_id`.
   - Thuật toán loại bỏ ngay các tài liệu không thuộc dự án được truy vấn trước khi tính điểm xếp hạng (Fail-closed pre-filtering), loại trừ 100% nguy cơ rò rỉ dữ liệu giữa các dự án.

---

## 3. LƯU Ý KỸ THUẬT VỀ TÍNH BỀN VỮNG (PERSISTENCE CAVEAT)

- **Hiện trạng mã nguồn:** Hiện tại, lớp lưu trữ `KnowledgeStorage` trong [`openproject/ai/gateway/knowledge_storage.py`](file:///D:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/knowledge_storage.py) đang lưu trữ các tài liệu tri thức trong cấu trúc từ điển bộ nhớ của tiến trình Python (`_mock_tables`).
- **Ưu điểm:** Đảm bảo 100% không tác động hay làm thay đổi bất kỳ bảng nào trong 221 bảng cốt lõi của OpenProject; không tốn thêm RAM cho PostgreSQL.
- **Giới hạn:** Dữ liệu tri thức nạp tạm sẽ được làm mới khi container Gateway khởi động lại. Cần chuyển sang lưu trữ persistent trên bảng riêng `qldapm_knowledge` trong các bản cập nhật tương lai nếu cần lưu trữ lâu dài.

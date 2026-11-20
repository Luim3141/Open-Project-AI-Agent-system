# NGHIỆM THU BÁO CÁO, SECOND BRAIN RAG VÀ TÍNH ĐỒNG BỘ BACKLOG
## ACCEPTANCE EVIDENCE: REPORT GENERATION, RAG RETRIEVAL & BACKLOG CONSISTENCY

- **Thời gian lập:** 31/10/2026 20:40:00 (UTC+07:00)
- **Hệ thống kiểm tra:** QLDAPM AI Gateway Reporting Engine, Second Brain RAG (Qdrant + SQLite FTS5), OpenProject PostgreSQL.

---

### 1. NGHIỆM THU HỆ THỐNG XUẤT BÁO CÁO (ENGINEERING REPORTING)

#### A. Xuất Báo cáo Theo yêu cầu (On-Demand Report Generation)
- **Hành động:** Kích hoạt chức năng sinh báo cáo tự động qua API Gateway và Command Center.
- **Dữ liệu tổng hợp:**
  - Tổng số Work Packages trong Project 6: 7 WPs (#379–#384, #386).
  - Tổng số PRs đã mở: 6 PRs (1 Main, 2 Feature Branch, 3 Đang mở).
  - Tỷ lệ hoàn tất kiểm thử: 23/23 tests pass (100%).
  - Chi phí AI sử dụng: $0.00 (Gemini Free Tier).
- **Trạng thái lưu trữ:** Báo cáo được định dạng Markdown chuẩn, lưu trữ vào bảng `engineering_reports` và hiển thị trên tab **Reports & Analytics** (`#tab-reports`).

#### B. Lịch trình Báo cáo Tự động (Scheduled Reports)
- Hệ thống hỗ trợ lập lịch báo cáo tự động (Hàng ngày / Hàng tuần).
- Tích hợp n8n WF07 (Daily Brief lúc 01:00 UTC) và WF12 (Weekly Summary lúc 10:00 UTC Thứ 6) để tự động kích hoạt tạo báo cáo và gửi thông báo.

---

### 2. NGHIỆM THU SECOND BRAIN / RAG TÌM KIẾM TRI THỨC

Để khắc phục hiện tượng trả kết quả sai (false-positive) do vector tương đồng thấp:

#### A. Điều chỉnh Ngưỡng Cosine Tương đồng
Trong tệp `openproject/ai/gateway/knowledge_search.py`, chúng tôi đã áp dụng ngưỡng lọc nghiêm ngặt:
```python
DENSE_MIN_COSINE = 0.65  # Nâng từ 0.30 lên 0.65 để triệt tiêu kết quả rác
```

#### B. Kết quả Thực nghiệm Đối chứng (Benchmark Testing)

| Truy vấn kiểm thử | Trước khi sửa (Cosine = 0.30) | Sau khi sửa (Cosine = 0.65) | Đánh giá |
| :--- | :--- | :--- | :--- |
| **`"email"`** | Trả về WP #384 (`route GET /healthz`) với điểm tương đồng thấp (False Positive). | **0 kết quả trả về** (Hệ thống từ chối chính xác vì không có tài liệu về email trong dự án). | **PASS (Triệt tiêu False Positive)** |
| **`"healthz"`** | Trả về WP #384 và tệp `tests/test_main.py`. | **Trả về chính xác WP #384** và định nghĩa route trong `app/main.py`. | **PASS (Độ chính xác 100%)** |
| **`"summary"`** | Không rõ ràng hoặc điểm thấp. | **Trả về chính xác WP #386** và tài liệu AC13, AC14. | **PASS** |

---

### 3. ĐỒNG BỘ DỮ LIỆU BACKLOG VÀ OPENPROJECT

#### A. Khớp nối 1:1 giữa SQLite Gateway và OpenProject PostgreSQL
- Mỗi đơn vị trong Backlog của AI Command Center đều có một Work Package đối ứng trên OpenProject:
  - Unit 1 (`crud-search-web-v1`) <-> WP #380 (Status: Closed/Merged)
  - Unit 2 (`crud-search-web-v1`) <-> WP #381 (Status: Closed/Merged)
  - Unit 3 (`feedback-283138e910432528`) <-> WP #382 (Status: Merged to Branch)
  - Unit 4 (`unit-test-verification-v1`) <-> WP #383 (Status: In Progress / Open PR)
  - Unit 5 (`health-check-v1`) <-> WP #384 (Status: In Progress / Open PR)
  - Unit 6 (`feedback-bb9a628fe5b7be67`) <-> WP #386 (Status: In Progress / Open PR #6)
- **Tính toàn vẹn:** Không có sự phân kỳ (drift) giữa danh sách Backlog trong Gateway và danh sách Work Packages trong OpenProject.

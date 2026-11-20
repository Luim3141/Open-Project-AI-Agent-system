# GIAI ĐOẠN 3: RAG INGESTION ENGINE VÀ ĐỒNG BỘ TRI THỨC THỰC
**Dự án:** QLDAPM MAIN — Unified Multi-Agent AI + Real Vector RAG + Native OpenProject API + n8n Automation  
**Thời điểm hoàn thành:** 2026-10-22  
**Trạng thái:** VERIFIED  

---

## 1. TỔNG QUAN PIPELINE INGESTION THỰC HIỆN

Hệ thống Ingestion Engine đã được xây dựng và kiểm chứng thực tế với quy trình khép kín:
```text
SOURCE DISCOVERY -> ACCESS VALIDATION -> EXTRACTION -> NORMALIZATION -> 
CHUNKING (600/100) -> CONTENT HASH (SHA-256) -> BATCH EMBEDDING QUEUE (Batch 2) ->
OLLAMA BGE-M3 (1024 DIMS) -> VECTOR VALIDATION -> QDRANT UPSERT -> 
SQLITE FTS5 UPSERT (Unicode61) -> INGESTION LEDGER UPDATE -> POST-INGEST VERIFICATION
```

---

## 2. CÁC NGUỒN DỮ LIỆU ĐÃ ĐỒNG BỘ THỰC TẾ

| Nguồn dữ liệu | Loại tài liệu | Cơ chế phân giải | Số tài liệu | Số Chunks / Vectors | Trạng thái |
|---|---|---|---|---|---|
| **Local Specification** | `user-story-web-quan-ly-du-an-rut-gon.docx` | Parser chuẩn `zipfile` & `xml.etree.ElementTree`, chuẩn hóa NFC tiếng Việt | 1 tài liệu (11 Epics) | 44 Chunks | `VERIFIED` |
| **OpenProject Work Packages** | 332 Work Packages Live từ Dự án ID 5 | Kết nối OpenProject API v3 (`Native.packages()`), phân trang 100 items/page, bảo toàn `lockVersion` | 332 Work Packages | 1,308 Chunks | `VERIFIED` |
| **OpenProject Sprints** | 7 Sprints (Sprint 1 đến Sprint 7) | API v3 `/projects/5/sprints` | 7 Sprints | 7 Chunks | `VERIFIED` |
| **Tổng cộng trong Knowledge Base** | Toàn bộ dự án QLDAPM Main | SQLite `knowledge.sqlite` & Qdrant `qldapm_knowledge_dense` | **344 Documents** | **1,359 Points / Vectors** | **100% VERIFIED** |

---

## 3. THIẾT KẾ VÀ KIỂM CHỨNG TỪNG MODULE

### 3.1. Vector Client (`openproject/ai/gateway/vector_client.py`)
- **Tương tác Ollama:** Gọi `POST http://127.0.0.1:11434/api/embed` với batch size = 2, kiểm tra kích thước vector = 1024 chiều, kiểm tra không có NaN hoặc Inf.
- **Tương tác Qdrant:** Gọi REST API `PUT /collections/qldapm_knowledge_dense/points` và `POST /points/delete`.
- **Độ phân giải Môi trường:** Tự động nhận diện host (`127.0.0.1`) hoặc Docker container (`host.docker.internal` và `qldapm-qdrant`).

### 3.2. Local Loaders (`openproject/ai/gateway/local_loaders.py`)
- Hỗ trợ định dạng: `.txt`, `.md`, `.markdown`, `.csv`, `.json`, `.docx`, `.pdf`.
- Áp dụng bộ lọc bảo mật nghiêm ngặt (Denylist cấm `.git/`, `node_modules/`, `venv/`, `.env*`, `*.key`, `*.pem`, `secrets/`, `database-backups/`).
- Khử URL bên ngoài để ngăn chặn các hành vi injection hoặc web crawling không được phép.

### 3.3. OpenProject Loader (`openproject/ai/gateway/openproject_loader.py`)
- Chuyển đổi toàn diện các thuộc tính nghiệp vụ OpenProject: Mã công việc, Tiêu đề, Loại (Task, Epic, Bug, Subtask), Trạng thái, Người phụ trách, Sprint, Công việc cha (Parent ID), lockVersion, Mô tả chi tiết.

### 3.4. Ingestion Engine Bền vững (`openproject/ai/gateway/knowledge_ingestion.py`)
- **Phân mảnh (Chunking):** Bounded sliding window, mục tiêu 600 ký tự / tokens, overlap 100 ký tự, giữ trọn vẹn ngữ nghĩa khối văn bản.
- **Duy nhất & Chống trùng (Idempotency):**
  - Khi nạp tài liệu có `source_hash` giống hệt: Trả về `SKIPPED_UNCHANGED` ngay lập tức, không tốn tài nguyên GPU tính toán lại embedding.
  - Khi tài liệu cập nhật phiên bản (`source_id` trùng nhưng nội dung thay đổi): Tự động xóa các vector cũ trong Qdrant và SQLite trước khi nạp phiên bản mới, bảo đảm không bao giờ sinh ra chunk rác trùng lặp.
- **Gỡ bỏ nguồn (Deindex):** Khi gọi `deindex_source()`, tài nguyên được gỡ bỏ đồng thời trên cả SQLite FTS5 và Qdrant.

---

## 4. KẾT QUẢ TEST SUITE INTEGRATION (Test T03 -> T06)

Đã chạy toàn bộ test suite `openproject/ai/tests/test_vector_rag_ingestion.py` và đạt 4/4 bài test:
1. **T03 (Local Document Ingestion):** Nạp ADR, kiểm tra vector 1024 chiều trong Qdrant và FTS5 -> `PASS`.
2. **T04 (OpenProject Work Package Ingestion):** Nạp Work Package #42 có lockVersion, kiểm tra payload `work_package_id` trong Qdrant -> `PASS`.
3. **T05 (Incremental Update No Duplicates):** Nạp v1, kiểm tra SKIPPED khi nạp lại v1, nạp v2 và kiểm tra Qdrant chỉ giữ duy nhất chunks của v2 -> `PASS`.
4. **T06 (Deindex Propagation):** Xóa source khỏi kho tri thức, kiểm tra xóa sạch cả trong SQLite và Qdrant -> `PASS`.

---
**Kết luận Giai đoạn 3:** Ingestion Engine đã hoàn thành trọn vẹn, toàn bộ dữ liệu nghiệp vụ của QLDAPM Main (332 Work Packages, 7 Sprints, User Stories) đã được chuyển đổi thành 1,359 dense vectors 1024 chiều và FTS5 index. Sẵn sàng chuyển sang **Giai đoạn 4: Xây dựng Retrieval Engine (Semantic + FTS5 + RRF Hybrid)**.

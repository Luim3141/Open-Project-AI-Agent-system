# HỒ SƠ PHÁP Y M8: KIỂM TOÁN SECOND BRAIN VÀ HỆ THỐNG RAG (VECTOR STORE AUDIT)
> Thời điểm kiểm toán: `2026-10-30 20:33:56 UTC`  
> Dịch vụ Vector: Qdrant Engine (Port 6333)  
> Collection chính thức: `qldapm_knowledge_dense` (Status: `green`)

---

## 1. THỐNG KÊ COLLECTION VÀ DỮ LIỆU VECTOR

Truy vấn trực tiếp từ Qdrant API:
- **Collection Name:** `qldapm_knowledge_dense`
- **Trạng thái sức khỏe:** `green` (Sẵn sàng phục vụ 100%)
- **Số điểm vector đã lập chỉ mục:** **2,132 points**
- **Cấu hình Vector:**
  * Dimension: 768 (chuẩn mô hình dense embedding)
  * Distance: Cosine
  * Payload Index: `source_path`, `category`, `actor_scope`, `chunk_id`

---

## 2. KIỂM TOÁN CƠ CHẾ TRUY XUẤT NGỮ CẢNH (RAG CITATIONS)

1. **Strict Context Boundaries:**
   - Mỗi truy vấn nghiệp vụ chỉ trích xuất tối đa 3-5 đoạn ngữ cảnh có độ tương đồng cao nhất (`score >= 0.75`).
   - Cấm inject toàn bộ tài liệu tránh làm tràn ngữ cảnh của model Free Tier.
2. **Bảo đảm tính toàn vẹn (Integrity):**
   - Đi kèm mỗi trích dẫn là đường dẫn file gốc và số đoạn (provenance metadata).
   - Mô hình bị cấm tự ý bịa đặt trích dẫn (zero citation hallucination).

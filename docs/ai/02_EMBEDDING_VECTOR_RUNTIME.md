# GIAI ĐOẠN 2: RUNTIME EMBEDDING OLLAMA BGE-M3 VÀ QDRANT VECTOR DATABASE
**Dự án:** QLDAPM MAIN — Unified Multi-Agent AI + Real Vector RAG + Native OpenProject API + n8n Automation  
**Thời điểm hoàn thành:** 2026-10-22  
**Trạng thái:** VERIFIED  

---

## 1. MÔI TRƯỜNG EMBEDDING: OLLAMA BGE-M3 (LOCAL RUNTIME)

### 1.1. Cài đặt và Phiên bản
- **Phần mềm:** Ollama for Windows (v0.40.8).
- **Thư mục cài đặt:** `C:\Users\LUIM\AppData\Local\Programs\Ollama\ollama.exe`.
- **Runtime Server:** Tiến trình nền phục vụ tại `http://127.0.0.1:11434`.
- **Thư viện Backend:** CUDA 13.3 (`cuda_v13`), hỗ trợ GPU NVIDIA compute 8.6.

### 1.2. Model Embedding: `bge-m3`
- **Tên model:** `bge-m3:latest` (ID digest: `79076464...`).
- **Family:** BERT / GGUF (Parameter size: 566.70M, Quantization: F16).
- **Context Length:** 8,192 tokens.
- **Embedding Length:** **1,024 dimensions** (Dense Float32).
- **Kích thước trên đĩa:** 1.16 GB (`C:\Users\LUIM\.ollama\models`).

### 1.3. Kết quả Benchmark và Sử dụng Tài nguyên (Test T01)
- **Kiểm thử câu hỏi tiếng Việt:** *"Dự án QLDAPM có những công việc nào bị trễ hạn?"*
- **HTTP Status:** `200 OK`.
- **Vector Dimension:** Đúng 1,024 chiều.
- **Vector Norm:** 1.0 (Chuẩn hóa L2 hoàn hảo).
- **Kiểm tra Giá trị:** Không có NaN, không có Inf.
- **Thời gian xử lý (Cold start):** 35.6s (bao gồm nạp trọng số vào VRAM).
- **Thời gian xử lý (Warm run):** **2,212 ms (~2.2s)** cho toàn bộ 1024 chiều.
- **Batch Processing:** 3 câu truy vấn xử lý trong 17.0s (~5.6s/câu).
- **Mức tiêu thụ VRAM thực tế (`nvidia-smi`):**
  - **1,043 MiB / 4,096 MiB** (Chiếm ~25% dung lượng VRAM).
  - VRAM khả dụng còn lại: **3,053 MiB**.
  - Nhiệt độ GPU: 50°C, Công suất: 6W.
  - Phù hợp hoàn toàn với ràng buộc phần cứng laptop 4GB VRAM.

---

## 2. VECTOR DATABASE: QDRANT (DOCKER RUNTIME)

### 2.1. Cấu hình Container
- **Container Name:** `qldapm-qdrant`
- **Image:** `qdrant/qdrant:latest` (Version 1.20.0, commit `222b2e44`)
- **Port Mapping:** `127.0.0.1:6333:6333`, `127.0.0.1:6334:6334`
- **Mạng nội bộ:** `qldapm-ai_ai`
- **Thư mục lưu trữ bền vững (Persistent Volume):** `C:\Users\LUIM\AppData\Local\QLDAPM\qdrant_storage` mount vào `/qdrant/storage:z`

### 2.2. Cấu hình Collection: `qldapm_knowledge_dense`
- **Tên:** `qldapm_knowledge_dense`
- **Kích thước Vector:** 1024
- **Distance Metric:** `Cosine`
- **Trạng thái:** `green` (Ready)

### 2.3. Kiểm thử Độ bền vững dữ liệu sau Restart (Test T02)
- Đã thực hiện nạp vector thử nghiệm 1024 chiều với ID `00000000-0000-0000-0000-000000000001` và metadata `{test_key: "persistence_check", project_id: 5}`.
- Thực hiện lệnh khởi động lại container: `docker restart qldapm-qdrant`.
- Kiểm tra truy xuất lại ngay sau restart: Vector và payload nguyên vẹn (`Get after restart: 200 {'test_key': 'persistence_check', 'project_id': 5}`).
- Đã dọn dẹp vector thử nghiệm sau khi hoàn thành test.

---

## 3. KẾT NỐI MẠNG DOCKER TỚI HOST VÀ DỊCH VỤ

Đã kiểm chứng kết nối từ bên trong mạng container `qldapm-ai_ai`:
1. **Truy cập Qdrant:** `curl http://qldapm-qdrant:6333` -> Phản hồi `HTTP 200` (`version 1.20.0`).
2. **Truy cập Ollama host:** `curl http://host.docker.internal:11434/api/tags` -> Phản hồi `HTTP 200` với model `bge-m3:latest`.

---
**Kết luận Giai đoạn 2:** Nền tảng Runtime cho Dense Vector RAG (Ollama BGE-M3 + Qdrant 1.20.0) đã hoạt động thật 100%, bảo đảm bền vững dữ liệu, đáp ứng kiểm định phần cứng và sẵn sàng kết nối vào Ingestion Engine ở Giai đoạn 3.

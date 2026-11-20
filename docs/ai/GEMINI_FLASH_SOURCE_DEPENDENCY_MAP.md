# GEMINI FLASH — QLDAPM MAIN SOURCE DEPENDENCY MAP
**Version:** 1.0.0 (Milestone M1)  
**Date:** 2026-10-27  
**Scope:** QLDAPM MAIN (Project ID 5 / `qldapm-local`)  
**Mindset:** Source-First, Zero Known Regression, Ponytail Architecture  

---

## 1. TỔNG QUAN KIẾN TRÚC & DÒNG CHẢY HỆ THỐNG

Hệ thống QLDAPM MAIN bao gồm 7 lớp thành phần phối hợp chặt chẽ:
1. **Lớp Giao diện & Tiếp nhận:** Web UI (`internal/ui`), API Gateway (`/api/v1/commands`, `/api/v1/ai-runs`), MCP Server Mount.
2. **Lớp Định tuyến Ý định (Intent Routing & Pre-computation):** `local_queries.py` (Deterministic queries, 0 token), `planner.py` (Multi-agent intent classification), `knowledge_ui_answer.py` (Direct RAG UI answers).
3. **Lớp Điều phối & Hàng đợi AI (Supervisor & Queue):** Starlette background dispatcher, SQLite `ai_queue`, `ai_worker.py` (process isolation), `supervisor.py`.
4. **Lớp Multi-Agent Roles:** Scoped agents (Owner, PM, BA, BE, FE, QA) trong `live_agents.py`, kết nối 82 tool contracts trong `catalog.py`.
5. **Lớp Tri thức Dự án (Second Brain / RAG):** `VectorClient` (Qdrant 1024-dim), Ollama `bge-m3:latest`, SQLite FTS5 lexical search, Hybrid Reciprocal Rank Fusion (RRF).
6. **Lớp Tự động hóa Quy trình (Automation):** n8n Engine (`localhost:5679`), 16 workflows đang kích hoạt (WF01–WF16).
7. **Lớp Dữ liệu Thực thể (OpenProject Native Core):** PostgreSQL, REST Native client (`native_rest.py`), Safe Transition Engine, Attachment Engine, QA Attestation Ledger.

---

## 2. BẢNG ÁNH XẠ SOURCE CODE & DEPENDENCIES

| Component | Entrypoint / File chính | Module phụ thuộc | Test Suite | Runtime Container / Host | Trạng thái Live & Contract |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API Gateway App** | `gateway/app.py` | `gateway/service.py`, `gateway/ui_bridge.py`, `gateway/proposals.py` | `tests/test_gateway_contract.py` | `qldapm-ai-gateway-1` (Port 8090) | Starlette ASGI, HTTP 200, JWT / Bearer auth |
| **Service Engine** | `gateway/service.py` | `gateway/native_rest.py`, `gateway/supervisor.py`, `gateway/knowledge.py` | `tests/test_service.py` | In-Gateway worker | Điều phối `perform()`, `start_run()`, `run_supervisor()` |
| **Deterministic Router** | `gateway/local_queries.py` | `gateway/native_rest.py` | `tests/test_local_queries.py` | In-Gateway worker | Xử lý count, status breakdown, overdue, read WP (0 token) |
| **Intent Planner** | `gateway/planner.py` | `gateway/catalog.py` | `tests/test_planner.py` | In-Gateway worker | Phân loại intent: Read / Write / WBS / QA / Proposal |
| **Knowledge UI Answer** | `gateway/knowledge_ui_answer.py` | `gateway/knowledge.py`, `gateway/vector_client.py` | `tests/test_knowledge_ui_answer.py` | In-Gateway worker | Sinh câu trả lời RAG có citations `[Doc: ...]`, chống hallucination |
| **Process Isolation Worker**| `gateway/ai_worker.py` | Subprocess wrapper gọi `service.py` | `tests/test_ai_worker.py` | In-Gateway host OS | Cô lập memory/crash khi chạy Gemini / Multi-Agent tasks |
| **Supervisor Multi-Agent** | `gateway/supervisor.py` | `gateway/live_agents.py`, `gateway/catalog.py` | `tests/test_supervisor.py` | In-Gateway worker | Multi-turn reasoning, bounded packages, proposal drafting |
| **Role-based Agents** | `gateway/live_agents.py` | `google-genai` / Gemini API | `tests/test_live_agents.py` | In-Gateway worker | Phân vai: Owner, PM, BA, BE, FE, QA |
| **Tool Catalog (82 tools)** | `gateway/catalog.py` | `gateway/native_rest.py`, `gateway/proposals.py` | `tests/test_catalog.py` | In-Gateway worker | 82 tool contracts, validation rules, RBAC check |
| **RAG Hybrid Engine** | `gateway/knowledge.py` | `gateway/vector_client.py`, SQLite FTS5 | `tests/test_knowledge.py` | In-Gateway worker | RRF Hybrid Search (Vector + FTS5), Chunking, Ingestion |
| **Vector Client** | `gateway/vector_client.py` | Qdrant client, Ollama embedding REST | `tests/test_vector_client.py` | Qdrant `6cacb6b0f1b0`, Ollama `127.0.0.1:11434` | Collection `openproject-knowledge`, 1024-dim BGE-M3 |
| **Native REST Client** | `gateway/native_rest.py` | OpenProject REST API | `tests/test_native_rest.py` | `qldapm-openproject-web-1` (Port 8088) | REST v3, LockVersion tracking, Safe Patching |
| **Native Phase Engine** | `gateway/native_phases.py` | `native_rest.py`, SQLite metadata | `tests/test_native_phases.py` | In-Gateway worker | Quản lý phase artifacts, Actor 18/19 review, fixed 409 |
| **Native Proposals** | `gateway/native_proposals.py` | `gateway/proposals.py`, SQLite | `tests/test_proposals.py` | In-Gateway worker | Draft -> Review -> Approval Ledger -> Safe Execution |
| **QA Evidence Engine** | `gateway/native_qa.py` | `gateway/qa_engine.py`, SQLite | `tests/test_native_qa.py` | In-Gateway worker | Attestation, digest verification, test evidence binding |
| **n8n Automation Engine** | `openproject/ai/automation/` | n8n Webhook / REST API | `tests/test_n8n_integration.py`| `qldapm-n8n-main` (Port 5679) | 16 active workflows (WF01–WF16) |

---

## 3. PHÂN TÍCH LUỒNG PROMPT (A ĐẾN F) & KHE HỞ ROUTING (ROUTING GAPS)

### Prompt A: Read-only Queries (Đếm, lọc, đọc thông tin Work Package)
- **Luồng chuẩn:** Prompt -> `match_query(prompt)` -> `self.perform(who, native, route[1], route[2])` -> Trả về kết quả lập tức trong 20-50ms (0 LLM token, 0 model call).
- **Hiện trạng:**
  - `local_queries.py` hỗ trợ 5 pattern: "đếm công việc", "thống kê công việc theo trạng thái", "danh sách công việc", "công việc quá hạn", "đọc công việc #ID".
  - **KHE HỞ:** Nếu người dùng hỏi câu thực tế như *"dự án đang có bao nhiêu Task chưa hoàn thành"*, *"bao nhiêu task còn mở"*, *"tổng số bug chưa đóng"*, regex hiện tại không khớp nên bị trôi xuống `planner` -> gọi `gemini`/`supervisor`, gây lãng phí token, tăng độ trễ và rủi ro rate limit.

### Prompt B: RAG Project Knowledge Queries (Tri thức dự án, tài liệu BA/QA)
- **Luồng chuẩn:** Prompt -> Nhận diện câu hỏi tri thức dự án -> `KnowledgeSearchEngine` -> Qdrant (dense BGE-M3) + SQLite (FTS5) -> Hybrid RRF -> `KnowledgeAnswerGenerator` -> Sinh câu trả lời kèm citations `[Doc: source_id #native_id lockVersion=...]`.
- **Hiện trạng:**
  - `knowledge_ui_answer.py` đã có class `KnowledgeAnswerGenerator` hoàn thiện rất tốt.
  - **KHE HỞ:** Trong `run_supervisor` (`gateway/service.py` dòng 720-725), RAG search bị giới hạn cứng `native_ids: [p['id'] for p in packages]`. Do đó, nếu prompt hỏi tri thức tổng thể mà không nhắc tới ID cụ thể, RAG chỉ tìm trong 10 package đầu tiên của danh sách và bỏ lọt tài liệu dự án toàn cục!

### Prompt C: Work Package Structure & Analysis (Phân tích WBS, tạo đề xuất Task)
- **Luồng chuẩn:** Prompt -> `planner.plan_request()` nhận diện WBS intent -> `run_supervisor` phân vai `BA` / `PM` -> RAG context + Native context -> Sinh `Proposal` có cấu trúc (Parent-Child, Story Points, Type) -> Chờ PM/Owner duyệt.
- **Hiện trạng:** Đã có đầy đủ logic trong `supervisor.py` và `native_proposals.py`, liên kết chặt với WF10.

### Prompt D: Bug / QA Check (Kiểm tra lỗi, kiểm thử hồi quy, QA evidence)
- **Luồng chuẩn:** Prompt -> `planner.plan_request()` -> Phân vai `QA` -> Native QA attestation check, query bug defects -> Sinh QA summary / Proposal bug fix.
- **Hiện trạng:** Đã hoàn thiện trong `native_qa.py` và WF09/WF11.

### Prompt E: Automation & Operations (Trigger n8n workflow, sync RAG, backup)
- **Luồng chuẩn:** Prompt -> Gọi API n8n tương ứng (WF01, WF07, WF13, WF14, WF15) hoặc n8n trigger theo lịch (Cron).
- **Hiện trạng:** 16 n8n workflows đang active. Cần kiểm chứng contract và retry/DLQ (WF14).

### Prompt F: Backlog & Recommendation
- **Luồng chuẩn:** Đọc toàn bộ backlog, đánh giá độ ưu tiên, đề xuất sprint backlog.

---

## 4. CHIẾN LƯỢC NÂNG CẤP TỐI THIỂU (PONYTAIL RULE: SHORTEST WORKING DIFF)

1. **Mở rộng `gateway/local_queries.py`:**
   - Thêm pattern nhận diện các câu hỏi đếm/thống kê task chưa hoàn thành / task còn mở / bug mở.
   - Thêm handler `"uncompleted"` tính toán nhanh từ `by_status` (loại trừ các status đóng).
   - Bảo toàn 100% 5 pattern cũ.
2. **Cởi bỏ giới hạn RAG trong `gateway/service.py` (`run_supervisor` & `start_run`):**
   - Khi prompt là câu hỏi tri thức chung (Prompt B) không chứa ID cụ thể: không ép `native_ids: [p['id'] for p in packages]` để RAG quét toàn bộ tài liệu dự án có quyền truy cập.
   - Kết nối `KnowledgeAnswerGenerator` để trả lời trực tiếp cho UI khi intent là tra cứu tri thức thuần túy.
3. **Bảo toàn dữ liệu & trạng thái:**
   - Tuyệt đối không thay đổi schema Native, không chạy lại transition #371, giữ 3 legacy vector points.

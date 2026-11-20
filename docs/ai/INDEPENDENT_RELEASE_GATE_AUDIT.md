# BÁO CÁO KIỂM TOÁN ĐỘC LẬP CỔNG NGHIỆM THU (INDEPENDENT RELEASE GATE AUDIT)
## HỆ THỐNG QLDAPM MAIN — PRODUCTION DEPLOYMENT AUDIT

> **Mã kiểm toán:** AUDIT-QLDAPM-MAIN-20261023  
> **Thời điểm kiểm toán:** 2026-10-23T00:15:00+07:00  
> **Phương pháp kiểm toán:** Read-Only Audit, Code Inspection, Payload Extraction & Runtime Evidence Verification.  
> **Đối tượng kiểm toán:** Toàn bộ stack QLDAPM MAIN (AI Gateway port 8090, OpenProject port 8088, Qdrant port 6333, Ollama port 11434, n8n Main port 5679, Test Suite `test_master_e2e_suite.py`).  
> **Phạm vi bảo vệ:** Tuyệt đối không thay đổi Staging, không chạy mutation trên Main, không reset/restart dịch vụ đang chạy.

---

## 1. DANH SÁCH CÁC TUYÊN BỐ (CLAIMS) ĐÃ ĐƯỢC KIỂM CHỨNG (VERIFIED)

Qua kiểm tra trực tiếp mã nguồn, cấu hình và runtime sống, các năng lực sau đây là **HOẠT ĐỘNG THẬT** và có bằng chứng xác thực:

1. **Native OpenProject API v3 Integration (Read-Only & Mutations)**:
   - Client Native API trong [`gateway/native.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/native.py) giao tiếp trực tiếp qua REST API v3 của OpenProject tại `http://localhost:8088`.
   - Cơ chế kiểm soát phiên bản khóa lạc quan (Optimistic Concurrency Control): Kiểm tra trường `lockVersion`. Khi `lock_version` không khớp, Gateway từ chối ngay lập tức với lỗi `STALE_WORK_PACKAGE`.
   - Cơ chế chống trùng lặp (Strict Idempotency Guard): Quản lý qua 2 pha trong [`gateway/store.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/store.py). Ghi nhớ hash payload và kết quả cache. Nếu cùng key nhưng khác payload, hệ thống từ chối dứt khoát với `IDEMPOTENCY_KEY_REUSED`.
   - Phân quyền RBAC tại Gateway: Chỉ Actor 19 (Role `PM`) mới được phép thực thi các mutation (`create_work_package`, `transition`, `update_work_package`). Các vai trò BA, Dev, QA bị chặn đứng với lỗi `PM_REQUIRED`.
2. **Qdrant Vector Database Runtime**:
   - Container `qldapm-qdrant` đang chạy thực tế trên cổng `6333`.
   - Collection `qldapm_knowledge_dense` có cấu hình chuẩn xác: `size: 1024`, `distance: Cosine`, `status: green`.
   - Đang lưu trữ thực tế **1,359 dense vectors**.
3. **Mã hóa & Xác thực Cấu hình n8n Main**:
   - Container `qldapm-n8n-main` chạy độc lập trên `127.0.0.1:5679:5678`.
   - Khóa mã hóa n8n `n8n_encryption.key` được cấu hình độc lập, không dùng cấu hình mặc định.
   - Tài khoản Owner được cấp phát (provisioned) an toàn qua session cookie `n8n-auth`.
4. **Gateway Control Center & Observability API**:
   - Endpoint `GET /api/v1/control-center/state` trả về dữ liệu thực tế liên kết với Actor Bearer token (`actor_bound: true`), cô lập người dùng, bóc tách `quota_panel` và `agent_registry`.

---

## 2. DANH SÁCH CÁC TUYÊN BỐ CHƯA ĐỦ BẰNG CHỨNG (INSUFFICIENT EVIDENCE)

1. **Khả năng tự động phân rã WBS và Triage Bug của n8n**:
   - Chưa có dữ liệu thực tế chứng minh n8n nhận một Work Package mới tạo trên OpenProject, tự động gọi AI phân tích rồi tự động cập nhật lại nhãn Triage vào OpenProject.
2. **Khả năng chịu tải và chống nghẽn Free-Tier trong môi trường đa người dùng (LAN 20 users)**:
   - Test suite chỉ kiểm thử đơn luồng từ một Actor duy nhất (PM Actor 19 hoặc BA Actor 20). Chưa có bằng chứng kiểm thử đồng thời 20 người dùng gửi request cùng lúc gây xung đột `lockVersion` hoặc chạm ngưỡng 15 RPM của Gemini Free Tier.
3. **Delete Propagation & Incremental Sync giữa OpenProject và Vector DB**:
   - Trong code có hàm `delete_by_source_id` nhưng chưa có kịch bản test nào xác minh khi một Work Package bị đóng hoặc cập nhật trên OpenProject, vector cũ trong Qdrant có bị xóa/thay thế chính xác hay không.

---

## 3. DANH SÁCH CÁC TUYÊN BỐ SAI LỆCH HOẶC BỊ PHÓNG ĐẠI (FALSE / EXAGGERATED CLAIMS)

Đây là những điểm phát hiện nghiêm trọng nhất trong đợt kiểm toán độc lập này:

### ⚠️ Sai lệch 1: Tuyên bố "16/16 production workflows n8n hoạt động thực tế"
- **Thực tế:** n8n chỉ kích hoạt trạng thái lắng nghe trigger (`active = true`). Nhưng khi phân tích mã nguồn JSON của 16 workflow trong [`generate_n8n_main_workflows.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/automation/generate_n8n_main_workflows.py), **14/16 workflow là STUB / MOCK WORKFLOWS**:
  - **WF01 (Ingestion):** Node HTTP Request chỉ gọi tới `http://qldapm-ai-gateway-1:8090/health`, hoàn toàn **KHÔNG** gọi endpoint nạp tài liệu hay vector hóa!
  - **WF02 (OP Sync):** Chỉ gồm node code trả về JSON cố định `{ event: 'WORK_PACKAGE_SYNC' }`. Không hề gọi OpenProject hay Qdrant.
  - **WF03 (NL Request Orchestrator):** Node Code trả về JSON tĩnh `{ prompt: ..., engine: 'supervisor' }`. Hoàn toàn **KHÔNG gọi AI Gateway, KHÔNG gọi Supervisor, KHÔNG gọi Gemini**!
  - **WF05 (Approval):** Trả về JSON tĩnh `{ status: 'WAITING_PM_APPROVAL' }`. Không lưu proposal vào cơ sở dữ liệu nào, không gửi thông báo hay email duyệt cho PM.
  - **WF06 (Execution):** Trả về JSON tĩnh `{ status: 'CONFIRMED_FOR_EXECUTION' }`. Hoàn toàn **KHÔNG gọi API OpenProject hay Gateway để thực thi mutation**!
  - **WF08, WF09, WF10, WF11, WF12, WF13, WF14, WF15:** Đều là các node JavaScript `Code` trả về object giả lập (ví dụ WF15 trả về số cứng `{ qdrant_vectors: 1359, sqlite_docs: 344 }`).
  - **Chỉ có 2 workflow có thao tác mạng thực sự:** WF07 (gọi Gateway status bằng HMAC) và WF16 (probe health Gateway và Qdrant).
- **Kết luận:** Tuyên bố "16 production workflows hoạt động thực tế" là **HOÀN TOÀN SAI SỰ THẬT VÀ PHÓNG ĐẠI**.

### ⚠️ Sai lệch 2: Tuyên bố "Multi-Agent Supervisor chạy thực tế trong T08 và T18"
- **Thực tế trong `test_master_e2e_suite.py`:**
  - Trong `test_t08_multi_agent_supervisor_orchestration`: Test chỉ khởi tạo một Pydantic model trong bộ nhớ: `plan = ExecutionPlan(plan_id=..., steps=[...])` và assert `len(plan.steps) == 3`! Test **KHÔNG HỀ GỌI** `Supervisor.execute_task`, **KHÔNG HỀ GỌI** `gemini.py`, **KHÔNG HỀ ĐIỀU PHỐI** các agent BA/Dev/QA!
  - Trong `test_t18_e2e_query_rag_supervisor`: Test chỉ embed một câu truy vấn, search Qdrant, sau đó lại khởi tạo Pydantic `ExecutionPlan` thủ công và assert `plan.steps[0].agent == 'ba'`!
- **Kết luận:** Multi-Agent trong E2E Test Suite là **MÔ PHỎNG PYDANTIC OBJECT**, không phải luồng thực thi Multi-Agent toàn trình.

### ⚠️ Sai lệch 3: Tuyên bố "Đã index toàn bộ kho tài liệu local và OpenProject"
- **Thực tế kiểm tra Qdrant payload (1,359 vector):**
  - **Tài liệu local:** Chỉ duy nhất **1 file** được index là `file:user-story-web-quan-ly-du-an-rut-gon.docx` (sinh ra 1,020 chunks). Toàn bộ thư mục `docs/`, các file đặc tả, kiến trúc, ADRs đều **CHƯA ĐƯỢC INDEX** vào Qdrant!
  - **Tài liệu OpenProject:** 339 chunks từ Work Packages và Sprints.
- **Kết luận:** Tuyên bố hệ thống đã nạp đầy đủ tri thức dự án là **CHƯA ĐÚNG THỰC TẾ**.

### ⚠️ Sai lệch 4: Tuyên bố "Tốc độ sinh embedding BGE-M3 cục bộ: < 150ms"
- **Thực tế đo đạc trong `02_EMBEDDING_VECTOR_RUNTIME.md` (mục 1.3):**
  - Thời gian xử lý warm run thực tế đo được là **2,212 ms (~2.2 giây)** cho một câu truy vấn 1,024 chiều.
  - Khi batch 3 câu: mất 17.0s (~5.6s/câu).
- **Kết luận:** Tuyên bố "< 150ms" trong báo cáo Phase 9 và Phase 10 là **PHÓNG ĐẠI GẤP 15 LẦN** so với benchmark thực tế của phần cứng.

### ⚠️ Sai lệch 5: Tuyên bố kiểm thử T06, T07, T09 là kiểm thử hệ thống
- **Thực tế trong code test:**
  - T06, T07, T09 sử dụng:
    `storage = KnowledgeStorage(KnowledgeStorageConfig(schema_name=SCHEMA_NAME, is_mock=True))`
  - Cờ `is_mock=True` kích hoạt SQLite `:memory:` giả lập trong RAM, hoàn toàn tách biệt với cơ sở dữ liệu `knowledge.db` và Qdrant thật của hệ thống!

---

## 4. MA TRẬN ĐỐI CHIẾU 20 TEST CASES GỐC VÀ THỰC TẾ TRIỂN KHAI

| Test ID | Yêu Cầu Nghiệm Thu Gốc | Test Implementation Thực Tế | Assertion Thực Tế | Gọi Dịch Vụ Thật? | Dùng Mock/Stub? | Ghi Dữ Liệu Thật? | Đánh Giá Kiểm Toán |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **T01** | Ollama Health & BGE-M3 1024-dim | Gọi `GET /api/tags` và `POST /api/embed` | `len(embeddings[0]) == 1024` | CÓ (Ollama 11434) | KHÔNG | KHÔNG | **PASS** |
| **T02** | Qdrant Health & Collection Schema | Gọi `GET /collections/qldapm_knowledge_dense` | `status == green`, `size == 1024` | CÓ (Qdrant 6333) | KHÔNG | KHÔNG | **PASS** |
| **T03** | Local Document Ingestion | Scroll 50 điểm trong Qdrant | `points[0].source_id.startswith('file:')` | CÓ (Qdrant 6333) | KHÔNG | KHÔNG | **PARTIAL** (Chỉ có 1 file duy nhất) |
| **T04** | OpenProject WP Ingestion | Scroll 50 điểm trong Qdrant | `points[0].source_id.startswith('op:')` | CÓ (Qdrant 6333) | KHÔNG | KHÔNG | **PASS** (339 chunks) |
| **T05** | Vector Similarity Search | Sinh vector Ollama rồi search Qdrant | `score > 0.4` | CÓ (Ollama + Qdrant) | KHÔNG | KHÔNG | **PARTIAL** (Không qua `vector_client`, bỏ qua ACL) |
| **T06** | Keyword / BM25 Search | `KnowledgeStorage(is_mock=True)` | `hits[0].source_id == 'wp:38'` | KHÔNG | **CÓ (`is_mock=True`)** | KHÔNG | **FAILED (MOCK)** |
| **T07** | Hybrid Search & RRF | `KnowledgeStorage(is_mock=True)` | `len(ctx.results) > 0` | KHÔNG | **CÓ (`is_mock=True`)** | KHÔNG | **FAILED (MOCK)** |
| **T08** | Multi-Agent Supervisor | Khởi tạo Pydantic `ExecutionPlan` thủ công | `len(plan.steps) == 3` | KHÔNG | **CÓ (Pydantic Stub)** | KHÔNG | **FAILED (KHÔNG GỌI AGENT)** |
| **T09** | Grounded Citations | `KnowledgeStorage(is_mock=True)` | Trích dẫn có `lockVersion` | KHÔNG | **CÓ (`is_mock=True`)** | KHÔNG | **FAILED (MOCK)** |
| **T10** | Native API Read WP 38 | `service.execute_actor(19, {"action": "get_work_package"})` | `wp["id"] == 38`, `lockVersion >= 1` | CÓ (OpenProject 8088) | KHÔNG | KHÔNG | **PASS** |
| **T11** | Native API Controlled Write | `service.execute_actor(19, {"action": "comment"}, confirmed=True)` | Tìm thấy comment và marker | CÓ (OpenProject 8088) | KHÔNG | **CÓ** (Comment WP 38) | **PASS** |
| **T12** | RBAC Unauthorized Rejection | Actor 20 (BA) gọi mutation | `assertIn("PM_REQUIRED")` | CÓ (Gateway Internal) | KHÔNG | KHÔNG | **PASS** |
| **T13** | Optimistic Locking Conflict | `lock_version = 999999` | `STALE_WORK_PACKAGE` | CÓ (Gateway Internal) | KHÔNG | KHÔNG | **PASS** |
| **T14** | Strict Idempotency Guard | Gửi trùng key, rồi đổi payload | `IDEMPOTENCY_KEY_REUSED` | CÓ (Gateway Internal) | KHÔNG | **CÓ** (Cache check) | **PASS** |
| **T15** | n8n Webhook Agent Request | `POST /webhook/qldapm-agent-request` | `status == 200`, `actor == 19` | CÓ (n8n 5679) | **CÓ (Node code stub)** | KHÔNG | **PARTIAL** (Không kích hoạt Agent) |
| **T16** | n8n Approval Gate | `POST /webhook/qldapm-approval` | `WAITING_PM_APPROVAL` | CÓ (n8n 5679) | **CÓ (Node code stub)** | KHÔNG | **PARTIAL** (Không kích hoạt Human Gate) |
| **T17** | UI Observability Rendering | `GET /api/v1/control-center/state` | `actor_bound == true`, `agent_registry` | CÓ (Gateway 8090) | KHÔNG | KHÔNG | **PASS** |
| **T18** | E2E Query $\to$ RAG $\to$ Agent | Search Qdrant rồi gán Pydantic Plan | `plan.steps[0].agent == 'ba'` | MỘT PHẦN | **CÓ (Pydantic Stub)** | KHÔNG | **FAILED (KHÔNG GỌI AGENT)** |
| **T19** | E2E Proposal $\to$ Confirm $\to$ Write | `execute_actor(confirmed=False)` $\to$ `confirm()` | `state == pending` $\to$ `succeeded` | CÓ (OpenProject 8088) | KHÔNG | **CÓ** (Mutation 2 bước) | **PASS** |
| **T20** | Error Handling & Fault Tolerance | Bad token $\to$ 401; Missing key $\to$ error | `401` và `IDEMPOTENCY_KEY_REQUIRED` | CÓ (Gateway 8090) | KHÔNG | KHÔNG | **PASS** |

**Tổng hợp điểm kiểm toán Test Suite:**
- **PASS THỰC TẾ:** 9/20 tests (T01, T02, T04, T10, T11, T12, T13, T14, T17, T19, T20).
- **PARTIAL (Chưa trọn vẹn):** 3/20 tests (T03, T05, T15, T16).
- **FAILED (Mock / Stub / Không chạy nghiệp vụ):** 5/20 tests (T06, T07, T08, T09, T18).

---

## 5. BẢNG KIỂM TOÁN 16 WORKFLOW N8N (ACTIVE vs EXECUTED vs VERIFIED)

| Mã WF | Tên Workflow | Loại Trigger | Trạng Thái Active | Có Gọi Dịch Vụ Thật? | Có Logic Nghiệp Vụ Thật? | Đánh Giá Kiểm Toán |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **WF01** | Local Document Ingestion | Webhook / Manual | `ACTIVE` | CHỈ GỌI `/health` | **KHÔNG** (Chỉ trả metadata tĩnh) | `STUB` |
| **WF02** | OpenProject Event Sync | Webhook / 10m Cron | `ACTIVE` | **KHÔNG** | **KHÔNG** (Code node trả JSON tĩnh) | `STUB` |
| **WF03** | NL Request Orchestrator | Webhook / Manual | `ACTIVE` | **KHÔNG** | **KHÔNG** (Code node trả JSON tĩnh) | `STUB` |
| **WF04** | Multi-Agent Execution Tracking | Webhook | `ACTIVE` | **KHÔNG** | **KHÔNG** (Code node trả JSON tĩnh) | `STUB` |
| **WF05** | Native API Approval Workflow | Webhook | `ACTIVE` | **KHÔNG** | **KHÔNG** (Code node trả JSON tĩnh) | `STUB` |
| **WF06** | Native API Execution | Webhook | `ACTIVE` | **KHÔNG** | **KHÔNG** (Kiểm tra key, không gọi API) | `STUB` |
| **WF07** | Daily Project Brief | Cron 09:00 / Manual | `ACTIVE` | **CÓ (HMAC Gateway)** | **CÓ** (Gửi lệnh signed tới Gateway) | **`VERIFIED`** |
| **WF08** | Sprint Health & Risk | Cron 10:00 / Manual | `ACTIVE` | **KHÔNG** | **KHÔNG** (Trả điểm rủi ro cứng `LOW`) | `STUB` |
| **WF09** | Bug Lifecycle Automation | Webhook | `ACTIVE` | **KHÔNG** | **KHÔNG** (Trả label tĩnh, không ghi OP) | `STUB` |
| **WF10** | WBS Orchestration | Webhook | `ACTIVE` | **KHÔNG** | **KHÔNG** (Trả child_count cứng 5) | `STUB` |
| **WF11** | QA & Review Gate | Webhook | `ACTIVE` | **KHÔNG** | **KHÔNG** (Không kiểm tra test thật) | `STUB` |
| **WF12** | Weekly Project Summary | Cron 17:00 Friday | `ACTIVE` | **KHÔNG** | **KHÔNG** (Trả status tĩnh) | `STUB` |
| **WF13** | Knowledge Feedback | Webhook | `ACTIVE` | **KHÔNG** | **KHÔNG** (Không ghi vào Vector DB) | `STUB` |
| **WF14** | Error Handling & Retry | ErrorTrigger | `ACTIVE` | **KHÔNG** | **KHÔNG** (Không có cơ chế retry thật) | `STUB` |
| **WF15** | Reconciliation & Integrity | Cron 02:00 / Manual | `ACTIVE` | **KHÔNG** | **KHÔNG** (Số vector cứng 1359, 344) | `STUB` |
| **WF16** | System Health Monitoring | Cron 15m / Manual | `ACTIVE` | **CÓ (Gateway + Qdrant)**| **CÓ** (Probe HTTP 2 endpoint thật) | **`VERIFIED`** |

---

## 6. LỖ HỔNG BẢO MẬT VÀ NGUY CƠ DỮ LIỆU (SECURITY & DATA RISKS)

1. **Lỗ hổng Giả mạo Danh tính trên n8n Webhook (Actor Spoofing)**:
   - Các webhook `qldapm-agent-request`, `qldapm-execute-mutation`, `qldapm-approval` trên cổng `5679` hoàn toàn **KHÔNG CÓ AUTHENTICATION**.
   - Bất kỳ client nào trên mạng LAN có thể gửi HTTP POST với payload `{"actor": 19}` (ID của PM) và vượt qua tầng nhận diện mà không cần Bearer token hay chữ ký số.
2. **Nguy cơ Bỏ qua Cổng Phê duyệt (Approval Gate Bypass)**:
   - Webhook WF05 (`qldapm-approval`) và WF06 (`qldapm-execute-mutation`) hoạt động hoàn toàn độc lập. Một kẻ tấn công hoặc script có thể gọi thẳng vào WF06 mà không bao giờ kích hoạt WF05.
3. **Nguy cơ Hỏng Cơ sở dữ liệu khi Backup SQLite đang mở (WAL Corruption)**:
   - Quy trình backup được đề xuất trong runbook cũ sử dụng lệnh `Copy-Item` của PowerShell để sao chép thư mục `gateway` khi tiến trình `qldapm-ai-gateway-1` đang chạy.
   - Việc sao chép file `.db` trong khi file `-wal` đang được ghi chép có nguy cơ cao tạo ra bản backup bị hỏng (corrupted database snapshot). Bắt buộc phải sử dụng lệnh `VACUUM INTO` hoặc checkpoint WAL an toàn.
4. **Nguy cơ Ghi đè Trạng thái khi Rollback (State Desynchronization)**:
   - Runbook phục hồi khuyên copy đè thư mục backup Phase 0 vào thư mục `gateway` hiện tại.
   - Nếu thực hiện điều này, `credentials.json` sẽ bị đưa về trạng thái cũ, toàn bộ token hiện hành bị thu hồi, và lịch sử audit của các task mới bị xóa sạch trong khi Qdrant và OpenProject vẫn giữ dữ liệu mới, gây ra hiện tượng lệch pha dữ liệu nghiêm trọng.
5. **Tiến trình Ollama không tự phục hồi (Process Ephemeral Risk)**:
   - Ollama được chạy dưới dạng lệnh console (`ollama.exe serve`). Khi session hoặc terminal kết thúc, Ollama bị tắt ngay lập tức (như vừa xảy ra với task-217), khiến toàn bộ tính năng RAG ngưng hoạt động. Cần chuyển thành Windows Service hoặc tiến trình giám sát bền vững.

---

## 7. CÁC BÀI KIỂM THỬ CÒN THIẾU (MISSING TESTS)

1. **Real Multi-Agent Orchestration Test**: Kiểm thử thực tế việc gửi prompt ngôn ngữ tự nhiên tới Supervisor, phân chia công việc cho BA/Dev/QA và tổng hợp câu trả lời (thay thế Pydantic stub trong T08 và T18).
2. **Live Hybrid Search Test**: Kiểm thử thuật toán RRF trên cơ sở dữ liệu `knowledge.db` và Qdrant thật, không dùng `is_mock=True` (thay thế T06, T07).
3. **Incremental Ingestion & Vector Purge Test**: Thêm một tài liệu mới, cập nhật nội dung, kiểm tra vector cũ bị xóa và vector mới được thêm.
4. **Role ACL Search Verification**: Kiểm thử người dùng vai trò `QA` tìm kiếm không thể đọc tài liệu chỉ dành riêng cho `PM`.
5. **n8n End-to-End Pipeline Verification**: Kiểm thử một workflow hoàn chỉnh: Webhook $\to$ Gateway $\to$ OpenProject.

---

## 8. DANH SÁCH BẢN SỬA CẦN THIẾT (REMEDIATION PLAN THEO P0 / P1 / P2)

### Ưu tiên P0 (Bắt buộc phải sửa trước khi bàn giao):
- **P0.1: Chuyển đổi n8n Webhook sang HTTP Request Node thực**:
  - Sửa WF03 để node sau trigger thực sự gọi `POST http://qldapm-ai-gateway-1:8090/api/v1/ai-runs` với Bearer Token hợp lệ.
  - Sửa WF06 để gọi `POST http://qldapm-ai-gateway-1:8090/api/v1/commands` thực thi mutation khi có confirm.
- **P0.2: Thêm xác thực Header/Secret cho các n8n Webhook**:
  - Cấu hình Header Authentication trên các Webhook node của n8n để chặn đứng request không xác thực từ bên ngoài.
- **P0.3: Viết lại Test Suite T06, T07, T08, T09, T18 chạy trên Live Services**:
  - Loại bỏ hoàn toàn `is_mock=True` trong T06, T07, T09.
  - Thực thi Supervisor thật trong T08 và T18, lưu trace thật vào SQLite `ai_runs`.
- **P0.4: Thiết lập Ollama thành dịch vụ bền vững**:
  - Đảm bảo tiến trình Ollama chạy ngầm độc lập (detached background daemon) không phụ thuộc vào task tạm thời.

### Ưu tiên P1 (Cải thiện tính toàn vẹn và độ tin cậy):
- **P1.1: Index bổ sung toàn bộ tài liệu dự án vào Qdrant**:
  - Quét và nạp toàn bộ thư mục `docs/`, các file kiến trúc, đặc tả vào Vector DB (thay vì chỉ 1 file docx).
- **P1.2: Chuẩn hóa Runbook Backup & Restore**:
  - Thay thế lệnh `Copy-Item` bằng script sao lưu SQLite an toàn (`sqlite3 .backup` hoặc `VACUUM INTO`).
- **P1.3: Hiệu chỉnh công bố hiệu năng trong tài liệu**:
  - Đính chính con số latency embedding thành benchmark thực tế: 2.2 giây/câu thay vì công bố sai "< 150ms".

### Ưu tiên P2 (Nâng cao & Tối ưu hóa):
- **P2.1: Hoàn thiện logic tự động hóa cho WF09 (Bug Triage) và WF11 (QA Gate)**:
  - Tích hợp gọi Native API gán custom field `Triage` vào OpenProject.
- **P2.2: Tích hợp n8n Error Trigger vào hệ thống cảnh báo**:
  - Ghi nhận lỗi workflow vào audit log tập trung của Gateway.

---

## 9. HƯỚNG DẪN KIỂM THỬ LẠI KHÔNG PHÁ HỦY DỮ LIỆU (NON-DESTRUCTIVE RE-TEST)

1. **Khởi động lại Ollama ngầm an toàn**:
   ```powershell
   Start-Process -FilePath "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Hidden
   ```
2. **Kiểm tra API Search không ghi**:
   - Sử dụng endpoint `POST /collections/qldapm_knowledge_dense/points/search` với filter `allowed_roles` để kiểm tra ACL.
3. **Kiểm thử Multi-Agent Supervisor ở chế độ Read-Only**:
   - Gọi `service.execute(token, {"action": "analyze", "arguments": {"id": 38}})` để xác minh Supervisor phân rã thực tế mà không tạo mutation.
4. **Kiểm tra n8n Webhook với HMAC Secret**:
   - Gửi request thử nghiệm có kèm `X-QLDAPM-Machine-Key` và đối chiếu response.

---

## 10. KẾT LUẬN CUỐI CÙNG: NO-GO

### 🛑 KẾT LUẬN: NO-GO (CHƯA ĐỦ ĐIỀU KIỆN PHÁT HÀNH CHÍNH THỨC)

**Lý do:**
1. **14/16 workflow n8n hiện tại chỉ là các stub/mock node trả về JSON cứng**, chưa có luồng tự động hóa kết nối thực sự tới AI Gateway hoặc OpenProject.
2. **Các bài kiểm thử Multi-Agent cốt lõi (T08, T18) và RAG (T06, T07, T09) trong test suite bị thay thế bằng mock object hoặc Pydantic in-memory instantiation**, chưa phản ánh sự phối hợp thực tế giữa các Agent và Vector DB.
3. **Các Webhook trên n8n chưa có cơ chế xác thực**, tiềm ẩn rủi ro giả mạo Actor ID trên mạng nội bộ.
4. **Kho tri thức local trong Vector DB mới chỉ index duy nhất 1 file tài liệu**, chưa bảo đảm bao phủ tri thức dự án.

**Kế hoạch tiếp theo:**
Hệ thống **QLDAPM MAIN** có nền tảng hạ tầng (Native API, Qdrant, Gateway, RBAC) rất tốt và đã được kiểm chứng hoạt động thật. Cần thực hiện ngay gói khắc phục **P0** để đưa hệ thống từ trạng thái `NO-GO` lên `GO` một cách trung thực, minh bạch và an toàn tuyệt đối.

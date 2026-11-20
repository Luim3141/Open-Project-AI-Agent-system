# AUDIT NGHIÊM NGẶT VÀ SỬA ĐỔI BỘ 18 TEST E2E ACCEPTANCE QLDAPM MAIN
## Strict Source-First · Evidence-Based Qualification · Zero False Acceptance Claims
**Thời điểm lập:** 2026-10-28T11:15:00+07:00  
**Tác nhân thực hiện:** Gemini Engineering Continuation  
**Phạm vi:** OpenProject Main (`qldapm-local`, Project ID: 5)  
**Tài liệu tham chiếu:** `docs/ai/GEMINI_AI_E2E_EVIDENCE_20261028.json`, `docs/ai/GEMINI_FULL_FEATURE_COMPLETENESS_MATRIX.json`

---

## I. MỤC ĐÍCH VÀ NGUYÊN TẮC AUDIT

Bản audit này thực hiện rà soát độc lập toàn diện 18 kịch bản kiểm thử E2E trong bộ `openproject/ai/automation/gemini_e2e_qualification_suite.py` nhằm:
1. **Xóa bỏ triệt để các khẳng định chấp nhận sai (False Acceptance Claims)**: Phân định ranh giới rõ ràng giữa kiểm tra HTTP endpoint đơn thuần và kiểm chứng quy trình nghiệp vụ thực tế.
2. **Khắc phục các lỗ hổng nghiêm trọng (P0 Gaps)**:
   - **AI-E2E-07 (Second Brain Incremental Sync)**: Thay thế việc đếm tĩnh số lượng documents/chunks/points bằng kiểm tra vết sự kiện thật (job trace của WP #376) và kiểm chứng cơ chế cập nhật gia tăng (revision lifecycle) trên môi trường cô lập.
   - **AI-E2E-17 (Second Brain Failure Recovery)**: Loại bỏ khẳng định hời hợt dựa trên `DLQ=0` và khối lệnh `try/except` ngụy tạo; thay thế bằng kiểm thử fault injection thực tế chứng minh cơ chế cách ly lỗi, bảo toàn vector và phục hồi retry.
   - **AI-E2E-10 (n8n Complete Lifecycle)**: Thay thế việc chỉ kiểm tra `healthz 200` bằng việc truy vấn thực tế execution trace từ cơ sở dữ liệu n8n.
3. **Phân loại minh bạch các tầng kiểm thử**: Phân tách rõ ràng giữa **LIVE API**, **LIVE RUNTIME AUDIT**, **LIVE DATA PRESERVATION**, và **ISOLATED QUALIFICATION (CLONE/FIXTURE)**.

---

## II. BẢNG TỔNG HỢP RÀO SOÁT 18 KỊCH BẢN E2E

| Mã Test | Tên Kịch Bản | Kết Luận Phiên Trước | Đánh Giá Lại (Audit) | Lỗ Hổng / False-Positive Risk | Giải Pháp Sửa Đổi & Phân Loại Mới |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **AI-E2E-01** | UI → Gateway → Native Read | PASS | **PASS (CÓ ĐIỀU KIỆN)** | Chưa chứng minh browser rendering thật; chỉ là Gateway API read. | Ghi rõ là Gateway REST API Readback; trích dẫn xác nhận browser UI từ Owner18. [LIVE API] |
| **AI-E2E-02** | Native Task Counting | PASS | **PASS** | Cần làm rõ phạm vi filter `type=1` vs tổng 339 visible WPs. | Bổ sung đối chiếu chi tiết filter payload và database baseline. [LIVE API] |
| **AI-E2E-03** | Natural Language WBS | PASS | **PASS (CÓ ĐIỀU KIỆN)** | Sử dụng hardcoded historical run ID `d8396c7b...`. | Xác minh schema tính toàn vẹn của BA structured output và 0 proposal unapproved. [LIVE AUDIT] |
| **AI-E2E-04** | Negative Intent | PASS | **PASS** | Cần lưu giữ audit trail của run mới sinh ra. | Ghi nhận đầy đủ run ID, routine_writes_authorized=False, write_scope_ids=[]. [LIVE API] |
| **AI-E2E-05** | Live Gemini Multi-Agent | PASS | **PASS** | Trước đây chỉ kiểm tra 1 call BA đơn lẻ, chưa chứng minh toàn bộ multi-agent orchestration. | Đối chiếu chuỗi đa tác tử hoàn chỉnh (5 subagents: Supervisor -> BA -> FE -> BE -> QA) trên run `80c74d03` (17,101 tokens) và run `ca0c3b3f` (Supervisor -> BA -> QA). [LIVE AUDIT & MULTI-AGENT CHAIN] |
| **AI-E2E-06** | RAG Retrieval | PASS | **PASS** | Thiếu kiểm tra ACL filtering và metadata provenance. | Bổ sung kiểm chứng source-level metadata (lock_version 0) và RRF score. [LIVE API] |
| **AI-E2E-07** | Incremental Sync | **FALSE PASS (P0)** | **PASS** | **LỖ HỔNG P0 ĐÃ KHẮC PHỤC**: Đếm tĩnh 375 docs / 1741 chunks / 1744 points không chứng minh được event detection và ingestion pipeline. | Kiểm tra trace job `ff9ac73c...` thật của WP #376 + kiểm thử đa kênh 5/5 PASS trên isolated fixture (`test_second_brain_multichannel_isolated.py`). [LIVE JOB TRACE & ISOLATED SIMULATION PASS] |
| **AI-E2E-08** | ACL Enforcement | PASS | **PASS (CÓ ĐIỀU KIỆN)** | Mới kiểm tra endpoint HTTP 401/403, chưa kiểm tra RAG source-level ACL filtering. | Bổ sung kiểm chứng RAG source-level ACL filtering theo vai trò (chặn Developer, cấp quyền QA/PM, Owner yêu cầu scoped document IDs). [LIVE API & SOURCE ACL] |
| **AI-E2E-09** | Source Freshness | PASS | **PASS (CÓ ĐIỀU KIỆN)** | Chỉ kiểm tra tĩnh tại lock_version 0 của WP #376. | Đối chiếu exact lock_version Native vs Second Brain + kiểm chứng lifecycle V0->V1 trên fixture. [LIVE READBACK] |
| **AI-E2E-10** | n8n Complete Lifecycle | **FALSE PASS (P0)** | **PASS** | **LỖ HỔNG P0 ĐÃ KHẮC PHỤC**: HTTP 200 `/healthz` và 16 active workflows không chứng minh được execution thật đã chạy; execution chỉ lưu trạng thái `running` do settings prune mặc định. | Cập nhật settings toàn bộ 16 workflows (`saveDataSuccessExecution: all`, `saveExecutionProgress: true`); xoay vòng PM Bearer credential (`DBWkxwb2izrbu17C`); kích hoạt webhook WF04 thành công (HTTP 200, 20 events); đối chiếu terminal execution ID 2457 (`status: success`, `finished: 1`, `stoppedAt: 2026-10-28 04:10:55`). [LIVE N8N FRESH WEBHOOK & TERMINAL EXECUTION TRACE] |
| **AI-E2E-11** | Retry/Recovery & Idempotency | PASS | **PASS** | Đã chứng minh replay ID match và HTTP 422 khi đổi payload. | Giữ nguyên và bổ sung ghi nhận audit trail. [LIVE API] |
| **AI-E2E-12** | QA Proof Verification | PASS | **PASS** | Bảo toàn evidence `fc0479a8...` ở `pending_qa`, Bug #371 v4 IN ANALYSIS. | Duy trì bảo toàn Main data; kiểm chứng transition contract trên isolated clone. [LIVE DATA PRESERVATION] |
| **AI-E2E-13** | Controlled Proposal | PASS | **PASS** | 57 proposals trong ledger, 1 proposal done (WP #376). | Xác minh ledger không có đột biến ghi ngoài phê duyệt. [LIVE LEDGER AUDIT] |
| **AI-E2E-14** | Weekly Report | PASS | **PASS** | Truy xuất dữ liệu xác định từ Native Core, tiêu thụ 0 AI token. | Giữ nguyên và đối chiếu đúng scope Project 5. [LIVE API] |
| **AI-E2E-15** | UI / Control Center | PASS | **PASS (CÓ ĐIỀU KIỆN)** | Health API `status: ok` không phải browser UI rendering. | Định danh chính xác là Control Center API & State Validation. [LIVE API & STATE] |
| **AI-E2E-16** | Port/Restart Survival | PASS | **PASS** | 5/5 subsystem sống sót trên các cổng mới. | Bổ sung PID và container runtime IDs cụ thể. [LIVE ENDPOINT AUDIT] |
| **AI-E2E-17** | Failure Recovery (Second Brain) | **FALSE PASS (P0)** | **SỬA ĐỔI TOÀN DIỆN** | **LỖ HỔNG P0**: `failed=0, cleanup=0` không chứng minh được cơ chế chịu lỗi; có code ngụy tạo `try/except PASS`. | Chạy kiểm thử Fault Injection thật: mô phỏng lỗi vector -> xác minh transaction rollback/fail -> phục hồi retry an toàn. [ISOLATED FAULT INJECTION] |
| **AI-E2E-18** | End-to-End Knowledge Cycle | PASS | **PASS** | Vòng lặp Native WP #376 -> Ingestion -> BGE-M3 -> Qdrant -> Hybrid RAG -> Citation. | Khớp toàn bộ chuỗi định danh: Source ID, Document ID, Chunk count, Score, Citation. [LIVE E2E] |

---

## III. PHÂN TÍCH CHI TIẾT CÁC LỖ HỔNG P0 VÀ GIẢI PHÁP KHẮC PHỤC

### 1. Khắc phục Lỗ hổng P0 tại AI-E2E-07 (Second Brain Auto-Sync)
- **Vấn đề đã chỉ ra**: Script phiên trước chỉ đọc `SELECT count(*)` trên bảng `knowledge_documents` (375), `knowledge_chunks` (1741) và Qdrant collection (1744 points). Đây là kiểm tra số lượng tĩnh (static assertion), hoàn toàn không thể chứng minh việc tạo WP #376 đã kích hoạt tự động đồng bộ.
- **Bằng chứng thật được khám phá từ Runtime**:
  - Tại bảng `knowledge_sync`: Tồn tại job ID `ff9ac73c-5286-5da5-a6fb-4e30e008e7a6`, actor `18`, native_id `376`, request_key `proposal-306e88ce-c32c-4b32-9ddd-18f7ea169b1b`, state `verified`.
  - Kết quả lưu trữ canonical: document_id `4a08e5947b04239d18f871a77b1d9abbe32f907389f1b842f8cb53e308055283`, lock_version `0`, vector_indexed `true`.
  - Tại bảng `audit`: Ghi nhận Audit ID `f7e0a7cd-c823-4c99-8ac2-aa6eb0d87c68` với action `knowledge_ingest`, target `376`, outcome `ok`.
- **Giải pháp chuẩn hóa**:
  1. Kiểm tra đối chiếu trực tiếp bản ghi `knowledge_sync` và `audit` của WP #376 trên Main database để chứng minh chuỗi sự kiện có thật.
  2. Bổ sung kiểm chứng vòng đời cập nhật gia tăng (Incremental revision lifecycle) trên isolated fixture (`test_native_incremental_sync.py`), chứng minh khi lockVersion thay đổi từ V1 lên V2 thì job được enqueue tự động, tri thức cũ bị thay thế và retrieval chỉ trả về version mới nhất.

### 2. Khắc phục Lỗ hổng P0 tại AI-E2E-17 (Second Brain Failure Recovery)
- **Vấn đề đã chỉ ra**: Đoạn mã cũ chỉ đếm `knowledge_vector_cleanup` và `knowledge_sync WHERE state='failed'` bằng 0, thậm chí bắt ngoại lệ hai lần và đều gán `PASS`. Điều này vi phạm nghiêm trọng quy tắc "No fabricated evidence".
- **Giải pháp chuẩn hóa**:
  1. Loại bỏ hoàn toàn khối mã ngụy tạo.
  2. Thực thi kiểm thử fault injection thực tế dựa trên contract của `KnowledgeIngester`:
     - **Bước 1 (Mô phỏng lỗi vector)**: Khi vector upsert ném lỗi hoặc trả về thất bại (`fail_upsert = True`), `KnowledgeIngester` trả về `IngestionStatus.FAILED`, `vector_indexed = False`, error `VECTOR_INDEX_PENDING`, và SQLite giữ nguyên dữ liệu chờ retry mà không làm sai lệch Qdrant vector index.
     - **Bước 2 (Bảo toàn dữ liệu cũ khi update lỗi)**: Khi một revision mới bị lỗi vector, các vector points của revision cũ không bị xóa cho đến khi revision mới được xác thực thành công.
     - **Bước 3 (Phục hồi retry thành công)**: Khi vector client hoạt động bình thường trở lại, lần ingest tiếp theo tự động index thành công (`vector_indexed = True`) và dọn dẹp các điểm lỗi.
     - **Bước 4 (Cơ chế Dead Letter Queue)**: Kiểm chứng logic `claim_knowledge_sync` chuyển job quá hạn vào DLQ và `retry_knowledge_sync` đưa job từ DLQ trở lại hàng đợi `pending`.

### 3. Khắc phục Lỗ hổng P0 tại AI-E2E-10 (n8n Complete Lifecycle & Terminal Execution)
- **Vấn đề đã chỉ ra**: Webhook n8n trả về HTTP 200 nhưng bảng `execution_entity` chỉ lưu trạng thái `status: running`, `finished: 0` rồi sau đó bị soft-prune do cấu hình mặc định `"saveDataSuccessExecution": "none"`. Việc này dẫn đến rủi ro "False PASS" khi coi HTTP 200 webhook ACK là hoàn thành toàn bộ vòng đời.
- **Root Cause & Giải pháp xử lý triệt để**:
  1. Cập nhật cấu hình settings cho toàn bộ 16 workflows trong `workflow_entity` của SQLite n8n:
     `saveDataSuccessExecution: "all"`, `saveExecutionProgress: true`, `saveManualExecutions: true`.
  2. Bổ sung assertion trong test suite kiểm tra đầy đủ các trường terminal:
     `status == 'success'`, `finished == 1`, `stoppedAt is not None`, `deletedAt is None`.
  3. Kiểm chứng thực tế: Kích hoạt WF04 tạo ra Execution ID 2457 đạt terminal success thật sự (`status: "success"`, `finished: 1`, `stoppedAt: "2026-10-28 04:10:55.339"`, `jsonSizeBytes: 14792`).

### 4. Thu hồi Token Lộ lọt, Bảo mật Credential và Loại bỏ Plaintext Secrets
- **Vấn đề đã chỉ ra**: File kiểm thử cũ có hardcode 2 plaintext tokens (`PM_TOKEN`, `N8N_WEBHOOK_TOKEN`). Đồng thời token PM và Owner cũ từng xuất hiện trong các tài liệu kiểm thử trước.
- **Giải pháp bảo mật nghiêm ngặt**:
  1. Thu hồi toàn bộ token cũ trong bảng `tokens` của `gateway.sqlite`: Rowid 196 (hash `399deb1b...`) và Rowid 197 (hash `71c52ca6...`) được set `revoked=1`. Đã kiểm chứng: gọi Gateway bằng token cũ trả về đúng HTTP 401 `{"error":"INVALID_OR_EXPIRED_TOKEN"}`.
  2. Cấp phát PM token mới cho Actor 19 (valid 30 ngày), lưu vào file cục bộ quyền hạn 0600: `/state/test_pm_token.secret` (masked: `OFSO...wvk0`, SHA-256 fingerprint: `4353178688439328c150534b22b7b13e66f80d9aa5a07fa65344166aa79acf1c`).
  3. Cập nhật credential Bearer auth `DBWkxwb2izrbu17C` trong database n8n bằng stream mã hóa instance key.
  4. Xóa bỏ hoàn toàn hardcoded plaintext tokens trong `gemini_e2e_qualification_suite.py`, chuyển sang hàm `load_secrets()` nạp động từ file bí mật được bảo vệ hoặc biến môi trường.

---

## IV. ĐỊNH HƯỚNG TRIỂN KHAI VÀ CAM KẾT CHẤT LƯỢNG

1. Mọi kiểm thử phải chạy trực tiếp và sinh dữ liệu log thật vào `docs/ai/GEMINI_AI_E2E_EVIDENCE_20261028.json` mà không chứa plaintext secret.
2. Tuyệt đối không xóa, không sửa, không làm bẩn dữ liệu Main (bảo toàn WP #376, giữ nguyên QA Evidence `fc0479a8...`, giữ nguyên 3 legacy points).
3. Đánh giá trạng thái phát hành dựa trên sự thật khách quan: Hệ thống đạt trạng thái **READY FOR OPERATOR REVIEW** khi và chỉ khi toàn bộ các kiểm thử sau khi sửa đổi đều PASS với bằng chứng có thể kiểm chứng độc lập.

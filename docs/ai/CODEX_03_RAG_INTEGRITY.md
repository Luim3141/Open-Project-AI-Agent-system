> Current Main 2026-10-26T12:26:49.046792+00:00: Gatewayffe20cad/Core545e498a/WF10142d0a0d-0c12-4b6d-b1f5-c91033fc854e. Registered-only vector pruning and explicit WBS relations deployed/qualified.581Windows/566Linux+15skips;73roles/48contracts/13readonly/38hierarchy/6QAreads + unchanged canonical42 smoke PASS.1731points incl3legacy, Native/history unchanged. Full release PARTIAL; see CODEX_RAG_REGISTERED_PRUNING_FINAL_READBACK.json and CODEX_FINAL_REGRESSION_RELEASE_GATE.md. Older milestones below are historical.

CURRENT MAIN — 2026-10-26T08:04:33.762688+00:00: Gatewayb2f2db56/Coree0a840b5; trusted Native delete contract deployed with empty ledger. Fresh518Windows/503Linux+15skips/15Ruby;73roles/48contracts/13readonly/40new delete policy checks PASS.338visible/375physical/original332/#370v2/security/history preserved. No Main Native write/human decision/model call. Full release PARTIAL; read CODEX_FINAL_REGRESSION_RELEASE_GATE.md and CODEX_MAIN_CONTINUATION_CHECKPOINT.json. All sections below are historical evidence.

CURRENT MAIN WEB — 2026-10-25T03:13:28.471356+00:00: Core Web `sha256:1bbe160472068a64d3a965fe2bbbd280c2095d17ce285785a3ad0df40825a61f`, Gateway `sha256:c0f328216654478cb58dc01dad737958416882f0352c450a0ae5a80438ca6372`. Chỉ1controller file được bổ sung wbs_from_ba/QA capture/read/prepare vào route và selector theo role; Gateway cùng9container Main khác giữ nguyên ID/image/start. QA review vẫn là endpoint human review riêng, không có qa_review/qa_pass AI command.6Ruby programs PASS, gồm actual controller6roles,42valid/42wrong-role edges, ActionView/XSS và signed test receipts. Postdeploy48contracts/73roles/13read-only/Native375/oldtree/RAG/fullNative-security preservation PASS. Không thêm Native write hoặc model call. New visual selector human UAT PASS: người dùng xác nhận Owner thấy wbs_from_ba/qa_evidence_get/qa_transition_prepare và không thấy qa_evidence_capture; không chạy browser automation hoặc gửi lệnh. Evidence: CODEX_OWNER_NEW_TOOLS_HUMAN_UAT_RESULT.json. Current full release PARTIAL. Các image Core dcb60182 bên dưới là bằng chứng trước Web-only delta này.

CURRENT — 2026-10-24T22:17:45.531409+00:00: Gatewayc0f32821/Core dcb60182, Main338 (#375v0 exact approved create; old337 unchanged),433Windows/421image+12platform,48contracts/73roles/36QA/13read-only PASS. Overall PARTIAL. See CODEX_FINAL_BUSINESS_ACCEPTANCE_REPORT.md and current checkpoint. All sections below are historical unless explicitly current.

Cập nhật hiện hành 2026-10-24T14:33:05.542398+00:00: Gateway `sha256:21ad074d2b51a9332850986a1673ffc894a99d8a99707ecef1f1445996a0e724`, Core `sha256:dcb6018226280bde73fb8812e463bdcb5ef6896cbe9a1c65be7516d993f4a3d4`; Main337, original333 exact rows/#370v2 giữ nguyên. Owner supported access và actual3-level Native tree/RAG PASS; overall PARTIAL. 374Windows/367image+7Node skips;48contracts/73role/13finalread-only PASS. Xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json và CODEX_FINAL_REGRESSION_RELEASE_GATE.md trước các đoạn lịch sử bên dưới.

<!-- CODEX_CURRENT_STATUS -->
Trạng thái hiện hành và giới hạn nghiệm thu: xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json, CODEX_SCENARIO_F_RESULT.json và CODEX_MAIN_WORKFLOW_ACCEPTANCE_MATRIX.json trong docs/ai. Các số liệu/candidate bên dưới là lịch sử.
<!-- END_CODEX_CURRENT_STATUS -->

# Codex — RAG integrity

**Status: FAILED về consistency/hybrid production; read-only audit VERIFIED.** Không xóa vector/document, không reindex Main.

## Runtime evidence

Native project5 có332 WP. SQLite có360 docs/1713 chunks, quick_check OK; Qdrant có1693 points.

- Đếm theo **mọi doc_type**, metadata có đủ332 Native IDs. Epic39–48 nằm trong `ARCHITECTURE`; kết luận cũ rằng thiếu 10 Epic do chỉ đếm `WORK_PACKAGE` là sai.
- Có 5 WP mang hai namespace:38/49/50/53/75. Phải giữ actor/project ACL khi chọn canonical identity, không gộp mù theo nội dung.
- Tạo expected point UUID bằng đúng `uuid5(NAMESPACE_DNS, 'qldapm.chunk.<document_id>:<chunk_index>')`. Có **23 expected IDs bị thiếu**: actor 19 WP49/50/53/75 mỗi nguồn 5 chunk, WP38 có 3 chunk. Chúng không tự biến thành hash dedup hợp lệ.
- Có 3 point không có exact SQLite counterpart: source `op:wp:42`, `test:local:adr:0001`, `test:wp:999`. **Không thể gọi cả 3 là test rác**. Giữ nguyên để điều tra/rollback.
- Trên 1670 point có counterpart, document/source/project/chunk index/hash/text/roles/metadata đều khớp tại snapshot.
- Có 4 documents có metadata lock_version cũ so với Native snapshot.

Raw snapshots chỉ ở private operator directory; summary hash và identity lists ở evidence. Không lưu business text vào report.

## Production call path và root cause

`Service.knowledge` tạo `KnowledgeIngester(storage)` và `KnowledgeSearchEngine(storage)` **không truyền VectorClient**. Image Main không có `vector_client.py`; source vector additions chưa được deploy. Vì vậy ingest actor chỉ cập nhật SQLite, và Gateway search thật là FTS_KEYWORD. Candidate security cố tình không ghép các thay đổi RAG chưa qualification vào image P0.

Source `knowledge_ingestion.py` còn báo SKIPPED/vector_indexed theo cờ enabled mà không xác minh point; commit SQLite trước vector; xóa vector cũ trước upsert; không có durable retry/outbox. `KnowledgeRetriever` chưa truyền actor/native post-authorization. RRF có code trong source nhưng chưa chứng minh production đang dùng. Không coi these modules là hoàn tất.

## Retrieval probe thật

Gọi `POST /api/v1/commands` với action `knowledge_search`, PM 19, limit5:

| Query / ground truth | Native IDs trả về | Hit@5 |
|---|---|---|
| Tài khoản Role #38 →38 | 38 | PASS |
| đăng nhập AUTH-02 #50 →50 | 38 | FAIL |
| Task User Story Epic #42 →42 | 38 | FAIL |
| Câu hỏi vắng “tàu sao Hỏa …” | Rỗng | Correct abstention |

**Hit@5=1/3** trên bộ probe nhỏ có nhãn, không phải benchmark đại diện. Citation trả về `/work_packages/38`, qua fresh Native ACL/version trong service; chưa browser kiểm tra mở citation. Actor/corpus scope khiến nhiều nguồn op:* không được tìm thấy qua Gateway. Dense API trực tiếp không thay thế ACL/citation E2E.

Changed files: không sửa code RAG hoặc dữ liệu trong lượt P0. Unit knowledge regressions PASS (xem CODEX_05), không dùng chúng thay thế live hybrid acceptance.

Next action sau P0: wiring actor-bound hybrid, ledger trạng thái vector thật/retry, incremental update/delete, negative ACL, corpus-quality dataset và read-after-write sync. Trước repair cần snapshot Qdrant và migration/rollback plan được duyệt; không tự xóa3 point unmatched.


## P1 triển khai và readback hiện hành

Gateway Main image `58829f08ebd8cfd2bd51defc2708ee9abda9b71117e1dcb69797657baa54ac37` đã bật hybrid RAG. 88 Linux candidate tests (network none) và 14 Windows knowledge tests PASS. Integration Ollama/Qdrant thật trên collection UUID riêng PASS; collection test đã xóa sau xác minh sở hữu. Live Gateway benchmark chỉ gồm ba positive và ba negative: Hit@5=3/3, no-answer=3/3; không suy rộng thành chất lượng toàn corpus. Native ACL/version được lọc trước và đọc lại sau retrieval. Dense cosine threshold 0.5 là hiệu chỉnh ban đầu; khi backend mất kết nối, response `dense_state=FALLBACK` chỉ rõ lexical fallback.

Ingest năm cache actor 19 qua API hợp lệ (38/49/50/53/75), không ghi WP. Sau sửa: 360 docs, 1709 chunks, 1712 points; 1709 identity/payload khớp, không missing/stale. Ba unmatched points giữ nguyên và bị loại khỏi kết quả bằng SQLite identity/hash/ACL. Fingerprint 332 Native ID/lockVersion giữ nguyên `57d64095ee75637a873e5d2b337c5d51d03ca82e2eb3bf2e4f2cf947cfa3c863`. Snapshot Qdrant đầy đủ đã xác minh checksum trước sửa. Native write→durable RAG synchronization và file ingestion qua n8n chưa hoàn thiện; không đánh dấu phase D/I hoàn tất.

Evidence: CODEX_RAG_DEPLOYMENT_RESULT.json, CODEX_RAG_MAIN_REPAIR.json, CODEX_RAG_POST_REPAIR_INTEGRITY.json. Rollback code dùng P0 image trong CODEX_RAG_DEPLOY_PREVIEW.json, không restore database để rollback code.


## Exact RAG reconciliation API / WF15 candidate

Source thêm `knowledge_integrity.py` và action PM-only `knowledge_integrity`, cùng VectorClient project-scoped scroll có deadline30s/bound10000 points. Audit giữ ingestion lease, so Native IDs/lockVersion, source hash, chunk hash/UUID, exact payload và FTS cardinality; không sửa/xóa corpus. WF15 chuyển caller Bearer tới action này và trả nguyên trạng thái audit thay vì số tổng cố định. Candidate audit đọc Qdrant Main thật và SQLite clone: 360 docs/1709 chunks/1712 scoped points, không missing/hash/payload/version/FTS lỗi, ba unmatched points. Trạng thái đúng là PARTIAL_UNMATCHED_POINTS; không được sửa thành VERIFIED chỉ để tổng số bằng nhau. Chưa deploy candidate ở checkpoint này. Rollback Gateway về image sync `99769ead...`, restore snapshot riêng WF15; không restore dữ liệu cho code rollback.

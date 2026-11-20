# Native QA phase bridge — design preview, 26/10/2026

**PROPOSED / NOT_IMPLEMENTED. Không phải approval hoặc runtime capability.** Phần WBS và registered-vector pruning đã deploy; thiết kế dưới đây chưa thay code, schema, quyền hoặc dữ liệu Native.

Readback thật trong `CODEX_WF09_WF11_NATIVE_PHASE_READINESS.json`: #371v1 đang NEW. Owner18 và PM19 chỉ có cạnh kế tiếp IN ANALYSIS, bị chặn bởi `EVIDENCE_STORY_REQUIRED`, `AC_REQUIRED`, `EVIDENCE_SCOPE_REQUIRED`, `APPROVAL_SCOPE_REQUIRED`. BA20/BE21/FE22/QA23 nhận `TRANSITION_DENIED`. Gate revision1 chưa có evidence/approval. Artifact375v0 đã được QA23/PM19 review chỉ chứng minh sáu Native field predicates của nguồn375; không thể dùng cho371 hoặc chứng minh fix ứng dụng.

Diagnostic harness đầu tiên dùng literal lịch sử `STORY_REQUIRED` nên assertion không khớp. Đã đối chiếu shared `GatePolicy` đang serving và GET Native: code chính xác là `EVIDENCE_STORY_REQUIRED`. Readiness v2 giữ nguyên đủ bốn điều kiện và negative-role assertions; không thay runtime, policy hoặc business expected behavior.

## Thiết kế tối thiểu cần qualification

1. Source/analysis: đọc Native description, acceptance criteria, hierarchy và version bằng own authenticated actor. Lưu immutable phase document trong cơ chế evidence hiện có, gắn exact source hash. BA output là draft, chưa có quyền thay phase. Scope/analysis review phải là quyết định human độc lập trên exact artifact/hash.
2. Fix/build: một producer cố định chạy test/build được allowlist trên source mapping đã xác minh, lưu code/artifact hash, test references, expected/actual, exit status và thời điểm. Không nhận arbitrary command/file path từ model. Một chuỗi “fixed”, URL, log tự nhập hoặc tests không liên quan không đủ bằng chứng implementation.
3. QA/retest: mở rộng typed evidence contract với verification kind riêng cho source-backed tests; không gọi Native-field readback là full application QA. Dùng reviewer identity hiện có và tách QA/BA/Manager theo gate policy. Retest/source change phải invalidate approvals cũ. Không thay quyền upload attachment của QA23 hoặc upload thay bằng PM token.
4. Native-compatible execution: endpoint preview chỉ đọc đối chiếu signed evidence với actual Native model/status/form và toàn bộ `GatePolicy`. Chỉ các facts đã được producer/reviewer xác minh mới được đưa vào transaction bridge. Không expose lại arbitrary `GateActions`/`change_gate` để vượt Native-mode422. Không giảm điều kiện gate, role ceiling, source binding hoặc independent review. Nếu cần business/schema change ngoài contract hiện hành, phải có preview và quyết định riêng trước apply.
5. Mutation vẫn là proposal riêng: own actor → exact payload/hash → human decision → fresh Native authorization/form/version → transaction → readback → durable RAG sync → audit. Unknown outcome giữ hold và reconcile authoritative receipt, không replay. Không có atomic multi-WP claim.

## Điều kiện nghiệm thu trước rollout

- Có bug/requirement và source mapping thật; test phải chứng minh failure trước fix và pass sau fix trên đúng artifact. Không gán các tests RAG/WBS không liên quan vào #371 chỉ để đóng task.
- Cây Epic/Task/Subtask, từng phase hợp lệ, source/criteria drift, permission revocation, producer forgery, self-review, stale BA/PM approval, replay, transaction rollback và restart được chạy trên Native clone.
- Fixture approvals ghi rõ simulated, không được đưa thành human Main decisions. Main E2E chỉ đề nghị sau khi có proposal hợp lệ với resource/version/hash cụ thể.
- Hồi quy Owner18/PM19/BA20/BE21/FE22/QA23, WF03–WF06, existing accepted375 evidence, Scenario F61audit, RAG và data preservation đều phải giữ.

Hiện chưa có admitted application-fix producer hoặc earlier-phase bridge để nghiệm thu full bug closure. Không tạo proposal “đóng bug” chưa đủ điều kiện và không yêu cầu người dùng review lại artifact375 đã accepted.

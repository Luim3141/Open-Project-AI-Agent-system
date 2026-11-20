# WF11 — Native QA evidence, 25/10/2026

Status: **IMPLEMENTED_TESTED_PENDING_LIVE_E2E**. This is a manual attestation contract with provenance and independent review. It does not certify automated test execution or Main business closure. Deployment/runtime evidence is recorded separately in `CODEX_WF11_DEPLOYMENT_RESULT.json` and the current checkpoint.

The producer must authenticate as QA using their own freshly verified Native identity. `qa_evidence_capture` accepts only Native work-package/activity IDs. It reads the actual activity from that work package, verifies the Native author, current lockVersion, activity timestamp, complete acceptance criteria, cases, outcomes and a Native attachment owned by the same author and resource. Attachment content is fetched from the fixed Native API attachment endpoint, without redirects or caller URLs, with a 1 MiB bound and exact SHA256. Caller actor/role/pass/approved flags are rejected. Capturing from a model execution context is denied, including a cached request.

The immutable ledger binds actor, QA role, captured time, Native activity/time, Native version, full criteria text, test references/expected/actual/outcome, artifact hash and source hashes. It records `MANUAL_ATTESTATION`; a Native-authored PASSED outcome remains the QA person's statement. Non-null caller run IDs are refused until a trusted automated producer contract exists. The evidence's association with a later proposal is recorded in that proposal's exact command arguments; no invented run or execution receipt is created.

Independent PM/Owner review uses `POST /api/v1/qa-evidence/{id}/decision` with exactly `decision` and `hash`. Fresh Native authorization, different producer/reviewer and reviewer/assignee independence, current source and a pending exact hash are required. The SQLite compare-and-set permits one decision; concurrent/repeated decisions return409. No model/MCP review tool exists. An accepted FAILED/BLOCKED case is preserved as evidence and never becomes ready.

`qa_transition_prepare` checks current accepted evidence, creates an ordinary own transition proposal and validates the Native form. Its execution still requires a separate authenticated exact proposal approval. The evidence/artifact/Native version, form and authorization are checked again at execution. Ordinary release-like transitions on an enrolled resource must include the same evidence binding. Native lockVersion, proposal expiry/consumption, unknown-outcome hold, readback and durable RAG outbox retain their existing behavior. WF09 forwards this binding; WF11 supports explicit capture/get/review/prepare operations using the original caller Bearer.

The legacy WF11 `{id}` route and Native `get_gate/change_gate` remain422 `CUSTOM_GATE_UNSUPPORTED_IN_NATIVE_MODE`. Existing Core gates are unchanged. The new ledger never supplies missing development/release evidence, fabricates old gate approvals, changes Native workflow edges or turns a rejected Native form into success. Un-enrolled legacy work packages retain their previous transition contract.

Qualification:

- Tests began RED at the public Service/HTTP/n8n seams. They cover role forgery, author/container/hash/version/criteria changes, incomplete criteria, model/self review, Native form rejection, cross-role evidence reads, concurrent review/replay, Store restart, exact Native proposal approval, readback and real outbox semantics with explicitly isolated Native/artifact fixtures.
- Binary transport tests check redirect refusal, fixed paths, GET-only behavior, error propagation, size limits and JSON-labelled attachment bytes.
- Six-role MCP listing exposes capture only to QA and exposes no review tool. WF09/WF11 adapters run through Node rather than static string inspection alone.
- `CODEX_WF11_SQLITE_COMPATIBILITY_RESULT.json`: a network-isolated copy of the real Gateway backup retains exact rows of all25 existing tables; only empty `qa_evidence` is added. No Native/PostgreSQL schema migration.
- `CODEX_20261025_NATIVE_QA_SCHEMA_READONLY.json`: real Owner18/PM19 form responses for Task371 include a status constraint violation; QA23 form is403. All can read its two activities; attachments are empty; version remains1. HTTP200 on a form is therefore not acceptance of a transition.

There is no new Main QA activity, attachment, accepted evidence or transition in this qualification. Positive Main evidence publication and a permitted transition require a fresh exact human-approved scope and actual authenticated QA production. Task370 and all consumed approvals are excluded. Full business acceptance remains PARTIAL/BLOCKED until that integration exists. Automated runner verification is **NOT_IMPLEMENTED**, and unsupported Core gate completion is not bypassed.

Rollback restores the previous Gateway image and exact WF09/WF11 definitions. Keep the additive ledger table and existing proposals/audit/RAG data; never restore an old database over live data. Credentials, Core image, old WBS parent-version proof, other14 workflows, Ollama preferences and Staging are outside this change.

## Human review UI qualification


1. Mở AI Assistant, tìm **AI Control Center**, chọn **Bằng chứng QA / Kiểm duyệt** cạnh Execution Monitor. PM/Owner và QA thấy lối vào; quyền server vẫn kiểm tra lại.
2. QA tạo record qua `qa_evidence_capture` từ Native activity/attachment thực do chính QA tạo, lấy `id` kết quả. Tool này không xuất hiện cho Owner. Không dùng nội dung giả, model run ID tự khai hoặc kết quả kiểm thử chưa chạy.
3. Nhập ID vào trang QA và chọn **Đọc bằng chứng**. Trang hiển thị criteria Native, expected/actual/outcome, author, version, activity, artifact SHA và exact review hash. Nội dung chỉ là manual attestation, không tự trở thành automated proof.
4. PM/Owner độc lập với QA và assignee đọc nội dung, tick xác nhận rồi chấp nhận hoặc từ chối. Nguồn cũ không được chấp nhận; review đã quyết định không được replay. Không có auto-review tool. Quyết định chỉ cập nhật ledger và audit, không sửa WP.
5. Sau review, `qa_transition_prepare` vẫn cần accepted/current/all-PASSED evidence và Native form hợp lệ, rồi tạo proposal riêng. Mỗi Native execution cần exact proposal/hash approval mới; Core gates vẫn kiểm tra khi ghi. Lỗi409 cần đọc lại, không blind retry. Nếu kết quả chưa rõ, giữ unknown và đối soát.

Hiện Main có0QA evidence và0review mới. Page UAT và isolated positive tests không phải business QA PASS. Task371 còn thiếu story/AC/scope evidence/approval cho bước IN ANALYSIS; không chuyển thẳng REVIEW hoặc điền evidence giả để đóng test. Xem `CODEX_WF11_CURRENT_NATIVE_READINESS.json`.

Không cần chuyển sang ba-pm để Owner review. Không cần đổi password/TOTP/token hoặc dùng n8n editor cookie. External notifications, Native relation/deletion và full DR vẫn chịu blocker riêng. Tất cả approval cũ đã consumed.

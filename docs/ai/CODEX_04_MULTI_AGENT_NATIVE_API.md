> Current Main 2026-10-26T12:26:49.046792+00:00: Gatewayffe20cad/Core545e498a/WF10142d0a0d-0c12-4b6d-b1f5-c91033fc854e. Registered-only vector pruning and explicit WBS relations deployed/qualified.581Windows/566Linux+15skips;73roles/48contracts/13readonly/38hierarchy/6QAreads + unchanged canonical42 smoke PASS.1731points incl3legacy, Native/history unchanged. Full release PARTIAL; see CODEX_RAG_REGISTERED_PRUNING_FINAL_READBACK.json and CODEX_FINAL_REGRESSION_RELEASE_GATE.md. Older milestones below are historical.

CURRENT MAIN — 2026-10-26T08:04:33.762688+00:00: Gatewayb2f2db56/Coree0a840b5; trusted Native delete contract deployed with empty ledger. Fresh518Windows/503Linux+15skips/15Ruby;73roles/48contracts/13readonly/40new delete policy checks PASS.338visible/375physical/original332/#370v2/security/history preserved. No Main Native write/human decision/model call. Full release PARTIAL; read CODEX_FINAL_REGRESSION_RELEASE_GATE.md and CODEX_MAIN_CONTINUATION_CHECKPOINT.json. All sections below are historical evidence.

CURRENT MAIN WEB — 2026-10-25T03:13:28.471356+00:00: Core Web `sha256:1bbe160472068a64d3a965fe2bbbd280c2095d17ce285785a3ad0df40825a61f`, Gateway `sha256:c0f328216654478cb58dc01dad737958416882f0352c450a0ae5a80438ca6372`. Chỉ1controller file được bổ sung wbs_from_ba/QA capture/read/prepare vào route và selector theo role; Gateway cùng9container Main khác giữ nguyên ID/image/start. QA review vẫn là endpoint human review riêng, không có qa_review/qa_pass AI command.6Ruby programs PASS, gồm actual controller6roles,42valid/42wrong-role edges, ActionView/XSS và signed test receipts. Postdeploy48contracts/73roles/13read-only/Native375/oldtree/RAG/fullNative-security preservation PASS. Không thêm Native write hoặc model call. New visual selector human UAT PASS: người dùng xác nhận Owner thấy wbs_from_ba/qa_evidence_get/qa_transition_prepare và không thấy qa_evidence_capture; không chạy browser automation hoặc gửi lệnh. Evidence: CODEX_OWNER_NEW_TOOLS_HUMAN_UAT_RESULT.json. Current full release PARTIAL. Các image Core dcb60182 bên dưới là bằng chứng trước Web-only delta này.

CURRENT — 2026-10-24T22:17:45.531409+00:00: Gatewayc0f32821/Core dcb60182, Main338 (#375v0 exact approved create; old337 unchanged),433Windows/421image+12platform,48contracts/73roles/36QA/13read-only PASS. Overall PARTIAL. See CODEX_FINAL_BUSINESS_ACCEPTANCE_REPORT.md and current checkpoint. All sections below are historical unless explicitly current.

Cập nhật hiện hành 2026-10-24T14:33:05.542398+00:00: Gateway `sha256:21ad074d2b51a9332850986a1673ffc894a99d8a99707ecef1f1445996a0e724`, Core `sha256:dcb6018226280bde73fb8812e463bdcb5ef6896cbe9a1c65be7516d993f4a3d4`; Main337, original333 exact rows/#370v2 giữ nguyên. Owner supported access và actual3-level Native tree/RAG PASS; overall PARTIAL. 374Windows/367image+7Node skips;48contracts/73role/13finalread-only PASS. Xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json và CODEX_FINAL_REGRESSION_RELEASE_GATE.md trước các đoạn lịch sử bên dưới.

<!-- CODEX_CURRENT_STATUS -->
Trạng thái hiện hành và giới hạn nghiệm thu: xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json, CODEX_SCENARIO_F_RESULT.json và CODEX_MAIN_WORKFLOW_ACCEPTANCE_MATRIX.json trong docs/ai. Các số liệu/candidate bên dưới là lịch sử.
<!-- END_CODEX_CURRENT_STATUS -->

# Codex — Multi-Agent và Native API

**Status: PARTIAL.** Đọc source, SQLite receipts/runs và Native Main; chưa fresh full Gemini generation hoặc mutation E2E.

## Phân biệt các năng lực

- `planner.py` + `supervisor.py`: local deterministic routing/handlers, bounded DAG; kết quả ghi rõ local và model_used=false.
- `live_agents.py` + `gemini.py`: structured model outputs, hạn chế model/HTTP calls, có receipts/usage và retry429/503 có giới hạn. SDK runtime2.30.1; không phải1.53.0 như báo cáo cũ.
- `ai_worker.py`: business tool worker riêng. Candidate P0 chỉ tạo proposals cho model writes.
- `service.py` + `native.py`: authenticated caller, native project/role, lockVersion, forms, readback và idempotency. Model suggestions không phải quyết định PM.
- `reviewer_agent.py`: kiểm tra references/versions/consistency; không chứng minh đã chạy code/test chỉ bằng lời review.

Run `5472f53d-7aa7-4cdb-b3e4-474752dfac88` có execution_mode LIVE_GEMINI và **1 QA generateContent**; provider usage3165 tokens, có countTokens receipt. Agent outputs là QA+Reviewer. Không chứng minh sáu agent đều Gemini hoặc full shared tool execution. Các run mới hơn trong snapshot là local PM+Reviewer, model_used=false. Hiện `dev` gộp FE/BE; PM/BA/QA/Reviewer có handlers nhưng chưa đủ role-specific UAT.

## Native read và write

Native read thật xác nhận actor 19/PM/project5,332 WP. Không dùng PostgreSQL để thay đổi business. Native writes/source markers/optimistic locking/readback/recovery có regression fixture; không gọi mutate trên WP38 hoặc task nghiệp vụ để kiểm chứng.

Approval candidate: proposal pending → PM exact decision → fresh role/policy → Native write → readback. **RAG sync và VERIFIED_COMPLETED chưa được nối/kiểm chứng**, nên endpoint/schema không tuyên bố full completion. Timeout sau remote write giữ failed_or_unknown; không tự gửi POST/PATCH lại.

Changed files P0: `gateway/{app,service,store,ai_worker,catalog}.py`, `openapi.json`, `mcp-tools.json`; source UI controller/view bỏ auto-write checkbox. Test commands và outcomes trong CODEX_05. Runtime image và Native data chưa thay đổi.

Remaining risk: cross-actor proposal handoff cho BA→PM chưa có contract hoàn chỉnh; persisted tool registry dùng RAG production còn thiếu vector; create/update/comment/transition E2E qua n8n chưa được duyệt trên tài nguyên riêng. Không suy token counts thành billing-free proof mới.

Rollback: pin image cũ, giữ credentials đã revoke và mutation disabled; không rollback Native data hoặc state database. Chỉ triển khai sau preview/approval P0; full Native E2E cần phê duyệt riêng ID test resource, loại thao tác và cleanup.


## Native relation projection deployed — 23/10/2026

FreshdetailGETWP49/50đãembeddedrelations2/4vàHTTP200;listcorpuskhôngembeddedkhôngchứngminhdetailAPIthiếu. Giảthuyếtfetchbugbịbácbỏ,bảnServicefetchcandidatebỏvàkhôngdeploy. LỗithậtđãREDtrênservingbase:LiveAgentscontextkhôngfieldrelations. Image40137d60chỉoverlaylive_agents.py,đưatype/from_id/to_idvàomodelcontext,khôngrawrelationdescription,title,externalIDs. CurrentservingmoduleSHAkhớpsource. NativePM/BAcontextAPI200,isolatednewimageprojectionvớiNative49/50inputthậtcó2validedges;stubproviderkhôngGoogle.201Linux/200PASS/1skip;45relatedWindowsPASS. Providerreceipts96/usage101và332WPfingerprintkhôngđổi. KhôngcoiđâylàfreshGemini/six-roleproof. CODEX_CONTEXT_DEPLOYMENT_RESULT.json.

NativecontrolledE2Epreviewhash862c99e3dd0251275cf04154b3b86b55603a12b992ffd99a675d3ffb0f255528:formPOSTvalidatewithoutcommitPASS,chưaNativebusinesswrite. OwnerquestionđangpendingtheomụcG;khôngdùngWPcũlàmmutationfixture.

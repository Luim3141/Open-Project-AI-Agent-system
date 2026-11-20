CURRENT MAIN — 2026-10-26T08:04:33.762688+00:00: Gatewayb2f2db56/Coree0a840b5; trusted Native delete contract deployed with empty ledger. Fresh518Windows/503Linux+15skips/15Ruby;73roles/48contracts/13readonly/40new delete policy checks PASS.338visible/375physical/original332/#370v2/security/history preserved. No Main Native write/human decision/model call. Full release PARTIAL; read CODEX_FINAL_REGRESSION_RELEASE_GATE.md and CODEX_MAIN_CONTINUATION_CHECKPOINT.json. All sections below are historical evidence.

<!-- QA_REVIEW_UI_CURRENT -->
## Main human QA review — 2026-10-25T03:36:33.562329+00:00

**Scoped deployment PASS; full release PARTIAL.** Gateway `sha256:8c91c1c0ae3edf754615b302575d093fa45b5257ffa0b86f84d7872830a3c3ec`, Core Web `sha256:175c337834cabb5e56689432cbb913e5dc4ef622d77b7e3e49d16333cdab85e2`. AI Assistant → AI Control Center → **Bằng chứng QA / Kiểm duyệt** opens the separate human review page. User confirmed the page/ID input/read button; final navigation button is qualified by actual ActionView six-role rendering, not a claimed browser click. PM/Owner review uses their own session, Rails CSRF, signed nonce, fresh Native identity, independent reviewer, exact source/hash and one-decision CAS. QA reads/captures their own evidence; BA/BE/FE and other Admins gain no approval authority. There is no review AI/MCP tool and no automatic Native write.

434 Windows tests,422 Linux tests(+12 platform cases passed on Windows),8Ruby programs,73role API checks,48contracts,13read-only checks and10signed bridge negative checks PASS. All67 serving Gateway sources and5changed Core templates/controller/routes match workspace. All375 physical WP rows and338Main versions remain exact;370v2 unchanged. ScenarioF consumed row/61audit rows/original RAG report, old history IDs and two unknown request rows are retained. No new provider receipt, proposal, QA decision, Native write, credential change or Staging operation. RAG338IDs/373docs/1728chunks/1731points remains consistent; three historical excluded points retained.

Actual371 next Native edge is NEW→IN ANALYSIS, not NEW→REVIEW. Existing Core policy still requires story, AC, scope evidence and scope approval; current records are empty. No evidence or approval was invented. Genuine Main QA production/independent review/valid closure remains incomplete, along with versioned Native dependency writes, trusted deletion and full recovery. See [qualification](CODEX_QA_REVIEW_UI_QUALIFICATION.json), [runtime preservation](CODEX_QA_REVIEW_UI_FINAL_READBACK.json), [Native readiness](CODEX_WF11_CURRENT_NATIVE_READINESS.json). Roll back only exact previous service images/config; retain current databases and prior fixes.
Typed decision input validation was separately regression-tested and deployed Gateway-only; no policy weakening. QA23 currently advertises comments but no attachment upload link; the V1 producer gap and proposed alternative are recorded in CODEX_WF11_QA_PRODUCER_CAPABILITY_RESULT.json and CODEX_WF11_NATIVE_QA_PRODUCER_DESIGN_PREVIEW.md. No upload/write was attempted.
<!-- END_QA_REVIEW_UI_CURRENT -->

CURRENT MAIN WEB — 2026-10-25T03:13:28.471356+00:00: Core Web `sha256:1bbe160472068a64d3a965fe2bbbd280c2095d17ce285785a3ad0df40825a61f`, Gateway `sha256:c0f328216654478cb58dc01dad737958416882f0352c450a0ae5a80438ca6372`. Chỉ1controller file được bổ sung wbs_from_ba/QA capture/read/prepare vào route và selector theo role; Gateway cùng9container Main khác giữ nguyên ID/image/start. QA review vẫn là endpoint human review riêng, không có qa_review/qa_pass AI command.6Ruby programs PASS, gồm actual controller6roles,42valid/42wrong-role edges, ActionView/XSS và signed test receipts. Postdeploy48contracts/73roles/13read-only/Native375/oldtree/RAG/fullNative-security preservation PASS. Không thêm Native write hoặc model call. New visual selector human UAT PASS: người dùng xác nhận Owner thấy wbs_from_ba/qa_evidence_get/qa_transition_prepare và không thấy qa_evidence_capture; không chạy browser automation hoặc gửi lệnh. Evidence: CODEX_OWNER_NEW_TOOLS_HUMAN_UAT_RESULT.json. Current full release PARTIAL. Các image Core dcb60182 bên dưới là bằng chứng trước Web-only delta này.

CURRENT — 2026-10-24T22:17:45.531409+00:00: Gatewayc0f32821/Core dcb60182, Main338 (#375v0 exact approved create; old337 unchanged),433Windows/421image+12platform,48contracts/73roles/36QA/13read-only PASS. Overall PARTIAL. See CODEX_FINAL_BUSINESS_ACCEPTANCE_REPORT.md and current checkpoint. All sections below are historical unless explicitly current.

Cập nhật hiện hành 2026-10-24T14:33:05.542398+00:00: Gateway `sha256:21ad074d2b51a9332850986a1673ffc894a99d8a99707ecef1f1445996a0e724`, Core `sha256:dcb6018226280bde73fb8812e463bdcb5ef6896cbe9a1c65be7516d993f4a3d4`; Main337, original333 exact rows/#370v2 giữ nguyên. Owner supported access và actual3-level Native tree/RAG PASS; overall PARTIAL. 374Windows/367image+7Node skips;48contracts/73role/13finalread-only PASS. Xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json và CODEX_FINAL_REGRESSION_RELEASE_GATE.md trước các đoạn lịch sử bên dưới.

<!-- CODEX_CURRENT_STATUS -->
Trạng thái hiện hành và giới hạn nghiệm thu: xem CODEX_MAIN_CONTINUATION_CHECKPOINT.json, CODEX_SCENARIO_F_RESULT.json và CODEX_MAIN_WORKFLOW_ACCEPTANCE_MATRIX.json trong docs/ai. Các số liệu/candidate bên dưới là lịch sử.
<!-- END_CODEX_CURRENT_STATUS -->

# Codex — Security remediation

**Status: PARTIAL / production P0 BLOCKED chờ phê duyệt vận hành.** Source đã sửa và có regression; Main vẫn đang phục vụ image cũ.

## Sự cố đã xác minh

- Secret webhook trong `FINAL_BEHAVIORAL_RELEASE_GATE_REPORT.md` trùng private config hiện hành. Probe vào WF05 với UUID không tồn tại: thiếu secret→403 ingress; secret lộ→qua ingress, downstream500. Không gọi mutation.
- Bearer PM/BA hardcoded trong source vẫn có record token còn hiệu lực. Cookie Owner n8n bị hardcode vẫn đọc `/rest/workflows` được200.
- Credential n8n `DBWkxwb2izrbu17C` được đọc qua CLI export có kiểm soát: header Authorization đúng bằng một Bearer PM bị lộ. Không đưa plaintext ra report/log.
- Tái hiện runtime: BA 20 đọc trace PM 19 trực tiếp Gateway→403; cùng BA 20 qua WF04+n8n→200, lộ10 events của run `9492b7f7-0fa4-449d-a122-5e6af4119bcd`. Không ghi WP.
- Fixture trước sửa chứng minh `auto_execute=true` ghi mà không duyệt, và thay payload trong SQLite không bị phát hiện khi confirm.

## Root cause và thay đổi

1. `gateway/service.py`: từ chối client auto_execute; native write sau confirmation phải là PM; thêm `decide_proposal` cho quyết định REST xác thực theo caller, exact hash, own proposal.
2. `gateway/store.py`: `BEGIN IMMEDIATE`, rehash payload thật trong transaction, claim một lần và trả đúng payload vừa claim. Ngăn đổi payload giữa read và execution.
3. `gateway/app.py`: `POST /api/v1/proposals/{id}/decision` nhận duy nhất `decision` và `hash`; không tin actor/role/approved trong body. Không thêm MCP confirmation tool.
4. `gateway/ai_worker.py`: model chỉ tạo proposals, không dùng consent checkbox để auto-write. Failure sau write vẫn UNKNOWN, không blind retry.
5. `automation/deploy_real_n8n_workflows.py`: candidate dựa trên **nodes live** để giữ các sửa WF11 và cấu hình hiện hữu; bỏ shared PM credential ở mọi Gateway node; chuyển Authorization từ header của chính request; tắt lưu execution payload chứa credential; không retry writes; không follow redirect. WF05 chỉ preview, WF06 gửi exact decision vào Gateway. Cron không có human context bị disable trong candidate, chờ service identity đọc chuyên biệt.
6. UI controller/view và catalog/OpenAPI đã cập nhật source. UI core **chưa deploy**; Gateway sẽ từ chối checkbox cũ sau khi deploy candidate.
7. Gỡ plaintext đã biết ở11 file source/report; thay token/cookie bằng environment lookup. Snapshot forensic nằm ngoài repository với ACL LUIM/SYSTEM.

## Kiểm tra

`tests.test_takeover_security`: unapproved, rejected, expired, fake actor/hash, altered payload, role change, stale lock, concurrent approval, replay, response loss; thêm REST anonymous/BA/spoof rejection và PM exact-hash success trên fixture.

`tests.test_takeover_workflows`: kiểm tra credential/header forwarding, redirect, retention và WF06 không nhận raw mutation. Đây là static/fixture tests, **không phải live n8n E2E**. Tổng regression hiện hành xem CODEX_05.

Quét exact secret đã biết: Git reachable history không có match; 10.000 dòng log gần nhất mỗi Main Gateway/n8n không có match. Kiểm tra SQLite/Qdrant corpus không có exact secret đã biết. Đây không phải cam kết không tồn tại mọi loại secret chưa biết hoặc trong backup lịch sử.

## Việc cần phê duyệt

Xem exact preview `CODEX_SECURITY_DEPLOY_PREVIEW.json`: rotate webhook credential; revoke các Gateway Bearer PM/BA đã lộ; invalidate cookie Owner lộ bằng n8n `/rest/logout` rồi đọc lại401; deploy candidate Gateway và16 workflow auth changes. Native API tokens, mật khẩu, TOTP và dữ liệu WP không đổi. PM/BA clients và n8n Owner có thể phải đăng nhập/enroll Bearer lại.

Installed n8n `AuthService.invalidateToken` ghi invalid token vào repository khi logout; không chỉ xóa cookie trình duyệt. Nếu revoke/readback không thành công, giữ mutation webhook dừng và báo BLOCKED, không tuyên bố credential đã vô hiệu.

Rollback: giữ maintenance/mutation workflows bị khóa khi có lỗi, đổi lại image code được pin nếu cần; không hồi sinh credential bị lộ và không restore đè SQLite. Backup nhất quán đã có, nhưng full Main restore chưa nghiệm thu. Không gọi release GO khi P0 chưa được sửa trên runtime.

Thiết lập không lưu execution payload được đối chiếu với [n8n workflow settings](https://docs.n8n.io/build/manage-workflows/configure-workflow-settings.md). CLI export đọc credential dùng đúng flags trong [n8n Server CLI](https://docs.n8n.io/deploy/host-n8n/configure-n8n/use-the-command-line.md); plaintext export chỉ được xử lý trong private operator storage.

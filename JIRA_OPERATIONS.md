# JIRA OPERATIONS — QLDAPM / QAG3

Cập nhật 2026-10-09. Đây là playbook, không phải cấu hình Jira đã triển khai hoặc lệnh CLI được đăng ký. Authority: [AGENTS.md](AGENTS.md); khả năng phiên: [JIRA_CAPABILITIES.md](JIRA_CAPABILITIES.md); trace: [JIRA_MCP_AUDIT.md](JIRA_MCP_AUDIT.md).

## 1. Đích và quy tắc bất biến

- Workspace thật: `D:\AI project\QLDAPM chat`.
- Site: https://luimjiraqldapm.atlassian.net; cloudId 560ef0cc-d24b-4613-98d3-d541afe8f32b.
- Target QAG3 / 10002; Scrum board 3 / filter 10002; Sprint 1 future. Đọc lại trước mọi lệnh ghi.
- Không ghi KAN/SAM1, không tạo project trùng QAG3, không tự thêm Story/Bug type.
- Ngân sách 0; không cài add-on, trial hoặc đổi gói. Không dùng REST/server khác để vượt MCP.
- Snapshot hiện có trong [checkpoint](JIRA_PROGRESS_CHECKPOINT_2026-10-09.md). Ba workflow riêng chưa kích hoạt; 23 E2E chưa chạy. Chưa có automation hay WBS mới trên QAG3.

## 2. Chu trình chuẩn và approval

**Preflight → đọc hiện trạng → draft → preview → duyệt → thực thi đúng tool → đọc lại → report.**

1. CLI read-only khi cần: `codex mcp list`, `codex mcp get atlassian`. Không in config chứa secret.
2. Gọi identity/resources thực; xác minh site. Discover đúng một mục đích mỗi query, đọc schema hiện tại; pass cloudId cấp ngoài.
3. Nếu auth hỏng: dừng ghi; người dùng tự hoàn tất OAuth. Kết nối chính thức khác chỉ dùng khi xác minh độc lập.
4. Với write: trình target, source IDs, before/after, số item, role, thay đổi scope, rủi ro và rollback; chờ approval cụ thể. Không suy từ “full quyền” ra quyền xóa/HR.
5. Chạy từng lô nhỏ. Timeout sau create không retry mù: tìm lại source label/key rồi đối soát. Đọc hết pagination trước kết luận toàn bộ.
6. Khi có partial failure, giữ kết quả đã thành công, chỉ retry phần lỗi sau kiểm tra. Ghi operation name/route và read-back.
7. Không tự gán Done khi chưa có test/acceptance evidence. Không coi ticket tạo thành công là code hoàn tất.
8. UI fallback phải công bố trước và được duyệt khi cần. Link editor chỉ là review; rule native Subtask không kiểm tra toàn bộ Task của Epic.

Mẫu preview:
```text
Target / route / tool:
Số item và key/source ID:
Before → After:
Parent / assignee accountId / dates / labels giữ lại:
AC và bằng chứng:
Tác động / rollback:
Giới hạn và nội dung xin duyệt:
```

## 3. Blueprint project — draft trước khi tạo

Nếu người dùng thực sự yêu cầu dự án khác: chốt tên/key/Scrum/company-managed, timezone, scope, owner, DoR/DoD; list project kiểm tra trùng. Discover createJiraProject; nếu không được expose, trình fallback chứ không dùng createProject của Atlassian Projects.
Chuẩn bị issue types, roles, board/filter, components, estimation, dependency, notification, version và workflow scheme riêng; preview/approval trước tạo. Sau đó đọc lại key/ID/style, board, statuses, membership. Không nói tạo xong chỉ dựa toast UI.
Đối với công việc đang dở, **tiếp tục QAG3**, không tạo dự án mới.

## 4. WBS và traceability

Nguồn đã duyệt: 53 User Story/11 Epic, bỏ Burndown. Hierarchy: Epic → nhiều Task chức năng đầu-cuối → Subtask phần việc cá nhân. Mỗi Task lưu Story ID, câu User Story, AC và checklist. Không nhân đôi cùng Story thành cả Story issue và Task issue.

| Vai trò | Đầu ra Subtask phù hợp |
| --- | --- |
| BA | Quy tắc nghiệp vụ, AC, edge cases, wireframe/flow được duyệt |
| BE | Logic/API, quyền, dữ liệu/migration nếu cần, xử lý lỗi và test |
| FE | Màn hình, state loading/empty/error, validation, tích hợp/accessibility |
| Tester/QA | Test case, execution, bug evidence, retest/regression |
| PM | Scope, dependency, risk/plan, acceptance và bàn giao |

Không mặc định mỗi Task có đủ 5 Subtask nếu không có đầu ra riêng; cũng không chia toàn bộ thành nút/ô nhập thiếu giá trị nghiệm thu. Fix Bug theo yêu cầu bài tập là Subtask dưới Task gốc, assign Dev có trách nhiệm, QA retest. Không có Bug type QAG3 hiện tại.

Trường tối thiểu: source ID duy nhất, summary, business value, AC, owner thật nếu xác minh, priority được duyệt, estimate/capacity chưa biết để trống, dependency, parent, checklist/evidence. Chưa tạo CSV trong bootstrap.

Trước import: JQL đúng QAG3 theo `source-<ID>`; 0 match đề xuất create; 1 match đọc/diff; >1 dừng xử lý trùng. Giữ labels/components hiện có. Tạo Epic trước, resolve key thật, Task rồi Subtask; import mẫu đã duyệt, kiểm tra parent/type/AC/assignee trước toàn bộ. Trace requirement → issue → PR/commit → test → release. Không chế key/author/worklog.

## 5. Phân công năm người

Email và vai trò chủ dự án đưa nằm ở checkpoint: BE nguyenduc6325@gmail.com; QA Duyhungls2005@gmail.com; FE ttheduy1401@gmail.com; BA-PM hiepk40c@gmail.com; PM 2101minhkhai@gmail.com.
Identity của hiepk40c đã xác minh; bốn người còn lại chưa xác minh trong bootstrap.
Dùng lookupJiraAccountId khi cần tìm danh tính, listJiraIssueAssignableUsers để xác minh assignable **trong QAG3**, không coi user search là quyền assign.
Project PM role phải đối chiếu đúng người; BA-PM không tự động có quyền admin/PM chỉ vì email. Invite/role/permission cần preview tác động và approval; không gán tất cả việc vào một account để giả lập 5 thành viên.
Không tự duyệt code của mình; reviewer và bằng chứng phải rõ.

## 6. Workflow, QA và hard gates

Đặc tả duy nhất: [jira-workflows.md](jira-workflows.md). Generic AGENTS blueprint không thay kế hoạch được duyệt:

- Epic: NEW → READY → IN PROGRESS → REVIEW → DONE, CANCELLED và các cạnh trả lại/mở lại.
- Task: NEW → IN ANALYSIS → READY FOR DEV → IN PROGRESS → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → READY FOR RELEASE → DONE; có reject/bug/ReDev/Retest/Reopen.
- Subtask: NEW → IN PROGRESS → REVIEW → DONE; Rework/Reopen.
- Task REVIEW: Lead review → retest nếu cần → BA xác nhận → PM duyệt; deploy chỉ môi trường Test tập trung, không mặc định Production.

Trước publish/map: đọc đúng workflow/scheme ID, dependencies và phạm vi dùng; snapshot trước; preview mapping Epic/Task/Sub-task, PM-only, reason fields, Resolution đặt/xóa, gate child/QA/checklist. Xin duyệt; không sửa scheme dùng chung.
Không activate khi gate Epic rỗng/Task chưa Done chưa được bảo đảm theo yêu cầu. Codex pre-check không phải gate server-side nguyên tử; automation sau Done không phải validator trước Done.
QA phải có expected/actual/env/repro/severity/evidence; còn bug chưa sửa/retest thì không đánh dấu đạt.
Rollback: tắt rule mới trước, đối soát mapping/status rồi xin phép khôi phục scheme QAG3; không xóa issue hay sửa KAN.
Chạy đủ T01–T23 của đặc tả bằng PM và non-PM thật, replay/concurrency, scope snapshots; ghi key/actor/run ID/results. Bootstrap chưa chạy các test đó.

## 7. Board, Sprint và phạm vi

Board 3 đã có, không tạo thêm mặc định. Discover/get board config trước bố trí cột/WIP; field/type/permission chưa có thì báo rõ.
Sprint 1 future, chưa có goal/dates. PM chốt mục tiêu, lịch timezone, ngày nghỉ, giờ khả dụng thực do nhóm cung cấp, review/QA/carryover, complexity/dependencies và buffer. Không suy capacity từ 8h/ngày hoặc point→giờ.
Preview backlog/issues/assignee/estimates và committed snapshot trước start. manageJiraSprint đi theo execute-family được catalog chỉ định; **update có thể clear các field bị bỏ qua**, phải gửi lại field cần giữ; close một chiều, cần duyệt riêng.
Theo dõi WIP/blockers/scope change qua MCP; không tự bật lịch nền khi chưa có yêu cầu recurring.
Thêm/bớt Task phải có PM scope approval; Epic REVIEW/Done nhận việc chưa Done cần xử lý theo đặc tả. Sửa câu chữ không mở lại.
Tiến độ hiện tại không ghi đè snapshot cam kết hoặc đánh giá Sprint đã chốt; không cộng đôi Task/Subtask.

## 8. Automation, release và báo cáo

A01–A05 trong đặc tả hiện là hợp đồng, chưa có rule thật. Discover lại operation read/write automation; thiếu thì trình UI hoặc integration cần ủy quyền riêng. Kiểm tra miễn phí/quota thực trước quyết định, không chế quota.
Rule chỉ QAG3; kiểm tra type/parent/status/phạm vi, dữ liệu đầy đủ, actor ít quyền, re-fetch, idempotency/no-op, audit, không auto Epic Done và không ping-pong. Exactly-once/concurrency phải test, không hứa bằng fresh-read đơn thuần.
Read version qua getJiraProjectVersions; manageJiraProjectVersion phải preview/approval release/move unresolved, read-back. Tách deploy Test khỏi phát hành thật.
Report tổng hợp từ dữ liệu phải nêu snapshot/nguồn/missingdata; listJiraDashboards chỉ là metadata, không lấy gadget metrics. Không tạo dashboard bằng entity property.
Review riêng tư theo [SPRINT_REVIEW_TEMPLATE.md](SPRINT_REVIEW_TEMPLATE.md), chỉ khi người dùng yêu cầu. Không xếp hạng/HR; không chia sẻ/saving review cá nhân khi chưa duyệt.

## 9. Prompt alias có thể dùng trong chat

| Câu gửi Codex | Hành vi |
| --- | --- |
| /jira-health | Preflight và audit kết nối thật, chỉ đọc |
| /jira-audit QAG3 | Kiểm kê cấu hình/data/rủi ro, chỉ đọc |
| /jira-bootstrap QAG3 | Draft/preview; ghi chỉ sau duyệt |
| /jira-sprint-plan QAG3 | Đề xuất goal/scope/capacity/phân công, không auto start |
| /jira-sprint-review QAG3 1 | Thu evidence thật, draft riêng tư; thiếu dữ liệu không chấm |
| /jira-workflow-check QAG3 | Đọc trạng thái/gates, đề xuất; không tự publish |
| /jira-sync ISSUEKEY | So Jira với code/test, trình diff cần duyệt |

Đây là prompt alias để diễn giải, không phải slash command đăng ký trong app, background daemon hoặc API endpoint.

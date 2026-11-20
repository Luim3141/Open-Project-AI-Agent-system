# QAG3 — nghiên cứu revision gate (2026-10-10)

## Kết luận và phạm vi

Checklist hiện tại **không đáp ứng** actor-bound review, revision-bound retest và invalidation sau rework. Không coi đây là gate đã hoàn chỉnh. Hướng nhỏ nhất đáng khảo sát: giữ các expression gate hiện có; dùng lịch sử Jira làm nguồn actor/rework, evidence có revision rõ ràng; chỉ cân nhắc function validator đọc dữ liệu nếu expression không đủ. Đây là findings/khuyến nghị, không phải thay đổi kiến trúc hay phê duyệt triển khai.

Chỉ đọc `AGENTS.md` và `forge/qag3-validator/manifest.yml` trong dự án. Manifest có 5 expression validators, runtime `nodejs24.x`, không khai báo scopes/function/storage/egress; delivery checklist chỉ kiểm tra lựa chọn và evidence text, description cũng phủ nhận việc xác thực reviewer/retest. `development 2.1.0` là thông tin người dùng cung cấp, không phải deployment đã xác minh. Không kết nối Jira/MCP, không đọc credentials hay file dự án khác, không ghi ngoài file này. Skill `research` đã đọc; không có công cụ background subagent nên nghiên cứu trực tiếp, không tạo chat thay thế.

## 1. Validator và input — đã xác minh

- `jira:workflowValidator` hỗ trợ `function` **hoặc** `expression` cho mỗi validator; module còn ở Preview.
- Expression: `user` là actor chuyển trạng thái; `issue` chứa pending transition-screen changes; `originalIssue` là trước thay đổi, không có ở initial transition. Context còn có `project`, `transition`, `workflow`, `config`.
- Function payload: `issue.key`, `configuration`, `transition.from/to`, `transition.modifiedFields`. Không có `originalIssue`/changelog được tài liệu hóa trong payload. Muốn baseline/history phải đọc riêng; REST không thay thế pending input.
- `modifiedFields` cần **`read:jira-work`**; gồm các field types được liệt kê, không mặc định mọi field. Array bị xóa thành `null`; user field chỉ trả `accountId`. Kết quả: `{result, errorMessage}`.

Nguồn: [Workflow validator: expressions/context](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/#context-variables), [lambda/modifiedFields/scopes](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/#validating-with-lambda-functions).

Function nhận `(payload, context)`; `context.principal?.accountId` là identity do nền tảng cung cấp nhưng `principal` optional. Thiếu identity phải chặn; cần thử thực tế validator trước khi dựa vào nó. Không nhận reviewer từ field tự nhập. [Function arguments](https://developer.atlassian.com/platform/forge/function-reference/arguments/#context-schema).

## 2. Pure expressions và native validation

Expression **có lịch sử**: `issue.changelogs` mới nhất trước; `getNewestChangelog(field, filters)`; changelog có `id`, `author`, `created`, `items` với `fieldId/from/to`. Có `issue.links[].linkedIssue`, `new Issue(...)`, và `user.getProjectRoles(project)`. Đọc role người khác cần quyền admin thích hợp; issue không tồn tại/không nhìn thấy có thể trả `null`. [Type reference](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/#issue), [User](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/#user), [Changelog](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/#changelog).

Native có role/permission conditions, previous-status và separation-of-duties; conditions không kiểm tra pending screen input, validators mới làm việc đó. Chúng hữu ích để giới hạn actor, nhưng danh mục không chứng minh retest đúng artifact/revision. Không suy ra “đã từng qua QA” nghĩa là QA cho revision hiện tại. [Advanced workflows](https://support.atlassian.com/jira-cloud-administration/docs/configure-advanced-issue-workflows/).

Expression chạy phía Jira, không phải JavaScript tùy ý gọi HTTP/ghi ledger. Giới hạn: 10 expensive operations, 50.000 steps, 10.000 ký tự; xử lý collection lớn có thêm giới hạn/chi phí. Không cắt lịch sử rồi mặc định PASS khi thiếu dữ liệu. [Expressions/restrictions](https://developer.atlassian.com/cloud/jira/platform/jira-expressions/#restrictions).

**Suy luận:** expression có thể xác thực actor của transition lịch sử và bỏ qua review trước lần rework gần nhất, nếu đã có sự kiện review/rework đáng tin và evidence revision rõ ràng. Tuy nhiên `originalIssue` chỉ là baseline của transition này, không phải snapshot lúc review; pending transition chưa phải lịch sử đã commit. Checkbox, user-picker, URL hay text không tự chứng minh người review hoặc test đã chạy. Expression/native không tự tạo provenance, thu thập kết quả test, hay chứng minh nội dung artifact bên ngoài.

## 3. REST scopes — chỉ nghiên cứu, chưa yêu cầu quyền

Đối chiếu [OpenAPI chính thức](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130) do REST docs liên kết; trang Issues quá lớn cho web reader nên parse OpenAPI công khai trong bộ nhớ, không lưu thêm file.

| Đọc | Endpoint và scope |
| --- | --- |
| History đầy đủ | `GET /rest/api/3/issue/{issueIdOrKey}/changelog`: classic `read:jira-work`; granular `read:issue-meta:jira`, `read:avatar:jira`, `read:issue.changelog:jira`. Phân trang, cũ nhất trước. [Get changelogs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get). |
| Issue/linked target | `GET /rest/api/3/issue/{issueIdOrKey}?fields=...`: classic `read:jira-work`; granular được endpoint liệt kê: `read:issue-meta:jira`, `read:issue-security-level:jira`, `read:issue.vote:jira`, `read:issue.changelog:jira`, `read:avatar:jira`, `read:issue:jira`, `read:status:jira`, `read:user:jira`, `read:field-configuration:jira`. Không giả định chỉ `read:issue:jira` đủ. [Get issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get). |
| Link cụ thể | `GET /rest/api/3/issueLink/{linkId}`: classic `read:jira-work`; granular: `read:field:jira`, `read:issue-link-type:jira`, `read:issue:jira`, `read:issue-type:jira`, `read:priority:jira`, `read:status:jira`, `read:avatar:jira`, `read:issue.time-tracking:jira`, `read:project-category:jira`, `read:project:jira`, `read:user:jira`. [Get issue link](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-linkid-get). |

Scopes không thay thế Browse Projects/issue security; linked issues cần quyền xem hai phía. Scope đọc không bị giới hạn riêng QAG3: code vẫn phải kiểm tra project của issue và từng linked target; từ chối đọc ngoài QAG3. Endpoint link không đảm bảo trả đủ evidence fields; đọc target riêng khi cần.

Nếu được duyệt sau này, Forge `requestJira` hỗ trợ `asApp()` và tự gắn authorization; không cần API token thủ công. App identity không phải reviewer identity; không tự suy ra `asUser()` dùng được trong validator. [requestJira](https://developer.atlassian.com/platform/forge/apis-reference/fetch-api-product.requestjira/).

## 4. Route nhỏ nhất khả thi — đề xuất có điều kiện

1. Trước hết kiểm tra khả năng biểu diễn bằng expression trên **sự kiện có provenance**, không bổ sung checkbox: review Lead/QA/BA/PM phải gắn actor thật của hành động, role/account được duyệt, target revision và evidence. Mapping actor/role hiện chưa xác minh; không hard-code danh tính giả.
2. Revision phải là định danh artifact/build/commit hoặc requirements baseline đáng tin, không chỉ `issue.updated`. Xác định tập thay đổi làm mất hiệu lực: rework/reopen, scope/AC/code/build và linked defect/evidence có liên quan. Gate chỉ nhận review/retest đúng revision và sau invalidation; thiếu/không xác định thì FAIL. Không cần xóa lịch sử cũ: giữ audit, chỉ loại khỏi quyết định hiện tại.
3. Nếu phải phân trang history, phối hợp linked evidence hoặc xử lý dữ liệu vượt expression budget: đề xuất một function validator dùng chung, đọc Jira, ghép baseline với `modifiedFields` theo field semantics (kể cả `null`), fail closed khi thiếu history/quyền/evidence. `read:jira-work` là candidate scope phục vụ cả pending fields và các REST reads trên; không tự thêm storage/egress/write scope.
4. Function đọc-only **không tạo evidence đáng tin từ hư không**. Nếu QAG3 chưa có actor-recorded review events và nguồn test results bảo vệ được khỏi sửa giả, cần preview riêng cơ chế ghi nhận/provenance. Không triển khai function rồi tuyên bố đủ yêu cầu. Retest do QA chứng thực có actor khác với bằng chứng test runner thực thi; phải chốt mức bằng chứng cần đạt.

Đây là khuyến nghị nghiên cứu, không sửa workflow/source/architecture. Budget0: không add-on/trial, deploy/install/upgrade hoặc scope consent trước **preview + human approval**. Nếu không chứng minh được route đáp ứng ngân sách và provenance, báo gate chưa hỗ trợ, không hạ chuẩn sang manual claims.

## 5. Chi phí, concurrency và việc chưa xác minh

- Forge hiện tính consumption, vượt allowance có overage; functions có 200.000 GB-seconds/app/tháng, logs 1 GB/tháng. Usage tính cả development/staging/production; **development không đảm bảo miễn phí**. Chưa kiểm tra billing/usage hiện tại hay hard spending cap; không cam kết chi phí 0. [Pricing](https://developer.atlassian.com/platform/forge/forge-platform-pricing/).
- Runtime thông thường tối đa 25s. Docs công bố rate limits user-led 1.200/min/user, 7.000/min/install và 300/s/install; đây không phải số concurrent validators được bảo đảm, cũng chưa xác nhận cách phân loại invocation này. Jira REST có rate limits riêng. [Invocation limits](https://developer.atlassian.com/platform/forge/limits-invocation/), [Platform limits](https://developer.atlassian.com/platform/forge/platform-quotas-and-limits/).
- Chưa có bằng chứng transaction/snapshot atomic giữa REST reads, linked issues và transition commit. Hai actor/rework đồng thời có thể gây TOCTOU; re-read giảm rủi ro nhưng không chứng minh loại bỏ race. Không ghi approval/evidence trong validator trước commit: transition có thể thất bại bởi rule khác. Cần kiểm thử retry/duplicate, concurrent retest–rework, pending revision sửa cùng transition, actor giả/sai role, old evidence replay, history pagination, 403/429/timeout, links bị đổi và initial transition thiếu baseline.
- Chưa kiểm chứng live: active workflow bindings, review/rework transition IDs, fields có mặt trong `modifiedFields`, `principal` tại invocation thật, quyền đọc lịch sử/linked issues, trusted revision/evidence source, coverage mọi đường edit/reopen/bypass và role tại thời điểm review. Không có live test hay deployment trong nghiên cứu này; skill fallback không thay thế kiểm chứng.

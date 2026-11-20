# Jira Free — admin limits và Epic→Task gate

Ngày nghiên cứu: 2026-10-09. Bounded sidecar theo skill `research`; đã đọc AGENTS.md, jira-management.md và jira-workflows.md tại thư mục authoritative. Không gọi Jira/MCP Atlassian, không browser UI, không đọc credential/key, không tạo integration/code; chỉ ghi file này. Skill yêu cầu background agent nhưng phiên không có công cụ subagent, nên nghiên cứu trực tiếp.

`DOCS` = tài liệu chính thức Atlassian; `SUY LUẬN` = hệ quả có giới hạn; `ACTUAL SITE: UNKNOWN` = không xác minh tại site. Không dùng checkpoint cũ làm bằng chứng hiện trạng; live discovery/preflight thuộc công việc người dùng đang làm.

## 1. Mời 5 người, không mặc định là thêm 5 seats

- **DOCS:** Jira Free tối đa 10 users/site. **SUY LUẬN:** chỉ cấp thêm access cho account còn thiếu, sao cho tổng users/site ≤10; nhóm 5 người không tự chứng minh còn đủ chỗ. [Explore Jira Cloud plans — Free user limit](https://support.atlassian.com/jira-cloud-administration/docs/explore-jira-cloud-plans/).
- **DOCS — thao tác cho admin, chưa thực hiện:** centralized management: Atlassian Administration → chọn organization → Directory → Users → Invite users → nhập email → chọn Jira/site và app role cần thiết → Invite users. Organization admin hoặc user access admin của app được mời; original management dùng site Admin → Invite → Users. Chọn quyền User thông thường khi chỉ cần cộng tác, không tự cấp admin. Email có account sẵn dùng account đó; email chưa có sẽ được hướng dẫn tạo account. [Invite a user](https://support.atlassian.com/user-management/docs/invite-a-user/).
- **DOCS:** app-access role lúc invite khác Jira project role; PM/BA/BE/FE/Tester không tự trở thành project permissions chỉ vì đã invite. [User management và app-level permissions](https://support.atlassian.com/migration/docs/user-management-differences-in-cloud-and-server/).

## 2. Company-managed Free: roles ≠ workflow customization

- **DOCS:** Free không cho assign project/space roles, cấu hình issue security schemes hoặc hạn chế permissions qua schemes. Roles/schemes có từ downgrade/migration được giữ nhưng không sửa được. **SUY LUẬN:** không thể coi kế hoạch gán mới 5 project roles và permission scheme riêng là khả năng Free đã được bảo đảm. [Permissions limitations in Free Jira sites](https://support.atlassian.com/jira-cloud-administration/docs/permissions-and-issue-level-security-in-free-plans/).
- **DOCS:** site luôn ở Free thì mọi người có Jira access là admin của mọi project/space, không đồng nghĩa organization admin. **SUY LUẬN:** PM-only cần phân biệt hạn chế transition với khả năng thành viên sửa cấu hình; không hứa phân quyền chặt chỉ bằng nhãn vai trò. [What is the Free Jira Cloud plan?](https://support.atlassian.com/jira-cloud-administration/docs/what-is-the-free-jira-cloud-plan/).
- **DOCS:** bảng pricing Atlassian liệt kê customizable workflows ở Free; không đồng nhất giới hạn permission scheme với cấm mọi custom workflow. Conditions có lựa chọn assignee, group, user custom field và project role; tài liệu tổng quát này không bảo đảm từng lựa chọn khả dụng/an toàn ở site Free cụ thể. [Pricing — customizable workflows](https://www.atlassian.com/en/software/jira/pricing), [Advanced workflows — conditions](https://support.atlassian.com/jira-cloud-administration/docs/configure-advanced-issue-workflows/).
- **DOCS:** workflow scheme ánh xạ work types tới workflows; sửa active scheme tạo draft, phải publish để có hiệu lực. Link/editor hoặc workflow Inactive không chứng minh đã áp dụng vào project. [Configure workflow schemes](https://support.atlassian.com/jira-cloud-administration/docs/configure-workflow-schemes/).

## 3. Epic→Task hard gate: chưa chứng minh, không kết luận bất khả thi

- **DOCS:** `Sub-Task Blocking Condition` chặn cha theo trạng thái **subtasks**; editor mới đặt tên `Restrict based on the status of subtasks`. Epic có Task/Story/Bug, còn Task có Subtask. **SUY LUẬN:** không suy rộng gate Task→Subtask thành gate Epic→Task. [Advanced workflows](https://support.atlassian.com/jira-cloud-administration/docs/configure-advanced-issue-workflows/), [Workflow editor mapping](https://support.atlassian.com/jira-cloud-administration/docs/what-is-the-new-workflow-editor/), [Work types và hierarchy](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/).
- **DOCS:** validator kiểm tra trước khi transition hoàn tất; thất bại thì không tới destination status. **SUY LUẬN:** yêu cầu hiện tại cần kiểm tra Task không rỗng, tất cả DONE, PM hợp lệ và dữ liệu hiện thời trước nghiệm thu, kể cả thêm/reopen/reparent đồng thời. Những tài liệu đã đọc chưa chứng minh native Free rule đáp ứng toàn bộ điều này; cũng không chứng minh mọi phương án miễn phí đều không thể đáp ứng. [Edit workflow rules — Validate details](https://support.atlassian.com/jira-cloud-administration/docs/edit-an-issue-workflow/).
- **DOCS:** Automation `Work item transitioned` chạy khi status đã chuyển. **SUY LUẬN:** rule đổi ngược trạng thái sau DONE không tương đương pre-transition hard gate; cờ all-done được cập nhật trước đó cũng chưa chứng minh tính nguyên tử. [Automation triggers](https://support.atlassian.com/cloud-automation/docs/jira-automation-triggers/).

## 4. Official MCP supported-tools: catalog, không phải live proof

Đối chiếu trang catalog cập nhật 2026-09-30; mỗi hàng chỉ mô tả tài liệu, không phải operation đã gọi.

| Nhu cầu | DOCS catalog |
|---|---|
| Invite user / cấp Jira access | Không liệt kê operation invite. [Supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/) |
| Gán project role / sửa permission scheme | Không liệt kê operation tương ứng. [Supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/) |
| Đọc workflow | Có `getJiraWorkflows`, gồm statuses/transitions/gating rules. [Supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/) |
| Ghi/publish workflow hoặc workflow scheme | Có `getJiraWorkflowEditorLink`: prefilled change để review, không áp dụng; không liệt kê publish/mapping scheme operation. [Supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/) |
| Jira Automation CRUD/enable/audit | Không liệt kê operation quản lý Automation rules. [Supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/) |

**DOCS:** `manage_jira` mặc định disabled; runtime phụ thuộc auth/scopes/groups/app access, deferred tools qua `discover`. Catalog không thay live proof. [Supported tools — dynamic availability](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/).

**USER-REPORTED, không phải sidecar verification:** main đã xác minh local/hosted MCP thiếu invite/role/publish/automation; đang chờ xác nhận UI ngoại lệ, chưa có authority quản trị. Sidecar không kiểm tra lại hoặc thực hiện thao tác.

## 5. Vượt user limit: nguy cơ đổi gói và phát sinh phí

- **DOCS có khác biệt diễn đạt:** pricing nói vượt 10 users tự vào Standard trial 7 ngày; licensing nói email billing/technical contacts và nâng Standard sau 7 ngày nếu không giảm users. Không coi đây là cam kết thời điểm chính xác cho site. [Pricing — Free trial details](https://www.atlassian.com/en/software/jira/pricing), [Cloud licensing — exceeding Free limit](https://www.atlassian.com/licensing/cloud).
- **DOCS:** billing guide mô tả Standard trial khi chủ động upgrade là 14 ngày; không tính phí trước trial end. Không có payment on file: >10 users thì subscription bị deactivated, ≤10 thì về Free. Vì vậy không được nói “vượt limit chắc chắn bị trừ tiền ngay” hoặc “không có thẻ thì không có rủi ro”. [Manage subscription](https://support.atlassian.com/subscriptions-and-billing/docs/manage-your-bill-for-standard-and-premium-plans/).
- **DOCS:** paid monthly dựa trên số Jira users, annual theo tier; không chỉ thu phí phần users vượt 10. **SUY LUẬN:** ngân sách 0 phải giữ tổng access ≤10, không kích hoạt trial/plan change. Không báo giá hay khoản tiền site sẽ bị thu khi chưa biết subscription/billing state. [Pricing — billing users](https://www.atlassian.com/en/software/jira/pricing).

## 6. Lựa chọn tối thiểu cần người dùng quyết định

1. **Invite:** quyết định có cho phép UI ngoại lệ để admin mời người còn thiếu, quyền User, chỉ khi tổng users/site ≤10; không tự thu hồi access. Cơ sở: [Invite users](https://support.atlassian.com/user-management/docs/invite-a-user/), [Free limit](https://support.atlassian.com/jira-cloud-administration/docs/explore-jira-cloud-plans/).
2. **Gate:** khuyến nghị giữ yêu cầu hard gate và chưa nghiệm thu/rollout phần chưa chứng minh. Hoặc người dùng phê duyệt rõ việc đổi sang PM kiểm tra thủ công/soft automation; lựa chọn sau là thay đổi yêu cầu, không được gọi là hard gate đạt. Không đề nghị mua/trial, không tạo integration, không tự thay hierarchy. Cơ sở phân biệt pre/post transition: [Validate details](https://support.atlassian.com/jira-cloud-administration/docs/edit-an-issue-workflow/), [Automation trigger](https://support.atlassian.com/cloud-automation/docs/jira-automation-triggers/).

**ACTUAL SITE: UNKNOWN:** plan và lịch sử downgrade, số Jira-access users/seats, invitation/accountId/assignability, quyền admin/PM, roles/schemes, workflow active/publish, rule availability, Automation quota/actor/audit, payment/trial state và concurrent gate behavior. Sidecar không chạy lại discovery/preflight/E2E; không có kết luận triển khai thành công.

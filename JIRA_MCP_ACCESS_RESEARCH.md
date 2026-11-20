# Kết nối và phạm vi quản lý Jira qua MCP

Cập nhật 2026-10-09 (+07). Site: https://luimjiraqldapm.atlassian.net; cloudId `560ef0cc-d24b-4613-98d3-d541afe8f32b`. Mục tiêu mới gồm bot giám sát định kỳ trên máy người dùng. Đây là bằng chứng/giới hạn, không phải cam kết toàn quyền.

## 1. Xác minh phiên thực tế

Route: MCP chính thức `atlassian`; không Browser Use, REST Jira hay server bên thứ ba.

| Kiểm tra | Tool thực gọi | Kết quả |
| --- | --- | --- |
| Danh tính | atlassianUserInfo | accountId `712020:0d04982c-00bf-46af-b3a7-446d0f44edfb` |
| Site/product | getAccessibleAtlassianResources | Đúng site/cloudId, Jira và Artifacts advertised read-write; không chứng minh mọi thao tác ghi |
| Smoke test | discover; executeRead → listJiraProjects(query=QAG3) | QAG3/10002, classic; isLast=true |
| Issue baseline | searchJiraIssuesUsingJql(project=QAG3) | issues=[], isLast=true |
| Workflow đang áp dụng | executeRead → listJiraStatuses | Epic/Task/Sub-task đều To Do/In Progress/Done; chưa 6/10/4 |
| Artifacts | executeRead → listArtifacts | artifacts=[]; chưa upload/publish; lỗi create HTTP400 trước đó chưa có evidence đã sửa |

Authentication/read: **VERIFIED**. Admin/full control: **PARTIAL / NOT VERIFIED**. Primary create/edit/transition/comment được expose nhưng phiên này chưa thử ghi. KAN/SAM1 không bị ghi.

## 2. Phân biệt quyền và giới hạn công cụ

Danh mục MCP phụ thuộc authentication, scopes, nhóm quyền tổ chức và app access. `manage_jira` mặc định tắt; nhóm này có đọc workflow, project/screen administration. `getJiraWorkflowEditorLink` chỉ chuẩn bị link để review, **không áp dụng thay đổi**. Danh mục công bố không có operation ghi/publish workflow scheme hoặc quản lý Jira Automation rule; chưa được coi là hỗ trợ full administration. [Atlassian — Supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/).

Trong phiên này, discover `getJiraWorkflows`, workflow editor, workflow scheme/automation/member và MCP permission groups không trả thao tác đúng mục đích; searchable175/316. Kết quả gần nghĩa về Confluence permissions/Atlassian Teams không cấp quyền Jira. **Không có lỗi 403 hoặc đọc cấu hình nhóm quyền thực**, vì vậy chưa kết luận admin group trên site chắc chắn tắt.

MCP chỉ hoạt động theo danh tính và quyền được cấp, không tăng quyền chỉ vì người dùng đã đăng nhập Jira trong browser. [Atlassian — Authentication and authorization](https://developer.atlassian.com/cloud/rovo-mcp/guides/authentication-and-authorization/).

## 3. Bước quản trị cần người có quyền xác nhận

Atlassian hướng dẫn organization admin mở **Atlassian Administration → Rovo → Rovo MCP server → Permissions**, xem trạng thái và chi tiết theo app. Thiết lập tại đây ưu tiên hơn Connected Apps/Marketplace; thay đổi quyền có hiệu lực ngay. [Atlassian — Configure MCP permissions](https://support.atlassian.com/security-and-access-policies/docs/configure-atlassian-mcp-server-permissions/).

Kiểm tra Jira Read/Write/Search và khả năng bật nhóm `manage_jira` cho scope quản trị cần thiết; không chọn Allow all/future additions hoặc bật delete mặc định. Ghi lại giá trị cũ để rollback. Đây là **đề xuất kiểm tra**, chưa có thao tác thay quyền trong phiên này. Không yêu cầu mua gói, gửi token/password hay tắt bảo mật.

Sau khi admin xác nhận thay đổi: discover lại và thử read `getJiraWorkflows` nếu được expose; preview riêng từng mutation. Nếu vẫn không có workflow publish/scheme/automation tools thì tăng scope không tự tạo thêm API. Cần thống nhất integration cụ thể hoặc thay đổi phạm vi, không giả vờ UI/REST là MCP. Người dùng đã cho phép khảo sát/cài API/MCP cho bot, nhưng bot đọc hiện tại không cần integration khác.

## 4. Ngân sách và thiết kế bot

Không gọi semantic search/Teamwork Graph hoặc công cụ sinh Remix có mức Rovo credits được công bố; dùng JQL và Jira read trực tiếp. Không suy ra quota/billing Jira của site từ quota Codex. [Atlassian — Supported tools, credit notes](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/).

Bot dùng lịch Codex local và MCP outbound đã kết nối; không cần public tunnel/container chỉ để đọc Jira. Lịch local cần máy bật, app chạy và project còn trên disk; thiết lập lịch không chứng minh một scheduled run đã thực thi. [OpenAI — Scheduled tasks](https://learn.chatgpt.com/docs/automations?surface=app).

Hướng dẫn triển khai/baseline: [JIRA_BOT.md](JIRA_BOT.md). Giới hạn Free/gates có điều kiện, actual site plan UNKNOWN: [JIRA_FREE_WORKFLOW_RESEARCH.md](JIRA_FREE_WORKFLOW_RESEARCH.md). Không thay hard gate Epic–Task bằng automation hậu kiểm.

## 5. Chưa đạt và điều kiện tiếp tục

- Chưa xác minh đọc mọi dữ liệu, mọi quyền ghi/admin, site plan hoặc organization-admin identity.
- Chưa kích hoạt workflow/scheme/gates/Automation A01–A05; 23 Jira E2E vẫn NOT RUN.
- Bốn thành viên còn lại chưa resolve/assignable theo audit trước; không fake assignee.
- CSV v7 vẫn draft local; bot không tự nhập hoặc thay phạm vi.
- Upload năm bootstrap vẫn chưa xong. Không mở rộng quyền upload sang báo cáo bot/nghiên cứu.
- Scheduled execution, recovery khi app/máy tắt và báo cáo có dữ liệu thật chưa kiểm thử.

## 6. Kiểm tra lớp client, không nâng quyền — 2026-10-09

Đọc root config theo allowlist keys, không in secret: atlassian URL official v2; enabled_tools/disabled_tools không khai báo. Project authoritative không có override `.codex/config.toml`. Các khóa filter có ý nghĩa allowlist và denylist; không tìm thấy filter tại hai lớp đã kiểm tra không chứng minh mọi effective/managed policy. [OpenAI — Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference).

Đã gọi MCP qua helper local/temporary Codex app-server riêng: identity/resources/QAG3 project/JQL đều thành công và exit0, cùng account/site. Không có cuộc gọi model, API trả phí, credential copy hay thay đổi Jira/config. Vì client local thu dữ liệu được, **không cần reinstall MCP để phục vụ read bot**. Thiếu admin operations vẫn cần scope/tool enablement thực từ admin; client reconnect/install khác không tự tạo khả năng workflow publish.

Không có proof scheduled execution hoặc hoạt động khi desktop đóng. Quota snapshot ordinaryUsageAllowed=true, used60%/25%, còn40%/75%; không bị quota chặn. Không coi quota reset là cách chữa thiếu tools/admin.

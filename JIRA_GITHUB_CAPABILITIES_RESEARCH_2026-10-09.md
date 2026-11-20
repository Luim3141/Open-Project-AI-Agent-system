# Jira Cloud sidecar — GitHub capability research
Ngày: 2026-10-09. **budgets0: ngân sách 0; integration mới chưa approved.**

Chỉ đọc GitHub/API công khai tại commit ghim dưới đây; không clone/cài/chạy code bên thứ ba, không authenticated API/Jira write, không đọc secrets. LIVE TESTED = **NOT RUN** cho mọi candidate; MCP session không kiểm tra. Báo cáo source GitHub do agent nghiên cứu riêng thực hiện; phần API Atlassian và tổng hợp phương án được kiểm tra riêng.

## Kết luận cho main

Không candidate nào chứng minh “quản lý Jira Cloud đầy đủ qua MCP”. Ưu tiên nghiên cứu **atlassian-python-api/JiraCloud** làm nền SDK cho adapter admin hẹp nếu được duyệt; không phải MCP sẵn dùng. **sooperset** chỉ hợp tác nghiệp issue/agile, không lấp gap admin. **pycontribs/jira** không phù hợp làm nền admin Cloud mới. **gojira-mcp** đáng tham khảo handler, **không nên triển khai hiện tại**: UNLICENSED, chưa release, còn gap.

## Maintenance/license đã xác minh

GitHub public API xác minh default-branch HEAD và latest release (không tính prerelease); ngày UTC. Dates không chứng minh security/trust; không dùng stars.

| Repo | HEAD permalink / ngày | Latest release / published | License |
|---|---|---|---|
| sooperset/mcp-atlassian | [0a5d242](https://github.com/sooperset/mcp-atlassian/commit/0a5d2427144d72f5aade07d4fabd385421cec401), 2026-09-19 | [v0.23.1](https://github.com/sooperset/mcp-atlassian/releases/tag/v0.23.1), 2026-08-19 | [MIT](https://github.com/sooperset/mcp-atlassian/blob/0a5d2427144d72f5aade07d4fabd385421cec401/LICENSE) |
| atlassian-api/atlassian-python-api | [5291abe](https://github.com/atlassian-api/atlassian-python-api/commit/5291abe315924f66bab46f5b34a90eaf1b80aa46), 2026-10-03 | [5.0.5](https://github.com/atlassian-api/atlassian-python-api/releases/tag/5.0.5), 2026-09-15 | [Apache-2.0](https://github.com/atlassian-api/atlassian-python-api/blob/5291abe315924f66bab46f5b34a90eaf1b80aa46/LICENSE) |
| pycontribs/jira | [bf7306b](https://github.com/pycontribs/jira/commit/bf7306b8b3905c91f97401eaae61d04827e1c309), 2026-05-01 | [3.10.5](https://github.com/pycontribs/jira/releases/tag/3.10.5), 2025-07-28 | [BSD-2-Clause](https://github.com/pycontribs/jira/blob/bf7306b8b3905c91f97401eaae61d04827e1c309/LICENSE) |
| windoze95/gojira-mcp | [575a2c1](https://github.com/windoze95/gojira-mcp/commit/575a2c118b21a1dda82e4a92ea283bd0e21773aa), 2026-08-17 | [Releases](https://github.com/windoze95/gojira-mcp/releases): API trả danh sách rỗng | [package.json: UNLICENSED](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/package.json#L6) |

## Advertised → implemented (static inspection)

**1. sooperset:** README quảng bá Cloud + Server/DC. Toàn bộ [servers/jira.py](https://github.com/sooperset/mcp-atlassian/blob/0a5d2427144d72f5aade07d4fabd385421cec401/src/mcp_atlassian/servers/jira.py) có tool decorators và handlers issue/search/sprint/version; user chỉ `get_user_profile`, `search_assignable_users`. Không thấy invite/create user, role mutation, workflow-scheme mapping/publish hoặc automation-rule CRUD. `get_transitions/transition_issue` là chuyển issue, không sửa workflow. Không suy capabilities từ tên model `workflow.py`.

**2. atlassian-python-api:** SDK, không phải MCP; [JiraCloud](https://github.com/atlassian-api/atlassian-python-api/blob/5291abe315924f66bab46f5b34a90eaf1b80aa46/atlassian/jira/jira_cloud.py#L16) tách legacy JiraServer, mặc định v3. [core_methods.py](https://github.com/atlassian-api/atlassian-python-api/blob/5291abe315924f66bab46f5b34a90eaf1b80aa46/atlassian/jira/core_methods.py) thực thi:
- `create_user` L9515 → POST `rest/api/{version}/user`; chưa chứng minh gửi invitation hay cấp product access.
- `add_actor_users/set_actors/delete_actor` L7670–7746 → POST/PUT/DELETE `project/{project}/role/{id}`; có global-role CRUD.
- `set_workflow_scheme_draft_issue_type` L11128 → PUT draft mapping; `publish_draft_workflow_scheme` L11146 → POST draft/publish, `validateOnly`; có mapping non-draft và project assignment.
- Không thấy Automation Rule Management CRUD trong JiraCloud/Core/Software; workflow transition-rule configuration không phải Jira Automation.
[CloudAdmin.create_scim_user](https://github.com/atlassian-api/atlassian-python-api/blob/5291abe315924f66bab46f5b34a90eaf1b80aa46/atlassian/cloud_admin.py#L136) POST `admin.atlassian.com/scim/directory/{id}/Users`: provisioning riêng, không tự chứng minh invitation hoặc phù hợp budgets0. [Test association](https://github.com/atlassian-api/atlassian-python-api/blob/5291abe315924f66bab46f5b34a90eaf1b80aa46/tests/test_jira_cloud_clients.py#L19) dùng mock; chưa chạy.

**3. pycontribs:** SDK hỗ trợ Jira, không MCP. [client.py](https://github.com/pycontribs/jira/blob/bf7306b8b3905c91f97401eaae61d04827e1c309/jira/client.py#L5350) `add_user` POST `rest/api/latest/user`, payload legacy `name/applicationKeys/password/notification`; không Cloud-specific invitation handler. [Role.add_user](https://github.com/pycontribs/jira/blob/bf7306b8b3905c91f97401eaae61d04827e1c309/jira/resources.py#L1293) POST role resource với `user/group`; `Role.update` dùng `categorisedActors`. Cloud accountId compatibility chưa kiểm chứng. `workflows/workflowscheme` chỉ GET; không thấy dedicated mapping/publish/automation CRUD trong client/resources.

**4. gojira:** README quảng bá Cloud admin. [workflows.manage](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/src/tools/defs/workflows.ts#L199) có bulk create/update và `publishWorkflowSchemeDraft` → POST `/rest/api/3/workflowscheme/{id}/draft/publish`, polling task. [schemes.ts](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/src/tools/defs/schemes.ts) chỉ read workflow schemes; không thấy mapping/project-association writes. [projects.ts](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/src/tools/defs/projects.ts#L87) đọc roles, không mutation. [orgAdmin.manageUser/provisionUser](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/src/tools/defs/orgAdmin.ts#L195) POST `/orgs/{org}/users`: handler có thật, endpoint validity/invitation semantics cần main đối soát, không coi đã hoạt động.
[automation.ts](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/src/tools/defs/automation.ts) có GET summaries/rule, POST rule, PUT rule/state, DELETE rule; client base `api.atlassian.com/automation/public/jira/{cloudId}/rest/v1`; wrapper chọn per-user Basic API-token auth. Đây là code evidence, không chứng nhận auth/API normative.

## Exposure và gaps

Sooperset [entrypoint](https://github.com/sooperset/mcp-atlassian/blob/0a5d2427144d72f5aade07d4fabd385421cec401/src/mcp_atlassian/__init__.py#L327): stdio/SSE/streamable-http; HTTP host mặc định 0.0.0.0. Gojira [server](https://github.com/windoze95/gojira-mcp/blob/575a2c118b21a1dda82e4a92ea283bd0e21773aa/src/server.ts): bearer-protected streamable HTTP, Redis/credential-store footprint. Không thấy MCP raw-HTTP/script tool trong các tool defs đã kiểm tra; không phải security audit toàn repo. SDK [request(absolute=True)](https://github.com/atlassian-api/atlassian-python-api/blob/5291abe315924f66bab46f5b34a90eaf1b80aa46/atlassian/rest_client.py#L489) cho URL tùy ý; không expose nguyên xi qua MCP. Legacy JiraServer có ScriptRunner custom endpoints: DC/plugin, không Cloud capability.

Đối chiếu main cung cấp (không tự nghiên cứu lại): Organization v2 invite cần paid subscription; Jira create-user là legacy compatibility/org-admin; Free không cho assign project roles; draft publish async có validateOnly; Automation CRUD dùng Basic email:API-token, không hỗ trợ OAuth apps. Vì vậy code không vượt được budgets0 hoặc quyền/gói. Main cần đối soát provisionUser endpoint, migration/status mapping và rollback. Chưa dependency audit/live test. Chỉ đề xuất adapter allowlisted sau approval riêng; không thêm integration/config.

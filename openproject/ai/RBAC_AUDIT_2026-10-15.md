# RBAC audit — 15/10/2026

Phạm vi: source overlay/core v17.9.1, native REST v3, Gateway REST/MCP, Gemini executor, Boards/Backlogs, approvals và privacy. Chỉ staging 18091/18092 được thay đổi. Live 8088/8090 và Jira chỉ đọc. Không đổi credential, reset DB/volume hoặc tự triển khai live.

## AS-IS / TO-BE trước sửa code

| Bề mặt | AS-IS có bằng chứng source/checkpoint | TO-BE |
|---|---|---|
| PM | Có quyền tạo/sửa/chuyển; xóa cần local approval | Quản lý nghiệp vụ trong project, workflow và confirmation giữ nguyên |
| BA/BE/FE/QA | Checkpoint reliability đã nghiệm thu cả 5 role tạo/sửa/chuyển; roles13–16 có manage_subtasks | Chỉ đọc, phân tích, export, comment |
| Gateway | execute_actor xác thực token/user/project, nhưng chưa chặn business write theo role trước proposal; Native Mode dùng native PATCH | Chặn non-PM trước preview/idempotency và kiểm tra lại mỗi lần execute/confirm; comment có whitelist riêng |
| Gemini | Actor backend cố định; mọi role dùng cùng business write tools | Giới hạn declarations theo quyền backend; direct tool vẫn bị kiểm tra; bản đề xuất non-PM chỉ là văn bản |
| Native API/Boards | Native role permissions và GatePolicy cũ cho non-PM ghi; chưa có PM-only ceiling | Thu hẹp native roles và thêm ceiling vào native authorization/model để share/role phụ/drag-drop không cấp lại quyền |
| GatePolicy | BA/BE/FE/QA được ghi evidence, checklist, approval, transition | Chỉ PM ghi gate. Giữ independence/evidence/revision; cần PM độc lập để duyệt nếu PM là contributor |
| Identity | qldapm_actor có login whitelist, không dựa hoàn toàn membership | User active/non-admin, project membership thực; nhiều role tổng hợp dưới PM-only ceiling |
| Sessions/privacy | Bearer hash/expiry, own-user token, actor-scoped runs/proposals/history đã có | Giữ và kiểm thử hồi quy, không cho đọc hội thoại PM |
| UI | Danh sách manual tools và checkbox ghi giống nhau cho mọi role | Tool phù hợp role, thông báo read/comment-only; PM có trang Role & AI Permissions chỉ giám sát |

## Jira READ-ONLY

JIRA MCP SESSION CHECK
Site: https://luimjiraqldapm.atlassian.net | cloudId: 560ef0cc-d24b-4613-98d3-d541afe8f32b | Project: QAG3 (10002)
MCP configured: YES (server exposed; không đổi config)
OAuth/authentication checked: PASS
Actual MCP tool calls: mcp__atlassian__atlassianUserInfo, getAccessibleAtlassianResources, discover, executeRead(name=listJiraProjects)
Read-only smoke test: PASS — QAG3 / QLDAPM Agile Practice 3
Permission groups/capability tested: identity + project read. Hai discover về project roles/permission scheme không tìm được operation tương ứng; ma trận Jira NOT VERIFIED.
Computer/Browser Use: NONE
Status: PARTIAL — chỉ quyền project read được chứng minh; không suy native Jira RBAC từ workflow lịch sử. Không Jira writes.

## Kế hoạch và tác động

Đọc runtime và backup permissions trước mọi đổi role; role chỉ dùng project3 mới được đổi. Không cấp manage_members/admin/config quyền cho PM. Backend ceiling áp dụng project qldapm-local; PM project A không có quyền B. Comment-only không được kèm field updates. Native permissions vẫn là giới hạn thực tế: PM-only ceiling không tự cấp permission thiếu.

Giữ các hard gates và tách xung đột: thay actor được phép ghi bằng PM, không bỏ kiểm tra evidence/reviewer độc lập. Những approval trước đây cần BA/QA nay do PM độc lập phụ trách. Nếu chỉ có một PM đồng thời là contributor thì gate vẫn chặn self-approval; cần operator phân công PM độc lập, không tự nâng role.

Kết quả runtime, kiểm thử và các giới hạn sẽ được ghi thêm sau khi thực hiện, không xem checkpoint lịch sử là PASS mới.

## Kết quả sau triển khai

Staging project3: native ceiling + WorkPackage/custom-field/Board/Widget guards và quyền roles đã đồng bộ theo TO-BE; Gateway/MCP/Gemini dùng role thật, native effective permissions và actor-bound confirmation. Không đổi project memberships hoặc credential. Đọc [checkpoint nghiệm thu](RBAC_CHECKPOINT_2026-10-15.md) và các artifact được dẫn trong đó cho PASS/BLOCKED/NOT TESTED.

Live project5 vẫn dùng official core và roles cũ; đã audit read-only bằng Rails model thực tế, không mutate: `artifacts/rbac-live-readonly.json` (329work packages). Chính sách staging không tự bảo vệ live; rollout cần operator approval riêng. Jira chỉ project-read verified, role/permission scheme chưa xác minh.

| Runtime/role | Create WP | Edit WP | Manage Boards | Manage members |
|---|---|---|---|---|
| Live PM22 | Có | Có | Có | Có — vượt TO-BE |
| Live BA23 / BE24 / FE25 / QA26 | Có — vượt TO-BE | Có — vượt TO-BE | Không | Không |
| Staging PM12 sau thay đổi | Có | Có | Có | Không |
| Staging BA-PM13 / BE14 / FE15 / QA16 sau thay đổi | Không | Không | Không | Không |

Các role live không bị sửa vì user yêu cầu chỉ rollout live sau khi test đạt và operator phê duyệt. Backend ceiling áp dụng các đường ứng dụng và dịch vụ đã nêu; không phải database RLS cho người quản trị DB có SQL/console quyền máy chủ.

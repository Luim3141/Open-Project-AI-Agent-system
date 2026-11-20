# JIRA CAPABILITIES — QAG3, 2026-10-09

## 1. Cách đọc kết quả

Site/cloudId và trace: [JIRA_MCP_AUDIT.md](JIRA_MCP_AUDIT.md). Audit chỉ đọc trên kết nối chính thức `atlassian`.
`MCP SUPPORTED` nghĩa là operation đúng mục đích được expose hoặc discover trong phiên; cột bằng chứng chỉ rõ đã chạy hay mới advertised. Không suy ra quyền ghi từ schema hoặc quyền Jira UI.

- `UI FALLBACK`: đường UI đã quan sát trước đó hoặc đề xuất có điều kiện; không được tự thực thi. Cần MCP độc lập hoạt động, thông báo trước, duyệt tác động/rollback và đọc lại nếu có thể.
- `NOT VERIFIED`: chưa tìm thấy operation phù hợp hoặc chưa kiểm tra quyền/cấu hình; không đồng nghĩa `NO PERMISSION`.
- `NO PERMISSION`: chỉ dùng khi có lỗi/quyền bị từ chối thực tế. Audit này chưa có bằng chứng cho nhãn đó.
- `API INTEGRATION NEEDED`: chỉ là đề xuất khi bắt buộc lập trình mà MCP không có thao tác; cần ủy quyền riêng, không tự gọi REST/cài server khác. Audit này không triển khai integration.

## 2. Ma trận toàn bộ nhóm yêu cầu

| Nhóm / thao tác | Phân loại | Operation thực được expose/discover | Bằng chứng và giới hạn |
| --- | --- | --- | --- |
| Issues: đọc/tìm | MCP SUPPORTED | getJiraIssue, searchJiraIssuesUsingJql | Đã đọc KAN-68 Done, tìm QAG3 trả rỗng/isLast=true |
| Issues: tạo/sửa/comment/chuyển | MCP SUPPORTED | createJiraIssue, editJiraIssue, addOrEditJiraIssueComment, transitionJiraIssue | Primary tool expose; KHÔNG chạy ghi trong bootstrap; phải preview/duyệt |
| Epics | MCP SUPPORTED | listJiraProjects + createJiraIssue/editJiraIssue | Epic 10000 có trong QAG3; chỉ metadata được đọc, chưa tạo/đọc Epic QAG3 |
| Stories | NOT VERIFIED | createJiraIssue có khả năng chọn type sẵn có | Story không nằm trong QAG3 issue types. WBS hiện dùng Task lưu Story/AC; không nhập type giả |
| Tasks | MCP SUPPORTED | createJiraIssue/editJiraIssue; getJiraIssueTypeMetaWithFields | Task 10011, 16 create field đã đọc; chưa ghi |
| Subtasks | MCP SUPPORTED | createJiraIssue; convertJiraIssueHierarchy | Sub-task 10010 có trong QAG3; convert schema discover, chưa thực thi; parent phải đúng Task |
| Bugs | NOT VERIFIED | createJiraIssue nếu project có type Bug | QAG3 không có Bug type; phương án đã duyệt là Fix Bug Subtask, không tự thêm type |
| Projects: đọc | MCP SUPPORTED | listJiraProjects | Đã đọc đủ 3 project; QAG3 classic 10002 |
| Projects: tạo/cấu hình | UI FALLBACK | createJiraProject/updateJiraProject không xuất hiện | QAG3 tạo qua UI ở công việc trước; bootstrap không ghi. Re-discover admin khi tiếp tục |
| Boards: đọc | MCP SUPPORTED | listJiraBoards, getJiraBoardConfig | Đã đọc board 3 Scrum/filter 10002/ba cột |
| Boards: tạo | MCP SUPPORTED | createJiraBoard | Schema discover; cần filter ID hợp lệ, company-managed; chưa chạy ghi |
| Boards: sửa cột/WIP/sharing | NOT VERIFIED | Không có operation ghi đúng mục đích được xác nhận | Read config không cho phép suy ra edit board; cần khám phá lại hoặc duyệt UI |
| Sprints: đọc | MCP SUPPORTED | listJiraBoardSprints, getJiraBoardSprintData | Sprint ID 1 future; đã đọc, chưa có dates |
| Sprints: create/add/start/update/close | MCP SUPPORTED | manageJiraSprint → executeDestructive | Advertised, chưa gọi. Route chính xác theo catalog dù action=create; update có thể clear field bỏ qua, close một chiều |
| Workflows: trạng thái dự án | MCP SUPPORTED | listJiraStatuses, listJiraIssueTransitions | Project statuses đã đọc; issue transitions chưa gọi, không chứng minh mọi gate |
| Workflows: đầy đủ rule/publish/scheme | UI FALLBACK | getJiraWorkflows/getJiraWorkflowEditorLink không xuất hiện | Saved inactive workflow chỉ UI-VERIFIED theo checkpoint; chưa map/publish, không xác nhận đầy đủ gate |
| Screens: đọc/sửa | NOT VERIFIED | getJiraScreen/updateJiraScreen không xuất hiện | Đã thử query thường và tên cụ thể; chưa chạy hoặc sửa UI screen |
| Fields: create metadata | MCP SUPPORTED | getJiraIssueTypeMetaWithFields | Đọc toàn bộ 16 field Task; board Story Points 10035 không nằm trong create metadata |
| Fields: custom field mới/context/config | NOT VERIFIED | Query create Jira custom field không có operation tương ứng | Không dùng entity property giả làm custom field; chưa kiểm tra edit context |
| Roles / project membership | NOT VERIFIED | getJiraCurrentUser, lookupJiraAccountId/listJiraIssueAssignableUsers chỉ hỗ trợ identity/assignability | Current user đã đọc; chưa xác minh bốn người còn lại hoặc role PM. createTeam/updateTeam không cấp Jira project role |
| Permissions: read/edit project filter | MCP SUPPORTED | listJiraProjects action=edit | QAG3 có trả về; chỉ quyền lọc được kiểm tra, không toàn admin |
| Permissions: scheme/global scope | NOT VERIFIED | Query Jira permissions/permission scheme không có thao tác Jira phù hợp | Không có 403; không suy ra group disabled hay tự nâng scope |
| Releases: đọc | MCP SUPPORTED | getJiraProjectVersions | QAG3 trả total=0/isLast=true |
| Releases: create/update/release/archive | MCP SUPPORTED | manageJiraProjectVersion → executeDestructive | Advertised; chưa chạy. Move unresolved issue khi release không tự đảo ngược khi unrelease |
| Customizations: hierarchy/dependency | MCP SUPPORTED | convertJiraIssueHierarchy, createJiraIssueLink, createJiraIssueRemoteIssueLink | Schema discover; chưa chuyển loại/tạo link. Link không thay parent |
| Customizations: scheme/notification/config khác | NOT VERIFIED | Không có operation quản trị phù hợp được xác nhận | Chưa thay site hoặc cài add-on |
| Automation rule: read/create/update | NOT VERIFIED | Query create/list Jira automation rules không trả operation quản lý rule | Chưa bật rule, chưa kiểm tra quota/actor; có thể đề xuất UI sau duyệt, không dùng changelog thay rule config |
| Dashboards: danh sách/link | MCP SUPPORTED | listJiraDashboards | Dashboard shared project 10002 trả total=0; không đọc gadget data |
| Dashboards: tạo/gadget/edit | NOT VERIFIED | Query create Jira dashboard không có create dashboard đúng mục đích | Entity property/publishArtifact không tạo dashboard Jira |
| Reports: dữ liệu sprint/issue | MCP SUPPORTED | getJiraBoardSprintData, searchJiraIssuesUsingJql; listJiraIssueChangelogs/Worklogs | Sprint metadata đã đọc; history/worklog advertised nhưng chưa gọi. Chưa có dữ liệu để chấm |
| Reports: báo cáo Jira built-in đầy đủ | NOT VERIFIED | Query get Jira reports không có API report đầy đủ | Báo cáo tổng hợp từ evidence không đồng nghĩa report engine Jira |
| AI sprint review | MCP SUPPORTED | Đọc evidence bằng MCP + tổng hợp theo AGENTS.md | Mới có template/quy trình; chưa đánh giá cá nhân, không auto HR/ranking/publish |

## 3. Dấu vết discovery

Bảng ghi đúng các operation trả về trong top results, bao gồm cả kết quả không liên quan; không coi kết quả gần nghĩa là hỗ trợ thao tác. Primary tools không cần discover lại để gọi.

| Query đã thực gọi | Top operation trả về |
| --- | --- |
| list Jira projects | `listJiraProjects`, `listJiraProjectComponents`, `listJiraStatuses`, `getJiraProjectVersions`, `listJiraProjectIssueTypesMetadata` |
| create Jira project | `listJiraProjectIssueTypesMetadata`, `manageJiraProjectVersion`, `manageJiraProjectVersionRelatedWork`, `listJiraProjects`, `createJiraBoard` |
| get Jira workflows | `listJiraIssueTransitions`, `listJiraStatuses`, `getConfluenceApproval`, `listJiraDashboards`, `getContentFormatGuide` |
| list Jira boards | `listJiraBoards`, `listJiraBoardSprints`, `listJiraFilters`, `getJiraBoardIssueData`, `getJiraBoardSprintData` |
| list Jira board sprints | `listJiraBoardSprints`, `getJiraBoardSprintData`, `manageJiraSprint`, `getJiraBoardIssueData`, `listJiraBoards` |
| get Jira screen | `getJiraUser`, `listJiraProjects`, `getJiraCurrentUser`, `getJiraBoardConfig`, `getJiraEntityProperty` |
| list Jira fields | `getJiraIssueTypeMetaWithFields`, `listJiraIssueChangelogs`, `listJiraProjectIssueTypesMetadata`, `listJiraIssueTransitions`, `listJiraIssueRemoteIssueLinks` |
| createJiraProject | `listJiraProjectIssueTypesMetadata`, `manageJiraProjectVersion`, `manageJiraProjectVersionRelatedWork`, `listJiraProjects`, `createJiraBoard` |
| getJiraWorkflows | `listJiraIssueTransitions`, `listJiraStatuses`, `getConfluenceApproval`, `listJiraDashboards`, `getContentFormatGuide` |
| getJiraScreen | `getJiraUser`, `listJiraProjects`, `getJiraCurrentUser`, `getJiraBoardConfig`, `getJiraEntityProperty` |
| list Jira project roles | `listJiraProjects`, `listJiraProjectComponents`, `listJiraStatuses`, `getJiraProjectVersions`, `listJiraProjectIssueTypesMetadata` |
| get Jira permissions | `getConfluenceContentPermissions`, `listJiraIssueAssignableUsers`, `getConfluenceContentRestrictionState`, `updateLoomVideoPermissions`, `removeConfluenceContentPermissions` |
| create Jira automation rule | `listJiraIssueChangelogs`, `createJiraBoard`, `createJiraIssueRemoteIssueLink`, `createJiraIssueLink`, `listJiraProjectIssueTypesMetadata` |
| create Jira dashboard | `manageJiraProjectVersionRelatedWork`, `listJiraDashboards`, `editJiraEntityProperty`, `createJiraIssueRemoteIssueLink`, `getJiraEntityProperty` |
| get Jira reports | `getTalentUser`, `getJiraBoardSprintData`, `getTalentPositionsByEntity`, `listJiraIssueComments`, `publishArtifact` |
| create Jira custom field | `getJiraIssueTypeMetaWithFields`, `createJiraIssueRemoteIssueLink`, `listJiraProjectIssueTypesMetadata`, `createJiraIssueLink`, `manageJiraSprint` |
| invite Jira project member | `createTeam`, `listJiraIssueAssignableUsers`, `getJiraUser`, `updateTeam`, `searchTeams` |
| list Jira issue changelogs | `listJiraIssueChangelogs` |
| list Jira issue worklogs | `listJiraIssueWorklogs`, `addOrEditJiraIssueWorklog`, `getJiraEntityProperty`, `editJiraEntityProperty`, `listJiraStatuses` |
| list Jira issue transitions | `listJiraIssueTransitions`, `listJiraIssueChangelogs`, `listJiraStatuses`, `listJiraBoardSprints`, `listJiraProjectComponents` |
| list Jira issue assignable users | `listJiraIssueAssignableUsers`, `getJiraUser`, `lookupJiraAccountId`, `listJiraIssueTransitions`, `listJiraIssueLinkTypes` |
| convert Jira issue hierarchy | `convertJiraIssueHierarchy` |
| get Jira workflow scheme | `listJiraIssueTransitions`, `listJiraStatuses`, `getConfluenceApproval`, `listJiraDashboards`, `getContentFormatGuide` |
| update Jira project permission scheme | `manageJiraProjectVersion`, `manageJiraProjectVersionRelatedWork`, `updateCapacityPlanNonProjectWork`, `getJiraProjectVersions`, `listJiraIssueAssignableUsers` |
| list Jira automation rules | `listJiraIssueChangelogs`, `listJiraProjects`, `listJiraBoards`, `listJiraFilters`, `listJiraBoardSprints` |

Số truy vấn: 25. Mỗi lần discovery báo catalog searchableCount=175 / totalCatalogSize=316; không phải tổng quyền đã test. Danh sách có thể thay đổi ở phiên sau; phải khám phá lại thao tác cần dùng.

## 4. Phương án tiếp tục không phí

Bổ sung upload được người dùng duyệt: listArtifacts đọc thành công trả rỗng; createArtifactsUpload đã được expose nhưng thực gọi hai lần đều HTTP 400. Phân loại khả năng ghi Artifacts: NOT VERIFIED / thực thi bị chặn, không NO PERMISSION vì chưa có 403. Chưa upload/publish, không artifact link; xem JIRA_ARTIFACTS_UPLOAD.md. Đây là nhóm Artifacts, không phải khả năng ghi Jira.

Giữ QAG3, KAN không đổi; ưu tiên các thao tác issue/board/sprint được expose sau preview. Đối với admin, có thể nhờ người có quyền kiểm tra enablement MCP rồi xác thực lại; không tự bật scope. Workflow editor link, nếu được expose sau đó, chỉ là review chứ không áp dụng.
Nếu vẫn không có thao tác quản trị, trình phương án UI có điều kiện. Không tự thay gate server-side bằng kiểm tra trước từ Codex; đó là thay đổi yêu cầu cần quyết định.
Không trả phí/add-on/trial. Không có integration REST mới.
Nguồn phân nhóm sản phẩm: [Atlassian supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/); kết luận phiên dựa trên trace ở audit, không chỉ trên tài liệu.

## 5. Bổ sung mục tiêu MCP full-control và bot — 2026-10-09

Preflight mới thực gọi local atlassianUserInfo/getAccessibleAtlassianResources, discover và executeRead(listJiraProjects QAG3/listJiraStatuses/listArtifacts), searchJiraIssuesUsingJql. Đúng account/site, QAG3/10002 classic, issues=[]/isLast=true, các type vẫn3status, artifacts=[]. Không Jira write hoặc UI/REST trong phiên.

Discover exact getJiraWorkflows, editor, workflow scheme/automation/member và MCP permission groups vẫn không trả admin operation cần thiết, searchable175/316. Tài liệu mới phân biệt manage_jira mặc định tắt, OAuth/Jira permissions và giới hạn catalog; không đủ bằng chứng kết luận site đang tắt nhóm hoặc user không admin. `getJiraWorkflowEditorLink`, nếu được bật sau này, không áp dụng workflow. Nguồn và admin action cụ thể: [JIRA_MCP_ACCESS_RESEARCH.md](JIRA_MCP_ACCESS_RESEARCH.md).

Người dùng nay cho phép khảo sát/cài API/MCP cho bot; chưa triển khai API khác vì official MCP hiện đủ cho read monitoring. Không biến sự cho phép này thành quyền vượt scope, mua gói, tự nâng quyền hoặc âm thầm dùng REST thay MCP.

Bot local mỗi giờ và lịch tiếp tục sau quota đã tạo/cập nhật qua Codex App MCP, config đọc lại ACTIVE. Read monitoring manual baseline PASS; scheduled execution/admin writes/concurrency chưa test. Runbook: [JIRA_BOT.md](JIRA_BOT.md). Actual Jira plan UNKNOWN; nghiên cứu giới hạn Free chỉ là điều kiện: [JIRA_FREE_WORKFLOW_RESEARCH.md](JIRA_FREE_WORKFLOW_RESEARCH.md).

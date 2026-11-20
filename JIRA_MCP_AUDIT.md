# JIRA MCP AUDIT — bootstrap 2026-10-09

## 1. Kết luận phiên

Snapshot kiểm tra: 2026-10-09 03:28:53 +07:00 (Asia/Bangkok).
Kết nối chính thức local `atlassian` đã xác thực và đọc dữ liệu thật thành công. Bootstrap **PARTIAL** về khả năng quản trị: kết nối/read/search VERIFIED; không chứng minh toàn quyền admin hoặc quyền ghi bằng một phiên chỉ đọc.

```text
JIRA MCP SESSION CHECK
Site: https://luimjiraqldapm.atlassian.net
cloudId: 560ef0cc-d24b-4613-98d3-d541afe8f32b
Project: QAG3 / 10002 / QLDAPM Agile Practice 3
MCP configured: YES — enabled, streamable_http, official v2 endpoint
OAuth/authentication checked: PASS — actual identity + resources + Jira reads
Actual MCP tool calls: atlassianUserInfo; getAccessibleAtlassianResources;
  discover; executeRead; getJiraIssue; searchJiraIssuesUsingJql
Read-only smoke test: PASS — listJiraProjects returns QAG3; KAN-68 read as Done
Permission/capability tested: read/search PASS; QAG3 action=edit read filter PASS;
  global manage_jira/delete_jira availability NOT VERIFIED
Computer/Browser Use: FALLBACK — read-only checkpoint of existing saved Subtask editor;
  not used for bootstrap Jira operations; no UI writes
Status: PARTIAL — read connection VERIFIED; admin/write operations not fully verified
```

Local config location: `C:\Users\LUIM\.codex\config.toml`.
CLI thực chạy: `codex mcp list`, `codex mcp get atlassian`; exit 0. Server enabled, OAuth, URL `https://mcp.atlassian.com/v2/mcp`. Không sửa config hoặc gọi login; không thu thập token/password.
Công cụ MCP thực dùng có namespace `mcp__atlassian__`, KHÔNG phải browser và không dùng helper/REST để che lỗi. Plugin hosted là kết nối riêng; bootstrap không kiểm thử plugin đó.

## 2. Trace đọc thực tế

CloudId ở cấp ngoài mọi lời gọi Jira. Bảng dưới là tóm tắt kết quả thật, không phải log giả lập; chỉ liệt kê operation đã thực thi.

| Tool / operation | Tham số chính | Kết quả |
| --- | --- | --- |
| atlassianUserInfo | {} | accountId 712020:0d04982c-00bf-46af-b3a7-446d0f44edfb |
| getAccessibleAtlassianResources | {} | Đúng site/cloudId; Jira access read-write được khai báo |
| executeRead → listJiraProjects | startAt=0, maxResults=100, expand=issueTypes,lead | KAN 10001, QAG3 10002, SAM1 10000; total 3, isLast=true |
| getJiraIssue | issueIdOrKey=KAN-68, view=compact | ID 10077; status Done; updated 2026-10-08T19:37:27.228+0700 |
| searchJiraIssuesUsingJql | project = QAG3 ORDER BY key ASC; maxResults=100 | issues=[], isLast=true; không có issue trả về trong phạm vi quyền hiện tại |
| executeRead → listJiraBoards | projectKeyOrId=QAG3; startAt=0, maxResults=100 | QAG3 board ID 3, scrum; total 1, isLast=true |
| executeRead → listJiraBoardSprints | boardId=3; startAt=0, maxResults=100 | QAG3 Sprint 1, ID 1, future; total 1, isLast=true; chưa có dates |
| executeRead → getJiraBoardConfig | boardId=3 | filter 10002; To Do / In Progress / Done; Story Points customfield_10035 |
| executeRead → listJiraStatuses | mode=project, projectKey=QAG3 | Epic/Task/Sub-task đều chỉ có To Do 10008, In Progress 3, Done 10009 |
| executeRead → getJiraProjectVersions | projectIdOrKey=QAG3; startAt=0, maxResults=100 | total 0, isLast=true |
| executeRead → listJiraDashboards | projectId=10002; startAt=0, maxResults=100 | total 0, isLast=true; đây là dashboard chia sẻ cho project, không phải toàn site |
| executeRead → getJiraCurrentUser | {} | hiepk40c, hiepk40c@gmail.com, active=true, Asia/Bangkok |
| executeRead → getJiraIssueTypeMetaWithFields | QAG3, issueTypeId=10011, startAt=0, maxResults=200, requiredFieldsOnly=false | total 16 field; đã phủ hết. Required: project, issuetype, summary |
| executeRead → listJiraProjects | query=QAG3, action=edit, startAt=0, maxResults=100 | QAG3 trả về; chỉ chứng minh bộ lọc quyền edit project, không phải mọi admin action |
| executeRead → getJiraBoardSprintData | boardId=3, sprintId=1, includeIssues=false | Đọc lại Sprint 1 future, không lấy dữ liệu để chấm cá nhân |

Không có lời gọi executeWrite/executeDestructive/create/edit/transition/comment trong bootstrap. `access=read-write` và công cụ được expose không đồng nghĩa mọi lệnh ghi đã được kiểm thử.

Đích demo đọc: [KAN-68](https://luimjiraqldapm.atlassian.net/browse/KAN-68) — key đã nhận từ Jira. Không thay đổi KAN.

## 3. Discovery và giới hạn

`discover` được thực gọi với 25 truy vấn Jira, gồm các từ khóa có khoảng trắng và tên cụ thể để kiểm tra lại operation không xuất hiện. Catalog trả searchableCount=175, totalCatalogSize=316; đây là số của catalog nhiều sản phẩm, không phải 175 quyền Jira đã kiểm thử.

Truy vấn và các operation chính trả về được lưu trong [JIRA_CAPABILITIES.md](JIRA_CAPABILITIES.md). Không chọn các kết quả Confluence/Talent/Atlassian Projects làm thay thế cho Jira admin. Đặc biệt `createProject` không phải `createJiraProject`; `updateTeam` không phải cấp membership/role dự án Jira; entity property không tạo dashboard.

Không tìm thấy `createJiraProject`, `getJiraWorkflows`, `getJiraScreen` hoặc operation sửa workflow scheme trong các kết quả discovery hiện tại. Không gọi tên đoán được hoặc thử REST để vượt scope. Không có lỗi 403 chứng minh tài khoản bị từ chối admin, nên không gắn nhãn NO PERMISSION chỉ vì operation vắng mặt.

Tài liệu chính thức cho biết nhóm manage_jira và delete_jira cần admin enablement và mặc định tắt. Đây là thông tin sản phẩm, **không phải bằng chứng nhóm trên site này đang tắt**. [Atlassian supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/).
Kiểm tra cấu hình CLI/OAuth theo [OpenAI MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli); không thực hiện thay đổi global.

## 4. Tình trạng dự án và rủi ro

- QAG3 có Epic 10000, Task 10011, Sub-task 10010; **không có Story/Bug** trong issue types trả về. Không tự thêm loại hoặc nhập chúng thay Task. WBS đã duyệt dùng Task mang Story/AC và Subtask Fix Bug; thay đổi cấu trúc cần duyệt.
- Ba workflow riêng đang Inactive theo checkpoint. Dữ liệu status project thật hiện vẫn là workflow mặc định 3 trạng thái; bootstrap không publish/map workflow.
- Board dùng Story Points customfield_10035, nhưng field này không có trong 16 field create metadata Task. Chưa kiểm tra edit context hoặc screen; không khẳng định estimate có thể ghi được ngay.
- Không có version và dashboard chia sẻ project trả về; không suy rộng là site không có dashboard.
- Chưa chứng minh PM-only, hard gate Epic–Task, snapshot hoặc automation; toàn bộ 23 Jira E2E vẫn NOT RUN.
- Năm email đã lưu, chưa mời/phân công; không suy ra membership từ email hoặc role mong muốn.
- Không đánh giá thành viên hoặc tạo fake evidence. Không phát sinh phí/add-on.

## 5. Thay đổi local và khôi phục

Trước bootstrap đã lưu [checkpoint](JIRA_PROGRESS_CHECKPOINT_2026-10-09.md) và bản cũ [AGENTS.before-bootstrap-2026-10-09.md](AGENTS.before-bootstrap-2026-10-09.md).
Nội dung D:\Download\AGENTS.md được giữ nguyên làm phần đầu AGENTS.md; phần QLDAPM được bổ sung để bảo toàn quy tắc riêng. Skill writing-for-agents hướng dẫn giữ một nguồn authority và dùng pointer; OpenAI Docs dùng để xác minh cấu hình MCP.

Xung đột được xử lý rõ:
1. Blueprint workflow tổng quát không thay kế hoạch 6/10/4 trạng thái đã duyệt.
2. Quy ước Point=giờ/8h/ngày chỉ là mô phỏng bài tập, không phải capacity hoặc hiệu suất thật.
3. Quyền quản lý rộng trước đây không thay preview/approval bắt buộc của chỉ dẫn mới.
4. Không mua app để giải quyết gate; thiếu gate phải báo giới hạn.
5. Hướng dẫn cũ về plugin/helper là lịch sử; ưu tiên MCP chính thức trực tiếp đang expose và xác minh từng phiên.

Rollback local: so sánh bản backup rồi dùng file edit khôi phục các mục cần thiết khi chủ dự án yêu cầu; không tự gỡ MCP, xóa Jira hoặc thay scheme.

## 6. Đã làm / chờ duyệt / chưa đạt

- Đã làm: checkpoint, backup, merge AGENTS, preflight CLI, identity/resources, smoke test và audit chỉ đọc, 4 tài liệu bootstrap, cập nhật pointer/trạng thái docs cũ.
- Chờ duyệt ở bước tiếp tục: phương án xử lý gate thiếu; những thay đổi quản trị/quyền, mẫu import hoặc các lô Jira ghi theo preview cụ thể. Không tạo dự án mới nữa vì QAG3 đã tồn tại.
- Không có lời gọi MCP đọc nào thất bại trong bootstrap. Operation admin cần thiết chưa được expose; không tuyên bố full admin.
- Không cài skill/plugin mới, không đổi cấu hình global, không gửi đánh giá và không ghi Jira trong bootstrap. Sau phần audit, chủ dự án yêu cầu upload năm tài liệu bootstrap lên Atlassian Artifacts; đây là bước bổ sung được duyệt riêng, dùng createArtifactsUpload/publishArtifact qua MCP. Kết quả upload được ghi riêng trong JIRA_ARTIFACTS_UPLOAD.md sau khi thực hiện; tại snapshot audit chưa có upload.

## 7. Bổ sung sau snapshot — upload do người dùng yêu cầu

Đã discover createArtifactsUpload/publishArtifact qua MCP, tính đúng byte/hash AGENTS.md và gọi executeWrite → createArtifactsUpload hai lần (UUID rồi site URL theo schema). Cả hai trả HTTP 400: `Artifacts artifact_createContent request failed.` Không có upload URL/contentId, không chuyển bytes hoặc gọi publishArtifact. executeRead → listArtifacts thành công trả artifacts=[]. Upload chưa hoàn tất; xem [JIRA_ARTIFACTS_UPLOAD.md](JIRA_ARTIFACTS_UPLOAD.md). Không có artifact link hoặc cấp share; tài liệu local đã hoàn tất. Tổng discovery gồm 25 truy vấn Jira + 2 truy vấn Artifacts; các lệnh ghi Artifacts này không sửa Jira.

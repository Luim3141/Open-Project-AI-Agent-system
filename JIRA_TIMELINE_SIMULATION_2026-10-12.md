# QAG3 — Timeline mô phỏng 2026

Lịch kế hoạch giả định cho bài tập, không phải ngày thực hiện, nghiệm thu hay năng lực nhân sự thực tế. User yêu cầu tự phân bổ đủ ngày cho 11–12 Epic và mọi Task/Subtask; scope live có 11 Epic WBS, 53 Task, 265 Subtask (329 mục), không tạo Epic mới.

## Lịch Epic nối tiếp

| Epic | Nội dung | Start date | Due date |
|---|---|---|---|
| QAG3-1 | Tài khoản & Role | 2026-08-17 | 2026-08-28 |
| QAG3-32 | Quản lý Project | 2026-08-31 | 2026-09-14 |
| QAG3-69 | Backlog | 2026-09-15 | 2026-09-25 |
| QAG3-100 | Sprint | 2026-09-28 | 2026-10-08 |
| QAG3-131 | Task / User Story | 2026-10-09 | 2026-10-21 |
| QAG3-162 | Kanban | 2026-10-22 | 2026-11-02 |
| QAG3-187 | Gantt / Timeline | 2026-11-03 | 2026-11-12 |
| QAG3-212 | Issue / Bug | 2026-11-13 | 2026-11-25 |
| QAG3-243 | Comment | 2026-11-26 | 2026-12-08 |
| QAG3-274 | Dashboard | 2026-12-09 | 2026-12-18 |
| QAG3-299 | Notification | 2026-12-21 | 2026-12-31 |

## Phân bổ công việc

- 99 ngày thứ Hai–thứ Sáu từ 17/08 đến 31/12/2026, chưa loại ngày lễ.
- Epic sau bắt đầu ngày làm việc kế tiếp sau due date Epic trước. Đây là ràng buộc kế hoạch, chưa là workflow gate/automation chặn việc bắt đầu.
- Task cùng Epic chạy cuốn chiếu. Mỗi Task: BA 1 ngày → BE và FE song song 1 ngày → QA 1 ngày → PM 1 ngày. Mỗi vai trò chỉ có tối đa một Subtask trên một ngày. Phần còn lại là đệm refinement/review; thời lượng 1 ngày là giả định học tập, không suy ra worklog/capacity thật.
- Mọi Task nằm trong khoảng Epic cha; mọi Subtask nằm trong khoảng Task cha. Start date ≤ Due date; Epic không chồng nhau.
- Ghi đúng fields: Start date/customfield_10015 và duedate, thêm nhãn simulated-timeline-2026, giữ toàn bộ nhãn cũ. Không ghi assignee/Parent/status/description/worklog/checklist/Sprint/workflow/automation.
- Description lịch sử 11/10 có ngày mô phỏng cũ được bảo toàn; Start date/Due date mới là lịch kế hoạch hiện hành. Không backdate created/updated/changelog. Trạng thái hiện tại không được tự đồng bộ với lịch này; ba Epic đầu vẫn REVIEW do lỗi validator expensive-operations đã ghi ở audit reset.

## Session và xác minh

Site https://luimjiraqldapm.atlassian.net, cloud560ef0cc-d24b-4613-98d3-d541afe8f32b, projectQAG3/10002. Official MCP atlassianUserInfo/getAccessibleAtlassianResources/getJiraIssue verified đúng owner/site/project. getJiraIssueTypeMetaWithFields xác minh Start date và Due date schema=date. Route MCP official; không browser/API supplementary.

editJiraIssue: 329 lần ghi thành công, mẫu QAG3-1 đọc lại trước bulk. searchJiraIssuesUsingJql sau ghi đủ 4 trang đến isLast=true: 329/329 mục; errors=0; mọi ngày khớp kế hoạch, status/Parent/assignee và nhãn cũ bảo toàn. VerifiedAtUtc 2026-10-11T17:22:03.664Z.

QAG3-330 được lookup trả key hiện tại KAN-69 Test A01; không phải WBS QAG3, không ghi hoặc sửa item này. KAN/SAM1/monitor/billing không thay đổi.

## Audit và phục hồi

jira-bot/timeline-simulation-2026-10-12.json lưu lịch 329 mục và observed before; trường cũ bị MCP bỏ khỏi response giữ UNKNOWN, không coi là null. Cần đọc changelog thật nếu phục hồi ngày trước bị thiếu, không tự xóa ngày dựa trên UNKNOWN. Nhãn mới có thể bỏ riêng, giữ tất cả nhãn còn lại. Ghi ngày cập nhật lịch sử Jira thật có thể làm thay đổi cửa sổ updated và các biểu đồ lịch; không phải chứng cứ tiến độ thực.

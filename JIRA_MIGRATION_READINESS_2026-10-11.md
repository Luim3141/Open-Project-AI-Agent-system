# QAG3 — dữ liệu đã hoàn thiện, migration còn chặn (11/10/2026)

## Cập nhật mới: đường switch có dữ liệu đã triển khai

`preview_scheme_switch` đã advertised/gọi thật qua registered `qag3-admin`; snapshot329 và calculatormapping trênsitePASS. Không còn blocker “project rỗng” đối với đường switch mới, assign cũ giữguard. Currentpreview0794ba52… vẫnBLOCKED vìT01–T23/PMreviewmissing, chưaapproval/apply. Independentassociation10003. Xem `JIRA_SCHEME_SWITCH_IMPLEMENTATION_2026-10-11.md`;105localtestsPASS khôngJiraE2E. Các đoạn bên dưới nói populated-tool chưaimplement là snapshot lịch sử trước thay đổi này, không kết luận mới vềAPIAtlassian.

## 1. Kết quả trên Jira

Toàn bộ dự án là **SIMULATION cho học tập**, không phải sản phẩm, công việc hay đánh giá cá nhân thật.

| Loại | Done giả định | In Progress giả định | Tổng |
|---|---:|---:|---:|
| Epic | 10 | 1 | 11 |
| Task | 49 | 4 | 53 |
| Subtask | 257 | 8 | 265 |

Tiến độ Task: **92,45%**. Đã hoàn thiện 26 mô tả/nhãn và 29 chuyển trạng thái còn gián đoạn, đọc lại đủ 329 mục qua JQL tới isLast=true. Key/type/title/Parent/assignee/status/labels/description khớp; so sánh Markdown chỉ chuẩn hóa bullet và khoảng trắng cuối dòng. Ba Task QAG3-219/225/231 được xác minh To Do trước chuyển, không ghi lại mô tả.

## 2. Worklog và điểm mô phỏng

Đã tạo **265 worklog, tổng384giờ**, chỉ ở Subtask. Đọc lại từng worklog xác nhận ID, marker duy nhất, ngày, giây, nội dung và author. Task/Epic không ghi giờ; không sửa/xóa log cũ.

Native author luôn là admin. Contributor giả định theo role ghi trong comment; không impersonate. Biểu đồ native theo author sẽ gom giờ về admin, không phản ánh công sức thật của năm người. Mỗi log có SIMULATION ONLY và marker QAG3-SIM-20261011:<issue>:worklog-v1.

Giờ kế hoạch giả định =30%giờ Junior đề xuất nguồn, làm tròn15phút; Done ghi đủ giờ giả định, InProgress ghi50% làm tròn15phút. Đây là tham số minh họa, không đổi Point thành giờ thật. Lịch S1–S5 từ07/09 đến09/10/2026, tối đa8giờ/ngày/vai trò trong bộ dữ liệu; không chứng minh trình tự triển khai/QA hoặc capacity thực. Jira created/updated vẫn là thời gian ghi thật.

| Role giả định | Giờ kế hoạch | Giờ tiêu hao | Điểm giả định/100 |
|---|---:|---:|---:|
| BA | 55.5 | 55.5 | 91.8 |
| BE | 117 | 117 | 90.4 |
| FE | 97 | 97 | 91.1 |
| QA | 88 | 85 | 90.38 |
| PM | 30.5 | 29.5 | 91.06 |

Rubric:25%Delivery+25%Quality+20%Collaboration+15%Ownership+15%Contribution. Delivery tính từ phút kế hoạch của Subtask giả định Done; bốn chiều khác là đầu vào tác giả **đặt giả định**, không phải bằng chứng QA/review thật. Không xếp hạng/HR. Công thức và từng input được lưu tại **QAG3-299/comment10004**, đã đọc lại; JSON có dữ liệu chi tiết.

## 3. Mapping329mục đã chuẩn bị

Site:https://luimjiraqldapm.atlassian.net; cloudId560ef0cc-d24b-4613-98d3-d541afe8f32b; QAG3/10002.

| Loại | Workflow đích | Version đã đọc |
|---|---|---:|
| Epic10000 | QAG3 Epic Lifecycle v1 | 7 |
| Task10011 | QAG3 Task Delivery v1 | 6 |
| Subtask10010 | QAG3 Individual Work v1 | 6 |

316Done/statusId10009 và13InProgress/statusId3. Cả ba workflow đích có đúng hai ID này: **10009→10009 và3→3**. Không chuyển tất cả về NEW. Hiện không còn To Do; NEW10010 là trạng thái đầu cho công việc mới sau activation. Mapping giữ key/type/Parent/assignee/worklog/lịch sử. Migration vào Done không kiểm chứng Deploy/Acceptance.

## 4. Migration chưa thực hiện — nguyên nhân cụ thể

- inspect_scheme cuối lượt vẫn QAG3→**10003**, target10004 chưa gắn.
- Official MCP discovery không trả association/migration workflow.
- Supplementary preview_scheme(associate_scheme,10004) trả **PROJECT_NOT_VERIFIED_EMPTY: no deletion or migration attempted**. API/công cụ chỉ hỗ trợ association project rỗng; không xóa/move329issue để né guard.
- Activation yêu cầu recorded Jira gate tests và human-approved exact preview hash. Chưa đủ T01–T23; không dùng Done/worklog/điểm giả định làm rollout-evidence.
- inspect_expression_runtime thực sự chạy10module trên QAG3-1/2/3: PM/child-Done trảtrue; reason/checklist/QA/readiness/acceptance cònfalse. Tool ghi jiraE2EVerified=false và pendingTransitionFieldsTested=false. Biểu thức không phải transition E2E.
- Quy trình hiện yêu cầu E2E trước activation trong khi workflow chưa chạy trên project: đây là **phụ thuộc ngược của thiết kế rollout hiện hành**, không phải chủ dự án thiếu quyền hay phải thêm giờ công. Cần qualification/rollout kiểm thử có giới hạn được phép trước wizard migration project có dữ liệu. Không sửa guard/proof hoặc đổi sang UI để bypass.

UI Switch Scheme đã tìm thấy ở lượt trước; không mở/thực hiện trong lượt này. Không apply_change/publish/migration/bật A01–A05, không resume monitor, không KAN/SAM1/OpenProject/billing/credential mutation. Không tạo duplicate lịch hoặc app.

## 5. Evidence và khôi phục

- simulation-resume-before-2026-10-11.json: before329.
- simulation-resume-plan-2026-10-11.json:26metadata/29transitions.
- simulation-resume-results-2026-10-11.json và simulation-resume-verified-2026-10-11.json: write và readback329.
- simulation-worklogs-scores-2026-10-11.json:265worklog ID, công thức và inputs.
- simulation-worklog-verified-2026-10-11.json:265verified,1382400giây.
- migration-mapping-draft-2026-10-11.json:mapping329,migrationExecuted=false.
Tất cả ở jira-bot; không collector/runtime/rollout schema, không ghi đè baseline/state/cursor/Sprint.

Khôi phục metadata/status cần diff hiện tại với before snapshot. Worklog/comment IDs giữ để đối soát/sửa qua yêu cầu cụ thể; không tự xóa hoặc backdate lịch sử. Comment10004 công khai với người có quyền xem QAG3-299, không gửi email/Confluence/Artifacts.

## 6. MCP session thực

Official identity/resources/full JQL PASS đúng owner/site/project. Đã gọi editJiraIssue/transitionJiraIssue/executeRead(listJiraIssueWorklogs)/executeWrite(addOrEditJiraIssueWorklog)/addOrEditJiraIssueComment và đọc lại. Supplementary inspect_scheme/inspect_workflow/inspect_expression_runtime; preview_scheme chỉ preview lỗi, không apply. Browser fallback:NONE. Data scenario:VERIFIED; workflow rollout:BLOCKED.


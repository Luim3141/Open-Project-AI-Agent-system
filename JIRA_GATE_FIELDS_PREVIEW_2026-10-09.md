# QAG3 — preview nền tảng field cho workflow gates

Trạng thái: FIELD FOUNDATION APPLIED — 09/10/2026. Ba field và Field Scheme riêng đã áp dụng QAG3; form Epic/Task/Subtask đã được official MCP đọc lại. Chưa áp dụng transition validators đầy đủ hoặc kích hoạt workflow. Target duy nhất: luimjiraqldapm.atlassian.net / cloud560ef0cc-d24b-4613-98d3-d541afe8f32b / QAG3 project10002. Các mục preview/readback cũ bên dưới là lịch sử; kết quả hiện hành tại mục sau.

## Kết quả hiện hành: field foundation đã áp dụng

- Approval: “duyệt tạo QAG3 Gate Fields v1, giữ cấu hình hiện tại, thêm ba field và áp dụng riêng QAG3”. Official MCP preflight xác minh owner/site/project; discovery không có field/screen admin operations. Ghi cấu hình bằng Jira admin UI, không gọi browser là MCP.
- Copy Default Field Scheme1 thành **QAG3 Gate Fields v1 / ID4**. Đối chiếu 60 field gốc/copy theo name/type/description/availability/required không khác. Thêm đúng ba field; scheme4 tổng63field và chỉ associated QAG3/project10002. Availability chỉ Epic/Task/Sub-task, Required on không loại nào. Không thay Default field settings/KAN/SAM1.
- `customfield_10043`: QAG3 Change reason, textarea; `customfield_10044`: QAG3 Acceptance checklist, multicheckboxes; `customfield_10045`: QAG3 Review evidence, textarea. Supplemental inspect_gate_fields exit0/readComplete=true, matchedCatalogCount3 xác minh definitions, không coi đây là kiểm tra context/screens.
- Context mặc định Global không restrict được trong UI hiện hành; giới hạn availability bằng Field Scheme riêng, không tuyên bố field definition/context chỉ tồn tại QAG3. Checklist có8option, không default tick: IDs10020–10027 lần lượt AC verified; Lead review completed; QA passed; Retest passed; Retest not required; BA accepted; PM approved; Test deployment smoke passed.
- Work type screen scheme10002 shared by1project/QAG3: Default→screen scheme10010, Epic→10011. Cả hai screen schemes dùng Default cho các operation chưa mapping, lần lượt screen10010/tab10013 và10011/tab10014. Bổ sung ba field vào cuối mỗi screen, giữ nguyên17field cũ và thứ tự; cuối cùng20field/screen. Checkbox tự thêm field vào mọi scheme sử dụng screen đã bỏ chọn trước ghi.
- Trong thao tác picker Task, UI chọn nhầm Actual end/Actual start; đã gỡ chỉ hai association vừa tạo, không xóa field hoặc giá trị issue. Readback cuối đúng17field gốc+3field QAG3, không còn association chọn nhầm.
- Official `getJiraIssueTypeMetaWithFields` đọc đủ một trang mỗi type, startAt0/maxResults200: Epic10000 total18, Task10011 total19, Sub-task10010 total19. Cả ba trả đủ IDs10043/10044/10045, required=false; checklist array/option và đúng8allowedValues/IDs. Đây là create metadata; không suy edit metadata hoặc Jira transition E2E đã kiểm thử.
- Không tạo/sửa issue values, tick checklist, ghi evidence, migrate329issue, activate workflow, bật A01–A05 hoặc resume monitor. Field availability không thay thế hard gate; reason mới, evidence revision-bound, retest và danh tính reviewer vẫn phải triển khai/kiểm thử.
- Proof: `jira-bot/qag3-gate-fields-applied-2026-10-09.png`, `jira-bot/qag3-gate-fields-screen-2026-10-09.png`. Rollback chỉ sau preview/readback/approval mới: associate QAG3 về scheme1 và gỡ ba association screen mới; không tự xóa fields/values hoặc phục hồi ghi đè cấu hình người dùng.

## Bằng chứng hiện hành

- Official MCP identity/resources/getJiraIssue QAG3-2: owner đúng, project10002/classic, status To Do10008. Một issue mẫu không phải snapshot329issue.
- getJiraIssueTypeMetaWithFields Task: total16, một trang đầy đủ; form create không có checklist/reason/retest. includeEditableFields bị experiment cohort chặn, không suy edit metadata đã đọc.
- listJiraProjectIssueTypesMetadata: total3, Epic10000/Task10011/Sub-task10010. Không có Bug. WBS v7 mô tả lỗi bằng Fix Bug Subtask; giữ mô hình hiện có, không tự thêm issue type.
- Registered supplementary MCP inspect_gate_fields: readComplete=true, matchedCatalogCount=0, fields=[]. Phạm vi là custom field có tên/description chứa QAG3, không chứng minh mọi field tên khác hoặc context/screens đã kiểm tra.
- Epic inactive v5 đã có PM và children-Done validators theo checkpoint16. Đây chưa phải checklist/reason/retest gates.

## Lô field đề xuất

| Tên | Kiểu | Mục đích |
|---|---|---|
| QAG3 Change reason | Text, nhiều dòng | Ghi lý do mới tại transition Reopen/Cancel/Restore, giữ lịch sử qua changelog. |
| QAG3 Acceptance checklist | Checkboxes | Hiển thị các mục nghiệm thu cần thiết, để validator kiểm tra đúng nhánh. |
| QAG3 Review evidence | Text, nhiều dòng | Link/ID bằng chứng review, test/retest, AC và bàn giao Test; không chứa token hoặc dữ liệu cá nhân không cần thiết. |

Các option checklist dự kiến: AC verified; Lead review completed; QA passed; Retest passed; Retest not required; BA accepted; PM approved; Test deployment smoke passed. Retest passed/not required loại trừ nhau; non-code Subtask không bị ép có code review/deploy. Các mục bắt buộc theo type/transition phải được preview trước khi gắn validator. Không tự tick hoặc điền evidence cho backlog hiện hữu.

Field definitions là tài nguyên cấp site. Chỉ context dành project10002 và ba type hiện hữu; không gắn vào screen/context dùng chung KAN/SAM1. Nếu API tạo default global context, giới hạn context của chính field mới trước khi đưa vào screen; lỗi/timeout giữ audit và không tạo lại mù. Quyền/scope API, context và screen thực tế phải kiểm tra trước apply. Không xóa/chỉnh field có sẵn nếu gặp trùng tên hoặc schema khác.

## Điều kiện bảo vệ không được bỏ

- Checkbox hoặc text do người nhập KHÔNG chứng minh đúng reviewer/PM đã duyệt; không coi ba field này là full hard gates.
- Review cần gắn người thực hiện, revision công việc và bằng chứng hiện hành. Thay nội dung/scope hoặc mở lại phải làm evidence cũ không đủ điều kiện, không xóa lịch sử.
- Reason phải có nội dung mới ngay trong lần transition. originalIssue và issue cho phép đối chiếu before/transition-screen; chỉ field nonempty là chưa đủ. Screen phải hỗ trợ nhập giá trị tại transition, không buộc sửa trước để né kiểm tra.
- Tester không hoàn tất QA khi còn Fix Bug Subtask chưa sửa/retest. DONE đơn lẻ không chứng minh retest đạt; cần predicate đọc child hiện thời và evidence phù hợp, kể cả visibility/error/limit.
- Không gắn scheme/migrate329issue/bật rule hoặc deploy manifest mới trong lô field này. Chưa thay API scope của Forge app.

## Rollback

Giữ field mới trống, chưa dùng trong validator hoặc screen: có thể dừng mà không ảnh hưởng issue. Sau khi thêm screen/context, rollback bỏ association của đúng field mới sau preview riêng; không xóa field có dữ liệu hoặc thay screen dùng chung. Không tự xóa để làm sạch trạng thái partial. Readback phải lưu fieldID/contextID/schema/options/scope; không đoán ID.

## Automation và migration

API Automation chính thức có create/update/state/template endpoints nhưng component type/value là cấu hình riêng cần lấy từ template/native rule, không đoán từ placeholder docs. Official MCP discovery hai cách không expose thao tác automation tương ứng. Supplementary hiện chưa create/edit/enable; không xem API có endpoint là tính năng đã triển khai.

Migration project có issue không dùng endpoint project-empty. Cần fresh snapshot đầy đủ và preview mapping trước thao tác UI được báo rõ; không đổi guard sang giả PASS hoặc xóa WBS.

## Nguồn chính thức đã kiểm tra

- [Field definitions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/)
- [Field contexts](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-custom-field-contexts/)
- [Forge validator context, issue và originalIssue](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/)
- [Automation rules](https://developer.atlassian.com/cloud/automation/rest/api-group-rule-management/)
- [Automation templates](https://developer.atlassian.com/cloud/automation/rest/api-group-templates/)

## Readback sau phê duyệt — 09/10/2026

- Official MCP preflight đúng owner/site/QAG3; discovery không có create custom field. Tạo qua browser fallback, không phải official MCP write.
- Đã tạo **QAG3 Change reason**, `customfield_10043`, Paragraph/rich text. Supplemental MCP `inspect_gate_fields` exit0/readComplete=true trả một definition/schema `com.atlassian.jira.plugin.system.customfieldtypes:textarea`. Không replay create khi UI báo lỗi transient sau success.
- Default Global context/configuration scheme `10147`; không default value, không thêm screen/Field Scheme, không ghi giá trị issue. Acceptance checklist/Review evidence **chưa tạo**.
- UI ghi default Global context không thể xóa/giới hạn theo work type/project; controls disabled. Không ép API vượt cơ chế mới, không tuyên bố đã restrict context.
- Site có **Field schemes** mới. Danh sách một Default Field Scheme ID1/60fields; panel Spaces liệt kê QLDAPM Agile Practice3/QAG3. Không suy ra toàn bộ screen/project đã audit.
- Phương án cần duyệt: Copy Default Field Scheme thành **QAG3 Gate Fields v1**, giữ cấu hình hiện hành; thêm ba field và giới hạn availability theo Epic/Task/Subtask; associate chỉ QAG3 sau readback copy/settings/scope. Không sửa Default scheme; nếu không bảo toàn cấu hình hoặc giới hạn được thì dừng trước association. Rollback association về scheme1 sau preview/readback riêng; không xóa field/dữ liệu.
- Form Copy đã điền để preview, **chưa bấm Copy**, chưa tạo/associate scheme. Việc copy giữ settings/60fields cần đọc lại thực tế.
- Approval mới chỉ cho field-scheme foundation, không workflow scheme10004, migration329issues, validator bổ sung hoặc automation. Field scheme khác workflow scheme.
- Ảnh: `jira-bot/qag3-field-scheme-preview-2026-10-09.png`. Nguồn: https://support.atlassian.com/jira-cloud-administration/docs/what-are-field-schemes/ (scheme kiểm soát availability/type/space; context kiểm soát content/options).

Chưa full gates/Jira E2E; giám sát giữ tạm dừng. Field đã tạo giữ unused, không tự xóa.

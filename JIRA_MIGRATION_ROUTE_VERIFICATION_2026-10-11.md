# QAG3 — xác minh đường migration và expression, 11/10/2026

## Kết quả thực tế

- Official MCP xác minh owner, site/cloudId và đọc QAG3-2 thành công.
- Bổ sung tool chỉ đọc `inspect_expression_validation()` vào supplementary MCP local: không nhận URL, expression hoặc context tùy ý; chỉ đọc manifest đã deploy, SHA256 `ba890f52fc7aca64b73d4a360571935c759986d7b52f952525e3429723af715e`.
- Gọi thật tool qua server đã đăng ký `qag3-admin`, dùng `tools/jira_mcp.py`: Jira `/expression/analyse` trả cả 10 expression `valid=true`, `allValid=true`. Đây là kiểm tra cú pháp mặc định, không phải type-check/runtime/E2E; `jiraE2EVerified=false`.
- 92 kiểm thử Python Jira regression/stdio PASS. Không deploy Forge hoặc thay cấu hình Jira trong lượt này.

## Sửa nhận định về API migration

API `PUT /rest/api/3/workflowscheme/project` chỉ áp dụng khi project không có issue, theo [tài liệu Atlassian chính thức](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-scheme-project-associations/). Vì QAG3 có 329 mục, không thể hỗ trợ migration bằng cách bỏ `empty_project()` trong gateway local. Giữ guard này; không xóa/move issue để làm project rỗng.

Browser admin fallback đã đọc đúng QAG3 qua các link hiển thị:

1. Project summary → Workflows: scheme hiện hành vẫn `QAG3: Software Simplified Workflow Scheme`.
2. `Switch Scheme` → wizard `Associate Workflow Scheme to Space`, Step 1 of 3, projectId10002.
3. Danh sách có target `QAG3 Managed Delivery v1`. Có cảnh báo backup trước association.
4. Không bấm Associate, không chọn mapping hoặc bắt đầu migration. Bấm Cancel trở lại cấu hình QAG3.

Đường UI đã tìm thấy không đồng nghĩa migration đã kiểm thử hoặc hoàn tất. Cần đọc bước mapping thực tế và đối soát snapshot key/Parent/assignee/type/status trước khi ghi. Không dùng endpoint UI chưa tài liệu hóa qua shell/REST để giả lập khả năng MCP.

## Phần chưa hoàn tất

- Lead/BA provenance và hard gate cho Fix Bug/retest chưa đầy đủ; checkbox hoặc câu tự nhập không chứng minh actor review thật.
- Chưa kiểm thử chuyển trạng thái thực tế bằng QA thật và PM độc lập; không dùng owner/bot giả danh QA, không ghi giả T01–T23 PASS.
- Thiết kế hiện yêu cầu E2E trước activation nhưng workflow chưa hoạt động; đây là phụ thuộc cần giải quyết bằng rollout kiểm thử có giới hạn, không coi syntax PASS là E2E và không tự hạ gate. Chủ dự án đã chọn gate-first, không migration với gate thiếu.
- Supplementary gateway vẫn yêu cầu chủ dự án duyệt exact preview hash trước apply. Chỉ thị tự quyết không được biến thành chữ ký/approval hash giả hoặc sửa guard để bypass.
- A01 vẫn Disabled theo readback gần nhất; A02–A05 chưa tạo/bật. Bot giám sát vẫn PAUSED theo yêu cầu, không tự khởi động lại.
- Chưa migration 329 mục, chưa chấm hiệu suất cá nhân, chưa thay đổi KAN/SAM1, OpenProject, billing hoặc credential.

## Trình tự để kết thúc rollout

Hoàn thiện các gate thiếu → thiết kế và xác nhận rollout kiểm thử giới hạn phù hợp gate-first → kiểm thử thật, kể cả hai nhánh Subtask/QA/reopen/reason/child-Done → backup và preview mapping To Do→NEW theo từng type → dùng wizard migration đúng QAG3 → đọc lại toàn bộ key/Parent/assignee/type/status → cấu hình/kiểm thử A01–A05 trước enable → đối soát và bàn giao. Không ghi mọi bước là đã đạt chỉ từ tài liệu hoặc unit test.

## Nguồn

- [Jira expression analysis](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-jira-expressions/): phân tích cú pháp; type-check là tùy chọn experimental.
- UI đã quan sát: `https://luimjiraqldapm.atlassian.net/plugins/servlet/project-config/QAG3/workflows` và link Switch Scheme dẫn tới `https://luimjiraqldapm.atlassian.net/secure/project/SelectProjectWorkflowScheme!default.jspa?projectId=10002`.

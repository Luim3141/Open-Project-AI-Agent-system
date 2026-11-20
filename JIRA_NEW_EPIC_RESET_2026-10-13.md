# Đồng bộ NEW dưới ba Epic — 13/10/2026

## Kết quả

QAG3 / 10002, site https://luimjiraqldapm.atlassian.net, cloud560ef0cc-d24b-4613-98d3-d541afe8f32b. Official MCP identity/resources/getJiraIssue preflight PASS đúng owner; không dùng browser thay kết nối MCP lỗi.

| Epic giữ NEW | Task về NEW | Subtask về NEW |
|---|---:|---:|
| QAG3-243 — Comment | 5 | 25 |
| QAG3-274 — Dashboard | 4 | 20 |
| QAG3-299 — Notification | 5 | 25 |
| Tổng | 14 | 70 |

84/84 mục được official MCP full readback xác minh NEW; JQL resolution is not EMPTY trả0/isLast=true. Mỗi mục giữ summary/type/Parent/labels/assignee/Start date/Due date theo so sánh before/after. Các Epic còn lại đọc lại giữ nguyên trạng thái; không gửi mutation tới chúng.

## Thực hiện và sửa lỗi

Official listJiraIssueTransitions cho thấy Done chỉ Reopen→IP, IP không có đường NEW. Discover workflow update không có operation. Browser admin fallback thêm **tạm** Reset simulation backlog: Done/IP→NEW, validator PM allowlist có sẵn + fresh Change reason + native Parent NEW, screen10010, clear Resolution. Giữ mọi transition/gate nghiệm thu/routing/layout cũ; không thêm quyền hoặc sửa Forge source.

Task reset trước, Subtask reset sau để Parent NEW đạt gate. Ghi issue bằng official transitionJiraIssue, lấy transition ID thực cho từng issue ngay trước chuyển. Lý do đầu plain string bị400; sửa thành ADF theo response rồi thành công. Không tạo comment/note ở backlog; reason ghi trên transition theo gate bắt buộc. Lịch sử, description mô phỏng, checklist/evidence/worklog cũ giữ nguyên, không xóa hoặc giả làm lịch sử mới.

Sau hoàn tất, browser gỡ đúng hai transition do lượt này tạo và Update workflow; supplemental independent read kiểm tra từng original transition theoID, bỏ UUID rule volatile, giữ semantics/actions/validators/conditions/screen, status layout exact. Task **v10/9c2910ac-442d-4988-8419-a3387113bb52**, Subtask **v11/91b86a32-f2f1-4a3f-82bd-d7f847585d8a**. Không còn reset tạm, không bỏ QA conjunction.

## Phạm vi và giới hạn

Đây là đồng bộ trạng thái **một lần** của ba Epic NEW, không phải automation ép mọi cấp luôn cùng trạng thái. A01–A05 không chỉnh; monitor vẫnPAUSED, không tiếp tục lịch hoặc deploy app. Không đụng KAN/SAM1, billing/permission/Sprint/worklog hoặc timeline. Chưa chạy lại toàn bộ Jira E2E/non-PM; đã thực thi và đọc lại đủ84reset.

Before/rollback evidence: jira-bot/new-epic-reset-before-2026-10-13.json. Kết quả, từng key và readback: jira-bot/new-epic-reset-result-2026-10-13.json. Proof: jira-bot/QAG3-new-epic-descendants-reset-2026-10-13.png. Nếu cần phục hồi trạng thái cũ sau này phải qua workflow/gate hợp lệ với bằng chứng mô phỏng mới, không replay snapshot hoặc xóa history.

Nguồn cơ chế Resolution: [Atlassian — Configure resolutions](https://support.atlassian.com/jira-cloud-administration/docs/configure-resolutions-in-a-jira-workflow/). Bằng chứng trạng thái là MCP thực thi/readback, không chỉ tài liệu vendor.

Đã dừng sau khi hoàn tất yêu cầu.


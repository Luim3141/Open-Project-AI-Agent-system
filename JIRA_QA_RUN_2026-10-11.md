# QA run — QAG3, 11/10/2026

## Outcome

- Official MCP session verified as the owner at https://luimjiraqldapm.atlassian.net, cloudId560ef0cc-d24b-4613-98d3-d541afe8f32b. No browser/REST fallback or impersonation.
- Complete JQL for the real QA assignee returned 53 Subtasks, isLast=true; all To Do before this batch. No inference about omitted Parent fields from that search.
- QAG3-6 evidence read resolves Parent QAG3-2, real QA assignee, source-AUTH-01-QA and incomplete checklist. Explicit editable-field probe was unavailable for this MCP experiment cohort; do not infer write eligibility for gate custom fields.
- Scheme10003 remains applied; current QAG3-6 transitions are11ToDo/21InProgress/31Done, not the new delivery workflow.

## Executed technical QA

| Check | Actual result | Limit |
|---|---|---|
| Node predicate fixtures, including owner simulation and self-review positives/negatives | PASS | Synthetic predicate logic, not Jira transitions |
| Python Jira regression/stdio suite | 94 tests PASS | No product test execution |
| Official identity/resources/JQL/QAG3-6 read | PASS | Read scope only |
| Actual workflow transition discovery | PASS | Shows old workflow; new Pass testing unavailable |
| Jira new workflow E2E T01–T23 | NOT RUN | Not active; no fake rollout proof |
| AUTH-01 product execution/retest | NOT RUN | No verified revision/Test endpoint in this batch |

## Actual Jira writes

Owner requested running QA work; preview disclosed starting test design only. Through official MCP:

1. addOrEditJiraIssueComment(QAG3-6) created comment10003 with12testcases/AC trace/expected and actual=CHƯA CHẠY, plus execution limitations.
2. transitionJiraIssue(QAG3-6, transitionId21) succeeded, To Do→In Progress, to reflect actual test-design work begun, not testing completed.
3. Assignee, Parent, description, labels and checklist were not edited. No Done/SIMULATED PASS/worklog/personnel score or change to52other QA Subtasks, other WBS, scheme, automation or paused monitor.

Rollback if needed is a separately scoped request to move this Subtask back via a fresh transition read and amend the comment; no deletion is implied. Keep the audit history.

## AUTH-01 designed cases

| Case | Source | Input/action | Expected | Actual |
|---|---|---|---|---|
| AUTH-TC01 | AC1 | Email mới hợp lệ, mật khẩu/xác nhận khớp theo chính sách đã chốt | Tạo đúng một tài khoản; báo thành công | NOT RUN |
| AUTH-TC02 | AC1 | Email rỗng hoặc thiếu @/domain | Không tạo tài khoản; báo lỗi hợp lệ | NOT RUN |
| AUTH-TC03 | AC1 | Email đã đăng ký | Không tạo tài khoản thứ hai; thông báo không làm lộ mật khẩu | NOT RUN |
| AUTH-TC04 | AC1 | Mật khẩu hoặc xác nhận rỗng | Không tạo tài khoản; báo trường bắt buộc | NOT RUN |
| AUTH-TC05 | AC1 | Mật khẩu và xác nhận không khớp | Không tạo tài khoản; lỗi dễ hiểu | NOT RUN |
| AUTH-TC06 | AC1 | Mật khẩu không đạt chính sách BA đã duyệt | Bị từ chối; không tự giả định quy tắc độ dài | NOT RUN |
| AUTH-TC07 | AC1 | Gửi lặp hoặc hai yêu cầu đồng thời cùng email | Không tạo hai tài khoản; kết quả nhất quán | NOT RUN |
| AUTH-TC08 | AC2 | Đăng ký thành công bằng email mới | Tài khoản chưa thuộc Project nào | NOT RUN |
| AUTH-TC09 | AC2 | Tài khoản mới truy cập dữ liệu Project không được cấp | Không đọc/sửa dữ liệu; lỗi quyền phù hợp | NOT RUN |
| AUTH-TC10 | AC1/AC2 | Đăng ký thất bại ở bước xác thực | Không có tài khoản/quan hệ Project tạo dở | NOT RUN |
| AUTH-TC11 | Risk | Mạng lỗi/timeout khi gửi đăng ký | Hiển thị trạng thái rõ; thử lại không tạo trùng | NOT RUN |
| AUTH-TC12 | Retest | Chạy lại case lỗi sau bản sửa xác định revision | Lưu actual/expected và liên kết Fix Bug; chưa PASS nếu chưa chạy | NOT RUN |

The two ACs come from QAG3-6/QAG3-2; resilience/security cases are additional risk coverage, not invented acceptance-policy decisions. Password policy needs BA confirmation; do not invent numeric thresholds.

## Remaining

Owner simulation policy is deployeddevelopment2.6.0 but not applied via the custom workflow. Test design and94infrastructure tests do not constitute product QA PASS, real Tester acceptance, current-QA changelog or the required new-workflow E2E. No qualification evidence or global power grants fabricated. Monitor remains paused.


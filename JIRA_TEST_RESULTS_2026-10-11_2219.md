# QAG3 — kết quả kiểm thử 11/10/2026, 22:19 +07

## Kết luận

Đã chạy toàn bộ bộ kiểm thử Jira local hiện có và kiểm tra chỉ đọc trên Jira. **Chưa đạt nghiệm thu migration**: không có kết quả chuyển trạng thái trên ba workflow mới, vì QAG3 vẫn gắn scheme10003. Không ghi T01–T23 PASS hoặc tạo rollout-evidence.json từ kết quả local.

## Kiểm thử đã thực thi

| Bộ kiểm tra | Kết quả thực tế | Giới hạn |
|---|---|---|
| Python `-m unittest discover -s tests -p 'test_jira_*.py' -q` | 105 tests, exit0, OK | HTTP/rollout/migration tests có mock; không phải Jira transition E2E |
| Node `forge/qag3-validator/test.cjs` | Predicate fixtures PASS, exit0 | Không phải Jira engine |
| Forge CLI14.1.0 `lint` | No issues found, exit0 | CLI cảnh báo Node hiện tại ngoài phiên bản hỗ trợ22.x/24.x |
| PowerShell supervisor success/recovery | exit0/0, số lần khởi động1/2 | Start-Process/Start-Sleep được mock; không bật monitor |
| PowerShell supervisor exhaustion/missing | exit7/1 đúng nhánh lỗi | Không khởi động daemon thật |
| Jira expression type analysis | 10/10 valid, Boolean | Không chuyển trạng thái |
| Jira expression evaluation | 10/10 đánh giá hoàn tất; 3true/7false | Dữ liệu đã lưu của QAG3-1/2/3; chưa kiểm tra pending transition fields |
| WBS qua official MCP, phân trang đến isLast=true | 329 unique:11Epic/53Task/265Subtask; Parent đúng;5assignee;329nhãn mô phỏng | Không kiểm tra lại từng AC/checklist hoặc từng worklog ở lượt này |
| Trạng thái WBS | 316Done/13In Progress | Hoàn thành mô phỏng theo workflow cũ, không phải bằng chứng gate mới |

Bảy giá trị false thuộc reason/checklist/QA/acceptance/readiness trên dữ liệu đã lưu. Không tự coi false là lỗi chương trình hoặc coi true là gate E2E PASS. Ba true là PM actor, Epic child Tasks Done và Task Subtasks Done.

## Xác minh phiên và cấu hình thật

- Site https://luimjiraqldapm.atlassian.net; cloudId560ef0cc-d24b-4613-98d3-d541afe8f32b; projectQAG3/10002.
- Official MCP: atlassianUserInfo, getAccessibleAtlassianResources, getJiraIssue(QAG3-2), searchJiraIssuesUsingJql và discovered executeRead/listJiraIssueTransitions thực sự thành công. Owner account712020:0d04982c-00bf-46af-b3a7-446d0f44edfb.
- Supplementary MCP: inspect_scheme/inspect_workflow/inspect_expression_validation/inspect_expression_runtime/inspect_automation thực sự gọi, không phải official MCP admin write. ADMINISTER=true; ADMINISTER_PROJECTS=false; chưa xác minh quyền ghi bằng lượt kiểm thử này.
- Association10003. QAG3-1/2/3 chỉ có transitions11ToDo/21InProgress/31Done, không có transitions của workflow mới.
- Epicv7:6statuses/10transitions; Taskv6:10/16; Subtaskv6:7/13. Hai nhánh assignee business/dev tồn tại trong cấu hình Subtask.
- Source manifestSHA256837884a1f8829990d99ae9456c56cb1312745f649db8d8c8f6af768cb78c517e; catalog10validators.
- A01 UUID01a1216a-82a7-7a79-9f26-8102e7f6a942 DISABLED. inspect_automation readComplete=true; không có A02–A05 trong kết quả.
- Không Computer Use, Jira write, deployment, migration, bật automation hoặc resume monitor.

## Phát hiện cần xử lý

1. **Lỗi cấu hình Resolution:** Epic Cancel transition9 có `actions=[]`; chưa đặt Resolution hủy như hợp đồng. Restore10 có clear Resolution; Accept6 đặt10000. Đây là phát hiện đọc cấu hình, chưa phải transition test.
2. **Thiếu lý do ở Reanalyse:** Epic transition3 không có validator hoặc transition screen, trong khi đặc tả yêu cầu lý do. Return/scope changed7 cũng chưa có validator/screen lý do.
3. **Thiếu đường qualification:** gateway yêu cầu bằng chứng Jira T01–T23 trước activation, nhưng custom transitions chưa khả dụng trên QAG3. Chạy thêm unit tests không giải quyết vòng phụ thuộc này. Cần một đường triển khai kiểm thử giới hạn, có preview/approval và rollback được hỗ trợ rõ ràng; không bỏ guard hoặc giả kết quả.
4. **Automation chưa triển khai:** A01 tắt, A02–A05 chưa có. Không thể thử replay/concurrency/audit của các rule chưa chạy.
5. **Phần chưa được chứng minh:** linked Fix Bug/retest, Lead/BA reviewer, tính nguyên tử của child-scope và nghiệm thu, snapshot Sprint đóng băng. Checklist text/QA attestation không tự xác minh bài test hoặc lỗi liên kết.

## Đối soát T01–T23

Trạng thái dưới đây là **Jira E2E**, không thay bằng PASS local. BLOCKED là chưa thể thực thi trên workflow đích; NOT RUN là chưa có lượt thao tác kiểm thử tương ứng.

| ID | Kết quả Jira E2E | Bằng chứng/phần còn thiếu |
|---|---|---|
| T01 | BLOCKED | Gate empty-Epic có trong nguồn; chưa transition READY/REVIEW/DONE trên Epic rỗng |
| T02 | BLOCKED | Child-Done validator có trong cấu hình; chưa thử child chưaDone |
| T03 | BLOCKED | A02 chưa có; chưa thử lastTaskDone→EpicReview |
| T04 | BLOCKED | Accept gate/Resolution có; chưa nghiệm thu và snapshot |
| T05 | BLOCKED | A01 tắt; chưa trigger một lần |
| T06 | BLOCKED | A03 chưa có; chưa thử addTask/reopen/clearResolution |
| T07 | BLOCKED | A03 chưa có; chưa thử mở lại Task/Epic |
| T08 | BLOCKED | A04 chưa có; chưa thử Parent cũ/mới/rỗng |
| T09 | BLOCKED | Chưa thử text-only edit với rules hoạt động |
| T10 | BLOCKED | PM validator được type-check; chưa negative UI/MCP bằng non-PM |
| T11 | BLOCKED | Reason gate có; phát hiện Cancel thiếu action Resolution; chưa cancel/restore thật |
| T12 | BLOCKED | Deploy có childDone/checklist; chưa thử transition negative/positive |
| T13 | BLOCKED | QA attestation có; linked Fix Bug/retest chưa chứng minh |
| T14 | BLOCKED | Cạnh và reopen clearResolution được đọc; chưa chạy các nhánh thật |
| T15 | BLOCKED | Cấu hình hai nhánh đã đọc; chưa transition theo assignee/đổi nhánh/unassigned |
| T16 | BLOCKED | Local one-shot/replay tests PASS; không phải Jira rule replay/concurrency |
| T17 | BLOCKED | Chưa thử concurrent child change + Accept Epic; không bảo đảm atomicity |
| T18 | NOT RUN | Chưa kiểm thử snapshot/điểm Sprint đóng băng khi đổi scope |
| T19 | NOT RUN | Chưa thực thi test extension/newEpic/link/preserve acceptance |
| T20 | BLOCKED | Local error branches PASS; chưa lỗi lookup/quota/permission của rule Jira |
| T21 | BLOCKED | Không ghi KAN/CANCELLED; chưa chứng minh rule isolation bằng event thật |
| T22 | BLOCKED | Checklist source có; chưa Deploy/smoke evidence thật trên workflow mới |
| T23 | PARTIAL | Count/unique/Parent/5assignee/mô phỏng PASS đọc toàn bộ329; chưa kiểm tra từng AC/checklist và chuỗi import mẫu ở lượt này |

**Tổng Jira E2E hoàn chỉnh: 0/23 PASS.** Không phải23FAIL: phần lớn chưa thể chạy, không được biến NOT RUN/BLOCKED thành PASS.

## Bước tiếp theo chính xác

Sửa lỗi cấu hình đã phát hiện theo preview được duyệt; thiết kế đường qualification có giới hạn để thử workflow thật trước rollout329; hoàn thiện và thử A01–A05; ghi bằng chứng issue/actor/action/readback/audit thật cho T01–T23. Chỉ sau đó tạo preview switch mới, duyệt exact hash, switch và poll/đối soát329. Không cần thêm worklog giả hoặc chờ quota để giải quyết các thiếu hụt trên.

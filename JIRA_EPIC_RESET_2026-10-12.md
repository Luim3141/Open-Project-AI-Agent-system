# QAG3 — reset ba Epic để thực hành workflow

## Đính chính lựa chọn Epic — 12/10/2026

Người dùng xác nhận ba Epic cuối WBS mới là mục tiêu NEW, không phải ba Epic đầu. Đã sửa qua official MCP và đọc lại toàn bộ 11 Epic (`isLast=true`): QAG3-243 Comment, QAG3-274 Dashboard, QAG3-299 Notification = NEW; QAG3-212 Issue / Bug = In Progress. QAG3-100/131/162/187 vẫn Done. QAG3-330 Test A01 không thuộc danh sách WBS và không thay đổi.

Khôi phục QAG3-1/32/69: đã xác minh 16 Task và 80 Subtask con đều Done, rồi chuyển NEW → READY → In Progress → REVIEW. Evidence ghi rõ SIMULATION ONLY. Gate hiện dùng delimiter literal `\\n`, không nhận newline thật; cấu trúc evidence được gửi theo delimiter hiện hành, không sửa validator.

**Chưa khôi phục được Done:** Accept Epic6 trên cả ba trả HTTP400: `Expression executed too many expensive operations (limit: 10)` tại `child.project` trong QAG3 Epic delivery acceptance. Đọc lại xác nhận cả ba vẫn REVIEW. Không tắt/bỏ gate, không sửa workflow, không ghi Task/Subtask, không bật automation/monitor. Cần tối ưu validator và kiểm thử trước khi thử Accept Epic lại; không coi lỗi runtime này là thiếu nghiệm thu thực tế của dữ liệu mô phỏng.

## Phạm vi và quyền

Chủ dự án yêu cầu đưa ba Epic hiện có về NEW và cho phép quyết định xử lý vấn đề phát sinh. Site luimjiraqldapm.atlassian.net; cloud560ef0cc-d24b-4613-98d3-d541afe8f32b; projectQAG3/10002. Official MCP preflight identity/resources và issue read đã xác minh owner712020:0d04982c-00bf-46af-b3a7-446d0f44edfb. Không mở rộng KAN/SAM1/OpenProject/billing/permission hoặc khởi động monitor.

## Chẩn đoán và bản sửa

- Trước sửa: QAG3-1 Reopen8 có reason ADF mới bị400 với thông báo fresh reason, cả fields và update.set. String trực tiếp bị REST từ chối vì field yêu cầu ADF. Browser Use đối chứng: form có reason mới, Update vẫn cùng lỗi; hủy form chưa lưu.
- Development2.7.0 bổ sung xử lý RichText nhưng original repro vẫn lỗi, không coi đó là nguyên nhân thực tế.
- Development2.8.0 giữ predicate và tạm trả kiểu dữ liệu khi fail. Actual Jira error: `current=Map, previous=null, reason=string, oldReason=null`. Không xuất nội dung field, secret hay thông tin cá nhân trong diagnostic.
- Nguyên nhân chứng minh: mã so primitive `typeof` với `'String'`, trong khi runtime trả `'string'`; harness local cũng giả lập chữ hoa nên đã che lỗi.
- Development2.9.0 sửa tất cả checks cùng lỗi trong7module;10validator giữ nguyên, không đổi graph/checklist/PM/QA policy hoặc thêm scopes/function/storage/egress. Diagnostic đã bỏ. Manifest SHA256 `8b7de8e6498f5cf58d418f01bfd7c82d3b5d3824eef9a29c4e538db81b2263db`.
- Read-only analyser hash pin/sourceVariant cập nhật đúng bản mới; không đổi write allowlist, exact-hash approval, rollout-evidence hoặc activation checks. Registered server đã chạy trước sửa có thể cần refresh để đọc source mới; chưa tuyên bố Jira type analysis của hash này đã chạy.

## Kiểm tra đã thực hiện

Node fixture: RichText regression RED trước hỗ trợ; lowercase runtime regression RED trước sửa; toàn bộ fixture GREEN sau sửa. Forge deploy lint No issues found; deploy development2.9.0 exit0. Python `unittest discover -s tests -p test_jira*.py`:105tests PASS sau cập nhật read-only source hash; lần trước3tests lỗi do hash mới chưa nằm trong allowlist, đã sửa đúng nguyên nhân. Node25.8.2 ngoài dải ForgeCLI hỗ trợ22/24, nhưng những lệnh lint/deploy đã chạy exit0; không tự nâng runtime.

## Jira before/after và bằng chứng

| Epic | Trước | Reopen8 | Cancel9 | Restore10/read-back |
|---|---|---|---|---|
| QAG3-1 Tài khoản & Role | Done10009 | In Progress | CANCELLED | NEW10010 |
| QAG3-32 Quản lý Project | Done10009 | In Progress | CANCELLED | NEW10010 |
| QAG3-69 Backlog | Done10009 | In Progress | CANCELLED | NEW10010 |

Các mutation thành công là `mcp__atlassian__transitionJiraIssue`, mỗi transition gửi reason ADF mới mô tả reset học tập, giữ công việc con. `getJiraIssue` đọc lại3Epic NEW và owner Khai Dương account712020:47b24428-aa71-4363-b68f-29ed2285aad8 giữ nguyên. Before source field rỗng trên UI; after reason là lý do Restore riêng từng Epic.

Negative thực tế: QAG3-1 ở In Progress gọi Cancel9 không đưa reason mới bị400 đúng; ngay sau đó reason mới cho phép Cancel. Không tự tick checklist, giả QA hoặc đổi assignee; không gửi API ghi Task/Subtask, worklog, điểm số, deadline, automation hay monitor.

## Giới hạn và rollback

Chưa chạy toàn bộ QA/acceptance/linked-Bug/retest/non-PM/concurrency/A01–A05 E2E. Resolution được yêu cầu nhưng connector không trả nên actual Resolution UNKNOWN, không suy null. Chưa đối soát lại toàn329+testitems/automation effects. Task con vẫn không được reset bởi các lệnh trên; để test A01 cần Epic READY và Task con bắt đầu chuyển trạng thái sau đó, NEW Epic một mình không kích hoạt A01.

Rollback mã: phục hồi các primitive checks và hai dòng reason từ development2.6.0 theo source đã lưu, kiểm tra hash/fixtures rồi deploy development có review; điều này khôi phục lỗi nên chỉ dùng rollback khi cần, không uninstall app đang tham chiếu. Rollback trạng thái không đồng nghĩa QA thật: phải dùng các transitions hợp lệ và nhập evidence mô phỏng minh bạch, không ghi trực tiếp status hoặc xóa lịch sử.

Nguồn tham khảo primary: [Forge workflow validator](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/), [Jira expression types/RichText](https://developer.atlassian.com/cloud/jira/service-desk/jira-expressions-type-reference/). Runtime diagnostic trên chính QAG3 là bằng chứng quyết định cho lowercase string, không dựa vào tên kiểu String trong bảng tài liệu.

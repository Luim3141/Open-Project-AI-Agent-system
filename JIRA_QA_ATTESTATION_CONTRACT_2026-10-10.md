# QAG3 — QA xác nhận kiểm thử

## Quyết định đã chốt

Ngày 10/10/2026 (+07), chủ dự án chọn **dùng phương án QA xác nhận** thay vì bắt buộc xác minh từ CI/test runner. Đây là mức bằng chứng nghiệp vụ cho bài tập: người QA thật chịu trách nhiệm xác nhận đã kiểm thử phiên bản được nêu, kèm bằng chứng. Không xem đó là bằng chứng hệ thống đã tự chạy test.

Trạng thái hiện hành: development2.3.0/catalog8; Task inactivev6 có QA gates; Subtask inactivev6 có QA-attest Pass testing và independent PM acceptance Approve work, screens10010. Approved exactpreview/apply và independentreadback/preservation đạt; chi tiết JIRA_QA_TASK_GATE_BATCH_2026-10-10.md và JIRA_SUBTASK_ACCEPTANCE_PREVIEW_2026-10-10.md. Chưa full Fix Bug/retest/Lead/BA/Epic hoặc Jira runtime/E2E/migration. Previewdeploy cũ giữ làm lịch sử; không approval cho payload khác. QA active verified official MCP, không chứng minh login/test.

## Quy tắc thiết kế

1. Người thực hiện xác nhận phải là tài khoản Tester đã ánh xạ trong JIRA_TEAM_QAG3.json: 712020:94d1f95d-9618-4f25-8284-41105336b942 (Duyhungls2005@gmail.com). Phải xác minh identity/active/access hiện hành trước E2E; thông tin invited/assignable cũ không chứng minh người này đã đăng nhập. Không dùng owner, bot hoặc trường tên QA tự nhập để giả danh QA.
2. Task tại Pass testing và Subtask BE/FE tại Pass testing phải nhận xác nhận QA cùng bằng chứng cho vòng làm việc hiện hành. Subtask BA/Tester/PM giữ luồng nghiệp vụ riêng và reviewer phù hợp; không ép qua Code Review/QA như Subtask phát triển, không cho tự nghiệm thu chỉ bằng checkbox.
3. Dùng QAG3 Review evidence hiện có cho: bản build/commit/bản tài liệu được kiểm thử; môi trường Test; testcase/phạm vi; kết quả; link báo cáo/ảnh/bằng chứng; Bug đã retest hoặc lý do không cần retest. Thiếu phiên bản hoặc bằng chứng thì không đạt. Không tạo field thứ tư hoặc tích hợp mới chỉ từ quyết định này.
4. Nguồn danh tính/thời điểm là actor thật của hành động Jira đã commit và lịch sử hệ thống, không phải tên/email/timestamp trong evidence text. Checkbox chỉ là checklist, không phải chữ ký QA. Candidate ưu tiên expression đọc changelog; phải thử runtime, thiếu/không đọc được lịch sử thì chặn, không mặc định PASS.
5. Rework/ReDev/Bug found/Reopen hoặc thay đổi phạm vi/AC/phiên bản liên quan sau xác nhận làm xác nhận trước đó không còn đủ để nghiệm thu. Giữ lịch sử cũ, yêu cầu QA xác nhận lại phiên bản/vòng mới. Retest not required không được dùng để bỏ qua Bug chưa xử lý hoặc chưa retest; nếu xác nhận không cần retest thì QA phải ghi lý do và vẫn xác nhận kiểm thử hiện hành.
6. Gate trước Done phải đối soát xác nhận QA hiện hành và lỗi chặn nghiệm thu, cùng các gate Lead/BA/PM/checklist/children Done đã yêu cầu. QA xác nhận không thay PM nghiệm thu, không tự Epic Done hoặc thay đổi điểm hiệu suất.
7. Sửa code/artifact ngoài Jira không tự được nhận biết khi chưa có integration. QA phải ghi đúng phiên bản và xác nhận lại nếu phiên bản thay đổi. Không tuyên bố đã xác minh nội dung file/link hoặc test execution chỉ vì evidence nonblank.

## Mẫu evidence cho QA

```text
Revision: <commit/build hoặc phiên bản tài liệu>
Environment: Test - <địa chỉ/tên môi trường>
Test scope: <testcase/phạm vi đã kiểm tra>
Result: PASS | FAIL
Evidence: <link báo cáo/ảnh/test log>
Retest: PASSED | NOT REQUIRED
Bug references / retest rationale: <issue keys và kết quả hoặc lý do>
```

Mẫu là dữ liệu người QA khai báo; các thông tin tự nhập không thay authenticated actor hoặc timestamp hệ thống. Format validator/parser cụ thể và mapping transition phải được chuẩn bị/test trong lô kỹ thuật kế tiếp trước khi preview/duyệt ghi Jira.

## Kiểm thử bắt buộc trước rollout

- QA thật xác nhận + evidence đầy đủ, đúng revision/vòng: đạt gate QA, nhưng không tự đạt toàn bộ gate Done.
- Dev/PM/bot bấm Pass testing hoặc ghi tên QA trong text: bị từ chối xác nhận QA.
- Checkbox tick đủ nhưng không có sự kiện QA/bằng chứng: bị chặn.
- Evidence rỗng/thiếu revision/FAIL, cả hai hoặc không có kết quả retest hợp lệ: bị chặn.
- Dùng xác nhận cũ sau Rework/Reopen/sửa revision hoặc nội dung liên quan: bị chặn; QA xác nhận mới mới có thể đạt.
- Bug chưa Done/retest, history không đủ hoặc thiếu quyền đọc: bị chặn, không suy từ null/omitted thành không có Bug.
- Giữ hai nhánh Subtask; không tự chấm QA Task là Done khi còn bug phải retest.
- Lặp/sự kiện đồng thời và thay đổi pending screen không cho dùng xác nhận cũ; chưa cam kết atomic multi-issue transaction.

## Phạm vi không thay đổi

Chỉ QAG3; ngân sách0; giữ KAN/SAM1/OpenProject. Chưa bật CI, thêm app scopes/function/storage/egress, migration329issues, A01–A05 hoặc resume bot. Lần ghi Jira tiếp theo cần preview cụ thể/approval/read-back theo AGENTS.md; quyết định QA không tự nghiệm thu các gate còn thiếu.

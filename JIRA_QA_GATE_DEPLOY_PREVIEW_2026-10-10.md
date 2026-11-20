# QAG3 QA gate — preview deployment development

## Trạng thái thực

Candidate local đã implement/test, CHƯA deploy/gắn workflow. Official MCP identity/resources/QAG3-2 preflight PASS. getJiraUser trả QA Hung/account712020:94d1f95d-9618-4f25-8284-41105336b942 active=true; không chứng minh đã login/accept/test. Supplementary inspect_workflow(task) vẫn v5/cd076ba7-57ee-455a-813b-c70e40453171, catalog5validators cũ, Pass testing chưa có gate QA. Không Jira write trong lượt này.

## Lô xin duyệt

- App hiện có f6f77ef8-978a-4e85-a3df-b30d3ef38d06, chỉ development, site luimjiraqldapm.atlassian.net.
- Manifest SHA256 `9942ba518b1f0a17418ade1001fd51a20c6b67de8352a3fdc4e5daa7cfe52b6d`.
- Chỉ thêm2modules qag3-qa-attest/current. Năm module cũ/runtime/app ID giữ nguyên; đối chiếu baseline SHA25648e05af89cdd43806749ed608db5e235767db5cf49bebf57460fbc432a48bc74 PASS.
- Không permissions/function/storage/egress/dependency mới; không register/install lại, Production, billing/payment hoặc paid service. Free allowance/dashboard không là hard cap.
- Không gắn validators, sửa graph/screen, activate/migrate329issues, enable automation hoặc resume monitor. Catalog xuất hiện không nghĩa gate hoạt động.
- Sau deploy: đọc deploy history và Jira catalog độc lập, lấy version thật từ kết quả.
- Rollback khi modules mới chưa được dùng: restore baseline manifest rồi deploy development qua preview/approval mới. Không uninstall app vì gates cũ đang tham chiếu; nếu đã gắn modules mới, restore workflow trước.

## Hai modules candidate

QA-attest dự kiến Task Pass testing10/Subtask phát triển Pass testing12: real QA active, nguồn IN TESTING10018, evidence mới cùng transition. Bảy dòng duy nhất/nonblank: Revision, Environment, Test scope, Result, Evidence, Retest, Bug references / retest rationale. Result PASS, Environment Test - tên; checklist QA passed và đúng một retest khớp text. Không tin tên QA tự nhập.

QA-current dự kiến trước Task Approve13/Deploy14: đọc history newest-first, chọn sự kiện IN TESTING10018→REVIEW10012 gần nhất, real QA author active, cùng event evidence thay đổi và toString khớp field hiện tại. Thiếu/lỗi history thì chặn. Sau event, chỉ cho status REVIEW→READY FOR RELEASE của Task; rework/retest/reopen hoặc sửa summary/description/Parent/assignee/evidence làm stale. Kiểm tra cả pending edits trên screen. Evidence QA sau ký giữ nguyên; ghi chú sau đó dùng comment, không suy comment là reviewer signature.

## Chưa đủ điều kiện migration

- QA khai báo phiên bản/kết quả, không CI; chưa đọc nội dung link/file hoặc phát hiện code sửa ngoài Jira.
- Chưa đối soát live Bug links/closure/retest từng Bug; rationale text không thay hard gate lỗi chưa retest.
- History có giới hạn tải/độ phức tạp, lỗi fail-closed. Fixture JS không chứng minh Jira engine, ADF/changelog serialization hoặc visibility.
- Chưa khóa child-scope concurrent edits; còn Lead/BA/business reviewer identity.
- READY FOR RELEASE hiện chỉ có Deploy: lô gắn QA-current cần preview đường quay lại testing khi stale, chưa thêm cạnh trong lô deploy này.
- Không gắn QA-current vô điều kiện lên business Subtask; cần guard nhánh và chống đổi assignee để bypass. Hai nhánh chưa Jira E2E.

## Validation thật

Node fixtures PASS: actor/active, missing/FAIL/duplicate evidence, retest mismatch/XOR, reused evidence, stale history, pending edits, foreign project, re-attestation mới. Một lượt fixture lỗi do adapter typeof chưa hỗ trợ member access đã sửa và chạy lại PASS. Forge lint No issues found; Python Jira regression88tests PASS. Không thay code admin/MCP hoặc rollout evidence. Jira engine/transition E2E NOT RUN.

test.cjs SHA256 `ab7019b4f10184cad91da11df722132dcf2601e83ab7afb8b58bc15ef544a34d`.

Nguồn: [Expression types](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/), [Forge workflow validator](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/).

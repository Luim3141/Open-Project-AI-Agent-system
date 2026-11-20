# QA Task gates — saved inactive and read back

## Kết quả đã xác minh

User duyệt deploy manifest9942ba518b1f0a17418ade1001fd51a20c6b67de8352a3fdc4e5daa7cfe52b6d. Forge deploy development **2.2.0** Success, deploy history createdAt2026-10-10T10:16:59.191Z; catalog Jira độc lập có7validators. Không permissions/function/storage/egress/dependency/billing mới. Năm modules cũ/runtime/app đối chiếu baseline hash nguyên vẹn.

User duyệt **Duyệt lô QA Task inactive**, preview24a2237f-7517-42b1-b9c3-ba9a8995eea0, SHA256e1415852687fa714f8d098622ffab2a7e74b2d60ffb87852f5d3bd18ea9f558e, APIvalidation errors=[], blockers[]. Supplementary MCP apply_change qua registered qag3-admin/Codex app-server trả VERIFIED. Không browser mutation.

Task9f21c6fc-718d-4f3c-aca9-49ab9c89c899 **v5→v6**, versionIDfe305b00-242d-4bc2-bf6a-bdf7f6564591:

| Transition | Thay đổi được duyệt và đọc lại |
|---|---|
| Pass testing10: IN TESTING→REVIEW | Screen10010, qag3-qa-attest: QA thật active, evidence mới+đầy đủ+PASS và retest outcome khớp checklist |
| Approve13: REVIEW→READY FOR RELEASE | Thêm qag3-qa-current; giữ PM-only cũ |
| Deploy14: READY FOR RELEASE→DONE | Thêm qag3-qa-current; giữ PM-only, childrenDone, delivery checklist, native condition và Resolution |
| Retest before release16: READY FOR RELEASE→IN TESTING | Cạnh mới, PM-only, để thoát khỏi pre-release khi QA evidence stale; không nghiệm thu tự động |

QA-current yêu cầu committed Pass testing gần nhất do QA, evidence cùng event khớp hiện tại và chưa bị thay đổi/làm lại; chặn cả pending screen edits. Sau xác nhận QA, giữ nguyên Review evidence; ghi chú sau đó dùng comment nhưng không xem comment là authenticated reviewer signature. QA xác nhận lại phải gửi evidence khác (nêu vòng/build/test run mới), không chỉ thêm khoảng trắng.

## Bằng chứng và giới hạn

- Official atlassianUserInfo/resources/getJiraIssue(QAG3-2) preflight đúng site/cloud/project. QA active từng được getJiraUser xác minh; chưa có session QA thật hoặc test thực tế.
- Independent supplementary inspect_workflow đọc Taskv6 và đúng4transitions. Second readback qua registered MCP+semantic assertions PASS: bỏ đúng additions được duyệt thì mọi gate/graph/layout/screen/Resolution cũ bằng before, không chỉ nhìn version.
- Before/preview/started/result audit: C:/Users/LUIM/AppData/Local/QLDAPM/jira-admin-audit/24a2237f-7517-42b1-b9c3-ba9a8995eea0.*.json. Không replay apply; rollback cần fresh current version+preview/human approval.
- Nodefixtures/Forge lint PASS;89Python Jira tests PASS (thêm fixed Task QA preview builder, idempotency/conflict/preservation và stdio catalog15tools). Localtests/API validation/catalog không chứng minh Jira expression transition engine hoặc E2E.
- inspect_scheme vẫn QAG310002→10003. inspect_automation readComplete=true chỉA01 DISABLED. Không migrate329issues/activate/bật rule/resume monitor. Epic/Subtask không ghi trong lô này.

## Còn phải hoàn thiện trước migration

1. Subtask: gate QA ở BE/FE branch, business review độc lập và chống đổi assignee để bypass; không gắn QA-current vô điều kiện lên BA/QA/PM.
2. Live Bug links/closure và retest từng Bug; text rationale không thay server-side kiểm tra lỗi chưa retest.
3. Lead/BA reviewer identity và revision, Epic READY/acceptance checklist/evidence; QA gate không thay các gate này.
4. Runtime history/customfield serialization/visibility/limits và concurrency; real QA session/E2E, không impersonate hoặc fake evidence.
5. Staged migration329items/mapping giữ key/Parent/assignee; rollout guard hiện yêu cầu project rỗng cần thay trình tự qua preview/approval, không xóa WBS hay fakeE2E.
6. A02–A05 và nghiệm thu A01/replay/parent changes; mọi automation vẫn phải tương thích gate reason/PM đã duyệt.

Full setup chưa hoàn tất; không ghi rollout PASS, điểm cá nhân hoặc nghiệm thu code từ trạng thái Jira.

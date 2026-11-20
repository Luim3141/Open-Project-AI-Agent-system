# QAG3 Subtask acceptance — development2.3.0 / Subtask inactivev6 VERIFIED

## Kết quả thực hiện sau phê duyệt — 10/10/2026

Owner duyệt deploy manifest SHA256 `5c99687fa8895a35a5ac46fa12db26185722d2273b59ed77d6d2bd615f186301`; kiểm tra hash trước chạy. Forge deploy development **2.3.0** thành công, lint No issues found; deploy list ghi Success lúc **2026-10-10T10:42:39.358Z**. Supplementary MCP đọc catalog độc lập đủ8validators. Không register/install lại hoặc thêm scopes/function/storage/egress/billing.

Owner duyệt workflow preview **9124e90c-4c89-46f1-864a-3031d45684b2**, SHA256 **2b40297c57a4abf4854fd5cbcfd855ed79bce8e8eadd51bb440664b3f3e2df0d**, API validation errors=[]/blockers=[]. Registered qag3-admin `apply_change` trả VERIFIED. Independent `inspect_workflow` đọc Subtask **v6/7ccb46c1-ea7e-48b4-99aa-d98d1f6b3e89**: Pass testing12 có screen10010/QA-attest; Approve work4 có screen10010/independent Subtask acceptance. Preservation assertions PASS: giữ7statuses/13transitions, mọi condition/action/validator cũ, graph/layout/description/Resolution và reason gate Reopen6.

Official preflight thực atlassianUserInfo/resources/getJiraIssue(QAG3-4) PASS đúng owner/cloud/site/QAG3. Hai discover workflow admin không trả operation cần dùng; route ghi là supplementary registered MCP đã được duyệt, không browser hoặc official admin write. ADMINISTER=true/ADMINISTER_PROJECTS=false chỉ là preflight, không bằng chứng full admin.

Node predicate fixtures và90Python Jira regression chạy lại PASS; không Jira expression runtime hoặc E2E. Đọc lại association vẫn QAG3→10003; automation readComplete=true chỉ A01 DISABLED. Không migration329mục, bật A02–A05 hoặc resume monitor. Before/preview/started/result giữ tại `C:\Users\LUIM\AppData\Local\QLDAPM\jira-admin-audit\9124e90c-4c89-46f1-864a-3031d45684b2.*`; rollback cần fresh preview/approval, không replay hoặc uninstall app đang dùng.

Các mục candidate bên dưới là lịch sử thiết kế. Bug thực hành đã có quy ước Subtask Fix Bug trong jira-workflows.md; thiếu Bug issue type không tự yêu cầu thêm loại mới. Marker/evidence/retest của Fix Bug vẫn phải kiểm chứng trước fullgate; không suy Epic phát triển tính năng Bug tracking là lỗi thực hành.

## Session và trạng thái hiện hành

Official atlassianUserInfo/resources/getJiraIssue(QAG3-4) PASS đúng owner/site luimjiraqldapm.atlassian.net/cloud560ef0cc-d24b-4613-98d3-d541afe8f32b/QAG310002. Supplementary inspect_workflow Subtask v5/1afd7884-4080-4cfc-9a59-f9b789c7edfd,7statuses/13transitions; chỉ reason gate tạiReopen, chưa QA/reviewer gate. Chưa ghi Jira trong lượt candidate.

## Deployment preview

Appdevelopment hiện2.2.0; candidate chỉ thêm qag3-subtask-acceptance, không sửa7modules cũ/runtime/app, bytehashbaseline9942ba518b1f0a17418ade1001fd51a20c6b67de8352a3fdc4e5daa7cfe52b6d assertion PASS.

Candidate manifest SHA256 `5c99687fa8895a35a5ac46fa12db26185722d2273b59ed77d6d2bd615f186301`. Không scopes/function/storage/egress/dependency/billing, no Production/register/install lại. Rollback khi module mới chưa dùng: restore manifest2.2.0 rồi deploy qua preview/approval riêng; không uninstall vì rules cũ đang tham chiếu. Deployment approval không cho gắn workflow/migrate329issue/enable automation/resume monitor.

## Predicate và chính sách cần duyệt

- Chỉ Subtask QAG3, nguồn REVIEW; realactive PM trong2accounts đã chốt nghiệm thu cuối, không tự approve assignee hiện tại hoặc từng có mặt trong assignment history.
- Assignee active/known; không đổi summary/description/Parent/assignee cùng acceptance.
- Development nếu hiện là BE/FE hoặc history từng có BE/FE assignee hoặc CodeReview/ReadyForTest/InTesting. Đổi assignee sang BA không xóa phân loại này. Cần committed QA hiện hành cùng event evidence, không sửa evidence sau QA hoặc sử dụng pass trước Rework/Reopen/Retest.
- Business BA/QA/PM chưa từng development: không ép CodeReview/QA. PM độc lập gửi evidence mới trên acceptance screen: `Revision:`, `Review scope:`, `Review result: ACCEPTED`, `Evidence:`; mỗi dòng duy nhất/nonblank.
- Subtask PM phải do PM còn lại duyệt. Nếu cả2PM từng được phân công, predicate chặn cả2 có chủ đích; cần chỉ định reviewer độc lập qua thay đổi chính sách được duyệt, không xóa history/giả actor.
- Native routing vẫn theo assignee, không security roles. Dev đổi sang business có thể cần PM trả assignee về BE/FE để qua QA/retest; không tự sửa assignment bằng lô gate.
- History omitted/error→fail-closed; expressionlimits/visibility/serialization và realQA/PM E2E chưa được chứng minh. Không QA impersonation, fake evidence hoặc fake rollout PASS.

## Lô workflow dự kiến sau deploy/catalog-readback

Supplementary preview_subtask_acceptance_gates mới, fixed inactiveSubtask only:

1. Pass testing12: thêmscreen10010 và installed qag3-qa-attest.
2. Approve work4: thêmscreen10010 và installed qag3-subtask-acceptance.

Giữ7statuses/13transitions/nativeassigneeconditions/Resolution/layout/reason gate. Không sửa Task/Epic. Dùng lại previewhash900s/freshversion/approval/audit/oneshot/readback; không thêm URL/shell/APIallowlist. Cần APIvalidation errors=[] và ownerduyệt đúnghash trướcapply. Source16tools đã qua localstdio test; currentchat catalog có thể cần reload, registeredMCP mới dùng qua helper.

## Validation và những bước chưa đạt

Node fixtures PASS: business/development positive, wrongactor/inactive/selfreview/previousassignee, dev→business bypass, missing/duplicate/rejected/stale evidence, pendingedits/historyunknown. Một fixture dùng nhầm pendinghistory thayoriginalIssue history đã sửa và chạy lạiPASS. Forge lint No issues found.90Python Jira regression PASS gồm builder/preservation/idempotency/conflicts và stdiocatalog. Không Jira engine/E2E.

Còn Bug links/retest từng Bug, code reviewer/Lead/BA identity, Epic readiness/acceptance và concurrency; candidate này không full gates. Official listJiraProjectIssueTypesMetadata QAG3 trả total3/full: Epic10000,Subtask10010,Task10011, không Bug. listJiraIssueLinkTypes xác minh Blocks10000 (inward is blocked by/outward blocks),Cloners/Duplicate/Relates. Chưa tự thêm issue type hoặc suy Task tính năng Issue/Bug tracking trong WBS là Bug thật. Phải chốt representation của Fix Bug (Bug issue type hoặc Task phân loại rõ) và evidence/retest links trước fullgate. Migration/A01–A05/bot vẫn chưa bật. Không đổi KAN/SAM1/OpenProject hoặc đánh giá cá nhân.

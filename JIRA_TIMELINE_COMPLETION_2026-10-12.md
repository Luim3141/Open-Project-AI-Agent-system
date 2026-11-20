# QAG3 Timeline và ba Epic đầu — hoàn tất 12/10/2026

- Scope: đúng site luimjiraqldapm.atlassian.net, cloud560ef0cc-d24b-4613-98d3-d541afe8f32b, QAG3/10002,329WBS; không KAN/SAM1.
- User yêu cầu mỗi Task/Subtask có ngày riêng, cho phép bắt đầu sớm, không note/comment; yêu cầu baEpic đầuDone trong kịch bản học tập.
- Official route: atlassianUserInfo/getAccessibleAtlassianResources/getJiraIssue/searchJiraIssuesUsingJql/editJiraIssue/transitionJiraIssue. Supplemental integration dùng fixed read-only expression/workflow inspection; Forge CLI chính thức deploydevelopment, không gọi đây là officialMCP admin mutation.
-329datewrites và fullpaginationreadback:11Epic/53Task/265Subtask, không thiếu hoặc sai Start10015/Due; Parentkey/id, assignee,labels và326status ngoài baEpic giữ nguyên.
- Lịch03/04–31/12/2026,195weekdays,11Epic nối tiếp; BA1d,BE/FE2–3d song song,QA1–2d,PM1d+2d cuốiEpicbuffer. Con nằm trong cha; không chồng việc theo vai trò. Không điều chỉnh lịch nghỉ lễ/capacity thật.
- UI Timeline trước đó Align to Sprints gây thiếu bar; hiện Work item dates. UI đọc riêngTaskQAG3-14Apr13–17,BA15Apr13,BE16/FE17Apr14–15,QA18Apr16,PM19Apr17.
- QAG3-1/32/69 REVIEW→Done10009 qua actualAccept6, Resolution10000Done đọc lại độc lập. Checklist/evidence cần thiết được gửi cùng transition, đánh dấu SIMULATIONONLY; khôngcomment/note/description/worklog/Sprint/assignee mutation.

## Sửa blocker kỹ thuật

Lỗi ban đầu: Epic acceptance quá10expensiveoperations ở descendant.project/childIssues; requesttextarea cầnADF; Jira string split không giống Node đối với newline escapes. Các candidate2.10–2.12 đãdeploydevelopment nhưng transition vẫnfail; không báo chúng thành công. Final2.13.0 giữ10module, chia descendantDone sang companion gate vốn đã gắn/enabled ởAccept6; acceptance giữPM/scope/checklist/evidence fresh/owner/summary/description unchanged. Không tắt gate hoặc ghi trực tiếpstatus. ADFtextparagraph/hardBreak đọc trực tiếp, unknownshape fail-closed, tiết kiệmnewRichTextoperations.

ManifestfinalSHA256:e9d70f8d28d961e57f6c9a39da2b65460b1c790aa114165fdbae959c17f4eff6. Nodepredicatefixtures (foreignproject, childnotDone/null, unchanged/unsupportedADF),105Pythonregressions vàForgelint PASS. FixedAPIexpressionruntime PASS cảacceptancepending vàchildrenDone, sau đó3transitionthật vàreadbackPASS. Không đủ bằng chứngfullA01–A05/QA/concurrencyE2E; monitor vẫnPAUSED.

## Khôi phục

Snapshot trước/sau kế hoạch tại jira-bot/timeline-expanded-2026-10-12.json; chỉ khôi phục2datefields theo before sau yêu cầu củaowner, không sửaparent/assignee/status. Epicrollback dùngtransitionReopen hợp lệ với lý do mới; khôngbackdatechangelog/xóaissue. Code rollback đảo các sửa ở2Epicmodule/test vàdeploybaseline2.9.0; sẽ tái tạo blocker cũ, khônguninstall app. Giữ auditcandidate/lỗi, không giả qualification hoặc reset monitor/quota.

Nguồn primary: https://developer.atlassian.com/cloud/jira/platform/jira-expressions/ và https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/ . Giới hạn operation đã kiểm tra trên API/transition thật, không suy từ cấu hình.

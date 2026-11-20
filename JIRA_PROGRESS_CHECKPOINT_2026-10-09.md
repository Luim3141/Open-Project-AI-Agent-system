# Checkpoint Jira trước bootstrap — 2026-10-09

## 43. Hiện hành — A01–A05 ENABLED toàn QAG3; Subtask runtime đã sửa — 13/10/2026

A01 giữ ENABLED; A02–A05 đã bỏ riêng điều kiện `labels = qag3-test`, vẫn scoped QAG3/10002. A03/A04 giữ `qag3-scope-approved`; A05 là bình luận @mention PM, không email, không QA/acceptance/performance evidence. A02 thêm native **To status = Done** để lọc event gốc, tránh nhận Approve khi JQL chạy muộn đã thấy Done. Read-only supplemental API đối soát actor, toàn bộ components và các thay đổi trigger chính xác; không nới quyền hoặc đổi billing. Rule bật không tự xử lý lại mọi issue đã Done trong quá khứ.

Forge development **2.21.0**, SHA256 `b8e9648dc25dc7f2c420612a2fbede46dd47837e50f12a2bcf4003fff6c645f7`,12 expression modules/no functions/scopes/storage/egress. Stage2.20.0 giữ11module cũ; owner duyệt gate hash `da7c55436b262ca7b064057521727bff19c020e2fbd91fa6939d675caad9316f`, apply VERIFIED và independent MCP read Subtask **v9/d9c8e3c0-0697-459c-aed8-c45924f8c6c7**. Approve4 có acceptance+freshness+history; không được gỡ một gate. Taskv8/Epicv9 giữ nguyên.

Native admin-labelled SIMULATION: BA/PM Approve/reopen PASS; BE và FE đã QA→Review→Done/ResolutionDone. Missing reason, saved QA reuse và QA stale sau đổi summary bị400 đúng; fresh retest cho phép Done. Task Approve13/Deploy14 PASS. Smoke khi Task332 **không có qag3-test**: A03 reason/status changelog12147; A02 IP→REVIEW12155; A04 hai auditSuccess c1982c55…/2b4dd41e… và changelog12159; A05 comment10012 đúng @Hiệp/event qag3-a05-10012-20261012203501197. Fixture332 Parent331/Done/test label đã phục hồi,335/336 Done; không ghi329WBS/timeline/3Epic đầuDone/KAN/SAM1, không resume monitor.

106 Python Jira regression +3 targeted tests, Node conjunction/freshness, Forge lint và12/12 Boolean PASS. Đây là targeted native verification, **không** fullT01–T23/non-PM identity/concurrency/exactly-once/linkedBug/Lead/BA qualification. Giữ lịch sử errors, không tạo rollout-evidence PASS. Chi tiết, bằng chứng và rollback: `JIRA_AUTOMATION_FULLSCOPE_2026-10-13.md`. Các mục dưới là diễn tiến lịch sử.

## 42. Hiện hành — Subtask v8 / development2.19.0; BE vẫn bị chặn — 13/10/2026

- Approved Subtask additive QA freshness đã lưu/đọc lại v8 `e6aa1eac-47ea-40d4-966c-976e2267178a`: Approve work4 có cả acceptance và companion enabled, giữ screen10010/graph/Resolution/reason/routing. Không được gỡ một gate.
- Owner đã duyệt và deploy development2.17.0 (`dc5d99…`),2.18.0 (`9263d2…`),2.19.0. Bản cuối đúng SHA256 `98d21c680ca1c387d7e14f1e53e95b5c02c75a27d5e794de6cfded07b5025e54`; Forge lint PASS,11 module/no scopes/function/storage/egress/billing. Bản trước2.18.0 được giữ để rollback qua preview riêng; không uninstall app.
- Native fixture BA/PM QAG3-335 đã Approve4→Done, Reopen6 thiếu reason bị400, fresh reason→IP với Resolution clear; review/approve vòng2→Done. Official MCP cuối lượt xác nhận Done/ResolutionDone. Đây là fixture SIMULATION, không nghiệm thu sản phẩm/người thật.
- Native BE QAG3-336 đã đi Code Review→Ready for test→In testing→Pass testing→REVIEW. Approve4 vẫn400 trên cả2.17/2.18/2.19; lỗi2.19 tại `originalIssue.changelogs`, expensive operations limit10. Read-only2.19 Boolean/static6/BEtrue/runtime9 không chứng minh native transition PASS. Không retry unchanged hoặc đổi trạng thái giả để che lỗi.
- A01 ENABLED; A02–A05 ENABLED **chỉ labels=qag3-test**, không toàn329WBS. A04 native Parent reconciliation đã có Success; A05 hiện2commentactions/0email, **addCommentOnce=false cả2 nhánh**, frozen event guard/attempt marker vẫn giữ. Native issue-once từng chặn lượt review mới (audit a97ed01b…); sau sửa có comment10009 trên335 và10010 trên332. Marker/auditSuccess không tự chứng minh comment hoặc inbox delivery.
- QAG3-332 hiện CODE REVIEW sau thử review mới; QAG3-335 Done; QAG3-336 REVIEW. Chỉ fixtures331–336 trong qualification;329WBS/timeline/baEpic đầuDone/KAN/SAM1/monitorPAUSED giữ nguyên.
- Node predicate/conjunction/Task freshness chạy lại PASS; fixed saved-config verifier exit0 xác minh cả4rule enabled/testScope và A05 issue-once OFF/event-key dedup ON. Chưa full native BE/FE, stale/non-PM/concurrency hoặc project-wide rollout; không tạo rollout-evidence PASS.
- Bước tiếp: thiết kế lại truy vấn history với chi phí hữu hạn, đối chiếu native context và giữ đủ kiểm tra ever-assigned/QA provenance/staleness; cache-history đơn thuần đã thất bại. Thay đổi nguồn/deploy tiếp phải có preview/hash phù hợp, không dùng approval98… cho code khác.

Audit: `jira-bot/subtask-runtime-and-a05-final-2026-10-13.json`. Proof: `jira-bot/QAG3-A05-event-dedup-final-2026-10-13.png`. Các mục bên dưới giữ lịch sử từng bước, không phải trạng thái hiện hành.

## 41. Hiện hành: A02–A05 ENABLED qag3-test; A05 hai PM-mention comment verified — 13/10/2026

Taskactivev8/Forgedevelopment2.16.0 native QAApprove/DeployPASS; Epicactivev9 Return7screen10011+freshreason approvedhash80f931a5… đãapplyVERIFIED/readback. A02 parentIP→REVIEW changelog12058; A03 REVIEW→IP+reason12076; A04 Success1d421393…/Parentreconcile, incompleteSibling/emptyEpic khôngautoDone. A02–A05 đều ENABLED chỉqag3-test; chưaproject-wide.

Owner duyệt A05 email→comment @mention PM, UI lưu2comment/0email +addCommentOnce/frozenevent/labels-preservingmarker. MCP listcomments full/isLast xác minh10005@Khai và10006@Hiệp doAutomationforJira; auditSuccess4c55363d… và7c90de56…, RetestNoactions2ae90e3a…. Khôngprivacy/billing/permission hoặc329WBSwrite. Fixture332REVIEW/assigneeKhai sautest; fixtures333/334 được tạo riêngtrướctest. MonitorPAUSED. Local105Python+1freshness+1Returntest/Nodepredicate/freshness/archived288automationcasesPASS; currentfrozenA05asserts/savedconfigchecksPASS. KhôngfakefullT01–T23/rollout-evidence; nativeSubtask/stale/non-PM/concurrency đầyđủ chưaverified. Literal\\n evidence còn hạn chế. Audit/rollback/remaining `JIRA_QA_RUNTIME_FIX_2026-10-13.md`; A05 structuredproof `jira-bot/a05-comment-qualification-2026-10-13.json`.

## 40. Hiện hành: A04/A05 import thật DISABLED, 12/10/2026

Trạng thái hiện hành workflow/timeline đã cập nhật ở đầu `jira-management.md`; các mục39trở xuống là lịch sử trước manual migration. Lượt này official preflightPASS, browser IAB callable lại; native import tạo A04 UUID01a13075-71e9-7e0f-b65f-006ec2a4b83b/A05 UUID01a13075-71e9-750f-9913-5e43ba4adaf0 scopedQAG3DISABLED. Supplemental readComplete=true đủ5rule; native exports graph/trigger/scope semanticPASS, 51component/288localdecisioncasesPASS. A01ENABLED/A02–A03DISABLED giữ nguyên. ImportresetactorA04AutomationforJira; chưa PM-gated execution/enable/JiraE2E/maildelivery/quota/concurrency/fullreviewer. QA-current lỗi cũ chưa sửa; không gate/scope/billing changes hoặc issue mutation. MonitorPAUSED. Audit/remaining/rollback/candidate: `JIRA_A04_A05_IMPORT_2026-10-12.md`. Không reimport tạo duplicate.

## 39. Hiện hành: populated scheme switch implement/registered preview VERIFIED; migration chưa chạy — 11/10/2026

User duyệt bổ sung đườngmigration sauresearchAPI. `tools/jira_admin_mcp.py` thêm2fixedtools preview_scheme_switch/inspect_scheme_switch_result; snapshot329/type11/53/265/Parent/assignee/simulation/statusID, calculatorofficialAPI/mapping/asyncswitch/readback. Giữassignemptyguard, rolloutT01–T23/PMreview và exacthumanhash900s/lock/audit/no-replay.105Pythonregression/stdio testsPASS, catalog21, khôngJiraE2E. Officialidentity/resources/QAG3-2/discoverPASS; registered localpreview actualcalculator200/traversal329current316Done/13IP. Newpreview0794ba52-fc67-4baf-b3f7-ff9bdf19bcfb/hashdc16f48378b094ccb9ec2acf69f48fdfc9e37a089c9d6855b61dd8944997a936, **blockedT01–T23/PM reviewmissing**, chưaapproved. Mapping10008→10010 theo3type(required0currentToDo),3/10009giữID. Independent inspectscheme vẫn10003; noapply/switchPOST/activation/migration/automationenable/monitorresume/UI/KAN/SAM1/OpenProject/billing. Qualificationbeforeactivation vẫn cần đường được phép; khôngfakeproof hoặc tựtạoprojectthử. Auditremainingrollback `JIRA_SCHEME_SWITCH_IMPLEMENTATION_2026-10-11.md`; research schema `JIRA_SCHEME_SWITCH_API_RESEARCH_2026-10-11.md`. Phần38giữ lịch sử trước tool switch mới.

## 38. Hiện hành: mô phỏng329 +265worklog VERIFIED; migration BLOCKED — 11/10/2026

Official MCP đã hoàn thiện26metadata/29transitions còn thiếu, full JQL đọc lại329 khớp key/type/title/Parent/assignee/status/labels/source content. Hiện10EpicDone/1IP,49TaskDone/4IP(92,45%giảđịnh),257SubtaskDone/8IP. Không reimport WBS hoặc cộng đôi.265worklog SIMULATION ghi và đọc lại từng mục, tổng384giờ; native authoradmin, contributor giả định ghi riêng, no impersonation. Điểm minh họa5role với công thức/inputs giả định công khai tạiQAG3-299/comment10004, readbackverified. Không realQA/HR/rollout proof. Report và IDs: JIRA_MIGRATION_READINESS_2026-10-11.md, jira-bot/simulation-worklogs-scores-2026-10-11.json.

Mapping329 dự kiến giữ Done10009 vàInProgress3 (ID tồn tại cả3workflow), không có ToDo còn lại. inspect_scheme cuối vẫn10003; preview_scheme associate10004 lỗiPROJECT_NOT_VERIFIED_EMPTY. Current gateway/API không migration populated project và activation còn thiếu Jira gate tests; không fakeT01–T23/approvehash hoặc dùng UI vượt guard. Runtime10module evaluateComplete=true, jiraE2EVerified=false. Không publish/activation/A01–A05/monitorresume/KAN/SAM1/OpenProject/billing/key mutation. Phần37 giữ lịch sử rate429/partial; hiện phần dữ liệu đã complete, workflow rollout chưa đạt.

## 37. Classroom scenario PARTIAL, Jira429 — 11/10/2026

Owner explicitly requests wholeQAG3hypothetical work/dates/progress. Official MCP full4pages/329unique/11Epic53Task265Subtask verified; before snapshot jira-bot/simulation-before-2026-10-11.json. Plan49TasksDone(92.45%)/4TaskIP,10EpicDone/1IP,257SubtaskDone/8IP; labels qag3-simulation+academic-scenario-2026-10-11, visiblehypotheticalschedule07Sep–14Oct and originalcontent preserved. No due-date overwrite because field omitted/UNKNOWN; no historicaltimestamps/worklog/employee scores/testevidence fake. Pilot5readbackPASS with Jira bullet/trailing-space normalization.

ActualMCPsuccess:300complete updates =265Subtasks(257Done/8IP)+35TasksDone. QAG3-219/225/231description+labels succeeded, transitions errored and currentstatusUNKNOWN;26notedited(15Task11Epic). readgetIssue/listTransitions429,45sbackoffprobe429; stopwrites/no browserbypass/no inventedresettime. Fullfinalreadback incomplete. Exact progress journal jira-bot/simulation-progress-2026-10-11.json; audit JIRA_ACADEMIC_SIMULATION_2026-10-11.md. Migration/customscheme/A01–A05/monitorresumeNOTDONE; priorusertrialE2E/sourcehashguards kept. Planned92.45% is not current verifiedcompletion. No KAN/SAM1/OpenProject/config/credentials changes.

## 36. QA work bắt đầu, QAG3-6 In Progress — 11/10/2026

User yêu cầu chạy QA. Official identity/resources/JQL realQA53Subtasks isLast=true, trướcwrite allToDo. QAG3-6 ParentQAG3-2/QAassignee/sourceAUTH01 verified; transitions thực chỉ11/21/31; scheme10003. Nodepredicatefixtures và94Python regression/stdio rerunPASS, khôngproduct/transitionE2E. Preview bắt đầu testdesign→officialaddOrEditComment10003 ghi12case AC/expected/actualCHƯACHẠY, transition21 ToDo→InProgress succeeded. Assignee/Parent/checklist/labels giữ nguyên; khôngSIMULATEDPASS/Done/worklog/score hoặc52QA còn lại. No activation/migration/automationenable/monitorresume. Editablefield probe unavailable experimentcohort, khôngclaimfieldwritecapability. Audit `JIRA_QA_RUN_2026-10-11.md`.

## 35. Named-owner simulation development2.6.0 DEPLOYED — 11/10/2026

Owner yêu cầu account của mình làm QA/self-review cho học tập. Official MCP identity/resources/QAG3-2 PASS. Sửa 3 module QA-attest/current/Subtask-acceptance: real QA giữ PASS; đúng owner dùng nhãn qag3-simulation trước transition và SIMULATED PASS hoặc business SIMULATED ACCEPTED, cho phép self-assignment trong nhánh mô phỏng. Không mở mọi admin, fake QA, global transition hoặc bỏ reason/checklist/descendants/scope/freshness. Hash837884a1f8829990d99ae9456c56cb1312745f649db8d8c8f6af768cb78c517e; Node fixtures/preservation7modules/Forge lint/Jira10Boolean/94Python PASS. Forge deploy development exit0/Deployed2.6.0; MCP readbackcatalog10/policydescription mới, Taskv6/scheme10003 unchanged. Không issue write/329migration/A01–A05enable/monitorresume hoặc Jira E2E. Read-only pin thêm hash candidate, không thay tool approval/activation guards. Contract/rollback JIRA_ADMIN_SIMULATION_2026-10-11.md; architecture15.41. Không làm OpenProject.

## 34. Hiện hành: committed-data runtime10module COMPLETE, khôngE2E — 11/10/2026

Officialidentity/resources/QAG3-3PASS. Supplementarysource19tools thêmfixedinspect_expression_runtime reusepin605a58b1…/10modules/officialevaluate, khôngcallerURL/expression/context/actor hoặcissuewrite. Registeredlive10requestQAG3-1/2/3 responseverifiedproject/key/type/ownerPM/Boolean: PM=true/9gates=false, khôngengineexception. evaluationComplete=true nhưngjiraE2EVerified=false/pendingTransitionFieldsTested=false, khôngQApositive/transition/screens/actions/concurrencytests.94Pythonregression/stdioPASS. rollout-evidence.json chưa tồn tại; khôngfakePASS/hạguard/activation/migration/A01–A05enable/monitorresume hoặcForge redeploy. Detail JIRA_RICHTEXT_FIX_PREVIEW_2026-10-11.md; architecture15.40.

## 33. Hiện hành: RichText development2.5.0 DEPLOYED — 11/10/2026

Owner sau exactmanifest preview605a58b1… yêu cầu “cứ deploy”; Forge CLI pinneddeploydevelopment exit0/Deployed/version2.5.0/lintPASS. Hash605a58b13b101191226433def8e44ba950f958a17711220419a09b9eb175b3de verified trướcdeploy. Officialidentity/resources/QAG3-2 PASS; supplementaryreadback Taskv6/catalog10/association10003; majorversionlist10modules/0scope-function-remotes-services-egress/noLicense. Jira postdeploysource typecheck10/10Boolean,93Pythonregression/stdio rerunPASS. SourceVariant chỉphânbiệtsource, CLI riêngchứngminhdeploy. No reinstall/newpermissions/billing/activation/329migration/automationenable/monitorresume/QAimpersonation. RemainingLead/BA/FixBug/E2E/rolloutguard chưađạt, khôngfakeapprovalhash. Audit JIRA_RICHTEXT_FIX_PREVIEW_2026-10-11.md; architecture15.39. Mục32 làcandidatehistory, khôngtrạngtháilivemới.

## 32. Hiện hành: RichText type defect sửa local, chờ development deploy — 11/10/2026

Official identity/resources/QAG3-2 PASS. Supplementary registered MCP nâng check=type đã tìm4module baseline ba890f52… TypeError do description RichText vào helper Map/ADF. Candidate sửa5description reads trong4module, giữ10module/permissions/logicgates, hash605a58b13b101191226433def8e44ba950f958a17711220419a09b9eb175b3de. Jira type-check candidate10/10Boolean/allValid=true; Nodefixture RichText red→green, ForgelintPASS,93Pythonregression/stdioPASS. Đây là local candidate NOT DEPLOYED, khôngJiraE2E/activation/migration/A01–A05 hoặc monitorresume. Đã hỏi duyệt development exacthash; chưa có câu trả lời. Detail/rollback JIRA_RICHTEXT_FIX_PREVIEW_2026-10-11.md; architecture15.38.

## 31. Hiện hành: expression syntax PASS, xác minh đường migration — 11/10/2026

Supplementary source18tools thêm fixed read-only inspect_expression_validation; hash-pinned deployed manifest ba890f52…/10modules. Registered MCP live Jira analysis allValid=true/10valid=true, không type/runtime/E2E. 92Python Jira regression/stdio PASS. Official identity/resources/QAG3-2 PASS. Không Jira write/deploy/activation/automation hoặc monitor resume.

Đính chính migration: official PUT workflowscheme/project chỉ hỗ trợ project rỗng; không bỏ empty_project guard cho329issues. Browser đọc QAG3 Workflows→Switch Scheme wizard Step1of3, target scheme10004 có trong selector; Cancel, không Associate. Gate-first vẫn giữ: full Lead/BA/FixBug/retest và QA thật/E2E chưa đủ; không giả rollout evidence hoặc approval hash. Chi tiết và đường xử lý tại JIRA_MIGRATION_ROUTE_VERIFICATION_2026-10-11.md; architecture15.37.

## 30. Hiện hành: Epic development2.4.0 / inactivev7 VERIFIED — 11/10/2026

Ownerapprovedexactpreview317db13d/hashb19116fa…; registered qag3-admin apply_change VERIFIED. Independentreadback Epicv7/4f007f20-c611-4a35-aa8c-1c5083b6a2d7, Scope2 vàAccept6 screen10011+newgate. PreservationassertionsPASS6statuses/10transitions/oldPM+childDone+reason+Resolution/graph/layout/metadata. Scheme10003 vàonlyA01Disabled/readComplete verified aprèsapply. No329migration/automationenable/monitorresume/TaskSubtask/KAN/SAM1/OpenProject/HRwrite. Pendingpreview phrasing below retains before-apply history, notcurrent. Next realdependency: Task Lead/BA provenance, FixBugretest, scope/concurrency and Jira E2E.

Official session identity/resources/QAG3-1 PASS; supplementary Epicv6/catalognow10. Owner approvedmanifest ba890f52fc7aca64b73d4a360571935c759986d7b52f952525e3429723af715e, deploydevelopment2.4.0 Success2026-10-10T21:35:48.550Z; old8module/runtime/app bytepreservationPASS. NewEpicreadiness/acceptance dùng currentchildscope/PM/checklist/freshevidence/descendantsDone, no newpermissions. Nodefixtures/lint/91PythonregressionPASS, khôngJiraengine/E2E.

Registered newfixed preview_epic_delivery_gates17tools; preview317db13d-b076-4cf8-a30f-db89bd8d8ef8/hashb19116fa1fc7ad487597ec17940f4fb97b5e374296783bc4f05c7cd9e89dd3cb/APIerrors=[]/blockers=[] chờ ownerapproval, chưaworkflowwrite. Scope2 và Accept6 chỉscreen10011+newgate, giữoldgates/layout/Resolution. Deployment approval khôngmigration/automation. Details/rollback/limits JIRA_EPIC_DELIVERY_GATE_BATCH_2026-10-11.md; architecture15.36. Khôngmonitorresume/KAN/SAM1/OpenProject/HR.

## 29. Hiện hành: Subtask development2.3.0 / inactivev6 VERIFIED — 10/10/2026

Owner duyệt deployhash5c99687f…; Forge development2.3.0 Success2026-10-10T10:42:39.358Z/lintPASS, independentcatalog8validators. Owner duyệt preview9124e90c-4c89-46f1-864a-3031d45684b2/hash2b40297c57a4abf4854fd5cbcfd855ed79bce8e8eadd51bb440664b3f3e2df0d/APIerrors=[]; registered supplementary MCP apply_change VERIFIED. Independentreadback Subtaskv6/7ccb46c1-ea7e-48b4-99aa-d98d1f6b3e89: QA-attest+screen10010 Pass testing12, independentacceptance+screen10010 Approve4. PreservationassertionsPASS toàn graph/7statuses/13transitions/routing/layout/Resolution/oldreason. Officialidentity/resources/QAG3-4 smokePASS; khôngbrowser.

90Pythonregression+NodefixturesPASS, khôngJiraruntime/E2E. Scheme10003/A01Disabled/readComplete hiện hành; khôngmigration329issue/A02–A05enable/monitorresume/HR/KAN/SAM1/OpenProject. FullLead/BA/Epicready/checklist/FixBugretest/concurrency vẫnpending. Strict previous-assignee selfreview có thểchặn cả2PM, khôngxóahistory/bypass. QuyướcFixBugSubtask đã có trongjira-workflows.md; cần kiểmchứng marker/evidence/retest, khôngtự thêmBugtype vìmetadata3types. Chi tiếtapproval/audit/rollback tạiJIRA_SUBTASK_ACCEPTANCE_PREVIEW_2026-10-10.md; architecture15.35.

## 28. Hiện hành: Subtask acceptance candidate, chờ deploy duyệt — 10/10/2026

OfficialMCPidentity/resources/QAG3-4 PASS; SubtaskSupplementaryreadback v5/7statuses/13transitions. Localnewmoduleqag3-subtask-acceptance/manifest5c99687f…; existing7module unchangedhashassertionPASS. IndependentPMbusinessreview/QAcurrentdevelopment/historyassignee chốngbypass. Nodefixtures+Forgelint+90Python regressionPASS. Sourcefixedpreview tool16catalog, khôngnewAPIallowlist. Candidate/policy/rollback tạiJIRA_SUBTASK_ACCEPTANCE_PREVIEW_2026-10-10.md; architecture15.34. Deployapproval đã hỏi, chưa nhận/chưadeploy hoặcworkflowwrite của lôSubtask. No migration/automation/monitorresume/E2E/HR/KAN/SAM1/OpenProject.

Officialmetadatafulltotal3 xác minh QAG3 khôngBugtype; Blockslink10000 tồn tại. ChưatựthêmBugtype hoặcphânloạiTask. Đây là dependencyphảichốtcủalinkedBug/retestgate, khôngsuyTasktínhnăngIssue/Bugtracking làBugthật.

## 27. Lịch sử gần nhất đã VERIFIED: QA deployed2.2.0, Task inactivev6 — 10/10/2026

User duyệt deployhash9942ba51…: development2.2.0 Success, independentcatalog7modules. User duyệt exact preview24a2237f-7517-42b1-b9c3-ba9a8995eea0/hashe1415852687fa714f8d098622ffab2a7e74b2d60ffb87852f5d3bd18ea9f558e/errors=[]: supplementary registered MCP apply_change VERIFIED, Taskv6/fe305b00-242d-4bc2-bf6a-bdf7f6564591. QA-attest screen10010 tạiPass testing10; QA-current Approve13/Deploy14; PM-only Retest before release16 ReadyRelease→InTesting. Independent readback+preset preservation assertions PASS; original5modules/gates/layout/Resolution intact. No browser write.

89Python tests+Nodefixtures+Forge lint PASS, no Jira engine/QA session/E2E. API/catalog/deploy không nghiệm thu full gate. Scheme10003 unchanged; automationreadComplete onlyA01Disabled. No329migration/A02–A05enable/monitor resume/Epic/Subtask/KAN/SAM1/OpenProject writes. Full Bug/retest/Lead/BA/business reviewer/scope/concurrency gates vẫn pending. Approval/audit/rollback/nextwork JIRA_QA_TASK_GATE_BATCH_2026-10-10.md; architecture15.33 updated.

## 26. Lịch sử: QA candidate implement/test local — 10/10/2026

Official MCP preflight owner/resources/QAG3-2 PASS; getJiraUser QA Hung active=true, chưa chứng minh login/accept/test. Supplementary inspect_workflow task vẫnv5/catalog5validators. Thêm2candidate QA modules local, giữ nguyên5module cũ/runtime/app bằng hashbaseline assertion. Nodefixtures+Forge lint+88Python regression PASS. Không Jira engine/E2E/write/deploy mới. Preview/hash/rollback/remaining blockers JIRA_QA_GATE_DEPLOY_PREVIEW_2026-10-10.md; architecture15.32 updated.

Gate hiện hành vẫn inactive reason+Task acceptance cũ. Candidate không full Bug/retest/Lead/BA/business reviewer hoặc cross-issue concurrency; cần đường testing từ READY FOR RELEASE để xử lý stale, chưa sửa graph. Chờ duyệt lô deploy development7modules, rồi catalog-readback/preview workflow riêng trước ghi. Không migrate329items, enableA01–A05, resume monitor, sửa KAN/SAM1/OpenProject hay billing/token.

## 25. Lịch sử: chốt QA xác nhận, không yêu cầu CI — 10/10/2026

User chọn **dùng phương án QA xác nhận**. JIRA_QA_ATTESTATION_CONTRACT_2026-10-10.md ghi quyết định và thiết kế gate local: actor QA thật, evidence/version/Test/result/retest, xác nhận cũ mất hiệu lực sau rework/reopen/thay đổi liên quan, Bug chưa retest chặn nghiệm thu. QA account lấy từ mapping lịch sử, chưa xác minh acceptance/login lại trong lượt này; không impersonate và không xem owner/bot hoặc tên tự nhập là QA.

Chỉ cập nhật tài liệu local (apply_patch), không gọi Jira/browser/Forge hoặc thay manifest/rules; không suy đã triển khai gate từ việc chốt phương án. Không chạy tests mới trong lượt ghi quyết định; 88localtests ở mục24 là bằng chứng lượt trước. Bước tiếp: candidate expression + tests theo contract, preview lô kỹ thuật đầy đủ trước approval/apply. Giữ gate-first/no migration329issues/A01Disabled/A02–A05pending/botPAUSED theo readback lượt trước, chưa đọc lại live lượt này. Không CI/scopes/function/storage/egress mới hoặc OpenProject changes.

## 24. Lịch sử: reason gates inactive đã lưu và VERIFIED — 10/10/2026

Owner duyệt **Duyệt lưu lô reason gates inactive**. Fresh supplementary MCP versions khớp before. Browser fallback lưu Task→Epic→Subtask từng lần; inspect_workflow độc lập và semantic assertions PASS đúng diff được duyệt, giữ mọi graph/layout/conditions/Resolution/old validators. Không replay/rollback tự động.

Epicv6/e9bfab73-dc0c-46b1-9304-f5520e12f9a7: Reopen8/Cancel9/Restore10 có screen10011+freshreason. Taskv5/cd076ba7-57ee-455a-813b-c70e40453171: Reopen15 screen10010+freshreason giữPM. Subtaskv5/1afd7884-4080-4cfc-9a59-f9b789c7edfd: Reopen6 screen10010+freshreason, giữ hai nhánh assignee. Validator UI config empty, enabled by default; không có disabled=true hoặc expression override. Before/readback và ba saved screenshots tại jira-bot/qag3-reason-*-2026-10-10.*; batch JIRA_REASON_GATE_BATCH_2026-10-10.md ghi approval/result/rollback.

inspect_scheme sau lưu xác minh QAG3 vẫn10003; inspect_automation readComplete=true chỉA01 DISABLED, A02–A05 chưa tạo. Workflows inactive,329issue không migration/transition. 88Python+Nodefixtures PASS, Jira E2E NOT RUN. Reviewer/revision/retest/Subtask acceptance/Epic readiness vẫn chưa đủ; không gọi saved inactive là gate runtime acceptance. Bot giữ pause, không KAN/SAM1/OpenProject changes. Bước an toàn tiếp: primary-source research reviewer/revision gates, không thêm function/scopes/deploy trước preview/approval mới.

### Kết quả research reviewer/revision (chưa triển khai)

Nghiên cứu primary sources tại JIRA_REVISION_GATE_RESEARCH_2026-10-10.md: expression có changelogs/getNewestChangelog, actor và linked issues; không cần mặc định chuyển sang function/read scope. Parent agent đã mở lại official workflowValidator và expression types để đối chiếu. Bước nhỏ nhất tiếp theo là candidate expression dựa vào sự kiện review có actor thật và mốc rework/content revision; không xem checkbox hoặc issue.updated là provenance. Chưa có hợp đồng trusted revision/evidence hoặc sự kiện BA riêng, nên chưa viết/deploy module rồi tuyên bố đủ gate. Function/scopes chỉ là fallback cần preview/cost/approval riêng; chưa thay manifest. Không cam kết hard-cap0 hoặc multiissue atomic từ tài liệu.

## 23. Lịch sử: reason gate batch UI draft — 10/10/2026

User yêu cầu tiếp tục đủ gate trước migration. Official MCP preflight owner/resources/QAG3-2 PASS; transition-screen admin unsupported by discovery, disclosed browser fallback. Supplementary inspect_workflow verifies Epicv5/ad587970, Taskv4/3f2d44b0, Subtaskv4/5a32d28e (do not restore historicalv2). Full before snapshot saved via apply_patch: jira-bot/qag3-reason-before-2026-10-10.json.

Prepared UNSAVED browser drafts: Epic Reopen8/Cancel9/Restore10 screen10011 + qag3-fresh-change-reason; Task Reopen15/Subtask Reopen6 screen10010 + same validator. Existing gates/paths/layout/Resolution and Subtask assignee routing retained. No Update workflow clicked. Screenshots jira-bot/qag3-reason-{epic,task,subtask}-draft-2026-10-10.png and exact batch JIRA_REASON_GATE_BATCH_2026-10-10.md. Specific approval requested, not yet received at this checkpoint. Tabs must be handed off, not closed; fresh version check before save and independent MCP read-back afterward. Each save separate, stop/reconcile on partial failure, no replay or automatic rollback.

88Python local tests PASS and Node predicate fixtures PASS this turn; no Jira expression runtime/E2E or UI draft updateValidation errors=[] claim. Reason text is not verified truth; reviewer/revision/retest/checklist gates still incomplete. A03 automated reopen must satisfy same-transition freshness, not edit reason first or bypass. No migration329issues, activation, A01–A05 enable, KAN/SAM1, OpenProject or paused-monitor changes. Overall setup NOT COMPLETE.

## 22. Lịch sử: development2.1.0 và Task inactive v4 — 10/10/2026

Owner yêu cầu chạy tiếp/tự chọn bước trong scope đã duyệt, giữ gate-first/chưa migration. Official MCP atlassianUserInfo/getAccessibleAtlassianResources/getJiraIssue(QAG3-2) PASS: owner712020:0d04982c-00bf-46af-b3a7-446d0f44edfb, cloud560ef0cc-d24b-4613-98d3-d541afe8f32b, project10002, Task10011/ToDo10008. Discover workflow validators không expose admin write, dùng integration supplementary đã duyệt; không browser fallback phiên này.

Forge CLI deploy development **2.1.0** Success, source manifest hash48e05af89cdd43806749ed608db5e235767db5cf49bebf57460fbc432a48bc74 đúng preview trước. Jira capabilities độc lập nhận đủ5modules, gồm fresh reason/Task childDone/checklist. Không scopes/function/storage/egress mới, không đổi billing/install access; catalog presence không Jira transition E2E PASS.

Supplementary MCP thêm narrow preview_task_acceptance_gates, không endpoint/credential/scope mới; reuse inactive guard/catalog/current-version/preview900s/exact-hash approval/audit/readback. 88 local Python tests PASS gồm stdio; Node predicate fixtures PASS; deploy lint No issues found. Không coi tests local là Jira gates nghiệm thu.

Owner duyệt exact preview **a929d394-8131-4bd5-913e-a48d68426f6e**, SHA256 **bcddcbed8511ce63ff5a75d06ce30117a2b1aa3a858c9a957527ad4176d6c386**, Jira validation errors=[]. Registered qag3-admin apply_change trả VERIFIED, inspect_workflow độc lập đọc **Taskv4 /3f2d44b0-a179-4149-995e-3e4219cfea7c**: PM-only tại Approve13/Deploy14/Reopen15; Deploy thêm Task-subtasks-Done và delivery-checklist/evidence. Giữ native child blocking, Resolution, layout và graph. Readback trước apply là v3, không suy v2 cũ vẫn hiện hành.

Chưa gắn reason validator vào transition, chưa transition screens/reviewer/evidence revision/retest/Fix Bug/concurrency đầy đủ. QAG3 association vẫn10003 qua inspect_scheme, chưa migration/activation/issue writes; A01 giữ tắt, A02–A05 chưa tạo/bật và Jira E2E NOT RUN. Bot monitor PAUSED, không chấm cá nhân. Rollback Task cần before audit ngoài repo + phiên bản hiện hành + preview/approval mới; không tự uninstall khi workflow dùng validators. Mục21 trở xuống là lịch sử khi mâu thuẫn.

## 21. Lịch sử: gate-first; A01 DISABLED — 09/10/2026

Owner chọn **Hoàn thiện gate trước, chưa migration**, không rollout deny-all tạm thời. QAG3 vẫn scheme10003; UI migration Step1 chọn10004 nhưng chưa Associate. Official MCP identity/resources/project PASS đúng owner/site/cloud; full JQL4pages/isLast,329unique keys đều To Do10008. Snapshot jira-bot/qag3-before-migration-2026-10-09.json không nguyên tử; resolution omitted ghi UNKNOWN, không null. Không đổi issue/key/Parent/assignee.

Native rule **QAG3 A01 - Start Epic on Task delivery**, UUID01a1216a-82a7-7a79-9f26-8102e7f6a942 đã lưu **DISABLED**, riêngproject10002, qua browser admin fallback. Task delivery trigger → Parent QAG3 → re-fetch → Epic10000/READY10011 guard → In Progress. UI Saved/Disabled và supplemental inspect_automation exit0/readComplete=true xác minh1rule. Actor Automation557058:f58131cb-b67d-43c7-b30d-6b58d40bd077, không PM impersonation; A02–A05 chưa tạo/bật. Proof jira-bot/qag3-a01-disabled-2026-10-09.png; URL suffix RULE_TURNED_ON không phải state bằng chứng. A01 chưa runtime/replay/concurrency test.

Forge source local thêm3validators reason mới, Task childrenDone, Task delivery checklist/evidence; Node24 fixture PASS và Forge lint No issues found. **Chưa deploy/gắn rule**, full identity/revision/retest/concurrency gates và transition screens pending; development live vẫn2validators cũ. Jira E2E NOT RUN, monitor PAUSED, không chấm cá nhân. README Forge mô tả giới hạn; mục20 trở xuống là lịch sử khi mâu thuẫn.

## 20. Lịch sử: QAG3 Gate Fields v1 đã áp dụng — 09/10/2026

User duyệt copy/giữ cấu hình và thêm3field riêng QAG3. Field Scheme4 copy Default1/60field được đối chiếu không khác settings, thêm3field thành63; association chỉ project10002/QAG3, availability Epic/Task/Sub-task, required none. Field IDs10043 reason textarea,10044 checklist multicheckboxes,10045 evidence textarea; Global contexts giữ nguyên, scope qua field scheme không phải restricted context.

Hai dedicated screens10010/10011 đã append3field, giữ17field cũ và order; work type screen scheme10002 shared by1project/QAG3. Official MCP create metadata đọc đủ một trang/type: Epic total18, Task19, Subtask19, cả3field required=false, checklist8allowedValues IDs10020–10027. Supplemental definitions readComplete=true/count3. Không ghi issue/checklist/evidence giả. UI picker nhầm2field Actual end/start ở screen10010 đã gỡ chỉ association vừa thêm; final readback20field đúng cả2screen. Chi tiết và rollback tại JIRA_GATE_FIELDS_PREVIEW_2026-10-09.md, proof PNG trong jira-bot.

Tiếp tục: thiết kế/preview transition screens và validators dùng IDs thật, reason mới tại transition, checklist theo nhánh, evidence revision-bound và retest/lỗi hiện hành. Chưa workflow activation/mapping329issue/A01–A05/Jira E2E; monitor giữ paused, không chấm cá nhân. Không gọi field foundation là full gates hoặc overall setup complete. Trạng thái bên dưới là lịch sử nếu mâu thuẫn mục20.

## 19. Lịch sử: ba field được duyệt, một field đã tạo; cần đổi cơ chế scope

QAG3 Change reason/customfield_10043 đã tạo qua browser fallback sau official MCP preflight/discovery; supplementary MCP exit0/readComplete=true xác minh textarea. Default Global context10147 bị khóa project/type theo trải nghiệm Field Schemes mới. Chưa field checklist/evidence, screen/scheme/default/issue writes. Không replay create hoặc xóa field unused.

Default Field Scheme1 có60fields; Spaces panel liệt kê QAG3. Form Copy chuẩn bị QAG3 Gate Fields v1, chưa submit. Cần duyệt copy bảo toàn settings, thêm ba field/type availability và associate riêng QAG3, không sửa Default scheme. Nếu readback không bảo toàn cấu hình/scope thì dừng trước association; rollback association về1 phải preview riêng. Field scheme khác workflow scheme; chưa migrate329items/full gates/A01–A05/E2E. Monitor vẫn pause.

Preview/readback: JIRA_GATE_FIELDS_PREVIEW_2026-10-09.md. Ảnh: jira-bot/qag3-change-reason-created-2026-10-09.png và jira-bot/qag3-field-scheme-preview-2026-10-09.png. Browser copy form giữ handoff, không có action pending. Không lưu URL query chứa atl_token.

## 1. Phạm vi và bằng chứng

Dự án thật: `D:\AI project\QLDAPM chat`. Jira: https://luimjiraqldapm.atlassian.net.
Target: QAG3 / QLDAPM Agile Practice 3, project ID 10002, company-managed, board 3.
CloudId đã xác minh ở phiên trước: `560ef0cc-d24b-4613-98d3-d541afe8f32b`; bootstrap phải kiểm tra lại.
KAN không được thay đổi.

Đây là checkpoint phục hồi công việc, không phải biên bản nghiệm thu. Trạng thái Epic/Task dưới đây được quan sát trong công việc trước bootstrap; Subtask được đọc lại trực tiếp ngày 2026-10-09: Inactive workflow, Update workflow disabled, Approve work và Reopen mỗi chuyển có 1 rule. Không có thao tác Jira ghi mới trong bước lưu checkpoint này. Các cấu hình trước đó dùng browser UI đã công bố fallback, KHÔNG phải MCP.

## 2. Cấu hình đang có

| Workflow | ID | Trạng thái | Tiến trình |
| --- | --- | --- | --- |
| QAG3 Epic Lifecycle v1 | 5079dd5a-c3a9-4049-a1d7-70c0acc6a365 | Inactive; chưa ánh xạ QAG3 | 6 status, Create + 9 định nghĩa transition (Cancel đa nguồn) |
| QAG3 Task Delivery v1 | 9f21c6fc-718d-4f3c-aca9-49ab9c89c899 | Inactive; chưa ánh xạ QAG3 | 10 status, Create + 14 transition; Deploy có 2 rule, Reopen có 1 rule |
| QAG3 Individual Work v1 | 7512e21c-34cd-4fc8-baf4-9398f36f3e37 | Inactive; đã lưu, chưa ánh xạ QAG3 | 4 status, Create + 5 transition; Approve work/Reopen mỗi chuyển 1 rule |

Scheme đang gắn QAG3: 10003 / QAG3: Software Simplified Workflow Scheme.
Workflow mặc định đang dùng: 2bf6edf8-90ad-4092-92dd-63a10acf6041.
Loại công việc QAG3 đã quan sát: Epic 10000, Task 10011, Sub-task 10010.
Board mới ban đầu trống; Sprint QAG3 Sprint 1 chưa bắt đầu. Chưa kiểm tra lại số issue trong checkpoint.

### Epic

NEW → READY → In Progress → REVIEW → Done.
READY → NEW; REVIEW → In Progress; Done → In Progress.
Cancel Epic: NEW/READY/In Progress/REVIEW → CANCELLED; Restore: CANCELLED → NEW.
Chưa có gate tất cả Task Done, PM-only, lý do bắt buộc, rule Resolution cho Epic hay snapshot phạm vi.

### Task

NEW → IN ANALYSIS → READY FOR DEV → In Progress → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → READY FOR RELEASE → Done.
Code rejected: CODE REVIEW → In Progress; Bug found: IN TESTING → In Progress.
ReDev: REVIEW → In Progress; Retest: REVIEW → IN TESTING; Reopen: Done → In Progress.
Deploy đã cấu hình điều kiện Subtask ở Done. Đã thêm action Resolution Done và clear khi Reopen; số lượng rule đã quan sát nhưng nội dung action cần đọc lại trước kích hoạt. Chưa đủ checklist BA/PM/retest hoặc gate Bug.

### Subtask

NEW → In Progress → REVIEW → Done; Rework: REVIEW → In Progress; Reopen: Done → In Progress.
Approve work được thêm Resolution Done; Reopen clear Resolution; trạng thái lưu và số rule đã đọc lại. Chưa có gate reviewer/owner/lý do hoặc evidence.

## 3. Nhóm người dùng do chủ dự án cung cấp

| Email | Vai trò yêu cầu | Tình trạng |
| --- | --- | --- |
| nguyenduc6325@gmail.com | BE | AccountId và quyền dự án chưa xác minh; chưa mời/phân công |
| Duyhungls2005@gmail.com | Tester/QA | AccountId và quyền dự án chưa xác minh; chưa mời/phân công |
| ttheduy1401@gmail.com | FE | AccountId và quyền dự án chưa xác minh; chưa mời/phân công |
| hiepk40c@gmail.com | BA-PM, chủ tài khoản | Identity đã xác minh phiên trước; bootstrap kiểm tra lại |
| 2101minhkhai@gmail.com | PM | AccountId và quyền dự án chưa xác minh; chưa mời/phân công |

Ngân sách 0: không mua, không dùng trial trả phí/add-on JSU, không đổi gói.

## 4. Chưa hoàn tất

- Chưa gắn ba workflow riêng vào scheme QAG3.
- Chưa cấu hình đầy đủ quyền/gates/Resolution; chưa chứng minh hard gate Epic kiểm tra Task mới tại thời điểm nghiệm thu.
- Chưa có automation đối soát Epic, parent change, chống lặp hoặc snapshot.
- Chưa tạo/import WBS mới 11 Epic, 53 Task và Subtask phù hợp; không tính Burndown.
- Chưa có CSV mới, checklist nghiệm thu, phân công theo accountId thật.
- Chưa chạy 23 kiểm thử Jira trong jira-workflows.md; tất cả vẫn NOT RUN.
- Chưa triển khai chấm hiệu suất; dữ liệu mô phỏng không được coi là thành tích thật hoặc dùng quyết định HR.
- Không thay thế Jira bằng open source/local.

## 5. Tiếp tục sau bootstrap

Công việc Jira trên tạm dừng theo yêu cầu chủ dự án. Đọc AGENTS.md mới, jira-management.md, jira-workflows.md và kết quả audit trước khi tiếp tục.
Kiểm tra lại thực tế qua MCP; trình preview, tác động và rollback để xin duyệt những thay đổi tiếp theo theo quy tắc mới.
Không kích hoạt workflow hoặc import WBS khi hard gate/permission chưa đáp ứng hoặc chưa thống nhất giới hạn.

## 6. Checkpoint hiện hành — 2026-10-09 14:13 +07

Mục1–5 giữ lịch sử trước bootstrap. Công việc đã được người dùng yêu cầu tiếp tục; read theo `jira-management.md` mục11 và JIRA_ADMIN_MCP_SETUP.md trước hành động mới.

- Jira đã chuyển **Free** theo approval toàn site riêng ở lượt trước. Credential admin riêng do owner lưu đã xác thực, không cần tạo lại. Official atlassian và supplementary qag3-admin qua registered Codex app-server PASS account/site/QAG3. Supplementary ADMINISTER=true/ADMINISTER_PROJECTS=false; chỉ thao tác thực đã test mới VERIFIED.
- Approval mới **“Duyệt lô chuẩn bị này”** chỉ Epic Resolution và tạo scheme unused. `apply_change` Epic preview742a93ad-4fab-49fc-973d-58448ac7efcb VERIFIED: Epic5079dd5a **v3**, Accept Epic đặt Done/10000, Reopen+Restore clear. Không chỉnh gate/cạnh/trạng thái.
- `apply_change` scheme previewb62e6c37-93e8-47d0-9ed5-02c47dc14dae VERIFIED: **10004 / QAG3 Managed Delivery v1**, defaultTask, mappingsEpic10000/Task10011/Subtask10010→3workflow đã lưu. **QAG3 vẫn10003 sau read-back**, chưa associate/publish/enable. Taskv2/Subtaskv1 không sửa.
- 10 admin tools có preview/hash/900s/fresh-state/lock/replay guards/audit/readback; helper thêm --server allowlist/default atlassian, bot không đổi. 72/72 local Python PASS, không phải23JiraE2E. Automation scoped-read HTTP200/rules[]/readComplete=true, chỉ hỗ trợ đọc+disable existing; chưa create/edit/enable A01–A05. Guard của map/publish/associate/disable được kiểm thử mock, chưa ghi live các thao tác này.
- Audit ngoài repo `%LOCALAPPDATA%\QLDAPM\jira-admin-audit`; before/payload/started/result riêng, hash và rollback ở guide. Không retry các preview đã ghi. Khôi phục phải preview/current version/approval mới; để scheme10004 chưa dùng nếu dừng, không tự xóa.
- WBS v7 DRAFT đã có:11Epic/53Task/265Subtask, chưa nhập. Hard gates Epic–Task/PM-only/reason/checklist/concurrency và23JiraE2E còn chưa đạt; local reviewed-evidence rollout guard không thay gate Jira. Member invitation/assignability, automation templates/snapshot/assessment vẫn pending. Không bỏ gate để đạt “full quyền”.
- Không đổi AGENTS/admin quyền/role/token/scopes/billing/KAN/SAM1/issue/bot/lịch/Gemini trong lô chuẩn bị; no browser. Không goal complete/dừng lịch giám sát. Mỗi lô kích hoạt hoặc ghi sau đây cần preview/tác động/rollback và approval riêng.

## 7. Mời thành viên đã hoàn tất — 2026-10-09 14:39 +07

- Phiên official MCP đã preflight đúng owner/site/cloud/QAG3/10002/classic. User duyệt chính xác “Duyệt gửi 4 lời mời Jira User”; đã thực hiện **COMPUTER_USE_FALLBACK**, không gọi thao tác này là MCP.
- Admin Users đúng org2ce490bd-70de-4c97-aede-e693a5651adc: bỏ chọn các ứng dụng mặc định, chỉ chọn Jira User/Free, Administrator access=None, không Jira Administration, không group tùy chỉnh hoặc ứng dụng khác. Gửi một lần bốn email BE/Tester/FE/PM. UI thông báo **4 người dùng đã được thêm thành công**, từng dòng **Đã mời**, tổng5; owner không mời lại. Không khẳng định email đã được mở/accept.
- Official `executeRead(listJiraIssueAssignableUsers, project=QAG3)` trả đủ5 accountId, đối chiếu email/accountId với liên kết Users. Mapping tại **JIRA_TEAM_QAG3.json**; ảnh **jira-bot/jira-invitations-2026-10-09.jpg**. Vai trò nghiệp vụ không đồng nghĩa Jira project role; chưa phân công issue và không cấp admin cho PM.
- Read-back supplemental `inspect_scheme`: QAG3 vẫn10003. `inspect_automation`: rules=[]/readComplete=true. Official JQL đầy đủ QAG3: issues=[]/isLast=true. Epicv3 vẫn không conditions/validators trên Accept/Cancel/Restore; capabilities native child gate chỉ mô tả subtasks, connectRules=[]/forgeRules=[]. Chưa associate/publish/create-enable A01–A05/import329item.
- Phát hiện **vòng phụ thuộc trong guard local**: rollout_blockers yêu cầu T01–T23 PASS trước associate/publish và empty_project; nhưng T23 yêu cầu mẫu rồi toàn bộ WBS. Guard này chưa thể chứng minh bằng quy trình hiện tại. Không ghi evidence giả hoặc sửa guard để tự cho phép activation. Cần quy trình staged test được duyệt: gate/config validation trước test activation cô lập; E2E bằng mẫu; import đầy đủ cuối cùng/đối soát T23 sau import. Đây mới là đề xuất, không đổi hard gates.
- Primary docs mới xác nhận Jira expression `issue.childIssues` và Epic `stories` có thể truy cập child; **ứng viên**, không native validator đã cài. Forge workflow validator có expression, nhưng chưa triển khai/đọc scope/app/billing thực/kiểm thử T17 concurrency. Forge có free allowance, cũng có overage/billing; không tự cài app, bật billing hoặc hứa0đ. Thông tin mới không thay audit capability thực của site.
- Không chạy lại72unit tests hoặc23E2E trong lượt này; chỉ đọc/live verification và invitations. Không sửa MCP code/config/gates, AGENTS, WBS, bot/lịch/Gemini/snapshots hoặc KAN/SAM1. Setup/goal chưa complete. Cần authority bổ sung nếu triển khai app validator hoặc thay hợp đồng nghiệm thu.

## 8. WBS backlog DRAFT nhập đủ — 2026-10-09 15:11 +07 (hiện hành)

- Approval **“Duyệt nhập backlog nháp trước”**: 329 mục To Do/DRAFT, đúng năm accountId, checklist chưa hoàn tất, mẫu7 rồi toàn bộ; không start Sprint/bật automation/ghi số mô phỏng vào field thực. Chỉ thay thứ tự import, không đổi yêu cầu gate và không coi setup hoàn tất.
- Official MCP preflight đúng owner/site/cloud/QAG3/10002/classic, type3/assignable5; QAG3 rỗng lúc đầu, live To Do10008/In Progress3/Done10009. CSV v7 hash49368cf812189fa981cf6021f00353dc906b2c5015adc80bddcbc1d449535577 không sửa.
- Mẫu QAG3-1(E01), QAG3-2(AUTH-01), QAG3-3–7(five role Subtasks) tạo/readback đạt. **Đã nhập QAG3-1–329**, full final read4pages/isLast=true, verifiedAtUtc2026-10-09 08:11:19 UTC:11Epic/53Task/265Sub-task,329uniqueSource/key, parent và assignee đúng, nội dung/106AC/checklist được bảo toàn, toàn bộTo Do/timetracking rỗng. Notes kế hoạch không Sprint/blocks/estimate/worklog thực.
- MCP transport closed lúc tạo PRJ-03-QA; source read chứng minh QAG3-49 đã tạo, không replay. Giữ mapping/audit riêng `jira-bot/wbs-import-QAG3-2026-10-09.json` stateCOMPLETED_DRAFT_IMPORT; không xóa để rollback. Team metadata cập nhật assignment thật, không suy người nhận đã accept invitation.
- Chưa associate/publish workflow hoặc bật A01–A05; hard gate/PM-only/checklist/reason/concurrency/23E2E vẫn chưa đạt. QAG3 nay không rỗng: admin empty-project guard phải được thay bằng migration/status mapping hợp lệ qua preview/approval, không bypass. Import readback không biến toàn bộ T01–T23 thành PASS.
- Không code/config/admin permission/token/AGENTS/bot/runtime-cursor/lịch/Gemini/snapshot lịch sử/KAN/SAM1 hoặc Artifacts write. Không sửa mocktests hoặc tuyên bố chạy lại suite72. Chưa goal complete; bot giám sát tiếp tục. Chi tiết ở jira-management.md mục13/JIRA_WBS_GUIDE.md mục7/architecture.md15.14.

## 9. Bot giám sát tạm dừng — 2026-10-09 15:20 +07 (hiện hành)

- Theo user “tạm huỷ cái scheduled task đi”: monitor CodexPAUSED quaautomation_update/readback, Windows taskQLDAPM-Jira-MCP-MonitorDisabled/Stop. Child11636 xác minh CIM đúngpython/script/interval/parent/CreationDate rồi dừng; finalCIM0runner/wrapper. Không xóa cấu hình/state/events/reports hoặc thay dữ liệuJira.
- Lịch continuation riêng vẫnACTIVE; chỉ monitor bị tạm dừng. Không tự restart/resume monitor dù processmissing; cần user yêu cầu bật lại. JIRA_BOT.md mục11/architecture15.15 ghi bằng chứng. Không pause/complete goal hoặc coi setup xong từ việc dừng lịch; không thu collector/Gemini trong lượt này.

## 10. Task giữ ảnh, Subtask phân nhánh — 2026-10-09 15:38 +07

- User chọn Task đúng ảnh; Subtask BA/Tester/PM luồng4-stage, BE/FE qua Code Review và test trong luồng7-stage. Thay thiết kế Subtask chung4-stage, không thay hard gates. Official preflight identity/site/QAG3 và getJiraIssue/listJiraStatuses xác minh project còn3defaultstatus; supplementary inspect_workflow xác minh Taskv2 đúng graph, Subtaskv1 còn4status/inactive.
- Local MCP thêm `preview_subtask_delivery`,11tool; giữ scope/fresh approval/hash/audit/readback. 77tests Python PASS. Hai preview multi-value assignee failvalidation, không apply. NativeUI form xác minh Equals Assignee single-value, Cancel không lưu; condition ANY từng account được API validation errors=[].
- Preview19360e5d-993b-411a-b537-a95f5cac7746 hash13641cfd0ea81d320e62f3e6222e6617cb277137f546205d7b29dfac2035956f (900s) đang chờ approval riêng chỉ lưu inactive. Không apply_change, chưa activate/migrate329issue. Fixed-assignee routing không cấp security role; đổi assignee cần kiểm soát/test, không pretend QA/checklist/PM gate hoàn tất.
- Đọc jira-workflows.md13/architecture15.16 trước tiếp tục; cần Jira runtime role-route và migration/staged tests riêng. Monitor vẫnPAUSED/WindowsDisabled, không collector/Gemini/notification/write KAN/SAM1. Không goal complete.

## 11. Subtask inactive lưu thành công — 2026-10-09 15:50 +07 (hiện hành)

- User “ưu workflow inactive” được hiểu là approval trả lời câu hỏi lưu inactive. Official preflight identity/resources/QAG3-2 PASS, workflow-admin không có trong discovery. Supplemental registered MCP thực hiện ghi, không browser.
- Preview19360e5d bị STALE trước ghi; khác duy nhất UUID rule trong Task đọc về. Fix fingerprint chỉ bỏ rule object's id, giữ semantic fields/version/IDs; fresh preview766f1d95-7b15-412e-9964-95e9e961a345 hash62ea0b3d5366b53ab57afbc2058af17fcf0adfdccde93bcbe9a549aaf8868f46 validation errors=[], normalized approved content unchanged.
- Một update lưu Subtask7512e21c **v2**, 7status/13transition. Apply trả UNKNOWN/READBACK_MISMATCH vì API reorder transitions; KHÔNG replay. Inspect/readback/assertion đối chiếu theoID PASS, Taskv2 nguyên cấu hình, QAG3 association vẫn10003. Audit unknown giữ nguyên; `.reconciled.json` cùng preview ngoài repo ghi **VERIFIED_AFTER_READBACK_ERROR**, expected/actual/approval/rollback. Không giả apply tool đã trả VERIFIED.
- Sửa readback sort status/transition IDs, không reorder actions; regression FAIL trước/PASS sau.79localPython tests PASS + actual reconciliation assertion PASS; Jira role-route E2E chưa chạy. Architecture15.17/jira-workflows14/JIRA_ADMIN_MCP_SETUP cập nhật.
- Không activation/migration329issue/automation/role/plan/token/KAN/SAM1 write hoặc resume monitor. Chờ rollout/migration/gate plan riêng được duyệt; overallsetup chưa complete. Không gọi apply cùng preview đã started, không auto restore từ before.

## 12. Tiếp tục rollout sau các lượt ngắt ngày 09/10/2026

User yêu cầu hoàn tất activation/migration/gates/A01–A05/E2E/bot. Preflight official owner/site PASS, QAG3-2 To Do; supplemental scheme vẫn10003/rules[] complete. Preview associate10004 từ chối PROJECT_NOT_VERIFIED_EMPTY, không có write. Official API docs xác nhận endpoint chỉ dùng project rỗng; không được bỏ guard để migrate329issue.

Epic đọc lại version4, layout khác checkpointv3; conditions/validators Accept/Cancel/Restore vẫn thiếu. Giữ live layout/user changes, không restorev3. Gate Epic–Task cần phương án server-side bổ sung; Forge expression validator là ứng viên, chưa cài/đạt test/bảo đảm budget0. Xin quyết định app/scopes/cost trước khi triển khai app, không tự tăng quyền hoặc hạ hard gate. Không chạy E2E/activate/create-enable automation/score cá nhân/resume giám sát. Plan và primary sources tại JIRA_ROLLOUT_BLOCKERS_2026-10-09.md; không giả evidence hoặc lặp import WBS.

## 13. Chủ dự án duyệt tiếp tục; Forge gặp điều kiện phí tại bước tạo Space

- User: “ok, tôi cho phép bạn làm hết”. Cho phép tiếp tục mục tiêu QAG3, không thay ngân sách0 hoặc cho phép tự chấp nhận nghĩa vụ phí.
- Official MCP xác minh đúng owner/site/cloud; QAG3-2 đọc view full có project10002 và To Do10008. Không gọi một issue mẫu là snapshot329issue hiện hành.
- Browser fallback chỉ kiểm tra Developer Console vì MCP Jira không có thao tác này. Phiên đăng nhập đúng hiepk40c; menu Space không có Space hiện hữu, danh sách app trống. Mở form Create a Developer Space, CHƯA nhập tên hoặc bấm Create.
- Form ghi chủ tài khoản là administrator và chịu trách nhiệm any applicable usage charges. Tài liệu billing cho phép không thêm payment method trong free allowance nhưng không chứng minh hard cap0 khi vượt allowance: https://developer.atlassian.com/platform/forge/developer-space/billing-for-developer-spaces/ . Pure-expression validator vẫn là phương án đang xác minh, chưa được chứng minh chi phí0 bằng runtime/billing.
- Ảnh form: jira-bot/forge-developer-space-confirmation-2026-10-09.jpg. Giữ tab handoff để chủ tài khoản xem. Chưa tạo Space/app, cài Forge CLI, cấp app scopes, deploy validator, migrate, publish, tạo/bật rule, chạy E2E hoặc chấm cá nhân. Monitor giữ tạm dừng.
- Cần chủ tài khoản quyết định cụ thể về điều kiện phí trước khi gửi form; không xem broad approval là chấp nhận điều khoản hoặc cho phép phí vượt ngân sách. Không hạ gates để né bước này.

## 14. Developer Space đã tạo; Forge CLI chưa đăng nhập

- User xác nhận “ok” với câu hỏi tạo Space không payment method dù có overage risk. Browser Create **QLDAPM QAG3** success/readback; screenshot jira-bot/forge-space-created-2026-10-09.jpg. Cost dashboard $0/forecast$0/no apps, dữ liệu có thể trễ1h. Không thêm payment method, không đăng ký app hay accept app terms.
- Official MCP atlassianUserInfo/getAccessibleAtlassianResources/getJiraIssue QAG3-2 full PASS đúng owner/site/project10002/ToDo. discover không cung cấp Forge app registration.
- Cài CLI14.1.0 local tools/forge-cli/pin+lockfile trên Node bundled24.19.0, không global Node/MCP changes. Usage analytics=false. `forge whoami` trả Not logged in, chưa nhận Forge token. Không lấy token Jira admin khỏi DPAPI hoặc gửi token qua browser/chat.
- Nguồn nháp forge/qag3-validator: hai expression gates PM actor và Epic children nonempty/all Task Done. Predicate fixture tests PASS, không Jira lint/compile/runtime gate/E2E/concurrency proof. Chưa app ID, không deploy bản nháp như full gates.
- `npm audit`44findings/3critical; non-force audit fix giữ44. Chưa credential Forge/tunnel/public exposure; không giả audit sạch. Dependency execution risk cần review trước deployment, không auto force downgrade.
- Auth CLI cần chủ tài khoản tự tạo token app Forge và login qua keychain. Không thay scheme/workflows/issues/automation/sprint/assignee/KAN/SAM1 hoặc resume monitor. Overall setup chưa hoàn tất; architecture15.20 cập nhật.

## 17. Tiếp tục gate foundation — 09/10/2026

User duyệt tiếp tục phương án, không lặp xin quyền chung. Official identity/resources/getJiraIssue QAG3-2 PASS; Task create metadata16fields một trang đầy đủ, không field gate trên form. EditableFields cohort unavailable không gọi complete. Projecttypes đúng3 Epic/Task/Subtask; giữ Fix Bug Subtask theo WBS, không thêm type.

Supplementary registered MCP thêm inspect_gate_fields read-only,13tools; actual call readComplete=true/matchedCatalogCount0/fields[]. Pagination failclosed, không field write or token/global config changes. 87 local Python tests PASS được đối soát sau cập nhật; không Jira E2E. JIRA_GATE_FIELDS_PREVIEW_2026-10-09.md trình3field names/types/options/context-boundary/rollback và không coi manual flags là authenticated approval. Cần approval cụ thể field foundation trước ghi cấu hình; chưa fieldIDs và chưa gắn gate mới.

Official discovery automation hai cách không expose create/edit/enable. Primary public API rules/templates đọc có endpoints nhưng opaque component chưa được kiểm chứng; supplementary không thêm guessed create tool. Không activation/migration329issue/automation/monitor/score changes. Forge dependency risk vẫn chưa giải quyết. Mục16 là trạng thái Epic đã ghi trước đó.

## 16. Development install và hai gate Epic inactive đã VERIFIED

- Install session15503 kết thúc thành công. `forge install list`: đúng Jira/site, development Version2/Up-to-date, installation3d31bab5-2544-4a81-8012-3bcf21b1dc84. Catalog Jira có hai Forge validators; không API scopes/function/storage/egress.
- User duyệt preview ec2c3238-98ba-48b0-b61b-ea5770b607d7, SHA256 ec9f2d8b5bec00c2d8f5c96c84852ca2589747861371180a29023788a5f6b902, validation errors=[]. Registered supplementary MCP `apply_change` session59650 exit0/status VERIFIED; `inspect_workflow(epic)` độc lập xác minh version5/ad587970-0156-4760-8a3c-a98a7811470c.
- PM gate trên Approve scope/Accept Epic/Cancel Epic/Restore; child-nonempty/all-Task-Done gate trên Submit acceptance/Accept Epic. Giữ layout/actions/Resolution; không sửa Task/Subtask. Before/hash/result audit ngoài repo tại LOCALAPPDATA/QLDAPM/jira-admin-audit; rollback cần before + current version + preview/approval mới, không replay apply.
- Local MCP thêm `preview_epic_forge_gates`, catalog12tools; deterministic validator IDs, reject expression override/disabled/foreign catalog/active workflow. 83 local Python tests PASS sau sửa fixture catalog; predicate fixtures/lint PASS. Chưa transition thật, visibility/concurrency hoặc non-PM E2E.
- Chưa full checklist/reason/retest gates, activation/migration329issue/A01–A05/performance. Monitor giữ pause. CLI audit44/3critical chưa giải quyết; không coi lint là security acceptance. Setup tổng thể vẫn chưa hoàn tất. Mục15 dưới đây là checkpoint lịch sử trước install.

## 15. Forge login/register/deploy đã xác minh; install đang đối soát (lịch sử)

- Owner báo đã nhập token. Forge whoami PASS đúng owner/email/accountId; developer-spaces list đúng QLDAPM QAG3/a13a582a-3325-40f8-a025-d3d2dbe490ae. Official MCP identity/resources/QAG3-2 full preflight PASS; chưa đọc lại toàn329issue.
- Register dừng tại prompt Terms/Privacy/overage; user trả lời “Duyệt chấp nhận để đăng ký app” rồi mới submitYes. Register thành công **QAG3 Workflow Gates**, appf6f77ef8-978a-4e85-a3df-b30d3ef38d06; không tạo trùng, không copy token.
- forge lint No issues found, JS fixtures PASS. Deploy **development v2.0.0** success, CLI deploy list readback Success2026-10-09T10:39:28.011Z. install list trước cài: not installed anywhere. Không Production deployment, function/storage/egress/API scopes hoặc workflow writes.
- User duyệt chính xác “Duyệt cài development để kiểm tra” sau preview scope/rollback. Install đúng Jira/site luimjiraqldapm.atlassian.net/development đang chạy session15503, chưa có success/readback ở thời điểm ghi checkpoint. Không replay khi pending; chưa gắn rules hoặc activate/migrate/enableA01–A05/test runtime/performance/resume monitor.
- Supplemental Epic đọc lại v4, forgeRules trướcinstall=[]; native/gate thiếu không thay. CLI dependency warnings vẫn còn, không gọi lint sạch là dependency security acceptance; không tunnel hoặc build code/tài liệu bên ngoài không tin cậy.

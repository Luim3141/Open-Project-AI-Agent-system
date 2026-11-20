# QAG3 Forge validator — development deployment, gates still DRAFT

## Hiện hành: named-owner simulation development2.6.0 DEPLOYED — 11/10/2026

Manifest837884a1…; realQA giữ PASS, đúng owner có QA và Subtask self-review mô phỏng với nhãn `qag3-simulation` trước transition và `SIMULATED PASS`/`SIMULATED ACCEPTED`. Freshness/checklist/reason/descendants/scope giữ nguyên; no new scopes/functions/storage/egress/billing. PinnedCLIdeploy exit0/Deployed2.6.0; installedcatalog10 readback descriptions mới, Taskv6/scheme10003 unchanged. Node/lint/Jira10Boolean/94Python PASS, không migration/E2E/automationenable/monitorresume. Source backup `manifest.before-admin-simulation-2026-10-11.yml`; contract ../../JIRA_ADMIN_SIMULATION_2026-10-11.md. Các phần dưới là lịch sử.

## Hiện hành: RichText fix development2.5.0 DEPLOYED — 11/10/2026

Owner tiếpnhậnpreviewhash605a58b1… vàyêucầu“cứdeploy”. PinnedCLI actualdeploydevelopment exit0/Deployed/version2.5.0/lintPASS; no reinstall/permissions/billing. Installedcatalog10readback, sourcepostdeployJiratypecheck10/10Boolean;93PythonrerunPASS. Scheme10003/Taskv6 giữ nguyên, không329migration/A01–A05enable/monitorresume/JiraE2E. DeployCLI vàcatalog làbằngchứngriêng, khôngtựsuydeploytừsourceVariant. Audit ../../JIRA_RICHTEXT_FIX_PREVIEW_2026-10-11.md. Candidatephíadưới làhistory.

## Local source hiện hành: RichText fix candidate, chưa deploy — 11/10/2026

Manifest hash605a58b13b101191226433def8e44ba950f958a17711220419a09b9eb175b3de khác deployeddevelopment2.4.0/ba890f52…. LiveJira type analysis baseline tìm4TypeError do descriptionRichText vào helperMap/ADF; sửa đúng5description reads/.plainText trong4module, giữ10module/noPermissions/gatepolicy. CandidateJira10/10Boolean, fixtureRichText red→green/lint/93PythonPASS. KhôngtransitionE2E/Forge deploy/migration hoặcautomationenable. Preview/rollback ../../JIRA_RICHTEXT_FIX_PREVIEW_2026-10-11.md; chờownerexacthashapproval. Các deployment dưới là lịch sử live gần nhất, khôngchỉbảnsource đangdeploy.

## Hiện hành: development2.4.0 / Epic inactivev7 VERIFIED — 11/10/2026

Exactpreview317db13d/hashb19116fa… đượcduyệtvàapplyVERIFIED; independentEpicv7/4f007f20…/preservationPASS. Scope2 vàAccept6 screen10011+newgate; old6statuses/10transitions/rules/Resolution/layout giữ nguyên. Pendingwording below isbefore-applyhistory, khôngfullgate/E2E/activationproof.

Approvedmanifestba890f52… deploySuccess/catalog10; thêmEpicreadiness/acceptance, old8modules bytepreservationPASS. Nodefixtures/lint/91PythonregressionPASS, khôngJiraengine/E2E. Epicv6 chưaghi; preview317db13d/hashb19116fa… errors=[] chờexactapproval. Scope/currentdescendants/checklist/evidence không full Bug/reviewer/concurrencygate. Contract/audit/rollback JIRA_EPIC_DELIVERY_GATE_BATCH_2026-10-11.md; khôngmigration/automation/monitorresume.

## Hiện hành: development2.3.0 / Subtask inactivev6 — 10/10/2026

Approvedmanifest5c99687f… deploy2.3.0 Success; independentJiracatalog8validators. Approvedpreview9124e90c/hash2b40297c…/errors=[] applyVERIFIED; Subtaskv6 QA-attest Pass testing12 và independentPMacceptance Approve4, cả2screen10010. ReadbackpreservationPASS; Nodefixtures/90PythonregressionPASS. Taskv6 giữ nguyên; customworkflow vẫn chưa activeQAG3, khôngJiraE2E/fullBug/reviewer/scopegate/migration hoặcautomationenable. Audit/policy/rollback: JIRA_SUBTASK_ACCEPTANCE_PREVIEW_2026-10-10.md. Các mục candidate dưới đây là lịch sử.

Developer Space **QLDAPM QAG3** được tạo qua giao diện ngày 09/10/2026 sau xác nhận của owner. Không thêm payment method. Cost dashboard hiện $0, dữ liệu có độ trễ tới một giờ; đây không phải hard cap hoặc đảm bảo mọi lượt deploy miễn phí.

## Nguồn candidate: Subtask acceptance, chưa deploy — 10/10/2026

Localmanifest8modules:7deployed cũ byte-identical và1candidate qag3-subtask-acceptance. IndependentPMacceptance, businessreview riêng, QA-current chodevelopment theoassignment/statushistory, khôngxóaQA bằngreassignment. Nodefixtures/lint+90PythonregressionPASS. Deploymenthash/policy/screens/rollbackpending JIRA_SUBTASK_ACCEPTANCE_PREVIEW_2026-10-10.md; source8modules khôngđồngnghĩacatalog8. Liveverified vẫndevelopment2.2.0/Taskv6/Subtaskv5. KhôngfulllinkedBuggate hoặcE2E/migration.

## Deployment verified: development2.2.0 và Task QA gates inactive v6 — 10/10/2026

Owner duyệt manifest9942ba51…; deploy2.2.0 Success, independent Jira catalog7validators. Owner duyệt preview24a2237f/hash e1415852…; supplementary MCP apply VERIFIED và independent readback Taskv6: QA Pass testing+screen10010, current attestation Approve/Deploy, PM-only Retest before release→IN TESTING. Gate/Resolution/layout cũ preservation assertions PASS. Chi tiết approval/audit/rollback JIRA_QA_TASK_GATE_BATCH_2026-10-10.md.89Python localtests/Nodefixtures/lint PASS, chưa Jira E2E. Không migration hoặc automation enable; QA source deployed không nghĩa đầy đủ Bug/retest/business reviewer gates.

## Lịch sử: Candidate QA local — 10/10/2026, trước deploy

Nguồn hiện có7expression modules:5module deployed cũ giữ nguyên và2candidate QA attestation/current. Preview/hash/rollback/giới hạn tại ../../JIRA_QA_GATE_DEPLOY_PREVIEW_2026-10-10.md. Nodefixtures+Forge lint+88Python regression PASS. QA active xác minh official MCP, không giả đã login/test. Chưa full Bug/retest/reviewer gate; cần Jira engine/E2E và approval trước deploy/gắn workflow. Không migration/automation enable/monitor resume.

## Development2.1.0 đã xác minh trước candidate — 10/10/2026

Đã deploy development2.1.0 Success từ manifest48e05af89cdd43806749ed608db5e235767db5cf49bebf57460fbc432a48bc74; independent Jira catalog có5modules. Không thêm permissions/function/storage/egress. Owner duyệt exact previewa929d394/hashbcddcbed8511ce63ff5a75d06ce30117a2b1aa3a858c9a957527ad4176d6c386; Task inactivev4 lưu PM gate tại Approve/Deploy/Reopen, Deploy thêm childrenDone/checklist+evidence. Resolution/native conditions/layout giữ nguyên; reason module chưa gắn vì screens còn pending.88Python tests/Node predicate tests PASS, deploy lint PASS; Jira transition E2E NOT RUN. Scope/reviewer/revision/retest/concurrency gates chưa hoàn tất; không activate/migrate.

## Lịch sử gate local, chưa deploy — 09/10/2026

Owner chọn hoàn thiện gate trước, chưa migration. Nguồn local thêm3modules, development live vẫn chỉ hai modules cũ:

- `qag3-fresh-change-reason`: QAG3 Epic/Task/Subtask cần reason không trắng và khác reason trước transition sau trim, hỗ trợ String/ADF Map. Cần transition screen gửi field cùng transition; Edit trước rồi transition sẽ bị chặn có chủ đích. Lý do lặp phải bổ sung bối cảnh mới, không chỉ thêm khoảng trắng.
- `qag3-task-subtasks-done`: mọi child hiện thời phải là QAG3 Subtask Done10009; Task không có Subtask qua riêng predicate này. Không chứng minh QA hoặc khóa concurrent writes.
- `qag3-task-delivery-checklist`: đủ10020/21/22/25/26/27, đúng một trong10023/10024, evidence không trắng. Dành Deploy/Done, không dùng Approve trước deployment smoke. Không chứng minh danh tính reviewer, revision hay kết quả retest thật.

Node24 fixture tests PASS; Forge lint No issues found. Fixture chuyển kiểu Map/String sang JS và giả RichText chỉ để kiểm tra predicate; không Jira expression compilation/E2E. Chưa deploy/install/update workflow. Gate reviewer, Epic READY/scope, Fix Bug/retest, evidence revision-bound, screens và concurrency vẫn pending. Không gỡ PM/children-Done rules cũ.

## Phạm vi nguồn đã triển khai

`manifest.yml` chỉ có hai expression validators: PM actor là một trong hai account được duyệt; Epic có ít nhất một Task và mọi child là QAG3 Task Done10009. Chặn loại con khác để không bỏ sót công việc chưa phân loại. Không function, storage, scheduler, remote, egress hoặc API scope. App ID thật do Forge cấp: `ari:cloud:ecosystem::app/f6f77ef8-978a-4e85-a3df-b30d3ef38d06`, Space `a13a582a-3325-40f8-a025-d3d2dbe490ae`. Đã deploy development v2.0.0 ngày2026-10-09T10:39:28.011Z và gắn hai validators vào Epic inactive v5; chưa activate QAG3.

**CHƯA hoàn tất gate:** checklist có cấu trúc, lý do mới cho từng reopen/cancel, QA/retest/bug links, quyền chỉnh evidence, visibility/limits/concurrency và bảo vệ đường bypass khác. Không gắn hai validators này rồi tuyên bố đủ toàn bộ hợp đồng. Jira validator expression không phải transaction lock giữa nhiều issues.

## Kiểm thử local

Chạy Node24 với `test.cjs`. Tests dùng YAML parser đã có trong Forge CLI và JS VM với fixture tự tạo, không gọi Jira hoặc evaluate nội dung issue. Đây chỉ là test predicate; không chứng minh Jira expression compilation, đầy đủ child visibility, custom fields hoặc runtime E2E. Không lưu Jira rollout PASS từ tests này.

## CLI và xác thực

CLI cài local tại `tools/forge-cli`, pin14.1.0/lockfile, không global config MCP. Node bundled24.19.0; CLI usage analytics đã tắt. Owner đã tự đăng nhập bằng credential Forge riêng; agent không đọc token, không dùng token Jira admin DPAPI cho mục đích khác.

Owner đã tự login: `forge whoami` xác minh accountId `712020:0d04982c-00bf-46af-b3a7-446d0f44edfb`/hiepk40c@gmail.com. User duyệt Developer Terms/Privacy Policy rồi register một lần. `forge lint` No issues found, predicate fixtures PASS; chưa runtime/E2E. Development đã cài đúng site luimjiraqldapm.atlassian.net; install list xác minh installation `3d31bab5-2544-4a81-8012-3bcf21b1dc84`, Version2/Up-to-date. Jira catalog đã nhận hai validators.

## Epic inactive v5 — đã lưu và đọc lại

User duyệt preview `ec2c3238-98ba-48b0-b61b-ea5770b607d7`, SHA256 `ec9f2d8b5bec00c2d8f5c96c84852ca2589747861371180a29023788a5f6b902`; Jira validation errors=[]. Registered supplementary MCP `qag3-admin apply_change` trả VERIFIED; inspect_workflow độc lập xác minh Epic v4→v5, versionID `ad587970-0156-4760-8a3c-a98a7811470c`.

- PM validator: Approve scope, Accept Epic, Cancel Epic, Restore.
- Child-Tasks-Done validator: Submit acceptance, Accept Epic.
- Giữ layout/Resolution, không sửa Task/Subtask; chưa associate scheme, migrate 329 mục hoặc bật automation. 83 local Python tests PASS, không thay thế kiểm thử transition thật.

## Dependency risk

`npm audit` trên CLI14.1.0 ghi44 findings:4low/8moderate/29high/3critical. Một lần `npm audit fix` không force vẫn còn44 do dependencies vendor khóa; không downgrade major/override tùy tiện. Critical proxy-addr/shell-quote/websocket-driver chưa được đánh giá call graph đầy đủ; không suy mọi advisory đang exploitable hoặc CLI an toàn. Đã dùng CLI authenticated để register/deploy/install nguồn nội bộ expression-only; không tunnel/public server. Rủi ro dependencies chưa được giải quyết; lint PASS không phải security acceptance.

## Triển khai và rollback còn pending

Register/deploy/install và lưu hai gate Epic inactive đã được xác minh, không cần làm lại. Bổ sung gate còn thiếu và kiểm thử Jira engine trước staged migration QAG3. Không associate bằng endpoint project-empty, không xóa WBS. Gỡ app khi rule đang dùng làm transition bị chặn: phải restore workflow configuration/mapping có duyệt trước rồi mới uninstall. Không bật A01–A05 hoặc monitor từ bản nháp này.

Nguồn: [validator](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/), [expression types](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/), [billing](https://developer.atlassian.com/platform/forge/developer-space/billing-for-developer-spaces/).

# Workflow Jira — Epic, Task và Subtask

## Hiện hành — đồng bộ NEW dưới ba Epic hoàn tất, 13/10/2026

QAG3-243/274/299 giữ NEW; official MCP đã chuyển và full readback xác minh14Task+70Subtask NEW, Resolution rỗng. Parent/assignee/labels/summary/type/Start/Due giữ nguyên. Browser thêm rồi gỡ hai reset tạm có PM/freshreason/ParentNEW/screen10010/clearResolution; mọi original transition/gate/layout đã đối soát giữ nguyên. Taskv10, Subtaskv11; Forge2.21/Epic/A01–A05/billing/monitorPAUSED không đổi. Đây là sync một lần, không thêm permanent cascade. Audit: `JIRA_NEW_EPIC_RESET_2026-10-13.md`; trước/kết quả trong jira-bot/new-epic-reset-*.json. Đã dừng sau hoàn tất; phần dưới là lịch sử.

## Hiện hành — A01–A05 ENABLED toàn QAG3; Subtask runtime đã sửa — 13/10/2026

A01 giữ ENABLED; A02–A05 đã bỏ riêng điều kiện `labels = qag3-test`, vẫn scoped QAG3/10002. A03/A04 giữ `qag3-scope-approved`; A05 là bình luận @mention PM, không email, không QA/acceptance/performance evidence. A02 thêm native **To status = Done** để lọc event gốc, tránh nhận Approve khi JQL chạy muộn đã thấy Done. Read-only supplemental API đối soát actor, toàn bộ components và các thay đổi trigger chính xác; không nới quyền hoặc đổi billing. Rule bật không tự xử lý lại mọi issue đã Done trong quá khứ.

Forge development **2.21.0**, SHA256 `b8e9648dc25dc7f2c420612a2fbede46dd47837e50f12a2bcf4003fff6c645f7`,12 expression modules/no functions/scopes/storage/egress. Stage2.20.0 giữ11module cũ; owner duyệt gate hash `da7c55436b262ca7b064057521727bff19c020e2fbd91fa6939d675caad9316f`, apply VERIFIED và independent MCP read Subtask **v9/d9c8e3c0-0697-459c-aed8-c45924f8c6c7**. Approve4 có acceptance+freshness+history; không được gỡ một gate. Taskv8/Epicv9 giữ nguyên.

Native admin-labelled SIMULATION: BA/PM Approve/reopen PASS; BE và FE đã QA→Review→Done/ResolutionDone. Missing reason, saved QA reuse và QA stale sau đổi summary bị400 đúng; fresh retest cho phép Done. Task Approve13/Deploy14 PASS. Smoke khi Task332 **không có qag3-test**: A03 reason/status changelog12147; A02 IP→REVIEW12155; A04 hai auditSuccess c1982c55…/2b4dd41e… và changelog12159; A05 comment10012 đúng @Hiệp/event qag3-a05-10012-20261012203501197. Fixture332 Parent331/Done/test label đã phục hồi,335/336 Done; không ghi329WBS/timeline/3Epic đầuDone/KAN/SAM1, không resume monitor.

106 Python Jira regression +3 targeted tests, Node conjunction/freshness, Forge lint và12/12 Boolean PASS. Đây là targeted native verification, **không** fullT01–T23/non-PM identity/concurrency/exactly-once/linkedBug/Lead/BA qualification. Giữ lịch sử errors, không tạo rollout-evidence PASS. Chi tiết, bằng chứng và rollback: `JIRA_AUTOMATION_FULLSCOPE_2026-10-13.md`. Các mục dưới là diễn tiến lịch sử.

## Hiện hành — Subtask v8 / development2.19.0; BE vẫn bị chặn — 13/10/2026

- Approved Subtask additive QA freshness đã lưu/đọc lại v8 `e6aa1eac-47ea-40d4-966c-976e2267178a`: Approve work4 có cả acceptance và companion enabled, giữ screen10010/graph/Resolution/reason/routing. Không được gỡ một gate.
- Owner đã duyệt và deploy development2.17.0 (`dc5d99…`),2.18.0 (`9263d2…`),2.19.0. Bản cuối đúng SHA256 `98d21c680ca1c387d7e14f1e53e95b5c02c75a27d5e794de6cfded07b5025e54`; Forge lint PASS,11 module/no scopes/function/storage/egress/billing. Bản trước2.18.0 được giữ để rollback qua preview riêng; không uninstall app.
- Native fixture BA/PM QAG3-335 đã Approve4→Done, Reopen6 thiếu reason bị400, fresh reason→IP với Resolution clear; review/approve vòng2→Done. Official MCP cuối lượt xác nhận Done/ResolutionDone. Đây là fixture SIMULATION, không nghiệm thu sản phẩm/người thật.
- Native BE QAG3-336 đã đi Code Review→Ready for test→In testing→Pass testing→REVIEW. Approve4 vẫn400 trên cả2.17/2.18/2.19; lỗi2.19 tại `originalIssue.changelogs`, expensive operations limit10. Read-only2.19 Boolean/static6/BEtrue/runtime9 không chứng minh native transition PASS. Không retry unchanged hoặc đổi trạng thái giả để che lỗi.
- A01 ENABLED; A02–A05 ENABLED **chỉ labels=qag3-test**, không toàn329WBS. A04 native Parent reconciliation đã có Success; A05 hiện2commentactions/0email, **addCommentOnce=false cả2 nhánh**, frozen event guard/attempt marker vẫn giữ. Native issue-once từng chặn lượt review mới (audit a97ed01b…); sau sửa có comment10009 trên335 và10010 trên332. Marker/auditSuccess không tự chứng minh comment hoặc inbox delivery.
- QAG3-332 hiện CODE REVIEW sau thử review mới; QAG3-335 Done; QAG3-336 REVIEW. Chỉ fixtures331–336 trong qualification;329WBS/timeline/baEpic đầuDone/KAN/SAM1/monitorPAUSED giữ nguyên.
- Node predicate/conjunction/Task freshness chạy lại PASS; fixed saved-config verifier exit0 xác minh cả4rule enabled/testScope và A05 issue-once OFF/event-key dedup ON. Chưa full native BE/FE, stale/non-PM/concurrency hoặc project-wide rollout; không tạo rollout-evidence PASS.
- Bước tiếp: thiết kế lại truy vấn history với chi phí hữu hạn, đối chiếu native context và giữ đủ kiểm tra ever-assigned/QA provenance/staleness; cache-history đơn thuần đã thất bại. Thay đổi nguồn/deploy tiếp phải có preview/hash phù hợp, không dùng approval98… cho code khác.

Audit: `jira-bot/subtask-runtime-and-a05-final-2026-10-13.json`. Proof: `jira-bot/QAG3-A05-event-dedup-final-2026-10-13.png`. Các mục bên dưới giữ lịch sử từng bước, không phải trạng thái hiện hành.

## Hiện hành — active Taskv8/Epicv9 và automation qualification — 13/10/2026

Scheme10004/manualmigration đã hoàn thành trước lượt này. Taskv8 thêm QA-freshness Approve13/Deploy14; conjunction Forge2.16.0 đã native Approve/Deploy trênfixture332. Epicv9 Return7REVIEW→IP thêm screen10011/freshreason validator theo exactapproved batch; native missingreason bị400, A03reason+status12076verified. Subtask không đổi trong lượt. Không bỏ oldgates/layout/Resolution hoặc gỡ một gate trong QA conjunction.

A02–A05 ENABLED **chỉ qag3-test**, A01giữ nguyên; không coi là toàn329WBS qualified. A04 Parent reconciliationSuccess; A05 email thaynativecomment @mention PM theo approval, cảhai nhánh có comment AutomationforJira/auditSuccess. Native duplicate-comment guard+frozenkey/attemptmarker không atomic exactly-once; chưa fullSubtask/stale/non-PM/concurrency hoặc reviewer/Lead/BA/Bug gates. MonitorPAUSED; currentaudit `JIRA_QA_RUNTIME_FIX_2026-10-13.md`. CácmụcInactive/Disabled/migrationpending dưới là lịch sử.

## Hiện hành — sau manual migration và import A04/A05, 12/10/2026

Manual migration sang QAG3 Managed Delivery v1 đã hoàn thành ở phiên trước (không còn Inactive/scheme10003 như lịch sử bên dưới); baEpic đầuDone/timeline329 được ghi và đối soát trong `jira-management.md`. Lượt này không đổi workflow/gate/scheme hoặc issue. A01ENABLED; A02–A05 persistedDISABLED, scopedQAG3. A04/A05 mới import/native export+MCP readback verified, 288localcasesPASS nhưng chưa JiraE2E. A04 actor bị importer resetAutomationforJira, cần actor hợp lệ trước PM transitions. A05 là PM-coordinator draft policy, marker không atomic; chưa đáp ứng full exact reviewer/exactly-once mục8. Hợp đồng gate/qualification giữ nguyên, chưa bypass/enable. Audit: `JIRA_A04_A05_IMPORT_2026-10-12.md`.

## Triển khai mới nhất — 11/10/2026

Epicv7 Inactive có screen10011/readinessApproveScope2 vàacceptanceAcceptEpic6: PM/owner/currentTaskscope/freshevidence/checklist/currentTaskSubtaskDone. OldPM/childDone/reason/Resolution/6statuses/10transitions/layout preservedPASS. Approveddeploydevelopment2.4.0/catalog10/exactpreview317db13d/hashb19116fa… applyVERIFIED/independentreadback. Task/Subtaskv6unchanged. NoJiraE2E/migration/A01–A05enable/monitorresume; fullLead/BA/FixBugretest/scopeconcurrency pending. Contract/evidence/rollback JIRA_EPIC_DELIVERY_GATE_BATCH_2026-10-11.md vàcheckpoint30.

## Trạng thái triển khai mới nhất — 10/10/2026

WBS329mục đã nhậpDRAFT; associationQAG3 vẫn10003, ba customworkflows chưa active. Taskv6 cóQAattest/current vàPMretest-before-release; Subtaskv6 cóQAattestPass testing12/independentPMacceptanceApprove4/screens10010, giữ7statuses/13transitions/nativeassigneerouting/Resolution/reason. Deploydevelopment2.3.0/catalog8; approvedpreview9124e90c/hash2b40297c… applyVERIFIED/readbackpreservationPASS. KhôngfullLead/BA/Epic/FixBugretest/concurrencygates hoặcJiraE2E/migration/A01–A05enable. Monitorpaused. Proof/rollback tạiJIRA_SUBTASK_ACCEPTANCE_PREVIEW_2026-10-10.md vàcheckpoint29; phần cũ dưới giữ lịch sử đặc tả.

Cập nhật: 2026-10-09. **Đặc tả được người dùng phê duyệt; ba workflow đã lưu Inactive, chưa áp dụng vào dự án.** Checkpoint triển khai: [JIRA_PROGRESS_CHECKPOINT_2026-10-09.md](JIRA_PROGRESS_CHECKPOINT_2026-10-09.md). Quy tắc quyền/approval mới: AGENTS.md; audit phiên: JIRA_MCP_AUDIT.md.

Đây là quy trình quản lý phát triển, không phải workflow của sản phẩm QLDAPM. Nguồn yêu cầu: kế hoạch người dùng duyệt và sơ đồ Task được cung cấp. Tài liệu này là nguồn duy nhất cho cấu hình workflow mới; trạng thái triển khai và kết nối nằm trong [jira-management.md](jira-management.md).

## 1. Phạm vi và điều kiện triển khai

- Tạo dự án Jira Software **company-managed mới**. Không sửa project KAN, board 2, ticket hoặc scheme của dự án cũ.
- Đã tạo `QLDAPM Agile Practice 3`, key `QAG3`, project ID `10002`, Scrum board `3`. Đã đọc lại bằng MCP: `style=classic` (company-managed), gồm Epic `10000`, Task `10011`, Sub-task `10010`.
- Một Epic chứa nhiều Task chức năng đầu-cuối. Task lưu Story ID, câu User Story và Acceptance Criteria; Subtask là phần việc cá nhân, không thay thế Task chức năng.
- Phạm vi WBS: 53 Story đã chốt, 11 Epic chức năng, loại Burndown; không nhập đồng thời Story và Task trùng nội dung.
- Nhóm: 5 tài khoản thật, tương ứng PM, BA, BE, FE, Tester. Cần xác minh email/account ID và vai trò; không gán cả 5 vai trò cho tài khoản đang kết nối để giả lập quyền.
- Đã lưu ba workflow riêng Inactive với các cạnh theo kế hoạch: Epic 6 status, Task 10, Subtask 4. ID/rule và mức xác minh ở checkpoint; chưa gắn scheme QAG3. Task/Subtask có một số gate/Resolution, chưa đủ toàn bộ gates/roles. Automation và trường kiểm soát đầy đủ chưa tạo; CSV WBS v7 DRAFT local đã kiểm tra 11 Epic/53 Task/265 Subtask, chưa nhập. 23 E2E chưa chạy. Không coi tài liệu này là gói import áp dụng trực tiếp.

Workflow scheme ánh xạ từng issue type sang workflow; dùng scheme riêng của dự án mới, không sửa scheme chia sẻ. [Atlassian — workflow schemes](https://support.atlassian.com/jira-cloud-administration/docs/configure-workflow-schemes/).

## 2. Cấu hình chung

| Loại | Tên workflow dự kiến | Status category |
|---|---|---|
| Epic | QAG3 Epic Lifecycle v1 | NEW, READY = To Do; IN PROGRESS, REVIEW = In Progress; DONE, CANCELLED = Done |
| Task | QAG3 Task Delivery v1 | NEW, IN ANALYSIS, READY FOR DEV = To Do; từ IN PROGRESS đến READY FOR RELEASE = In Progress; DONE = Done |
| Subtask | QAG3 Individual Work v1 | NEW = To Do; IN PROGRESS, REVIEW = In Progress; DONE = Done |

Tên trên đã dùng cho workflow Inactive theo checkpoint; không phải ID Jira hoặc bằng chứng kích hoạt. Khi triển khai phải đọc ID issue type/status/role/field thực tế. Status category không thay thế nghiệp vụ: Task IN ANALYSIS đã bắt đầu làm dù thuộc nhóm To Do trên board.

- Issue type scheme chỉ gồm Epic, Task, Subtask cho WBS này; lỗi thực hành được theo dõi bằng Subtask Fix Bug dưới Task gốc, có loại công việc/nhãn phân biệt. Epic chức năng Bug tracking vẫn tồn tại để phát triển chức năng sản phẩm.
- Board Scrum riêng: Backlog/Sprint; NEW, IN ANALYSIS, READY FOR DEV ở nhóm chưa phát triển; các bước xử lý giữ rõ tên; cột hoàn tất ngoài cùng chỉ chứa DONE. Không gộp REVIEW hay READY FOR RELEASE vào Done.
- Bật Subtask, time tracking và estimation phù hợp dữ liệu WBS. Không đổi cấu hình toàn site nếu chỉ dự án mới cần.
- Resolution chỉ đặt tại DONE; Epic CANCELLED dùng lý do hủy tương ứng. Mọi chuyển từ DONE/CANCELLED về trạng thái hoạt động phải xóa Resolution; không xóa lịch sử hoàn tất.
- Flagged/Blocked + lý do + ngày mục tiêu là thông tin bổ sung, không thêm status.
- Không tạo global transition tới DONE hoặc CANCELLED làm đường vòng vượt gate.

## 3. Epic — phạm vi và nghiệm thu

### 3.1 Trạng thái

| Trạng thái | Ý nghĩa / điều kiện |
|---|---|
| NEW | Làm rõ mục tiêu, phạm vi và tiêu chí nghiệm thu. |
| READY | PM duyệt phạm vi; có owner, tiêu chí nghiệm thu và ít nhất một Task được duyệt. |
| IN PROGRESS | Ít nhất một Task đã bắt đầu phân tích hoặc thực hiện; các Task có thể ở những giai đoạn khác nhau. |
| REVIEW | Có ít nhất một Task trong phạm vi; toàn bộ Task đó DONE, chờ nghiệm thu Epic. |
| DONE | PM xác nhận mục tiêu, kiểm thử tích hợp và bàn giao; không còn lỗi chặn nghiệm thu. |
| CANCELLED | PM hủy có lý do; không tự hủy/xóa Task con. Không tính là Epic đã bàn giao. |

### 3.2 Chuyển trạng thái

| Từ | Sang | Hành động / quyền / gate |
|---|---|---|
| Create | NEW | Tạo Epic; chưa được coi là phạm vi đã duyệt. |
| NEW | READY | Approve scope — PM; owner, AC, >=1 Task và bản phạm vi đầy đủ. |
| READY | NEW | Reanalyse — PM; ghi lý do. |
| READY | IN PROGRESS | Start delivery — PM hoặc automation chuyên dụng; xác minh Task đã bắt đầu. |
| IN PROGRESS | REVIEW | Submit acceptance — PM hoặc automation; đọc lại toàn bộ Task thuộc phạm vi, không có Task chưa DONE và không rỗng. |
| REVIEW | DONE | Accept Epic — **chỉ PM**; kiểm tra hiện thời, checklist tích hợp/bàn giao đạt, không lỗi chặn. |
| REVIEW | IN PROGRESS | Return / scope changed — PM hoặc automation; ghi lý do và công việc còn lại. |
| DONE | IN PROGRESS | Reopen — PM hoặc automation khi Task hợp lệ được mở lại/thêm; lý do bắt buộc, xóa Resolution. |
| NEW, READY, IN PROGRESS, REVIEW | CANCELLED | Cancel Epic — chỉ PM, bắt buộc lý do; không đổi Task con. |
| CANCELLED | NEW | Restore — chỉ PM, ghi lý do, xóa Resolution; phạm vi phải được duyệt lại. |

Không hủy trực tiếp Epic DONE để làm mất kết quả đã nghiệm thu; nếu có sai sót, mở lại với lý do trước. Automation không khôi phục Epic CANCELLED và không nghiệm thu Epic.

## 4. Task — bàn giao chức năng đầu-cuối

Luồng chính: `NEW → IN ANALYSIS → READY FOR DEV → IN PROGRESS → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → READY FOR RELEASE → DONE`.

| Từ | Sang | Tên chuyển / trách nhiệm / điều kiện |
|---|---|---|
| Create | NEW | Create — lưu Story ID, Story, AC, Epic dự kiến và owner. |
| NEW | IN ANALYSIS | Start analysis — BA; bắt đầu làm rõ chức năng. |
| IN ANALYSIS | READY FOR DEV | Analysis done — BA; AC và phạm vi được duyệt, đủ dữ liệu để Dev thực hiện. |
| READY FOR DEV | IN PROGRESS | Start dev — BE/FE; nhận phần việc, có Subtask phù hợp. |
| IN PROGRESS | CODE REVIEW | Submit code — BE/FE; có bằng chứng triển khai và kiểm tra, phần việc Dev sẵn sàng review. |
| CODE REVIEW | IN PROGRESS | Code rejected — reviewer; ghi phát hiện và người sửa. |
| CODE REVIEW | READY FOR TEST | Approve code — reviewer được PM chỉ định; review đạt, bản Test sẵn sàng và có test case. |
| READY FOR TEST | IN TESTING | Start test — Tester; chỉ bắt đầu test execution sau gate này. |
| IN TESTING | IN PROGRESS | Bug found — Tester; tạo/liên kết Fix Bug Subtask, mức độ, bước tái hiện và Dev chịu trách nhiệm. |
| IN TESTING | REVIEW | Pass testing — Tester; có kết quả test/retest, không lỗi chặn và QA Subtask bắt buộc hoàn tất. |
| REVIEW | IN PROGRESS | ReDev — reviewer/BA/PM; yêu cầu sửa thuộc phạm vi đã duyệt, ghi lý do. |
| REVIEW | IN TESTING | Retest — reviewer/Tester/PM; ghi phạm vi kiểm tra lại. |
| REVIEW | READY FOR RELEASE | Approve — chỉ PM; Lead review → Retest nếu cần → BA xác nhận → PM duyệt, có bằng chứng từng bước. |
| READY FOR RELEASE | DONE | Deploy — PM/người triển khai được chỉ định; triển khai môi trường Test tập trung, smoke test đạt, Subtask bắt buộc DONE và checklist nghiệm thu đạt. |
| DONE | IN PROGRESS | Reopen — PM; lỗi/thiếu sót trong yêu cầu đã duyệt, ghi lý do, xóa Resolution và mở phần việc sửa/retest. |

Yêu cầu mới không đi tắt qua Reopen: tạo Task NEW và phân tích lại. “Lead” là trách nhiệm review được PM chỉ định trong nhóm, không tạo thành viên thứ sáu; không tự approve phần code mình làm. PM có thể thao tác thay khi có bằng chứng, không bỏ qua gate.

## 5. Subtask — công việc cá nhân

Luồng chính: `NEW → IN PROGRESS → REVIEW → DONE`.

| Từ | Sang | Quy tắc |
|---|---|---|
| Create | NEW | Một đầu ra kiểm chứng được; owner, vai trò, estimate, checklist và liên kết Task. |
| NEW | IN PROGRESS | Start work — assignee hoặc PM, ghi nhận bắt đầu. |
| IN PROGRESS | REVIEW | Submit work — assignee; checklist và bằng chứng hoàn thành đủ để reviewer kiểm tra. |
| REVIEW | DONE | Approve work — reviewer được chỉ định hoặc PM; kiểm tra theo loại việc. |
| REVIEW | IN PROGRESS | Rework — reviewer/PM; lý do và phần việc cần sửa bắt buộc. |
| DONE | IN PROGRESS | Reopen — reviewer/PM; lý do, xóa Resolution và giữ lịch sử. |

- BA: yêu cầu/AC; BE: logic/API/dữ liệu; FE: giao diện/tích hợp; Tester: test case/test execution/retest; PM: điều phối/nghiệm thu/bàn giao. Không bắt BA/Tester/PM đi qua CODE REVIEW.
- Subtask phải là phần việc có đầu ra, không chỉ chia nút/ô nhập nếu không có giá trị nghiệm thu độc lập. Chỉ chia UI khi hợp lý; cả BE, BA, QA, PM đều có phần việc phù hợp.
- Fix Bug có nguyên nhân, Dev gốc, bản sửa và kết quả retest. Tester không hoàn tất phần QA khi còn lỗi chưa sửa hoặc chưa retest.
- Mặc định mọi Subtask được tạo là bắt buộc. Không dùng nhãn “optional” để lách gate; phần việc loại khỏi phạm vi phải được PM duyệt và lưu audit trước khi xử lý cấu trúc.

## 6. Quyền, checklist và gates

Project role PM kiểm soát Approve scope, Accept Epic, Cancel/Restore Epic và Approve Task. BA/BE/FE/Tester chỉ có quyền phù hợp phần việc; người có quyền chỉnh sửa issue không mặc nhiên có quyền nghiệm thu.

Jira có điều kiện theo role, điều kiện chặn chuyển cha theo trạng thái Subtask và validator kiểm tra đầu vào trước transition. Cấu hình trên workflow và kiểm thử cả thao tác UI lẫn MCP; không chỉ ẩn nút UI. [Atlassian — advanced workflows](https://support.atlassian.com/jira-cloud-administration/docs/configure-advanced-issue-workflows/).

| Gate | Kiểm tra trước khi chuyển | Cách xác minh triển khai |
|---|---|---|
| Epic READY | PM, owner, AC, >=1 Task đã duyệt | Quyền role + dữ liệu phạm vi; chặn Epic rỗng. |
| Epic REVIEW | Có Task và tất cả Task hiện thời DONE | Kiểm tra trực tiếp Task của Epic, không nhầm với Subtask của Task. |
| Epic DONE | PM + kiểm tra lại Task hiện thời + tích hợp/bàn giao + không lỗi chặn | Cần gate server-side cho quan hệ Epic–Task; không dùng riêng cờ do automation cập nhật trước đó. |
| Task READY FOR RELEASE | Lead/BA/PM duyệt, retest đạt hoặc ghi rõ không cần | Checklist có reviewer, thời điểm và bằng chứng; thiếu bước thì chặn. |
| Task DONE | Mọi Subtask bắt buộc DONE, checklist đạt, deploy Test + smoke đạt | Sub-Task Blocking Condition cùng validator/kiểm tra checklist có cấu trúc. |
| QA Subtask DONE | Không lỗi mở/chờ sửa/chờ retest trong phạm vi kiểm tra | Đối chiếu Fix Bug và kết quả retest, reviewer chịu trách nhiệm. |
| Reopen / Cancel / Restore | Role hợp lệ và lý do không rỗng | Transition screen + validator; Resolution đặt/xóa đúng. |

Các tên dữ liệu sau là **nhãn nghiệp vụ dự kiến, chưa phải custom field ID đã tạo**: Scope version, Scope approval, Change reason, Blocking bugs, Lead review, Retest result, BA acceptance, PM approval, Test deployment evidence. Chọn field có cấu trúc và transition screen thực tế; checklist văn bản trong Description không đủ làm gate tự động tin cậy.

Kiểm tra UI thực tế: rule `Restrict based on the status of subtasks` chỉ có cấu hình `Check that subtasks are in`; không có lựa chọn Epic children. Đã hủy thử cấu hình rule này, không gắn vào Epic. Danh mục rule native hiện thấy không có validator kiểm tra trực tiếp trạng thái toàn bộ Task của Epic. Đây là giới hạn đã quan sát, không khẳng định mọi phương án Jira đều không hỗ trợ.

Ứng viên lịch sử đã loại khỏi triển khai vì ngân sách 0: JSU Automation Suite for Jira Workflows của Appfire; tham khảo trước đó ở [tài liệu nhà cung cấp](https://appfire.atlassian.net/wiki/spaces/JSUCLOUD/pages/12518578/Workflow%2Bvalidators) và [Marketplace](https://marketplace.atlassian.com/apps/5048/jsu-automation-suite-for-jira-workflows?hosting=cloud&tab=overview). **Chưa cài; không cài/trial hoặc mua app này.** Chưa chứng minh Epic rỗng/concurrency. Không tự thay hard gate bằng kiểm tra thủ công; giải pháp thiếu gate vẫn cần quyết định thay đổi yêu cầu hoặc phương án miễn phí được xác minh.

Điểm chặn triển khai: tài liệu Jira xác nhận Sub-Task Blocking Condition, nhưng chưa xác minh native gate đọc mọi Task của Epic, quyền chỉnh sửa từng trường duyệt và tính nguyên tử khi nhiều issue thay đổi đồng thời trên site này. **Không thay thế hard gate bằng automation trả trạng thái sau khi đã Done.** Nếu cấu hình hiện có không đáp ứng, báo rõ giới hạn và xin quyết định giải pháp bổ sung; chưa mua/cài add-on hoặc tự xây dịch vụ mới.

Automation actor chỉ được dùng các cạnh Start delivery / Submit acceptance / Return / Reopen cần thiết; không cấp role PM để vượt gate. Phải kiểm tra actor thực tế và điều kiện role tương ứng trên site trước khi bật.

## 7. Thay đổi phạm vi và tiến độ

### 7.1 Phê duyệt và xử lý

- BA tạo đề xuất trong Backlog; chưa đưa vào Parent Epic thuộc phạm vi được duyệt cho tới khi PM duyệt.
- Epic IN PROGRESS nhận Task mới đã duyệt: giữ trạng thái. Epic REVIEW nhận Task chưa DONE: trở lại IN PROGRESS.
- Epic DONE có lỗi/thiếu sót thuộc phạm vi đã nghiệm thu: PM mở lại với lý do, liên kết Task sửa; khôi phục trạng thái hoạt động và xóa Resolution.
- Tính năng mở rộng phiên bản sau: mặc định tạo Epic mới và liên kết Epic cũ, giữ kết quả bàn giao cũ. Chỉ thêm vào Epic DONE khi PM quyết định rõ ràng, lập phiên bản phạm vi mới và mở lại Epic.
- Đổi tiêu đề, sửa chính tả, comment hoặc assignee không tự mở Epic.
- Epic CANCELLED không tự mở khi child thay đổi; cảnh báo PM để quyết định khôi phục hoặc chuyển việc.
- Không xóa Task để cải thiện tỷ lệ. Parent thay đổi là thay đổi phạm vi phải đối soát hai Epic.

Audit mỗi thay đổi: Change ID, Epic, phiên bản trước/sau, người đề xuất/người duyệt, lý do, Task thêm/bớt, Point tăng/giảm và ảnh hưởng ngày mục tiêu, thời điểm áp dụng. Lưu bản đã duyệt; chỉnh sửa tiếp tạo phiên bản mới thay vì sửa lịch sử.

### 7.2 Hai số liệu tách biệt

- **Tiến độ hiện tại** = số Task DONE / tổng Task thuộc phạm vi hiện tại được PM duyệt; không cộng Subtask lần nữa.
- Epic rỗng: “Chưa có phạm vi”, không 100%, không tự REVIEW/DONE.
- Ví dụ: 4/5 = 80%; thêm một Task được duyệt thành 4/6 = 66,67%. Ghi nhận thay đổi phạm vi, không trừ lại thành tích đã chốt.
- **Cam kết Sprint**: snapshot khi chốt kế hoạch Sprint; kết quả/điểm hiệu suất đóng băng khi Sprint kết thúc. Nghiệm thu Epic có snapshot riêng. Mỗi snapshot lưu tập issue ID, scope version, Point, assignee, thời hạn và kết quả theo thời điểm đó.
- Sửa/mở lại sau chốt tạo sự kiện hoặc kỳ đánh giá mới; không ghi đè snapshot cũ. Chỉ sửa dữ liệu sai qua bản điều chỉnh có lý do, giữ bản gốc.

## 8. Automation — hợp đồng triển khai

Chỉ áp dụng project ID mới đã xác minh. Đọc issue type ID, Parent và trạng thái hiện thời trước mỗi hành động; không chạy bằng điều kiện rộng toàn site. Không có rule tự Epic DONE.

| Rule | Trigger | Kiểm tra và hành động |
|---|---|---|
| A01 Start Epic | Task chuyển từ NEW sang IN ANALYSIS hoặc bắt đầu thực hiện hợp lệ | Parent Epic READY và Task thuộc phạm vi đã duyệt → Epic IN PROGRESS. |
| A02 Ready for acceptance | Task chuyển DONE | Đọc lại đầy đủ Task của Epic; >=1 Task, tất cả DONE, Epic IN PROGRESS → REVIEW. |
| A03 Reopen Epic | Task được mở lại, hoặc Task chưa DONE được tạo/gắn vào Epic | Scope approval hợp lệ; Epic REVIEW/DONE → IN PROGRESS, xóa Resolution và audit lý do. |
| A04 Reconcile Parent | Parent của Task thay đổi | Lấy Parent cũ và mới từ change event; đối soát cả hai. Epic cũ còn việc chưa DONE hoặc rỗng thì không giữ REVIEW sai; tất cả DONE thì chỉ tới REVIEW từ IN PROGRESS. Epic DONE cũ không tự nghiệm thu lại hoặc bị mở vì chỉ bỏ Task; thay đổi phạm vi vẫn phải được PM duyệt. Epic mới theo A01/A03/A02; không tự DONE. |
| A05 Review notification | Task/Subtask thực sự vào giai đoạn cần review | Gửi đúng reviewer của bước, một lần cho mỗi lần đi vào bước; sự kiện lặp không gửi lại. |

### 8.1 Đối soát và chống lặp

- Chỉ lắng nghe thay đổi nghiệp vụ cần thiết; sửa Summary/Description không kích hoạt A03. Kiểm tra source status để tránh chuyển cùng trạng thái.
- Lấy dữ liệu child đầy đủ, kể cả phân trang; rỗng/không đủ quyền/lookup lỗi → dừng và ghi lỗi, không suy diễn “tất cả Done”.
- Re-fetch trước transition, không dựa riêng vào issue trong trigger. Parent cũ bị thiếu trong event → báo cần đối soát, không đoán.
- Audit key tối thiểu: project + issue + change event + hành động. Reviewer notification phân biệt một lần vào REVIEW mới với replay của cùng sự kiện.
- Không bật cho automation tự kích hoạt nhau nếu không cần. Khi cần chain phải kiểm tra cạnh và trạng thái, không dùng rule ping-pong.
- Lần chạy trùng phải là no-op nếu đích đã đúng; chỉ ghi audit/notify khi có thay đổi thật. Chưa chứng minh fresh-read + status check bảo đảm exactly-once dưới concurrency: phải thử replay và hai lần chạy song song trên Jira.
- Automation thất bại/quota hết/không đủ quyền → PM nhận thông tin lỗi có issue/rule/run ID; không coi trạng thái cũ là chứng cứ gate đạt. Số liệu/dashboard là eventual consistency, nghiệm thu phải kiểm tra trực tiếp.
- Task DONE có Subtask mở lại cần cảnh báo PM, chặn nghiệm thu Epic bằng dữ liệu child hiện thời; PM mở lại Task để sửa/retest. Không thêm rule ngoài kế hoạch mà không ghi quyết định.

## 9. Vận hành từ Codex và hiệu suất mô phỏng

Trước mọi lệnh ghi: đọc project ID/key đã xác minh trong runbook, issue hiện thời, transition khả dụng và quyền. Tìm theo Source ID trong **đúng project mới**, không fallback sang KAN nếu không tìm thấy.

Các yêu cầu người dùng có thể dùng sau khi triển khai:

- “Đưa Task <key> vào Code Review, đính kèm bằng chứng <...>.”
- “Đề xuất thêm Task <...> vào Epic <key>; trình PM duyệt phạm vi.”
- “Nghiệm thu Epic <key>: kiểm tra gate rồi cho tôi biết còn thiếu gì.” Chỉ chuyển DONE khi người dùng được xác minh là PM và gate đạt.
- “Chốt Sprint <id> và đánh giá hiệu suất mô phỏng theo yêu cầu bài thực hành 3.”

Các câu trên là yêu cầu thao tác, không phải CLI/API đã triển khai. Không báo cập nhật thành công trước khi đọc lại Jira.

Hiệu suất: giai đoạn 28/08–02/11/2026 là **mô phỏng**, 5 Junior, 8 giờ/ngày, 5 ngày/tuần. Theo quy ước bài tập 1 Point = 1 giờ Junior, không phải chuẩn chung ngành. Phân biệt estimate, actual, Point được nghiệm thu, Bug của phần việc và thay đổi phạm vi; không cộng đôi Task/Subtask. Đánh giá theo vai trò và bằng chứng, không quy lỗi cá nhân nếu chưa xác định nguyên nhân.

Chỉ chấm khi người dùng ra lệnh chốt Sprint; không bật lịch nền. Dữ liệu thời gian/bug giả định phải mang nhãn mô phỏng; không giả mạo worklog author hay Jira changelog của 5 người. Cơ chế snapshot/đánh giá AI chưa được xây hoặc kiểm thử trong bước chuẩn bị này.

## 10. Trình tự triển khai và rollback

1. Đã xác minh phiên Jira và quyền UI tạo company-managed project/workflow; MCP hiện chưa cung cấp operation quản trị cần thiết.
2. Đã tạo QAG3 / ID 10002 / board 3; không chia sẻ cấu hình với dự án cũ. Dự án hiện vẫn dùng workflow mặc định, chưa dùng để vận hành WBS.
3. Tạo 3 workflow + workflow scheme + issue type scheme riêng, publish, ánh xạ Epic/Task/Subtask; kiểm tra không có dự án khác dùng scheme này.
4. Xác minh 5 tài khoản, project roles, permission scheme, reviewer và automation actor. Cấu hình checklist/trường, Resolution, hard gates; xác minh giới hạn site trước khi tiếp tục.
5. Tạo rule scoped dự án mới ở trạng thái tắt, kiểm tra cấu hình rồi bật từng rule cho mẫu thử; lưu rule ID, version và audit.
6. Chạy toàn bộ test mục 11 với tài khoản PM và non-PM thật. Gate/quyền/concurrency không đạt → dừng trước import toàn bộ.
7. Tạo CSV WBS mới từ 53 Story: Epic → nhiều Task chức năng → Subtask phù hợp vai trò; kiểm tra source ID, parent, AC, estimate, checklist, assignee và không trùng; chạy import mẫu trước import toàn bộ.
8. Đối soát số lượng, Parent, assignee, trạng thái, Story/AC và audit sau import; cập nhật architecture/runbook với cấu hình thật và kết quả thử.

Rollback: lưu ID, bản cấu hình trước/sau và danh sách issue thử; tắt các rule mới trước khi sửa. Không xóa dự án hoặc ticket đã nhập để rollback tự động. Chỉ khôi phục scheme của **dự án mới** khi xác định đúng mapping dữ liệu và được phép; không tác động KAN. Sample issue giữ nhãn test/excluded-from-performance để không làm sai dữ liệu bài tập.

## 11. Bộ nghiệm thu — chưa chạy trên Jira

Mỗi test lưu issue key, tài khoản/role, thao tác, kết quả đọc lại, audit/run ID và PASS/FAIL. Hiện tất cả **NOT RUN**; kiểm tra văn bản cục bộ không phải Jira E2E.

| ID | Tình huống | Kết quả yêu cầu | Trạng thái |
|---|---|---|---|
| T01 | Epic rỗng yêu cầu READY/REVIEW/DONE | Bị chặn; tiến độ “Chưa có phạm vi”. | NOT RUN |
| T02 | Epic có một Task chưa DONE, PM yêu cầu DONE | Bị chặn trước transition. | NOT RUN |
| T03 | Task cuối cùng DONE | Epic chỉ tới REVIEW, không tự DONE. | NOT RUN |
| T04 | PM nghiệm thu đủ điều kiện | Epic DONE, Resolution đúng, snapshot nghiệm thu lưu. | NOT RUN |
| T05 | Task bắt đầu phân tích trong Epic READY | Epic IN PROGRESS một lần. | NOT RUN |
| T06 | Thêm Task đã duyệt chưa DONE vào Epic REVIEW/DONE | Epic IN PROGRESS, clear Resolution khi mở lại, audit đúng. | NOT RUN |
| T07 | Mở lại Task của Epic DONE | Epic IN PROGRESS; giữ lịch sử bàn giao cũ. | NOT RUN |
| T08 | Chuyển Task sang Epic khác; Epic cũ còn việc, all Done hoặc rỗng | Cả hai được đối soát; không auto DONE, rỗng không 100%. | NOT RUN |
| T09 | Sửa tiêu đề, câu chữ, comment hoặc assignee | Không tự mở lại Epic. | NOT RUN |
| T10 | Non-PM dùng UI và MCP để nghiệm thu/hủy/khôi phục Epic | Bị từ chối; không có transition/API đường vòng. | NOT RUN |
| T11 | PM hủy và khôi phục với/không lý do | Thiếu lý do bị chặn; có lý do hợp lệ, child không tự bị hủy, restore về NEW. | NOT RUN |
| T12 | Task xin DONE khi Subtask chưa DONE hoặc checklist chưa đạt | Bị chặn trước transition. | NOT RUN |
| T13 | Tester hoàn tất QA khi còn Fix Bug chưa retest | Bị chặn; retest đạt mới hoàn tất. | NOT RUN |
| T14 | Code rejected, Bug found, ReDev, Retest, Task/Subtask Reopen | Đúng cạnh, role, lý do; Resolution được xóa khi reopen. | NOT RUN |
| T15 | BA/Tester/PM thực hiện Subtask | Chỉ 4 trạng thái; không cần CODE REVIEW. | NOT RUN |
| T16 | Replay cùng event và 2 event chạy đồng thời | Không duplicate transition/audit/notification; trạng thái hội tụ đúng. | NOT RUN |
| T17 | Thêm/mở Task đồng thời với PM Accept Epic | Không nghiệm thu khi gate hiện thời không đạt; nếu không bảo đảm, ghi FAIL và chặn rollout. | NOT RUN |
| T18 | Đổi scope sau chốt Sprint | Tiến độ hiện tại thay đổi; snapshot/điểm kỳ cũ không bị ghi đè. | NOT RUN |
| T19 | Scope mở rộng phiên bản sau | Tạo Epic mới liên kết, không sửa kết quả nghiệm thu cũ. | NOT RUN |
| T20 | Rule thiếu quyền, lỗi lookup hoặc quota | Có lỗi quan sát được, không chuyển sai/đánh dấu thành công. | NOT RUN |
| T21 | Event của KAN hoặc Epic CANCELLED | Không bị rule mới thay đổi; CANCELLED không auto restore. | NOT RUN |
| T22 | Deploy Task | Có bằng chứng môi trường Test tập trung + smoke; không mặc định Production. | NOT RUN |
| T23 | Import mẫu rồi toàn bộ WBS | Đúng 11 Epic/53 Story được phủ trong Task; Parent/AC/checklist/5 assignee không trùng và không rơi vào KAN. | NOT RUN |

## 12. Điểm tiếp tục hiện tại

Bổ sung tiếp tục 2026-10-09: CSV v7 DRAFT đã tạo/kiểm tra local, giữ 53 Story/106 AC; xem [JIRA_WBS_GUIDE.md](JIRA_WBS_GUIDE.md). Local/hosted MCP đọc lại QAG3 ba status mặc định, JQL local rỗng; discovery chưa expose admin workflow cần thiết. Chưa map scheme/gates/automation hoặc import, 23 test ở mục 11 vẫn NOT RUN. Không thay đổi hợp đồng nghiệm thu chỉ vì CSV local đã đạt.

Đã lưu checkpoint trước bootstrap; cả ba workflow riêng Inactive, Subtask đọc lại thấy Update workflow disabled. QAG3 được đọc lại qua MCP; các type hiện chỉ có To Do/In Progress/Done. Scheme hiện tại theo quan sát UI trước đó: `QAG3: Software Simplified Workflow Scheme` / ID `10003`, workflow `Software Simplified Workflow for Project QAG3` / ID `2bf6edf8-90ad-4092-92dd-63a10acf6041`; chưa phải mapping ba workflow đã thiết kế. Công việc cấu hình tạm dừng, tiếp tục theo AGENTS.md mới.

Ngân sách 0: JSU thương mại nêu ở mục 6 chỉ là ứng viên lịch sử chưa cài, bị loại khỏi triển khai hiện tại; không trial/app/đổi gói. Năm email đã lưu checkpoint, chưa xác minh đủ accountId/assignability và quyền PM. Gate Epic–Task vẫn chưa đáp ứng; kiểm tra PM/Codex không tương đương hard gate và cần người dùng duyệt thay đổi yêu cầu nếu chọn. 23 test chưa chạy, chưa bật automation/import WBS hoặc đánh giá cá nhân. Template review mới theo AGENTS.md, riêng tư và dựa evidence; quy ước Point=giờ chỉ mô phỏng.

## 13. Yêu cầu mới: Subtask tách nhánh nghiệp vụ/phát triển — 2026-10-09 15:38 +07

User chọn: Task đúng ảnh; Subtask có luồng riêng theo vai trò, chỉ BE/FE đi qua Code Review và kiểm thử. Yêu cầu này thay thiết kế Subtask 4 trạng thái chung trước đây; chưa có approval ghi cấu hình hoặc kích hoạt của lô mới.

- Task live inactive v2 đã có đủ 10 trạng thái, các nhánh Code rejected/Bug found/ReDev/Retest và Reopen đã duyệt trước; giữ nguyên, không viết lại.
- Subtask dự kiến 7 trạng thái, 13 transition: BA/Tester/PM `NEW → IN PROGRESS → REVIEW → DONE`; BE/FE `NEW → IN PROGRESS → CODE REVIEW → READY FOR TEST → IN TESTING → REVIEW → DONE`. Giữ Rework/Reopen, thêm Code rejected/Bug found/Retest. Deploy nằm ở Task, không ở Subtask.
- Routing native dự kiến theo assignee của 5 tài khoản đã xác minh, không Jira security Role. Mỗi điều kiện Equals Assignee có một người; nhóm ANY kết hợp các người cùng nhánh. Không dùng quyền của người bấm transition để đoán loại công việc. Đổi assignee có thể đổi nhánh hoặc làm việc đang chạy không còn transition phù hợp; phải kiểm thử riêng trước activation. Không khẳng định đã giải quyết gate reviewer/QA/PM/checklist/lý do.
- Supplemental MCP `preview_subtask_delivery` chỉ cho workflow Subtask inactive, giữ actions/validators/cạnh cũ và Resolution. Preview `19360e5d-993b-411a-b537-a95f5cac7746`, SHA256 `13641cfd0ea81d320e62f3e6222e6617cb277137f546205d7b29dfac2035956f`, validation Atlassian `errors=[]`; chưa gọi apply_change. Hai preview encoding nhiều assignee trước đó bị từ chối và không được áp dụng.
- 77 local Python tests PASS, không phải E2E Jira. T15 cần kiểm tra hai nhánh: BA/Tester/PM không bị ép qua Code Review; BE/FE không được dùng Submit work để bỏ qua review/test. Bổ sung test unknown/unassigned, đổi assignee giữa nhánh, Rework/Reopen và Resolution; tất cả Jira runtime test mới NOT RUN. Không ghi T01–T23 PASS từ API validation.
- WBS đã nhập đủ 329 mục theo checkpoint mục8; QAG3 vẫn scheme10003/To Do–In Progress–Done. Lưu workflow inactive không là áp dụng vào project. Migration To Do→NEW và staged gate tests cần preview/approval riêng; không bypass empty-project guard, không sửa/xóa 329 issue hoặc khởi động monitor đã pause.

Nguồn cấu trúc rule: [Atlassian Workflow API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflows/); cách Equals một người được đọc từ form native của đúng workflow rồi Cancel, không Add/Update. API validation không chứng minh hành vi khi transition thật.

## 15. Hiện hành: reason gates inactive — 10/10/2026

Epicv6 Reopen8/Cancel9/Restore10 có screen10011 + qag3-fresh-change-reason; Taskv5 Reopen15 và Subtaskv5 Reopen6 có screen10010 + cùng validator. Owner duyệt lô riêng; browser lưu, supplementary MCP độc lập đọc lại và kiểm tra semantic approved diff PASS. Giữ graph/status/old gates/Resolution và hai nhánh Subtask theo assignee; không suy assignee routing thành quyền người review. Lý do phải nonblank và đổi trong cùng transition, không chỉ edit trước đó. Xem JIRA_REASON_GATE_BATCH_2026-10-10.md/checkpoint24.

Workflows inactive, QAG3 scheme10003, A01 disabled/A02–A05 absent. Jira gate E2E/revision-bound authenticated reviewer/retest và các gate acceptance còn pending. Không migration329issues hoặc resume monitor. Những phiên bản bên dưới là lịch sử.

## 14. Cấu hình inactive đã lưu — 2026-10-09 15:50 +07

Owner duyệt lưu inactive; Subtask7512e21c **version2**, 7status/13transition đúng hai nhánh mục13, Resolution Done khi Approve work/clear khi Reopen được giữ. Task9f21c6fc vẫnversion2, nội dung không đổi. QAG3 vẫnscheme10003; custom workflows chưa hoạt động trên329issue.

Route: official MCP preflight/read, supplemental MCP preview_subtask_delivery/apply_change/inspect_workflow/inspect_scheme. Preview766f1d95/hash62ea0b3d… validation errors=[] và cấu hình tương đương lô đã duyệt. Lần apply lưu Jira nhưng trả READBACK_MISMATCH do reorder danh sách transition; không retry. Đọc độc lập theo ID khớp cấu hình, assertion PASS; giữ unknown audit và thêm reconciled VERIFIED_AFTER_READBACK_ERROR. Architecture15.17 ghi sửa đối chiếu và79localtests PASS.

Chưa runtime test routing/assignee change/reviewer/QA/checklist hoặc gate Epic; không ghi các test Jira thành PASS. Không publish/associate, không sửa issue/bật automation/monitor. Rollback cần approval riêng và current-version preview từ snapshot before; không tự restore.


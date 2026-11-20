# Vận hành Jira từ Codex

## Hiện hành — khôi phục dấu duyệt phạm vi cho automation, 21/10/2026
Chủ dự án duyệt thêm qag3-scope-approved vào toàn bộ 53 Task WBS. Official MCP editJiraIssue đã thêm nhãn và giữ mọi nhãn cũ; đọc lại đủ 53/53. Không đổi cấu hình A01–A05: cả năm vẫn Enabled, UUID/updated/actor/scope nguyên. Trong cửa sổ này, Task QAG3-101 được chuyển trên Jira từ In Progress qua CODE REVIEW, READY FOR TEST đến IN TESTING; agent không tạo các transition đó và không hoàn nguyên hoạt động của người dùng. A03 đã mở Epic QAG3-100 Done→In Progress, changelog12799 lúc22:30:59+07, lý do tham chiếu Task101/READY FOR TEST. Không chạy vòng CodeReview thử đã dự kiến, không QA/Done writes, không sửa gate/quyền/billing/bot/OpenProject. A01/A02/A04/A05 sẵn sàng nhận sự kiện theo gate cũ, chưa tái nghiệm thu E2E toàn bộ. Audit/before/readback: jira-bot/scope-approval-2026-10-21-*.json. Rollback nhãn cần đọc mới và chỉ bỏ nhãn vừa thêm, không ghi đè nhãn/sự kiện phát sinh sau đó; không tự undo Epic reopen hợp lệ.

## Hiện hành — QAG3 gộp 4 Epic và lịch 10 Sprint, 21/10/2026
Đã áp dụng phương án B trực tiếp lên Jira QAG3: bốn Epic chính QAG3-1/69/100/243 chứa 11/10/13/19 Task và tổng 265 Subtask; 33 Task đổi Parent. Lịch 322 mục được lập lại trong 17/08–31/12/2026, 10 Sprint future ID 1–10. Bảy Epic dư giữ nguyên và hiện rỗng. Official MCP đọc lại đủ 336 issue, không sai lệch kế hoạch hoặc thay đổi trạng thái/assignee/labels/Resolution/gate fields. Scheme 10004, workflow Epic v10/Task v11/Subtask v12 và A01–A05 Enabled giữ nguyên cấu hình. Browser fallback chỉ dùng tạo/sửa Sprint vì official MCP không expose thao tác này. Không QA/E2E mới, không thao tác bot/OpenProject/billing. Bất nhất cũ QAG3-213 Done/QAG3-337 NEW và cảnh báo email quota đã được ghi rõ. Báo cáo, audit và rollback: jira-bot/REPLAN_QAG3_2026-10-21.md. Không import final.csv cũ vì kế hoạch và trạng thái khác phương án đã duyệt.

## Hiện hành — tổ chức 11 Epic qua 5 Sprint nháp ngày 15/10/2026

Theo user yêu cầu, official MCP xác minh QAG3/10002/board3 và 5Sprint future sẵn có IDs1–5, UI xác nhận ban đầu rỗng. Dùng lại, không tạo thêm. Đặt tên/goal rồi addIssues53Task: S1 Nền tảng (Epic1/32,11Task55Subtask); S2 Lập kế hoạch (69/100,10/50); S3 Task Kanban (131/162,9/45); S4 Lịch và lỗi (187/212,9/45); S5 Hoàn thiện (243/274/299,14/70). Epics giữ hierarchy/không ép Sprint trên Epic; Subtask theo Task cha. Goal ghi rõ Epic và mô phỏng, chưa dates/Start/Close; không sửa timeline issue để ép lịch9tháng thành5Sprint ngắn.

MCP full readback4pages/isLast/329unique xác minh53Task và265Subtask đúng Sprint; 64Epic/Task đối soát status/assignee/parent/summary/labels/Start/Due giữ nguyên. Không mở lại Done để hiển thị. Board trước còn mapping3status cũ; official discovery không có writecột, đã dùng browser fallback keyboard drag/drop: NEW/READY/IN ANALYSIS/READY FOR DEV vàoToDo,5review/test/release statuses vàoInProgress; Done vẫn chỉDone, CANCELLED0issue giữunmapped. getJiraBoardConfig readback PASS. Bật Epic panel ở backlog; DoneEpic/DoneTask bị native backlog ẩn nên S1–S4 hiển thị0visible không nghĩa Sprint chưa gán; S5 hiển thị14NEW. Không đụng6fixture/KAN/SAM1/gates/A01–A05/bot/billing.

Audit/before/readback: jira-bot/SPRINT_PLAN_QAG3_2026-10-15.json, SPRINT_ALLOCATION_RESULT_2026-10-15.json, SPRINT_WBS_READBACK_2026-10-15.json; screenshot QAG3_SPRINTS_BACKLOG_2026-10-15.jpg. 503 đọc Sprint được khắc phục bằng official getJiraBoardSprintData; lỗi rename400 giới hạn30ký tự đã sửa tên ngắn, không tạo trùng. Rollback chỉ phục hồi metadataSprint/Sprint issue và mapping cột trước qua preview, không xóa issue hoặc giả Sprint execution.

## Hiện hành — bot ACTIVE và báo cáo Epic Done, 15/10/2026

User yêu cầu bật lại monitor và nhận đánh giá riêng từng thành viên theo Epic Done. Đã resume heartbeat cũ giữ prompt/cadence/thread; Enable/Start Windows task sau CIM0runner. Python25440/Parent28316/CreationDateUTC07:16:17.225512, run189a271b-81f3-46dd-8b73-82619afac3cd/cycle1 complete07:17:36.938346UTC/readComplete=true/335issue; process/event/state/freshness khớp. MCP identity/resources/QAG3-1 và full Epic search isLast=true PASS, không browser/Jira writes. Gemini DISABLED_CONFIG.

Báo cáo10trang `Danh_gia_thanh_vien_theo_Epic_Done_QAG3_2026-10-15.docx` đã render/xem toàn bộ: 7Epic WBS Done,34Task/170Subtask Done; mỗi người34/34Subtask trong phạm vi7Epic, không phải toàn53Subtask. Năm chiều hiệu suất thiếu evidence, không chấm năng lực từ lịch/worklog mô phỏng hoặc xếp hạng. Cursor giữ notification history; không thay baseline collector, gate/A01–A05/billing/credential. Chưa kiểm thử lại reboot/appclosed/sleep hoặc Codex scheduled run. Audit `jira-bot/MONITOR_RESUME_EPIC_REVIEW_2026-10-15.json`; các mục PAUSED13/10 dưới là lịch sử.

## Lịch sử — bot giám sát PAUSED, 13/10/2026

User yêu cầu tạm dừng monitor và tạo handbook. Heartbeat PAUSED, Windows task Disabled/Stopped; child runner xác minh đúng PID/Parent/script/CreationDate rồi dừng. CIM0 runner/wrapper lúc `2026-10-13T04:48:41.7699852Z`, kiểm lại Disabled/CIM0 lúc `2026-10-13T05:12:13.2121524Z`. Không sửa issue/workflow/automation hoặc lịch continuation khác; A01–A05 vẫn Enabled. State/events/báo cáo được giữ nguyên. Audit `jira-bot/MONITOR_PAUSE_2026-10-13T044841Z.json`; handbook `So_tay_van_hanh_Jira_QAG3_2026-10-13.docx` gồm17trang,14chương,39transitionnative/12validator/5automation, đã render/kiểm trực quan mọi trang. Phần ACTIVE dưới đây là lịch sử.

## Lịch sử — bot giám sát ACTIVE và đánh giá thành viên riêng tư, 13/10/2026

User yêu cầu bật lại monitor và đánh giá công việc từng thành viên. Đã Enable/Start đúng Windows task QLDAPM-Jira-MCP-Monitor sau CIM0runner; heartbeat bot-theo-d-i-ti-n-jira-qag3 ACTIVE giữ mỗi giờ phút15/chatđích. Runner PID21772/parent18492/CreationDateUTC04:35:08.288059, run6d83a338-dd8f-4ba3-8e39-dc2493b6dd49/cycle1 complete04:36:22.036004UTC, state335issue/readComplete=true, GeminiDISABLED_CONFIG. Process/event/freshness đã đối soát; không suy Codex scheduled execution hoặc reboot proof.

Runner bổ sung memberAssessment trong cùng complete cycle: scope qag3-wbs329, loại6fixture; từng vai trò53Subtask/39Done/14NEW/0WIP=73,58% mô phỏng. PM53Task/11Epic báo riêng, không cộng đôi. Năm chiều thiếu evidence nên overallScore=null/INSUFFICIENT_EVIDENCE, không điểm giả/HR ranking, không rawPII sangGemini. Báo cáo local/chat riêng tư, chỉ notify meaningfulchange, khôngtimestamp-only. 11runner/108Jirasuite testsPASS. Không đổi Jira/billing/credential/lịchcontinuation khác. Lượt này chỉ bật lại monitor cũ, không tạo daemon hoặc lịch trùng. Audit/report: `jira-bot/MONITOR_RESUME_2026-10-13T043621Z.json`, `jira-bot/REPORT_MEMBERS_2026-10-13T043621Z.md`. Chưa nghiệm thu lại reboot/appclosed/sleep/OAuthexpiry hoặc nhiều giờ sauresume; các mụcPAUSED dưới là lịch sử.

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

## Hiện hành — A02–A05 ENABLED trong qag3-test; A05 comment hai nhánh PASS — 13/10/2026

Task activev8 đã gắn QA companion; Forge development2.16.0 native Approve/Deploy fixturePASS. Epic activev9 Return7 có screen10011+fresh-reason validator theo exact owner-approved hash; A03 lưu reason cùng status trong changelog12076, A04 auditSuccess1d421393… sau sửa field ngoài screen/timestamp. A02–A05 hiện ENABLED **chỉ trigger labels=qag3-test**, A01 giữ nguyên. Chưa rollout toàn329WBS.

Owner duyệt đổi A05 email sang comment @mention PM: đã lưu2actioncomment/0email, native duplicate-comment guard bật, frozen event/marker/routing giữ nguyên. OfficialMCP comment10005 @Khai và10006 @Hiệp trênQAG3-332, authorAutomationforJira; auditSuccess hai lần4c55363d…/7c90de56…, RetestNoactions2ae90e3a…. Chỉ mô phỏng/điều phối review, không QA thật hoặc inbox-delivery proof. Parser QA evidence literal\\n còn hạn chế; fullSubtask/stale/non-PM/concurrency/project-wide qualification chưa hoàn tất. MonitorPAUSED,329WBS/timeline/baEpicDone/KAN/SAM1/billing không đổi. Audit/remaining/rollback: `JIRA_QA_RUNTIME_FIX_2026-10-13.md`; proof `jira-bot/a05-comment-qualification-2026-10-13.json`. Các trạng thái Disabled/migrationpending dưới là lịch sử.

## Hiện hành — approved QA freshness đã apply/đọc lại Task v8 — 13/10/2026

Lôownerduyệthash7801068db638d6baee13ee83e5e70107ee488697e46f5f5e6569e171a741ef74 đãapplyVERIFIED qua cùngsupplementalguardCLI, saucachedMCPtừchốioperationtrướcwrite. Previewrenew721af4fc-aea2-4d68-98ca-9132a9600a1e cùnghash/errors=[], khôngsửatimestampold900s. Taskversion8/id a26b31bf-432c-443f-a880-65589d556d78: thêmqag3-qa-freshness enabled đúngApprove13/Deploy14; independentMCPread+semanticdiff giữmọioldgate/layout/screen/Resolution/condition. JirađổirulemetadataIDs, khôngcósemanticdiffkhác. Audit jira-bot/qa-freshness-apply-2026-10-13.json. Khôngissuewrite/automationenable/scheme/billing; A01ENABLED/A02–A05DISABLED/monitorPAUSED. Tiếp tốiưu QA-current dưới conjunction đãgắn; chưaE2E.

## Hiện hành — actor A03/A04 sửa, QA companion deploy2.14.0, đang chờ exact preview approval — 12/10/2026

A03/A04 actor đổiUserwhotriggered quaUI/Save, không cấpPMquyền; A04reloadverified, summaryreadbackdynamicnull. A01ENABLED/A02–A05DISABLED giữ nguyên. Forge2.14.0 thêmqag3-qa-freshness expression,10oldmodulesunchanged, no scopes/functions/storage/egress/billing; Node/lint/105Pythonregression+1newtestPASS. Companion Jira typevalid/runtimefixed332true; combinednewestcandidate forcedallpaths vẫnvượt10. Chưa sửa QA-current cũ, chưa apply/addgate hoặcE2E/enable.

Actualfixed activeTask preview fbbcc261-a1bc-4400-bc8a-e2ebe1fa2f3a, hash7801068db638d6baee13ee83e5e70107ee488697e46f5f5e6569e171a741ef74, errors=[]/blockers=[], chỉ thêmcompanionApprove13/Deploy14 giữoldQA-current. Đãxinownerexacthash trướcapply; giữ900s/stale/lock/no-replay/readback vàactivationguards. Audit `JIRA_AUTOMATION_QUALIFICATION_2026-10-12.md`. MCPserverđangsourcecũ(EXPR_MANIFEST_CHANGED); CLIpreviewfresh+stdio22toolsPASS, khôngtựrestartapp. MonitorPAUSED;329WBS/timeline/3EpicDone khôngđổi; StandardtrialUI khônglàplan/billingproof, A05quota/send chưakiểmtra.

## Hiện hành — A04/A05 đã import thật DISABLED, browser trong app hoạt động lại — 12/10/2026

Official owner/site/QAG3 preflight PASS. `mcp__cua_repl` hiện callable: native Jira Global Automation Import flows đã tạo A04 UUID01a13075-71e9-7e0f-b65f-006ec2a4b83b và A05 UUID01a13075-71e9-750f-9913-5e43ba4adaf0, scopedQAG3, DISABLED. Supplemental readComplete=true xác nhận đủ5rule; A01 vẫnENABLED, A02/A03 vẫnDISABLED, không ghi đè template. Đây là trạng thái mới, không còn chỉ browser draft/file local.

A04 đối soát raw Parent cũ/mới, refetch/first-match/nonempty/currentTaskDone; không autoDone/Cancel/Restore hoặc mở Epic cũDone chỉ vì bỏTask. A05 review-entry PM-coordinator notification, frozen event-key label ADDREMOVE/marker-before-mail; giữ labels cũ. Routing chỉ là coordinator, không full step-reviewer qualification; marker không atomic và mail fail có thể cần resend manual. Jira import reset actor A04 về AutomationforJira, chưa đổi/cấp quyền, có thể vướng PM gate. Mô tả A04 đã corrected trên Jira, đọc lại verified.

Export thật độc lập khớp trigger/graph/scope (Edit10→12/Email3→5 native migration); 51component/288localdecisioncases/Parent stale/replay/routing/label-preservation PASS. Chưa bật/JiraE2E/actual email/quota/concurrency/childvisibility; không hạ activation/gate guards. QA-current Approve13 expensiveoperations lỗi cũ chưa sửa. MonitorPAUSED;329WBS/timeline/baEpicDone/KAN/SAM1/OpenProject/workflow/scopes/billing giữ nguyên. Audit/file/tests/remaining: `JIRA_A04_A05_IMPORT_2026-10-12.md`; đừng reimport tạo Copy of. Các mục dưới là lịch sử.

## Hiện hành — A03 đã lưu; A04 draft chưa lưu, A05 chưa tạo — 12/10/2026

Chẩn đoán app tiếp theo: log xác nhận browser availability đã available=false/reason=statsig-disabled và cua_repl tools empty; hiện plugin đầy đủ installed/enabled. Đã đăng ký lại unified-computer-use26.1007.21434 qua `codex plugin add` exit0, nhưng browser tool vẫn absent trong phiên. Không sửa feature gate hoặc restart làm mất draft, không Jira writes. Bằng chứng/giới hạn: `JIRA_BROWSER_TOOL_DIAGNOSTIC_2026-10-12.md`.

Kiểm tra tiếp theo: Windows Computer Use `@oai/sky` đã khả dụng lại, nhưng đường điều khiển tab IAB `mcp__cua_repl` vẫn absent. Lần đầu Edge bị helper dừng do không xác định URL; lượt sau đã activate/read được cửa sổ Edge và URL, nhưng mở tab mới hai lần bị từ chối `user input was detected`, rồi thử activation sau MCP read cũng bị từ chối. Không đè thao tác người dùng hoặc điều khiển ChatGPT desktop UI. Official identity/resources vẫn đúng owner/site; supplementary readComplete vẫn chỉ A01 ENABLED, A02/A03 DISABLED. Không tạo tab Jira, không lưu A04/A05, không Jira writes trong các lần phục hồi này; draft IAB không được kiểm tra live bằng Windows helper.

Supplementary `inspect_automation` đọc lại `readComplete=true`: A01 ENABLED, A02 DISABLED, A03 `01a12ee4-1276-76b4-ba01-49bdeda52f9d` DISABLED. A04/A05 chưa có trong danh sách persisted rules. A03 đã lưu qua browser fallback: Created/Transitioned Task chưa Done, có Parent và nhãn `qag3-scope-approved`, Parent Epic REVIEW/Done → In Progress kèm QAG3 Change reason mới. Nhãn scope là metadata nghiệp vụ, không phải kiểm soát quyền PM. Chưa qualification/E2E A03.

Draft A04 đang ở browser copy của A03: tên `QAG3 A04 - Reconcile old and new Epic after Parent change`; trigger Parent field changed, JQL QAG3/Task10011/scope-approved. Nhánh 1 Epic mới REVIEW/Done, Task nguồn không Done → IP; nhánh 2 Epic mới READY, Task nguồn không NEW/Done → IP; nhánh 3 cả Parent cũ/mới đang IP, refetch/Children present và điều kiện All match đang chọn dở → REVIEW. Selector Parent dùng raw `fieldChange.from/to` với default0, không mở rộng site. Phải hoàn thiện nhánh3 và thêm REVIEW có Task chưa Done/không còn Task → IP; không mở lại Epic cũ Done chỉ vì bỏ Task, không restore CANCELLED hoặc auto-Done.

Lượt tiếp tục bị chặn bởi thay đổi khả dụng công cụ: `mcp__cua_repl`/browser control không còn được expose; đường dẫn computer-use skill cũ không tồn tại. MCP official không có create/edit automation, supplementary chỉ inspect/preview disable. Không dùng REST hoặc browser library khác để lách route. Plugin discovery không tìm được kết nối điều khiển tab hiện hành. Không lưu draft A04, không tạo A05 và không bật rule trong lượt bị chặn này. Cần khôi phục công cụ browser trước khi tiếp tục; draft có thể mất khi reload, phải đọc lại UI, không suy từ URL rằng đã saved.

A05 còn cần cấu hình Task/Subtask vào trạng thái review, dispatch PM được xác định, dấu sự kiện ở entity property + refetch/compare để giảm gửi lặp. Property không atomic: không được cam kết exactly-once; banner quota email và lỗi QA-current trước đây vẫn chưa giải quyết. Monitor PAUSED, workflow/timeline/329WBS không đổi.

## Hiện hành — A01 PASS, A02 lưu Disabled, QA-current bị chặn — 12/10/2026

Official identity/resources/QAG3 preflight PASS; supplementary inspect_automation đọc đầy đủ: A01 uuid01a1216a-82a7-7a79-9f26-8102e7f6a942 ENABLED; A02 mới uuid01a12eca-5f11-7ef3-9c33-3898c7b1e9f2 DISABLED cuối lượt; A03–A05 chưa tạo. A02 lưu qua browser UI fallback sau exportA01, scopedQAG3/parent/refetch/EpicIP/allchildrenTaskDone→REVIEW, actorAutomationforJira, canOtherRuleTrigger=false. Tạm bật để qualification rồi giữtắt vì không tới đượcTaskDone; không báoA02E2EPASS.

Mẫu thử táchWBS: QAG3-331 Epic, QAG3-332 Task; labelsqag3-test/qag3-simulation/excluded-from-performance/automation-e2e-2026-10-12. Approvescope331READY rồiStartanalysis332:331tựIP, officialchangelog12048/AutomationforJira xác minh A01 chạy thật. Task332 đi đủAnalysisdone/Startdev/Submitcode/Approvecode/Starttest/Pass testing vớiSIMULATEDPASS tớiREVIEW. Approve13 chặn400 tạiQA-current customfield10044/too manyexpensiveoperations10; vẫnREVIEW. Read-onlyAPI tái hiện baseline vàboundhistory8/2 vẫn quálimit; chưa sửa/deploy gate, chưa bỏhistory/reviewer/securitycheck. Forge vẫndevelopment2.13.0.

Chưa fullworkflow/A02–A05/concurrency E2E. Cần thay cách đọc/provenanceQA thay vì giảPASS; hướngForgefunction là expansionfunction/scopes, phảipreviewquyền/cost/rollback và approval trướcinstallupgrade. BannerJira báoemailnotifications đãchạmgiới hạn, không thửvượt hoặc nânggói. MonitorPAUSED;329WBS vàbaEpicDone giữnguyên, khôngnote/commentởbacklog.

## Hiện hành — Timeline chi tiết và ba Epic đầu Done, 12/10/2026

Official MCP identity/resources/QAG3 preflight PASS; editJiraIssue đã ghi Start date10015/Due date cho đủ329 WBS. Full4-page readback329unique:11Epic/53Task/265Subtask có ngày03/04–31/12/2026, không thiếu; Parent identity/assignee/labels giữ nguyên, lịch con nằm trong cha. UI Timeline dùng Work item start and end dates, không Align to Sprints; đã đọc thấy thanh riêng Task14 và Subtask15–19. Không thêm comment/note/description, worklog/Sprint/automation không đổi; monitorPAUSED.

Forge development2.13.0 sửa giới hạn đọc Epic: validator children-done kiểm tra cả Task và Subtask, validator acceptance giữ PM/scope/checklist/evidence fresh; cả hai vốn đã enabled trên Accept6, không sửa workflow graph/scheme. ADF paragraph/text/hardBreak được đọc trực tiếp, unsupported ADF fail-closed. Jira runtime read-only hai predicate PASS; Nodefixtures/105Python/lint PASS. Actual transitionJiraIssue6 đưa QAG3-1/32/69 REVIEW→Done10009; independent readback ResolutionDone10000. Các trạng thái khác giữ nguyên. Chỉ là kịch bản học tập được owner duyệt, không QA/nghiệm thu sản phẩm thật hoặc full E2E.

Lịch/rollback-before: jira-bot/timeline-expanded-2026-10-12.json. Audit hiện hành: JIRA_TIMELINE_COMPLETION_2026-10-12.md; lịch17/08 bên dưới là lịch sử trước điều chỉnh này.

## Timeline mô phỏng hiện hành — 12/10/2026

Official MCP đã ghi và full-pagination đọc lại đủ329mục WBS: Start date/customfield_10015 và Due date, nhãn simulated-timeline-2026. 11Epic nối tiếp từ17/08 đến31/12/2026;53Task/265Subtask nằm trong ngày cha, BA→BE/FE→QA→PM không trùng ngày theo vai trò. Giữ status/Parent/assignee/description/worklog/Sprint/workflow/automation; monitorPAUSED. Đây là lịch kế hoạch giả định, chưa là khóa workflow hoặc tiến độ thật. BaEpic đầu QAG3-1/32/69 hiện REVIEW (Accept Epic vượt10expensiveoperations), QAG3-212 IP; baEpic cuối243/274/299 NEW. Mục reset3NEW bên dưới là lịch sử trước đính chính. Audit/lịch: JIRA_TIMELINE_SIMULATION_2026-10-12.md và jira-bot/timeline-simulation-2026-10-12.json.

## Hiện hành — reset3Epic đã hoàn tất, 12/10/2026

QAG3 đã được người dùng migration sang QAG3 Managed Delivery v1 trên UI; MCP đọc Epic workflow v8 và chạy custom transitions thật. QAG3-1/32/69 đã về NEW10010 qua Reopen8/Cancel9/Restore10, lý do rõ SIMULATION; không gửi mutation Task/Subtask. Sửa lỗi `typeof` primitive string trong Forge app development2.9.0,105Python tests/Node fixture/lint PASS; Jira positive reopen/cancel/restore và negative thiếu lý do mới được quan sát. Không phải full A01–A05/QA/concurrency E2E. Monitor vẫn PAUSED. Audit: `JIRA_EPIC_RESET_2026-10-12.md`. Các mục10003/inactive bên dưới là lịch sử, không còn là trạng thái migration hiện hành.

## Đường triển khai thử — PROPOSED

`JIRA_QUALIFICATION_ROLLOUT_DESIGN.md` tách SIMULATION/LOCAL_TEST/JIRA_E2E và mô tả qualification cách ly. Chưa triển khai capability, không sửa guard/evidence, không Jira writes/activation/migration. Đây là thiết kế, không phải deployment proof.

## Kiểm thử mới nhất — 11/10/2026 22:19 +07

Đã chạy105Python tests/Nodefixtures/Forge lint và4supervisor mock cases; Jira10Boolean/type-valid và10runtime evaluations complete. Official full-pagination329unique/Parent/5assignee PASS. Scheme vẫn10003; custom transitions chưa khả dụng; A01Disabled/A02–A05absent. T01–T23 chưa có complete JiraE2EPASS; không tạo rollout-evidence hoặc migration. Đọc cấu hình phát hiện EpicCancel9 thiếu Resolution action, Reanalyse3/Return7 thiếu reason gate/screen. Kết quả/matrix/qualification blocker: `JIRA_TEST_RESULTS_2026-10-11_2219.md`. MonitorPAUSED, không Jira writes.

## Hiện hành — populated-project switch preview VERIFIED, migration còn gate blocker — 11/10/2026

MCP local `qag3-admin` đã thêm `preview_scheme_switch` và `inspect_scheme_switch_result`, catalog21tools/105localtests PASS. Registered actual preview đọc329mục và Atlassian calculator trả10008→10010 theo3type;316Done10009/13IP3 giữID. Không còn blocker project-rỗng cho đường switch mới; assign cũ giữguard. Preview0794ba52…/hashdc16f483… còn chặn **Jira T01–T23/PM review chưa ghi nhận**, chưa human-approved. Independent association vẫn10003. Khôngapply/activation/migration/A01–A05/monitorresume. Current audit/remaining/rollback: `JIRA_SCHEME_SWITCH_IMPLEMENTATION_2026-10-11.md`. Các đoạn “populated tool chưa implement” phía dưới là lịch sử, không phải kết quả mới.

## Hiện hành — academic329/worklog265 VERIFIED, migration còn chặn — 11/10/2026

Mô phỏng QAG3 đã hoàn thiện/đọc lại329mục,49/53TaskDone=92,45%;265worklog384giờ và điểm5role giả định đã ghi/đọc lại, comment10004 ởQAG3-299. Native author làadmin, không impersonate; không bằng chứng QA/HR thật. MappingDone10009/InProgress3 giữ ID trong cả3workflow, không có ToDo. inspect_scheme cuối vẫn10003; supplementary associate10004 báoPROJECT_NOT_VERIFIED_EMPTY, chưa migration/populated-project tool hoặc Jira qualification đủ. Không apply/publish/activation/A01–A05/monitorresume. Audit/remaining: JIRA_MIGRATION_READINESS_2026-10-11.md; checkpoint38. Lịch sử partial429 phía dưới đã được đối soát, không phải trạng thái dữ liệu hiện hành.

## Hiện hành — named-owner simulation development2.6.0 DEPLOYED, 11/10/2026

Owner có thể QA/self-review mô phỏng qua 3 validator mới trên appdevelopment hiện có: nhãn `qag3-simulation` trước transition, evidence `SIMULATED PASS` / business `SIMULATED ACCEPTED`. Đúng owner allowlist, realQA vẫn PASS; không cấp global/site quyền hoặc bỏ gates dữ liệu. Forge deploy exit0/Deployed2.6.0; independent MCP catalog10/policy mới, Taskv6/scheme10003 giữ nguyên. Node/preservation/lint/Jira10Boolean/94Python PASS; chưa transitionE2E/migration/A01–A05enable/monitorresume. Chi tiết và rollback: `JIRA_ADMIN_SIMULATION_2026-10-11.md`.

## Hiện hành — RichText fix development2.5.0 DEPLOYED, 11/10/2026

Owner saupreview605a58b1… yêucầucứdeploy; pinnedForgedeploydevelopmentSuccess/version2.5.0/lintPASS. Officialidentity/resources/QAG3-2verified. SupplementaryTaskv6/catalog10/association10003readback; Jira typecheck10/10Boolean/93PythonPASS. Khôngproduction/reinstall/scopes/billing hoặcworkflowmigration329/A01–A05enable/monitorresume/JiraE2E. Remaininggate/testing/exacthashapply chưađạt; khôngfakeQAhoặcrolloutevidence. Audit JIRA_RICHTEXT_FIX_PREVIEW_2026-10-11.md; checkpoint33/architecture15.39.

## Hiện hành — Epic development2.4.0 / inactivev7 VERIFIED, 11/10/2026

Officialidentity/resources/QAG3-1 smokePASS. Ownerapproveddeployhashba890f52…→development2.4.0Success/catalog10; exactpreview317db13d/hashb19116fa…→supplementary registeredMCPapplyVERIFIED. IndependentEpicv7/4f007f20… gateReadyScope2/Accept6/screens10011; preservationPASSold6statuses/10transitions/rules/layout/Resolution. Nodefixtures/lint/91PythontestsPASS, khôngJiraengine/E2E. Scheme10003/onlyA01Disabled/readComplete afterapply; no329migration/automationenable/monitorresume/KAN/SAM1/OpenProject/HR. Audit/remaining/rollback JIRA_EPIC_DELIVERY_GATE_BATCH_2026-10-11.md.

## Hiện hành — Subtask gates đã lưu inactivev6, 10/10/2026

Official identity/resources/QAG3-4 verified đúng site/cloud/project. Forge development2.3.0 approvedhash5c99687f… deploy Success/catalog8. Supplementary registered MCP approvedpreview9124e90c/hash2b40297c… errors=[]→apply VERIFIED→independentreadback Subtaskv6/7ccb46c1…, QA Pass testing12 và independentPM Approve4 có screen10010. PreservationPASS graph/routing/Resolution/reason/layout. Nodefixtures/90PythonlocaltestsPASS, khôngJiraruntime/E2E. Association vẫn10003, chỉA01Disabled/readComplete; no329migration/automationenable/monitorresume. Details/rollback JIRA_SUBTASK_ACCEPTANCE_PREVIEW_2026-10-10.md. Các mục dưới là lịch sử, không bằng chứng fulladmin.

Cập nhật: 2026-10-09. Quy tắc vận hành mới: [AGENTS.md](AGENTS.md). Audit bootstrap chỉ đọc xác minh MCP chính thức local, QAG3 và KAN-68 Done; xem [JIRA_MCP_AUDIT.md](JIRA_MCP_AUDIT.md) và [JIRA_CAPABILITIES.md](JIRA_CAPABILITIES.md). Các kiểm thử ghi/plugin ở những mục lịch sử là snapshot 2026-10-08, không chứng minh mọi quyền ghi/admin ở phiên sau. Đây là công cụ quản lý phát triển, không phải tích hợp trong sản phẩm QLDAPM.

## Hiện hành 10/10/2026 — QA Task inactivev6 VERIFIED, chưa migration

Approved deploy2.2.0/catalog7modules và exact preview24a2237f/hash e1415852…/errors=[] apply VERIFIED qua supplementary registeredMCP, không officialadminwrite/browser. Taskv6 thêm QA Pass testing+screen10010, QA-current Approve/Deploy và PM-only Retest before release. Independent preservation checks PASS oldgates/layout/Resolution.89localtests/Nodefixtures/lint PASS, chưa Jira E2E. JIRA_QA_TASK_GATE_BATCH_2026-10-10.md làcurrent audit/rollback/remaining; checkpoint27/architecture15.33. Scheme10003/A01Disabled unchanged, monitorPAUSED; no migration329items/Epic/Subtask/KAN/SAM1/OpenProject changes.

## Lịch sử 10/10/2026 — reason gates đã VERIFIED, chưa migration

Owner duyệt lô reason gates inactive. Browser admin fallback lưu Epicv6/Taskv5/Subtaskv5; supplementary MCP đọc lại độc lập và assertions xác minh đúng screen+validator thêm tại Epic Reopen/Cancel/Restore, Task/Subtask Reopen, giữ các gates/layout/Resolution/assignee routing cũ. Before/readback/proofs: JIRA_REASON_GATE_BATCH_2026-10-10.md; checkpoint24/architecture15.29. Official MCP preflight PASS; đây không phải official MCP write.

inspect_scheme sau ghi vẫn10003; inspect_automation readComplete=true chỉA01 DISABLED. No migration329issues, A02–A05 hoặc Jira E2E. 88 local tests+Nodefixtures PASS không chứng minh runtime. Full reviewer/revision/retest/acceptance còn thiếu; monitorPAUSED và budget0 không đổi. Các bảng/mục lịch sử bên dưới không phải trạng thái hiện hành.

## Lịch sử 10/10/2026 — Task gate inactive đã lưu, chưa migration

Official MCP session smoke QAG3 PASS đúng owner/site/cloud. Forge development2.1.0 deploy Success, Jira catalog5validators. User duyệt previewa929d394/hashbcddcbed…; supplementary MCP apply VERIFIED và independent readback Taskv4: PM-only Approve/Deploy/Reopen, Deploy childDone+checklist/evidence. Giữ Resolution/native conditions/layout.88Python tests + Node predicate fixtures PASS, không Jira E2E. Reason module chưa attach/screens; full identity/revision/retest/concurrency pending. QAG3 scheme10003 unchanged, A01 tắt/A02–A05 chưa bật, monitorPAUSED. Xem checkpoint22/architecture15.27.

## Lịch sử 09/10/2026 — gate-first, chưa migration

Owner chọn hoàn thiện gate trước; chưa associate10004, QAG3 vẫn10003.329items đọc full4pages/unique đềuToDo10008. Native A01 UUID01a1216a-82a7-7a79-9f26-8102e7f6a942 được lưu DISABLED chỉQAG3 qua browser fallback, supplementary MCP readbackcomplete xác minh. A02–A05 chưa tạo/bật, Jira E2E NOT RUN. Forge source local thêm3draft validators reason/childrenDone/checklist+evidence; fixtures/lint PASS, chưa deploy/gắn workflow và không coi là full identity/retest/revision gates. MonitorPAUSED. Chi tiết checkpoint21/architecture15.26; lịch sử bên dưới không chứng minh activation.

## 0. Triển khai workflow dự án mới — một phần, chưa sẵn sàng vận hành

Kiểm tra ngày 2026-10-08: ban đầu site có KAN và SAM1. Sau khi phiên trình duyệt có đăng nhập, đã tạo QAG3 bằng UI quản trị và đọc lại qua MCP; project ID 10002, style classic. Plugin/MCP local vẫn không cung cấp operation ghi workflow/scheme cần thiết; dùng phiên UI quản trị cho phần cấu hình này, không đọc/lưu credential.

Đặc tả đã duyệt và bộ test: [jira-workflows.md](jira-workflows.md). Đích mới đã xác minh là **QLDAPM Agile Practice 3 / QAG3**. Không dùng KAN làm đích thay thế; các mục KAN bên dưới chỉ là lịch sử vận hành dự án cũ. Quyền UI tạo dự án/workflow đã quan sát; quyền role PM và năm thành viên chưa xác minh.

| Dấu vết triển khai cần lưu | Trạng thái hiện tại |
|---|---|
| Project key/ID, board ID mới | QAG3 / 10002 / board 3, company-managed Scrum, đã xác minh |
| Issue types mới | Epic 10000; Task 10011; Sub-task 10010, đã đọc lại MCP |
| Workflow Epic / Task / Subtask và version | Cả ba đã lưu Inactive, có các cạnh theo kế hoạch; Epic 6, Task 10, Subtask 4 status. ID/rule và giới hạn: JIRA_PROGRESS_CHECKPOINT_2026-10-09.md; chưa gắn project hoặc nghiệm thu gates |
| Workflow scheme hiện tại | QAG3 vẫn gắn10003; scheme mới10004 đã ánh xạ3workflow nhưng chưa gắn/publish, xem mục11 |
| Workflow mặc định hiện tại | `2bf6edf8-90ad-4092-92dd-63a10acf6041`, chỉ dùng trong QAG3 theo UI; chưa sửa |
| Issue type / permission scheme | Issue type scheme `QAG3: Scrum Issue Type Scheme`; permission scheme chưa đối soát hoặc chỉnh sửa |
| Năm account ID và role PM/BA/BE/FE/Tester | Chưa xác minh đủ |
| Xác minh thành viên 2026-10-09 | listJiraIssueAssignableUsers xác nhận hiepk40c assignable; bốn email còn lại trả [] ở cả assignability và lookup. Xem JIRA_GOAL_CONTINUATION.md; chưa invite/role write |
| Trường checklist, hard gates, Resolution | Task Deploy có Subtask Done condition; Task/Subtask có Resolution actions; Epic v3 đã thêm Accept/Reopen/Restore Resolution qua lô duyệt mục11. Chưa đủ checklist/hard gate Epic–Task/PM-only; chưa E2E |
| Automation actor, rule ID/version/audit | Chưa tạo/bật |
| Kết quả mẫu, replay/concurrency, non-PM negative tests | NOT RUN |
| CSV WBS mới và đối soát import | Đã tạo v7 DRAFT local: 11 Epic/53 Task/265 Subtask, nguồn Story/106 AC đã kiểm tra. Chưa nhập; xem JIRA_WBS_GUIDE.md |
| Snapshot Sprint và chấm hiệu suất mô phỏng | Chưa triển khai/kiểm thử |

Điểm chặn: gate native được quan sát chỉ kiểm tra Subtask, chưa có gate đọc trực tiếp toàn bộ Task của Epic. Ngân sách 0, không cài app trả phí/trial/JSU. Năm email/role mong muốn đã cung cấp và lưu checkpoint; accountId/assignability và project role bốn người còn lại chưa xác minh. Không bật automation hoặc nhập toàn bộ trước khi thống nhất giải pháp gate và kiểm thử.

Chỉ cập nhật hoàn tất khi đọc lại cấu hình thật và có bằng chứng. Công việc Jira tạm dừng để bootstrap theo yêu cầu. Checkpoint mới: [JIRA_PROGRESS_CHECKPOINT_2026-10-09.md](JIRA_PROGRESS_CHECKPOINT_2026-10-09.md). QAG3 đọc lại chưa có issue và các type vẫn dùng To Do/In Progress/Done; ba workflow riêng chưa áp dụng. Tiếp tục phải preview/duyệt theo AGENTS.md mới. KAN không bị thay đổi.

## 1. Đích quản lý và kết nối

| Thuộc tính | Giá trị đã xác minh |
|---|---|
| Site | https://luimjiraqldapm.atlassian.net |
| Cloud ID | 560ef0cc-d24b-4613-98d3-d541afe8f32b |
| Project | QLDAPM_AI / KAN / ID 10001 |
| Board | KAN board / ID 2 / type simple (team-managed) |
| Luồng trạng thái | To Do → In Progress → In Review → Done |
| MCP server | atlassian — https://mcp.atlassian.com/v2/mcp |
| Codex config | C:\Users\LUIM\.codex\config.toml |
| Authentication | OAuth, được Codex lưu trữ; repository không chứa token |
| Repository tài liệu | D:\AI project\QLDAPM chat |

MCP trực tiếp và plugin Atlassian trong app là hai kết nối riêng. Lịch sử 2026-10-08: plugin đọc KAN-68, đối chiếu 11 Epic/53 Story và ghi comment 10002. Bootstrap 2026-10-09 kiểm tra trực tiếp MCP local đang expose, không kiểm tra lại hosted plugin; ưu tiên MCP chính thức đã xác minh của phiên.

## 2. Quy trình gọi công cụ

Ưu tiên công cụ Atlassian MCP đã xác thực có sẵn trong task. Nếu công cụ plugin báo chưa đăng nhập, dùng helper `tools/jira_mcp.py`; helper khởi tạo một phiên Codex app-server tạm, gọi chính MCP chính thức và sử dụng credential store của Codex. Helper không tạo một agent khác hay gọi model, và dừng tiến trình con khi xong.

Đọc schema đang được server cung cấp trước khi dùng tham số mới:

```powershell
& 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\AI project\QLDAPM chat\tools\jira_mcp.py' getJiraIssue --describe
```

Đọc một Story:

```powershell
'{"cloudId":"560ef0cc-d24b-4613-98d3-d541afe8f32b","issueIdOrKey":"KAN-5","view":"compact"}' |
  & 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\AI project\QLDAPM chat\tools\jira_mcp.py' getJiraIssue
```

Tìm backlog theo JQL:

```powershell
'{"cloudId":"560ef0cc-d24b-4613-98d3-d541afe8f32b","jql":"project = KAN AND labels = qldapm-mvp ORDER BY key ASC","maxResults":100,"view":"compact"}' |
  & 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\AI project\QLDAPM chat\tools\jira_mcp.py' searchJiraIssuesUsingJql
```

Tìm operation chưa có trong catalog chính:

```powershell
'{"query":"list Jira issue transitions"}' |
  & 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\AI project\QLDAPM chat\tools\jira_mcp.py' discover
```

Dùng đúng operation và schema trả về bởi discover rồi gọi executeRead/executeWrite/executeDestructive theo nhóm của operation. Truyền cloudId ở cấp ngoài và các tham số operation trong inputs. Tên thao tác không được suy đoán từ REST API.

Nếu JSON-RPC trả data là một CallToolResult lồng nhau, bóc tiếp content cho đến khi nhận dữ liệu domain. Một số kết quả discover bổ sung phần văn bản sau JSON; đọc khối JSON cùng phần ghi chú. Kiểm tra isError ở mỗi lớp và không coi lỗi trả về như thành công.

Mỗi truy vấn danh sách phải đọc hết pagination để kết luận toàn bộ. Khi thao tác ghi timeout, đọc lại bằng key/source label trước khi quyết định retry; không tự tạo lại.

## 3. Backlog đã nhập

Nguồn: user-story-web-quan-ly-du-an-rut-gon.docx. Đã đối soát toàn bộ dữ liệu Jira sau khi nhập: 11 Epic, 53 Story, 106 Acceptance Criteria; mỗi Story có đúng Epic cha và source ID duy nhất. Không có E11 (Burndown chart).

Ba ticket có sẵn KAN-1, KAN-2, KAN-3 được giữ lại. Các item nhập dùng labels `qldapm-mvp`, `codex-import`, `source-<ID>`; ticket vận hành kết nối KAN-68 dùng labels riêng `codex-setup`, `mcp-connection-check` và không tính vào 53 Story.

| Epic | Tên | Jira key | Số Story |
|---|---|---|---|
| E01 | Tài khoản & Role | [KAN-4](https://luimjiraqldapm.atlassian.net/browse/KAN-4) | 5 |
| E02 | Quản lý Project | [KAN-6](https://luimjiraqldapm.atlassian.net/browse/KAN-6) | 6 |
| E03 | Backlog | [KAN-7](https://luimjiraqldapm.atlassian.net/browse/KAN-7) | 5 |
| E04 | Sprint | [KAN-8](https://luimjiraqldapm.atlassian.net/browse/KAN-8) | 5 |
| E05 | Task / User Story | [KAN-9](https://luimjiraqldapm.atlassian.net/browse/KAN-9) | 5 |
| E06 | Kanban | [KAN-10](https://luimjiraqldapm.atlassian.net/browse/KAN-10) | 4 |
| E07 | Gantt / Timeline | [KAN-11](https://luimjiraqldapm.atlassian.net/browse/KAN-11) | 4 |
| E08 | Issue / Bug | [KAN-12](https://luimjiraqldapm.atlassian.net/browse/KAN-12) | 5 |
| E09 | Comment | [KAN-13](https://luimjiraqldapm.atlassian.net/browse/KAN-13) | 5 |
| E10 | Dashboard | [KAN-14](https://luimjiraqldapm.atlassian.net/browse/KAN-14) | 4 |
| E12 | Notification | [KAN-15](https://luimjiraqldapm.atlassian.net/browse/KAN-15) | 5 |

### Ánh xạ nguồn → Jira

| Story ID | Jira key | Epic cha |
|---|---|---|
| AUTH-01 | [KAN-5](https://luimjiraqldapm.atlassian.net/browse/KAN-5) | KAN-4 |
| AUTH-02 | [KAN-16](https://luimjiraqldapm.atlassian.net/browse/KAN-16) | KAN-4 |
| AUTH-03 | [KAN-17](https://luimjiraqldapm.atlassian.net/browse/KAN-17) | KAN-4 |
| AUTH-04 | [KAN-18](https://luimjiraqldapm.atlassian.net/browse/KAN-18) | KAN-4 |
| AUTH-05 | [KAN-19](https://luimjiraqldapm.atlassian.net/browse/KAN-19) | KAN-4 |
| PRJ-01 | [KAN-20](https://luimjiraqldapm.atlassian.net/browse/KAN-20) | KAN-6 |
| PRJ-02 | [KAN-21](https://luimjiraqldapm.atlassian.net/browse/KAN-21) | KAN-6 |
| PRJ-03 | [KAN-22](https://luimjiraqldapm.atlassian.net/browse/KAN-22) | KAN-6 |
| PRJ-04 | [KAN-23](https://luimjiraqldapm.atlassian.net/browse/KAN-23) | KAN-6 |
| PRJ-05 | [KAN-24](https://luimjiraqldapm.atlassian.net/browse/KAN-24) | KAN-6 |
| PRJ-06 | [KAN-25](https://luimjiraqldapm.atlassian.net/browse/KAN-25) | KAN-6 |
| BLG-01 | [KAN-26](https://luimjiraqldapm.atlassian.net/browse/KAN-26) | KAN-7 |
| BLG-02 | [KAN-27](https://luimjiraqldapm.atlassian.net/browse/KAN-27) | KAN-7 |
| BLG-03 | [KAN-28](https://luimjiraqldapm.atlassian.net/browse/KAN-28) | KAN-7 |
| BLG-04 | [KAN-29](https://luimjiraqldapm.atlassian.net/browse/KAN-29) | KAN-7 |
| BLG-05 | [KAN-30](https://luimjiraqldapm.atlassian.net/browse/KAN-30) | KAN-7 |
| SPR-01 | [KAN-31](https://luimjiraqldapm.atlassian.net/browse/KAN-31) | KAN-8 |
| SPR-02 | [KAN-32](https://luimjiraqldapm.atlassian.net/browse/KAN-32) | KAN-8 |
| SPR-03 | [KAN-33](https://luimjiraqldapm.atlassian.net/browse/KAN-33) | KAN-8 |
| SPR-04 | [KAN-34](https://luimjiraqldapm.atlassian.net/browse/KAN-34) | KAN-8 |
| SPR-05 | [KAN-35](https://luimjiraqldapm.atlassian.net/browse/KAN-35) | KAN-8 |
| TSK-01 | [KAN-36](https://luimjiraqldapm.atlassian.net/browse/KAN-36) | KAN-9 |
| TSK-02 | [KAN-37](https://luimjiraqldapm.atlassian.net/browse/KAN-37) | KAN-9 |
| TSK-03 | [KAN-38](https://luimjiraqldapm.atlassian.net/browse/KAN-38) | KAN-9 |
| TSK-04 | [KAN-39](https://luimjiraqldapm.atlassian.net/browse/KAN-39) | KAN-9 |
| TSK-05 | [KAN-40](https://luimjiraqldapm.atlassian.net/browse/KAN-40) | KAN-9 |
| KAN-01 | [KAN-41](https://luimjiraqldapm.atlassian.net/browse/KAN-41) | KAN-10 |
| KAN-02 | [KAN-42](https://luimjiraqldapm.atlassian.net/browse/KAN-42) | KAN-10 |
| KAN-03 | [KAN-43](https://luimjiraqldapm.atlassian.net/browse/KAN-43) | KAN-10 |
| KAN-04 | [KAN-44](https://luimjiraqldapm.atlassian.net/browse/KAN-44) | KAN-10 |
| GNT-01 | [KAN-45](https://luimjiraqldapm.atlassian.net/browse/KAN-45) | KAN-11 |
| GNT-02 | [KAN-46](https://luimjiraqldapm.atlassian.net/browse/KAN-46) | KAN-11 |
| GNT-03 | [KAN-47](https://luimjiraqldapm.atlassian.net/browse/KAN-47) | KAN-11 |
| GNT-04 | [KAN-48](https://luimjiraqldapm.atlassian.net/browse/KAN-48) | KAN-11 |
| BUG-01 | [KAN-49](https://luimjiraqldapm.atlassian.net/browse/KAN-49) | KAN-12 |
| BUG-02 | [KAN-50](https://luimjiraqldapm.atlassian.net/browse/KAN-50) | KAN-12 |
| BUG-03 | [KAN-51](https://luimjiraqldapm.atlassian.net/browse/KAN-51) | KAN-12 |
| BUG-04 | [KAN-52](https://luimjiraqldapm.atlassian.net/browse/KAN-52) | KAN-12 |
| BUG-05 | [KAN-53](https://luimjiraqldapm.atlassian.net/browse/KAN-53) | KAN-12 |
| CMT-01 | [KAN-54](https://luimjiraqldapm.atlassian.net/browse/KAN-54) | KAN-13 |
| CMT-02 | [KAN-55](https://luimjiraqldapm.atlassian.net/browse/KAN-55) | KAN-13 |
| CMT-03 | [KAN-56](https://luimjiraqldapm.atlassian.net/browse/KAN-56) | KAN-13 |
| CMT-04 | [KAN-57](https://luimjiraqldapm.atlassian.net/browse/KAN-57) | KAN-13 |
| CMT-05 | [KAN-58](https://luimjiraqldapm.atlassian.net/browse/KAN-58) | KAN-13 |
| DSH-01 | [KAN-59](https://luimjiraqldapm.atlassian.net/browse/KAN-59) | KAN-14 |
| DSH-02 | [KAN-60](https://luimjiraqldapm.atlassian.net/browse/KAN-60) | KAN-14 |
| DSH-03 | [KAN-61](https://luimjiraqldapm.atlassian.net/browse/KAN-61) | KAN-14 |
| DSH-04 | [KAN-62](https://luimjiraqldapm.atlassian.net/browse/KAN-62) | KAN-14 |
| NOT-01 | [KAN-63](https://luimjiraqldapm.atlassian.net/browse/KAN-63) | KAN-15 |
| NOT-02 | [KAN-64](https://luimjiraqldapm.atlassian.net/browse/KAN-64) | KAN-15 |
| NOT-03 | [KAN-65](https://luimjiraqldapm.atlassian.net/browse/KAN-65) | KAN-15 |
| NOT-04 | [KAN-66](https://luimjiraqldapm.atlassian.net/browse/KAN-66) | KAN-15 |
| NOT-05 | [KAN-67](https://luimjiraqldapm.atlassian.net/browse/KAN-67) | KAN-15 |

## 4. Quy tắc quản lý

1. Với công việc mới dùng project QAG3 và source label; KAN chỉ là lịch sử, không được ghi trừ khi có yêu cầu riêng. Không có match thì đề xuất tạo; một match thì đọc/preview diff; nhiều match thì báo trùng. Mọi ghi cần duyệt theo AGENTS.md.
2. Source ID là mã trong tài liệu, Jira key là mã ticket: ví dụ source `KAN-01` là Story `KAN-41`, không phải Jira `KAN-1`.
3. Đọc ticket trước khi sửa, giữ nguyên field không nằm trong yêu cầu. Với labels/components phải giữ toàn bộ giá trị hiện có khi ghi thay thế.
4. Giữ Story và Acceptance Criteria trong description; parent trỏ về Epic thật. Không coi nhập backlog là hoàn thành chức năng.
5. Lấy transition ID từ listJiraIssueTransitions ngay trước khi chuyển trạng thái. Lấy accountId từ người thực sự assignable trước khi giao việc.
6. Estimate, assignee, Sprint và ngày thực hiện cần dựa trên refinement/kế hoạch thật; chưa được quyết định thì để trống.
7. Draft/read/report không cần duyệt bổ sung; create/edit/triage có ghi phải preview và duyệt theo AGENTS.md mới. Thay đổi kiến trúc đi kèm architecture.md.
8. Khi cần lịch chạy tự động, tạo automation với tần suất người dùng yêu cầu. Kết nối MCP không có nghĩa là agent đang chạy liên tục khi task không hoạt động.

Lịch tiếp tục được người dùng yêu cầu đã tạo qua Codex App MCP: heartbeat `ti-p-t-c-jira-qag3-sau-reset-quota`, ACTIVE, hằng ngày 08:25; quota thật snapshot còn 83%/82%. Xem [JIRA_GOAL_CONTINUATION.md](JIRA_GOAL_CONTINUATION.md). Đây không phải Jira Automation A01–A05 hoặc lịch chấm nhân sự. Goal chưa hoàn tất; dừng scheduler chỉ sau nghiệm thu toàn bộ. Thiếu tool admin/assignability không phải lỗi quota.

## 5. Sprint và quyền quản trị còn cần cấu hình

Board 2 trả lỗi `The board does not support sprints`. Nó là board team-managed; createJiraBoard không hỗ trợ tạo thêm company-managed Scrum board bên trong Project này. Để dùng Scrum trên Project hiện tại, đăng nhập Jira UI và bật Backlog/Sprints trong phần Features của Project nếu tài khoản/gói hỗ trợ, sau đó kiểm tra lại listJiraBoardSprints. Chưa tạo hay start Sprint vì tính năng này chưa bật và lịch/capacity chưa được chốt.

MCP kiểm soát theo scope và quyền Jira thật. Các thao tác quản trị hoặc xoá có thể cần admin bật permission group tương ứng. Workflow editor có thể chỉ được mở để review; không coi lấy link editor là đã áp dụng workflow. Đã xác minh quyền edit Project bằng listJiraProjects action=edit; chưa kiểm thử org admin, xoá dữ liệu hoặc mọi thao tác quản trị.

Phiên trình duyệt trong app đã đăng nhập và đã dùng lưu workflow Inactive ở công việc trước bootstrap, độc lập OAuth MCP. UI không phải MCP; chỉ fallback được công bố cho thao tác thiếu MCP và cần approval phù hợp. Bootstrap không sửa Jira qua UI.

## 6. Kiểm tra, khôi phục và nguồn tham khảo

- `codex mcp list`: atlassian phải enabled và Auth OAuth.
- `codex mcp login atlassian`: xác thực lại nếu grant hết hạn/bị thu hồi; người dùng hoàn tất OAuth.
- Helper phải đọc được atlassianUserInfo và getJiraIssue từ một tiến trình mới.
- Phiên bản đã kiểm tra: Codex CLI 0.159.2, MCP server atlassian-mcp-server 1.0.0.
- Kết quả import/đối soát là snapshot ngày 2026-10-08; đọc dữ liệu hiện tại trước khi kết luận số lượng hoặc trạng thái ở lần sau.
- Rollback cấu hình MCP: `codex mcp remove atlassian` gỡ kết nối local; thu hồi grant tại Atlassian nếu cần. Nó không xoá backlog trên Jira.
- Nếu muốn khôi phục backlog nhập, dùng source labels/mapping để nhận diện đúng item và thống nhất phương án phục hồi trước mọi thao tác xoá không thể hoàn tác.

Nguồn chính thức: [Codex MCP](https://developers.openai.com/codex/mcp), [Codex App Server](https://developers.openai.com/codex/app-server), [Atlassian MCP setup](https://developer.atlassian.com/cloud/rovo-mcp/guides/getting-started/), [Supported tools](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/).

## 7. WBS v7 và kiểm tra tiếp tục 2026-10-09

[CSV v7](Jira_WBS_QAG3_v7_DRAFT.csv) và [hướng dẫn](JIRA_WBS_GUIDE.md) đã tạo/kiểm tra local. 329 item chưa nhập; 1297 giờ/Point chỉ mô phỏng đề xuất, chưa ghi estimate/assignee thật. Parent tạm phải resolve key thật. Approval WBS/lô ghi đang chờ.

Preflight mới: local/hosted MCP cùng trả account/site đúng; local `listJiraProjects` xác nhận QAG3 classic/10002, `listJiraStatuses` cả hai vẫn To Do/In Progress/Done. JQL QAG3 issues=[], isLast=true. Discovery regular/exact không trả admin workflow/scheme/automation cần thiết; không kết luận NO PERMISSION khi chưa có 403. Năm truy vấn assignable: chỉ hiepk40c có account, bốn email khác vẫn []. Không gán thay bằng chủ dự án.

Quota snapshot khoảng 03:56–03:57 +07: ordinaryUsageAllowed=true, còn 65% primary/79% secondary; không quota block/reset credit/chi phí. automation_update(view) trả card thành công; config lịch cũ ACTIVE/08:25 đọc lại nhưng chưa chứng minh scheduled run đã thực thi. Không tạo lịch mới/ghi Jira/REST/UI. Scope chưa đạt; tiến trình ở JIRA_GOAL_CONTINUATION.md.

## 8. Mời qua email và lựa chọn tích hợp — 2026-10-09 13:20 +07

Người dùng xác nhận chỉ cần gửi email mời để thành viên tự accept; giao agent lựa chọn phương án quản lý AI tối ưu. Chọn giữ official MCP cho tác nghiệp và bot đọc, bổ sung local admin MCP hẹp gọi API chính thức khi có credential và được phép thực hiện thay đổi cụ thể. Không lựa chọn server quảng cáo full admin nhưng chưa xác minh/license chưa rõ. Đề xuất kỹ thuật: JIRA_FULL_CONTROL_RESEARCH_2026-10-09.md; chưa cài server, chưa sửa MCP config.

**Preflight thực:** official `atlassianUserInfo`, `getAccessibleAtlassianResources`, `executeRead(listJiraProjects)` đúng account/site/cloudId, QAG3/10002/classic. Hai truy vấn discovery mời email không trả operation Jira invitation. Connection read VERIFIED; admin FULL chưa xác minh, không có 403 để quy nguyên nhân thành thiếu quyền.

**Fallback UI đã công bố:** từ Jira Settings → User management mở đúng org `2ce490bd-70de-4c97-aede-e693a5651adc`. Users hiển thị 1 tổng/1 active, hiepk40c là organization admin theo UI. Form mời mặc định chọn 5 ứng dụng; đã bỏ chọn tất cả trong draft, chưa điền email hoặc submit. Administrator access vẫn None. Sau đó hủy form; không tạo invitation, user hoặc membership mới. Chủ tài khoản đã active nên chỉ bốn email còn lại cần mời khi đủ điều kiện, không tự gửi lại cho chủ tài khoản.

**Phát hiện billing mới, thay thế UNKNOWN trước đây:** Jira trên site đang Premium FREE 30-DAY TRIAL, Monthly, kết thúc 07/11/2026; Next bill estimate USD18.30 cho 1 user. Payment info None; banner yêu cầu payment method trước ngày đó, nếu không subscription sẽ bị deactivated. Đây là estimate/cảnh báo tương lai, không phải khoản phí đã thu. Không mở rộng seat trước khi chốt ngân sách; không thêm payment method, kích hoạt trial, đổi/hủy gói.

Billing Change plan đã mở chỉ để đọc: có Free $0/10 users, không gồm user roles/permissions; đã đóng hộp chọn, giữ nguyên Premium trial. Chọn Free về mặt đề xuất vì ngân sách0, nhưng owner phải tự xác nhận bước đổi subscription; có ảnh hưởng toàn site và tính năng/quyền, không tự thực hiện bằng quyền quản trị QAG3. Không coi hạn chế Free đã giải quyết hoặc âm thầm hạ hard gates.

Chỉ kiểm tra boolean credential trong process/user environment: ATLASSIAN_API_TOKEN/JIRA_API_TOKEN/ATLASSIAN_EMAIL/JIRA_EMAIL đều chưa có. Không đọc credential store khác/cookie/OAuth token, không tạo token thay người dùng. OAuth official MCP hiện có không phải credential được phép dùng tùy ý cho Automation public API. Tạo/cấu hình credential mới cần người dùng thực hiện an toàn ngoài chat trước live admin integration.

Next: owner xác nhận Free trên billing; đọc lại gói → mời bốn email đúng site, chỉ Jira User (không admin, không app ngoài scope), theo dõi invited/accepted → xác minh assignability qua MCP. Sau đó tiếp tục tích hợp/gates/sample test trước WBS; không tự import toàn bộ hoặc tuyên bố full control. Goal/monitor/lịch hiện có giữ nguyên, không tạo lịch trùng; runtime process không kiểm tra lại trong lượt này.

## 9. Free đã chuyển, MCP/API bắt đầu — 2026-10-09 13:36 +07

User yêu cầu chuyển Free/thiết lập MCP API; action-time approval “Xác nhận chuyển Free” nhận. Official identity/resources/listJiraProjects verify QAG3/10002/classic, discover không có billing. Browser fallback SelectFree/Downgrade/SkipSurvey success/read-back PlanFree/1user/PaymentNone, không thêm payment/gói trả phí. Gói toàn site đổi riêng theo approval, không Jira data write KAN/SAM1.

Global qag3-admin đăng ký/read-back enabled/stdio,4tool inspection/preflight, chưa ghi. SDKmcp1.30.0/venv riêng/fixedgateway/QAG3/identity/allowlist/redactederrors.11admin tests/total43Python PASS; PowerShell parse/pipcheck PASS. Official MCP/helper/bot không đổi.

API mới CREDENTIAL MISSING/NOT LIVE VERIFIED. API tokens page step-up code8digit tới emailowner; owner tự nhập/create scopedtoken, chạy tools/Set-JiraAdminCredential.ps1 trong PowerShell tương tác để saveDPAPI ngoài repo. Agent chưa tạo/đọc/lưu token, không copy OAuth/cookie/chatkey. Runbook JIRA_ADMIN_MCP_SETUP.md; sau “đã lưu token” mới livepreflight/bổ sung write có preview/approval.

Chưa invitations/users/role/publish/scheme/automation/WBS;Free limits/hardgates không giải quyết tự động. Không báo fullquyền. Mục8 giữ lịch sử, bướcFree đã hoàn tất. Không đổi goal/lịch/runtime/cursor/Gemini hoặc chấmHR.

## 10. Token đã xác thực qua MCP local — 2026-10-09 13:53 +07

Sau owner “ĐÃ LƯU TOKEN”, official atlassian identity/resources/listJiraProjects verify đúng owner/site/QAG3/10002/classic. Actual supplementary SDK MCP stdio qua launcher initialize/list_tools/api_status/api_preflight thành công: credential present và API200 cho identity/project/mypermissions. ADMINISTER=true, ADMINISTER_PROJECTS=false; chưa thử write, không kết luận mọi admin operation unavailable hoặc full control từ các boolean này. Không cần tạo/lưu lại token, không echo secret hoặc sửa scopes.

inspect_scheme HTTP200: QAG3 vẫn scheme10003/default simplified workflow, issueTypeMappings={}; association chỉ trả10002. inspect_workflow/capabilities HTTP200: Epic v2/6status, Task v2/10status, Subtask v1/4status/isEditable=true. Epic chưa condition/validator/action; Task Deploy có Subtask Done gate/set Resolution, Reopen clear; Subtask Approve/Reopen có Resolution actions. Capabilities native không chứng minh Epic-child Task gate; Connect/Forge rules rỗng. Không publish/map workflow khi chưa đủ hardgates/approval/tests. Chưa invitations/automation/WBS/23E2E. Guide/architecture đã cập nhật; không code/config/bot/scheduler/HR hoặc Jira mutation trong lượt này. SDK stdio không đồng nghĩa current chat đã reload catalog hay app-server route đã tested.

## 11. MCP/API lô chuẩn bị đã duyệt — 2026-10-09 14:13 +07

**Session check:** official `atlassianUserInfo`, `getAccessibleAtlassianResources`, `executeRead(listJiraProjects)` PASS đúng owner/site/cloudId/QAG3/10002/classic. Discovery admin thiếu operation cần dùng; supplemental qag3-admin gọi thực qua Codex app-server (helper --server qag3-admin), api_preflight PASS. Browser fallback NONE. ADMINISTER=true/ADMINISTER_PROJECTS=false không phải kết luận full quyền.

Approval “Duyệt lô chuẩn bị này” chỉ cho Epic Resolution và tạo scheme chưa dùng. `preview_workflow_resolution` + API validation errors=[] → `apply_change` VERIFIED: Epic5079dd5a v2→v3, Accept Epic Resolution Done10000, Reopen/Restore clear. Read-back đối chiếu semantics toàn trạng thái/cạnh/actions/conditions/validators, bỏ qua ID rule do server cấp; không đổi gates.

`preview_scheme(create_scheme)` → `apply_change` VERIFIED: **10004 / QAG3 Managed Delivery v1**, default QAG3 Task Delivery v1, mappings Epic10000/Task10011/Sub-task10010 vào3workflow cố định. **inspect_scheme sau ghi vẫn QAG3→10003**; chưa associate/publish, không đụng scheme nội bộ10003. Audit preview/started/result ngoài repo; ID/hash/rollback trong JIRA_ADMIN_MCP_SETUP.md.

`inspect_automation` HTTP200, rules=[]/readComplete=true: scoped credential đọc API được; chưa rule live-write.10tool có preview/apply và poll async; automation chỉ đọc/disable existing-QAG3, không create/edit components/enable. Publish/associate có rollout guard dựa23JiraE2E thực+review+fingerprint+project rỗng, không giả mock thành E2E, không thay hardgate Jira.72/72Python local PASS; official helper mặc định identity smoke PASS. Không invite/issue/WBS/role/notification write, không KAN/SAM1, không đổi bot/lịch/Gemini/config global hoặc billing trong lô này.

Pending: hardgate Epic–Task/PM-only/checklist/reason/concurrency;23JiraE2E; mẫu component automation A01–A05 thật; approval activation riêng; member invite/assignability; WBS duyệt và nhập. Chưa full control hoặc goal complete; không dừng bot định kỳ.

## 12. Lời mời đã gửi và identity nhóm đã resolve — 2026-10-09 14:39 +07

Action-time approval **“Duyệt gửi 4 lời mời Jira User”** đã nhận và thực hiện bằng giao diện admin, sau official MCP preflight/discovery. Chỉ Jira User trên Free; Administrator=None, không Jira Administration/app khác/group tùy chỉnh. UI xác nhận4người được thêm, bốn email đều **Đã mời**; không mời lại owner. Mời đã gửi không có nghĩa người nhận đã accept hoặc email đã được chuyển tới hộp thư.

Official `executeRead(listJiraIssueAssignableUsers)` cho QAG3 trả đủ5accountId. **JIRA_TEAM_QAG3.json** lưu mapping email/nghiệp vụ/accountId và nguồn UI/MCP. Đây là dữ liệu nhận diện/assignability để dùng ở lô WBS được duyệt, chưa là cấu hình project role hoặc issue assignment. Ảnh proof: `jira-bot/jira-invitations-2026-10-09.jpg`.

MCP supplemental đọc lại QAG3 vẫn scheme10003; automation rules[]/readComplete=true; official JQL issues[]/isLast=true. Epic custom vẫn không condition/validator, connect/forge capabilities rỗng. Không activate scheme hoặc bỏ gates. Cần bổ sung server-side validator được kiểm chứng nếu muốn đáp ứng hợp đồng hiện tại; API token/MCP không tự tạo tính năng đó.

Guard local T01–T23-before-associate/publish và empty-project mâu thuẫn với T23 toàn bộ import. Đã ghi checkpoint; cần đổi **trình tự nghiệm thu** qua preview/approval, không đổi kết quả yêu cầu hoặc giả PASS. Workflow/automation components/E2E/WBS vẫn pending; bot giám sát không đổi, không lặp lời mời.

## 13. WBS đã nhập thành backlog nháp — 2026-10-09 15:11 +07

User duyệt **“Duyệt nhập backlog nháp trước”** sau preview329mục/To Do/DRAFT/five accounts/no automation/no Sprint/no actual simulation fields. Ngoại lệ chỉ cho thứ tự import, không cho publish/association/giảm gate hoặc công nhận nghiệm thu. Official preflight identity/resources/editable QAG3, metadata3types, assignee5 và statuses ba trạng thái mặc định PASS; QAG3 rỗng trước ghi.

Official `createJiraIssue` tạo mẫu7 (QAG3-1→2→3–7), từng mẫu `getJiraIssue` đọc lại khớp rồi tiếp tục toàn bộ. Dedup bằng source label trước tạo; Parent dùng key thật. PRJ-03-QA bị transport closed sau write: source search xác minh QAG3-49 tồn tại, readback đạt, không gửi lại create. Một read transport lỗi đã đọc lại an toàn, không giả lỗi là chưa có issue.

**Kết quả live:** QAG3-1 đến QAG3-329, full JQL bốn trang tới isLast=true, không duplicate key/source, đúng11Epic/53Task/265Sub-task. Đối chiếu từng mục: project/type/summary/assignee/Parent/labels, description bảo toàn sau chuẩn hóa Markdown, checklist unchecked, timetracking={}. 106AC nguồn được giữ trong53Task. verifiedAtUtc **2026-10-09 08:11:19 UTC**; audit/mapping `jira-bot/wbs-import-QAG3-2026-10-09.json`. CSV hash49368cf8… vẫn nguyên, không sửa CSV gốc hoặc Word.

Assignee theo `JIRA_TEAM_QAG3.json`: BA/BE/FE/Tester53Subtask mỗi người, PM53Subtask+53Task+11Epic; không cộng các cấp thành năng suất. Invite acceptance/project role chưa chứng minh. DRAFT/To Do không nghĩa công việc hoàn tất hoặc hard gates hoạt động. Priority/simulation hours/Point/proposedSprint/dependency source chỉ notes; không ghi worklog/estimate thật, không start Sprint hoặc chấm HR.

Không associate/publish/create-enable automation, không sửa token/role/AGENTS/admin code/bot/lịch/Gemini/KAN/SAM1, không upload Artifacts. QAG3 nay có dữ liệu: empty-project admin guard chặn rollout, cần migration/status mapping được duyệt riêng và giữ hard gates; không tự bypass. Setup toàn bộ/goal chưa complete. JIRA_WBS_GUIDE.md mục7 và checkpoint mục8 là trạng thái hiện hành, thay mọi ghi chú WBS-chưa-nhập trước đây.

## 14. Workflow Subtask phân nhánh đang chờ lưu — 2026-10-09 15:38 +07

User chọn Task10-status theo ảnh; Subtask BA/QA/PM4-stage và BE/FE7-stage qua Code Review/test. Official MCP preflight/project/sample/status đọc đúng QAG3; official discovery chưa expose workflow-admin. Supplementary registered qag3-admin đọc Taskv2 đúng graph và Subtaskv1/inactive. Local preview_subtask_delivery bổ sung11th tool, 77localtests PASS; nativeUI chỉ đọc form/Cancel, không Save. Equals Assignee từng người trong ANY đã validation errors=[] cho preview19360e5d/hash13641cfd…; chưa apply, approval đang hỏi riêng cho inactive only. Routing assignee không security role, chưa E2E và không giải quyết reviewer/PM/checklist hard gates. Không activation/migration329issue/automation; monitor tiếp tục pause. Hợp đồng/rollback trong jira-workflows.md13 và architecture15.16.

## 18. Hiện hành: field foundation áp dụng riêng QAG3 — 09/10/2026

Approval copy/giữ cấu hình hiện tại đã thực hiện: Field Scheme4 QAG3 Gate Fields v1,60field gốc unchanged+3field mới, chỉ association project10002. customfield_10043 Change reason textarea;10044 Acceptance checklist multicheckboxes/8options IDs10020–10027;10045 Review evidence textarea. Availability chỉ Epic/Task/Sub-task, required none; Global contexts không restrict, không gọi đây là context riêng QAG3.

Screen schemes10010/10011 và work type screen scheme10002 chỉ QAG3: append3field vào dedicated screens10010/10011, giữ17field cũ/order. Official MCP create metadata đủ trang Epic18/Task19/Subtask19 xác minh IDs/schema/optional/8options; supplemental inspect definitions complete/count3. Browser fallback thực hiện admin mutation, không giả official MCP hỗ trợ admin. Chi tiết proof/rollback tại field preview và checkpoint20.

Chưa activate/migrate329issue/A01–A05/full checklist/reason/retest gates/E2E; monitor giữ paused. Field entry không là nghiệm thu hay bằng chứng reviewer. Bước kế tiếp preview transition screens/validators với IDs thật, không reimport WBS hoặc tạo fields trùng.

## 17. Lịch sử: field foundation partial — 09/10/2026

Chủ dự án duyệt reason/checklist/evidence. Đã tạo QAG3 Change reason/customfield_10043 qua browser fallback; supplementary MCP xác minh textarea/readComplete. Global context10147 không restrict được trong UI mới. Hai field còn lại chưa tạo; không thêm screen/scheme hoặc giá trị issue. Đề xuất copy Default Field Scheme1/60fields thành QAG3 Gate Fields v1 để giới hạn availability chỉ QAG3/type hiện hữu, bảo toàn settings và readback trước association. Form chỉ preview/chưa Copy. Cần duyệt cơ chế mới; không sửa Default scheme, activate workflow/migrate/enable automation/resume monitor. Chi tiết tại checkpoint19/architecture15.24/JIRA_GATE_FIELDS_PREVIEW_2026-10-09.md.

## 16. Hai gate Epic inactive đã lưu — 09/10/2026

Forge development cài đúng site, Version2/Up-to-date; supplementary MCP catalog12tools. Sau exact approval preview ec2c3238-98ba-48b0-b61b-ea5770b607d7/hash ec9f2d8b5bec00c2d8f5c96c84852ca2589747861371180a29023788a5f6b902, validation errors=[], apply VERIFIED và independent inspect xác minh Epicv5: PM validator trên Approve scope/Accept/Cancel/Restore; child Tasks nonempty/allDone trên Submit acceptance/Accept. Giữ layout/Resolution, Task/Subtask không đổi. 83 local tests PASS, chưa Jira runtime tests. Không activation/migration329issue/A01–A05/full checklist/reason/retest hoặc resume monitor. Checkpoint16/architecture15.22 là bằng chứng hiện hành; audit/before ngoài repo, restore cần preview/approval mới. Không tuyên bố hoàn tất setup.

## 15. Subtask inactive đã lưu — 2026-10-09 15:50 +07 (lịch sử)

Approval user lưu inactive; preflight official identity/resources/QAG3-2 đúng site/cloud/project. Ghi bằng supplementary `qag3-admin apply_change` trên fresh preview766f1d95/hash62ea0b3d… validation errors=[] sau đối chiếu nguyên nội dung được duyệt. Subtaskv2/7status/13transition đã lưu. Tool trả UNKNOWN vì server reorder transitions; không retry, inspect độc lập và actual assertion theoID PASS. Giữ unknown audit, thêm reconciled evidence ngoài repo. Taskv2 nguyên cấu hình, associationQAG3 vẫn10003; không apply custom workflows vào329issue.

Fix local volatile-rule-ID fingerprint và order-insensitive status/transition readback đã regression-test;79Python tests PASS, không Jira E2E. Không role/gate/issue/automation/plan/token/monitor/KAN/SAM1 mutation. Chi tiết rollback/no-replay ở checkpoint11/architecture15.17/jira-workflows14; setup tổng thể còn pending.



# QA runtime và qualification automation — 13/10/2026

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

## Trạng thái cuối lượt — A02–A05 bật trong scope kiểm thử, chưa project-wide

- A01 giữ ENABLED; A02/A03/A04/A05 hiện ENABLED với trigger `labels = qag3-test`. Supplemental API read-back và assertions đã xác minh cả bốn. Đây không phải kích hoạt trên toàn bộ329WBS.
- Owner duyệt thay email A05 bằng bình luận @mention PM trong QAG3. UI đã lưu **hai action `jira.issue.comment`, không còn action email**; giữ actor Automation for Jira, routing PM đối ứng, frozen event/status, labels ADDREMOVE, marker-before-comment và canOtherRuleTrigger=false. Native `addCommentOnce=true`, sendNotifications=true, commentVisibility=null. Không sửa privacy, permission hoặc billing.
- Official MCP đọc đủ2comment trên fixture QAG3-332: **10005** @Khai khi assigneeHiệp, event `qag3-a05-10012-20261012191114566`; **10006** @Hiệp khi assigneeKhai, event `qag3-a05-10012-20261012191213831`. Cả hai do Automation for Jira tạo; chứa SIMULATION và không phải QA/acceptance/performance evidence. Account mention HTML đúng hai account IDs; không có visibility restriction. `jsdPublic=true` trong comment response không chứng minh issue mở public.
- A05 audit **Success**: `4c55363d-c626-4016-991e-0be6700a2cbe`/5.48s và `7c90de56-fcd2-4b19-9a0d-70f71c9f5921`/4.64s. Retest trước lần2: `2ae90e3a-d8b7-4d0c-87e2-70cece1a3dde`/No actions/0.85s. Không có marker10018 mới trong hai chu kỳ này. Đây chưa là stress/race/duplicate-engine test.
- Email pilot lỗi được giữ trong audit/labels, không xóa để giả thành công; không retry email nữa. Marker chỉ chứng minh attempt, không delivery. Comment tạo thành công không chứng minh inbox/email notification được nhận hoặc đọc.
- A05 variable phải alphabetic: `qagReviewEventKey`, lazy=false; frozen guard so sánh currentstatus/keylength với key.substring(9,14)/32. Format17timestamp thay toMillis; local frozen-event asserts PASS và independent saved-configuration asserts PASS.
- Parser evidence hiện tại cần **literal `\\n`** giữa7 dòng; lần thử newline thật bị QA-attest400, sau dùng format fixture đã được deploy chấp nhận thì transition thành công. Đây là hạn chế nhập liệu cần sửa riêng, không báo input lỗi là PASS hoặc thay đổi parser âm thầm.
- QAG3-332 vẫn REVIEW, assigneeKhai sau thử nhánh đối ứng; chỉ fixtures331–334 được thay đổi.329WBS/timeline/baEpic đầuDone/KAN/SAM1/billing giữ nguyên; monitorPAUSED.

Proof: `jira-bot/a05-comment-qualification-2026-10-13.json`, `jira-bot/QAG3-A05-mentions-final-2026-10-13.png`. Native comment syntax dựa trên [Atlassian comment action](https://support.atlassian.com/jira-software-cloud/docs/comment-on-issue-action/).

Remaining: full Subtask/native stale/non-PM/concurrency qualification và mở rộng scope từ qag3-test sang toàn dự án chưa hoàn tất. Không tạo rollout-evidence PASS hoặc gỡ activation guards. A05 duplicate guard/marker không atomic exactly-once. Rollback kênh: tắt A05 qua UI, giữ lịch sử comment/marker; phục hồi cấu hình trước chỉ qua preview phù hợp, không bật lại email đang lỗi.

Các mục dưới ghi diễn tiến trong lượt, không ghi đè trạng thái cuối phía trên.

## Đã xác minh

- Site luimjiraqldapm.atlassian.net, cloud560ef0cc-d24b-4613-98d3-d541afe8f32b, QAG3/10002. Official MCP preflight đúng owner/site và QAG3-332.
- Approved additive freshness gate đã apply/read-back Task active v8, hai transition Approve13/Deploy14; exact hash và audit trong jira-bot/qa-freshness-apply-2026-10-13.json.
- Forge development2.15.0 chỉ là bước thử: read-only PASS nhưng Approve thật vẫn vượt10 expensiveoperations. Không coi đó là E2E PASS.
- Development **2.16.0** đã deploy, SHA256 `6b4782bda709d0e3333ff8f547b59d23139d5cf0cfedb7715246f476ec13d3df`. Vẫn11 module, không scopes/functions/storage/egress/billing. Chỉ QA-current và companion tối ưu;9 module baseline khác giữ nguyên.
- Jira getNewestChangelog lọc items theo field: phải đọc status và evidence riêng, bắt buộc cùng changelog ID và evidence khớp nguyên văn. QA-current giữ author active/allowlist, structured evidence, checklist/retest và pending summary/description/evidence; companion kiểm tra5 core fields/latest status và pending Parent/assignee. Task ADF chỉ paragraph/text/hardBreak, unsupported fail-closed. Subtask legacy vẫn giữ nguyên hành vi.
- Native MCP QAG3-332 Approve13 → READY FOR RELEASE **thành công**; Deploy14 thiếu checklist trả400 đúng message gate. Sau sửa checklist trên fixture, Deploy14 → Done thành công; Resolution Done được read-back.
- A02 được giới hạn thêm `labels = qag3-test` qua UI fallback rồi bật cho qualification. Task332 Done → Epic331 tự REVIEW, independent official changelog **12058**, author Automation for Jira, 13/10 01:20:58+07. Không gửi transition Epic thủ công.
- A03 cũng giới hạn `qag3-test`, actor vẫn User who triggered, bật cho qualification; Task332 Reopen15 với fresh SIMULATION reason đã về IP. Parent outcome cần đọc lại.
- Node predicate/freshness và105 Python regression +1 additive test PASS; Forge lint PASS;11/11 expression Boolean type-valid; read-only provenance/freshness/forced paths PASS. Local automation graph51components/288cases PASS, không thay thế execution proof.

## Giới hạn, không che giấu

## Cập nhật sau kiểm thử

- Return7 lỗi thật: rule chuyển được Epic nhưng bỏ qua Change reason do không có screen. Owner đã duyệt exact hash `80f931a5255e4fd8962000f901b380554fd692bca432d8bb39a39f5dda62afc5`, preview `71c5c04c-95ae-4d96-afaf-ea972aa7c53b`. Guard CLI apply VERIFIED, independent MCP Epic **v9/89d407b5-d92c-47f7-a4c6-445cbba2c868** có screen10011 + fresh-reason validator tại7. Không đổi các gate khác. Native thử Return7 thiếu reason trả400 đúng message; A03 sau Task332 Reopen15 đã lưu reason cùng trạng thái Epic331 REVIEW→IP, changelog **12076**.
- A04 lượt đầu Some errors/`62de2b08-e8e3-437f-95bb-cfd3831cbffa`: Start delivery4 bỏ qua reason ngoài screen. Đã bỏ field gửi thừa ở **Start delivery4 và Submit acceptance5**; giữ reason ở Return7/Reopen8 và giữ mọi điều kiện/nhánh. Sửa timestamp `updated.toMillis` bị render rỗng sang `updated.format("yyyyMMddHHmmssSSS")`. Lượt đổi Parent333→331 tiếp theo **Success**, audit `1d421393-a66f-40fe-bb26-d5db115a4f8b`/12.62s. Native331 IP→REVIEW changelog12074;333 có Task334 NEW vẫnIP, không auto-Done/Cancel/Restore.
- Thêm đúng **hai fixture** QAG3-333 Epic và QAG3-334 Task NEW, labels qag3-test/qag3-simulation/excluded-from-performance, ngoài329WBS. QAG3-330 resolve sang KAN-69: chỉ đọc, không sửa hoặc tái sử dụng.
- A05 vẫn DISABLED trong lúc sửa event key. Dùng format17chữ số thay smartvalue toMillis không hoạt động; guard status so sánh `status-eventKey.length` với `triggerStatus-32` để timestamp rỗng không đi tới marker/email. Scope thêm qag3-test. Usage chỉ có estimate107steps/0Rovo credits, không chứng minh quota email hay góiFree.

### Còn phải kiểm tra

Task conjunction kiểm tra các field cốt lõi xác định, không quét mọi malformed metadata không liên quan. Companion chỉ có ý nghĩa cùng provenance gate; pending Parent/assignee đã chuyển sang companion, không được gỡ một gate. Chưa negative stale/retest/concurrency Jira đầy đủ, Subtask E2E, A03/A04/A05 full qualification hoặc email quota/delivery. A05 marker không atomic.

329 WBS, timelines, ba Epic đầu Done, KAN/SAM1, billing và bot monitor PAUSED không đổi. Chỉ fixture331/332 thay trạng thái/checklist/labels/reason. Rollback sửa nguồn hai module về development2.14.0 rồi lint/deploy qua preview riêng; vẫn giữ companion đã gắn, không uninstall app hoặc bỏ gate. A02/A03 đang giới hạn test, chưa công bố project-wide qualified.

Primary reference: [Jira expression types/getNewestChangelog, RichText và chi phí](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/). Đây là kiểm thử vận hành mô phỏng, không QA sản phẩm thật.

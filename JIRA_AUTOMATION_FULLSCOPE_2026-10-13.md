# A01–A05 — bật toàn QAG3, 13/10/2026

## Kết quả

Site https://luimjiraqldapm.atlassian.net, cloud560ef0cc-d24b-4613-98d3-d541afe8f32b, QAG3/10002. Official MCP identity/resources/issue smoke PASS, quota ordinaryUsageAllowed=true. Không mua/reset credit.

| Rule | Hiện hành | Điều kiện và hành động |
|---|---|---|
| A01 | ENABLED, không sửa | Task bắt đầu → Epic READY sang In Progress |
| A02 | ENABLED toàn QAG3 | Event chuyển **To Done**, Task Done có Parent; Epic IP và mọi Task Done → REVIEW, không tự nghiệm thu |
| A03 | ENABLED toàn QAG3 | Task chưaDone được duyệt scope → Epic REVIEW/Done sang IP, có reason; giữ actor User who triggered |
| A04 | ENABLED toàn QAG3 | Parent thay đổi ở Task duyệt scope → đối soát Epic cũ/mới theo trạng thái và scope hiện hành; không auto-Done/Cancel/Restore |
| A05 | ENABLED toàn QAG3 | Bước review → comment @mention PM đối ứng; frozen event/attempt marker, không email hoặc tự xác nhận QA |

A02–A05 không còn yêu cầu qag3-test; A03/A04 vẫn yêu cầu qag3-scope-approved. KAN/SAM1 bị loại bởi project scope. Bật rule không phải backfill lịch sử; không chạy đại trà để đổi329 trạng thái.

Route: official MCP cho issue/transition/changelog/comments; UI browser trong app cho trigger automation do discover chính thức không có operation; fixed supplemental official-API read-only cho đối soát. Gate write dùng fresh guarded CLI từ cùng source MCP sau exact owner approval, không giả thành registered MCP write khi process cache chưa có tool mới.

Before native configs: C:/Users/LUIM/AppData/Local/QLDAPM/jira-admin-audit/automation-rollout-before-2026-10-13.json. Final verifier exit0: scopeARI/actor/components nguyên vẹn, trigger chỉ bỏ fixture predicate và A02 thêm To Done. Mô tả A03/A04/A05 cập nhật trạng thái rollout; A05 đã lưu và đọc lại “full QAG3 simulation scope”. Không thay permission, privacy hoặc billing.

## Sửa Subtask và kiểm thử thực thi

1. Deploy2.20.0 hash73e07c827783c6471237ddce83d84bd5315367c1a854761f6e40bc0437a07f3a: thêm history module,11oldmodules unchanged.
2. Owner duyệt preview67fad996-051e-4871-a0c3-1c2065f3f940/hashda7c55436b262ca7b064057521727bff19c020e2fbd91fa6939d675caad9316f/errors=[]; apply VERIFIED, Subtask8→9/d9c8e3c0-0697-459c-aed8-c45924f8c6c7. Chỉ thêm history gate Approve4, giữ acceptance/freshness, screen10010/Resolution/graph.
3. Sau independent MCP đọc đủ3gate, deploy2.21.0 hashb8e9648dc25dc7f2c420612a2fbede46dd47837e50f12a2bcf4003fff6c645f7. Chuyển full history/ever-assigned/QA provenance sang gate riêng; acceptance giữ pending evidence/business review/simulation label; freshness giữ scope/actor/pending core/checklist.10module khác không đổi. Không truncate history hoặc bỏ điều kiện.

| Native test | Kết quả thực thi |
|---|---|
| BA/PM fixture335 reopen→review→approve | PASS; reuse review thiếu fresh evidence bị400; fresh v3 cho Done |
| BE fixture336 Approve4 | PASS trên2.21, không còn expensive-operations400; Done/ResolutionDone |
| FE routing trên cùng disposable fixture336 | Submit code→QA→Review→Approve Done PASS; assignee FE thật, actor vẫn owner simulation; trả assignee vềBE |
| Reopen6 thiếu reason | 400 đúng gate; fresh reason cho IP và clear Resolution |
| Pass testing dùng QA cũ | 400; fresh evidence/checklist cho REVIEW |
| Đổi summary sau QA rồi Approve4 | 400 history gate; restore summary vẫn cần Retest13 và QA mới; QA v3 cho Done |
| Task332 QA→Approve13→Deploy14 | PASS trên2.21; mới v6/v7 là SIMULATED PASS, không QA sản phẩm thật |
| Full-scope smoke không qag3-test | A03 reason/status12147; A02 status12155; A04 status12159 và2Success; A05 comment10012 |

Test issue332 được bỏ qag3-test tạm thời, giữ simulation/excluded-from-performance/scope-approved/marker; sau smoke trả Parent331, Done và thêm lại đúng nhãn test, không mất marker.335/336 Done,336 trảBE.329WBS/timeline/3Epic đầuDone/KAN/SAM1 không ghi; monitor tiếp tục theo policy PAUSED, không khởi động/resume trong lượt.

## A02 — lỗi event chồng và sửa cuối

Audit68b66dce-454c-4a50-a689-b313d4d776f2/03:35:39 Success;8399244f-98bd-4006-8b5d-963fb3ed19d9/03:35:40 Some errors: lượt sau không còn transition khi lượt trước đã đưa Epic331 vềREVIEW. Đây là kết luận đối chiếu hai event và changelog, không suy ra thiếu quyền từ thông báo generic.

Trigger cũ nhận mọi transition, JQL kiểm tra trạng thái khi thực thi nên Approve/Deploy sát nhau có thể cùng thấy Done. Native To status=Done đã lưu/read-back dạng [{"type":"NAME","value":"Done"}], From status giữ[]; actor/canOtherRuleTrigger=false/components giữ nguyên. Chạy lại rapid Approve/Deploy trên fixture khôngqag3-test và đọc Parent REVIEW. Không xóa audit lỗi cũ; không tuyên bố cơ chế này atomic/exactly-once.

Config change8976fcbc-1697-4e2b-8f6c-1e5792af1f9e lúc03:47:39+07. Lượt rapid sequence sau sửa: **2baff71f-5c8a-45a8-8396-344846e5748a/03:48:56+07/Success/4.80s**, chỉ một run execution trong audit kể từ config change ở lần quan sát này; không có Some errors mới ở sequence vừa thử. Proof QAG3-A02-done-filter-success-2026-10-13.png. Không suy ra exactly-once cho nhiều Task hoặc delivery replay từ một sequence.

## Kiểm tra và giới hạn

- 106 Python test_jira*.py PASS;3targeted Subtask additive/read-back PASS; Node predicate/conjunction/freshness PASS; Forge lint PASS; Jira12/12Boolean type-valid.
- Server source có25tool qua fresh stdio smoke; cached connection có thể vẫn catalog cũ. Chưa sửa global MCP config/restart app.
- A05 addCommentOnce=false; marker chống lặp theo event, không marker=delivery. Comment10012 do AutomationforJira, @Hiệp đúng, không xác minh inbox đã nhận/đọc.
- Chưa fullT01–T23, non-PM identity native, stress/race nhiều Task, atomic child scope, linkedBug/reviewer/Lead/BA, dữ liệu history cực dài hoặc code sản phẩm. Không ghi PASS giả hoặc điểm cá nhân từ mô phỏng.
- Literal backslash-n evidence parser còn hạn chế nhập liệu đã ghi nhận, chưa sửa ngoài hash đã duyệt.

## Rollback

Rule: khôi phục qag3-test vào trigger hoặc tắt rule liên quan, giữ actions/actor/project scope và toàn bộ lịch sử. Có thể khôi phục A02 To status[] theo preview phù hợp nếu cần nhưng sẽ tái tạo rủi ro event cũ.

App/gate: phục hồi manifest.before-subtask-history-split-2026-10-13.yml (2.19.0) trước; sau đó chỉ gỡ history gate bằng current-version preview được duyệt. Không gỡ một partner khi lighter acceptance đang deployed, không uninstall app hoặc xóa issue/comment.

Bằng chứng chính: jira-bot/automation-fullscope-2026-10-13.json; QAG3-A04-fullscope-success-2026-10-13.png; jira-bot/QAG3-A02-A05-enabled-fullscope-2026-10-13.png hiển thị đủ năm công tắc Enabled. Lịch sử các bản2.17–2.19fail được giữ trong JIRA_QA_RUNTIME_FIX_2026-10-13.md.

Primary sources: [Jira expression limits](https://developer.atlassian.com/cloud/jira/platform/jira-expressions/), [native automation triggers](https://support.atlassian.com/cloud-automation/docs/jira-automation-triggers/). Nguồn vendor giải thích cơ chế, không thay bằng chứng thực thi ở trên.

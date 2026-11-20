# Bot giám sát tiến độ Jira trên máy chủ dự án

## Hiện hành — PAUSED theo yêu cầu tắt nhanh ngày 15/10/2026

Đã PAUSED heartbeat bot-theo-d-i-ti-n-jira-qag3, giữ prompt/cadence/thread; Disable/Stop Windows task QLDAPM-Jira-MCP-Monitor và dừng đúng child Python có command tools/jira_monitor.py --interval3600. Giữ toàn bộ state/events/cursor/report và credential, không tác động Jira A01–A05 hoặc lịch khác. Chỉ bật lại khi người dùng yêu cầu; các mục ACTIVE bên dưới là lịch sử.

## Hiện hành — bot ACTIVE và báo cáo theo Epic Done ngày 15/10/2026

Theo yêu cầu mới, đã bật lại heartbeat `bot-theo-d-i-ti-n-jira-qag3` bằng automation tool, giữ nguyên cadence mỗi giờ phút15 và chat đích. Windows task `QLDAPM-Jira-MCP-Monitor` Enable/Start sau khi xác minh không có runner; không tạo lịch hoặc daemon trùng. Task Running; python.exe PID25440/Parent28316/CreationDateUTC07:16:17.225512, command tools/jira_monitor.py --interval3600. Event run189a271b-81f3-46dd-8b73-82619afac3cd/cycle1 hoàn tất07:17:36.938346UTC, source07:17:36.891192UTC/readComplete=true/335issue. CIM/process/event/source/freshness đã đối soát. Gemini DISABLED_CONFIG, không gọi collector/Gemini lần hai.

Báo cáo Word riêng `Danh_gia_thanh_vien_theo_Epic_Done_QAG3_2026-10-15.docx`: 7Epic WBS Done →34Task/170Subtask Done; mỗi thành viên34/34Subtask trong phạm vi7Epic. Không cộng đôi cấp công việc, loại6fixture; không gán tỷ lệ mẫu đã Done cho toàn dự án. Năm chiều hiệu suất vẫn INSUFFICIENT_EVIDENCE/overallScore=null; lịch/worklog/tiến độ là mô phỏng, không xếp hạng người thật. Đã render và xem đủ10trang. Nguồn và audit: jira-bot/EPIC_REVIEW_SOURCE_2026-10-15.json, EPIC_REVIEW_RUNTIME_2026-10-15.json, MONITOR_RESUME_EPIC_REVIEW_2026-10-15.json. Cursor cập nhật bằng apply_patch giữ metadata chống lặp; baseline collector không đổi.

Không sửa Jira/A01–A05/billing/credential hoặc continuation khác. Chưa thử lại appclosed/reboot/sleep/OAuth expiry; event local không chứng minh Codex scheduled execution. Mục PAUSED13/10 bên dưới là lịch sử, bị thay bởi yêu cầu resume15/10.

## Hiện hành — bot giám sát PAUSED, 13/10/2026

Theo yêu cầu mới nhất, heartbeat `bot-theo-d-i-ti-n-jira-qag3` đã PAUSED; Windows task `QLDAPM-Jira-MCP-Monitor` đã Disabled/Stopped. Child Python PID21772 được xác minh đúng script, Parent18492 và CreationDate trước khi dừng. CIM readback lúc `2026-10-13T04:48:41.7699852Z`: không còn runner/wrapper. Giữ nguyên state/events/report và không thay lịch continuation khác. A01–A05 vẫn Enabled trong Jira; tắt monitor không tắt Jira Automation. Mục ACTIVE dưới đây là lịch sử trước lần tạm dừng này. Audit: `jira-bot/MONITOR_PAUSE_2026-10-13T044841Z.json`.

## Hiện hành — bot giám sát ACTIVE và đánh giá thành viên riêng tư, 13/10/2026

User yêu cầu bật lại monitor và đánh giá công việc từng thành viên. Đã Enable/Start đúng Windows task QLDAPM-Jira-MCP-Monitor sau CIM0runner; heartbeat bot-theo-d-i-ti-n-jira-qag3 ACTIVE giữ mỗi giờ phút15/chatđích. Runner PID21772/parent18492/CreationDateUTC04:35:08.288059, run6d83a338-dd8f-4ba3-8e39-dc2493b6dd49/cycle1 complete04:36:22.036004UTC, state335issue/readComplete=true, GeminiDISABLED_CONFIG. Process/event/freshness đã đối soát; không suy Codex scheduled execution hoặc reboot proof.

Runner bổ sung memberAssessment trong cùng complete cycle: scope qag3-wbs329, loại6fixture; từng vai trò53Subtask/39Done/14NEW/0WIP=73,58% mô phỏng. PM53Task/11Epic báo riêng, không cộng đôi. Năm chiều thiếu evidence nên overallScore=null/INSUFFICIENT_EVIDENCE, không điểm giả/HR ranking, không rawPII sangGemini. Báo cáo local/chat riêng tư, chỉ notify meaningfulchange, khôngtimestamp-only. 11runner/108Jirasuite testsPASS. Không đổi Jira/billing/credential/lịchcontinuation khác. Lượt này chỉ bật lại monitor cũ, không tạo daemon hoặc lịch trùng. Audit/report: `jira-bot/MONITOR_RESUME_2026-10-13T043621Z.json`, `jira-bot/REPORT_MEMBERS_2026-10-13T043621Z.md`. Chưa nghiệm thu lại reboot/appclosed/sleep/OAuthexpiry hoặc nhiều giờ sauresume; các mụcPAUSED dưới là lịch sử.

## Latest observed classroom data — 11/10/2026

Continuation fully reconciled329QAG3issues and individually verified265SIMULATIONworklogs/384hours. Academic Task completion49/53=92.45%; role score assumptions publishedQAG3-299/comment10004, not real-person assessments or evidence of product/QA delivery. Full IDs/formula/inputs and unresolved migration are in JIRA_MIGRATION_READINESS_2026-10-11.md. Native worklog authoradmin; contributor role in notes is hypothetical. This does not enable the monitor, Gemini or automated scoring. Monitor remainsPAUSED; collector/runtime/baseline/rolloutschemas were not replaced. The PARTIAL429 paragraph below is historical, superseded for data reconciliation only; migration remainsNOTDONE.

## Current data boundary — classroom scenario, 11/10/2026

Owner explicitly authorised hypothetical progress/schedule in QAG3. Academic-scenario/qag3-simulation-labelled Done is simulated, not code/QA/release acceptance or personnel delivery evidence. The bulk scenario is PARTIAL under Jira429;300writescomplete/3metadata-only/26untouched, finalreadbacknotcomplete. Do not derive real individual scores, treat the intended49/53as observed completion or count this as workflow E2E. On any later user-approved monitor resume, label scenario metrics as simulated and reconcile current Jira data. Before/progress simulation JSON are NOT collector/runtime/rollout schemas; never overwrite state-QAG3.json, runnerstate or proof files with them. Monitor remains paused; this notice does not resume/change schedules. Audit JIRA_ACADEMIC_SIMULATION_2026-10-11.md.

Ngày thiết lập: 2026-10-09. Authority: [AGENTS.md](AGENTS.md). Bot theo dõi tiến độ dự án, không tự chấm/xếp hạng thành viên hoặc thay đổi Jira.

## 1. Thiết kế đã cấu hình

| Thành phần | Cấu hình / bằng chứng |
| --- | --- |
| Host | Máy Windows; heartbeat Codex và runner Python local riêng (mục9) |
| Jira | https://luimjiraqldapm.atlassian.net; QAG3/10002 |
| Kết nối | MCP Atlassian chính thức `atlassian`, OAuth đã kiểm tra identity/resources/project |
| Bot monitor | `bot-theo-d-i-ti-n-jira-qag3`, heartbeat **ACTIVE** theo yêu cầu bật lại15/10/2026; Windows task Running, process/event complete hiện hành đã xác minh; cadence mỗi giờ phút15/chat riêng tư |
| Tiếp tục thiết lập | `ti-p-t-c-jira-qag3-sau-reset-quota`, ACTIVE, hằng ngày 08:25 (+07); cập nhật theo quota khi thật sự bị chặn |
| Đích thông báo | Chat hiện tại; riêng tư; không thông báo lặp khi không có biến động/hành động mới |
| Dữ liệu local | [jira-bot/state-QAG3.json](jira-bot/state-QAG3.json), collector [tools/jira_bot.py](tools/jira_bot.py), báo cáo dưới jira-bot |
| Docker/tunnel/API key riêng | Không tạo; không cần inbound endpoint cho MCP outbound hiện tại |

Hai lịch được tạo/cập nhật bằng `mcp__codex_app__automation_update`, không sửa automation.toml bằng tay. Bot monitor khác lịch tiếp tục setup: hoàn tất setup thì dừng lịch tiếp tục; monitor giữ chạy để phục vụ yêu cầu giám sát định kỳ, trừ khi người dùng yêu cầu dừng. Đây là mặc định đã hỏi lại scope/cadence; cập nhật nếu người dùng chọn khác, không tạo lịch trùng.

Máy phải bật, không sleep, OAuth còn hiệu lực và thư mục dự án phải truy cập được. Codex heartbeat cần desktop chạy; resident runner có Windows at-logon supervisor ở mục10, nhưng chưa thử đóng desktop hoặc reboot. Không đổi power policy toàn máy hoặc mở port; chưa bảo đảm24/7. [OpenAI — Scheduled tasks](https://learn.chatgpt.com/docs/automations?surface=app).

## 2. Thu dữ liệu an toàn mỗi lượt

1. Đọc AGENTS/runbook/snapshot gần nhất; kiểm tra quota Codex thực. Quota chặn thì không mua hoặc sử dụng reset credit; dùng automation tool điều chỉnh sau resetsAt khi cần. Auth hỏng thì báo người dùng OAuth, không lấy cookie browser.
2. Xác minh identity/resources và listJiraProjects QAG3. Site/cloudId không khớp thì dừng. Không tự chuyển qua KAN/SAM1 hoặc mở rộng project.
3. Chạy collector ở mục 7: query `project = QAG3 ORDER BY key ASC`, field tối thiểu summary, issuetype, status, assignee, duedate, updated, parent, labels, **view full**. Compact có thể bỏ field ngay cả khi đã yêu cầu; không dùng nó cho snapshot này. Đọc hết nextPageToken tới isLast; mất trang/lỗi thì UNKNOWN, giữ last successful snapshot. Field tùy chọn bị bỏ khỏi response là UNKNOWN, khác với null trả thật.
4. Metadata project statuses, board/sprint dùng purpose-built operation. Discover schema hiện tại. Changelog chỉ đọc khi cần chứng minh một nhận định; không quét toàn bộ lịch sử và worklogs mỗi giờ khi không cần.
5. So sánh current snapshot với lần đọc thành công trước. Cửa sổ 24 giờ là mô tả biến động cập nhật, không chứng minh lịch sử hoàn thành nếu chỉ có field updated. Ghi nguồn issue keys và timestamp, phân biệt tình trạng dữ liệu với tiến độ code.
6. Lưu snapshot bằng apply_patch sau khi toàn bộ đọc thành công. Chỉ thay state do bot quản lý; report có tên timestamp UTC duy nhất, không ghi đè report/snapshot lịch sử hoặc tài liệu người dùng. Không token, cookie, password, private message hay dữ liệu không cần thiết.

Snapshot current-state qua nhiều request không nguyên tử. Dữ liệu live có thể thay đổi giữa các trang; khi phục vụ quyết định quan trọng phải đối soát, không gọi snapshot này là hard gate/committed Sprint baseline.

## 3. Cách đánh giá tiến độ

- Tách thống kê Epic, Task/Story và Subtask. Completion của phạm vi chức năng = Task/Story trong status category Done, không có status CANCELLED/CANCELED / tổng Task/Story thuộc phạm vi hiện tại. Việc hủy được đếm riêng, không tự xóa khỏi mẫu số. Không cộng Task với các Subtask của nó. Tổng bằng 0 → **Chưa có phạm vi**, completion=null.
- Dùng category trả thật, không hardcode mọi trạng thái DONE/CANCELLED là hoàn thành; cancellation tách riêng nếu workflow có. Item demo/test đánh dấu riêng trước khi loại khỏi mẫu số, không tùy ý loại việc chậm.
- Nêu WIP, mới thêm/bớt/chuyển Parent, thiếu assignee và deadline quá hạn khi có ngày thật. Blocker/bug cần dữ liệu đã đọc, không mặc định absence là không có lỗi.
- Thiếu mục tiêu/ngày Sprint/capacity/baseline thì **không đủ dữ liệu kết luận đúng hạn/trễ hạn**. Jira Done chưa chứng minh AC, test, release hoặc code hoàn tất.
- Thay đổi phạm vi là thay đổi mẫu số, không tự trừ điểm cá nhân. Không gán estimate giả/worklog thật; không xếp hạng HR từ ticket/point counts.
- Chỉ thông báo khi có thay đổi đáng kể, blocker mới, kết quả hoàn tất có evidence, lỗi mới hoặc cần người dùng xử lý. Không ping rủi ro/bootstrap HTTP400 cũ mỗi giờ.

## 4. Mẫu báo cáo riêng tư

```text
Project / site / snapshot UTC và +07 / route MCP
Read completeness: COMPLETE / PARTIAL / FAILED
Phạm vi: Epic / Task-Story / Subtask; functional Done/total hoặc Chưa có phạm vi
Biến động từ baseline: thêm/bớt/chuyển/Done/reopen — kèm issue keys nếu có
WIP / assignee chưa có / deadline thật / blocker có bằng chứng
Đánh giá PM: tình trạng và lý do; UNKNOWN nếu dữ liệu thiếu
Hành động đề xuất: owner/quyết định cần thiết, chưa tự mutate Jira
Giới hạn: dữ liệu chưa đọc, lịch/scope/capacity/test chưa biết
```

Xuất bản Confluence hoặc Artifacts là lựa chọn riêng, chưa được duyệt cho bot. Quyền upload năm bootstrap không bao gồm báo cáo/state mới. Không tự gửi comment/email/thông báo nhân sự.

## 5. Baseline đọc thử và kiểm thử

Đọc thủ công qua MCP lúc khoảng **04:10:58 ngày 2026-10-09 (+07)**: QAG3/10002 classic, issues=[], isLast=true. Epic/Task/Sub-task cùng dùng 3 status mặc định. Đã lưu [báo cáo baseline](jira-bot/BASELINE_2026-10-09.md).

| Kiểm tra | Kết quả |
| --- | --- |
| OAuth đúng account/site và smoke project | PASS, gọi MCP thực |
| JQL baseline, hết pagination | PASS, issues=[]/isLast=true |
| Project rỗng không coi hoàn thành 100% | PASS, completion=null |
| Tạo monitor / cập nhật continuation | PASS, tool trả ACTIVE và đúng automationId |
| State JSON/invariant và link local/config cadence/thread | PASS, kiểm tra PowerShell thực chạy; files nguồn WBS/Word không bị sửa |
| Scheduled run tự thực thi | NOT VERIFIED — chưa có run handle/audit |
| Live paginated non-empty sample / concurrency / auth recovery / quota recovery | NOT RUN; pagination/error cases synthetic đã chạy ở mục 7 |
| Quyền ghi Jira/admin / 23 workflow E2E | NOT RUN trong phiên bot |

Không coi baseline thủ công là scheduled run. Chưa thử pause/resume máy hoặc đo tiêu thụ quota một vòng bot có dữ liệu. Đổi tần suất nếu quota thực không phù hợp; không mua gói để duy trì bot.

## 6. Kiểm thử client local chạy nền — 04:21 ngày 2026-10-09

Đã chạy helper có sẵn `tools/jira_mcp.py` bằng Python bundled, cwd authoritative. Helper tạo process Codex app-server riêng, sử dụng credential store và gọi **MCP chính thức**, không gọi model/REST trực tiếp hoặc sao chép token. Bốn lần gọi đều exit0/isError=false: atlassianUserInfo đúng account; getAccessibleAtlassianResources đúng site/cloudId; executeRead(listJiraProjects) trả QAG3/10002 classic/isLast; searchJiraIssuesUsingJql trả issues=[]/isLast=true. Process của từng lệnh đã kết thúc; không phải daemon/live job đang chờ.

Điều này chứng minh client nền có thể thu dữ liệu Jira trên host hiện tại. **Chưa kiểm thử khi đóng Codex desktop, chưa scheduler run, chưa loop định kỳ độc lập hoặc recovery/AI report có dữ liệu.** Không tự đóng app hoặc đổi startup/power policy để thử.

Root config MCP local có URL official v2, không khai báo enabled_tools/disabled_tools; project authoritative không có `.codex/config.toml`. Runtime kết nối thành công nên không cần cài lại hoặc sửa config root để thử chữa admin thiếu công cụ. Chưa đối soát mọi managed/effective policy. Ý nghĩa filter tham khảo [OpenAI — Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference).

Đọc thread hiện tại chỉ thấy goal turn inProgress, không có scheduled-run handle; state JSON chưa được thay bởi bằng chứng chạy tự động. Kiểm tra database state local ở chế độ query-only không thấy bảng automation/job; không suy ra scheduler thất bại hoặc dừng từ việc này. Chỉ Scheduled/run evidence hoặc process/job handle thực mới đủ chứng minh execution.

## 7. Collector đã triển khai và nối lịch — 04:33 ngày 2026-10-09

Collector read-only dùng Python standard library và helper MCP hiện có, không cài dependency, model/API key, daemon, container hoặc tunnel mới:

```powershell
& 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\AI project\QLDAPM chat\tools\jira_bot.py'
```

Collector xác minh account/site/QAG3 và metadata issue type trước JQL; full view, hết pagination, từ chối key ngoài QAG3/trùng key, trạng thái/type không phân loại được, updated không có timezone và lỗi MCP lồng nhau. Chỉ stdout JSON, exit 0/readComplete=true khi thu xong; lỗi exit 1/readComplete=false, không tự ghi đè baseline. Nó không tự biết scheduled trigger nên luôn trả scheduledExecutionVerified=false. AI trong lượt Codex dùng snapshot để nhận định; collector không tự chấm nhân sự.

Live command exit 0: snapshot **2026-10-08T21:33:20.368379+00:00** (04:33:20 +07), đúng QAG3/10002, issues=[], isLast=true, completion=null. Lưu riêng [smoke JSON](jira-bot/COLLECTOR_SMOKE_2026-10-09.json), giữ state/baseline cũ. Đây là manual smoke, không scheduled-run proof. KAN-68 chỉ được đọc trước đó để đối chiếu compact/full response contract; bot không giám sát hoặc ghi KAN.

```powershell
# Cwd: D:\AI project\QLDAPM chat
& 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -p test_jira_bot.py -v
```

17 tests PASS: empty scope, không cộng đôi, tách hủy, UNKNOWN/null, overdue theo +07/ngày đến hạn, full fields/timestamp, parser/error nested, pagination thiếu/lặp/foreign/duplicate/failed second page, read-tool boundary, identity/site/project mismatch. Fixture synthetic; không tạo issue giả hoặc thay 23 workflow E2E.

Đã cập nhật **đúng lịch monitor cũ** qua automation_update, giữ ACTIVE/mỗi giờ phút 15/thread; prompt gọi collector sau kiểm tra quota, giữ baseline khi lỗi, không thông báo chỉ vì timestamp mới, giữ metadata chống lặp và chỉ tạo report khi có thay đổi hữu ích. [OpenAI — Schedule a task inside a chat](https://learn.chatgpt.com/docs/automations#schedule-a-task-inside-a-chat). Không tạo lịch thứ ba hoặc sửa TOML bằng tay.

Giới hạn còn lại: live QAG3 rỗng, chưa có run ID/trigger/audit chứng minh lượt scheduled; chưa thử đóng app, phục hồi OAuth/quota, concurrency hoặc thu nhiều trang dữ liệu thật. Cancellation hiện nhận từ status name, chưa đọc resolution; metrics không đại diện mọi work item type hoặc mọi project/site. Scheduled monitor cần host/app chạy và dùng quota Codex; collector không mở rộng quyền admin. Không có inbound server cần công khai, chưa thay power/startup policy.

## 8. Gemini optional — tích hợp, chưa live inference

Objective mới cho phép Gemini hỗ trợ bot. [tools/jira_gemini.py](tools/jira_gemini.py) dùng Python standard library, lấy snapshot từ collector hoặc `--snapshot` để tránh đọc Jira hai lần. Jira vẫn chỉ qua MCP; request Google chỉ làm inference, không phải thay thế Jira MCP. Không thêm dependency, SDK hoặc public endpoint.

**Không dùng key đã gửi trong chat.** Cần tạo key mới, thu hồi key cũ và kiểm tra usage. Đặt key mới vào biến môi trường `GEMINI_API_KEY` trên máy, không gửi lại trong chat/Markdown/code. Windows: tìm Environment Variables → User variables → New; sau đó mở terminal mới để nạp biến. Không chụp/in phần Value. [Google — API key security và environment variables](https://ai.google.dev/gemini-api/docs/api-key).

Chỉ đặt `GEMINI_FREE_TIER_CONFIRMED=1` sau khi người dùng kiểm tra đúng project của key trong AI Studio có Plan Free, chưa billing. Flag là xác nhận của operator, **không phải xác minh billing bằng API hoặc bảo đảm chi phí vĩnh viễn**. Không bật billing, top-up, trial hoặc fallback paid. Model cố định `gemini-3.1-flash-lite` có Free Tier input/output trong tài liệu; quyền/quota/tier của key thực vẫn UNKNOWN. [Pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite), [Billing](https://ai.google.dev/gemini-api/docs/billing).

Sau khi điều kiện trên đạt, trên snapshot complete vừa thu ở lượt hiện tại:

```powershell
& 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\AI project\QLDAPM chat\tools\jira_gemini.py' --snapshot 'D:\AI project\QLDAPM chat\jira-bot\state-QAG3.json'
```

Adapter chỉ gửi số tổng Task/Done/hủy, số WIP/overdue/known-unassigned/unknown-field và cờ thiếu baseline. Không gửi site/cloudId/issue keys, tên/email/accountId, summary/labels/descriptions/comments/worklogs hoặc đánh giá cá nhân. Free Tier có data-use/human-review; không gửi dữ liệu confidential/personal. Xem [nghiên cứu Free Tier](JIRA_GEMINI_FREE_RESEARCH.md).

REST `generateContent` của Google là API legacy còn được tài liệu mô tả; dùng `x-goog-api-key` header, JSON structured `generationConfig.responseFormat.text`, timeout45s, output cap2048 tokens/response64KiB. Chỉ nhận một candidate STOP, kiểm tra các field/types/kích thước và không echo key. Không retry tự động khi429/401/timeout, không thực thi nội dung model thành Jira writes. [Google — structured output REST](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).

Output `assessmentComplete=true`, `aiDraft=true` chỉ sau parse/validation; nội dung AI vẫn là draft cần đối chiếu số liệu, schema không bảo đảm đúng nghiệp vụ. Baseline lịch/capacity/AC chưa thu thì UNKNOWN, không kết luận trễ Sprint hoặc chấm người. Adapter không có function/tool calling hoặc khả năng admin.

**Validation:** 22 tests PASS (17 collector + 5 Gemini mock): auth header không URL, minimal payload không PII, missing secret/unconfirmed billing/partial-foreign-inconsistent snapshot không gửi request, lỗi sanitized/no retry, output blocked/truncated/schema/key echo bị từ chối. CLI thực chạy trên môi trường chưa có key/flag trả exit1/assessmentComplete=false ngay, không gọi Google hoặc Jira trong lệnh đó. Chưa live Gemini authentication/inference/429 recovery hoặc model availability.

Hai heartbeat cũ đã cập nhật qua automation tool, giữ cadence/thread; monitor chỉ cân nhắc Gemini sau snapshot thành công và khi có biến động đáng kể, không gọi khi QAG3 rỗng hoặc chỉ timestamp đổi. Thiếu điều kiện thì giữ Gemini tắt, Codex vẫn có thể nhận định local. **Chưa có resident Gemini service/Windows startup hoặc bot độc lập khi desktop đóng.** Host độc lập, auto-recovery, live scheduled execution và full Jira capability vẫn là việc chưa nghiệm thu, không được coi adapter/tests là hoàn tất objective.

## 9. Runner local — đã chạy process và kiểm thử chu kỳ

[tools/jira_monitor.py](tools/jira_monitor.py) thu qua collector MCP theo chu kỳ, state riêng `jira-bot/runtime/state-QAG3.json`, events JSONL theo ngày UTC. Không viết vào baseline Codex, Jira/KAN hoặc snapshot Sprint đã chốt. State runtime giữ field theo dõi key/type/category/statusId/parent/assignee/due; không giữ summary/labels/raw text. AccountId chỉ ở state local, không log event hoặc gửi Gemini. Khi thu lỗi giữ state thành công trước và ghi event lỗi sanitized; đọc lại ở chu kỳ kế tiếp, không spam retry bên trong chu kỳ.

Single-runner lock Windows bằng msvcrt giữ bởi process, không dựa PID/lock file cũ. State ghi temporary cùng thư mục rồi os.replace; lỗi replacement giữ file cũ. Gemini chỉ bật khi key/Free Tier guards đạt và scope không rỗng; fingerprint không đổi không gọi lại draft đã thành công. AI lỗi/truncated/incomplete giữ draft cũ với source timestamp riêng; không gán draft đó cho dữ liệu mới. Event `scopeChanged` hiện nghĩa fingerprint dữ liệu thay đổi (có cả status/assignee/due), **không tự chứng minh phạm vi thêm/bớt**; muốn kết luận scope phải đối chiếu issue keys/Parent. Không dựa timestamp/ordinary text edit để thông báo.

Kiểm thử suite **32 PASS**: 18 collector + 5 Gemini + 9 runner. Có test regression draft chưa hoàn chỉnh làm mất draft cũ: đã thấy FAIL trước fix và PASS sau fix. Gemini/Google secrets được lọc khỏi env của helper MCP con; không copy credential. Sources: [Python msvcrt locking](https://docs.python.org/3.12/library/msvcrt.html), [os.replace](https://docs.python.org/3.12/library/os.html#os.replace).

### 9.1 Live bounded smoke

Lệnh `jira_monitor.py --interval 60 --cycles 2`: session5764, PID18556, runId `282e628e-0d34-4c81-85ab-1a49c2f40776`. Hai event complete lần lượt UTC21:46:26.801618/21:47:26.580614 ngày08/10/2026, cùng runId/PID, QAG3 rỗng; lần2 data fingerprint không đổi. Process đã terminal exit0, CIM sau đó không còn PID phù hợp. Lệnh thứ hai trong lúc process còn sống bị khóa, exit1 PermissionError trước thu MCP. Đây là chu kỳ loop local thật, **không Codex Scheduled run**. Events ở runtime/events-2026-10-08.jsonl.

### 9.2 Resident process trước cutover sang supervisor — lịch sử

Sau smoke, Start-Process -WindowStyle Hidden chạy đúng script trên host, interval3600 giây; không tạo thêm Codex/Windows scheduler. PID19532, start04:48:05 +07 ngày09/10/2026, runId `08753158-3fa5-4c38-94ab-a3e61f9b82bb`. Đã đọc lại CIM và event đầu tiên UTC21:48:23.724172 ngày08/10: COLLECTED/readComplete=true, QAG3 rỗng, geminiStatus=DISABLED_CONFIG. Đây là snapshot chứng minh process đang sống và lần đọc đầu, chưa chứng minh đã chạy đủ vòng hourly/reboot hoặc khi đóng desktop.

Nếu cần chạy lại, **kiểm tra không có process đúng script còn sống trước**; không chạy trùng chỉ vì output stale. Lệnh foreground:

```powershell
& 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\AI project\QLDAPM chat\tools\jira_monitor.py' --interval 3600
```

Kiểm tra thực: CIM process đúng python/script/commandline và PID/CreationDate khớp latest event runId/cycle; freshness tối đa interval+120s. File/PID cũ một mình không đủ. Resident stdout/stderr dưới runtime; event log vẫn append. Dừng foreground bằng Ctrl+C; với background chỉ Stop-Process đúng PID sau khi đối chiếu commandline, không kill toàn bộ Python/Codex. Không xóa state/history khi dừng.

Monitor heartbeat cũ đã cập nhật bằng automation_update: khi runner/process/latest event được xác minh và fresh, dùng metrics/events/draft của runner, không chạy lại collector/Gemini; cursor Codex riêng nếu cần. Runtime schema không phải input --snapshot của adapter. Nếu process sống nhưng lỗi/stale, UNKNOWN và theo chu kỳ, không restart do observation timeout; fallback collector chỉ khi xác minh process terminal/missing. [OpenAI scheduled tasks](https://learn.chatgpt.com/docs/automations#schedule-a-task-inside-a-chat).

**Giới hạn:** chưa đăng ký Windows service/startup/reboot supervisor, thay power policy hoặc đóng desktop thử. Process có thể dừng khi reboot/logoff/máy sleep; cần thiết lập/vận hành và kiểm thử thêm trước khi hứa24/7. Helper timeout hiện theo từng response wait, chưa strict total deadline; disk/log I/O lỗi có thể làm runner stop. Gemini lỗi được thử lại tối đa một lần ở chu kỳ sau khi fingerprint chưa có draft thành công, không bảo đảm provider quota-reset recovery. Log theo ngày chưa retention tự xóa. Không có HTTP/API inbound hoặc public tunnel; full Jira admin, Gemini live inference và các gates vẫn chưa nghiệm thu.

## 10. Windows supervisor — cập nhật hiện tại

Task `\QLDAPM-Jira-MCP-Monitor` đã đăng ký và đọc lại: logon LUIM\\LUIM, Interactive/Limited, IgnoreNew, không lưu password, execution limit PT0S. Không thay execution/power policy; chỉ cho phép riêng task chạy trên battery. Native RestartOnFailure đã gỡ sau test không relaunch; wrapper tự giới hạn tối đa3 retry/cách60 giây cho child exit lỗi (một lần chạy ban đầu +3 retry). Lỗi launch/path/storage dừng ngay. [Microsoft — task principal](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskprincipal), [task settings](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset).

Action chạy PowerShell Hidden/NoProfile/NonInteractive và [Start-JiraMonitor.ps1](tools/Start-JiraMonitor.ps1). Script chờ child Python Hidden để chuyển exit code cho scheduler; hourly loop không đổi. Log supervisor.stdout/stderr có thể được ghi lại sau restart; daily events JSONL là audit giữ lịch sử. Không service SYSTEM, public port/tunnel hoặc Docker mới.

Cutover: PID19532 được xác minh đúng command/CreationDate, không có read child, rồi dừng. Task thực Running lúc04:58:16+07 → wrapper24036 → Python28104; event readComplete=true QAG3 lúc04:58:46+07, runId119c0d39-b677-4753-9d69-7d1a27f6f14e. Suite32 PASS + PowerShell parser PASS. Gemini DISABLED_CONFIG. Đây là host scheduler execution thực, **không Codex heartbeat scheduled-run proof**.

Native recovery test FAIL: dừng đúng Python28104 lúc04:59:25+07 sau complete/no active helper; task Ready/LastTaskResult4294967295, wrapper và Python không còn; tới08:26 vẫn không retry. Không coi cài setting là recovery proof. Đã thay bằng loop bounded trong wrapper và loại native RestartOnFailure để tránh retry nhân lên; không nguyên nhân giả định hoặc đổi quyền/policy.

Lúc08:26:48 khởi động lại đúng task terminal, wrapper25404 → Python24492. Event complete QAG3 UTC01:27:19.792183 ngày09/10, runId1a8a8e17-8586-4dd7-9f7a-07fea0a0b452. Suite32PASS +4 PowerShell self-check PASS (success, one retry recovery, retry exhaustion, missing path). Harness đã sửa truyền LASTEXITCODE; không Jira/Google request trong self-check.

Recovery wrapper thực **PASS**: dừng đúng Python24492 lúc08:28:32.497513+07 sau complete/no helper, giữ wrapper25404 sống. Không start tay; cùng wrapper tự tạo Python11636 lúc08:29:32.762736+07 (~60.27s), runId1118e998-83e2-40f9-aa48-b94b891f0e3c, event MCP complete UTC01:30:02.863902 ngày09/10. TaskRunning, stderr0 byte; fresh event/PID/command/parent/CreationDate đã đối chiếu. Không dùng lock/file một mình. Xem [báo cáo riêng tư](jira-bot/REPORT_RUNTIME_2026-10-09T013002Z.md).

Cursor Codex riêng `jira-bot/runtime-cursor.json` lưu run/cycle/fingerprint/lastNotifiedCondition và condition baseline cũ, không thay schema baseline hoặc state runner. Cursor/report runtime được gitignore; không đánh giá lại/notify scope rỗng khi chỉ timestamp đổi. Nếu đọc cursor lỗi/owner sai, không ghi đè.

Xem trạng thái bằng Get-ScheduledTask/Get-ScheduledTaskInfo và CIM đúng script, so với latest events/runId/CreationDate/freshness. Muốn dừng có chủ đích: Disable-ScheduledTask đúng tên trước rồi Stop-ScheduledTask; đối chiếu và dừng đúng child nếu còn sống. Muốn chạy lại: xác minh không có child thủ công, Enable-ScheduledTask rồi Start-ScheduledTask. Không xóa state/events hoặc kill toàn bộ Python/Codex.

**Chưa kiểm thử:** đăng nhập lại/reboot/đóng desktop, OAuth expiry, máy sleep hoặc lỗi hung helper. Interactive chỉ hoạt động trong phiên đăng nhập; máy off/asleep/logoff không phải host24/7. Wrapper retry giới hạn3 lần, không tự sửa mất credential/disk; hết retry task dừng, cần operator xử lý. Secret environment mới chỉ được nạp khi process khởi động mới; Gemini chưa bật/verified Free Tier. Full admin/all-data Jira và workflow gates vẫn thiếu.

## 11. Giám sát tạm dừng theo người dùng — 2026-10-09 15:20 +07 (hiện hành)

User yêu cầu “tạm huỷ cái scheduled task đi” sau heartbeat giám sát. Tạm dừng bot QAG3, không xóa lịch hoặc dữ liệu: automation_update đúng id monitor giữ prompt/cadence/thread, statusPAUSED; automation.toml đọc lại PAUSED, không sửa TOML bằng tay. Windows task `\QLDAPM-Jira-MCP-Monitor` đã Disable rồi Stop; readback Disabled/Enabledfalse.

Stop-ScheduledTask đã dừng wrapper25404 nhưng child11636 còn sống. CIM đối chiếu python.exe/đúng script/interval3600/Parent25404/CreationDate2026-10-09T01:29:32.762736Z; child chỉ conhost, không collector đang chạy. Đã Stop-Process đúng11636; kiểm tra lại **0 runner/wrapper** lúc2026-10-09 08:20:36 UTC. Không kill Python/Codex khác, không thu Jira hoặc gọi Gemini trong lượt dừng.

Giữ state/events/cursor/reports/credential/WBS và lịch đã lưu. Lịch riêng `ti-p-t-c-jira-qag3-sau-reset-quota` vẫn ACTIVE, không nằm trong yêu cầu tạm dừng monitor. Không tự khởi động lại monitor từ continuation hoặc vì process thiếu; chỉ resume sau yêu cầu mới của người dùng. Các mô tả Running/ACTIVE ở mục lịch sử không còn là trạng thái hiện hành. Nếu resume, kiểm tra không có runner trùng, bật đúng Windows task và đúng Codex monitor; giữ các Free Tier/safety guards.

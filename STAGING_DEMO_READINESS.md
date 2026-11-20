# Staging demo readiness — 21/10/2026

**Kết luận: ĐỦ ĐIỀU KIỆN DEMO CHỈ ĐỌC CÓ GIỚI HẠN — READY_FOR_READ_ONLY_DEMO_WITH_LIMITS.** PM đã enroll TOTP mới và đăng nhập thành công; Assistant, Control Center, Second Brain search, Monitor, Kanban, Backlog/Sprint và Gantt WBS đã được kiểm tra trực tiếp. Giữ nguyên runtime Staging làm phương án dự phòng.

Snapshot: **14:20–14:33**, kiểm tra backend bổ sung đến **14:36**, UAT trình duyệt hoàn tất **14:53**, Asia/Bangkok (UTC+07). Không restart, rebuild, đổi Quick Tunnel hoặc đồng bộ Main sang Staging. Ngoại lệ duy nhất do audit thực hiện là reset m ật khẩu/TOTP của PM theo phê duyệt mới của Owner sau lỗi 422.

PASS chỉ áp dụng cho phạm vi bằng chứng ghi rõ; PARTIAL là còn thiếu kiểm chứng hoặc có giới hạn; FAIL là hành vi cần demo đang lỗi/thiếu dữ liệu. Lịch sử model thành công không chứng minh một lượt gọi model mới sẽ thành công.

## 1. Địa chỉ và danh tính

- URL hiện tại: https://deployment-mae-promote-python.trycloudflare.com.
- Trang lấy lại URL hiện hành: http://localhost:18090.
- Staging: `qldapm-local`, **Project 3**; PM là **login pm / User 7**.
- Web: `127.0.0.1:18091`; Gateway: `127.0.0.1:18092`.
- n8n editor: http://localhost:5678; cần operator owner riêng.
- Main độc lập: Web8088/Gateway8090, **Project 5**, PM là **ba-pm / User 19**. Không dùng lẫn mappings/tài khoản giữa hai môi trường.

## 2. Ma trận PASS / PARTIAL / FAIL

| Hạng mục | Kết quả | Bằng chứng và giới hạn |
|---|---|---|
| Docker Staging | **PASS** | 7 containers running/healthy, restart_count=0, không OOM; ID/image/start/ports/networks/mounts trước–sau khớp. |
| Web tại 18091 | **PASS** | `/health_checks/default` trả 200 trước/sau; PM Native API đọc đúng Project3 và 335 Work Packages. |
| Duyệt UI trực tiếp localhost:18091 | **PARTIAL** | Edge gặp ERR_SSL_PROTOCOL_ERROR khi chuyển sang HTTPS. Health HTTP vẫn tốt; dùng URL tunnel. Chưa có UI offline được nghiệm thu. |
| AI Gateway tại 18092 | **PASS** | `/health` trả 200, native mode; PM7 identity/role thật PASS, API credential vẫn dùng được sau reset. |
| Ports và network | **PASS** | Chỉ publish loopback. DB không publish; Stage và Main dùng network riêng. Quick Tunnel chỉ công bố Web. |
| Quick Tunnel từ Internet | **PARTIAL** | HTTPS qua Cloudflare từ máy này trả 200 cho health/login; Edge mở form thật. Hai lần fetch từ công cụ web từ xa không truy cập được. Chưa xác nhận bằng thiết bị/mạng độc lập. |
| PM browser login | **PASS** | Owner đăng nhập/enroll native thành công; UI hiện QLDAPM PM, đọc được dự án private; device32/User7 active. Không đọc/lưu QR hoặc seed. |
| AI Assistant / Control Center UI | **PASS** | PM thật thấy Gateway ok/OpenProject authenticated,335WP, Gemini READY cached,6agentdefinitions IDLE và9run của mình. Không tạo run mới. |
| Assistant sau POST tìm Second Brain | **PARTIAL** | Search/citation đúng nhưng dashboard tóm tắt/kết nối phía trên trống do bản Core cũ chưa có sửa nạp context sau POST của Main. Mở lại URL Assistant bằng GET phục hồi đầy đủ. Không diễn giải thành gateway outage. |
| Agent Registry | **PASS** | Import registry từ image serving có supervisor, pm, ba, dev, qa, reviewer. Registry là năng lực cấu hình, không phải các agent đang chạy. |
| Supervisor local | **PARTIAL** | Implementation deterministic thật, không gọi model. Pure planner Staging chọn BA→Reviewer cho câu yêu cầu BA+QA; chưa có sửa chọn nhiều specialist của Main. |
| Gemini multi-agent đã lưu | **PASS — lịch sử** | PM run38fdb479… COMPLETED, plan BA/DEV/QA/Reviewer; Supervisor/BA/DEV/QA có LIVE_SUCCESS và usage provider thật. Không phải mock-only. |
| Gemini live cho một lượt demo mới | **PARTIAL** | Policy hợp lệ, cached proof khớp, không active circuit, local reservations hôm nay0. Không gọi Google mới nên chưa xác minh kết nối/quota provider hiện tại. |
| AI history / Execution Monitor | **PARTIAL** | UI tải run38fdb479… COMPLETED/LIVE_GEMINI,6node,4generation/27462tokens, BA detail và16mốc từ receipts cũ. execution_events=0: thiếu telemetry riêng; không trình bày như vừa chạy live. |
| Second Brain storage / FTS | **PASS** | knowledge.sqlite thật, quick_check=ok,5documents/3chunks; truy vấn FTS AUTH trả1hit. Runtime này không dùng PostgreSQL/pgvector hoặc embedding API. |
| Second Brain nghiệp vụ / UI | **PASS — tìm kiếm chỉ đọc** | PM tìm AUTH trên UI được1kết quả còn quyền, citationWP38/lockVersion1 khớpNative. Index chỉ có1native document nghiệp vụ; không kiểm ingestion/deindex mới. |
| n8n service / execution | **PASS** | DailyBrief và error-notice active; manual-status inactive để chạy thủ công. Execution37 DailyBrief success lúc13:07:43 hôm nay, execution36 success09:00. Không chạy workflow mới. |
| n8n editor authenticated | **PARTIAL** | Browser tới form sign-in; chưa có owner session được kiểm chứng. PM OpenProject không mặc nhiên có quyền quản trị n8n. |
| Daily Brief của PM | **PASS** | Ngày21/10, actor7/project3 READY. Actor6/8/9 cũng READY trong mẫu; actor5/stage-owner DENIED, không dùng admin thay business actor. |
| Work Packages | **PASS** |372 toàn instance; Project3 có335 =11Epic+54Task+270Subtask. PM API đọc335. Không xóa6mục dư để ép bằng329nguồn/Main. |
| Gantt cấu trúc WBS | **PARTIAL** | Trang Gantt thật tải bảng Epic/Task/Subtask, có cột ngày nhưng giá trị trống. Module/query37 tồn tại. Demo được cây WBS, chưa demo lịch dự án có ngày. |
| Gantt timeline có lịch của QLDAPM | **FAIL** |0/335mục có start/due. Không sửa dữ liệu để làm đẹp demo. DemoProject1 có14mục có ngày nhưng là dữ liệu mẫu khác dự án. |
| Kanban / Boards | **PARTIAL** | UI liệt kê7Boards, có4bảng chuẩn19–22. Board19 tải7cột và250card IDs trong DOM;335WP vẫn có trongNative. Chưa kiểm toàn bộcard/phân trang hoặc3board còn lại; không drag. |
| Sprint | **PARTIAL** | UI Backlog17/Sprints318,5SprintS1–S5; Native counts60/66/54/90/48. Đều planning, datesNULL, Version assignments0. Không có lịch7Sprint củaMain. |
| Tài khoản demo | **PARTIAL** | PM7 đã login và device32active sau reset. BE8 códeviceactive tại snapshot. BA6/FE9/QA10 chưa cóTOTPactive; chưa login lại các role còn lại. |
| Backup / recovery | **PARTIAL** | Container backup healthy; đã tạo PG custom dump private trước reset. Chưa diễn tập restore/restart mới; health không chứng minh restore PASS. |
| Isolation trong lúc Main nâng cấp | **PASS — cửa sổ audit** |7containers, URL, fingerprints nghiệp vụ và counters AI Staging giữ nguyên trong lúc Main có thay đổi lịch thực. Không phải bảo đảm uptime vô hạn. |

## 3. Containers và tài nguyên

Tất cả7containers có policy `unless-stopped`, healthy, started khoảng13:06:47+07 ngày21/10. Không restart do audit.

| Container trong qldapm-ai-stage | Image prefix | Ports host | Network |
|---|---|---|---|
| staging-web |79a90c208372|127.0.0.1:18091→8080|stage, stage-front|
| staging-gateway |456c38f6a9a9|127.0.0.1:18092→8090|stage-front, automation|
| db |2d2b8998d310|không publish|stage|
| quick-tunnel |a80f54e29918|không publish|stage-front|
| n8n |dd580fe1ab6e|qua editor|automation|
| n8n-editor |d8542f48d34a|127.0.0.1:5678,18090|automation, editor|
| local-backup |9713d54aad00|không publish|stage|

`radmin-proxy` stopped từ trước, không thuộc đường truy cập Quick Tunnel hiện hành. Các clone/rollback stopped không được khởi động chỉ để kiểm tra.

Docker có16CPU/11.54GiB RAM. Một snapshot ghi n8n dùng khoảng462/512MiB; clone Core khoảng1.44GiB/3GiB và~100%CPU. Đây không phải load test. Cần tránh build/test nặng và dùng Gemini Main đồng thời trong giờ demo.

## 4. Phần AI thật và nâng cấp còn thiếu

**Gemini thật đã chạy:** run PM `38fdb479-5566-4a18-b2da-6a9cf15aad3c` có plan BA+DEV+QA+Reviewer, trạng thái done/COMPLETED và LIVE_SUCCESS của Supervisor/BA/DEV/QA, model `gemini-3.5-flash-lite`, HTTP200, usage metadata. Có cả các run failed/unknown thật; không xóa hoặc gắn nhãn thành công. Replay không gọi lại model.

**Local thật, không dùng LLM:** Reviewer, Supervisor deterministic, Native reads, registry, SQLite/FTS, DailyBrief, workflow-error metadata và idempotency. Đây không phải mock; cũng không được giới thiệu như phân tích bằng model. Mock/stub trong test chỉ là bằng chứng offline.

Main Gateway hiện `a84bc31a582b`; Staging vẫn `456c38f6a9a9`. So sánh AST/source xác định6file khác:

- planner.py: chưa có resolve_target_agents; pure planner mới chỉ chọn một specialist.
- live_agents.py: logic execute/chọn specialists cũ; model planner lịch sử vẫn có thể chọn nhiều agent thật.
- store.py: chưa có thay đổi cancellation mới.
- reviewer_agent.py: chưa có kiểm tra result run-scope mới.
- knowledge_search.py: chưa có sửa pre-filter actor trong100FTSresults; có nguy cơ bỏ sót kết quả khi index lớn. Chưa có bằng chứng rò rỉ dữ liệu trong audit này.
- service.py: knowledge integration khác bản mới.

Ngoài Gateway, Core Staging còn lỗi nạp dashboard context sau POST search: kết quả Second Brain đúng nhưng các panel trên trống; GET Assistant mới phục hồi. Bằng chứng second-brain-ui.txt/png và assistant-demo-ready.png. Đây là sửa UI đã có trên Main nhưng chưa đưa xuống Stage. Không nâng cấp Stage trong lượt này.

7module thiếu trong image là nhóm dev/prototype đã được loại trừ lịch sử: e2e_demo, intent_evals, n8n_indexing_hook, proposal_aggregation, proposal_ux, scheduler_registry, supervisor_isolation. Thiếu tên file không tự chứng minh đường runtime bị hỏng. Không copy chúng vào Stage.

Policy local cấu hình15RPM/250000TPM/500RPD; guard90% áp dụng13/225000/450. Đây không phải quota còn lại ở Google. Main vàStage dùng cùng Googleproject, nên gọi Main có thể tiêu quota cần cho demo Stage. billing_enabled=false theo policy; chưa kiểm tra Console trực tiếp nên không cam kết chi phí thực tế tuyệt đối bằng0.

## 5. PM recovery theo phê duyệt mới

Owner đã cho phép reset mật khẩu/TOTP sau lỗi422. Chỉ tác động **Staging pm/User7**, không phải ba-pm/User6 hay MainPM19.

- Đổi password qua Native Rails validation; xóa device24 cũ và reset login-failure counter. Không tắt2FA hoặc thay role/admin/API tokens.
- Native password check PASS. PM Native API identity/role sau reset PASS.
- Fingerprints trong transaction của các users/passwords/devices khác, members, roles, settings, API tokens và Work Packages trước–sau khớp.
- Setting2FA vẫn enforced:true. Backup PG và accounts trước reset nằm trong thư mục private ngoài Git, ACL giới hạn Windows user vàSYSTEM.
- File mật khẩu mới: `C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/operator/PUBLICATION_REDACTED-pm-recovery-20261021-142650/PM_STAGING_LOGIN.txt`.
- User đã đăng nhập từ form mới, enrollQR native và xác nhận OTP. Device32/User7 active đã được đọc lại. Không dùng TOTP cũ hoặc gửi password/QR/seed/OTP vào chat.

Lỗi422 đã quan sát là **CSRF**, có3log authenticity failure lúc14:23/14:25/14:26. Reset credentials chưa chứng minh lỗi CSRF đã được sửa. Nếu tái diễn, dùng cửa sổ InPrivate và một tab duy nhất cùng hostname hiện tại, bắt đầu từ GET/login mới. Nếu vẫn lỗi, dừng; không tắtCSRF/MFA hoặc reset lặp. Login/enrollment mới đã thành công và UI PM đã được kiểm chứng. Chưa xác định dứt điểm nguyên nhân CSRF cũ; không cần tắt bảo vệ hoặc reset tiếp.

## 6. Bảo toàn Staging trong các bước Main tiếp theo

Stage có PGvolume `qldapm-ai-stage_stage-db`, assets `qldapm-ai-stage_stage-assets`, n8nvolume `qldapm-ai-stage_n8n-data`, gateway state `stage-ai` vàworkspace `stage-ai-workspaces`, khác Main. Network riêng. Main đã thay đổi lịch trong cửa sổ kiểm tra, trong khi Stage vẫn giữ372WP/352relations/4Versions cùng fingerprints và113AI/23agent/44receipts/517usage/5knowledge.

Tài nguyên còn chia sẻ là DockerDesktop/WSL, CPU/RAM/disk/network và Googleproject quota. Một số source được bind read-only vào Stage; sửa source trên Windows vẫn có thể ảnh hưởng file container nhìn thấy.

1. Chỉ thao tác Main service đã resolve hoặc qualification riêng. Đọc Stage ID/image/start/URL vàhealth trước/sau mỗi thay đổi Main; dừng bước Main nếu Stage giảm health hoặc thiếu tài nguyên.
2. Không down/restart/rebuild/recreate Stage; không restart DockerDesktop/WSL, prune/remove volumes hoặc cleanup hàng loạt. Không sync DB/SQLite/credentials hay thay image manifest Stage.
3. Không sửa các source đang bind vào Stage trong lúc giữ demo: quick_tunnel_web.rb, Quick.Caddyfile, scripts/core helpers và trusted backup scripts. Qualify ở bản copy riêng nếu cần thay chúng.
4. Giữ network automation, machinekey và workflows Stage. Không repoint n8n Stage sang Main hoặc dùng chung credential để lấp phần Main còn thiếu.
5. Giữ FreeOnly; không paid fallback. Không tự replay run unknown/failed hoặc gọi model chỉ để healthcheck.
6. Trước demo, lấy URL tại18090, kiểm health, đăng nhập PM trong một tab và mở trước các trang lịch sử. Tránh tác vụ Main nặng trong buổi demo.

Đây là runbook và kiểm chứng cửa sổ audit; chưa cài khóa toàn cục ngăn thao tác từ người/chương trình khác. Không bảo đảm Internet/uptime khi host hoặc tunnel bị thay đổi ngoài phiên này.

## 7. Kịch bản demo 13–14 phút

**Đã đạt:** PM enroll/login thành công, Assistant/Control Center/Search/Monitor/Kanban/Backlog đã mở được. Operator vẫn cần tự đăng nhập n8n nếu muốn trình bày editor. Không để khâu enroll lần đầu trước khán giả. Kịch bản chỉ đọc: không gửi AI mới, ExecuteWorkflow, Approve, dragcard, Ingest, Deindex hoặc Edit.

| Thời gian | Thao tác | Nội dung |
|---|---|---|
|00:00–01:00|18090→QuickTunnel; xác nhận Stage vàPM|Bản dự phòng độc lập Main, dùng role thật.|
|01:00–03:30|Work Packages/query29; mở Epic→Task→Subtask|335mục/11Epic; owner/status/hierarchy; xem một công việc, không sửa.|
|03:30–05:00|Boards19Kanban và20Workload; Backlog/S1|7cộtstatus,6cộtassignee,5Sprint planned; không drag hoặc nhầm Sprint vớiVersion.|
|05:00–05:45|Gantt/query37|Trình bày WBS và nói rõ Stage chưa applydates. Nếu cần thanh có ngày, dùng DemoProject1 và ghi rõ là dữ liệu mẫu.|
|05:45–08:00|Assistant→lịch sửPM→run38fdb479…|Kết quả đã lưu, planBA/DEV/QA/Reviewer, model/usage thật; nói rõ replay.|
|08:00–09:30|ExecutionMonitor của run đó|Graph/outputs/trace; nêu thiếu timing/events ở run cũ, không giả chuyển động live.|
|09:30–10:45|Second Brain, tìm AUTH hoặc Tài khoản|Một index nativeWP38/version1; theo citation về công việc; không ingest mới. Hiển thị kết quả thiếu/stale trung thực.|
|10:45–12:00|Mở lại GET Assistant rồi Control Center|6agentdefinitions, ownhistory, FreeOnly; phân biệt IDLE với LIVE_SUCCESS cũ và quota local với Google.|
|12:00–13:30|n8n bằng owner hiện có; xem DailyBrief/Executions|Execution37success, PMbriefREADY; không Execute. Nếu chưa có owner session, chỉ trình bày bằng chứng trong báo cáo.|
|13:30–14:00|Quay lại công việc/Assistant|Nêu phạm vi đã quan sát; mọi write vẫn cần preview/PMapproval riêng.|

Các đường dẫn trên hostname tunnel hiện tại:

- `/projects/qldapm-local/qldapm-ai`
- `/projects/qldapm-local/qldapm-ai/executions`
- `/projects/qldapm-local/qldapm-ai/executions/38fdb479-5566-4a18-b2da-6a9cf15aad3c`
- `/projects/qldapm-local/boards`
- `/projects/qldapm-local/backlogs/backlog`
- `/projects/qldapm-local/gantt`

Bỏ phần Gantt và rút ngắn n8n để xuống10phút. Không hứa live generation cho kịch bản bảo toàn dữ liệu này.

## 8. Main: kết quả kiểm chứng tiếp tục và giới hạn

Audit này không deploy/ghi Main hoặc gọi Google mới. Một tiến trình khác cập nhật Main trong lúc audit; không nhận công thực thi đó và không chạy apply lại.

Đọc độc lập lúc14:36:329/329rows khớp finalCSVv2 SHA256 `e25fa52a1f9999f971d4d0ecc26b1e0a1e84334e7674f2e9865583ca29f7301b`; dates/assignee/status/schedulingflags/Sprint/Version khớp, parentrollup0mismatch, boundariesMon–Fri,7Sprints05/10/2026→08/01/2027 ở in_planning. Chưa recheck343dependency/capacity thực trong lượt này.

Regression source hiện hành: **70/70offline testsPASS** trênWindows, gồmLiveAgents/Nativefixtures/CCauthorization/Monitor/knowledge. Lần đầu có2importerrors do module search path; giữloggốc và rerun corrected toàn bộ70PASS. Không dùng kết quả mock để ký nghiệm thu Gemini live.

Main run `ca0c3b3f-c01d-4291-a327-9c06b98e4f63` có BA+QA/Reviewer và receipts thật, nhưng **failed_or_unknown/GEMINI_REVIEW_FAILED** vì BA nhắc#102 ngoài context#49. Runc92242b2… cũng failed vì nguồn#38 lại nhắc#49. Guard đã chặn đúng; hành vi trả kết quả thành công end-to-end vẫn chưaPASS. Không nới Reviewer hoặc gọi lại để đổi nhãn.

Mainknowledge.sqlite đang0documents. Không có bằng chứng nối QLDAPM với birdsong/pgvector; không dùng containers Birdsong làm bằng chứng Second Brain QLDAPM. n8n hiện kiểm chứng là Stage, Mainautomation_runs/daily_briefs0 ở baseline; không coi đó là automation Main. Các khẳng định100%trong handoff mới phải được đối chiếu lại với các giới hạn này.

## 9. Bằng chứng và phần chưa kiểm

Bộ evidence: `docs/PUBLICATION_REDACTED-audit-20261021/` gồm before/after/details, native-and-main, provider-read-only, runtime-function-drift, csrf-signals, pm-recovery, preservation, main-schedule-readback, các scripts vàlogsregression. SQL dùng READONLY; SQLite dùng mode=ro/query_only; n8nDatabaseSyncreadOnly. Không export password/TOTPseed/key/rawproviderprompts vào evidence.

**Còn thiếu:** n8n owner editor; sửa context sauPOST củaStage;3Boards còn lại/toàn bộcard Kanban; thiết bị Internet độc lập; Gemini generation mới; ingestion/deindex mới; load20users; restore/restart rehearsal mới. Giữ kết luận **READY_FOR_READ_ONLY_DEMO_WITH_LIMITS** cho đúng kịch bản trên, không coi là nghiệm thu mọi chức năng hoặc demo livegeneration.

Bổ sung UAT14:53: `browser-uat-final.json`, assistant-ui.txt, second-brain-ui.txt/png, monitor-ui.txt/png, monitor-demo-ready.png, kanban-ui.txt, backlog-ui.txt, gantt-ui.txt/png. Các kiểm tra assertion đều PASS; sau UAT counts113AI/23agent/44receipts/517usage và fingerprints nghiệp vụ/ID-image-start của7containers vẫn giữ. Một mẫu console có lỗi từ chrome-extension, không khẳng định console sạch toàn diện.

![Assistant PM đã xác thực sau GET](docs/PUBLICATION_REDACTED-audit-20261021/assistant-demo-ready.png)

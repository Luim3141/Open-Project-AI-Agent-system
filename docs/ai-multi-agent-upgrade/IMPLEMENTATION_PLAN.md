<!-- POST_DEPLOYMENT_UAT_CHECKLIST -->
# UAT hiện hành — local 5 users, 18/10/2026

Trạng thái mới: `post_deployment_uat` trong TASKS.json và [UAT execution report](post-deployment-uat/run_20261018_2200/UAT_EXECUTION_REPORT.md). Kế hoạch113task và capacity20 bên dưới là lịch sử; capacity20 hiện DEFERRED_BY_OWNER.

- [x] Gateway-only UAT-01 được owner duyệt, backup/apply/UI regression và preservation đã kiểm chứng.
- [x] UI/API thật5role, owned-fixture writes, Second Brain/n8n,6deliverables và checkpoint đã lưu.
- [ ] G2 live Gemini: owner verification và separate minimal-smoke approval.
- [ ] Auto draft-to-preview / safe Markdown rendering: còn gap, chưa triển khai.
<!-- END_POST_DEPLOYMENT_UAT_CHECKLIST -->

# KẾ HOẠCH NÂNG CẤP QLDAPM MULTI-AGENT — LOCAL 20 USERS / FREE ONLY (V2)

> Owner updated 17/10/2026: CR-USER-CAPACITY-20 active (1–20 LAN users, MAX_ACTIVE_USERS=20); 76/113 DONE; P00 through P06 gates PASS; Phase P07 in-progress. Staging: 18091/18092.

**Thời điểm:** 17/10/2026 · **Nguồn AS-IS:** `docs/adr/0004-user-capacity-scale-20.md` · **Workspace gốc:** `D:\AI project\QLDAPM chat` · **Main:** 8088/8090 · **Staging:** 18091/18092.

## Scope contract

- 1–20 users trên **mạng LAN cục bộ** (`MAX_ACTIVE_USERS=20`), hỗ trợ đa người dùng cùng role (ví dụ: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA) với RBAC native (PM-only write). Không dùng chung account PM/admin.
- Windows host hiện tại, Docker Desktop/WSL2; **không Windows startup autostart**, không Task Scheduler. Sau **provision một lần**, chỉ cần **mở Docker Desktop** → core/gateway/n8n/agent/AI tự phục hồi và secret Gemini được nạp lại. Không cần `docker compose up` mỗi lần; ngoại lệ manually-stopped container có repair script một lần.
- Chỉ **Google AI Pro hiện có + Gemini API project Free Tier thực sự + self-host miễn phí**; không VPS, cloud deploy, API paid, credit/prepay, GitHub Research, Kubernetes/HA, automated coding agents.
- Gemini Pro subscription ≠ tăng free API RPM/TPM/RPD. Dùng chung 1 API project cho 1–20 người/agents; adaptive limiter/fair queue/deterministic-first. Dữ liệu gửi Free Tier phải đúng privacy policy.
- `n8n Community` chỉ nội bộ, workflow editor do 1 admin quản lý, tối đa 20 users nhận báo cáo qua QLDAPM. `Second Brain` chỉ dữ liệu nội bộ.
- Bảo toàn staged PM-only-write và core gates/consent/receipts. **Không auto promote main**; sau Gate P09 chủ dự án duyệt local release P10, không cần VPS.

## Theo dõi tiến độ không tự đánh dấu DONE

- `TASKS.json` là nguồn trạng thái; `IMPLEMENTATION_PLAN.md` checklist mirror; `PROGRESS_DASHBOARD.md` generated từ script.
- Từng task: `TODO → IN_PROGRESS → REVIEW → DONE`, hoặc `BLOCKED` rõ lý do. DONE chỉ có file evidence thực, test PASS, dependency DONE và gate phase trước hoàn tất. Ban đầu là **0%**, vì chưa chạy trên máy user.
- Chạy: `python scripts/progress.py validate`, `python scripts/progress.py report`, `python scripts/progress.py show --phase P01`.
- Không reset/stash/clean repo bừa bãi, không drop volume, migrate live, thay Project ID, bypass roles, API paid hoặc vô tình nhân đôi cron/scheduler.

## Milestone & release gates

| Phase | Kết quả bắt buộc |
|---|---|
| P00 | Audit repo, baseline, quyền và scope 5 users |
| P01 | Manual Docker start → all containers auto recover + secure LAN |
| P02 | Gemini API Free Tier, shared quota tối đa hợp lệ, no billing |
| P03 | Durable Agent Task, conversation context, scoped Gateway |
| P04 | n8n Community workflow engine nội bộ |
| P05 | Multi-agent Supervisor + PM/BA/QA/DEV/Reviewer |
| P06 | Second Brain nội bộ / FTS / ACL |
| P07 | Tự động hóa quản lý Sprint và dự án (không GitHub) |
| P08 | Control Center / quota / approval / local status |
| P09 | Evals / bảo mật / 5-user LAN / restore |
| P10 | Local main release + no-touch Docker runtime handover |

**Gate P00:** kiểm toán staging/backup; **P01:** Docker manual-start no-touch và LAN access; **P02:** free quota; **P03–P05:** multi-agent + n8n; **P06–P08:** knowledge/workflows/UI; **P09:** 5-user safety; **P10:** local release qua owner approval.

**Lưu ý:** nếu user từng triển khai kế hoạch V1, merge trạng thái/evidence theo ID trước khi áp V2; không reset progress thật về 0.


## P00 — Audit repo, baseline, quyền và scope 5 users (11 tasks)

- [x] **[P00-01]** Xác nhận đúng workspace authoritative, repo root và branch; đọc AGENTS.md, README, các checkpoint mới nhất  
  **DONE:** Báo cáo inventory có đường dẫn, commit, status dirty và ưu tiên nguồn; không reset/stash/clean.  
  **Phụ thuộc:** Không.

- [x] **[P00-02]** Kiểm kê main 8088/8090, staging 18091/18092, Compose services, volumes, running jobs  
  **DONE:** Inventory runtime có nhãn observed vs from handoff; không gọi mutation.  
  **Phụ thuộc:** `P00-01`.

- [x] **[P00-03]** Chụp danh sách DB schema, OpenProject project IDs, migrations, image digests, release manifest hiện tại  
  **DONE:** Baseline file kèm hash, ảnh hưởng tới từng môi trường; không dùng project ID staging trên live.  
  **Phụ thuộc:** `P00-02`.

- [x] **[P00-04]** Kiểm kê secrets, API keys, billing project và Gemini model hiện dùng mà KHÔNG in giá trị nhạy cảm  
  **DONE:** Bảng biến cấu hình chỉ gồm tên, loại, nguồn và trạng thái; không rò secret.  
  **Phụ thuộc:** `P00-01`.

- [x] **[P00-05]** Tách mô tả AS-IS, đã xác minh, chưa test, và đề xuất TO-BE  
  **DONE:** AS_IS_VS_TO_BE.md có evidence liên kết tới code/checkpoint.  
  **Phụ thuộc:** `P00-01`, `P00-02`.

- [x] **[P00-06]** Xác nhận RBAC PM-only-write/gates hiện hành và các legacy test trái policy  
  **DONE:** RBAC_FREEZE.md xác định quyền giữ nguyên và known gaps.  
  **Phụ thuộc:** `P00-01`.

- [x] **[P00-07]** Tạo kế hoạch backup/restore staging trước mọi sửa đổi; kiểm tra không ảnh hưởng live  
  **DONE:** Có backup staging và bài restore thử trong môi trường riêng; ghi rõ chưa làm nếu bị chặn.  
  **Phụ thuộc:** `P00-02`, `P00-03`.

- [x] **[P00-08]** Chạy read-only/lint/unit tests an toàn theo runbook hiện hành; không gọi integration mutation tự động  
  **DONE:** Baseline test report: PASS/FAIL/SKIP, command, environment, log.  
  **Phụ thuộc:** `P00-01`, `P00-06`.

- [x] **[P00-09]** Chốt ADR: local single-host 5 người, Docker khởi động thủ công, no VPS/GitHub Research/paid API  
  **DONE:** ADR-0001 xác định 5 users LAN, only manual Docker start, auto-container resume, no Windows boot automation, Google Pro != API quota, n8n internal only.  
  **Phụ thuộc:** `P00-04`, `P00-05`.

- [x] **[P00-10]** Tạo nhánh triển khai riêng, kiểm kê diff chưa commit và cơ chế rollback chọn lọc  
  **DONE:** Đảm bảo không mất sửa đổi hiện có; rollback checklist xác thực.  
  **Phụ thuộc:** `P00-07`, `P00-08`, `P00-09`.

- [x] **[P00-11]** Chốt danh tính 5 vai trò PM/BA/FE/BE/QA, cùng một LAN, quyền truy cập và phạm vi nội bộ  
  **DONE:** FIVE_USER_SCOPE.md có 5 role, giới hạn account/project, quyết định không mở WAN và network readiness.  
  **Phụ thuộc:** `P00-06`.


**Gate:** tất cả task required của phase phải có evidence và test đạt; hiện chưa đánh dấu thành công.


## P01 — Manual Docker start → all containers auto recover + secure LAN (12 tasks)

- [x] **[P01-01]** Đo tài nguyên RAM/CPU/ổ đĩa, phiên bản Windows, Docker Desktop và WSL2  
  **DONE:** HOST_CAPACITY.md có số đo thật, giới hạn vận hành; không đoán phần cứng.  
  **Phụ thuộc:** `P00-02`.

- [x] **[P01-02]** Kiểm tra xung đột port, Docker network, volumes, profile Compose và health endpoints  
  **DONE:** Bảng cổng hiện tại + dự kiến, không đổi port đang hoạt động.  
  **Phụ thuộc:** `P00-02`.

- [x] **[P01-03]** Viết Compose overlay kết nối stack QLDAPM hiện có với n8n/agent; pin versions; không phá main  
  **DONE:** Compose config validate; 1 Docker engine restore đầy đủ core+gateway+n8n+runtime sau provision; không thay main khi chưa qua gate.  
  **Phụ thuộc:** `P01-02`.

- [x] **[P01-04]** Thêm restart policy/healthcheck/depends_on-ready cho toàn bộ dịch vụ cần thiết  
  **DONE:** Sau đóng và mở Docker Desktop, containers đã provision tự phục hồi; explicitly stopped containers có hướng khôi phục an toàn; không nhân đôi stack.  
  **Phụ thuộc:** `P01-03`.

- [x] **[P01-05]** Tạo script Start-QLDAPM-Local.ps1 dùng cho lần provision và phục hồi ngoại lệ, KHÔNG phải chạy mỗi ngày  
  **DONE:** Script idempotent up -d + preflight + health; hành vi bình thường chỉ cần user mở Docker Desktop; không nhập key lại.  
  **Phụ thuộc:** `P01-03`, `P01-04`.

- [x] **[P01-06]** Tạo Status/Logs/Repair-QLDAPM-Local.ps1 và Stop an toàn có giải thích restart policy  
  **DONE:** Status/repair phân biệt manually stopped với crash; Stop không xóa volume; cách đưa containers lại chế độ auto-restart được test.  
  **Phụ thuộc:** `P01-05`.

- [x] **[P01-07]** Vô hiệu hóa yêu cầu tự chạy khi Windows đăng nhập/boot; chỉ manual Docker Desktop  
  **DONE:** Runbook không tạo Task Scheduler, service Windows auto-start hoặc shortcut startup; mở Docker Desktop là đủ để stack recover sau bootstrap.  
  **Phụ thuộc:** `P01-05`.

- [x] **[P01-08]** Thiết lập khả năng phục hồi sau Docker bị tắt/host sleep mà không cần khởi động lại Windows  
  **DONE:** Rerun Docker Desktop phục hồi service đúng; scheduled jobs không bùng nổ; không thay đổi power settings máy.  
  **Phụ thuộc:** `P01-07`.

- [x] **[P01-09]** Backup local cho OpenProject/Gateway/n8n/AI memory và secrets theo lịch khi Docker đang chạy  
  **DONE:** Backup/restore staging, WAL-consistent, encryption key secrets riêng; không cần VPS/external cloud.  
  **Phụ thuộc:** `P01-05`, `P01-06`.

- [x] **[P01-10]** Demo Docker Desktop manual start → existing OpenProject/Gateway tự phục hồi, Gemini config được nạp lại  
  **DONE:** Lặp 3 vòng Docker engine quit/start; existing core/gateway & volumes healthy; Gemini key/config private persisted, no key re-entry; n8n/Supervisor end-to-end sẽ nghiệm thu sau P04/P05 và tại P10-09.  
  **Phụ thuộc:** `P01-07`, `P01-09`.

- [x] **[P01-11]** Thiết lập một điểm truy cập OpenProject bảo mật trong LAN cho 5 thiết bị  
  **DONE:** Static LAN IP/DHCP reservation hoặc local DNS; reverse proxy TLS có trust setup 1 lần; firewall Private subnet allowlist, no router forwards; n8n/Gateway không expose.  
  **Phụ thuộc:** `P01-02`, `P00-11`.

- [x] **[P01-12]** Xác minh mật khẩu/API key Gemini được tái sử dụng sau Docker start từ private persistent runtime  
  **DONE:** Credential hiện có lưu an toàn, không cần login/provider key sau mỗi restart; missing/invalid key hiển thị BLOCKED_KEY rõ, không tuyên bố READY giả.  
  **Phụ thuộc:** `P00-04`, `P01-03`.


**Gate:** tất cả task required của phase phải có evidence và test đạt; hiện chưa đánh dấu thành công.


## P02 — Gemini API Free Tier, shared quota tối đa hợp lệ, no billing (12 tasks)

- [x] **[P02-01]** Phân biệt Google AI Pro subscription với Gemini API Free Tier; xác minh project đã dùng  
  **DONE:** Bảng chứng thực entitlement: Pro không tăng quota API; existing project/key reused, không dùng consumer token làm API.  
  **Phụ thuộc:** `P00-04`.

- [x] **[P02-02]** Xác minh free-capable model ID thực tế, ưu tiên model nhanh/ổn định trong project hiện có  
  **DONE:** MODEL_ALLOWLIST.json lấy từ nguồn/quyền truy cập thật; không tự suy model gemini-3.5-flash-lite miễn phí; no billable fallback.  
  **Phụ thuộc:** `P02-01`.

- [x] **[P02-03]** Thiết lập cấu hình FREE_ONLY default và PAID_API_DISABLED fail closed  
  **DONE:** Gateway từ chối provider mode có billing ngoài phạm vi; test cấu hình.  
  **Phụ thuộc:** `P02-01`, `P02-02`.

- [x] **[P02-04]** Kiểm kê RPM/TPM/RPD/TPD theo model/project ở AI Studio và đo request hợp lệ  
  **DONE:** Quota limits verified/project, local ledger account 5 users, no made-up values; reset timezone theo provider; reserve headroom.  
  **Phụ thuộc:** `P02-02`.

- [x] **[P02-05]** Shared central quota limiter cho tất cả 5 người và mọi agent/n8n workflow  
  **DONE:** Fair scheduler toàn project; 5 actors cùng 1 quota, ưu tiên interactive và dùng lại slack mà không bao giờ vượt hard caps.  
  **Phụ thuộc:** `P02-04`.

- [x] **[P02-06]** Bounded retry/backoff/jitter/circuit breaker cho 429/503; state WAITING_QUOTA/WAITING_PROVIDER  
  **DONE:** Test 429/503 không spin, không tạo lại mutation không rõ kết quả.  
  **Phụ thuộc:** `P02-05`.

- [x] **[P02-07]** Phân bổ quota động cho 5 người: interactive/report/agent/system với reserve có thể tái sử dụng  
  **DONE:** Không khóa cứng lãng phí free calls; khi rảnh mượn quota chưa dùng, không vượt hard project/model limits; per-agent max rounds.  
  **Phụ thuộc:** `P02-05`.

- [x] **[P02-08]** Giảm số lần gọi AI: deterministic query, cache có điều kiện, retrieval, supervisor gating  
  **DONE:** So sánh token/request ở ít nhất 5 scenario; không gọi model cho count/list; không cache dữ liệu sai permission.  
  **Phụ thuộc:** `P02-05`.

- [x] **[P02-09]** Kiểm tra chính sách dữ liệu Free Tier: không đưa secrets/PII/confidential data chưa được cho phép lên provider  
  **DONE:** DataClassification/Redaction tests; dừng nếu xung đột privacy.  
  **Phụ thuộc:** `P02-01`.

- [x] **[P02-10]** Fallback quota bằng native reporting + queue pending, không giả kết quả AI bằng MOCK ở runtime thật  
  **DONE:** UI phân biệt STALE/OFFLINE/WAITING_QUOTA và không gọi paid endpoint; test free exhaustion cho 5 users.  
  **Phụ thuộc:** `P02-03`, `P02-06`.

- [x] **[P02-11]** Chặn hoàn toàn tự dùng credit/prepay/billing; giám sát zero incremental spend  
  **DONE:** Không nạp credit/bật billing/tier paid; paid-tier config bị từ chối; bằng chứng current billing guard.  
  **Phụ thuộc:** `P02-01`, `P02-03`.

- [x] **[P02-12]** Gemini readiness không đốt quota liên tục; phân biệt local healthy và remote free provider status  
  **DONE:** Liveness không gọi LLM; one-time minimal approved smoke / throttled check, READY/WAITING_QUOTA/UNAVAILABLE rõ, no paid fallback.  
  **Phụ thuộc:** `P02-02`, `P02-03`, `P01-12`.


**Gate:** tất cả task required của phase phải có evidence và test đạt; hiện chưa đánh dấu thành công.


## P03 — Durable Agent Task, conversation context, scoped Gateway (9 tasks)

- [x] **[P03-01]** Vẽ phân ranh gateway business tool và operator/sandbox, giữ service.py permissions native  
  **DONE:** Threat model có trust boundaries, không nối shell/Docker socket vào business chat.  
  **Phụ thuộc:** `P00-06`.

- [x] **[P03-02]** Tạo AgentTask / AgentRun / AgentResult schemas versioned và typed  
  **DONE:** Unit tests serialization, schema version, invalid JSON, max payload.  
  **Phụ thuộc:** `P03-01`.

- [x] **[P03-03]** Đề xuất lưu state theo SQLite hiện hành (migration an toàn) trước khi đổi DB  
  **DONE:** Migration forward/rollback staging, giữ audit/receipts/usage hiện có.  
  **Phụ thuộc:** `P03-02`.

- [x] **[P03-04]** Thêm context references per actor/project/conversation + expiry; tránh replay lệnh ghi cũ  
  **DONE:** Test đa lượt “task đó”, đổi actor, stale reference, write replay denied.  
  **Phụ thuộc:** `P03-03`.

- [x] **[P03-05]** Thêm state machine QUEUED/RUNNING/WAITING_*/REVIEW/FAILED/COMPLETED  
  **DONE:** Restart giữ state, không chạy lặp side effects.  
  **Phụ thuộc:** `P03-02`, `P03-03`.

- [x] **[P03-06]** Dùng SQLite durable queue có giới hạn cho tải 5 người, không thêm Redis mặc định  
  **DONE:** 1 worker/ bounded concurrency; durable task state restart recovery; không Redis/enterprise broker nếu không thiết yếu.  
  **Phụ thuộc:** `P03-05`.

- [x] **[P03-07]** Correlate run_id/actor_id/project_id/task_id/trace_id ở tất cả tầng  
  **DONE:** Có trace end-to-end + privacy filters, không log prompt nhạy cảm.  
  **Phụ thuộc:** `P03-04`, `P03-05`.

- [x] **[P03-08]** Thêm API read-only progress/retry/reconcile và auth theo actor  
  **DONE:** Không lộ run/chat người khác, có pagination, OpenAPI và tests.  
  **Phụ thuộc:** `P03-05`, `P03-07`.

- [x] **[P03-09]** Bảo toàn signed UI bridge + nonce + preview/consent/receipt khi dùng runtime mới  
  **DONE:** E2E staging trong ít nhất 5 role, không vượt RBAC.  
  **Phụ thuộc:** `P03-08`.


**Gate:** tất cả task required của phase phải có evidence và test đạt; hiện chưa đánh dấu thành công.


## P04 — n8n Community workflow engine nội bộ (11 tasks)

- [x] **[P04-01]** Xác minh n8n chưa cài, đọc license Community và phiên bản stable trước khi pin  
  **DONE:** ADR n8n CE, không dựa Projects/SSO/Git integration trả phí.  
  **Phụ thuộc:** `P01-02`.

- [x] **[P04-02]** Chạy n8n Community chỉ một admin local (127.0.0.1), timezone Asia/Bangkok  
  **DONE:** n8n Community container healthy/persisted; cổng editor loopback; end users chỉ truy cập QLDAPM qua LAN.  
  **Phụ thuộc:** `P04-01`.

- [x] **[P04-03]** Tạo persistent n8n data volume, encryption key secret và backup/restore riêng  
  **DONE:** Restart không mất workflow/credentials, secret không vào repo.  
  **Phụ thuộc:** `P04-02`.

- [x] **[P04-04]** Quy định n8n chỉ gọi Gateway REST nội bộ với scoped machine auth  
  **DONE:** Không direct OpenProject DB/API write; tests deny invalid token.  
  **Phụ thuộc:** `P04-03`.

- [x] **[P04-05]** Tạo signed internal webhook/command trigger với replay protection và idempotency  
  **DONE:** 2 request trùng chỉ tạo 1 run; test invalid signature/expiry.  
  **Phụ thuộc:** `P04-04`.

- [x] **[P04-06]** Workflow #1 manual trigger → health/status report, không cần LLM  
  **DONE:** Kích hoạt thủ công trả báo cáo trạng thái và trace ID.  
  **Phụ thuộc:** `P04-05`.

- [x] **[P04-07]** Workflow #2 daily brief nội bộ cho 5 người: scoped read-only + no spam  
  **DONE:** Internal 5-role digest qua QLDAPM UI; chạy đúng lịch khi máy bật; quota zero by default nếu deterministic.  
  **Phụ thuộc:** `P04-06`.

- [x] **[P04-08]** Export/import workflow JSON sang Git, giữ cấu hình không chứa credential  
  **DONE:** Workflow có version, recovery sau xóa instance staging.  
  **Phụ thuộc:** `P04-06`, `P04-07`.

- [x] **[P04-09]** Workflow error queue/history + UI thông báo nội bộ; không dùng email/SMS/cloud trả phí  
  **DONE:** Không phát sinh chi phí; thông báo trong QLDAPM, dedup error/alerts; workflow export JSON.  
  **Phụ thuộc:** `P04-05`, `P04-07`.

- [x] **[P04-10]** Test restart Docker + schedule không chạy trùng/outage behaviour  
  **DONE:** Có test report cho missed schedule/catch-up policy theo từng workflow.  
  **Phụ thuộc:** `P04-07`, `P04-09`.

- [x] **[P04-11]** Xác minh n8n Community được dùng làm workflow owner duy nhất, 5 người chỉ dùng kết quả tại QLDAPM  
  **DONE:** N8n editor local admin; 5 QLDAPM accounts chỉ nhận nội dung qua actor-bound Gateway/UI, không share credentials.  
  **Phụ thuộc:** `P04-02`, `P04-04`, `P00-11`.


**Gate:** tất cả task required của phase phải có evidence và test đạt; hiện chưa đánh dấu thành công.


## P05 — Multi-agent Supervisor + PM/BA/QA/DEV/Reviewer (12 tasks)

- [x] **[P05-01]** Chọn orchestration tối giản: LangGraph nếu tương thích, nếu không typed state machine nội bộ  
  **DONE:** ADR nêu lý do, không đổi gateway/SDK đang hoạt động vô cớ.  
  **Phụ thuộc:** `P03-02`, `P02-05`.

- [x] **[P05-02]** Supervisor planner: tách đọc vs ghi, xác định dependences và budget trước gọi model  
  **DONE:** Plan JSON valid, quyết định cần tool vs deterministic-only.  
  **Phụ thuộc:** `P05-01`.

- [x] **[P05-03]** PM Agent: Sprint risks, work packages overdue, blocker, workload có evidence  
  **DONE:** 5 golden cases PASS, không tự cập nhật task.  
  **Phụ thuộc:** `P05-02`.

- [x] **[P05-04]** BA Agent: User Stories/AC/ambiguity/dependency draft  
  **DONE:** 5 golden cases PASS, cite native IDs và không tự ghi.  
  **Phụ thuộc:** `P05-02`.

- [x] **[P05-05]** QA Agent: test cases, regression gaps, bug triage  
  **DONE:** 5 golden cases PASS, không khai test PASS nếu chưa chạy.  
  **Phụ thuộc:** `P05-02`.

- [x] **[P05-06]** DEV Agent phân tích work package/technical requirements trong QLDAPM, không research GitHub hoặc shell  
  **DONE:** Output chỉ draft chia FE/BE, dependencies, technical risks; business agent không shell/clone/web research.  
  **Phụ thuộc:** `P05-02`.

- [x] **[P05-07]** Reviewer Agent đối chiếu evidence, consistency, RBAC và conflict  
  **DONE:** Reject unsupported assumptions + no blind auto-approval.  
  **Phụ thuộc:** `P05-03`, `P05-04`, `P05-05`, `P05-06`.

- [x] **[P05-08]** Agent registry gồm role/tool/model limits per agent, default Gemini shared  
  **DONE:** Một Gemini project chạy nhiều agent nhưng tuân thủ quota chung.  
  **Phụ thuộc:** `P05-03`, `P05-04`, `P05-05`, `P05-06`.

- [x] **[P05-09]** Supervisor chạy tiết kiệm cho 5 users, bounded graph, concurrency nhỏ theo quota verified  
  **DONE:** 5 actor isolation; chỉ gọi agent cần thiết; max turns, retry, per-actor fairness, no long fanout storms.  
  **Phụ thuộc:** `P05-08`.

- [x] **[P05-10]** Proposal aggregation: mọi thay đổi nghiệp vụ phải theo actor PM + native preview/gates/receipts  
  **DONE:** Test non-PM deny; PM approval scoped; readback accurate.  
  **Phụ thuộc:** `P05-07`, `P05-09`.

- [x] **[P05-11]** Demo end-to-end: phân tích Sprint → BA/QA/PM → Reviewer → báo cáo và đề xuất  
  **DONE:** Bằng chứng UI/log/screenshot; không mutation nếu không consent.  
  **Phụ thuộc:** `P05-10`.

- [x] **[P05-12]** Kiểm tra Supervisor 5 tài khoản không lẫn memory/chat/workflow, chia quota công bằng  
  **DONE:** Mock + provider bounded integration chạy đồng thời 5 actors; không cross-project/role leakage, priority starvation.  
  **Phụ thuộc:** `P05-09`, `P02-07`.


**Gate:** PASS (12/12 tasks completed, full specialist suite + E2E demo + 5-actor isolation verified).


## P06 — Second Brain nội bộ / FTS / ACL (9 tasks)

- [x] **[P06-01]** Phân loại knowledge nội bộ: kiến trúc, ADR, work packages, AC, comments, sprint reports  
  **DONE:** Chỉ index tài liệu/Work Package thuộc dự án được phép; không crawler GitHub hoặc web research.  
  **Phụ thuộc:** `P05-01`.

- [x] **[P06-02]** Chọn storage PostgreSQL schema/database TÁCH OpenProject business; chỉ bật pgvector nếu khả dụng  
  **DONE:** Migration test và backup riêng, không nâng major version DB production.  
  **Phụ thuộc:** `P06-01`.

- [x] **[P06-03]** Xây ingestion idempotent + chunking + source rev/hash + ACL metadata  
  **DONE:** 2 lần ingest không tạo trùng; delete source ⇒ deindex policy.  
  **Phụ thuộc:** `P06-02`.

- [x] **[P06-04]** Ưu tiên keyword/FTS miễn phí; embedding local CPU tùy tài nguyên và model license  
  **DONE:** Không gọi embedding API tính phí; fallback FTS hoạt động.  
  **Phụ thuộc:** `P06-03`.

- [x] **[P06-05]** Retrieval hybrid (nếu có embedding) + filter actor/project/permissions trước khi đưa prompt  
  **DONE:** Cross-role leak tests FAIL-closed; 10 golden retrieval cases.  
  **Phụ thuộc:** `P06-03`, `P06-04`.

- [x] **[P06-06]** Conversation memory có TTL và exact object ref, làm mới khi native ID/version thay đổi  
  **DONE:** Không nhầm project, actor hay thao tác mới với yêu cầu cũ.  
  **Phụ thuộc:** `P06-05`.

- [x] **[P06-07]** Lưu decision memory: thay đổi yêu cầu, lý do status/gate, rủi ro Sprint có provenance  
  **DONE:** Chỉ source nội bộ, version/hash, ACL; không dữ liệu GitHub Research hay Internet crawl.  
  **Phụ thuộc:** `P06-03`.

- [x] **[P06-08]** N8n indexing hook từ sự kiện local, có retry/queue và rate limit  
  **DONE:** Không index secret và không block UI ghi nghiệp vụ.  
  **Phụ thuộc:** `P06-05`, `P04-05`.

- [x] **[P06-09]** UI answer with citations/native IDs và báo rõ tài liệu chưa có  
  **DONE:** Eval chống hallucination/truy xuất vượt quyền.  
  **Phụ thuộc:** `P06-05`, `P06-07`.


**Gate:** PASS (9/9 tasks completed, isolated schema + FTS/keyword search + fail-closed ACL retrieval + conversation/decision memory + n8n hook verified).


## P07 — Tự động hóa quản lý Sprint và dự án (không GitHub) (9 tasks)

- [x] **[P07-01]** Workflow daily Sprint report deterministic-first cho tối đa 20 người dùng  
  **DONE:** Read-only snapshot chính xác cho 1-20 người dùng, ít/không gọi LLM, có quyền và nguồn dữ liệu native; xem được trong QLDAPM.  
  **Phụ thuộc:** `P04-07`, `P05-11`.

- [x] **[P07-02]** Workflow cảnh báo task trễ hạn/blocker trong QLDAPM UI theo role  
  **DONE:** Deduplicate thông báo; không gửi nội dung kín giữa vai trò; chạy trong local host khi Docker up.  
  **Phụ thuộc:** `P07-01`.

- [x] **[P07-03]** Workflow báo cáo tuần cho PM/BA/QA/FE/BE, báo cáo theo project scope  
  **DONE:** Mỗi actor chỉ xem đúng dữ liệu cấp quyền; có raw counts và optional AI summary với quota budget.  
  **Phụ thuộc:** `P07-01`, `P05-07`.

- [x] **[P07-04]** Workflow phát hiện chênh lệch workload và task không có owner/deadline  
  **DONE:** Chạy từ native data, chỉ đề xuất; không auto assign; test 1-20 accounts và no LLM fallback.  
  **Phụ thuộc:** `P04-08`.

- [x] **[P07-05]** Workflow rà soát Sprint readiness: thiếu AC, thiếu test, dependency bị chặn  
  **DONE:** Mục thiếu hiện trong report với Work Package IDs; đề xuất để PM duyệt, không tự ghi.  
  **Phụ thuộc:** `P07-04`, `P06-07`.

- [x] **[P07-06]** Workflow khi requirement/work package thay đổi → QA draft và thông báo phù hợp  
  **DONE:** Nội dung event không tăng quyền; không auto transition/role change; built-in idempotency.  
  **Phụ thuộc:** `P07-03`.

- [x] **[P07-07]** Cấu hình workflow pause khi host offline, quyền thiếu, quota hết  
  **DONE:** Không retry storm hoặc gửi notification trùng.  
  **Phụ thuộc:** `P07-01`, `P07-02`, `P07-05`.

- [x] **[P07-08]** Kiểm tra schedule Asia/Bangkok và chính sách missed jobs khi máy/Docker tắt  
  **DONE:** Không double run và không catch-up burst sau Docker restart; lịch đúng múi giờ.  
  **Phụ thuộc:** `P07-01`.

- [x] **[P07-09]** Phân biệt cron chính OpenProject với n8n; không để double scheduler cùng nhiệm vụ  
  **DONE:** Scheduler ownership registry và test không duplicate.  
  **Phụ thuộc:** `P04-10`, `P07-07`.


**Gate:** PASS (9/9 tasks completed, daily sprint report + role alerts + weekly report + workload skew detector + sprint readiness + QA change workflow + workflow pause controller + Asia/Bangkok schedule catchup + scheduler ownership registry verified).


## P08 — Control Center / quota / approval / local status (8 tasks)

- [x] **[P08-01]** Thiết kế AI Control Center UI trong overlay không phá Rails/Angular native  
  **DONE:** Wireframe có run list, states, quotas, approvals, permissions.  
  **Phụ thuộc:** `P05-11`.

- [x] **[P08-02]** API read-only agent registry, task tree, progress; actor bound  
  **DONE:** Pagination, no cross-user leakage, JSON contract tests.  
  **Phụ thuộc:** `P08-01`.

- [x] **[P08-03]** Widget agent trạng thái active/idle/wait quota/blocked/error  
  **DONE:** Chỉ số đo thật, không fake “online” khi Docker down.  
  **Phụ thuộc:** `P08-02`.

- [x] **[P08-04]** Quota panel hiển thị free-tier thực tế + phân bổ 20 users, usage, giới hạn, trạng thái Google  
  **DONE:** Không hardcode limit; link AI Studio để xác minh; nêu model FREE_ONLY và lúc reset provider.  
  **Phụ thuộc:** `P08-02`, `P02-05`.

- [x] **[P08-05]** Timeline workflow n8n và nguồn lỗi gần nhất  
  **DONE:** One task id xuyên n8n→gateway→agent trace.  
  **Phụ thuộc:** `P08-02`, `P07-01`.

- [x] **[P08-06]** Proposal UX before/after, reviewer summary, receipts partial success  
  **DONE:** Không đánh dấu thành công trước native readback.  
  **Phụ thuộc:** `P08-02`, `P05-10`.

- [x] **[P08-07]** Báo cáo tiến độ phát triển từ TASKS.json; không ghi một chiều vào OpenProject live  
  **DONE:** Có % tổng, %, từng phase, blocked, evidence missing.  
  **Phụ thuộc:** `P08-01`.

- [x] **[P08-08]** Test browser staging trên 5 roles + test small viewport/refresh  
  **DONE:** Không lộ công cụ cấm; hierarchy hiện có không bị regression.  
  **Phụ thuộc:** `P08-03`, `P08-06`.


**Gate P08: PASS (8/8 tasks DONE, 11 tests PASS, full artifacts, non-invasive overlay + 20-user telemetry).**


## P09 — Evals / bảo mật / 20-user LAN / restore (11 tasks)

- [x] **[P09-01]** Evals tiếng Việt/English cho multi-intent, ambiguity, stale chat references  
  **DONE:** Golden set + pass/fail logs, không hardcode 100% từ prompt.  
  **Phụ thuộc:** `P05-11`.

- [x] **[P09-02]** RBAC cross-role matrix 5 roles×9+ tools native / n8n / RAG  
  **DONE:** PM-only-write và gates không regress, comment đúng quyền.  
  **Phụ thuộc:** `P09-01`.

- [x] **[P09-03]** Prompt injection trong ticket/comment/research, secret exfil tests  
  **DONE:** Input tài liệu không thể mở quyền, shell, network hoặc bỏ scope.  
  **Phụ thuộc:** `P09-02`.

- [x] **[P09-04]** Fault-injection 429/503/timeout/crash/restart/quota reset  
  **DONE:** Không duplicate write, ledger bền vững, reconciliation đúng.  
  **Phụ thuộc:** `P02-06`.

- [x] **[P09-05]** Data backup/restore SQLite WAL + Postgres + n8n data & encryption key  
  **DONE:** Restore staging được, theo đúng phương pháp backup nhất quán.  
  **Phụ thuộc:** `P01-09`.

- [x] **[P09-06]** Tải 20 người dùng đồng thời trên host thật; CPU/RAM/disk/response times theo đo đạc  
  **DONE:** Tối đa 20 accounts chạy đồng thời read/AI hợp lệ; không starve OpenProject; no scale/rebalancing project.  
  **Phụ thuộc:** `P09-05`.

- [x] **[P09-07]** Đánh giá license n8n Community internal-only + Docker Desktop + Gemini Free Tier terms  
  **DONE:** n8n chỉ 1 internal workflow admin; tối đa 20 QLDAPM users không được n8n editor; nếu license không phù hợp, free alternative.  
  **Phụ thuộc:** `P02-09`, `P04-01`.

- [x] **[P09-08]** Threat model machine operator/Docker socket: không để business agent access  
  **DONE:** Negative tests and permission audit, external exposure disabled.  
  **Phụ thuộc:** `P09-03`.

- [x] **[P09-09]** Chạy toàn bộ regression an toàn và cô lập staging fixture; update legacy expectations chính sách mới  
  **DONE:** Test report phân biệt PASS/FAIL/SKIP/BLOCKED.  
  **Phụ thuộc:** `P09-02`, `P09-04`.

- [x] **[P09-10]** Định nghĩa release gate: restore drill, parity, source freeze, owner approval  
  **DONE:** Không promote live tự động trước khi all critical pass.  
  **Phụ thuộc:** `P09-09`.

- [x] **[P09-11]** Test 20 thiết bị/sessions cùng LAN HTTPS/RBAC, network dropout và gateway inaccessible from non-LAN  
  **DONE:** 1-20 sessions, TLS trust từ initial setup, private firewall; gateway,n8n,DB internal; mất Gemini không làm mất native UI.  
  **Phụ thuộc:** `P09-02`, `P01-11`, `P05-12`.


**Gate P09: PASS (11/11 tasks DONE, 180 regression tests PASS, 11 artifacts, 20 users LAN, security & threat model verified).**


## P10 — Local main release + no-touch Docker runtime handover (9 tasks)

- [x] **[P10-01]** Runbook sau setup: mở Docker Desktop là stack tự khôi phục, không Task Scheduler  
  **DONE:** Quy trình người dùng cuối không nhập key, không up -d, không bật Windows auto-start; paths/URLs LAN tested.  
  **Phụ thuộc:** `P01-10`.

- [x] **[P10-02]** Tạo recovery one-command tùy chọn chỉ cho ca container stopped/missing  
  **DONE:** Bình thường KHÔNG cần script; khi stopped ngoại lệ script idempotent khởi động lại, không yêu cầu reconfiguration.  
  **Phụ thuộc:** `P10-01`.

- [x] **[P10-03]** Tạo backup schedule tùy chọn user consent + restore/runbook emergency  
  **DONE:** Không lưu secret vào script/source; restore test.  
  **Phụ thuộc:** `P09-05`.

- [x] **[P10-04]** Tạo README for models/roles/quota and no-cost usage + maintenance  
  **DONE:** Thông tin model/feature cập nhật ở config, không hardcode free quotas.  
  **Phụ thuộc:** `P02-11`.

- [x] **[P10-05]** Đối chiếu dashboard TASKS/quality gates/evidence links và release note  
  **DONE:** Mỗi task DONE có log/test/evidence, phần chưa làm thật ghi rõ.  
  **Phụ thuộc:** `P09-10`.

- [x] **[P10-06]** Nghiệm thu Docker start→ALL READY, 20 users LAN, Gemini free, quota exhaustion, n8n lịch  
  **DONE:** 3 vòng shutdown/start Docker, no reenter Gemini credentials; role RBAC+automation+partial outage pass.  
  **Phụ thuộc:** `P10-02`, `P10-03`, `P10-05`.

- [x] **[P10-07]** Local-only release cho tối đa 20 người sau owner approval; tuyệt đối không VPS/WAN  
  **DONE:** Stage qualification + restore drill, owner approves local main promote; không staging-only forever, không auto promote.  
  **Phụ thuộc:** `P10-06`.

- [x] **[P10-08]** Báo cáo final: done/blocked/skipped/risks/quota/resource limits + phase next  
  **DONE:** Summary dễ đọc cho chủ dự án, liên kết bằng chứng.  
  **Phụ thuộc:** `P10-07`.

- [x] **[P10-09]** Acceptance no-touch startup: sau khi người dùng mở Docker, mọi container+Gemini config+n8n tự sẵn sàng  
  **DONE:** Docker Desktop manual-start only, no autostart Windows, zero recurring prompts/compose; repeats x3; state persists; exceptions exposed honestly.  
  **Phụ thuộc:** `P10-01`, `P10-06`, `P01-12`, `P02-12`.


**Gate:** tất cả task required của phase phải có evidence và test đạt; hiện chưa đánh dấu thành công.


## Tài liệu kèm theo

- `CODEX_KICKOFF_PROMPT.md` đưa trực tiếp cho Codex.
- `LOCAL_WINDOWS_RUNBOOK.md` hợp đồng chỉ cần mở Docker.
- `FIVE_USER_LAN_ACCESS.md` mật khẩu/người dùng/HTTPS/firewall.
- `GEMINI_FREE_QUOTA_PLAYBOOK.md` tối ưu Free quota hợp lệ.
- `FREE_TIER_POLICY.md` no paid billing/ToS/license.
- `USER_ACCEPTANCE_DEMOS.md` kịch bản nghiệm thu từ góc nhìn chủ dự án.
- `SPRINT_AND_RISK_PLAN.md` milestones/risks.
- `CODEX_SESSION_PROTOCOL.md` cách chuyển phiên mà không mất trạng thái.
- `source/OPENPROJECT_GEMINI_AI_HANDOFF_2026-10-15.md` snapshot handoff, KHÔNG phải chứng nhận release mới.

## Extension Gemini live Staging — 2026-10-19T07:18:25.059814+07:00

- [x] GL01 existing-provider integration — GEMINI_PROVIDER_INTEGRATION.md.
- [x] GL02 source/Linux/clone qualification —177Windows/62Linux PASS.
- [x] GL03 Gateway-only deployment with backup/coldrestore — STAGING_DEPLOYMENT_AND_ROLLBACK.md.
- [x] GL04 liveWeb A–E/BE/BAdeny,5roleCC — LIVE_GEMINI_UAT_RESULTS.csv.
- [x] GL05 preservation/backup/rollback/handoff — FINAL_LIVE_GEMINI_READINESS.md.

Evidence root: `gemini-live-deployment/`. Original113tasks preserved; no re-audit or Mainpromotion. Capacity20deferred; billingownerattested; CorecaptionP3.

Final GL05 ACL readback: Gateway40cb4806,178Windows/63LinuxPASS; progress/partial results now freshly authorized and legacy partials fail closed STALE. Real5roleUI reopened,19Googlecalls unchanged; post-ACL backup ba33c28b-2cf2-4ad7-b9b8-c50c69ad08df and3SQLitecoldrestorePASS. See gemini-live-deployment/run_20261019_0013/acl-live-readback.json. Original113tasks unchanged.


<!-- EXECUTION_MONITOR_CURRENT -->
## Execution Monitor — extension, không kiểm toán lại113tasks

- [x] Inspect real source/trace/session/NativeACL và run7d528511actor7.
- [x] Typed projection, additive code-only telemetry, canonical agent outputs, history APIs.
- [x] Rails/SVG Monitor, detail/timeline/replay/history/CC integration.
- [x]196Windows/127Linux regression và18monitor tests PASS.
- [x] Backup restore221PGtables/assets/config +3SQLite, backward Gateway schema compatibility.
- [x] Final immutable-image Playwright suite + source/image/runtime parity refresh (25checks PASS).
- [x] Owner approval exact Core/Gateway deployment preview61e1719f persectionXV.
- [x] Deploy approved pair and public QuickTunnel Playwright acceptance (30servingchecks/5rolesPASS).
<!-- END_EXECUTION_MONITOR_CURRENT -->

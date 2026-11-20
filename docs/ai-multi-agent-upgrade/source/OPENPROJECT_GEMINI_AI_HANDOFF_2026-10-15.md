# QLDAPM — Hồ sơ kiến trúc OpenProject tích hợp Gemini

Ngày lập: **15/10/2026**, múi giờ Asia/Bangkok. Ngôn ngữ: tiếng Việt.

## 1. Mục đích và độ tin cậy

Tài liệu độc lập này dành cho một AI/kỹ sư khác đánh giá hệ thống hiện có và đề xuất nâng cấp. Đây là bản mô tả **AS-IS**, không phải cam kết mọi tính năng đều hoạt động hoặc đã triển khai production.

Nguồn: đọc source, manifests, kiến trúc và checkpoint trong repository. Trạng thái triển khai và kết quả thử nghiệm dưới đây được dẫn từ checkpoint gần nhất; lượt lập tài liệu **không kiểm tra lại container, không gọi Gemini, không chạy test và không ghi dữ liệu nghiệp vụ**. Không chứa mật khẩu, API key, token, cookie hay private configuration.

Workspace authoritative: `D:\AI project\QLDAPM chat`. Thư mục legacy `C:\Users\LUIM\Documents\QLDAPM` chỉ là pointer.

Ba khái niệm cần phân biệt:

1. **OpenProject local:** tracker đang dùng để quản lý công việc.
2. **Gemini Assistant:** phần mở rộng cho tracker, đã nâng cấp trên staging.
3. **Sản phẩm QLDAPM theo 53 User Story:** backlog thiết kế một ứng dụng quản lý dự án; việc đã nhập ticket không chứng minh sản phẩm đó đã được lập trình.

Jira Cloud là hệ thống riêng. Không suy từ dữ liệu nhập/mapping rằng có đồng bộ hai chiều thường trực, hoặc Gemini chat có quyền thao tác Jira.

## 2. Môi trường và trạng thái triển khai

| Thành phần | Main/live local | Staging nâng cấp |
|---|---|---|
| OpenProject UI | `http://localhost:8088` | `http://localhost:18091` |
| Gateway | loopback `8090` | loopback `18092` |
| OpenProject core | Official 17.9.1, chưa promote bộ nâng cấp mới | Core có overlay QLDAPM, RBAC, AI UI, gates, cây công việc |
| Gemini business assistant mới | Không được coi là đã triển khai trên live | Đã nghiệm thu các luồng được ghi trong checkpoint |
| Chính sách PM-only-write mới | Chưa áp dụng đồng nhất như staging | Đã áp dụng |

Image pair mới nhất **theo DATES checkpoint**, không phải kiểm tra runtime trực tiếp trong lượt này:

```text
Staging core:
sha256:1cdd2590d6f31384eacf93bd504b421288c7d0a7ef37a137e1e2b8ec009dd87a
Staging gateway:
sha256:79bc0c4c67d606b79936a7324040a7543c1b00a4518337a3e9270af0cc62ff3e
Main core:
sha256:2beeecac788d4f423c46a95ffbd04e6479491938b9924b610e9f47d81a38303c
Main gateway:
sha256:7190fcc265f54880c06927b846982b2c2770109790df0a389d7932637b8641a3
```

Staging project đang tích hợp: `qldapm-local`, native project ID 3. ID project live có thể khác; không dùng ID staging để ghi live.

Host là Windows + Docker Desktop/WSL2. Dịch vụ local phụ thuộc máy bật, Docker hoạt động và kết nối mạng. Chưa phải kiến trúc HA/production được qualification đầy đủ.

## 3. Sơ đồ tổng thể

```text
Người dùng
  │ OpenProject login/session + CSRF
  ▼
OpenProject Rails UI :18091
  ├─ Work Packages, hierarchy, Boards, gates
  └─ QLDAPM AI controller / preview / kết quả / permissions
          │ authenticated signed UI bridge, actor-bound
          ▼
Python Gateway :18092
  ├─ REST / MCP → Service dùng chung
  ├─ Native identity + role/effective permissions
  ├─ Proposal / consent / target scope / idempotency / receipts
  ├─ SQLite: runs, audit, proposals, requests, quota, jobs
  └─ Isolated AI worker
          │ Google Gen AI SDK, bounded requests/quota
          ▼
       Gemini
          │ chọn function + arguments; không tự có credential/quyền ghi
          ▼
  Service kiểm tra lại → OpenProject API/core mutation → PostgreSQL
          │ native readback + receipt
          └─────────────────────────────→ UI kết quả từng thao tác

Nhánh riêng của nền tảng Gateway:
MCP/REST → fixed jobs → local broker/operator → isolated runner
(không phải tập tools của Gemini business chat hiện tại)
```

OpenProject/PostgreSQL là nguồn sự thật nghiệp vụ. SQLite của gateway là trạng thái điều phối và audit, không thay database tracker.

## 4. Cấu trúc repository quan trọng

Các đường dẫn dưới đây tính từ workspace authoritative:

```text
architecture.md                         Kiến trúc tổng, gồm cả đề xuất sản phẩm và lịch sử
AGENTS.md                               Quy tắc vận hành repository
openproject/
  README.md, VALIDATION.md               Runbook nền và phạm vi xác minh
  compose.yml, Caddyfile                 Stack main OpenProject
  upstream-lock.json                    Pin upstream
  Manage-OpenProject.ps1                 Setup/start/stop/backup/restore nền
  scripts/                              Scripts tích hợp/import/vận hành
  upstream/                             Tài nguyên upstream
  development/core/                     Checkout/fork OpenProject phục vụ build
  ai/
    README.md, CHECKPOINT.md             Entry point; có nhiều đoạn lịch sử
    DATES_CHECKPOINT_2026-10-15.md        Trạng thái mới nhất về intent/ngày/runtime
    RBAC_CHECKPOINT_2026-10-15.md         PM-only-write và gaps kiểm thử
    BUSINESS_COMMANDS.md                 Hướng dẫn câu lệnh
    gateway/                            API, agent loop và điều phối
    core/overlay/                       Thay đổi Rails được ghép vào core
    core/*.rb                           Native policy/UI/integration test và helpers
    tests/                              Python regression + staging harness
    artifacts/                          Logs, receipts, ảnh nghiệm thu; không phải runtime DB
    compose.yml                         Gateway main
    stage.yml, deep-ai.stage.yml         Staging core/DB và gateway/UI bridge
    gemini-free.stage.yml               Overlay cấu hình provider staging
    Dockerfile, Dockerfile.gateway-patch Build gateway
    requirements.txt, requirements.lock.txt
    openapi.json, mcp-tools.json         API/tool exports; phải theo cùng source
    broker.py, runner.py                 Fixed jobs và sandbox
    operator_state.py                   Private operator bridge, single-OS state access
    release.py, Release-OpenProjectAI.ps1
    Manage-OpenProjectAI.ps1             Vòng đời AI và operator actions
    Start-OpenProjectMCP.ps1             MCP stdio/client wrapper
    jira_sync*.py, JIRA_SYNC_RUNBOOK.md  Nhánh integration riêng, không phải Gemini tools
```

Không coi checkout/fork là sạch mặc định: checkpoint gần nhất ghi có thay đổi RBAC chưa commit. Không reset/stash/clean hàng loạt để bắt đầu nâng cấp.

## 5. Stack và trách nhiệm module

Nền main: OpenProject 17.9.1, Rails/Angular từ upstream; PostgreSQL 17, memcached, worker/cron, Hocuspocus, Caddy. Staging Compose có cấu hình riêng, không hoàn toàn giống stack main.

Gateway Python dùng `mcp==1.29.1`, `starlette==1.6.0`, `pydantic==2.13.4`, `uvicorn==0.52.4`, `httpx==0.28.1`, `google-genai==2.30.1` theo `requirements.txt` đã đọc. Đây là versions của dự án, không khẳng định versions mới nhất trên thị trường.

| Module gateway | Trách nhiệm |
|---|---|
| `app.py` | HTTP routes, authentication, UI bridge, MCP transport |
| `service.py` | Dispatch chung; validate; native read/write; preview/confirm; readback |
| `catalog.py` | Tool descriptions và typed business parameters |
| `permissions.py` | Host role ceiling và mapping native permissions |
| `native.py` | OpenProject API client, identity/project binding |
| `bridge.py` | Xác minh assertion UI, chống replay |
| `gemini.py` | Provider policy, SDK, tool loop, projection dữ liệu, quota và output |
| `ai_worker.py` | Worker subprocess, consent/scope, timeout và progress |
| `presentation.py` | Nhận diện intent/ID, giải thích và hiển thị receipts bằng lời |
| `store.py` | SQLite state, idempotency, proposals, audit, quota, jobs/runs |
| `workspace.py` | Sandbox workspace và giới hạn đường dẫn |
| `local_operator.py`, `stdio.py` | Private operator commands và MCP stdio |

Core overlay quan trọng:

- `app/controllers/qldapm_ai_controller.rb`, `app/services/qldapm/ai_bridge.rb`: AI UI và bridge.
- `app/views/qldapm_ai/`, `app/helpers/qldapm_ai_helper.rb`: form, preview trước/sau, progress, kết quả nổi bật, permissions.
- `app/services/qldapm/mutations.rb`: strict mutation allowlist và native receipts.
- `app/models/qldapm/gate_policy.rb`, `gate_actions.rb` trong services: nghiệp vụ gate, evidence, reviewer, approval.
- `app/models/qldapm/{rbac,permission_ceiling,board_permissions}.rb` và concerns ghi: chặn đường ghi vượt policy ở core.
- `app/controllers/concerns/qldapm_work_package_tree.rb`, views `qldapm_work_packages/`, tree hook: hierarchy và root pagination.
- `lib/api/v3/qldapm/gates_api.rb`, routes/initializers: API tích hợp.
- Migrations: gate data, insight snapshots và mutation receipts. Nâng cấp cần kiểm tra schema thực tế trước migrate.

## 6. Luồng xử lý một yêu cầu Gemini

1. Người dùng nhập prompt, chọn có cho phép thao tác thông thường trong lượt hay chỉ xem đề xuất.
2. Rails dùng session hiện tại tạo yêu cầu bridge gắn actor; không lấy actor do model tự khai.
3. Gateway xác minh danh tính, project membership, native permissions và policy host.
4. Worker lấy tools được phép; chỉ gửi tập business tools và business projection được chấp thuận cho Gemini.
5. Model đọc công việc/options khi cần rồi gọi typed tool. Model không có shell, SQL, Docker socket hoặc API key trong prompt.
6. Host kiểm tra tool, arguments, intent yêu cầu ghi, ID scope, role và lock version.
7. Không có consent phù hợp: tạo proposal gắn actor/hash/expiry để người dùng xem và xác nhận. Có consent phù hợp: thực hiện routine write được yêu cầu trong lượt, trong scope.
8. Native core vẫn kiểm tra permission, workflow, gate và concurrency; provider consent không vượt các điều kiện này.
9. Gateway đọc lại native kết quả, lưu receipt và cập nhật UI theo từng thao tác. Partial failure không bị biến thành thông báo thành công toàn bộ.
10. Timeout/unknown write: giữ receipt/trạng thái, reconcile bằng bằng chứng; không tự gửi lại thao tác ghi hoặc đổi idempotency key để thử mù.

Mỗi run hiện gửi prompt hiện tại; **chưa tự ghép toàn bộ hội thoại cũ**. Vì vậy “việc đó/như trên” có thể mất đối tượng giữa hai lượt.

## 7. Khả năng thực sự của Gemini business chat

Gemini có đúng 9 function contracts trước khi lọc quyền:

`identity`, `list_work_packages`, `get_work_package`, `analyze`, `get_project_options`, `create_work_package`, `update_work_package`, `comment`, `transition`.

| Nhóm | Hiện hỗ trợ | Giới hạn |
|---|---|---|
| Đọc | Tiêu đề, mô tả nghiệp vụ, comment, quan hệ, scalar custom fields được phép | Đọc on demand, không tự nạp mọi dữ liệu vào mọi lượt |
| Tìm/list | Subject query, parent ID, offset, limit | 1–30 mục/trang; không có dedicated assignee-filter argument trong contract |
| Phân tích | Counts/status/overdue, giải thích yêu cầu, nháp AC/test case/chia việc | Không chứng minh phần mềm đã được kiểm thử hoặc hoàn thành |
| Tạo | Epic/Task/Subtask; subject, description, type, parent, assignee | Options/native IDs thực; host cấp Source ID ổn định nếu thiếu |
| Sửa | Subject, description, assignee, start_date, due_date, priority | Không phải generic PATCH mọi field |
| Comment | Thêm nội dung, readback, chống lặp request | Text comment là dữ liệu, không phải authorization |
| Trạng thái | Native transitions | Không nhảy tùy ý hoặc bỏ điều kiện workflow/gate |

Chưa expose cho business chat: đổi parent/type của item hiện hữu, custom-field writes, estimate/time entry, percentageDone, dependencies/attachments, delete, quản trị tài khoản/quyền/workflow, code/test/deploy, tìm web hay Jira.

Catalog Gateway/MCP rộng hơn có code workspace, fixed test jobs, gate operations, insights và proposals. **Có trong catalog không đồng nghĩa Gemini được gọi.** Mỗi đường còn bị lọc role/native permissions. PM gateway cũng không có quyền server administration/deploy/role changes; local operator là đường riêng.

## 8. Quyền và workflow hiện hành trên staging

| Role | Đọc/phân tích | Comment | Ghi nghiệp vụ |
|---|---|---|---|
| PM | Có | Có | Có trong project, còn native validation/workflow/approval |
| BA / alias BA-PM | Có | Có | Không |
| BE / FE / QA | Có | Có | Không |

Checkbox consent không cấp thêm quyền. Assignee permission không đồng nghĩa được sửa assignment. Policy được kiểm tra ở tools lẫn đường ghi core/Boards; không chỉ ẩn nút UI.

Administrator staging là tài khoản native riêng, đã có checkpoint kiểm thử quyền quản trị; **chưa enroll Gemini/MCP** theo checkpoint admin. Không coi admin UI là một service identity mặc định cho agent.

Gate overlay bảo vệ evidence/checklist/revision/reviewer/approval và parent-child consistency. Có nguyên tắc reviewer độc lập, không tự duyệt; sửa nội dung liên quan làm approval cũ mất hiệu lực. Parent REVIEW/DONE hạn chế ghi child theo policy; comment thông thường vẫn được phép. Không suy số status live hoặc workflow Jira là workflow core staging: cần đọc đúng `gate_policy.rb` và native options.

Ghi chú lịch sử về non-PM được sửa công việc hoặc được cấp `manage_subtasks` không còn là policy hiện hành. Không chạy bootstrap cũ để “sửa” lỗi permission.

## 9. Hierarchy và ngày tháng

Work Packages mặc định trên staging là cây Rails server-rendered: Epic đóng ban đầu → mở Task → mở Subtask. Phân trang theo root, giữ trọn descendants cùng nhánh; giữ thứ tự nguồn import và items độc lập được phép thấy. Native table, saved filters, exports và editor vẫn có đường truy cập riêng.

Nguồn import ban đầu: 11 Epic + 53 Task + 265 Subtask = 329 work packages, 106 AC. Checkpoint date ghi baseline 333 được bảo toàn, người dùng thêm ID 446 nên tổng lúc đó là 334; **không coi số này là số hiện tại cố định** hoặc dùng 329 làm mục tiêu xóa dữ liệu mới.

Ngày dùng typed `start_date`/`due_date` nullable, chuyển sang native `startDate`/`dueDate`. Nếu yêu cầu cả hai thì cập nhật cùng một lần. Validate định dạng và start ≤ due. Native `/work_packages/{id}/form` preflight tính calendar normalization; readback so với kết quả native hợp lệ, preview/receipt giải thích thay đổi.

Ví dụ 10/10/2026 là thứ Bảy, native có thể chuyển start sang 12/10; chỉ đặt due date có thể làm start thay đổi theo duration đã giữ. Không ép ngày nghỉ bằng retry hoặc tự thay `ignoreNonWorkingDays`.

## 10. API, state và bảo mật

Các route hiện có: `POST /api/v1/commands`, `POST /api/v1/ai-runs`, `GET /api/v1/ai-runs/{id}`, `GET /api/v1/proposals/{id}`, `GET /api/v1/insights`, `GET /api/v1/openapi.json`; MCP HTTP `/mcp`, stdio wrapper; private signed bridge `POST /internal/ui`. `/health` trả tối thiểu. Machine API cần Bearer; UI bridge dùng xác minh chữ ký riêng. Không có MCP tool tự xác nhận proposal.

SQLite lưu: `tokens` (hash), `audit`, `requests`, `jobs`, `proposals`, `ai_runs`, `ui_nonces`, `gemini_usage`, `gemini_blocks`, `gemini_recovery`. Credentials native/key được giữ trong private runtime, không đưa vào Markdown/exports/model.

Private runtime nằm dưới `%LOCALAPPDATA%/QLDAPM/openproject-ai`; staging state và workspace được mount riêng. Không mở SQLite/WAL đang chạy trên Linux container bằng Windows SQLite. Dùng operator bridge/connection đúng Linux; backup bằng API nhất quán, không xóa WAL/SHM để xử lý lỗi.

Runs/proposals/history gắn actor; PM chỉ có project audit metadata được cấp, không mặc nhiên đọc chat riêng của người khác. Ticket/comment/code là untrusted data, không có quyền mở scope, đổi role hoặc tự duyệt.

Sandbox/broker có fixed operations, immutable snapshots, giới hạn tài nguyên, không Internet/secrets/live volumes/Docker socket trong runner. Operator approval là exact hash, có expiry và kiểm tra target. Đây là cơ chế nền tảng riêng, không biến Gemini business chat thành coding agent toàn quyền.

Ranh giới bảo vệ không chống được malware/agent có terminal toàn quyền cùng Windows user hoặc host administrator; muốn cách ly mạnh hơn phải tách OS identity và secret access.

## 11. Model, quota và giới hạn vận hành

- Model trong source: `gemini-3.5-flash-lite`; Google Gen AI SDK.
- Project provider đã dùng: `gen-lang-client-0020540057`; key giữ backend, không cần gửi lại cho AI khác.
- Theo checkpoint, user đã cho phép continuous authorization không expiry, chấp nhận chi phí; không còn gate proof Free một giờ của các tài liệu cũ. Điều này không thay đổi billing thực tế hoặc bỏ quota Google.
- Data scope: `project-business-content`; đọc nội dung nghiệp vụ được quyền, redaction; không mở code/profiles/secrets.
- Local limits theo checkpoint: 13 RPM / 225.000 TPM / 450 RPD, dựa trên 90% quota user cung cấp. Không coi đây là quota Google được API xác minh hoặc số lượt chat; countTokens/generation có thể tiêu tốn nhiều request.
- Prompt tối đa 8.000 ký tự; toàn run timeout 600 giây. Không còn hard cap 6 tools/batch/model turns/write-scope IDs.
- Quota phút: chờ có giới hạn trong deadline. Daily exhaustion/provider failure: báo trạng thái và giữ receipts; không reset ledger hoặc dùng key khác để né quota.
- Không có bảo đảm mọi biến thể tiếng Việt/English đều được hiểu. Intent/parser hiện có aliases `set`, `thêm deadline`, sửa ngày, chuyển role và plural IDs; title-only/pronouns vẫn không đáng tin bằng explicit IDs.

## 12. Kiểm thử đã có và khoảng trống

Kết quả sau là **lịch sử có artifact**, không phải test được chạy lại khi lập hồ sơ:

- Date/intent regression: 147 Windows PASS; Linux 143 PASS + 4 OS-only skip. Native PM date pair/clear/invalid range; non-PM denied; real Gemini date writes và browser preview/hủy có bằng chứng.
- RBAC: 5-role native/API/Gemini, core/Boards, privacy, replay và restart có bằng chứng. Real MCP BE PASS; PM/BA/FE/QA bị chặn bởi test Bearers hết hạn, chưa coi là PASS.
- Hierarchy: native/controller và browser Epic→Task→Subtask, root pagination/reload/navigation, bảo toàn dữ liệu đã nghiệm thu.
- Restart date release: giữ ledger/receipts/config/credentials; source-image parity có artifact.
- Full legacy UI gate suite có 4 kỳ vọng BE write không còn hợp policy; chưa coi full suite xanh.
- Date API confirmation execution test bị automatic approval review chặn, không có lý do chi tiết; đã thử browser preview/reject, không bypass. Chưa chạy thêm real reassignment acceptance trong lượt date fix.
- Chưa có sealed production qualification mới, live promotion hay full production upgrade/restore acceptance cho pair hiện tại.

Artifacts tham khảo trong `openproject/ai/artifacts/`: `dates-unit-final.log`, `dates-linux-final.log`, `dates-ui-final.log`, `dates-stage.json`, `dates-restart.json`, `dates-image-parity.json`, `dates-success-browser.png`, `dates-preview-browser.png`; các checkpoint RBAC/hierarchy chỉ đến logs riêng.

Python unit suite thường chạy từ `openproject/ai` bằng `.venv/Scripts/python.exe -m unittest discover -s tests -v`. Native Ruby tests cần đúng image/DB fixture. Staging harness có thể tạo/ghi/xóa fixture; không chạy mù hoặc chạy trên live, không chạy lại manifest đã cleanup. Không chạy các suite mutation song song.

## 13. Vận hành, rollback và đọc checkpoint

Trước nâng cấp: đọc README/CHECKPOINT mới nhất, xác minh image/config/schema/project IDs và active runs/jobs; backup đúng môi trường. Stage Compose có seeder, nhưng seeder không phải công cụ restart thường ngày. Dùng image lock hiện hành để tránh downgrade bằng `.env`/tag cũ.

Rollback phải xét core+gateway compatibility, native schema/capability, config và current receipts. Giữ ledger hiện tại; không restore state cũ làm mất usage/receipt, không mở lại non-PM-write. Full live rollout cần freeze source, source/image parity, qualification/restore bằng chứng mới và operator approval; test staging không tự cấp quyền promote.

Thứ tự đọc hồ sơ nguồn khi được cấp repository:

1. `openproject/ai/README.md` và đầu `CHECKPOINT.md`.
2. `DATES_CHECKPOINT_2026-10-15.md` — mới nhất về runtime/intent/dates.
3. `RBAC_CHECKPOINT_2026-10-15.md`, `RBAC_AUDIT_2026-10-15.md`, `ADMIN_ACCESS_CHECKPOINT_2026-10-15.md`.
4. `BUSINESS_CHECKPOINT_2026-10-15.md`, `BUSINESS_COMMANDS.md`, `RELIABILITY_CHECKPOINT_2026-10-15.md`.
5. `HIERARCHY_CHECKPOINT_2026-10-15.md`, `CONTINUOUS_CHECKPOINT_2026-10-15.md`, `UNLIMITED_CHECKPOINT_2026-10-15.md`.
6. Source gateway/core overlay, exports/tests/artifacts tương ứng; `architecture.md` để hiểu bối cảnh rộng.

Tài liệu là append-history và có mâu thuẫn lịch sử (ví dụ deadline 120s trong phần cũ, source hiện tại 600s). Ưu tiên source hiện hành + checkpoint mới nhất của đúng phạm vi; không gom mọi câu “PASS/READY” lịch sử thành chứng nhận release hiện tại.

## 14. Bài toán cần AI khác đưa phương án nâng cấp

Mong muốn của chủ dự án: giao việc bằng ngôn ngữ tự nhiên chính xác hơn, bớt hỏi lại khi đủ dữ liệu; có thể làm nhiều thao tác phù hợp quyền; preview dễ đọc; kết quả nổi bật và nói rõ đã làm/không làm được gì; nhận biết đúng Epic/Task/Subtask và ngữ cảnh nghiệp vụ.

Các hướng cần đánh giá, **chưa phải tính năng đã triển khai hoặc phương án được duyệt**:

1. Ngữ cảnh hội thoại nhiều lượt: định danh đối tượng, phân biệt ý định mới với lệnh cũ, cập nhật context theo native dữ liệu mới; không tự replay write.
2. Task planning/clarification: nhận biết trường thật sự thiếu, phân biệt thiếu dữ liệu với thiếu permission/workflow/quota, hỏi lại đúng một vấn đề cần thiết.
3. Tool coverage: ưu tiên nghiệp vụ thiếu như đổi parent, custom fields, estimates, dependencies nếu có nhu cầu; phải đi đủ schema → gateway → core → preview/receipt → tests, không chỉ sửa prompt.
4. Search/context retrieval: lọc đa điều kiện, pagination, giới hạn dung lượng/context, provenance; tránh nạp cả dự án mỗi lượt hoặc lộ dữ liệu ngoài quyền.
5. Write orchestration: dependency giữa các bước, lock conflicts, partial completion, quota resume, durable receipts và explicit retry/reconcile.
6. UX: phân biệt đang chạy/đang chờ quota/cần thông tin/cần duyệt/thất bại; preview bằng lời kèm before-after, kết quả native và đường dẫn công việc.
7. Evals: bộ câu lệnh tiếng Việt/English thực tế cho read/create/update/date/comment/transition, phủ 5 roles, multi-intent, ambiguity, invalid workflow, quota, restart và prompt injection.
8. Release readiness: thu gọn checkpoint lịch sử, cập nhật tests theo RBAC, hoàn tất MCP identities và production qualification trước live.

Yêu cầu đầu ra cho AI đề xuất: phân biệt root cause đã có bằng chứng với giả thuyết; đưa phương án nhỏ nhất đủ giải quyết, modules bị ảnh hưởng, migration, acceptance criteria, test plan, rollout/rollback và tác động quota/chi phí. Không gợi ý “toàn năng” bằng bỏ quyền, bỏ xác nhận, bỏ native gates hoặc cho model shell/admin chung.

## 15. Giới hạn của chính hồ sơ này

Đây là snapshot tài liệu/source ngày 15/10/2026; dữ liệu người dùng, quota còn lại và runtime có thể đổi ngay sau đó. Không kèm toàn bộ source hoặc secret runtime. AI chỉ nhận file này đủ để đề xuất kiến trúc sơ bộ; muốn đưa patch đúng phải được đọc source/tests mới nhất và kiểm tra môi trường tương ứng.

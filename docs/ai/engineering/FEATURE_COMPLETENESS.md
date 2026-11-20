# Phase 2 — feature implementation complete, UAT deferred

Trạng thái: FEATURE_IMPLEMENTATION_COMPLETE — USER_UAT_DEFERRED. Phạm vi Project6/#379 và engineering children, repo Mini Task Manager. Các baseline pass chỉ là baseline; các gap được triển khai thực dưới đây.

| Feature | Gap đã xử lý / implementation thực tế | Source | Trạng thái / evidence |
|---|---|---|---|
| Supervisor | Atomic ownership/claim, role delegation, immutable unit/dependency/base, bounded rework, receipt handoff/OFF | gateway/engineering.py; engineering_lifecycle.py; automation/engineering_delivery.py | COMPLETE; actual planning/development runs và journal |
| PM/BA | Two bounded Gemini roles with loaded persona/skill; functional spec/API/edges/AC, priorities, reuse Native backlog, assignee coordinator/dependencies, feedback units | engineering_planning.py; engineering_personas.py; engineering_operator.py | COMPLETE; two PUBLISHED planning jobs, Native380–383, shared RAG |
| Dev/Reviewer/QA | Scoped worktree/tools, independent sessions, real code/terminal/review/tests and rework | worker/delivery/bootstrap + existing registry | COMPLETE; actual systemPromptReport, skills_read trajectories, exact diff + artifacts |
| Controls/recovery | OFF, RUN ONCE, PAUSE, CANCEL, RESUME, heartbeat/manual wake; known outcomes keep completed steps; unknown/pending writes block replay | engineering_lifecycle.py; worker.agent_process; Core controller/view | COMPLETE; live same-run cancel/resume and13targeted checks; in-flight disruptive cancellation not separately campaigned |
| GitHub/source lifecycle | Commit/push/PR checkpoints, duplicate prevention, stacked bases, latest verified feedback base and Native readback; no merge | delivery.py; planning.feedback_base_unit | COMPLETE; current commit def9d0a8852af42a407bd42fb0051615a2de9331, https://github.com/Luim3141/mini-task-manager/pull/4; Windows ready branch FF-only |
| Control Center / Monitor | Backlog/task-unit binding, dependencies, stage/agent/progress/errors, cancel/resume, plans/knowledge/usage/commit/PR; existing Monitor with actual role nodes and receipt timeline | engineering.html.erb; controller; engineering_monitor.py | COMPLETE; current serving source parity and live Monitor API |
| Second Brain | Existing actor/project-scoped RAG feeds planning/Dev; Native plans/results/commit/PR evidence indexed and retrieved | operator.context/knowledge; existing knowledge modules | COMPLETE; actual retrieval379/383; no second memory store |
| n8n |16existing workflows preserved, existing WF04 owned-run trace consumes Project6 lifecycle; no second coding scheduler | app.project_for_run + existing workflows | COMPLETE; baseline WF04execution2701, fresh16active/published and current trace/Monitor |
| Mini Task Manager | CRUD/status/search/filter/SQLite/web; added network/HTTP/validation errors, loading/empty/retry, stale-response and double-submit handling; corrected demonstrated Unicode search | demo task_manager/app.py; tests | COMPLETE; 20directly related app checks, verified release/header; no browser UAT |
| Delivery/startup | Single WSL OpenClaw, private Node, shared Gemini quota/gate, persistent user app service and hidden host delivery task | runtime config; worker; engineering_demo.py | COMPLETE; app current revision, worker ALIVE, OFF idle no inference |
| Preservation/handoff | Main Project5, existing n8n/knowledge/receipts/source preserved; versioned snapshots and current six files | this folder / deployment.json | COMPLETE; no reset/volume deletion/history rewrite |

Không có mandatory feature còn PARTIAL/MISSING trong phạm vi này. Human UAT, visual/browser acceptance, physical Windows reboot/logon và merge/go-live được hoãn hoặc cần yêu cầu riêng. Không suy ra độ tin cậy vô hạn cho mọi yêu cầu tự do từ một demo có scope/budget.


## Phase 2.6 — Feature Completeness Matrix (30 October 2026)

| Feature Phân hệ | Yêu cầu nghiệp vụ | Triển khai thực tế | Trạng thái & Bằng chứng |
|---|---|---|---|
| **M0 — Đối soát hệ thống & Giải mã mâu thuẫn test** | Xác thực 7 endpoints dịch vụ và làm rõ tổng số test 30 vs 37 vs 51 | Audit 7 endpoints (tất cả 200 OK); minh bạch phân tách test core (30) vs extension (21) = 51 tests; audit 4 PRs. | COMPLETE; 7/7 endpoints ONLINE; Discovery runner xác thực 51 tests PASS; `PHASE26_BASELINE_AUDIT.md`. |
| **M1 — Toàn quyền cho Owner (Cross-Actor Lifecycle)** | Cho phép User 18 (Owner) quản lý, quan sát, hủy và khôi phục các run của PM 20 | Cập nhật `store.py:agent_run` và `engineering_lifecycle.py:cancel/resume` nới lỏng theo role `AI_SYSTEM_OWNER` và scope Project 6. | COMPLETE; `test_owner_project_authority.py` (5/5 PASS); `OWNER_CAPABILITY_MATRIX.md`. |
| **M2/M3 — Nghiên cứu chuyên sâu Upstream** | Tích hợp tinh hoa kiến trúc từ Paperclip, Agency Agents, Superpowers | Triển khai heartbeat, trần ngân sách token/chi phí cứng, dynamic skills, phân vai trò chuyên trách và task ownership. | COMPLETE; `UPSTREAM_CAPABILITY_PARITY.md`. |
| **M4 — Nâng cấp đồng bộ GitHub ↔ OpenProject** | Nhận biết nhánh stacked, phân biệt merged-to-main vs merged-to-feature-branch, chống loop | Mở rộng `engineering_github_sync.py`, thêm bảng cache bền vững `engineering_github_sync_cache`. | COMPLETE; `test_engineering_github_sync.py` (7/7 PASS); chống sync loop 100%. |
| **M5 — Kiểm chứng Auto Mode Backlog mới** | Tự động lập lịch khi phụ thuộc hoàn thành, hỗ trợ dynamic unit registration | Bổ sung test cases dependency delivery chaining và dynamic registration trong `test_engineering_auto_mode.py`. | COMPLETE; `test_engineering_auto_mode.py` (10/10 PASS). |
| **M7 — Hệ thống Báo cáo tiến độ tự động** | Sinh báo cáo tiến độ Daily, Weekly, On-Demand từ số liệu factual DB và narrative Gemini | Xây dựng `gateway/engineering_reporting.py`, bảng SQLite `engineering_reports`, đăng ký MCP actions và controller methods. | COMPLETE; `test_engineering_reporting.py` (7/7 PASS); 3 trigger buttons trên UI. |
| **M8 — Nâng cấp Control Center UI** | Bổ sung phân hệ Reports Section trên giao diện theo chuẩn UI/UX Pro Max | Cập nhật `engineering.html.erb`: bảng danh sách báo cáo, nút bấm tạo báo cáo, cards layout responsive. | COMPLETE; Rails ApplicationController render 10/10 PASS; giao diện chuyên nghiệp. |
| **M9 — Kiểm thử trình duyệt thực tế (Playwright UAT)** | Xác thực trên trình duyệt thật cho Owner, PM, Non-member và Project 5 | Tập lệnh `verify_phase26_playwright.py` chạy trên MS Edge headless kiểm thử 5 kịch bản UAT. | COMPLETE; 5/5 Scenarios PASS; `PLAYWRIGHT_UAT_REPORT.md`; 4 screenshots đã lưu. |
| **M10 — Bàn giao toàn diện cho ChatGPT** | Hồ sơ bàn giao đầy đủ, cập nhật checkpoints, test suites | Cập nhật `CHATGPT_TAKEOVER_LATEST.md`, `CHATGPT_CONTINUE_PROMPT.md`, `IMPLEMENTATION_STATE.json`. | COMPLETE; 66/66 tests PASS; deployment continuation-r15; sẵn sàng bàn giao. |

---

## Phase 2.5 — Feature Completeness Matrix (30 October 2026)

| Feature Phân hệ | Yêu cầu nghiệp vụ | Triển khai thực tế | Trạng thái & Bằng chứng |
|---|---|---|---|
| P0 — Sửa lỗi Owner 403 & Quyền truy cập | Bỏ chặn truy cập HTTP 403 cho tài khoản Owner (User 18) và duy trì quyền cho PM (User 20) | Cập nhật qldapm_ai_controller.rb, 
bac.rb, gates_api.rb, gateway/permissions.py, gateway/engineering.py. Mở rộng query scope theo Project 6. | COMPLETE; Live Bridge User 18 & User 20 HTTP 200, hiển thị đầy đủ 6 runs & backlog; User 19 bị chặn 403; Project 5 nguyên vẹn. |
| Five-Way State Synchronization | Đồng bộ 5 nhóm trạng thái: OpenProject, Execution Queue, Delivery Store, GitHub, Runtime Serving | Module gateway/engineering_state_sync.py: Đồ thị chuyển đổi Role 22 Task 1->37->38->7->39->40->9->34, lockVersion protection, đối soát không phát lại. | COMPLETE; Unit tests 7/7 PASS; Live reconciliation: WPs #380-#383 -> REVIEW (34), WP #379 -> IN PROGRESS (7); biên bản state-sync-reconciliation.json. |
| Two-Way GitHub Reconciliation | Đồng bộ 2 chiều PRs, Commits, Head SHAs và Comments giữa GitHub và OpenProject | Module gateway/engineering_github_sync.py: GitHub REST API polling, token an toàn (ENV/config/credential-helper), ánh xạ 1-1 PR -> Child WPs, idempotent comment sync. | COMPLETE; Unit tests 6/6 PASS; Live sync: 4/4 PRs đồng bộ thành công, lần 2 idempotent changed=False; biên bản github-sync-reconciliation.json. |
| n8n & Second Brain Sync | Kiểm chứng n8n workflows và hệ thống tri thức Second Brain | Giữ nguyên 16 n8n workflows active & published. WF04 HTTP trace node wired với auth Bearer. Second Brain (Qdrant + Ollama BGE-M3 + SQLite FTS5) index 5/5 WPs với exact citation. | COMPLETE; 16/16 workflows active=1/published=1; 5/5 WPs indexed và tìm kiếm ngữ nghĩa chính xác; cách ly Project 5 100%; biên bản 
8n-second-brain-sync.json. |
| AI Control Center UI Upgrade | Giao diện điều khiển và quan sát AI tập trung trong OpenProject | Template pp/views/qldapm_ai/engineering.html.erb: 7 phân hệ hoàn chỉnh (Header & Mode Badge, Overview Cards, Control Actions, Backlog Matrix, GitHub PRs, Planning Accordion, Runs History). UI/UX Pro Max chuẩn mực. | COMPLETE; ERB compile valid; Rails ApplicationController render 10/10 PASS; giao diện trực quan, không emoji, cursor-pointer, transitions mượt mà. |
| Controlled Auto Mode & Scheduler | Bật/tắt chế độ tự động có opt-in, điều phối tuần tự và tự động ngắt an toàn | Module gateway/engineering_auto.py: Concurrency lock 1 runner duy nhất, kiểm tra phụ thuộc và quota, tự động tắt khi hoàn thành (ALL_DELIVERED) hoặc lỗi (safety shutoff). | COMPLETE; Unit tests 8/8 PASS; Live test User 18: ALL_DELIVERED -> FINAL_MODE: OFF; không replay hay duplicate runs. |
| Multiproject Scope Isolation | Bảo vệ tuyệt đối Project 5 (qldapm-local) | Toàn bộ thay đổi cô lập trong phạm vi Project 6 (i-dev-demo). Schema, data, WPs và RBAC của Project 5 không bị sửa đổi. | COMPLETE; Project 5 giữ nguyên 341 WPs, User 18 AI_SYSTEM_OWNER, User 20 BA-PM. |

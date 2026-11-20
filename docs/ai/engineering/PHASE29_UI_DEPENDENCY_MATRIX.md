# MA TRẬN PHỤ THUỘC GIAO DIỆN VÀ API CONTRACT — PHASE 2.9 (UI DEPENDENCY MATRIX)

**Dự án:** QLDAPM AI Command Center  
**Phiên bản:** Phase 2.9  
**Mục tiêu:** Cố định hợp đồng API Backend (Backend Contract Freeze), đảm bảo 100% các thành phần UI mới gọi đúng endpoint, đúng method, đúng actor permission và xử lý lỗi nhất quán.

---

## 1. Bảng ánh xạ thành phần UI vào Backend Contract

| UI Component | Data Source | Existing Endpoint | HTTP Method | Authorized Actor | Input Payload | Output Schema | Side Effect | Loading / Error Handling |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| **Mission Control: Header & Status** | Gateway Status | `bridge("engineering_status")` | GET / Render | `AI_SYSTEM_OWNER`, `PM` | `{}` | `{mode, active_run_id, worker, tasks, backlog, runs}` | Không | Skeleton loader; fallback hiển thị UNKNOWN |
| **Mission Control: Active Mission Card** | Work Package #379 & Current Run | `bridge("get_work_package", {id: 379})` | GET / Render | `AI_SYSTEM_OWNER`, `PM` | `{id: 379}` | `{id, subject, status, lock_version, ...}` | Không | Badge hiển thị `IN_PROGRESS` (chưa đóng) |
| **Pipeline Visualization: 8 Stages** | Run Execution Events & Stages | `engineering['runs'][0]['stages']` | GET / Render | `AI_SYSTEM_OWNER`, `PM` | N/A (Embedded) | Array of stage objects `{name, state, agent, duration, ...}` | Không | Hiển thị icon trạng thái, tooltips |
| **Control Actions: Mode Toggle (AUTO/OFF/PAUSE)** | Gateway Control API | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'engineering_control', arguments: '{"mode": "..."}'}` | Rendered view | Cập nhật `engineering_control` trong DB | Double-submit lock; Toast thông báo lỗi nếu 403 |
| **Control Actions: RUN ONCE** | Gateway Admission | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'engineering_run_once', engineering_unit: '...', engineering_task: '...'}` | Rendered view | Thêm run vào hàng đợi, lock unit | Disable button ngay khi click; Toast phản hồi |
| **Control Actions: CANCEL / RESUME** | Gateway Lifecycle | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'engineering_cancel'/'engineering_resume', arguments: '{"run_id": "...", "checkpoint_version": 1}'}` | Rendered view | Hủy hoặc tiếp tục execution run | Confirm dialog; Toast lỗi |
| **Control Actions: GitHub Sync** | GitHub Reconciler | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'engineering_github_sync', arguments: '{"repo": "Luim3141/mini-task-manager"}'}` | Rendered view | Cập nhật cache SQLite & comment OpenProject | Spinner loading; Idempotent (không spam comment) |
| **Agent Workforce: 6 Agent Cards** | Agent Personas & Active Runs | `engineering['agents']` & Trajectories | GET / Render | `AI_SYSTEM_OWNER`, `PM` | Embedded | Array of Agent definitions `{role, model, runtime, skills, status}` | Không | Card chi tiết; modal hiển thị skills khi click |
| **Backlog & Tasks Matrix** | Project 6 Tasks & Backlog Units | `engineering['tasks']` & `engineering['backlog']` | GET / Render | `AI_SYSTEM_OWNER`, `PM` | Embedded | Array of tasks `{id, subject, status, lock_version, unit, ...}` | Không | Client-side search, filter theo Priority/Status |
| **GitHub Delivery: 5 Stacked PRs** | GitHub PRs Reconciliation | `engineering['github_prs']` | GET / Render | `AI_SYSTEM_OWNER`, `PM` | Embedded | Array of PRs `{number, title, state, base_ref, head_sha, merge_target}` | Không | Link trực tiếp GitHub; Badge phân loại MAIN vs FEATURE |
| **Reports: Generation (Daily/Weekly/Snapshot)** | Reporting Generator | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'engineering_report_generate', arguments: '{"type": "daily"}'}` | Rendered view | Thêm bản ghi báo cáo vào `engineering_reports` | Loading spinner; thông báo thành công |
| **Reports: Schedule Modal Config** | Schedule API | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'engineering_report_schedule_update', arguments: '{...}'}` | Rendered view | Cập nhật cấu hình lịch chạy tự động | Form validation; hiển thị rõ `Asia/Ho_Chi_Minh` |
| **Notifications Bar & Dismiss** | Notifications API | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'engineering_notifications_dismiss', arguments: '{"id": 1}'}` | Rendered view | Xóa/ẩn thông báo | Tự ẩn sau khi dismiss |
| **System Integrations Status** | Health Checks Bridge | Core services health indicators | GET / Render | `AI_SYSTEM_OWNER`, `PM` | Embedded | Health statuses `{openproject, gateway, openclaw, n8n, qdrant, ollama}` | Không | Badge ONLINE / READY / FALLBACK |
| **Knowledge Center & Search** | Qdrant & FTS5 Second Brain | `POST /projects/ai-dev-demo/qldapm-ai/commands` | POST | `AI_SYSTEM_OWNER`, `PM` | `{tool: 'knowledge_search', arguments: '{"query": "..."}'}` | Rendered view | Truy vấn Second Brain | Hiển thị rõ `match_type: FTS_BM25 / DENSE` và citation |

---

## 2. Quy tắc bảo vệ tính toàn vẹn (Safety Guarantees)
1. **Không tạo API mock/giả:** Mọi tương tác nút bấm đều gửi payload JSON hợp lệ đến action `command` của `QldapmAIController`.
2. **Double-submit Protection:** Mọi form POST và nút hành động (Run Once, Sync, Report, Toggle Mode) đều có trạng thái disabled và indicator spinner khi đang submit.
3. **Session & CSRF Preservation:** Kế thừa đầy đủ `form_authenticity_token` từ Rails helper và session cookie `_open_project_session`.
4. **Không can thiệp ngoài Project 6:** Header controller kiểm tra cứng `engineering_project?` (`@project.id == 6 && @project.identifier == 'ai-dev-demo'`). Project 5 được bảo vệ tuyệt đối.

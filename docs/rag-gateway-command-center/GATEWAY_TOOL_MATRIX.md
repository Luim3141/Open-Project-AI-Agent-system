# Gateway / Telegram tool matrix — 13/11/2026

**Gateway reads: PASS trong scope đã chạy; command contracts: PASS cô lập; MAIN mutation: BLOCKED BY AUTHORIZATION.**
29 declarations / 22 read / 7 write, không mở rộng quyền. [Schemas](telegram-tool-schemas.json), [DTO/correlation IDs](main-integrations.json), [matrix đầy đủ input/output/permission](gateway-tool-matrix.json).

| Telegram tool | Gateway action | MAIN evidence |
|---|---|---|
| list_projects | identity (mỗi project đã pair) | READ_RETURNED |
| search_tasks | list_work_packages | READ_RETURNED |
| get_task_details | get_work_package | READ_RETURNED |
| get_project_options | get_project_options | READ_RETURNED |
| get_task_progress | observer_task_progress | READ_RETURNED |
| get_task_agent_runs | observer_task_progress | READ_RETURNED |
| get_current_agent | observer_task_progress | READ_RETURNED |
| get_run_details | observer_run_details | READ_RETURNED |
| get_run_errors | observer_run_details | READ_RETURNED |
| get_checkpoint_status | observer_run_details | READ_RETURNED |
| get_task_artifacts | observer_task_progress | READ_RETURNED |
| get_github_prs | observer_task_progress | READ_RETURNED |
| get_review_results | observer_task_progress | READ_RETURNED |
| get_qa_results | observer_task_progress | READ_RETURNED |
| search_knowledge | knowledge_search; mode answer → extract, không inference Gateway | READ_RETURNED |
| get_worker_status | observer_active(summary_only) | READ_RETURNED |
| get_queue_status | observer_active(summary_only) | READ_RETURNED |
| get_system_health | observer_active(summary_only) | READ_RETURNED |
| get_n8n_status | observer_active(summary_only) | READ_RETURNED |
| get_active_agents | observer_active(state/limit=50) | READ_RETURNED |
| get_blocked_tasks | observer_active(state/limit=50) | READ_RETURNED |
| get_pending_approvals | observer_active(state/limit=50) | READ_RETURNED |
| create_task | create_work_package → exact Gateway proposal approval | BLOCKED BY AUTHORIZATION |
| update_task | update_work_package → exact proposal approval | BLOCKED BY AUTHORIZATION |
| request_task_execution | engineering_run_once | BLOCKED BY AUTHORIZATION |
| resume_task | engineering_resume | BLOCKED BY AUTHORIZATION |
| pause_task | engineering_control(PAUSED) | BLOCKED BY AUTHORIZATION |
| set_execution_mode | engineering_control | BLOCKED BY AUTHORIZATION |
| request_github_sync | engineering_github_sync | BLOCKED BY AUTHORIZATION |

Gateway có15 REST paths trong [OpenAPI hiện hành](gateway-openapi.json); local MCP session thực initialize/tools-list/identity18/P6/unauth401 đã kiểm, 87 tools được token này nhìn thấy: [MCP](mcp-smoke.json). Số tool được liệt kê không có nghĩa có quyền thực thi mọi mutation. Chẩn đoán schema lần đầu dùng sai nested arguments/isError được giữ [tại đây](mcp-smoke-schema-diagnostic.json), không tính PASS.

Source routing: `openproject/ai/gateway/app.py`, `catalog.py`, `service.py`; callers `telegram-ai/app/tools.py`, Core controller và AiBridge. REST command body action/arguments/project_id; MCP tools có arguments object và project_id. Error paths giữ typed4xx/5xx, Retry-After/request ID. Controller/Bot không trở thành một control plane khác.

[Semantic read assertions](semantic-read-checks.json): #398 READY FOR RELEASE/AWAITING_OWNER_APPROVAL, current agent null, global active0/OFF, pending có398 không397, checkpoint27=11steps, completed run không resumable; reviewer/QA PASS là lịch sử. GitHub live PR15OPEN, statusCheckRollup rỗng không phải remote CI PASS.

OFF/AUTO/PAUSED/RUN_ONCE, resume-fencing, stale approval, replay/idempotency, role/actor/project spoofing, Native denial, queue/runtime errors và HTTP status contracts được chạy trong suite cô lập. Không click/chạy các mode mới trên MAIN; không cấp quyền thông qua tài liệu. API route inventory/source coverage còn lại kế thừa [206 dòng audit trước](../functional-audit/FUNCTIONAL_MATRIX.md), không nâng tất cả thành PASS mới.

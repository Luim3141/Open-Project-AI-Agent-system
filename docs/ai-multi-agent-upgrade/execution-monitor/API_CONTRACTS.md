# API đọc execution

**COMPLETE_ON_STAGING — 2026-10-19T19:59:52.412347+07:00**. [Serving deployment report](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md);30publicUI/API checksPASS. Qualification evidence below records pre-deployment validation.

| Route | Response | Security |
|---|---|---|
| GET /projects/qldapm-local/qldapm-ai/executions | HTML history | Native session + project view permission |
| GET …/executions.json | History schema v1 | Signed actor/project bridge |
| GET …/executions/:run_id | HTML Monitor shell | Native session/project checks |
| GET …/executions/:run_id.json | ExecutionMonitor schema v1 | Own run + fresh Native ACL/version |

Gateway commands: `list_execution_monitors(arguments={limit,offset,search,state,order})`; `get_execution_monitor(arguments={id})`. Catalog descriptions/export annotations readOnlyHint; dùng cùng HMAC UI bridge hoặc existing authenticated command surface, không bypass authentication. Browser không gửi actor/project làm authorization. UUID/typed scope và keys được kiểm tra tại Gateway.

History limit1..50(default10), offset≥0; order asc/desc allowlist; status allowlist. SQL values parameterized, ORDER only allowlisted. Response total/next_offset/items; rows chỉ chứa own request preview và metrics, không outputs/source body. Role hiện tại từ Native session.

Detail schema1: run_id,trace_id,actor_id,actor_role,project_id,request,state,terminal,mode,model,created_at,updated_at,duration_seconds,nodes,edges,events,metrics,sources,final_output,warnings. LIVE_GEMINI chỉ khi actual LIVE_SUCCESS receipts; MOCK_TEST chỉ MockTransport receipts; LOCAL_DETERMINISTIC từ local engine. Token missing=null, usage_complete phân biệt thiếu usage. Không suy chi phí USD.

Known permission/notfound bridge errors→403safe JSON, unavailable→503safe JSON; Native session expiry có thể redirect login. Client xử lý cả redirect/nonJSON/401/403/404, không giữ cached outputs. Cache-Control:no-store, detail noindex. STALE trả shell metadata và warning, request/nodes/events/sources/final_output bị ẩn. History không xác nhận source hiện còn hợp lệ; phải mở detail.


Post-deployment acceptance: [STAGING_DEPLOYMENT_REPORT](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md). Exact servingpair456c38f6/7d76c1eb;30publicchecksPASS, ledger517unchanged. Ownerapproval61e1719f preserved; previewfile remains the immutable approved plan, not current deploymentstate.

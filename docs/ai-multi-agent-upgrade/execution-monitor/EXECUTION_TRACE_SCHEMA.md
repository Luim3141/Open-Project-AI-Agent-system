# Execution trace v1

**COMPLETE_ON_STAGING — 2026-10-19T19:59:52.412347+07:00**. [Serving deployment report](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md);30publicUI/API checksPASS. Qualification evidence below records pre-deployment validation.

Contracts machine-readable trong `execution-event.schema.json` và `execution-monitor.schema.json` của run folder.

Event fields: schema_version1; event_id UUID; run_id/trace_id; event_type enum; optional agent_id/step_id; observed timestamp; monotonic stored sequence; status enum; receipt_id/phase/attempt/http_status/error_code theo allowlist. Extra fields bị từ chối. Không có raw prompts, request body, output hoặc provider payload. Error code chỉ uppercase identifier ≤80characters.

Storage: SQLite `execution_events(sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id UNIQUE, run_id, actor, project, document)`; index(actor,project,run_id,sequence), provider_receipt(actor,run_id). Admission/terminal và receipt transitions dùng deterministic event IDs để duplicate emission không tạo thêm row. Events đọc tối đa200/run, receipt tối đa200. Sequence là append order toàn store, có thể có khoảng trống trong từng run.

Events: REQUEST_RECEIVED,AUTHORIZED,QUEUED,PLANNING_STARTED,PLAN_CREATED,AGENT_ASSIGNED,AGENT_STARTED,MODEL_REQUEST_STARTED,MODEL_RESPONSE_RECEIVED,AGENT_COMPLETED,AGENT_FAILED,RETRY_SCHEDULED,REVIEW_STARTED,REVIEW_COMPLETED,RESULT_AGGREGATED,RESULT_AVAILABLE,PROPOSAL_CREATED,APPROVAL_REQUIRED,RUN_COMPLETED,RUN_FAILED. Chỉ emit tại lifecycle thực.

Legacy runs không backfill events. Timeline có thể chiếu timestamp + duration đã lưu trong provider receipts, ghi rõ origin RECORDED_PROVIDER_RECEIPT. Không chia đều tổng duration thành agent duration. Unknown timing là null. New per-agent outputs dùng AgentResult có run/task/actor/project/trace scope; kiểm tra lại trước projection. Reviewer chỉ xác minh reference/version/scope và deterministic constraints, không chứng nhận toàn bộ ý nghĩa nghiệp vụ.


Post-deployment acceptance: [STAGING_DEPLOYMENT_REPORT](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md). Exact servingpair456c38f6/7d76c1eb;30publicchecksPASS, ledger517unchanged. Ownerapproval61e1719f preserved; previewfile remains the immutable approved plan, not current deploymentstate.

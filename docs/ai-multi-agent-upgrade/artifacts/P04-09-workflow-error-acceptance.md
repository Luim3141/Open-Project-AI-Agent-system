# P04-09 accepted — 17Oct2026

Workflow error queue/history + UI thông báo nội bộ; không dùng email/SMS/cloud trả phí.

## 1. Tóm tắt kết quả
- Hoàn thành cơ chế bắt và lưu vết lỗi tự động cho toàn bộ workflow n8n (`qldapmManualStatus`, `qldapmDailyBrief`) thông qua workflow lỗi chuyên dụng `qldapmWorkflowErrors` (`workflow-errors.v1.json`).
- Không sử dụng email, SMS, hay bất kỳ cloud third-party trả phí nào. Toàn bộ thông báo lỗi được làm sạch (sanitized metadata only: `run_id`, `trace_id`, `workflow_id`, `execution_id`, `day`, `error_code`, `observed_at`) và chuyển giao an toàn vào Gateway nội bộ qua HMAC signed command.
- Raw stack trace và private error details (`P04_PRIVATE_RAW_ERROR_MUST_NOT_LEAVE_N8N`) được giữ hoàn toàn cục bộ trong private n8n execution store, không bao giờ lọt sang Gateway hoặc giao diện OpenProject.
- Năm role người dùng bản địa (6 BA-PM, 7 PM, 8 BE, 9 FE, 10 QA) nhận được thông báo lỗi sanitized theo phạm vi project trong lệnh `analyze` của UI nội bộ. Yêu cầu cross-project trả về danh sách rỗng (`cross_project_empty: true`).

## 2. Bằng chứng kiểm thử và thẩm định (Evidence)
- **Clone qualification (`docs/ai-multi-agent-upgrade/artifacts/P04-errors-clone.json`)**:
  - `passed: true`
  - Các checkpoint đạt: `backup_verified`, `published_error_workflow_and_field_only_bindings_verified`, `daily_schedule_and_five_native_roles_passed`, `clone_restarted`, `fresh_directory_restore_ready`, `startup_catchup_and_restored_five_native_roles_passed`, `actual_trigger_error_metadata_dedup_project_ui_verified`.
  - Induced actual trigger error: execution `mode: 'error'`, execution ID `45`.
  - Dedup kiểm chứng: gửi trùng lặp error event trả về cùng receipt, không tạo bản ghi mới hay kích hoạt lại.
  - `actual_five_role_ui`: 5/5 role nhận `native_authorized_notice: true`, `cross_project_empty: true`, `private_raw_error_absent_from_gateway: true`.
- **Staging provisioning**:
  - Cặp immutable candidate images được nạp thành công vào staging:
    - Gateway: `sha256:006b9c6cd8cec7f5e41cf7ae4fe9abae762475b7fd685d8dde66191f10554233`
    - Core: `sha256:8a42c7efe65d799dd2b4a259a8cacc567149a336a4dc366a830eb7c0f48bdfe8`
  - Trạng thái 7 container staging (`staging-gateway`, `staging-web`, `n8n`, `n8n-editor`, `db`, `local-backup`, `quick-tunnel`): 100% `Up` và `(healthy)`.
- **Staging workflow enrollment**:
  - `n8n_error_workflow.py` thực thi thành công: `published_version_id: "543eb013-1975-4a77-b5de-2b05a09057eb"`.
  - Đính kèm cài đặt error workflow vào cả `qldapmManualStatus` và `qldapmDailyBrief` qua REST settings patch (`nodes_connections_credentials_submitted: false`).
- **Bảo toàn dữ liệu và chi phí**:
  - PostgreSQL schema: 220 public tables + sequences (221 total) bảo toàn nguyên trạng.
  - Native business writes: 0.
  - Gemini API calls: 0 (bảng `gemini_usage` giữ nguyên 471 records).
  - Main environment (`localhost:8088`): nguyên vẹn, không chạm tới.

## 3. Trạng thái task
- Task P04-09: **DONE**
- Tiến độ tổng: **54/113 tasks DONE**
- Bước kế tiếp: Task P04-10 (Chính sách phục hồi n8n sau sự cố/khởi động lại máy và xử lý workflow gián đoạn).

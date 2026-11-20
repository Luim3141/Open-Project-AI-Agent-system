# Root causes and fixes — 22/10/2026

Trạng thái: sửa source và deploy Main; nghiệm thu Final Answer Gemini của image cuối còn BLOCKED_OWNER_ADDITIONAL_LIVE_APPROVAL. Không có Native mutation mới.

| Vấn đề | Bằng chứng / root cause | Sửa đúng tầng |
|---|---|---|
| Native CREATE chậm | Lần cũ #367: HTTP201 sau55.766s, client30s; worker/budget đã dừng. Fix90s đã có trong baseline4322, không phải thay đổi mới của đợt này. | Giữ Native CREATE theo deadline còn lại90s; GET/form vẫn30s; test5/30/55/75/>90s bằng virtual clock. Không retry POST. |
| Native commit nhưng worker lỗi | ai_runs chỉ có raw worker state; projection cũ partial và recovery cần operator. | business_runs additive SQLite tách provider/native/approval/synthesis/business outcome. Dispatcher hiện có đối soát READ-only tối đa3 probes/90s, backoff15/30s; exact source marker/project/author/parent/type/subject/description/assignee. |
| Receipt/audit và replay | Kết quả reconciliation và audit trước đây hai thao tác; POST thành công rồi readback403 có thể bị coi là chưa ghi. | Store.finish_reconciliation dùng BEGIN IMMEDIATE; post-commit readback lỗi luôn UNKNOWN. Native rejection400/401/403/404/409/412/422 có receipt NOT_APPLIED, replay trả lại lỗi và không POST lại. |
| Final Result | Model synthesis lỗi làm che Native outcome đã chứng minh. | Giữ ai_runs/error gốc, business outcome có audit riêng. Native proven hiển thị câu xác nhận yêu cầu và SYSTEM_GENERATED khi chưa có tổng hợp Gemini. Không giả model success. |
| History/Monitor/CC | Business Worker không có AgentRun và vắng trong Monitor dành cho Supervisor. | Actor/project-scoped history UNION, pagination/filter/order; Monitor Business Worker riêng, không tạo mutation DAG/agent giả; CC dùng cùng history. UI tách5 trạng thái, giữ source links/raw error. |
| Live lần đầu chưa hoàn tất | Run41d33283… trả4HTTP200/2generations nhưng GEMINI_INCOMPLETE_OR_BLOCKED_OUTPUT. Generation cuối có1493 output+thinking tokens so với cap1500. | Output cutoff là suy luận mạnh, finish reason cũ không được giữ nên không khẳng định MAX_TOKENS. Read engine chuyển Native preflight→one structured synthesis, hard1generation/2HTTP, cap3000. Provider loop thêm finish reason metadata; structured path đã có invalid-response diagnostics. |
| Live lần hai bị từ chối claim | Runb566b115… có structured provider response nhưng host reject exact scalar/path contract. Rejected JSON không được lưu, chưa xác định được riêng path/value nào sai. | ReadAnswer dùng citation IDs + typed facts(id,parent_id,assignee_id), đối chiếu toàn bộ với Native; source paths/hash do host tạo. IDs lạ, thiếu nguồn, parent/assignee sai vẫn deny. Generic output-validation error mới là INVALID_OUTPUT, không OFFLINE. Chưa live nghiệm thu fix này. |

## Source và callers

- gateway/business_runs.py (mới): lifecycle, exact proof, bounded recovery, scoped history/Monitor, one-turn Native read/synthesis và validation.
- gateway/service.py: queue/dispatcher, receipt rejection/readback, projection/Monitor/CC, explicit read mode và error mapping.
- gateway/store.py: additive business_runs, atomic reconciliation/audit, effective history. Native PostgreSQL không migration.
- gateway/ai_worker.py: giữ process boundary, route read engine không có model-executable tools; link command receipts.
- gateway/gemini.py: provider budget trước reservation, ID metadata parent/assignee/author/project, provenance/count receipts không nhầm SDK mock thành live.
- Core: show.html.erb, _result.html.erb, _control_center.html.erb, executions.html.erb, _execution_client.html.erb, qldapm_ai_helper.rb.
- tests/test_business_lifecycle.py mới; fixture project_id trong test_assistant_business.py; mcp-tools.json mô tả read mode; architecture.md.

Gateway thay đổi thực tế: SOURCE_CHANGES.json. Bảy prototype development vẫn bị .dockerignore loại trừ; không tự copy chúng vào runtime.

## Timeout và giới hạn

Rails AiBridge open3/read100/write5s. Start run trả receipt async, không giữ HTTP chờ cả model run. Native object90s, riêng CREATE dùng remaining deadline. Isolated worker ordinary600s, explicit read180s, legacy Owner envelope180s. Recovery tối đa90s riêng và không thực thi lại command. Không thêm scheduler/framework/operator business tools.

Model/key/project/billing/RBAC/TOTP/CSRF/HMAC/native gates giữ nguyên. Supervisor BA/QA/Reviewer read-only không trở thành Native WRITE actor.

Image cuối: Gateway `sha256:bcd7158e4febfd276d47599bf3be514997fbd976a32fb71be0f12b7d80748168`, Core `sha256:a3214219127e61ff934d33b0c45031df8a315e6a5f44ff9754c7985e2adcbcbb`. SourceSHA `0cc3f4e59c18fffc31c088d399078b4047328ba5707cc6a6a2eb902442eb70f6`. Bằng chứng: qualification.json, deployment-citation-fix.json, FINAL_INTEGRITY.json.

# P05-02 accepted — 17Oct2026

Supervisor planner: tách đọc vs ghi, xác định dependencies và budget trước gọi model.

## 1. Tóm tắt kết quả
- Triển khai thành công module **Supervisor Planner** tại [gateway/planner.py](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/planner.py) và các mô hình hợp đồng kế hoạch tại [gateway/agent_models.py](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/agent_models.py) (`PlanStep`, `PlanBudget`, `ExecutionPlan`).
- **Tách Đọc vs Ghi (Read vs Write Separation)**:
  - Phân tích từ khóa và ngữ cảnh yêu cầu: các thao tác tra cứu, đếm số lượng, xem báo cáo, kiểm tra trạng thái được xếp vào `READ_ONLY` (`requires_pm_approval: false`).
  - Mọi yêu cầu tạo mới, cập nhật, xóa, gán người, đổi trạng thái task/work package được xếp vào `PROPOSAL_WRITE` (`requires_pm_approval: true`).
  - Actor không phải PM (BA, FE, BE, QA) đề xuất ghi bắt buộc phải gắn cờ `requires_pm_approval = True` và bước tổng hợp đề xuất bắt buộc có `requires_pm_consent = True`.
- **Quyết định Tool / Model vs Deterministic-only**:
  - Với các truy vấn thuần dữ liệu xác định (như đếm work packages quá hạn, danh sách task mở, daily brief), Planner quyết định `deterministic_only = True`, `model_needed = False`, phân bổ `max_turns = 0` và `token_estimate = 0` để tiết kiệm tối đa hạn mức 15 RPM / 500 RPD của Gemini API.
  - Với các bài toán phân tích phức tạp (tiêu chí chấp nhận User Story, rủi ro sprint, phân tích bug regression), Planner phân bổ ngân sách giới hạn (`max_turns <= 2`, `token_estimate <= 1600`) trước khi gọi model.
- **Đồ thị phụ thuộc (DAG Step Dependencies)**:
  - Các bước thực thi được lập lịch tuần tự/song song có thứ tự nghiêm ngặt: Specialist Agent -> Reviewer Agent -> PM Proposal Aggregation (nếu có ghi).
  - Bảo đảm không có phụ thuộc vòng lặp (no circular dependencies), mọi dependency đều trỏ về step ID nhỏ hơn trước đó.
- **Tuân thủ hợp đồng và kích thước tài liệu**:
  - `ExecutionPlan` JSON tuân thủ đầy đủ schema Pydantic v2 strict và giới hạn `<= 32KB` của `AgentContract`.

## 2. Bằng chứng kiểm thử và thẩm định (Evidence)
- **Kiểm thử đơn vị Planner ([openproject/ai/tests/test_planner.py](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/tests/test_planner.py))**: 9/9 tests PASS (0.003s).
  - `test_read_instructions_classified_as_read_only`: PASS.
  - `test_write_instructions_classified_as_proposal_write`: PASS.
  - `test_non_pm_proposing_write_strictly_gated_by_pm_approval`: PASS.
  - `test_purely_deterministic_query_allocates_zero_model_budget`: PASS.
  - `test_complex_analysis_allocates_bounded_model_budget`: PASS.
  - `test_supervisor_routes_to_correct_domain_agent`: PASS.
  - `test_explicit_agent_choice_is_respected`: PASS.
  - `test_dag_steps_have_valid_dependencies_and_no_cycles`: PASS.
  - `test_plan_serializes_and_deserializes_cleanly_within_size_bounds`: PASS.
- **Kiểm thử hồi quy toàn diện**: 49/49 tests PASS (14.308s) bao gồm toàn bộ agent models, agent trace, agent API, queue, states, store, planner và outage policy.
- **Bảo toàn dữ liệu & runtime**:
  - 7/7 containers staging `Up` và `(healthy)`.
  - Database OpenProject 221 tables nguyên vẹn.
  - Bảng `gemini_usage` giữ nguyên 471 records (0 provider calls phát sinh trong quá trình lập kế hoạch).
  - Môi trường main (8088/8090) không thay đổi.

## 3. Trạng thái task
- Task P05-02: **DONE**
- Tiến độ Phase P05: **2/12 tasks DONE (16.7%)**
- Tiến độ tổng: **57/113 tasks DONE (50.4% - Chính thức vượt mốc 50% MVP)**
- Bước kế tiếp: Task P05-03 (PM Agent: Sprint risks, work packages overdue, blocker, workload có evidence).

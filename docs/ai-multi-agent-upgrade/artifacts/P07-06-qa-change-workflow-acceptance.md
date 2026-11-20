# BIÊN BẢN NGHIỆM THU TASK P07-06
## Workflow Khi Requirement/Work Package Thay Đổi → QA Draft và Thông Báo Phù Hợp

- **Task ID:** P07-06
- **Phase:** P07 — Tự động hóa quản lý Sprint và dự án (không GitHub)
- **Tình trạng:** DONE (100% Tiêu chí nghiệm thu đạt)
- **Change Request:** Tuân thủ đầy đủ `CR-USER-CAPACITY-20` (Hỗ trợ 1–20 người dùng mạng LAN, đa người dùng cùng role, RBAC PM-only write).
- **Ngày thực hiện:** 2026-10-17
- **Người thực hiện:** Gemini (Google Antigravity)

---

### 1. Mục tiêu và Tiêu chí chấp nhận (Acceptance Criteria)

- **Yêu cầu:** Nội dung event không tăng quyền; không auto transition/role change; built-in idempotency.
- **Ngân sách AI:** Thuần túy tính toán tất định (deterministic-first), `model_used: False`, tiêu tốn đúng **0 token** Gemini API Free Tier.
- **Xử lý sự kiện thay đổi yêu cầu (Requirement Change Event Handling):**
  - Khi nhận sự kiện thay đổi yêu cầu hoặc work package (`REQUIREMENT_UPDATED`, `WORK_PACKAGE_CHANGED`), hệ thống tự động trích xuất các trường thay đổi (`changed_fields`), phiên bản khóa (`lockVersion`) và thông tin liên quan.
  - Tự động soạn thảo bản nháp kịch bản kiểm thử (`qa_draft`) bao gồm: Happy Path, Regression/Boundary, và Security/OTP nếu có liên quan đến xác thực.
  - Bản nháp hoàn toàn mang tính chất đề xuất (`DRAFT_PENDING_REVIEW`), tuyệt đối không tự động ghi đè hoặc tạo dữ liệu nghiệp vụ giả mạo vào OpenProject.
- **Cơ chế Idempotency tích hợp sẵn (Built-in Idempotency):**
  - Quản lý băm sự kiện (`event_fingerprint = digest(canonical({package_id, lock_version, changed_fields}))`).
  - Khi nhận lại cùng một sự kiện trùng lặp, hệ thống trả về ngay bản nháp đã lưu (`idempotent_replay: True`) mà không chạy lại luồng xử lý hoặc spam thông báo lặp lại.
- **Bảo mật và Ngăn chặn leo thang đặc quyền (Anti-Escalation & No Auto-Transition):**
  - Hệ thống nghiêm ngặt từ chối mọi trường tự ý chuyển trạng thái hoặc thay đổi vai trò gắn kèm trong event (`auto_transitioned: False`, `status_mutation: "MUTATION_DISALLOWED"`).
  - Trạng thái công việc (`current_status`) được giữ nguyên bản theo OpenProject native, tuân thủ tuyệt đối quy định chỉ PM mới có quyền ký duyệt chuyển trạng thái nghiệp vụ.
- **Định tuyến thông báo phù hợp theo vai trò (Role-Appropriate Notifications):**
  - **QA:** Nhận thông báo yêu cầu rà soát kịch bản kiểm thử (`REVIEW_QA_DRAFT`).
  - **Lập trình viên được phân công:** Nhận thông báo nắm bắt thay đổi để đồng bộ mã nguồn với QA (`AWARENESS_ONLY`).
  - **PM:** Nhận thông báo giám sát rằng bản nháp kiểm thử đã được tạo và đang chờ QA rà soát (`OVERSIGHT_ONLY`).

---

### 2. Các tệp mã nguồn và kiểm thử

1. **`openproject/ai/gateway/qa_change_workflow.py`:**
   - Cung cấp lớp `QAChangeWorkflowEngine` và hàm `process_requirement_change(...)`.
   - Cơ chế sinh draft kiểm thử tất định và kiểm soát idempotency qua bộ nhớ băm.
   - Cơ chế bảo vệ biên giới RBAC ngăn chặn mọi nỗ lực tự chuyển trạng thái.
2. **`openproject/ai/gateway/service.py`:**
   - Cung cấp phương thức `Service.handle_requirement_change(actor, event)`.
3. **`openproject/ai/tests/test_qa_change_workflow.py`:**
   - 4 bài kiểm thử đơn vị bao phủ toàn diện:
     1. `test_qa_draft_generation_on_requirement_change`: Sinh đúng bản nháp kịch bản kiểm thử khi yêu cầu thay đổi.
     2. `test_built_in_idempotency`: Xác minh trả về bản ghi cũ khi nhận sự kiện trùng lặp.
     3. `test_no_privilege_escalation_or_auto_transition`: Chặn đứng hành vi cố tình leo thang vai trò hoặc tự động transition sang DONE.
     4. `test_role_appropriate_notifications`: Định tuyến thông báo chính xác tới QA, lập trình viên và PM.

---

### 3. Kết quả chạy kiểm thử thực tế

- Bộ kiểm thử `test_qa_change_workflow.py`: 4/4 bài kiểm thử PASS (thời gian chạy ~0.001s).
- Toàn bộ suite hồi quy (39 bài kiểm thử) đều PASS 100%.

---

### 4. Kết luận

Task `P07-06` đã hoàn thành 100% tiêu chí nghiệm thu. Luồng xử lý sự kiện thay đổi yêu cầu đảm bảo QA luôn nhận được kịch bản kiểm thử kịp thời, giữ vững tính toàn vẹn dữ liệu và phân quyền hệ thống.

# Phase 3.1 Emergency Functional Recovery & Architecture Alignment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Khắc phục triệt để các lỗi P0 gây tê liệt giao diện AI Command Center (HTTP 403 trên mọi nút điều khiển do thiếu khởi tạo `@role`, infinite spinner loading, 409 mù mờ, và bất đồng bộ trạng thái), thừa nhận trung thực các khoảng trống năng lực (Reviewer/QA, OpenClaw write permissions, PR #2), và xác minh bằng trình duyệt thật với tài khoản Owner thật.

**Architecture:** Sửa chữa trực tiếp tại tầng Rails controller (`qldapm_ai_controller.rb`) để khởi tạo `@role` trước mọi lệnh kiểm tra phân quyền; nâng cấp Frontend JavaScript với timeout và khối `finally` để triệt tiêu vĩnh viễn infinite spinner; chuẩn hóa thông điệp 409 từ Gateway; phân định minh bạch năng lực của các tác nhân (AI reasoning vs local-policy vs test runner); và xác minh toàn diện qua Playwright với read-back backend.

**Tech Stack:** Ruby on Rails 7 (OpenProject overlay), Python 3.12 (FastAPI AI Gateway, SQLite WAL), OpenClaw WSL2, Docker Desktop, Playwright Chromium.

**Spec:** User Directive Phase 3.1 (`EMERGENCY FUNCTIONAL RECOVERY, COMPLETE ARCHITECTURE REVALIDATION & REAL END-TO-END ACCEPTANCE`).

## Global Constraints
- Bảo tồn 100% Project 5 (`qldapm-local`): 341 Work Packages, lock_version tối đa 4, 0 mutations.
- Chi phí API bằng 0: Duy nhất mô hình `gemini-3.5-flash-lite` qua Free Tier.
- Tuyệt đối không auto-merge 5 Pull Requests trên GitHub; Work Package cha #379 duy trì `IN PROGRESS`.
- Không đánh đồng Toast submitting với thành công; mọi thao tác phải có backend read-back.
- Mọi nút bấm phải kết thúc ở trạng thái dứt khoát (success / failure / blocked / timeout), cấm spinner quay vô hạn.

## Review Focus
1. **Uninitialized `@role` in controller:** Gây lỗi HTTP 403 Forbidden trên mọi hành động POST của User 18 (Owner).
2. **Infinite spinner on fetch rejection:** Khi backend trả 403/409/500 hoặc response rỗng, cờ loading không được reset.
3. **Ambiguous HTTP 409 on `RUN ONCE`:** Khi toàn bộ 5/5 units đã hoàn tất (`ALL_DELIVERED`), người dùng bấm nút nhận thông báo khó hiểu.
4. **Audit contradictions:** Khẳng định 325 receipts trong SQLite trong khi file báo cáo chuyên đề trước ghi 0; PR #2 ghi OPEN trong khi thực tế đã MERGED vào feature branch; Reviewer là script nhưng gọi là AI.
5. **OpenClaw tool policy mismatch:** Khảo sát và làm rõ cơ chế ghi file của Dev Agent trong OpenClaw sandbox.

---

### Task 1: Sửa lỗi phân quyền cốt lõi trong Rails Controller (Root Cause của 403)

**Files:**
- Modify: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb:168-185`
- Test: `tools/test_controller_role_fix.py`

**Interfaces:**
- Consumes: `Qldapm::Rbac.role(@project, User.current, fresh: true)`
- Produces: `@role` được thiết lập chính xác (`AI_SYSTEM_OWNER` cho User 18, `PM` cho User 20) trước khi kiểm tra allowlist.

- [ ] **Step 1: Viết test tự động tái hiện lỗi 403 do `@role` uninitialized**
  Tạo `tools/test_controller_role_fix.py` mô phỏng việc gọi `QldapmAIController#command` và chứng minh hiện tại bị 403 do `@role` là `nil`.

- [ ] **Step 2: Chạy test để xác nhận FAIL (403 Forbidden)**
  Chạy: `python tools/test_controller_role_fix.py`
  Expected: FAIL (nhận 403 vì `@role` nil).

- [ ] **Step 3: Sửa `qldapm_ai_controller.rb`**
  Tại đầu hàm `def command`:
  Thêm dòng: `@role = Qldapm::Rbac.role(@project, User.current, fresh: true)`
  Đảm bảo `@role` có giá trị chuẩn xác trước dòng `return head :forbidden unless %w[PM AI_SYSTEM_OWNER].include?(@role)`.

- [ ] **Step 4: Chạy lại test để xác nhận PASS**
  Chạy: `python tools/test_controller_role_fix.py`
  Expected: PASS (User 18 được phân quyền thành công, `@role == "AI_SYSTEM_OWNER"`).

---

### Task 2: Triệt tiêu Infinite Loading & Nâng cấp xử lý lỗi Frontend

**Files:**
- Modify: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
- Test: `tools/test_frontend_error_boundary.py`

**Interfaces:**
- Consumes: Action submit handler, fetch API
- Produces: Visual state machine có khối `finally` đảm bảo reset cờ loading, hiển thị Toast lỗi chi tiết khi nhận 400, 401, 403, 409, 422, 500.

- [ ] **Step 1: Rà soát toàn bộ script xử lý sự kiện form submit trong template**
  Kiểm tra hàm `handleActionSubmit` và các listeners tương ứng.

- [ ] **Step 2: Bổ sung khối `finally` và bộ đón lỗi HTTP toàn diện**
  Đảm bảo khi fetch trả về status >= 400 hoặc network error:
  1. Gỡ bỏ lớp CSS submitting / disabled trên nút bấm.
  2. Ẩn thanh progress bar trên đỉnh trang.
  3. Đọc body JSON lỗi nếu có (ví dụ `data.error` hoặc `data.message`), nếu không có body thì map theo HTTP status:
     - 403: "Từ chối truy cập: Tài khoản không có quyền thực hiện thao tác này."
     - 409: "Xung đột nghiệp vụ: " + chi tiết từ backend (hoặc giải thích trạng thái).
     - 500: "Lỗi máy chủ nội bộ. Vui lòng thử lại sau."
  4. Bắn Toast thông báo màu đỏ trực quan.

- [ ] **Step 3: Kiểm thử xử lý lỗi mạng và HTTP failure không gây treo giao diện**
  Mô phỏng phản hồi 403 và 409, xác nhận spinner tắt sau tối đa 200ms và Toast hiển thị đúng.

---

### Task 3: Chuẩn hóa phản hồi State Machine và thông điệp 409 từ Gateway

**Files:**
- Modify: `openproject/ai/gateway/engineering_operator.py`
- Modify: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
- Test: `tools/test_state_machine_responses.py`

**Interfaces:**
- Consumes: `action: engineering_run_once`, `action: engineering_control`
- Produces: Thông điệp phản hồi rõ nghĩa khi không có unit đủ điều kiện chạy (5/5 DELIVERED).

- [ ] **Step 1: Viết test kiểm tra phản hồi khi gọi RUN ONCE lúc 5/5 units đã hoàn tất**
- [ ] **Step 2: Cải tiến thông điệp phản hồi trong Gateway & Controller**
  Thay vì để trả về lỗi trừu tượng, trả về cấu trúc rõ ràng:
  `{"status": "IDLE", "message": "Toàn bộ 5/5 Backlog units đã hoàn tất bàn giao. Hệ thống đang ở trạng thái an toàn."}`
- [ ] **Step 3: Chạy test xác nhận phản hồi rõ ràng, không gây hiểu lầm cho người dùng**

---

### Task 4: Khắc phục và kiểm chứng tính năng Sync GitHub

**Files:**
- Modify: `openproject/ai/gateway/engineering_github_sync.py`
- Modify: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
- Test: `tools/test_github_sync_live.py`

**Interfaces:**
- Consumes: GitHub REST API (`Luim3141/mini-task-manager`)
- Produces: Cập nhật cache SQLite `engineering_github_sync_cache`, phân biệt rõ ràng:
  - PR #2: `MERGED` vào feature branch `codex/openclaw-create-list-persistence-v1`
  - PR #1, #3, #4, #5: `OPEN`
  - Ghi nhận thời điểm sync thành công `last_sync_at`.

- [ ] **Step 1: Viết test gọi action `engineering_github_sync`**
- [ ] **Step 2: Sửa mã nguồn xử lý đồng bộ và hiển thị dữ liệu read-back**
- [ ] **Step 3: Xác minh bằng chứng đối soát được ghi vào SQLite và trả về giao diện**

---

### Task 5: Minh bạch hóa năng lực Tác nhân & Điều chỉnh Hồ sơ Roster

**Files:**
- Modify: `openproject/ai/gateway/agent_registry.py`
- Modify: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
- Test: `tools/test_agent_workforce_transparency.py`

**Interfaces:**
- Consumes: Agent definition catalog
- Produces: Hiển thị chính xác bản chất:
  - Reviewer: **`Deterministic Exact-Diff Checker (local-policy, 0 LLM Calls)`** kèm ghi chú rõ ràng về khoảng trống năng lực AI semantic review.
  - QA: **`Automated Pytest Runner`** kèm ghi chú rõ ràng về khoảng trống năng lực AI QA planning.
  - Dev: Làm rõ cơ chế ghi file trong OpenClaw sandbox.

- [ ] **Step 1: Cập nhật mô tả kỹ thuật trung thực trong `agent_registry.py`**
- [ ] **Step 2: Cập nhật thẻ hiển thị trên tab Agent Workforce**
- [ ] **Step 3: Xác minh giao diện phản ánh đúng thực tế, không thổi phồng**

---

### Task 6: Đóng gói Docker Revisions & Triển khai an toàn

**Files:**
- Modify: `openproject/ai/automation/engineering_deploy_continuation.py`
- Container: `qldapm-openproject-web-1`, `qldapm-ai-gateway-1`

- [ ] **Step 1: Build image `qldapm-core:engineering-continuation-r20-20261031`**
- [ ] **Step 2: Deploy revision `continuation-r20` lên Docker**
- [ ] **Step 3: Xác minh SHA256 các file trong container khớp 100% với mã nguồn host**
- [ ] **Step 4: Kiểm tra trạng thái sức khỏe container (healthy)**

---

### Task 7: Chiến dịch Kiểm thử Thực tế trên Trình duyệt Thật (Playwright)

**Files:**
- Create: `tools/verify_phase31_real_e2e.py`
- Output: `docs/ai/engineering/PHASE31_RECOVERY/screenshots/`

- [ ] **Step 1: Kịch bản 1 — Owner đăng nhập từ menu OpenProject vào Command Center**
- [ ] **Step 2: Kịch bản 2 — Owner bấm `RUN ONCE`**
  Xác minh: HTTP không phải 403, không spinner vô hạn, nhận Toast giải thích rõ ràng.
- [ ] **Step 3: Kịch bản 3 — Owner bấm `BẬT AUTO` / `OFF` / `PAUSE`**
  Xác minh: Mode cập nhật trong SQLite và hiển thị đúng trên badge header.
- [ ] **Step 4: Kịch bản 4 — Owner bấm `Sync GitHub`**
  Xác minh: Dữ liệu PRs được làm mới, Toast báo thành công kèm số lượng PRs.
- [ ] **Step 5: Kịch bản 5 — Owner bấm `Snapshot Tức Thời (+AI)` và `Lưu cấu hình lịch`**
  Xác minh: Báo cáo mới xuất hiện trong danh sách, lịch trình được lưu.
- [ ] **Step 6: Kịch bản 6 — Kiểm tra bảo toàn bất biến Project 5**
  Xác minh: Đúng 341 WPs, max lock_version 4, updated_at preserved.

---

### Task 8: Xuất bản Hồ sơ Pháp y Giai đoạn 3.1 & Bàn giao ChatGPT

**Files:**
- Target Directory: `docs/ai/engineering/PHASE31_RECOVERY/`
- Target Documents: 13 tài liệu bắt buộc theo yêu cầu Charter.
- Update: `IMPLEMENTATION_STATE.json`, `IMPLEMENTATION_JOURNAL.md`, `CHATGPT_TAKEOVER_LATEST.md`, `CHATGPT_CONTINUE_PROMPT.md`.

- [ ] **Step 1: Biên soạn 13 tài liệu pháp y thực chứng trong `PHASE31_RECOVERY/`**
- [ ] **Step 2: Cập nhật `IMPLEMENTATION_STATE.json` và `IMPLEMENTATION_JOURNAL.md`**
- [ ] **Step 3: Cập nhật `CHATGPT_TAKEOVER_LATEST.md` và tiếp quản prompts**
- [ ] **Step 4: Trình bày báo cáo tổng kết chi tiết gửi Chủ dự án để chờ Human UAT**

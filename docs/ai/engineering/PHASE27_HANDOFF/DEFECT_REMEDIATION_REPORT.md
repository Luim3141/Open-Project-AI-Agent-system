# BÁO CÁO CHI TIẾT KHẮC PHỤC 12 KHIẾM KHUYẾT (DEFECT REMEDIATION REPORT)
## DỰ ÁN: QLDAPM MAIN — PHASE 2.7

**Phiên bản Docker Deploy:** `qldapm-ai:engineering-continuation-r16-20261030` & `qldapm-core:engineering-continuation-r16-20261030`  
**Trạng thái kiểm thử:** 12/12 Defects FIXED & VERIFIED PASS 100%.

---

## DANH MỤC 12 KHIẾM KHUYẾT & KẾT QUẢ XỬ LÝ

### 1. DEFECT-01: Metadata Deployment Version Mismatch
- **Triệu chứng:** `IMPLEMENTATION_STATE.json` ghi `deployment_current: "r14"` trong khi `deployment.json` ghi `r15`.
- **Nguyên nhân gốc:** Script deploy Phase 2.6 cập nhật `deployment.json` nhưng bỏ sót trường `deployment_current` trong `IMPLEMENTATION_STATE.json`.
- **Giải pháp:** Cập nhật đồng bộ cả 2 file lên revision `continuation-r16`.
- **Files modified:** `docs/ai/engineering/deployment.json`, `docs/ai/engineering/IMPLEMENTATION_STATE.json`.
- **Bằng chứng:** `deployment.json` và `IMPLEMENTATION_STATE.json` đều phản ánh revision `r16`.

---

### 2. DEFECT-02: Implementation State Stale Stage
- **Triệu chứng:** `current_stage` trong `IMPLEMENTATION_STATE.json` vẫn là `PHASE_2_6_COMPLETED`.
- **Nguyên nhân gốc:** Chưa cập nhật tiến độ công việc sang Phase 2.7.
- **Giải pháp:** Cập nhật `current_stage` thành `PHASE_2_7_COMPLETED` kèm metadata chi tiết về forensic audit và remediation.
- **Files modified:** `docs/ai/engineering/IMPLEMENTATION_STATE.json`.
- **Bằng chứng:** Trạng thái trong state file là `PHASE_2_7_COMPLETED`.

---

### 3. DEFECT-03: UAT Phân Tầng Chưa Rõ Ràng (Conflation of Automated vs Human Acceptance)
- **Triệu chứng:** Tài liệu Phase 2.6 ghi "100% UAT COMPLETE" nhưng thực tế chỉ chạy các assert script tự động, chưa có người dùng nghiệp vụ (Human User) ký duyệt.
- **Nguyên nhân gốc:** Trộn lẫn khái niệm giữa Automated Verification Test và Human User Acceptance Testing.
- **Giải pháp:** Tách bạch 3 tầng rõ ràng:
  1. `automated_browser_tests`: Playwright script tự động verify UI (PASS).
  2. `engineering_acceptance`: Đội ngũ kỹ sư kiểm toán nội bộ xác nhận tiêu chuẩn kỹ thuật (PASS).
  3. `human_user_acceptance`: Dành cho Chủ dự án và Stakeholders thẩm định và ký duyệt bàn giao (PENDING/READY FOR REVIEW).
- **Files modified:** `docs/ai/engineering/IMPLEMENTATION_STATE.json`, `docs/ai/engineering/PHASE27_HANDOFF/README.md`.
- **Bằng chứng:** Ma trận nghiệm thu phân định rành mạch 3 tầng.

---

### 4. DEFECT-04: Owner Cross-Actor Authority & Run Scope Isolation
- **Triệu chứng:** Owner (User 18) không thể Hủy, Resume, hoặc Trace các runs do PM (User 20) tạo ra trong Project 6. Gateway trả về `AGENT_RUN_SCOPE_MISMATCH` hoặc không tìm thấy bản ghi.
- **Nguyên nhân gốc:** Các hàm trong `store.py` và `engineering.py` lọc cứng `WHERE actor = ?` và ném lỗi mismatch khi `actor_id != run.actor_id`.
- **Giải pháp:** Bổ sung ngoại lệ thẩm quyền cao nhất cho AI System Owner (User 18) đối với các runs thuộc Project 6 và Project 5. Cụ thể:
  - `openproject/ai/gateway/store.py`: Sửa các hàm `agent_task`, `agent_progress`, `agent_runs_page`, `agent_trace_page`, `execution_records`, `cancel_agent_run`, `run`.
  - `openproject/ai/gateway/engineering.py`: Sửa `project_for_run`, `claim`, `resume_reconciled`.
  - `openproject/ai/gateway/service.py`: Nới lỏng kiểm tra `AGENT_RESULT_SCOPE_MISMATCH` cho Owner.
- **Files modified:** `openproject/ai/gateway/store.py`, `engineering.py`, `service.py`.
- **Bằng chứng:** Test `owner_cancel_pm20_run` đạt `[PASS] cancelled: True` trong `tools/verify_phase27_remediations.py`.

---

### 5. DEFECT-05: Auto Mode State Machine & Safe Shutoff Verification
- **Triệu chứng:** Thiếu test evidence độc lập chứng minh Auto Mode tự động tắt (Auto Shutoff) khi hoàn thành hoặc khi xảy ra lỗi.
- **Nguyên nhân gốc:** Chưa có script kiểm thử độc lập cho state machine của `engineering_auto.py`.
- **Giải pháp:** Viết test script `tools/verify_defect05_auto_mode.py`. Kích hoạt AUTO mode khi toàn bộ backlog đã hoàn thành -> xác nhận hệ thống tự động nhận diện `ALL_DELIVERED` và chuyển an toàn về `OFF`.
- **Files modified:** `tools/verify_defect05_auto_mode.py`.
- **Bằng chứng:** `[PASS] initial_mode: OFF -> toggle_to_auto: AUTO -> auto_evaluated_mode: OFF (auto_shutoff_success: True)`.

---

### 6. DEFECT-06: Reporting Scheduler & UI Notifications
- **Triệu chứng:** Báo cáo tiến độ thiếu scheduler độc lập (chỉ chạy phụ thuộc vào engineering job), thiếu cấu hình lịch và thiếu thanh thông báo trên UI.
- **Nguyên nhân gốc:** Chưa có bảng lưu trữ lịch báo cáo định kỳ và thiếu polling kiểm tra thời gian.
- **Giải pháp:**
  - Tạo 2 bảng SQLite: `engineering_report_schedules` và `engineering_notifications`.
  - Khởi tạo lịch mặc định: Daily lúc 08:00 (có thể tùy chỉnh), Weekly lúc 09:00 Thứ 2 (Asia/Ho_Chi_Minh).
  - Thêm 4 API actions: `engineering_report_schedule_get`, `engineering_report_schedule_update`, `engineering_notifications_list`, `engineering_notifications_dismiss`.
  - Bổ sung thanh `Notifications Bar` ở đầu giao diện Control Center và hiển thị thông tin lịch tự động trong thẻ Báo cáo tiến độ.
- **Files modified:** `openproject/ai/gateway/engineering_reporting.py`, `engineering.py`, `catalog.py`, `permissions.py`, `service.py`, `openproject/ai/core/overlay/app/views/qldapm_ai/engineering.html.erb`.
- **Bằng chứng:** Test `report_schedule_get` [PASS], `report_schedule_update` [PASS], `report_generation_and_get` [PASS], UI Notifications Bar hiển thị rõ ràng trên Playwright screenshot.

---

### 7. DEFECT-07: Minh Bạch Hóa Trạng Thái GitHub Reviews & CI Checks
- **Triệu chứng:** Nhãn "Review: PASS" trên bảng Execution Runs gây hiểu nhầm rằng GitHub PRs đã được review trên GitHub.
- **Nguyên nhân gốc:** PRs được bot đẩy lên repo private `Luim3141/mini-task-manager` chưa có reviewer con người trên GitHub và chưa có GitHub Actions CI. Nhãn "Review: PASS" thực chất là Local AI Review của OpenClaw.
- **Giải pháp:**
  - Bổ sung trường `reviews_state` (`NO_REVIEWS_ON_GITHUB`) và `checks_state` (`NO_CI_CHECKS_CONFIGURED`) vào dữ liệu PR fetch từ GitHub.
  - Trên view: Thêm cột `Reviews & CI GitHub` với badge rõ ràng `No GH Reviews`, `No CI`. Đổi nhãn Execution Runs thành `Local AI Review: PASS`.
- **Files modified:** `openproject/ai/gateway/engineering_github_sync.py`, `openproject/ai/core/overlay/app/views/qldapm_ai/engineering.html.erb`.
- **Bằng chứng:** Test `GitHub PR Transparency` [PASS] và Playwright screenshot ghi nhận rõ ràng 2 badge `NO_REVIEWS_ON_GITHUB` và `NO_CI_CHECKS_CONFIGURED`.

---

### 8. DEFECT-08: Dynamic Agent Skills 6-Step Cycle Evidence
- **Triệu chứng:** Thiếu bằng chứng thực tế cho chuỗi 6 bước: Installed -> Discovered -> Selected -> Read -> Executed -> Verified.
- **Nguyên nhân gốc:** Các artifact tài liệu trước đây chỉ liệt kê tên skill mà không trích xuất runtime config, permission sandbox và prompt report.
- **Giải pháp:** Trích xuất bằng chứng chi tiết từ:
  1. Installed: 4 file `SKILL.md` trong `engineering_skills/`.
  2. Discovered & Configured: `openclaw.json` (`skills: [...]`, `contextInjection: 'always'`).
  3. Selected & Isolated: `/opt/qldapm/agents/feedback-4d13e695555a8d44/` (chmod 0444, root:root).
  4. Read & Injected: `gemini_call_receipts` và context injection.
  5. Executed: Phân quyền tool sandbox (`deny: write/edit` cho Dev, `deny: exec/write/edit` cho Reviewer).
  6. Verified: Acceptance test suites và Engineering Reports.
- **Files modified:** `tools/verify_defect08_skills.py`, `docs/ai/engineering/PHASE27_HANDOFF/skills_defect08_evidence.json`.
- **Bằng chứng:** Báo cáo kiểm chứng DEFECT-08 hoàn thành 6/6 bước.

---

### 9. DEFECT-09: Self-Contained Handoff Directory Missing
- **Triệu chứng:** Các tài liệu bàn giao nằm rải rác trong `docs/ai/engineering/`, thiếu một thư mục tự chứa độc lập dành riêng cho Phase 2.7.
- **Nguyên nhân gốc:** Chưa gom nhóm tài liệu theo tiêu chuẩn bàn giao khép kín.
- **Giải pháp:** Thiết lập toàn bộ cấu trúc bàn giao tự chứa tại `docs/ai/engineering/PHASE27_HANDOFF/` gồm `README.md`, `AUDIT_FORENSIC_REPORT.md`, `DEFECT_REMEDIATION_REPORT.md`, `ACCEPTANCE_MATRIX_35_QUESTIONS.md`, các file JSON evidence và thư mục `screenshots/`.
- **Files modified:** Toàn bộ thư mục `docs/ai/engineering/PHASE27_HANDOFF/`.
- **Bằng chứng:** Thư mục bàn giao tự chứa đầy đủ tài liệu và ảnh minh chứng.

---

### 10. DEFECT-10: Project 5 Isolation & Invariance Verification
- **Triệu chứng:** Cần kiểm chứng pháp y độc lập chứng minh Project 5 không bị sửa đổi ngoài ý muốn và được bảo vệ bất biến.
- **Nguyên nhân gốc:** Cần chứng minh bằng dữ liệu database và kiểm thử mutation.
- **Giải pháp:**
  - Kiểm tra database: 341 Work Packages giữ nguyên 100%.
  - Kiểm tra mutation: Lệnh gọi thao tác kỹ thuật vào Project 5 bị Gateway từ chối ngay lập tức với HTTP 403.
- **Files modified:** `tools/verify_phase27_remediations.py`.
- **Bằng chứng:** Test `project5_isolation` [PASS] (HTTP 403 denied).

---

### 11. DEFECT-11: Browser UAT Evidence Missing Actual Screenshots
- **Triệu chứng:** Thiếu ảnh chụp màn hình thực tế từ trình duyệt đối với giao diện Control Center của Owner.
- **Nguyên nhân gốc:** Các đợt kiểm thử trước chủ yếu dựa vào curl hoặc Rails view render string.
- **Giải pháp:** Viết test suite Playwright `tools/test_owner_ui_playwright.py` chạy trên Google Chrome thật, inject session cookie thật của Owner 18, chụp ảnh toàn trang và chụp sau tương tác click.
- **Files modified:** `tools/test_owner_ui_playwright.py`, `docs/ai/engineering/PHASE27_HANDOFF/screenshots/owner_control_center_live.png`, `owner_control_center_after_report_click.png`.
- **Bằng chứng:** 2 ảnh chụp màn hình dung lượng 157 KB và 147 KB trong thư mục `screenshots/`.

---

### 12. DEFECT-12: Milestone 6 (n8n + Second Brain) Omission in Final Reports
- **Triệu chứng:** Báo cáo tổng kết Phase 2.6 bỏ sót Milestone 6 (n8n 16 workflows + Qdrant Second Brain).
- **Nguyên nhân gốc:** Lỗi biên tập tài liệu Markdown.
- **Giải pháp:**
  - Kiểm tra độc lập runtime: Qdrant alive trên port 6333 với 2,117 points; n8n alive trên port 5679 với 16/16 workflows active.
  - Phục hồi Milestone 6 vào tài liệu tổng kết và ma trận nghiệm thu.
- **Files modified:** `tools/verify_defect12_m6.py`, `docs/ai/engineering/PHASE27_HANDOFF/m6_n8n_qdrant_evidence.json`.
- **Bằng chứng:** Test `verify_defect12_m6.py` [PASS] 100%.

# Phase 3.2: Complete Autonomous AI Engineering Workflow, Agent Coordination & Operational Command Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chuyển đổi QLDAPM AI Command Center thành trung tâm chỉ huy AI Engineering vận hành thực thụ, giải quyết triệt để 14 khoảng cách tính năng: cho phép giao việc mới bằng ngôn ngữ tự nhiên cho PM/BA Agent, quan sát chi tiết từng run và chuỗi tương tác Agent (PM → BA → Dev → Reviewer → QA), khắc phục đồng bộ GitHub hai chiều thời gian thực, đọc toàn văn báo cáo Markdown, và minh bạch hóa trạng thái điều khiển tự động.

**Architecture:** Mở rộng giao diện điều khiển hiện đại `_engineering_command_center.html.erb` theo tiêu chuẩn UI/UX Pro Max (OLED Dark, Lucide SVGs, Event Delegation không vi phạm CSP), kết nối trực tiếp các API Gateway đã kiểm chứng (`engineering_plan`, `get_execution_monitor`, `engineering_github_sync`, `engineering_reporting`), bổ sung 3 Modals tương tác chuyên sâu (Work Intake, Run Inspector, Report Reader) và chuẩn hóa phản hồi trạng thái Auto Mode.

**Tech Stack:** Ruby on Rails 7 (OpenProject overlay), Vanilla JavaScript (CSP nonced Unobtrusive JS), Python 3.14 (FastAPI Gateway & SQLite durable store), Docker Stack (revision continuation-r21), Playwright Chromium runner.

**Spec:** QLDAPM Main Project Charter, AGENTS.md, Phase 3.2 Operational Requirements.

## Global Constraints
- **Bảo vệ tuyệt đối Project 5 (`qldapm-local`, id=5):** Đúng 341 Work Packages, max lock_version 4, updated_at đóng băng `2026-10-29 10:08:56Z`, 0 thao tác ghi (zero writes).
- **Phạm vi dự án tác nghiệp:** Chỉ thực thi trên Project 6 (`ai-dev-demo`, id=6) với tài khoản User 18 (`op-owner`, AI System Owner) hoặc User 20 (`PM20`).
- **Ràng buộc chi phí Zero-Cost:** Chỉ sử dụng mô hình Google Gemini `gemini-3.5-flash-lite` Free Tier ($0.00). Tuyệt đối không dùng Pro/Ultra.
- **Bảo vệ nhánh GitHub:** Duy trì 5 Pull Requests (#1–#5) trên kho `Luim3141/mini-task-manager`; không auto-merge khi chưa có lệnh tường minh của Owner.
- **Tiêu chuẩn UI/UX Pro Max:** Tuyệt đối không dùng emoji làm biểu tượng; toàn bộ icons là SVG vector; con trỏ `cursor-pointer` trên mọi phần tử bấm được; độ tương phản >= 4.5:1 (WCAG AA); chuyển động mượt mà (150-300ms).

## Review Focus
1. CSP Nonce Compliance: Toàn bộ tương tác Modal và click handler phải sử dụng Unobtrusive Event Delegation, không chứa inline `onclick` vi phạm CSP.
2. Dynamic Backlog Extension: Lệnh `engineering_plan` phải phân tích thành công input tự nhiên, tạo được child Work Package và Engineering Unit mới mà không ảnh hưởng 5 units cũ.
3. Execution Monitor Projection: Modal Run Inspector phải nạp mượt mà dữ liệu DAG từ `get_execution_monitor` (Supervisor, BA/PM hoặc Dev/Reviewer/QA) mà không làm chậm trang.
4. GitHub Live Data Binding: Dữ liệu PRs phải lấy từ `eng['github']['prs']` thay vì fallback tĩnh `eng['github_prs']`.
5. Error Resilience: Khi API trả về lỗi hoặc timeout, giao diện phải hiển thị Toast rõ nghĩa và không bao giờ kẹt spinner vô hạn.

---

### Task 1: Thiết kế và tích hợp AI Work Intake Modal & PM/BA Planning Interface
**Mục tiêu:** Giải quyết Gap 1, 4, 8, 13 — Cung cấp giao diện trực quan cho phép Owner nhập yêu cầu tính năng mới, kích hoạt PM/BA Agent phân tích thành đặc tả kỹ thuật và sinh Unit mới trong Backlog.

**Files:**
- Modify: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
- Modify: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
- Test: `tests/test_work_intake_planning.py`

**Steps:**
- [ ] 1.1 Viết unit test kiểm tra Gateway tiếp nhận lệnh `engineering_plan` với feedback mới, sinh ra `Specification` và `DevelopmentPlan` (RED).
- [ ] 1.2 Cập nhật `qldapm_ai_controller.rb` chuẩn hóa thông điệp phản hồi cho action `engineering_plan`: thông báo rõ Unit mới và số Work Package con vừa được tạo.
- [ ] 1.3 Bổ sung nút bấm "Giao việc mới cho AI (+PM/BA)" nổi bật tại Header và thanh công cụ Mission Control trong `_engineering_command_center.html.erb`.
- [ ] 1.4 Xây dựng Modal "Giao việc mới cho AI & Lập kế hoạch PM/BA" (`#qcc-intake-modal`): gồm textarea yêu cầu, chọn công việc cha, tóm tắt các ràng buộc kỹ thuật.
- [ ] 1.5 Thêm khu vực hiển thị danh sách Kế hoạch PM/BA (`engineering['plans']`) với chi tiết: Tóm tắt yêu cầu, Acceptance Criteria, và các Work Packages con tương ứng.
- [ ] 1.6 Chạy test xác nhận hoàn tất (GREEN).

---

### Task 2: Xây dựng Execution Inspector Modal & Trực quan hóa Tương tác Đa Tác nhân
**Mục tiêu:** Giải quyết Gap 5, 6, 7, 12 — Cho phép bấm vào bất kỳ Run ID nào để xem toàn bộ sơ đồ DAG điều phối, chi tiết tương tác từng Agent (PM → BA → Dev → Reviewer → QA), diff code, pytest logs và sự kiện thời gian thực.

**Files:**
- Modify: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
- Modify: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
- Test: `tests/test_execution_monitor_view.py`

**Steps:**
- [ ] 2.1 Viết test kiểm tra endpoint `/projects/:id/qldapm-ai/execution?run_id=...&format=json` trả về cấu trúc DAG đầy đủ của `get_execution_monitor` (RED).
- [ ] 2.2 Đảm bảo action `execution` trong `qldapm_ai_controller.rb` hỗ trợ cả User 18 và User 20 với đầy đủ quyền truy cập Project 6.
- [ ] 2.3 Cập nhật bảng "Execution Center" và bảng "Recent Runs": chuyển toàn bộ Run ID thành nút bấm tương tác (`.qcc-run-inspector-btn`) có biểu tượng con mắt / chi tiết.
- [ ] 2.4 Xây dựng Modal "Chi tiết Thực thi & Giám sát Tác nhân" (`#qcc-run-modal`) gồm 5 tab con:
  - *Tab DAG & Phân luồng:* Sơ đồ luồng Supervisor → Dev → Reviewer → QA với trạng thái thời gian thực.
  - *Tab Dòng sự kiện (Timeline):* Bảng sự kiện chi tiết (`execution_events`) kèm timestamp và duration.
  - *Tab Mã nguồn & Diffs:* Danh sách file thay đổi, commit hash, link PR.
  - *Tab Kiểm thử & QA:* Log kết quả Pytest, tỷ lệ pass/fail, bằng chứng chấp nhận.
  - *Tab Dữ liệu thô (Raw JSON):* Hiển thị payload kỹ thuật cho audit.
- [ ] 2.5 Bổ sung script JS nonced tải dữ liệu bất đồng bộ qua `fetch('/projects/.../execution?run_id=...')` và render vào Modal mà không cần tải lại trang.
- [ ] 2.6 Chạy test xác nhận hoàn tất (GREEN).

---

### Task 3: Đồng bộ GitHub Hai chiều Thời gian thực & Phân định Nhánh Merge
**Mục tiêu:** Giải quyết Gap 9, 10 — Sửa lỗi binding dữ liệu PRs, hiển thị minh bạch trạng thái merge trên GitHub (MAIN vs FEATURE_BRANCH), và cập nhật hoạt động sang OpenProject.

**Files:**
- Modify: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
- Modify: `openproject/ai/gateway/engineering_github_sync.py`
- Test: `tests/test_github_sync_live.py`

**Steps:**
- [ ] 3.1 Viết test kiểm tra dữ liệu PRs từ GitHub REST API được nạp đúng vào `eng['github']['prs']` và khớp với `PR_WP_MAP` (RED).
- [ ] 3.2 Sửa lỗi truy vấn trong `_engineering_command_center.html.erb`: đọc `github_info = eng['github'] || {}; github_prs = github_info['prs'] || ...` thay vì fallback tĩnh cũ.
- [ ] 3.3 Bổ sung các huy hiệu trạng thái merge rõ nét:
  - `MERGED TO MAIN` (Huy hiệu xanh ngọc đậm: Đã gộp vào nhánh chính)
  - `MERGED TO FEATURE BRANCH` (Huy hiệu tím: Đã gộp vào nhánh phụ, chưa vào main)
  - `OPEN / IN REVIEW` (Huy hiệu xanh lá: Đang mở chờ duyệt)
- [ ] 3.4 Bổ sung nút "Đồng bộ GitHub ngay" tại tab GitHub và Header, kèm thông báo số PRs đã đối soát và cập nhật vào OpenProject.
- [ ] 3.5 Chạy test xác nhận hoàn tất (GREEN).

---

### Task 4: Xây dựng Markdown Report Reader Modal & Tự động Hiển thị Báo cáo mới
**Mục tiêu:** Giải quyết Gap 11 — Cho phép đọc toàn văn báo cáo Markdown, xem chi tiết các chỉ số đo lường và tự động hiển thị nội dung báo cáo sau khi tạo.

**Files:**
- Modify: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
- Modify: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
- Test: `tests/test_report_reader_view.py`

**Steps:**
- [ ] 4.1 Viết test kiểm tra API `engineering_report_list` và `engineering_report_get` trả về toàn văn nội dung Markdown (RED).
- [ ] 4.2 Cập nhật `_engineering_command_center.html.erb`: bổ sung nút "Đọc toàn văn" trên mỗi thẻ báo cáo.
- [ ] 4.3 Xây dựng Modal "Đọc Báo cáo Toàn văn" (`#qcc-report-modal`) định dạng chuẩn typography cho Markdown, có nút "Sao chép Markdown" và "In báo cáo".
- [ ] 4.4 Khi người dùng bấm "Snapshot Tức Thời (+AI)", controller trả về thông tin báo cáo vừa tạo; giao diện tự động bật popup thông báo với nút "Xem ngay báo cáo vừa tạo" để mở modal ngay lập tức.
- [ ] 4.5 Chạy test xác nhận hoàn tất (GREEN).

---

### Task 5: Cải tiến Trạng thái Điều khiển Tự động (Auto Mode & Header RUN ONCE)
**Mục tiêu:** Giải quyết Gap 2, 3, 14 — Minh bạch hóa lý do AUTO tự ngắt khi hết việc và hỗ trợ người dùng chọn chạy lại Unit hoặc giao việc mới khi backlog đã đầy.

**Files:**
- Modify: `openproject/ai/gateway/engineering_auto.py`
- Modify: `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`
- Modify: `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb`
- Test: `tests/test_auto_mode_transparency.py`

**Steps:**
- [ ] 5.1 Cập nhật `engineering_auto.py`: khi `all_delivered` là True, trả về lý do chi tiết `reason: 'ALL_DELIVERED'` kèm thông điệp rõ ràng: *"Tất cả 5/5 Backlog units đã hoàn tất giao hàng. Chế độ AUTO tự động tắt để bảo vệ hệ thống."*.
- [ ] 5.2 Cập nhật action `command` trong `qldapm_ai_controller.rb`: truyền thông điệp giải thích trung thực về trạng thái `AUTO -> OFF` lên Toast thay vì báo "Đã bật AUTO".
- [ ] 5.3 Khi 5/5 units đã hoàn tất, nút `RUN ONCE` trên Header chuyển thành nút dropdown hoặc hiển thị modal gợi ý: "Giao việc mới (PM/BA)" hoặc "Chạy lại Unit cũ".
- [ ] 5.4 Chạy test xác nhận hoàn tất (GREEN).

---

### Task 6: Đóng gói Docker Revision `continuation-r21` & Triển khai An toàn
**Mục tiêu:** Đóng gói toàn bộ thay đổi mã nguồn vào Docker image production, triển khai lên container `qldapm-openproject-web-1` và `qldapm-ai-gateway-1`, xác minh đối soát SHA256 100%.

**Files:**
- Script: `openproject/ai/automation/EngineeringCore.Dockerfile`
- Config: `docs/ai/engineering/deployment.json`

**Steps:**
- [ ] 6.1 Build Docker image `qldapm-core:engineering-continuation-r21-20261031`.
- [ ] 6.2 Hot-deploy mã nguồn vào container và gửi tín hiệu reload Puma worker an toàn.
- [ ] 6.3 Đối soát mã băm SHA256 giữa host và container, đảm bảo khớp 100%.
- [ ] 6.4 Kiểm tra 21/21 Docker containers đạt trạng thái `Up (healthy)`.

---

### Task 7: Chiến dịch Kiểm thử Thực tế trên Trình duyệt Thật (Playwright Chromium)
**Mục tiêu:** Kiểm chứng toàn diện trên giao diện trình duyệt thực tế với tài khoản User 18 (AI System Owner), thu thập ảnh chụp màn hình bằng chứng cho toàn bộ 14 tiêu chí.

**Files:**
- Script: `tools/verify_phase32_full_functional.js`
- Screenshots: `docs/ai/engineering/PHASE32/screenshots/`

**Steps:**
- [ ] 7.1 Kịch bản 1: Kiểm tra tải Command Center, mở Modal "Giao việc mới cho AI", nhập nội dung và xác nhận PM/BA nhận việc thành công.
- [ ] 7.2 Kịch bản 2: Bấm vào một Run ID trên bảng Execution Center, xác nhận Modal Run Inspector mở lên, hiển thị đủ 5 tab (DAG, Timeline, Code Diff, Pytest Log, Raw JSON).
- [ ] 7.3 Kịch bản 3: Chuyển sang Tab GitHub, xác nhận dữ liệu PRs đọc từ GitHub live, hiển thị đúng huy hiệu merge (MAIN vs FEATURE_BRANCH) và bấm nút Sync thành công.
- [ ] 7.4 Kịch bản 4: Chuyển sang Tab Reports, bấm "Xem toàn văn" mở Modal đọc báo cáo Markdown đầy đủ.
- [ ] 7.5 Kịch bản 5: Bấm "Snapshot Tức Thời (+AI)", xác nhận Toast hiển thị nút mở trực tiếp báo cáo vừa tạo.
- [ ] 7.6 Kịch bản 6: Bấm "BẬT AUTO", xác nhận nhận thông báo giải thích rõ ràng vì sao chế độ tự tắt khi 5/5 units đã xong.
- [ ] 7.7 Kịch bản 7: Kiểm tra bất biến Project 5 (đúng 341 WPs, max lock_version 4, 0 writes).
- [ ] 7.8 Xuất bản kết quả kiểm thử vào `docs/ai/engineering/PHASE32/FUNCTIONAL_TEST_RESULTS.json`.

---

### Task 8: Xuất bản Hồ sơ Pháp y Nghiệm thu Phase 3.2 & Cập nhật Bàn giao
**Mục tiêu:** Đóng gói toàn bộ 10 hồ sơ pháp y thực chứng, cập nhật trạng thái quản trị và sẵn sàng cho Chủ dự án Human UAT.

**Files:**
- Create: `docs/ai/engineering/PHASE32/ACCEPTANCE_REPORT.md`
- Create: `docs/ai/engineering/PHASE32/DEFECT_REMEDIATION_EVIDENCE.md`
- Create: `docs/ai/engineering/PHASE32/AGENT_COMMUNICATION_DAG.md`
- Create: `docs/ai/engineering/PHASE32/GITHUB_SYNC_AUDIT.md`
- Create: `docs/ai/engineering/PHASE32/NEXT_EXACT_ACTION.md`
- Create: `docs/ai/engineering/PHASE32/CHATGPT_TAKEOVER.md`
- Modify: `docs/ai/engineering/IMPLEMENTATION_STATE.json`
- Modify: `docs/ai/engineering/IMPLEMENTATION_JOURNAL.md`
- Modify: `docs/ai/engineering/CHATGPT_TAKEOVER_LATEST.md`

**Steps:**
- [ ] 8.1 Biên soạn trọn bộ tài liệu pháp y trong `docs/ai/engineering/PHASE32/`.
- [ ] 8.2 Cập nhật `IMPLEMENTATION_STATE.json` sang `PHASE_3_2_COMPLETED`.
- [ ] 8.3 Cập nhật `IMPLEMENTATION_JOURNAL.md` và `CHATGPT_TAKEOVER_LATEST.md`.
- [ ] 8.4 Trình bày báo cáo nghiệm thu tổng thể gửi Chủ dự án để tiến hành Human UAT.

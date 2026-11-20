# SƠ ĐỒ LUỒNG DỮ LIỆU TOÀN HỆ THỐNG (DATA FLOW MAP) — PHASE 2.9.2
**Hệ thống:** QLDAPM MAIN (OpenProject Core + AI Command Center + AI Gateway + OpenClaw + Second Brain)  
**Ngày lập:** 2026-10-31  
**Phiên bản:** Revision r19 (`qldapm-core:engineering-continuation-r19-20261030` / `qldapm-ai:engineering-continuation-r19-20261030`)

---

## 1. TỔNG QUAN LUỒNG THÔNG TIN TOÀN TUYẾN

```mermaid
flowchart TD
    subgraph Client ["Client Browser (User 18 / User 20)"]
        UI["OpenProject Project Sidebar / AI Command Center UI"]
        Toast["Toast Notification System (#qcc-toast-container)"]
        Poller["Background Polling Engine (setInterval 20s)"]
    end

    subgraph Rails ["OpenProject Rails Core (Port 18088)"]
        Nav["Sidebar Menu Filter (qldapm_gates.rb)"]
        Ctrl["QldapmAiController (#engineering_action / #show)"]
        Bridge["Qldapm::AiBridge (HMAC / Unix Socket / HTTP)"]
    end

    subgraph Gateway ["AI Gateway & Supervisor (Port 18089)"]
        GW_API["FastAPI App / Router (service.py)"]
        EngStore["Engineering SQLite Store (store.py)"]
        EngCore["Engineering Pipeline Core (engineering.py)"]
        SkillReg["Agent Dynamic Skills Registry (engineering_skills)"]
    end

    subgraph Integrations ["External / Subsystems Integration"]
        GH["GitHub API (Octokit / REST)"]
        OC["OpenClaw / Gemini API Runtime"]
        N8N["n8n Webhook Automations (Port 5679)"]
        QD["Qdrant Second Brain (Port 6333)"]
        OP_DB["OpenProject PostgreSQL (Project 5 & 6)"]
    end

    %% Client to Rails
    UI -->|1. Click AI Command Center Menu| Nav
    Nav -->|2. Route /projects/ai-dev-demo/qldapm-ai| Ctrl
    UI -->|3. Submit Action: RUN ONCE / AUTO / SYNC / SCHEDULE| Ctrl
    Poller -->|4. Polling GET ?format=json| Ctrl

    %% Rails to Gateway
    Ctrl -->|5. AiBridge.call(action, payload)| Bridge
    Bridge -->|6. POST /api/v1/engineering/*| GW_API

    %% Gateway Operations
    GW_API --> EngCore
    GW_API --> EngStore
    EngCore --> SkillReg
    EngCore --> GH
    EngCore --> OC
    EngCore --> N8N
    EngCore --> QD
    EngCore --> OP_DB

    %% Response cycle
    GW_API -->|7. JSON Response {status, result, error}| Bridge
    Bridge -->|8. Formatted Hash| Ctrl
    Ctrl -->|9. Render View with @result & Flash| UI
    Ctrl -->|10. JSON Status for Poller| Poller
    UI -->|11. Trigger DOM Toast Alert| Toast
```

---

## 2. CHI TIẾT CÁC LUỒNG DỮ LIỆU ĐẶC THÙ (ACTION FLOWS)

### 2.1. Luồng 1: Điều hướng Sidebar Menu (Navigation Entrypoint)
- **Tác nhân:** User 18 (Owner) hoặc User 20 (PM) truy cập bất kỳ trang nào của Project 6 (`ai-dev-demo`).
- **Đường truyền:**
  1. OpenProject nạp `Redmine::MenuManager.items(:project_menu, project)`.
  2. Filter `qldapm_gates.rb` kiểm tra `project.identifier == 'ai-dev-demo'` và `User.current.admin? || roles.include?('Project admin') || roles.include?('Project manager')`.
  3. Rails render thẻ `<li class="main-menu-item" data-name="qldapm_ai"><a class="qldapm-ai-menu-item" href="/projects/ai-dev-demo/qldapm-ai">AI Command Center</a></li>` ngay bên dưới mục `Work packages`.
  4. Client click link -> Điều hướng ngay vào Giao diện Command Center hiện đại (`?ui=modern`).
  5. Nút `← Work Packages` trên header cho phép điều hướng ngược lại `/projects/ai-dev-demo/work_packages` 100% hai chiều.

### 2.2. Luồng 2: Thực thi Lệnh Tức thời (RUN ONCE Action)
- **Tác nhân:** User click nút `RUN ONCE` trên Mission Control Header.
- **Đường truyền:**
  1. Event listener JavaScript chặn double submit:
     - Thêm class `qcc-submitting` vào nút bấm.
     - Hiển thị spinner và thanh progress bar đỉnh trang (`#qcc-top-progress`).
  2. Form gửi `POST /projects/ai-dev-demo/qldapm-ai` với params `command[action]=engineering_run_once`.
  3. `QldapmAiController#engineering_action` gọi `AiBridge.call(project, user, 'command', { action: 'engineering_run_once', arguments: {} })`.
  4. Gateway `service.py` xử lý lệnh:
     - Kiểm tra state hiện tại. Nếu toàn bộ 5/5 Units đã hoàn thành (`ALL_DELIVERED`), trả về:
       `{ "status": "ok", "message": "Tất cả 5 backlog units đã hoàn thành bàn giao (DELIVERED). Không còn unit tồn đọng để chạy.", "result": { "run_once": "noop", "active_run": null } }`.
  5. Controller bắt kết quả, gán `@result = res['result']`, humanize thông báo thành công vào `@result['message']`.
  6. View render lại: Toast alert container `#qcc-toast-container` lập tức bật Toast thông báo (màu xanh navy/emerald, thời gian tự hủy 7s). Thanh progress đỉnh trang kết thúc animation.

### 2.3. Luồng 3: Bật/Tắt Chế Độ Tự Động (AUTO ON/OFF Mode Switch)
- **Tác nhân:** User click `BẬT AUTO` hoặc `OFF`.
- **Đường truyền:**
  1. Form gửi `action=engineering_control`, params `mode=AUTO` (hoặc `OFF`).
  2. Gateway ghi nhận vào `engineering_state`:
     - Nếu chuyển sang `AUTO`, pipeline tự động kiểm tra điều kiện kích hoạt. Vì toàn bộ 5 units đã `DELIVERED`, Auto Mode tự động tắt an toàn (`shutoff_reason: ALL_DELIVERED`) để chống tiêu tốn token vô ích và tránh tạo commit rác.
     - Trả về payload xác nhận: `mode: AUTO -> OFF (Safe shutoff: 5/5 units delivered)`.
  3. Controller render `@result`, Toast thông báo hiển thị rõ: *"Đã cập nhật chế độ vận hành: AUTO (Safe Shutoff: Tất cả backlog units đã bàn giao)"*.

### 2.4. Luồng 4: Đồng bộ Hiện trạng GitHub (Sync GitHub)
- **Tác nhân:** User click `Sync GitHub` trong Hero Header.
- **Đường truyền:**
  1. Gửi lệnh `action=engineering_github_sync`.
  2. Gateway kích hoạt module `engineering_github_sync.py`:
     - Kết nối GitHub API, đọc trạng thái của 5 Pull Requests (#1 đến #5) thuộc repo `mini-task-manager`.
     - Đọc số branch, commit hash, CI checks status, và review threads.
     - Cập nhật snapshot mới nhất vào `engineering_github_sync.json` và DB.
  3. Controller trả về kết quả đồng bộ. Toast hiển thị: *"Đã đồng bộ thành công hiện trạng GitHub (5 PRs, 5 branches, 0 CI failures)"*.

### 2.5. Luồng 5: Cấu hình Lịch Báo cáo Định kỳ (Schedule Configuration)
- **Tác nhân:** User mở modal `Cấu hình lịch` trong Tab Reports & Analytics.
- **Đường truyền:**
  1. Modal `#schedule-config-modal` hiển thị dạng backdrop làm mờ OLED, điền sẵn cấu hình hiện tại (Daily 08:00, Weekly 09:00 Thứ 2, timezone Asia/Ho_Chi_Minh).
  2. User chỉnh sửa giờ/kênh gửi và click `Lưu cấu hình`.
  3. Form gửi `action=engineering_report_schedule_update` kèm payload JSON.
  4. Gateway lưu vào bảng `engineering_report_schedules`.
  5. Controller ghi nhận thành công, đóng modal và bắn Toast xác nhận: *"Cấu hình lịch báo cáo tự động đã được lưu thành công"*.

### 2.6. Luồng 6: Cơ Chế Polling Real-time (Zero Silent Stale)
- **Chu kỳ:** Mỗi 20 giây một lần khi tab trình duyệt đang active.
- **Đường truyền:**
  1. Poller gọi AJAX GET `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?format=json`.
  2. Controller thực hiện fetch nhẹ `engineering_status` từ Gateway và serialize JSON trả về client.
  3. Client script so sánh timestamp `last_updated`: nếu có thay đổi về tiến độ run hoặc worker status, tự động cập nhật DOM tại các thẻ KPI mà không làm reload toàn bộ trang.

---

## 3. BẢO MẬT & ĐẢM BẢO TÍNH TOÀN VẸN TRÊN TỪNG CHẶNG
1. **CSRF Protection:** Tất cả các form submit đều mang Rails authenticity token (`csrf-token`).
2. **CSP Nonce:** 100% script tương tác và event listeners đều gắn `nonce="<%= content_security_policy_nonce %>"` — tuyệt đối không có inline script vi phạm CSP.
3. **RBAC Gateways:**
   - User 18 (Admin/Owner): Full quyền.
   - User 20 (PM): Full quyền điều hành.
   - User 19 (Member thông thường / Dev): Bị chặn 403 Forbidden ngay tại Rails controller filter.
4. **Project 5 Isolation:** Mọi mutation trong Phase 2.9.2 chỉ định danh duy nhất Project 6 (`ai-dev-demo`), bảo toàn tuyệt đối 341 Work Packages của Project 5 (`qldapm-local`).

# DANH MỤC THAY ĐỔI MÃ NGUỒN (SOURCE CHANGE MANIFEST) — PHASE 2.9.2
**Hệ thống:** QLDAPM MAIN (OpenProject Core + AI Command Center Overlay)  
**Ngày lập:** 2026-10-31  
**Mục tiêu:** Lưu vết đầy đủ các tệp mã nguồn đã được sửa đổi, mục đích sửa, nguyên nhân gốc rễ và cơ chế phòng ngừa hồi quy.

---

## 1. BẢNG TỔNG KẾT TỆP MÃ NGUỒN ĐÃ SỬA ĐỔI

| STT | Đường dẫn tệp | Loại tệp | Mục đích thay đổi | Defect khắc phục |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `openproject/ai/core/overlay/config/initializers/qldapm_gates.rb` | Ruby Initializer | Đăng ký menu item `AI Command Center` cho Project 6 (`ai-dev-demo`) trên sidebar OpenProject; cấp quyền cho Owner (18) và PM (20). | **DEFECT-292-01** |
| 2 | `openproject/ai/automation/EngineeringCore.Dockerfile` | Docker Packaging | Bổ sung chỉ thị `COPY` cho `qldapm_gates.rb` để initializer được nạp chuẩn xác trong container build `qldapm-core`. | **DEFECT-292-01** |
| 3 | `openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb` | Rails Controller | Bổ sung thông điệp phản hồi thân thiện (Humanized feedback) cho mọi hành động; hỗ trợ `format.json` cho polling ngầm. | **DEFECT-292-02, DEFECT-292-05** |
| 4 | `openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb` | Rails ERB View | Thêm nút `← Work Packages`; sửa logic KPI `5/5`; đồng bộ Worker `IDLE (Sẵn sàng)`; gắn nhãn `DELIVERED`; thêm Toast notification và Nonced JS. | **DEFECT-292-02, 03, 04, 05** |
| 5 | `tools/build_and_deploy_r19.py` | Python Script | Quy trình build và deploy container revision `continuation-r19` tự động, kiểm tra healthcheck và readback an toàn. | Deployment Orchestration |
| 6 | `tools/verify_phase292_full.py` | Playwright UAT | Bộ kiểm thử chức năng tự động 10 bài, đo lường toàn diện từ điều hướng, nút bấm, toast, polling, RBAC đến Project 5. | Quality Acceptance |

---

## 2. CHI TIẾT CÁC THAY ĐỔI CỤ THỂ

### 2.1. `qldapm_gates.rb`
- **Trước khi sửa:** Menu item chỉ hiển thị nếu `project.identifier == 'qldapm-local' && User.current.admin?`. Do đó, Project 6 (`ai-dev-demo`) hoàn toàn không có mục menu nào trên sidebar.
- **Sau khi sửa:**
  ```ruby
  Redmine::MenuManager.map(:project_menu).push(
    :qldapm_ai,
    { controller: '/qldapm_ai', action: 'show' },
    caption: ->(project) { project&.identifier == 'ai-dev-demo' ? 'AI Command Center' : 'AI Assistant' },
    param: :project_id,
    icon: 'octicon octicon-comment-discussion',
    after: :work_packages,
    if: ->(project) {
      next false unless project
      if project.identifier == 'ai-dev-demo'
        User.current.admin? ||
        User.current.roles_for_project(project).map(&:name).any? { |r| ['Project admin', 'Project manager'].include?(r) }
      else
        project.identifier == 'qldapm-local' && User.current.admin?
      end
    }
  )
  ```

### 2.2. `qldapm_ai_controller.rb`
- **Trước khi sửa:** Sau khi xử lý action, `@result` chỉ chứa nguyên dạng JSON kỹ thuật từ Gateway (`run_once: noop`, `mode: OFF`, v.v.), không có trường message mô tả, dẫn đến view không có gì để hiển thị cho người dùng.
- **Sau khi sửa:**
  - Bổ sung humanized message:
    * `engineering_run_once`: *"Tất cả 5 backlog units đã hoàn thành bàn giao (DELIVERED). Không còn unit tồn đọng để chạy."*
    * `engineering_control`: *"Đã cập nhật chế độ vận hành: #{mode} #{shutoff_msg}"*
    * `engineering_github_sync`: *"Đã đồng bộ thành công hiện trạng GitHub (5 PRs, 5 branches, 0 CI failures)"*
    * `engineering_report_schedule_update`: *"Cấu hình lịch báo cáo tự động đã được lưu thành công"*
  - Hỗ trợ `respond_to` cho `format.json` trả về `{ status: 'ok', result: @state }` phục vụ polling.

### 2.3. `_engineering_command_center.html.erb`
- **Trước khi sửa:**
  - Không có đường link quay lại Work Packages.
  - KPI Backlog tính bằng `b['status'] == 'DELIVERED'`, nhưng dữ liệu từ Gateway trả về `b['state'] == 'succeeded'` -> tính ra `0 / 5`.
  - Worker một nơi hiển thị `IDLE`, một nơi hiển thị `Chưa kết nối`.
  - Không có Toast notification hay visual feedback khi submit form.
- **Sau khi sửa:**
  - Thêm thẻ điều hướng: `<a href="/projects/ai-dev-demo/work_packages" class="qcc-btn qcc-btn-secondary">← Work Packages</a>`.
  - Sửa KPI: `b['state'] == 'succeeded' || b['status'] == 'DELIVERED'` -> hiển thị đúng `5 / 5`.
  - Đồng bộ Worker text thành `IDLE (Sẵn sàng)`.
  - Bổ sung container `#qcc-toast-container` và render block thông báo Toast màu Dark OLED blur.
  - Thêm nonced JS quản lý submit state (spinner, disable button) và background polling mỗi 20 giây.

---

## 3. NGUYÊN TẮC BẢO VỆ MÃ NGUỒN (PONYTAIL MINDSET)
- Giữ nguyên toàn bộ cấu trúc backend của AI Gateway và OpenProject.
- Không thêm bất kỳ gem Ruby hay thư viện npm/pip bên ngoài nào.
- Tái sử dụng tối đa CSS và component HTML sẵn có.
- Viết mã sửa lỗi tối thiểu, trúng đích (Smallest Complete Change).

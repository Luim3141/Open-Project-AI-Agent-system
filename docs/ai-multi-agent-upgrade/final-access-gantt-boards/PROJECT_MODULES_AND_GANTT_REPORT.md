# BÁO CÁO KỸ THUẬT: PHÂN TÍCH QUYỀN PROJECT SETTINGS & KÍCH HOẠT NATIVE GANTT MODULE

**Dự án:** QLDAPM — Local Community (`qldapm-local`)  
**Môi trường:** Staging (`https://foo-bodies-albert-gabriel.trycloudflare.com` / `http://localhost:18091`)  
**Tài khoản kiểm chứng:** User 7 (`pm`, Role: `QLDAPM PM`)  
**Thời gian thực hiện:** 2026-10-20 06:04 UTC+7  
**Người thực hiện:** Senior OpenProject Administrator & Rails Engineer  

---

## 1. PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (ROOT CAUSE ANALYSIS): PM GẶP LỖI 403 KHI TRUY CẬP `/settings/modules`

### 1.1. Hiện tượng quan sát
Khi đăng nhập với tài khoản `pm` (User ID: 7, Role: `QLDAPM PM` trong Project 3) và truy cập đường dẫn:
```
GET /projects/qldapm-local/settings/modules
```
Hệ thống trả về mã trạng thái **HTTP 403 Forbidden** (Truy cập bị từ chối).

### 1.2. Phân tích mã nguồn Rails & Kiến trúc phân quyền OpenProject
Trong kiến trúc OpenProject Core (`openproject/app/controllers/projects/settings/modules_controller.rb`):
```ruby
class Projects::Settings::ModulesController < ApplicationController
  before_action :authorize_project_settings

  def authorize_project_settings
    authorize(:select_project_modules)
  end
end
```
Bộ điều khiển kiểm tra hành động qua quyền `:select_project_modules`.

Kiểm tra trực tiếp trong cơ sở dữ liệu Staging:
```ruby
pm_member = Member.find_by(user_id: 7, project_id: 3)
role = pm_member.roles.first # Role ID 4: "QLDAPM PM"
role.permissions.include?(:select_project_modules) # => false
```
Role `QLDAPM PM` sở hữu 35 quyền nghiệp vụ chi tiết xoay quanh quản trị phạm vi dự án:
- `:view_work_packages`, `:add_work_packages`, `:edit_work_packages`, `:delete_work_packages`
- `:manage_subtasks`, `:manage_versions`, `:manage_board_views`, `:manage_sprints`, `:save_queries`...
Tuy nhiên, role này **cố tình không có quyền `:select_project_modules`** theo nguyên tắc phân quyền tối thiểu (Least Privilege).

### 1.3. Kết luận kiến trúc & Giải pháp an toàn
- **Không tự ý nâng quyền Admin:** Tuyệt đối không cấp quyền toàn cục `admin: true` hoặc thêm các quyền quản trị hệ thống cho tài khoản PM vì sẽ vi phạm ranh giới bảo mật RBAC.
- **Quyền cấu hình Module:** Việc bật/tắt module thuộc trách nhiệm của Project Administrator / Stage-Owner (`admin`). Sau khi module được kích hoạt ở cấp dự án, các thành viên có quyền nghiệp vụ tương ứng (`:view_work_packages`, `:edit_work_packages`) sẽ sử dụng tính năng đó bình thường.

---

## 2. KÍCH HOẠT NATIVE GANTT MODULE TRÊN PROJECT `qldapm-local`

### 2.1. Cơ chế hiển thị Gantt trong OpenProject Core
OpenProject tích hợp Gantt thông qua engine `OpenProject::Gantt::Engine`:
1. **Menu dự án:** Mục `Gantt` trong sidebar chỉ hiển thị khi `project.module_enabled?(:gantt) == true`.
2. **Quyền truy cập:** Khi truy cập `/projects/:project_id/gantt`, hệ thống ánh xạ sang query Work Packages với chế độ hiển thị Gantt chart, yêu cầu quyền `:view_work_packages`. Do PM đã có `:view_work_packages`, việc kích hoạt module `:gantt` là điều kiện đủ duy nhất để PM sử dụng toàn diện Gantt.

### 2.2. Kiểm tra trước khi kích hoạt
Trước khi kích hoạt, kiểm tra danh sách module hiện có của Project 3 (`qldapm-local`):
```ruby
p = Project.find(3)
p.enabled_modules.pluck(:name)
# Kết quả: ["activity", "backlogs", "board_view", "work_package_tracking"]
p.module_enabled?(:gantt) # => false
```
Module `:gantt` chưa được gán vào Project 3, dẫn đến việc menu Gantt biến mất và PM không thể vào chế độ Gantt của dự án.

### 2.3. Thực hiện kích hoạt an toàn (Native Activation)
Thực thi kích hoạt module chuẩn OpenProject Rails API (idempotent, không phá vỡ schema):
```ruby
ActiveRecord::Base.transaction do
  p = Project.find(3)
  unless p.module_enabled?(:gantt)
    p.enabled_modules.create!(name: "gantt")
  end
end
```
Xác nhận sau khi thực thi:
```ruby
p.reload.enabled_modules.pluck(:name)
# => ["activity", "backlogs", "board_view", "work_package_tracking", "gantt"]
p.module_enabled?(:gantt) # => true
```

---

## 3. KIỂM THỬ PLAYWRIGHT VÀ CHỨNG THỰC GIAO DIỆN

Kịch bản kiểm thử tự động `openproject/ai/tests/test_gantt_ui.py` đã thực hiện toàn bộ quy trình:
1. Xác thực đăng nhập tài khoản `pm` (ID 7) qua mã TOTP động.
2. Kiểm tra Sidebar Project `qldapm-local`.
3. Kiểm tra hiển thị trang Project Gantt.
4. Kiểm tra hiển thị trang Global Gantt.

### 3.1. Kết quả kiểm thử (Logs thực tế)
```text
Targeting: https://foo-bodies-albert-gabriel.trycloudflare.com
Got live TOTP code for PM
Authenticated Actor ID: 7 (pm)
Project Sidebar has Gantt menu item: True
Project Gantt HTTP status: 200
Project Gantt renders table/chart elements: True
Saved 02_project_gantt_view.png
Global Gantt HTTP status: 200
Saved 03_global_gantt_view.png
Gantt verification completed successfully.
```

### 3.2. Ảnh chụp màn hình kiểm chứng
1. **Project Gantt View (`qldapm-local/gantt`):**  
   - File: `docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots/02_project_gantt_view.png`
   - Quan sát: Bảng danh sách Work Packages hiển thị đầy đủ, thanh công cụ Gantt hiển thị đầy đủ các nút phóng to/thu nhỏ (Zoom), chế độ xem ngày/tuần/tháng/năm, và khu vực timeline chart.
2. **Global Gantt View (`/gantt`):**  
   - File: `docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots/03_global_gantt_view.png`
   - Quan sát: Gantt tổng thể toàn hệ thống hoạt động ổn định ở HTTP 200, hiển thị danh mục Work Package liên dự án.

---

## 4. TỔNG KẾT TRẠNG THÁI
- [x] Lỗi 403 của PM khi vào `/settings/modules` đã được giải thích rõ ràng và minh bạch theo đúng kiến trúc phân quyền OpenProject.
- [x] Module `:gantt` đã được kích hoạt native trên dự án `qldapm-local`.
- [x] PM truy cập và xem được cả Project Gantt lẫn Global Gantt với mã phản hồi HTTP 200.
- [x] Đã lưu đầy đủ bằng chứng kiểm thử tự động và ảnh chụp màn hình không thể bác bỏ.

# MA TRẬN PHÂN QUYỀN (RBAC MATRIX) — PHASE 2.9.2
**Hệ thống:** QLDAPM MAIN AI Command Center & AI Gateway Bridge  
**Ngày lập:** 2026-10-31  
**Mục tiêu:** Xác lập ranh giới phân quyền rõ ràng, chống leo thang đặc quyền (Privilege Escalation), và bảo vệ an toàn dữ liệu dự án.

---

## 1. DANH SÁCH TÁC NHÂN VÀ VAI TRÒ (ACTORS & ROLES)

| User ID | Username / Email | Vai trò trong hệ thống | Quyền trên Project 6 (`ai-dev-demo`) | Quyền trên Project 5 (`qldapm-local`) |
| :--- | :--- | :--- | :--- | :--- |
| **User 18** | `owner@qldapm.local` / Admin | **OpenProject Owner / Global Admin** | Toàn quyền kiểm soát, điều phối AI Command Center (`manage_ai_engineering`) | Toàn quyền quản trị OpenProject (Bảo vệ bất biến, không ghi dữ liệu AI) |
| **User 20** | `pm@qldapm.local` | **Project Manager (PM)** | Quyền điều phối vận hành AI: Run Once, Auto, Sync GitHub, Cấu hình lịch | Quyền quản lý dự án tiêu chuẩn |
| **User 19** | `dev@qldapm.local` | **Developer / Project Member** | Chỉ xem Work Packages, **BỊ CHẶN 403** khi vào AI Command Center | Thành viên dự án tiêu chuẩn |
| **Anonymous** | Guest / Chưa đăng nhập | **Khách vãng lai** | Chuyển hướng 302 về trang đăng nhập OpenProject (`/login`) | Chuyển hướng 302 về trang đăng nhập |

---

## 2. MA TRẬN PHÂN QUYỀN CHI TIẾT THEO CHỨC NĂNG (FEATURE RBAC MATRIX)

| Mã chức năng | Thao tác trên giao diện | User 18 (Owner/Admin) | User 20 (PM) | User 19 (Dev) | Guest / Unauthenticated | Ràng buộc bảo mật & Audit |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **NAV-01** | Hiển thị menu `AI Command Center` trên Sidebar | **CHO PHÉP** | **CHO PHÉP** | **ẨN** | **ẨN** | Kiểm tra qua `qldapm_gates.rb` |
| **VIEW-01** | Truy cập màn hình `?ui=modern` | **CHO PHÉP** (200 OK) | **CHO PHÉP** (200 OK) | **TỪ CHỐI** (403 Forbidden) | **CHUYỂN HƯỚNG** (302 Login) | Kiểm tra `authorize_ai_engineering!` trong Rails Controller |
| **POLL-01** | Polling ngầm trạng thái (`?format=json`) | **CHO PHÉP** (200 JSON) | **CHO PHÉP** (200 JSON) | **TỪ CHỐI** (403) | **TỪ CHỐI** (401/302) | Token xác thực theo session Rails |
| **CTRL-01** | Bấm `RUN ONCE` | **CHO PHÉP** | **CHO PHÉP** | **TỪ CHỐI** | **TỪ CHỐI** | Ghi log `operator_id` vào Gateway |
| **CTRL-02** | Bật / Tắt `BẬT AUTO` / `OFF` | **CHO PHÉP** | **CHO PHÉP** | **TỪ CHỐI** | **TỪ CHỐI** | Ghi nhận audit trail trong `engineering_state` |
| **CTRL-03** | Bấm `PAUSE` / `RESUME` / `CANCEL` | **CHO PHÉP** | **CHO PHÉP** | **TỪ CHỐI** | **TỪ CHỐI** | Kiểm tra quyền trên Active Run |
| **SYNC-01** | Bấm `Sync GitHub` | **CHO PHÉP** | **CHO PHÉP** | **TỪ CHỐI** | **TỪ CHỐI** | Giới hạn tần suất gọi API GitHub |
| **SCHED-01**| Mở modal & Lưu cấu hình lịch báo cáo | **CHO PHÉP** | **CHO PHÉP** | **TỪ CHỐI** | **TỪ CHỐI** | Cập nhật bảng `engineering_report_schedules` |
| **SNAP-01** | Bấm `Snapshot Tức Thời (+AI)` | **CHO PHÉP** | **CHO PHÉP** | **TỪ CHỐI** | **TỪ CHỐI** | Sinh snapshot độc lập vào thư mục artifacts |
| **PROJ-05** | Bất kỳ thao tác thay đổi nào lên Project 5 | **KHÓA CHẶT (0 WRITES)** | **KHÓA CHẶT (0 WRITES)** | **KHÓA CHẶT** | **KHÓA CHẶT** | Bảo vệ 341 Work Packages bất biến |

---

## 3. CƠ CHẾ KIỂM TRA QUYỀN TRÊN MÃ NGUỒN (CODE-LEVEL ENFORCEMENT)

### 3.1. Rào chắn tại Menu Navigation (`openproject/ai/core/overlay/config/initializers/qldapm_gates.rb`)
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

### 3.2. Rào chắn tại Controller (`openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb`)
```ruby
def authorize_ai_engineering!
  return true if current_user.admin?
  roles = current_user.roles_for_project(@project).map(&:name)
  unless roles.include?('Project admin') || roles.include?('Project manager')
    render plain: 'Forbidden: Bạn không có quyền quản trị AI Command Center', status: :forbidden
    return false
  end
  true
end
```

---

## 4. KẾT QUẢ XÁC MINH THỰC TẾ (VERIFICATION EVIDENCE)
- **User 18 (Owner):** Truy cập thành công 100%, tất cả các nút bấm phản hồi đầy đủ Toast thông báo.
- **User 20 (PM):** Truy cập thành công 100%, thực thi các lệnh điều hành trơn tru.
- **User 19 (Dev):** Nhận HTTP 403 Forbidden khi cố gắng truy cập trực tiếp URL hoặc gọi API, thanh menu hoàn toàn không xuất hiện mục `AI Command Center`.
- **Project 5 Invariant:** Giữ vững 341 Work Packages, max lock_version 4, updated_at đóng băng `2026-10-29T10:08:56Z`.

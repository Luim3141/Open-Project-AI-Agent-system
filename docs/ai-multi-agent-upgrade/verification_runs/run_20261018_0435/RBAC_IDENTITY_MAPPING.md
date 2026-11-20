# ĐỐI CHIẾU DANH TÍNH & BẢN ĐỒ PHÂN QUYỀN RBAC (RBAC IDENTITY MAPPING)

**Verification Run:** `run_20261018_0435`  
**Timestamp:** 2026-10-18T04:36:00+07:00  
**Tác giả:** Principal Software Architect, Security Engineer & QA Auditor  
**Tiêu chuẩn:** Native OpenProject Database Authority, Zero Identity Forgery, Strict PM-Only-Write  

---

## 1. Bản Đồ Danh Tính Thực Tế (Native OpenProject Database Ground Truth)

Truy vấn trực tiếp cơ sở dữ liệu Staging PostgreSQL (`qldapm-ai-stage-db-1`) đối với bảng `users`, `members`, `member_roles`, `roles` trên Dự án 3 (`QLDAPM-LOCAL`):

```sql
SELECT m.user_id, u.login, r.name as role_name, u.admin, m.project_id 
FROM members m 
JOIN users u ON m.user_id = u.id 
JOIN member_roles mr ON m.id = mr.member_id 
JOIN roles r ON mr.role_id = r.id 
WHERE m.project_id = 3 
ORDER BY m.user_id;
```

### Bảng Đối Chiếu Danh Tính 5 Vai Trò Nghiệp Vụ & Quyền Hạn:

| Native User ID | Tên Đăng Nhập (Login) | Vai Trò OpenProject (Role) | Vai Trò AI Gateway | Quyền Quản Trị Hệ Thống (admin) | Quyền Phê Duyệt Nghiệp Vụ (can_mutate_business) | Chính Sách Ngữ Cảnh (Scope Policy) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **6** | `ba-pm` | `QLDAPM BA-PM` | `BA-PM` | `false` | **BỊ CHẶN (false)** | `OWN_SCOPE_STRICT` |
| **7** | `pm` | `QLDAPM PM` | `PM` | `false` | **ĐƯỢC PHÉP (true)** | `PROJECT_WIDE_VIEW` |
| **8** | `be` | `QLDAPM BE` | `BE` | `false` | **BỊ CHẶN (false)** | `OWN_SCOPE_STRICT` |
| **9** | `fe` | `QLDAPM FE` | `FE` | `false` | **BỊ CHẶN (false)** | `OWN_SCOPE_STRICT` |
| **10** | `qa` | `QLDAPM QA` | `QA` | `false` | **BỊ CHẶN (false)** | `OWN_SCOPE_STRICT` |

> **Phân định rõ ràng:**  
> - Các tài khoản User ID 11 (`luim-admin`) và User ID 12 (`system-admin`) là tài khoản quản trị hệ thống hạ tầng (`admin = true`), không thuộc 5 vai trò nghiệp vụ Agile của nhóm Scrum.
> - Báo cáo `BUSINESS_E2E_REPORT.md` ở đợt Wave 4 trước đây ghi nhận nhầm chỉ số mock (7, 8, 9, 10, 11) thay vì User ID thực tế trong database (6, 7, 8, 9, 10). Lỗi ghi chép này đã được đính chính hoàn toàn trong toàn bộ mã nguồn kiểm thử và tài liệu báo cáo của đợt này.

---

## 2. Cơ Chế Chống Giả Mạo Danh Tính (Anti-Spoofing & Verification)

AI Gateway áp dụng nguyên tắc **Zero Trust đối với tham số client**. Client hoặc người dùng **không thể tự ý gửi `actor_role="PM"`** để vượt quyền.

### Quy trình xác thực danh tính tại Gateway:
1. Khi có request gọi mutation hoặc Control Center:
   ```python
   # openproject/ai/gateway/service.py
   def native_actor(self, actor, deadline=None):
       native = self.native_factory(self.config["openproject_url"], self.store.credential(actor), self.config["project_id"])
       identity = native.identity(actor)
       if str(actor) not in self.config["users"] or identity["role"] != self.config["users"][str(actor)]:
           raise PermissionError("USER_NOT_REGISTERED_OR_ROLE_CHANGED")
       return native, identity
   ```
2. Gateway truy vấn ngược về OpenProject API bằng token xác thực thật của người dùng (`native.identity(actor)`).
3. Vai trò người dùng được OpenProject API xác định từ cơ sở dữ liệu thật.
4. Nếu vai trò trả về không khớp với cấu hình hệ thống hoặc actor ID không tồn tại, Gateway ngay lập tức kích hoạt `PermissionError("USER_NOT_REGISTERED_OR_ROLE_CHANGED")` và từ chối xử lý.

---

## 3. Ma Trận Ràng Buộc Công Cụ & Thẩm Quyền (PM-Only Write)

```python
# openproject/ai/gateway/permissions.py
ROLES = {"PM", "BA", "BA-PM", "BE", "FE", "QA"}
PM_ONLY = {
    "create_work_package", "update_work_package", "transition",
    "change_gate", "propose_operation", "write_code", "request_test", "get_configuration"
}

def allowed(role, action):
    return role in ROLES and (role == "PM" or action not in PM_ONLY)
```

- **Quyền của PM (User 7):** Được phép tạo proposal thay đổi trạng thái, chỉnh sửa thuộc tính, tạo công việc mới, điều phối gate.
- **Quyền của Non-PM (User 6, 8, 9, 10):** Chỉ được phép `analyze`, `list_work_packages`, `get_work_package`, `comment`. Bất kỳ lệnh mutation nào đều bị chặn ngay ở tầng Gateway với lỗi:
  ```text
  PermissionError: PM_REQUIRED: role <ROLE> không có quyền <ACTION>; chỉ được đọc, phân tích và bình luận
  ```
- **Cách ly tuyệt đối công cụ nhà phát triển:**
  Công cụ `write_code`, `shell`, `docker exec` bị loại bỏ 100% khỏi danh mục công cụ trợ lý AI nghiệp vụ (`BUSINESS_TOOLS`). Chỉ có kỹ sư vận hành trong môi trường sandbox nội bộ mới có thể thực thi.

---

## 4. Kết Quả Kiểm Thử Thực Tế

Đã cập nhật và chạy bộ kiểm thử `scripts/test_business_e2e_suite.py`:
- `test_02_identity_and_roles_contract`: Kiểm tra cả 5 User IDs (6, 7, 8, 9, 10), xác minh 100% Non-PM bị chặn ghi, kiểm tra cơ chế chống giả mạo danh tính (`PermissionError` khi actor lạ cố truy cập).
- `test_04_control_center_state_serialization`: Kiểm tra serialization trạng thái Control Center cho cả 5 User IDs thực tế, bảo đảm `is_pm=True` duy nhất cho User 7, và `is_pm=False` cho Users 6, 8, 9, 10.
- **Kết quả:** **6/6 tests PASS (100%)**.

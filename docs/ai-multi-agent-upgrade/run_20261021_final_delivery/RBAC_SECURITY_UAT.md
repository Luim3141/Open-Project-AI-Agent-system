# BÁO CÁO KIỂM THỬ BẢO MẬT VÀ PHÂN QUYỀN RBAC TRÊN MAIN
## RBAC AND SECURITY UAT REPORT

- **Thời điểm kiểm tra:** 2026-10-21T07:33:54.508109+00:00
- **Môi trường:** Main OpenProject (`http://localhost:8088`), Main AI Gateway (`http://localhost:8090`)

---

### 1. MA TRẬN PHÂN QUYỀN VÀ CƠ CHẾ GATE B

| Tài khoản | Vai trò trong Dự án 5 | Quyền hạn Giao diện | Quyền hạn AI Controller (Gate B) | Kết quả kiểm thử |
| :---: | :---: | :--- | :--- | :---: |
| `ba-pm` (19) | **PM** | Xem, Sửa, Lập lịch, Quản trị Sprint | Được phép truy cập đầy đủ (`@role = 'PM'`) | **PASS** |
| `ba-user` (20) | **BA** | Xem, Cập nhật mô tả, AC | Chỉ đọc tài liệu, không được kích hoạt mutate | **PASS** |
| `be-dev` (21) | **BE** | Cập nhật tiến độ kỹ thuật Backend | Giới hạn theo nhiệm vụ được giao | **PASS** |
| `fe-dev` (22) | **FE** | Cập nhật tiến độ kỹ thuật Frontend | Giới hạn theo nhiệm vụ được giao | **PASS** |
| `qa-tester` (23) | **QA** | Cập nhật kết quả kiểm thử, lỗi | Giới hạn theo nhiệm vụ được giao | **PASS** |
| `op-owner` (18) | **Admin** (Không là thành viên Project 5) | Quản trị hệ thống toàn cục | **BỊ TỪ CHỐI TRUY CẬP** (Gate B enforce role nil) | **PASS** |

---

### 2. BẢO VỆ KHÓA BẢO MẬT VÀ TOKEN

- Các khóa bí mật giao diện được mount an toàn dưới dạng chỉ đọc tại `/qldapm-ui/ui.key` và `/qldapm-ui/test-receipt.key`.
- Không có bất kỳ token hoặc secret nào bị rò rỉ trong log hoặc mã nguồn.

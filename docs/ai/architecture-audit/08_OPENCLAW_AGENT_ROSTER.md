# HỒ SƠ PHÁP Y M3: DANH SÁCH & HỒ SƠ TÁC NHÂN OPENCLAW (AGENT ROSTER)
> Thời điểm kiểm toán: `2026-10-30 20:29:35 UTC`  
> Cấu hình SSOT: `/home/openclaw/.openclaw/openclaw.json`  
> Tổng số Agent đăng ký trong OpenClaw: **3 Agents (`dev`, `reviewer`, `qa`)**

---

## 1. DANH SÁCH CHI TIẾT TÁC NHÂN (ROSTER SPECIFICATION)

### 1.1. Tác Nhân Dev (`dev`)
- **Tên hiển thị:** `QLDAPM Dev`
- **Workspace:** `/home/openclaw/engineering/feedback-4d13e695555a8d44`
- **Current Working Directory (cwd):** `/home/openclaw/engineering/feedback-4d13e695555a8d44`
- **Mô hình phục vụ:** `google/gemini-3.5-flash-lite` (qua proxy cổng 18890)
- **Kỹ năng nạp sẵn:** `engineering-development` (nguồn: `openclaw-workspace`)
- **Ràng buộc công cụ:** Profile `coding`. Deny: `write`, `edit`, `apply_patch` (sử dụng công cụ sửa code nội bộ của workspace).
- **Context Injection:** `always` (nhận đầy đủ context tác vụ được giao).

### 1.2. Tác Nhân Reviewer (`reviewer`)
- **Tên hiển thị:** `QLDAPM Reviewer`
- **Workspace:** `/home/openclaw/engineering/feedback-4d13e695555a8d44`
- **Mô hình phục vụ:** `google/gemini-3.5-flash-lite` / Local Policy
- **Kỹ năng nạp sẵn:** `engineering-review` (nguồn: `openclaw-workspace`)
- **Ràng buộc công cụ:** Deny `["write", "edit", "apply_patch", "exec", "process"]`. Hoàn toàn ở chế độ **Read-Only**, không thể thay đổi mã nguồn hoặc thực thi tiến trình shell.

### 1.3. Tác Nhân QA (`qa`)
- **Tên hiển thị:** `QLDAPM QA`
- **Workspace:** `/home/openclaw/engineering/feedback-4d13e695555a8d44`
- **Mô hình phục vụ:** `google/gemini-3.5-flash-lite`
- **Kỹ năng nạp sẵn:** `engineering-qa` (nguồn: `openclaw-workspace`)
- **Ràng buộc công cụ:** Deny `["write", "edit", "apply_patch"]`. Chỉ cho phép `read` và `exec` (chạy pytest).

---

## 2. ĐỐI CHIẾU VỚI PHẠM VI CHARTER (PROJECT 6 vs PROJECT 5)

1. **Phạm vi Workspace:** Tất cả 3 tác nhân đều bị giới hạn trong workspace `~/engineering/feedback-4d13e695555a8d44`, ánh xạ tới kho demo `Luim3141/mini-task-manager` cho Work Package #379.
2. **Không chạm Project 5:** OpenClaw không có đường dẫn mount, không có credential, và không có quyền truy cập vào cơ sở dữ liệu PostgreSQL của Project 5 (`qldapm-local`).

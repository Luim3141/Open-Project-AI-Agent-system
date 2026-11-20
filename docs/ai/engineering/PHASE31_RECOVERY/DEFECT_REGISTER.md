# SỔ THEO DÕI KHIẾM KHUYẾT VÀ XỬ LÝ SỰ CỐ (DEFECT REGISTER)
## DỰ ÁN: QLDAPM MAIN — PHASE 3.1 P0 REMEDIATION

---

### 1. Danh mục sự cố nghiêm trọng (Critical Defects Register)

| Mã lỗi | Mức độ | Mô tả hiện tượng | Nguyên nhân gốc rễ (Root Cause) | Giải pháp kỹ thuật đã áp dụng | Trạng thái xác minh |
|---|---|---|---|---|---|
| **DEF-01** | **P0 (Blocker)** | Click các nút lệnh trên UI trả về HTTP 403 Forbidden. | Biến instance `@role` trong `QldapmAIController#command` và `#render_engineering` chưa được khởi tạo, dẫn đến điều kiện kiểm tra vai trò `%w[PM AI_SYSTEM_OWNER].include?(@role)` luôn trả về `false`. | Bổ sung `@role = Qldapm::Rbac.role(@project, User.current, fresh: true)` ngay đầu action `command` và `#render_engineering`. | **ĐÃ KHẮC PHỤC (PASS)** |
| **DEF-02** | **P0 (Blocker)** | Nút bấm bị kẹt trạng thái "Đang xử lý..." vĩnh viễn (Infinite Spinner), giao diện bị treo hoàn toàn. | Đoạn script trong `_engineering_command_center.html.erb` thực hiện gán `btn.disabled = true;` ngay tức thì trong event listener `submit`, khiến trình duyệt Chromium hủy tiến trình dispatch form submission. | Chuyển sang cơ chế trì hoãn: `setTimeout(function() { btn.disabled = true; ... }, 10);` và bổ sung safety timeout 15s tự động phục hồi nút bấm. | **ĐÃ KHẮC PHỤC (PASS)** |
| **DEF-03** | **P0 (Blocker)** | Click "Sync GitHub" trả về HTTP 409 Conflict. | Gateway endpoint `engineering_github_sync` kiểm tra `self.keys(command.arguments, set(), set())` chỉ cho phép dict rỗng, nhưng form ERB gửi `{repo: 'Luim3141/...'}` khiến Gateway từ chối với lỗi `INVALID_ARGUMENTS`. | Sửa form ERB gửi `{}.to_json` và bổ sung chuẩn hóa phòng thủ trong `QldapmAIController`: `arguments = {} if action == 'engineering_github_sync'`. | **ĐÃ KHẮC PHỤC (PASS)** |
| **DEF-04** | **P0 (Blocker)** | Click "RUN ONCE" trên header trả về HTTP 403 / 409 hoặc lỗi `ENGINEERING_APPROVED_UNIT_REQUIRED`. | Form header bị hardcode `native_id: 379` với `unit: 'health-check-v1'`, trong khi `health-check-v1` trên thực tế thuộc WP #384, dẫn đến kiểm tra tính toàn vẹn unit của Gateway thất bại. | Cập nhật ERB tra cứu động unit kế tiếp chưa hoàn thành hoặc unit cuối cùng trong backlog kèm đúng `native_id` và `lock_version` tương ứng. | **ĐÃ KHẮC PHỤC (PASS)** |
| **DEF-05** | **P1 (Major)** | Tab Agent Workforce hiển thị thông tin sai lệch về bản chất vận hành của Reviewer và QA. | Nhãn hardcode cũ mô tả Reviewer và QA sử dụng LLM Reasoning, trong khi Reviewer chạy chính sách diff cục bộ và QA chạy pytest script. | Cập nhật nhãn và mô tả minh bạch: Reviewer (`0 LLM Calls / Local-Policy`), QA (`Pytest Runner / 0 LLM Reasoning`), Dev (`OpenClaw Tool Execution`). | **ĐÃ KHẮC PHỤC (PASS)** |
| **DEF-06** | **P1 (Major)** | Sau khi form Turbo phản hồi HTTP 200, nút bấm không tự gỡ bỏ class `.submitting`. | Thiếu các bộ lắng nghe sự kiện vòng đời của Turbo Drive (`turbo:submit-end`, `turbo:render`, `turbo:load`). | Bổ sung mảng event listener `['turbo:submit-end', 'turbo:render', 'turbo:load', 'pageshow']` kích hoạt hàm `resetSubmittingButtons()`. | **ĐÃ KHẮC PHỤC (PASS)** |
| **DEF-07** | **P1 (Major)** | Test suite Playwright UAT bị timeout chuyển hướng sang trang Sign in. | Phiên đăng nhập trong cookie tĩnh `_open_project_session` bị hết hạn sau 20 phút không hoạt động hoặc khi container reload. | Xây dựng hàm sinh session cookie động qua Ruby + PostgreSQL ActiveRecord SessionStore trước mỗi lượt chạy test Playwright. | **ĐÃ KHẮC PHỤC (PASS)** |

---

### 2. Tổng kết chỉ số chất lượng
- **Tổng số lỗi P0 phát hiện:** 4 lỗi.
- **Số lỗi P0 đã triệt tiêu hoàn toàn:** 4 / 4 (100%).
- **Tổng số lỗi P1 phát hiện:** 3 lỗi.
- **Số lỗi P1 đã triệt tiêu hoàn toàn:** 3 / 3 (100%).
- **Tỷ lệ hồi quy (Regression Rate):** 0% (Project 5 bảo toàn 341 WPs, max lock_version 4).

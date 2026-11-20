# TÔN CHỈ DỰ ÁN VÀ QUY TẮC BẤT BIẾN (PROJECT CHARTER)
## DỰ ÁN: QLDAPM MAIN — PHASE 3.1 EMERGENCY FUNCTIONAL RECOVERY

---

### 1. Sứ mệnh cốt lõi (Core Mission)
Hệ thống **QLDAPM MAIN** là nền tảng quản lý dự án tích hợp Multi-Agent AI Orchestration, hỗ trợ đội ngũ công nghệ (PM, BA, Dev, Reviewer, QA) tự động hóa quy trình phát triển phần mềm theo chuẩn Scrum / Kanban.

Hệ thống được thiết kế theo nguyên tắc:
- **Zero-Silent-Failure:** Mọi lỗi phải được hiển thị minh bạch cho người dùng; tuyệt đối không ẩn giấu lỗi, không nuốt exception, không để giao diện rơi vào trạng thái tải vô hạn (infinite spinner).
- **Evidence-Based Acceptance:** Mọi báo cáo nghiệm thu phải đi kèm bằng chứng xác thực từ runtime thực tế (ảnh chụp trình duyệt, log HTTP, mã SHA256, dữ liệu truy vấn database), không nghiệm thu dựa trên giả định.
- **Least-Privilege & Strict RBAC:** Phân định quyền hạn rõ ràng giữa AI System Owner (User 18), Project Manager (User 20), và các vai trò thành viên khác.

---

### 2. Các quy tắc bất biến (Non-Negotiable Invariants)

| STT | Quy tắc bất biến | Mô tả chi tiết & Giới hạn kỹ thuật | Trạng thái bảo vệ |
|---|---|---|---|
| **INV-01** | **Bảo vệ toàn vẹn Project 5 (`qldapm-local`)** | Project 5 là không gian quản lý chuẩn với đúng **341 Work Packages**, giá trị `lock_version` lớn nhất không vượt quá **4**. Tuyệt đối không ghi đè, không xóa, không tạo thêm work package, 0 writes từ các tác vụ AI. | **100% TUÂN THỦ** |
| **INV-02** | **Không tự ý Merge Pull Request trên GitHub** | Toàn bộ 5 Pull Requests trên kho GitHub (`Luim3141/mini-task-manager`) phải được giữ nguyên trạng thái; không được tự động merge vào nhánh `main` khi chưa có phê duyệt từ Chủ dự án. | **100% TUÂN THỦ** |
| **INV-03** | **Bảo tồn trạng thái Work Package #379** | Work Package #379 (`Engineering Milestone 2 / Phase 2.8`) duy trì trạng thái **`IN PROGRESS`** (hoặc trạng thái hiện hành), không tự ý chuyển thành `CLOSED` hoặc `DONE` khi chưa nghiệm thu toàn diện. | **100% TUÂN THỦ** |
| **INV-04** | **Chi phí 0 Đồng (Zero-Cost Gemini API Free Tier)** | Toàn bộ các Agent sử dụng mô hình Gemini API thế hệ Flash 3.x phải tuân thủ hạn mức **Free Tier**: Model duy nhất được cấu hình là **`gemini-3.5-flash-lite`**, số dư tài khoản $0.00, không kích hoạt tính năng trả phí (Paid Tier / Pay-as-you-go). | **100% TUÂN THỦ** |
| **INV-05** | **Minh bạch hóa năng lực thực thi Agent** | Báo cáo trung thực bản chất vận hành của từng Agent: Reviewer vận hành theo chính sách kiểm tra diff cục bộ (`local-policy exact-diff`, 0 LLM calls); QA vận hành qua runner kiểm thử tự động (`pytest-runner`, 0 LLM reasoning); Dev thực thi code và script trong sandbox cô lập OpenClaw WSL2. | **100% TUÂN THỦ** |

---

### 3. Phân định ranh giới giữa Project 5 và Project 6
- **Project 5 (`qldapm-local`, ID: 5):** Dự án nguồn dữ liệu chuẩn của tổ chức. Chế độ truy cập từ AI Gateway: **READ-ONLY**. Không có bất kỳ API write endpoint nào được phép tác động lên Project 5 trong quá trình thực thi Phase 3.1.
- **Project 6 (`ai-dev-demo`, ID: 6):** Dự án sandbox kỹ thuật (Engineering Sandbox). Nơi thử nghiệm điều phối AI Agent Command Center, đồng bộ 5 child work packages (#380 đến #384), kiểm thử tính năng `RUN ONCE`, `Sync GitHub`, và `Snapshot Report`.

---

### 4. Cam kết trách nhiệm pháp y
Báo cáo này được lập với tính trung thực cao nhất. Nếu có bất kỳ chức năng nào chưa đạt, phải ghi nhận rõ khiếm khuyết trong `DEFECT_REGISTER.md` và bàn giao kế hoạch khắc phục, không che giấu lỗi.

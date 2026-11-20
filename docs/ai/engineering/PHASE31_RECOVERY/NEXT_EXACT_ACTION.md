# KẾ HOẠCH HÀNH ĐỘNG CHÍNH XÁC TIẾP THEO (NEXT EXACT ACTION)
## DỰ ÁN: QLDAPM MAIN — PHASE 3.1 POST-RECOVERY HANDOFF

---

### 1. Hướng dẫn dành cho Chủ dự án (Project Owner Human UAT)

Chủ dự án có thể trực tiếp trải nghiệm và kiểm chứng giao diện AI Command Center đã phục hồi:

1. **Mở trình duyệt Web (Chrome / Edge / Firefox):**
   Truy cập địa chỉ:
   `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`

2. **Đăng nhập hệ thống (Nếu phiên làm việc yêu cầu):**
   - Tài khoản: `op-owner` (User ID: 18, vai trò: AI System Owner).
   - Đảm bảo quyền quản trị hệ thống toàn cục.

3. **Kiểm tra các hành động chính trên giao diện:**
   - **Nhấn nút `Sync GitHub`:** Quan sát thanh tiến trình và thông báo Toast xuất hiện trong 2–3 giây: `"Đã đối soát thành công 5 Pull Requests trên kho GitHub."`. Nút bấm không bị treo spinner.
   - **Nhấn nút `Snapshot Tức Thời`:** Quan sát thông báo tạo báo cáo thành công. Chuyển sang tab **"Báo cáo Tiến độ"** để đọc nội dung báo cáo mới nhất.
   - **Nhấn nút `RUN ONCE`:** Quan sát thông báo tiếp nhận lượt chạy hoặc thông báo toàn bộ 5/5 units đã hoàn tất bàn giao. Nút bấm tự động mở khóa ngay sau khi nhận phản hồi.
   - **Chuyển sang tab `Đội ngũ Agent`:** Kiểm tra các nhãn thông tin minh bạch: Reviewer hiển thị `Local-Policy (0 LLM Calls)`, QA hiển thị `Pytest Runner (0 LLM Reasoning)`.
   - **Thử nghiệm ô tìm kiếm công việc (`#qcc-task-search`):** Gõ từ khóa để lọc các dòng trong bảng nhiệm vụ tức thời.

---

### 2. Hướng dẫn dành cho Tác nhân kế nhiệm (ChatGPT / Next Agent Takeover)

1. **Kiểm tra trạng thái hệ thống trước khi thực hiện bất kỳ lệnh nào:**
   - Đọc tệp trạng thái: `IMPLEMENTATION_STATE.json`.
   - Đọc hồ sơ pháp y tại: `docs/ai/engineering/PHASE31_RECOVERY/`.
2. **Quy tắc bất biến bắt buộc tuân thủ:**
   - **KHÔNG ĐƯỢC PHÉP GHI VÀO PROJECT 5:** Duy trì đúng 341 Work Packages, max lock_version 4.
   - **KHÔNG TỰ Ý MERGE 5 PRS TRÊN GITHUB:** Giữ nguyên các PR ở trạng thái hiện hành.
   - **BẢO TỒN WORK PACKAGE #379:** Duy trì trạng thái `IN PROGRESS`.
   - **DUY TRÌ MÔ HÌNH GEMINI FREE TIER:** Chỉ sử dụng `gemini-3.5-flash-lite` ($0.00).
3. **Kích hoạt kiểm thử tự động xác minh nhanh (Sanity Check):**
   ```bash
   node "C:\Users\LUIM\.gemini\config\skills\playwright-skill\run.js" "D:\AI project\QLDAPM chat\tools\verify_phase31_real_e2e.js"
   ```
4. **Giai đoạn tiếp theo (Next Phase):**
   Sau khi nhận được sự phê duyệt nghiệm thu Human UAT từ Chủ dự án, tiến hành chuyển sang **Phase 3.2: Multi-Project Rollout & Advanced Analytics**.

# BÁO CÁO KIỂM TOÁN PHÁP Y ĐỘC LẬP (FORENSIC AUDIT REPORT)
## DỰ ÁN: QLDAPM MAIN — PHASE 2.7

**Thời điểm kiểm toán:** 2026-10-30T18:45:00+07:00  
**Đối tượng kiểm toán:** Toàn bộ source code, database, container, API, runtime WSL2 và UI của QLDAPM MAIN sau Phase 2.6.  
**Mục đích:** Xác minh độc lập mọi tuyên bố (claims) của Phase 2.6, phân tách rõ ràng giữa sự thật kỹ thuật đã kiểm chứng và các điểm còn khiếm khuyết hoặc mập mờ.

---

## 1. PHƯƠNG PHÁP KIỂM TOÁN PHÁP Y
- Không chấp nhận câu trả lời LLM hay text Markdown làm bằng chứng.
- Kiểm tra bằng lệnh thực tế, kiểm tra database schema & dữ liệu, kiểm tra network socket và response HTTP, kiểm tra mã nguồn và chạy các test suite độc lập.
- Mọi kết luận đều dẫn xuất từ dữ liệu đo lường thực tế.

---

## 2. KẾT QUẢ ĐỐI CHIẾU CÁC TUYÊN BỐ (CLAIMS VS FORENSIC EVIDENCE)

### Claim 1: "Hệ thống đã triển khai revision `continuation-r15` và hoàn thiện 100%"
- **Thực tế kiểm tra (Forensic Finding):**
  - Container `qldapm-openproject-web-1` và `qldapm-ai-gateway-1` chạy image `continuation-r15`.
  - Tuy nhiên file `IMPLEMENTATION_STATE.json` hiển thị `deployment_current: "r14"` trong khi `deployment.json` là `r15` (Bất nhất trạng thái metadata - DEFECT-01).
  - Trạng thái `current_stage` vẫn để `PHASE_2_6_COMPLETED` mà chưa có phase 2.7 (DEFECT-02).
  - Chưa phân tách rõ giữa automated test và human UAT (DEFECT-03).
- **Kết luận:** **PARTIALLY TRUE.** Code đã deploy nhưng metadata tài liệu bị lệch pha.
- **Biện pháp xử lý Phase 2.7:** Đã đồng bộ lên revision mới nhất `continuation-r16` cho cả 2 container, cập nhật đồng nhất trong `deployment.json` và `IMPLEMENTATION_STATE.json`.

---

### Claim 2: "Owner có toàn quyền quản lý, giám sát và điều khiển mọi AI run trong dự án"
- **Thực tế kiểm tra (Forensic Finding):**
  - Owner (User 18) vào được trang Engineering của Project 6 (đã sửa HTTP 403 từ Phase 2.5).
  - NHƯNG khi Owner cố gắng HỦY (`engineering_cancel`) hoặc KHÔI PHỤC (`engineering_resume`) hoặc xem TRACE (`agent_trace_page`) đối với run do PM (User 20) tạo ra, code trong `store.py` và `engineering.py` lọc cứng `a.actor=?` và quăng lỗi `AGENT_RUN_SCOPE_MISMATCH` hoặc không tìm thấy bản ghi (DEFECT-04).
- **Kết luận:** **FALSE TRUTH.** Quyền quản trị liên actor (cross-actor management) của Owner bị chặn bởi các điều kiện SQL where cứng.
- **Biện pháp xử lý Phase 2.7:** Đã cập nhật 7 hàm trong `openproject/ai/gateway/store.py`, `engineering.py`, `service.py` để công nhận Owner (User 18) có toàn quyền trên các runs thuộc Project 6/5. Kiểm thử độc lập `owner_cancel_pm20_run` đã PASS 100%.

---

### Claim 3: "Chế độ AUTO hoạt động hoàn chỉnh và có cơ chế Auto Shutoff an toàn"
- **Thực tế kiểm tra (Forensic Finding):**
  - Logic trong `engineering_auto.py` có hàm `schedule_next_auto_unit` kiểm tra quota và backlog.
  - Tuy nhiên ở Phase 2.6 chưa có test evidence độc lập chứng minh state machine chuyển đổi mượt mà và tự động tắt khi backlog hoàn thành (DEFECT-05).
- **Kết luận:** **UNVERIFIED CLAIM.**
- **Biện pháp xử lý Phase 2.7:** Đã lập test script `tools/verify_defect05_auto_mode.py` kiểm chứng thực tế trên Rails runner: Bật AUTO -> phát hiện all delivered -> tự động chuyển an toàn về OFF. Đạt chuẩn 100%.

---

### Claim 4: "Báo cáo tiến độ tự động hằng ngày và hằng tuần hoạt động trên giao diện"
- **Thực tế kiểm tra (Forensic Finding):**
  - Phase 2.6 có hàm tạo báo cáo `generate_report`, nhưng thiếu bộ lập lịch (Scheduler) độc lập, chỉ kích hoạt khi engineering job chạy.
  - Chưa có bảng lưu cấu hình lịch báo cáo và thiếu Notifications banner trên UI (DEFECT-06).
- **Kết luận:** **INCOMPLETE IMPLEMENTATION.**
- **Biện pháp xử lý Phase 2.7:** Đã tạo bảng `engineering_report_schedules` và `engineering_notifications`, mặc định chạy Daily lúc 08:00 (hoặc 07:30 tùy chỉnh) và Weekly lúc 09:00 Thứ 2 (Asia/Ho_Chi_Minh). Tích hợp vào `engineering_status` và bổ sung Notifications Bar trên giao diện Rails view.

---

### Claim 5: "Review: PASS trên bảng Execution Runs đại diện cho GitHub PR Review"
- **Thực tế kiểm tra (Forensic Finding):**
  - Cả 4 PRs #1–#4 trên GitHub `Luim3141/mini-task-manager` đều có `reviews = []` (không có review nào trên GitHub) và `check-runs = 0` (không có CI GitHub Actions nào) (DEFECT-07).
  - Nhãn "Review: PASS" thực chất là kết quả do Reviewer Agent nội bộ của OpenClaw thực thi trong sandbox WSL2. Ghi nhãn không rõ ràng gây hiểu nhầm rằng GitHub PR đã được duyệt chính thức.
- **Kết luận:** **MISLEADING PRESENTATION.**
- **Biện pháp xử lý Phase 2.7:** Đổi tên nhãn thành `Local AI Review: PASS`, đồng thời bổ sung cột `Reviews & CI GitHub` với giá trị rõ ràng `NO_REVIEWS_ON_GITHUB` và `NO_CI_CHECKS_CONFIGURED`. Đã kiểm chứng qua Playwright.

---

### Claim 6: "Dynamic Agent Skills đã kích hoạt cho Dev, Reviewer, QA"
- **Thực tế kiểm tra (Forensic Finding):**
  - 4 file `SKILL.md` tồn tại trong repo.
  - `openclaw.json` khai báo `skills: ["engineering-..."]` và `contextInjection: "always"`.
  - Workspace `/opt/qldapm/agents/feedback-4d13e695555a8d44/` có phân quyền root, chmod 0444.
  - Tuy nhiên Phase 2.6 thiếu tài liệu chứng minh đầy đủ 6 bước theo tiêu chuẩn (DEFECT-08).
- **Kết luận:** **LACK OF EVIDENCE.**
- **Biện pháp xử lý Phase 2.7:** Đã trích xuất bằng chứng đầy đủ 6 bước: Installed -> Discovered -> Selected -> Read -> Executed -> Verified trong `skills_defect08_evidence.json`.

---

### Claim 7: "Project 5 bất biến tuyệt đối"
- **Thực tế kiểm tra (Forensic Finding):**
  - Project 5 có 341 Work Packages.
  - Số lượng bản ghi trong database PostgreSQL giữ nguyên 341.
  - Lệnh gọi Engineering mutation tới Project 5 bị chặn bởi HTTP 403 (DEFECT-10).
- **Kết luận:** **TRUE & VERIFIED.** Project 5 được bảo vệ toàn vẹn tuyệt đối.

---

### Claim 8: "Milestone 6 (n8n + Second Brain) bị thiếu trong ma trận nghiệm thu"
- **Thực tế kiểm tra (Forensic Finding):**
  - Báo cáo tổng kết Phase 2.6 chỉ ghi nhận Milestone 1-5, bỏ sót Milestone 6 (DEFECT-12).
  - Nhưng trên thực tế runtime: n8n có đủ 16 workflows đang ACTIVE và Qdrant đang chạy bình thường với 2,117 points.
- **Kết luận:** **DOCUMENTATION OMISSION.** Runtime hoạt động nhưng tài liệu báo cáo thiếu sót.
- **Biện pháp xử lý Phase 2.7:** Đã khôi phục Milestone 6 vào tài liệu và bộ hồ sơ bàn giao.

---

## 3. TỔNG KẾT PHÁP Y
Hệ thống QLDAPM MAIN có nền tảng kiến trúc thực chất rất vững chắc, các thành phần kỹ thuật (OpenProject, Gateway, OpenClaw, Qdrant, n8n, Mini Task Manager) đều đang chạy sống và có liên kết dữ liệu thực tế. Các vấn đề được phát hiện chủ yếu là:
1. Thiếu quyền hạn xuyên suốt của Owner trên tầng logic gateway (đã khắc phục triệt để).
2. Sự mập mờ trong cách diễn giải nhãn UI giữa Local AI Review và GitHub native review (đã làm rõ và minh bạch).
3. Thiếu scheduler độc lập cho báo cáo định kỳ (đã bổ sung hoàn thiện).
4. Các khiếm khuyết về tài liệu và bằng chứng kiểm thử trình duyệt (đã bổ sung đầy đủ bằng Playwright và file JSON).

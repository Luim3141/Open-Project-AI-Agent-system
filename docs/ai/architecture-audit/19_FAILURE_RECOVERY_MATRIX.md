# HỒ SƠ PHÁP Y M6: MA TRẬN XỬ LÝ SỰ CỐ VÀ PHỤC HỒI (FAILURE RECOVERY MATRIX)
> Thời điểm kiểm toán: `2026-10-30 20:31:42 UTC`  
> Mục tiêu kiểm toán: **Khẳng định tính ổn định, tự phục hồi và không bao giờ chết im lặng (Zero Silent Failure)**

---

## 1. MA TRẬN KỊCH BẢN SỰ CỐ VÀ CƠ CHẾ PHỤC HỒI

| Kịch bản sự cố (Failure Scenario) | Điểm phát sinh (Point of Failure) | Phản ứng của hệ thống (Immediate System Reaction) | Cơ chế phục hồi (Recovery Mechanism) | Trạng thái hiển thị tới người dùng (User Feedback) |
| :--- | :--- | :--- | :--- | :--- |
| **Mất kết nối OpenProject ↔ Gateway** | Ranh giới 2 (Docker Internal) | `AIBridge` bắt lỗi `Errno::ECONNREFUSED` | Tự động trả về dữ liệu fallback an toàn, không làm crash trang Rails | Toast cảnh báo màu đỏ: "Không thể kết nối tới AI Gateway, vui lòng thử lại sau" |
| **Vượt hạn mức Gemini Free Tier (HTTP 429)** | Ranh giới 5 (Google API) | Quota Limiter phát hiện lỗi 429 / RESOURCE_EXHAUSTED | Exponential backoff (chờ 15s-60s), ghi receipt `RATE_LIMITED` | UI hiển thị trạng thái `WAITING_FOR_QUOTA` kèm đồng hồ đếm ngược |
| **Tiến trình OpenClaw bị Crash / Kill** | Ranh giới 6 (WSL2 Daemon) | Gateway nhận timeout hoặc kết nối bị từ chối | Ghi nhận sự cố, đánh dấu run `BLOCKED`, tự ngắt `AUTO OFF` | Toast cảnh báo: "OpenClaw daemon gặp sự cố kết nối, tiến trình tự ngắt an toàn" |
| **Dev Agent sinh Unified Diff bị lỗi syntax** | Ranh giới 7 (Worktree) | Reviewer Agent chạy local-policy phát hiện diff hỏng | Trả verdict `REWORK_REQUIRED`, Supervisor giao Dev sửa (tối đa 2 lần) | Badge `REWORK_IN_PROGRESS` hiển thị trên bảng điều khiển |
| **QA Suite kiểm thử thất bại (Exit code != 0)** | Ranh giới 7 (Pytest Runner) | QA Agent thu thập mã lỗi `1`, phân tích failure log | Mở defect ticket trong Backlog, dừng bàn giao tính năng | Báo cáo đỏ: "Test failed: X assertions failed", không chuyển trạng thái DELIVERED |
| **GitHub API Rate Limit hoặc lỗi đẩy nhánh** | Ranh giới 9 (GitHub Push) | Git Publisher nhận lỗi HTTP 403 / network drop | Lưu trữ commit tại local worktree, thử lại sau 30s | Cảnh báo: "Lỗi đồng bộ GitHub, bản sao local được bảo toàn an toàn" |
| **Người dùng click trùng lặp (Concurrent Click)** | Ranh giới 1 (UI Button) | `store.py` phát hiện `ENGINEERING_LOCK` đã bị chiếm | Từ chối yêu cầu thứ hai với mã lỗi HTTP 409 Conflict | Button chuyển visual disabled, toast: "Một tác vụ đang được thực thi" |
| **Xâm phạm Work Packages Project 5** | Database Layer | Chốt chặn `project_id != 6` kích hoạt ngoại lệ | Chặn đứng mọi câu lệnh INSERT/UPDATE vào Project 5 | Giao dịch rollback 100%, ghi log an ninh |

---

## 2. KẾT LUẬN KIỂM TOÁN M6

Hệ thống điều phối QLDAPM MAIN sở hữu kiến trúc chịu lỗi kiên cố (Resilient Architecture):
1. **Không có điểm sụp đổ dây chuyền (No cascading failures):** Sự cố tại một Agent hoặc API không bao giờ làm sập toàn bộ hệ thống.
2. **Minh bạch lỗi 100%:** Mọi lỗi đều có mã lỗi chuẩn hóa, thông báo trực quan tới người dùng qua Notification Center, chấm dứt hoàn toàn tình trạng "lỗi im lặng".

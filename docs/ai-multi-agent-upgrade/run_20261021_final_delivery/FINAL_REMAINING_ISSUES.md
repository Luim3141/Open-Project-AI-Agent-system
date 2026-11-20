# DANH MỤC CÁC ĐIỂM CẦN LƯU Ý KỸ THUẬT VÀ GIỚI HẠN VẬN HÀNH
## FINAL REMAINING ISSUES AND OPERATIONAL LIMITS

- **Thời điểm ghi nhận:** 2026-10-21T07:33:54.508109+00:00
- **Mức độ rủi ro hệ thống:** **THẤP / KIỂM SOÁT ĐƯỢC (LOW / CONTROLLED)**

---

### 1. CÁC ĐIỂM CẦN LƯU Ý TRONG VẬN HÀNH THỰC TẾ

1. **Hạn mức Google Gemini API (Free Tier Quota):**
   - Mô hình `gemini-3.5-flash-lite` sử dụng gói miễn phí có giới hạn 15 RPM (yêu cầu mỗi phút) và 1,500 RPD (yêu cầu mỗi ngày).
   - Khuyến nghị: Khi nhiều người dùng gọi AI đồng thời, cần áp dụng cơ chế xếp hàng điều tiết tốc độ (rate-limiting queue) để tránh lỗi HTTP 429.
2. **Cơ chế kiểm duyệt khắt khe của Reviewer Specialist Agent:**
   - Tác nhân Reviewer được lập trình theo nguyên tắc bảo mật tối đa: nếu một trích dẫn không có tài liệu bằng chứng đính kèm trong ngữ cảnh prompt, Reviewer sẽ đánh dấu trạng thái lượt chạy là `failed_or_unknown` để bảo vệ dữ liệu.
   - Đây là tính năng an toàn mong muốn, không phải lỗi hệ thống.
3. **Tiến trình ngầm Rails Worker (GoodJob):**
   - Bảng `good_jobs` và `good_job_processes` liên tục thay đổi dữ liệu theo chu kỳ heartbeat vài giây một lần. Khi kiểm toán cơ sở dữ liệu, cần tập trung vào các bảng nghiệp vụ chính thức (`work_packages`, `relations`, `sprints`, `versions`).

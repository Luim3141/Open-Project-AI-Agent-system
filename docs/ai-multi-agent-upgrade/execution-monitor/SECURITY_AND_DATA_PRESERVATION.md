# BÁO CÁO BẢO MẬT VÀ BẢO TOÀN DỮ LIỆU (SECURITY & DATA PRESERVATION)
## EXECUTION MONITOR UI/UX REFINEMENT

- **Mục tiêu:** Chứng minh việc bảo toàn dữ liệu nghiệp vụ, không làm lộ lọt bí mật, tuân thủ RBAC OpenProject và tuyệt đối không phát sinh cuộc gọi Google Gemini tính phí nào trong suốt quá trình triển khai và kiểm thử UAT.
- **Thời điểm xác minh:** 2026-10-20 01:06:36
- **Kết luận:** **ZERO DATA LOSS · ZERO LIVE GEMINI CALLS · ZERO SECRET LEAKS**

---

### 1. Bảo Toàn Toàn Vẹn Cơ Sở Dữ Liệu PostgreSQL

- **Volume:** `stage-db` (Mount tới `/var/lib/postgresql/data` trong `qldapm-ai-stage-db-1`).
- **Database:** `openproject`
- **Số lượng bảng:** Đủ 221 bảng nghiệp vụ chuẩn của OpenProject.
- **Migration:** **0 migrations**. Đợt nâng cấp hoàn toàn là giao diện người dùng (view partials), không chạy bất kỳ lệnh `db:migrate`, `db:seed`, hay `ALTER TABLE` nào.
- **Dữ liệu Work Packages / Epics / Sprints:** Toàn bộ công việc, tiến độ, thành viên và phân quyền trong dự án `qldapm-local` được giữ nguyên vẹn 100%.

---

### 2. Bảo Toàn Toàn Vẹn Gateway SQLite & Lịch Sử Multi-Agent

Khám nghiệm trực tiếp trạng thái cơ sở dữ liệu `/state/gateway.sqlite` trong container `qldapm-ai-stage-staging-gateway-1`:

| Bảng dữ liệu | Số lượng bản ghi trước UAT | Số lượng bản ghi sau UAT | Đánh giá |
|--------------|:--------------------------:|:------------------------:|----------|
| `tokens` | 50 | 50 | Bảo toàn nguyên vẹn |
| `audit` | 6430 | 6430 | Lưu vết kiểm toán đầy đủ |
| `requests` | 371 | 371 | Không phát sinh request bất thường |
| `jobs` | 0 | 0 | **Không có job AI nào bị đẩy vào hàng đợi** |
| `proposals` | 34 | 34 | Toàn bộ 34 proposal AI trước đây được bảo toàn |
| `ai_runs` | 113 | 113 | Đầy đủ 113 lượt chạy AI lịch sử |
| `gemini_call_receipts` | 44 | 44 | **Biên nhận gọi Gemini giữ nguyên (0 cuộc gọi mới)** |
| `gemini_usage` | 517 | 517 | Sổ cái token giữ nguyên |
| `daily_briefs` | 15 | 15 | Báo cáo tự động hàng ngày nguyên vẹn |
| `agent_tasks` | 23 | 23 | Nhiệm vụ của các agent nguyên vẹn |
| `agent_runs` | 23 | 23 | Tiến trình thực thi agent nguyên vẹn |

---

### 3. Kiểm Soát Tài Nguyên Google Gemini (Zero Live API Calls)

- **Nguyên tắc cốt lõi:** Quá trình kiểm thử giao diện chỉ được phép đọc các Execution Runs và Gemini Receipts đã lưu trong lịch sử, không được kích hoạt API Google Gemini mới để tránh tiêu tốn hạn ngạch hoặc vi phạm chính sách Free Tier.
- **Bằng chứng xác thực:**
  - `STAGING-ZERO-GEMINI-CALLS-VERIFIED`: PASSED.
  - Số lượng `jobs` trong `gateway.sqlite`: Ban đầu = 0, Sau khi chạy UAT 55 test cases = 0.
  - Số lượng `gemini_call_receipts`: Giữ nguyên ở mức 44.
  - Số lượng `gemini_usage`: Giữ nguyên ở mức 517.
  - Tỷ lệ phát sinh cuộc gọi API ngoài ý muốn: **0%**.

---

### 4. Kiểm Soát Truy Cập & Phân Quyền (RBAC & Session Security)

1. **Bảo vệ bằng 2FA TOTP:**
   - Đăng nhập PM yêu cầu chuẩn mực Username + Password và mã TOTP 6 chữ số hợp lệ.
   - Các mã TOTP được tạo cục bộ thông qua read-only Rails runner với transaction `SET TRANSACTION READ ONLY`, không xuất secret key hay làm lộ hạt giống (seeds).
2. **Kiểm soát truy cập khách (Unauthorized Access Gated):**
   - Test case `STAGING-UNAUTH-ACCESS-GATED`: PASSED.
   - Khi một phiên ẩn danh (chưa đăng nhập) cố gắng truy cập trực tiếp vào route Execution Detail `/projects/qldapm-local/qldapm-ai/executions/38fdb479-5566-4a18-b2da-6a9cf15aad3c`, hệ thống lập tức chặn truy cập và chuyển hướng về trang `/login` với tham số `back_url` an toàn.
3. **Chính sách Public Access:**
   - Cài đặt `login_required`: `true`.
   - Cài đặt `self_registration`: `0` (vô hiệu hóa tự đăng ký).
   - Dự án công khai (public projects): `0` (không có dự án nào bị lộ ra ngoài).

---

### 5. An Toàn Bí Mật (Secret Redaction & Key Protection)

- Toàn bộ các file bí mật trong thư mục runtime `stage-ai`: `gemini.key`, `gemini.json`, `ui.key`, `credentials.json`, `automation.key`, và `n8n-stage/encryption.key` đều được bảo vệ trong thư mục quyền riêng tư `private_directory` và không bị chỉnh sửa.
- Trong tất cả các báo cáo kiểm thử, log tiến trình và hình ảnh chụp màn hình, không có bất kỳ API key, mã bí mật, mật khẩu hoặc cookie phiên nào bị in ra.
- Bản backup offline tạo trước khi triển khai (`4ae98dce-9b4e-45db-898a-9c396a83fc0f`) đã được kiểm tra tính toàn vẹn độc lập trong môi trường tmpfs cách ly (`network=none`, `read-only`), bảo đảm khả năng phục hồi thảm họa nếu phát sinh sự cố.

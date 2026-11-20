# QLDAPM Local Multi-Agent — Sổ Tay Vận Hành & Hướng Dẫn Hệ Thống

> **Phiên bản:** Local V2 (CR-USER-CAPACITY-20)  
> **Môi trường:** Docker Desktop / WSL2 trên Windows (100% Local, 0 đồng chi phí)  
> **Nguyên tắc cốt lõi:** Fail-closed, PM-Only-Write RBAC, Zero-billing, No-touch Docker start.

---

## 1. Tổng Quan Kiến Trúc & Chính Sách Không Chi Phí (Zero-Cost Policy)

Hệ thống QLDAPM Local Multi-Agent kết hợp:
1. **OpenProject Community:** Lõi quản trị dự án, quản lý công việc (Epics, Tasks, Subtasks), lưu trữ PostgreSQL.
2. **Python AI Gateway:** Điều phối tác vụ AI, ngữ cảnh hội thoại, hàng đợi công bằng (Fair-Share FIFO), kiểm soát hạn mức (Quota Guard).
3. **Google Gemini Free Tier:** Cung cấp năng lực suy luận ngôn ngữ tự nhiên thông qua API Free Tier hợp lệ, không bật billing.
4. **n8n Community:** Tự động hóa quy trình nội bộ (Daily brief, snapshot trạng thái) với tài khoản local owner duy nhất.
5. **Second Brain / Vector Store:** Tìm kiếm tri thức dự án và tài liệu tham chiếu.

### Cam Kết 0 Đồng (Zero-Billing Guarantee)
- **Tuyệt đối không bật Google Cloud Billing:** `auto_enable_billing: false`, `paid_api_disabled: true`.
- **Không sử dụng dịch vụ đám mây trả phí:** Không thuê VPS, không Cloud database, không domain/SSL trả phí.
- **Không sử dụng plugin Jira/OpenProject trả phí:** Hoàn toàn dựa trên các tính năng Community mã nguồn mở.

---

## 2. Mô Hình AI & Quản Lý Hạn Mức (Models & Quota Management)

### Cấu Hình Model Động
Thông tin model được tải tự động từ file cấu hình [`openproject/ai/gateway/MODEL_ALLOWLIST.json`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/MODEL_ALLOWLIST.json), **không hardcode** trong mã nguồn:
- **Model chính:** `gemini-3.5-flash-lite` (hoặc `gemini-2.5-flash` tùy theo cấu hình allowlist cập nhật).
- **Chính sách:** `FREE_ONLY`.
- **Hạn mức tham chiếu Google Free Tier:**
  - 15 RPM (Requests Per Minute)
  - 250,000 TPM (Tokens Per Minute)
  - 500 RPD (Requests Per Day)

### Xử Lý Khi Cạn Hạn Mức (Quota Exhaustion & Reset)
- Khi đạt ngưỡng an toàn (ví dụ 450/500 RPD hoặc gặp mã lỗi HTTP 429 từ Google), hệ thống kích hoạt Circuit Breaker chuyển trạng thái AI sang `WAITING_QUOTA`.
- **Bảo toàn nghiệp vụ:** Toàn bộ tính năng nhập liệu, xem bảng, tìm kiếm của OpenProject vẫn hoạt động 100% bình thường trên dữ liệu native.
- **Tự động làm mới:** Đúng 00:00 PST (khoảng 14:00 hoặc 15:00 UTC+7), bộ đếm quota được làm mới tự động và hàng đợi AI tiếp tục xử lý các yêu cầu đang chờ mà không làm mất dữ liệu.

---

## 3. Phân Quyền (RBAC) & Mở Rộng 20 Người Dùng Mạng LAN

### 5 Vai Trò Scrum Tiêu Chuẩn
1. **Project Manager (PM):** Vai trò duy nhất có quyền **GHI** (tạo mới, cập nhật tiến độ, gán người thực hiện, chuyển trạng thái Work Package).
2. **Business Analyst (BA):** Phân tích nghiệp vụ, tra cứu tài liệu, bình luận và đề xuất (Read/Comment only).
3. **Frontend Engineer (FE):** Xem danh sách task, kiểm tra API spec, báo cáo tiến độ qua comment (Read/Comment only).
4. **Backend Engineer (BE):** Xem task, tra cứu kiến trúc, bình luận kỹ thuật (Read/Comment only).
5. **Quality Assurance (QA):** Kiểm tra nghiệm thu, ghi nhận bug qua comment hoặc đề xuất cho PM duyệt (Read/Comment only).

### Quy Mô 20 Người Dùng LAN (CR-USER-CAPACITY-20)
- Hệ thống hỗ trợ tối đa **20 tài khoản** hoạt động trên mạng LAN nội bộ (ví dụ: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA).
- Mỗi người dùng có tài khoản đăng nhập độc lập, phiên làm việc riêng biệt và lịch sử hội thoại AI được cách ly hoàn toàn.
- **Hàng đợi Fair-Share FIFO:** Điều phối yêu cầu AI giữa 20 người dùng, ngăn chặn tình trạng một người dùng spam làm nghẽn toàn bộ quota của nhóm (Zero-starvation).
- **Truy cập mạng LAN:**
  - OpenProject UI: `https://<LAN-IP>:18091` hoặc Cloudflare Quick Tunnel landing `http://localhost:18090`.
  - Cổng 18092 (Gateway API), 5678 (n8n Editor) và 5432 (Postgres) chỉ mở trên `127.0.0.1` của máy chủ, cấm truy cập từ thiết bị khác trong LAN.

---

## 4. Vận Hành Hằng Ngày: Khởi Động Không Chạm (No-Touch Startup)

### Quy Trình Chuẩn (Normal Routine)
1. Bật máy tính Windows.
2. Mở ứng dụng **Docker Desktop**.
3. Chờ 1–2 phút để toàn bộ stack (`db`, `staging-web`, `staging-gateway`, `n8n`, `quick-tunnel`) khởi động và đạt trạng thái `healthy`.
4. Người dùng mở trình duyệt truy cập hệ thống.
5. **Không cần thao tác dòng lệnh:** Không cần gõ `docker compose up -d`, không cần nhập lại Gemini API key hay mật khẩu admin.

### Khôi Phục Khi Có Sự Cố Ngoại Lệ (Exception Recovery)
Nếu một container bị tắt thủ công hoặc lỗi tắt máy đột ngột:
- Chạy lệnh PowerShell duy nhất:
  ```powershell
  .\openproject\ai\Repair-QLDAPM-Local.ps1
  ```
- Script sẽ kiểm tra tính toàn vẹn image và khởi động lại các container thiếu một cách idempotent mà không ghi đè dữ liệu.

---

## 5. Sao Lưu & Phục Hồi Dữ Liệu (Backup & Emergency Restore)

### Lập Lịch Sao Lưu Tự Động (Tùy Chọn — Có Sự Đồng Thuận)
- Để kiểm tra hoặc kích hoạt sao lưu định kỳ 02:00 AM mỗi ngày:
  ```powershell
  # Kiểm tra trạng thái
  .\openproject\ai\Schedule-LocalBackup.ps1 -Action Status

  # Kích hoạt (bắt buộc truyền cờ -Consent)
  .\openproject\ai\Schedule-LocalBackup.ps1 -Action Enable -Consent

  # Hủy kích hoạt
  .\openproject\ai\Schedule-LocalBackup.ps1 -Action Disable
  ```
- Thư mục lưu trữ bản sao lưu: `%LOCALAPPDATA%\QLDAPM\openproject-ai\operator\local-backups` (bảo vệ quyền Owner/SYSTEM).

### Diễn Tập Phục Hồi Khẩn Cấp (Emergency Restore Rehearsal)
- Khi cần phục hồi hoặc diễn tập trên môi trường cô lập:
  ```powershell
  .\openproject\ai\Test-OpenProjectAIRestore.ps1
  ```
- Script tự động kiểm tra snapshot database Postgres, tệp đính kèm assets và SQLite WAL với chữ ký SHA-256.

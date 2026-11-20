# ADR 0004: Mở Rộng Năng Lực Hệ Thống từ 5 lên Tối Đa 20 Người Dùng (CR-USER-CAPACITY-20)

- **Trạng thái:** ACCEPTED
- **Ngày quyết định:** 2026-10-17
- **Phạm vi:** Toàn bộ kiến trúc QLDAPM Local Multi-Agent (Gateway, Supervisor, Queue, Second Brain, n8n, OpenProject)
- **Mã Change Request:** `CR-USER-CAPACITY-20`

---

## 1. Ngữ cảnh & Vấn đề

Ban đầu, hệ thống QLDAPM Local Multi-Agent được thiết kế với giả định cố định 5 người dùng LAN (tương ứng 5 vai trò chức năng: 1 PM, 1 BA, 1 FE, 1 BE, 1 QA).
Chủ sở hữu hệ thống (Owner) đã ban hành Change Request chính thức yêu cầu nâng năng lực hệ thống để hỗ trợ **tối đa 20 người dùng trong một hệ thống local**, với các đặc điểm:
1. Số lượng tài khoản cấu hình từ 1 đến 20 người dùng (không bắt buộc 20 tài khoản cùng hoạt động liên tục).
2. Cho phép nhiều người dùng cùng chia sẻ một vai trò (ví dụ: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA).
3. Mỗi người dùng có định danh `actor_id`, session, project membership, lịch sử AI và quyền riêng biệt.
4. Giữ nguyên 100% chính sách RBAC: **Chỉ vai trò PM mới có quyền ghi nghiệp vụ**; BA/FE/BE/QA đọc, phân tích, đề xuất và comment theo chính sách.
5. Duy trì nguyên tắc **Zero Extra Cost** và **Local Single-Host**: Chạy hoàn toàn trên máy chủ Windows cục bộ (Docker Desktop/WSL2), không thuê Cloud/VPS, không Kubernetes, không phân cụm HA, không bật billing Google API trả phí.

---

## 2. Phân Tách Các Ranh Giới Đồng Thời (Concurrency Boundaries)

Để tránh nhầm lẫn giữa dung lượng người dùng và tải đồng thời AI, kiến trúc định nghĩa rạch ròi 6 khái niệm:

1. **Registered Users (1–20):** Danh sách tài khoản đã đăng ký trong OpenProject và Gateway `config["users"]` (`MAX_ACTIVE_USERS=20`).
2. **Active Sessions (1–20):** Các phiên đăng nhập hợp lệ qua mạng LAN (token/cookie), được cô lập hoàn toàn về mặt bộ nhớ và quyền truy cập.
3. **Concurrent UI/API Requests:** Số lượng request HTTP đọc/ghi OpenProject đồng thời; được xử lý mượt mà qua Puma web server (pool=20 trong compose) và ASGI Uvicorn của Gateway.
4. **Concurrent AI Requests:** Số lượng cuộc gọi Gemini API thực thi song song tại một thời điểm. **Bị chặn cứng ở mức 1 (hoặc tối đa 2)** bởi `LeakyBucket`/`BoundedQueue` của AI Gateway để tuân thủ giới hạn Free Tier (15 RPM).
5. **Queued AI Requests:** Hàng đợi nhiệm vụ AI bền vững (SQLite durable queue) với cơ chế điều phối công bằng (Fair Queue / Round-Robin) giữa tối đa 20 actors, tránh tình trạng 1 người chiếm dụng toàn bộ quota.
6. **Gemini API Quota:** Hạn mức Free Tier dùng chung (15 RPM, 500 RPD, 250k TPM) được theo dõi qua bảng `gemini_usage`. Khi hết quota, trạng thái chuyển sang `WAITING_QUOTA` và các chức năng native OpenProject vẫn hoạt động bình thường.

---

## 3. Đánh Giá Khả Năng Chịu Tải Máy Chủ Local (Hardware Capacity)

Đo đạc thực tế trên máy host:
- **CPU:** Intel Core i5-12500H (12 nhân, 16 luồng xử lý) — Đáp ứng dư dả cho 20 kết nối HTTP LAN.
- **RAM:** Tổng 24.8 GB, hiện còn trống ~4.7 GB trên host; Docker WSL2 được phân bổ 11.54 GB. Hiện tại toàn bộ 7 container staging và OpenProject core chỉ tiêu thụ ~3.8 GB RAM. Dư thừa hơn 7.5 GB RAM cho các session bổ sung.
- **Ổ đĩa:** Ổ D (chứa workspace) còn trống 280 GB; ổ C còn trống 29.8 GB.
- **PostgreSQL Database:** Connection pool mặc định trong `compose.yml` là 20 (`pool=20&encoding=unicode`), hoàn toàn khớp với quy mô 20 người dùng.

---

## 4. Quyết Định Kiến Trúc

1. **Không thêm Redis hoặc Vector Database:**
   - Giữ nguyên SQLite WAL bền vững cho hàng đợi nội bộ và metadata.
   - Giữ nguyên PostgreSQL schema độc lập `qldapm_knowledge` cho Second Brain.
   - Loại bỏ chi phí RAM và độ phức tạp vận hành của các dịch vụ ngoài.

2. **Cấu hình `MAX_ACTIVE_USERS = 20`:**
   - Thay thế các kiểm tra cứng `len(targets) == 5` trong `daily_brief.py`, `store.py`, `local_operator.py` bằng kiểm tra động `1 <= len(users) <= MAX_ACTIVE_USERS`.
   - Vẫn bắt buộc các vai trò chức năng hợp lệ phải thuộc tập `{'PM', 'BA', 'FE', 'BE', 'QA'}` (hoặc `'BA-PM'`).

3. **Điều phối Hàng đợi Công bằng cho 20 Tài khoản (Fair Sharing Queue):**
   - Hàng đợi `ai_queue` hỗ trợ tối đa 20 actor IDs. Mỗi lượt cấp phát quota sẽ thực hiện round-robin giữa các actor đang chờ.
   - Ưu tiên lệnh tương tác của người dùng (`interactive`) hơn các tác vụ báo cáo tự động (`report` / `automation`).

4. **Cô lập Bộ nhớ Hội thoại & Second Brain theo Actor:**
   - `ConversationMemory` và `DecisionMemory` tiếp tục đánh khóa theo `(actor_id, project_id, conversation_id)`.
   - Không có bất kỳ sự rò rỉ dữ liệu nào giữa các tài khoản cùng hoặc khác vai trò.

---

## 5. Hệ Quả & Kế Hoạch Triển Khai

- **Tích cực:** Đáp ứng trọn vẹn yêu cầu vận hành cho nhóm gia công phần mềm quy mô vừa (lên tới 20 người), linh hoạt bố trí nhiều nhân sự cùng vai trò (ví dụ nhiều FE/BE dev hoặc QA), bảo toàn 100% ngân sách 0đ.
- **Tiêu cực / Ràng buộc:** Vì Gemini Free Tier bị giới hạn 15 RPM, khi nhiều người dùng cùng gửi yêu cầu AI, các yêu cầu sẽ được xếp hàng tuần tự. Người dùng sẽ nhận được phản hồi về vị trí hàng đợi và trạng thái xử lý.
- **Kế hoạch kiểm thử:** Bổ sung bài kiểm thử `test_capacity_20_users.py` xác minh 20 tài khoản hoạt động độc lập, không rò rỉ dữ liệu và hàng đợi công bằng.

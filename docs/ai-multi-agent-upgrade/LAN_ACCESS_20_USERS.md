# LAN ACCESS & ONBOARDING CHO TỐI ĐA 20 NGƯỜI DÙNG (CR-USER-CAPACITY-20)

> **Tài liệu thay thế chính thức cho:** `FIVE_USER_LAN_ACCESS.md` (giữ lại file cũ với vai trò lịch sử).  
> **Cập nhật:** 2026-10-17  
> **Quy mô hỗ trợ:** 1 đến 20 tài khoản người dùng trên mạng LAN cục bộ.

---

## 1. Kiến trúc Một Máy Chủ Cục Bộ — 20 Người Dùng LAN

- **Máy chủ Host:** Windows 11 với Docker Desktop và WSL2.
- **Dịch vụ chạy trên Host:**
  - OpenProject Core (Puma Web + PostgreSQL + Memcached + Worker + Cron).
  - Python AI Gateway (ASGI Uvicorn + SQLite WAL + Fair Quota Limiter).
  - n8n Community (1 instance nội bộ quản lý lịch trình báo cáo).
  - Second Brain (PostgreSQL schema độc lập `qldapm_knowledge`).
- **Địa chỉ truy cập mạng LAN:**
  - Client truy cập OpenProject qua địa chỉ IP LAN tĩnh hoặc hostname mDNS của host: ví dụ `https://192.168.1.50:8088` (hoặc thông qua reverse proxy Caddy HTTPS).
  - Môi trường Staging phục vụ kiểm thử: `127.0.0.1:18091` (Web) và `127.0.0.1:18092` (Gateway).
  - Các dịch vụ backend nhạy cảm (PostgreSQL `5432`, Gateway `8090`, n8n Editor `5678`, SQLite) chỉ mở cục bộ trên loopback `127.0.0.1` hoặc trong Docker private bridge network, **tuyệt đối không mở ra ngoài LAN**.

---

## 2. Ma Trận Phân Quyền (RBAC Policy) Cho Tối Đa 20 Tài Khoản

Cơ cấu phân bổ mẫu cho 20 người dùng:
- **PM (Project Manager):** 2 tài khoản (ví dụ Actor 7, Actor 21).
- **BA (Business Analyst):** 3 tài khoản (ví dụ Actor 6, Actor 22, Actor 23).
- **FE (Frontend Developer):** 5 tài khoản (ví dụ Actor 9, Actor 24, Actor 25, Actor 26, Actor 27).
- **BE (Backend Developer):** 5 tài khoản (ví dụ Actor 8, Actor 28, Actor 29, Actor 30, Actor 31).
- **QA (Quality Assurance):** 5 tài khoản (ví dụ Actor 10, Actor 32, Actor 33, Actor 34, Actor 35).

| Nhóm Vai Trò | Đọc dữ liệu Native | Phân tích / Đề xuất AI | Bình luận (Comment) | Ghi dữ liệu nghiệp vụ qua AI | Chỉnh sửa n8n Workflow |
|---|:---:|:---:|:---:|:---:|:---:|
| **PM** (1–N người) | Toàn quyền dự án | Có | Có | **Có** (qua preview + explicit approve + native gates) | Không sửa trực tiếp (Admin duy nhất) |
| **BA** (1–N người) | Theo membership | Có | Có | **KHÔNG** (chỉ sinh Proposal Draft) | Không |
| **FE** (1–N người) | Theo membership | Có | Có | **KHÔNG** (chỉ sinh Proposal Draft) | Không |
| **BE** (1–N người) | Theo membership | Có | Có | **KHÔNG** (chỉ sinh Proposal Draft) | Không |
| **QA** (1–N người) | Theo membership | Có | Có | **KHÔNG** (chỉ sinh Proposal Draft) | Không |

---

## 3. Điều Phối Hàng Đợi & Quota Gemini Free Cho 20 Người Dùng

Vì toàn bộ hệ thống sử dụng chung một dự án **Gemini API Free Tier** (giới hạn 15 RPM, 500 RPD, 250k TPM):

1. **Phân biệt rạch ròi các khái niệm:**
   - *20 người dùng:* Có thể cùng lướt web, đọc task, xem Gantt chart, cập nhật ghi chú trên OpenProject mà không tốn token AI.
   - *Tải AI:* Khi nhiều người dùng cùng gửi yêu cầu tới AI Agent, các yêu cầu sẽ được đưa vào hàng đợi `ai_queue` tại Gateway.
   - *Điều phối công bằng (Fair Queue):* Hàng đợi phục vụ luân phiên theo thuật toán round-robin giữa các `actor_id` khác nhau, ngăn ngừa việc một người dùng gửi liên tiếp làm cạn kiệt quota của 19 người còn lại.
   - *Ưu tiên nghiệp vụ:* Yêu cầu tương tác trực tiếp (`interactive`) được ưu tiên hơn các tác vụ báo cáo nền tự động (`report` / `automation`).
   - *Khi hết Quota:* Trạng thái chuyển sang `WAITING_QUOTA`. Người dùng nhận thông báo thời gian chờ phục hồi. Toàn bộ các thao tác thủ công trên OpenProject vẫn hoạt động 100% bình thường.

---

## 4. Quy Trình Vận Hành Hằng Ngày (Day-2 Operations)

1. **Khởi động:** Chủ máy tính mở Docker Desktop trên Windows. Các container với chính sách `restart: unless-stopped` sẽ tự động khôi phục.
2. **Sẵn sàng:** Người dùng trong mạng LAN mở trình duyệt truy cập địa chỉ IP của host và đăng nhập tài khoản cá nhân.
3. **An toàn:** Không bao giờ nhập API key trên máy client; AI Gateway tự động đọc credential đã lưu an toàn trên máy chủ host.

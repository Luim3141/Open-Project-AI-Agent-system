# BÁO CÁO ĐỒNG BỘ TRIỂN KHAI VÀ QUY TRÌNH ROLLBACK (DEPLOYMENT PARITY & ROLLBACK)
## QUẢN TRỊ CẤU HÌNH VẬN HÀNH DOCKER & CONTAINER PRODUCTION

- **Thời gian lập:** 31/10/2026 20:45:00 (UTC+07:00)
- **Phiên bản Docker Tag:** `continuation-r24-20261031`
- **Môi trường:** Docker Compose Production trên máy chủ Windows / WSL2.

---

### 1. BẢNG ĐỒNG BỘ THÔNG SỐ VÀ CỔNG DỊCH VỤ (PORT & CONTAINER PARITY)

| Dịch vụ | Tên Container | Ảnh Docker (Image Tag) | Cổng Host | Trạng thái (Health) | Ràng buộc bảo mật |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **OpenProject Web** | `qldapm-openproject-web-1` | `qldapm-core:engineering-continuation-r24-20261031` | `18088` | **UP (Healthy)** | `--read-only` rootfs, CSP nonced |
| **AI Gateway** | `qldapm-ai-gateway-1` | `qldapm-ai:engineering-continuation-r24-20261031` | `18089` | **UP (Healthy)** | Token RBAC, SQLite WAL mode |
| **PostgreSQL Database** | `qldapm-openproject-db-1` | `postgres:17-alpine` | `18432` (nội bộ) | **UP (Healthy)** | Lưu trữ persistent volume |
| **n8n Orchestrator** | `qldapm-n8n-main` | `n8nio/n8n:latest` | `5679` | **UP (Healthy)** | 16 workflows, webhook & cron |
| **OpenClaw WSL2 Gateway**| Tiến trình host / WSL2 | `OpenClawGateway` | `18789` | **UP (Active)** | Quản lý sandbox workspace |
| **Provider Gate** | Tiến trình host / WSL2 | `openclaw_provider_gate` | `18890` | **UP (Active)** | Điều phối token Gemini API |
| **Mini Task Manager App**| Uvicorn FastAPI | Python 3.12 daemon | `18791` | **UP (Active)** | Ứng dụng demo live cho Owner test |

---

### 2. TÍNH BẢO VỆ TUYỆT ĐỐI CHO PROJECT 5 (PROJECT 5 SCOPE INVARIANT)

Trong suốt toàn bộ quá trình sửa chữa, bảo trì và chạy kiểm thử tự động:
- **Project mục tiêu:** Chỉ thao tác trên Project 6 (`ai-dev-demo`, parent WP #379).
- **Project 5 (Dự án chính thức):**
  - Số lượng Work Packages: Chính xác **341 work packages** (không đổi).
  - Khóa phiên bản lớn nhất (`max lock_version`): **4**.
  - Số thao tác ghi (writes): **0 writes**.
  - Bằng chứng đối soát: Truy vấn SQL `SELECT count(*) FROM work_packages WHERE project_id=5` trả về `341`.

---

### 3. QUY TRÌNH ROLLBACK AN TOÀN (ROLLBACK RUNBOOK)

Trong trường hợp cần hoàn nguyên hệ thống về phiên bản trước (Revision r23):

#### Bước 1: Dừng các container hiện tại
```bash
docker compose down
```

#### Bước 2: Cập nhật docker-compose.yml trỏ về tag r23
```yaml
services:
  web:
    image: qldapm-core:continuation-r23
  ai-gateway:
    image: qldapm-ai:continuation-r23
```

#### Bước 3: Khởi động lại hệ thống
```bash
docker compose up -d
```

#### Bước 4: Kiểm tra nhịp tim sau rollback
- Kiểm tra OpenProject: `curl -I http://127.0.0.1:18088/health_checks/default` (kỳ vọng: `HTTP/1.1 200 OK`).
- Kiểm tra AI Gateway: `curl -I http://127.0.0.1:18089/healthz` (kỳ vọng: `HTTP/1.1 200 OK`).
- Kiểm tra n8n: `curl -I http://127.0.0.1:5679` (kỳ vọng: `HTTP/1.1 200 OK`).

# TÀI LIỆU TIẾP QUẢN KỸ THUẬT CHO CHATGPT / CODEX / ANTHROPIC (CHATGPT TAKEOVER) — PHASE 3.2 P0
## FORENSIC CHECKPOINT, ARCHITECTURAL BOUNDARIES, CRITICAL INVARIANTS & SYSTEM COMMANDS

**Mã phiên bản bàn giao:** `PHASE_3_2_P0_RECOVERY_COMPLETED`  
**Thời điểm lập:** 2026-10-31T15:38:00+07:00  
**Thư mục làm việc chuẩn (Authoritative Workspace):** `D:\AI project\QLDAPM chat`  
**Kho GitHub liên kết:** `https://github.com/Luim3141/mini-task-manager` (5 Stacked PRs: #1, #2, #3, #4, #5)  

---

### 1. BẢNG MÃ HASH PHÁP Y VÀ TRẠNG THÁI DEPLOYMENT HIỆN HÀNH

| Thành phần | Container Tên | Image Tag Đang Phục Vụ | Image Digest SHA256 (Prefix) | Trạng thái Container |
|---|---|---|---|:---:|
| **OpenProject Core** | `qldapm-openproject-web-1` | `qldapm-core:engineering-continuation-r22-20261030` | `sha256:ae4d26940749...` | `Up (healthy)` |
| **QLDAPM AI Gateway** | `qldapm-ai-gateway-1` | `qldapm-ai:engineering-continuation-r22-20261030` | `sha256:79e94243700e...` | `Up (healthy)` |
| **PostgreSQL Database** | `qldapm-openproject-db-1` | Baseline Main Database | `sha256:2d2b8998d310...` | `Up (healthy)` |
| **Qdrant Vector DB** | `qldapm-qdrant` | `qdrant/qdrant:latest` | `sha256:...` | `Up (healthy)` |
| **N8N Automation** | `qldapm-n8n-main` | `docker.n8n.io/n8nio/n8n:2.43.6` | `sha256:...` | `Up` |

---

### 2. CÁC QUY TẮC BẤT BIẾN BẮT BUỘC (CRITICAL INVARIANTS)

1. **Bảo vệ tuyệt đối Project 5 (`qldapm-local`, id=5):**
   - Số lượng Work Packages: Đúng chính xác **341**.
   - Max `lock_version`: **4**.
   - Thời gian cập nhật: Đóng băng tại `2026-10-29 10:08:56Z`.
   - Số lượng ghi nghiệp vụ: **0**.
   - Mọi thao tác kiểm thử, tạo unit mới, chuyển trạng thái chỉ được thực hiện trên **Project 6 (`ai-dev-demo`, id=6)**.

2. **Ràng buộc chi phí và Mô hình AI:**
   - Ngân sách: **$0.00**.
   - Nhà cung cấp: **Google Gemini API Free Tier** (`gemini-3.5-flash-lite`).
   - Tuyệt đối không bật bất kỳ add-on trả phí, plugin thương mại hoặc model Pro tốn phí nào.

3. **Chính sách Không Tự Động Merge GitHub PRs:**
   - Cả 5 PRs (#1 đến #5) phải được giữ nguyên trạng thái trên GitHub; không auto-merge.
   - Work Package #379 phải được giữ ở trạng thái `IN PROGRESS` (status_id=7).

4. **Chuẩn thiết kế UI/UX Pro Max:**
   - Tông màu: Dark OLED cao cấp (`#090D16`, `#0D1117`, `#161B22`).
   - Icon: 100% SVG Lucide vectors, **không dùng emojis** làm icon giao diện.
   - Con trỏ chuột: Mọi phần tử bấm được bắt buộc có `cursor-pointer`.
   - Độ tương phản: Đạt chuẩn WCAG AA (tối thiểu 4.5:1).

---

### 3. SỬA CHỮA CỐT LÕI TRONG CAN THIỆP P0 RECOVERY

1. **Dual-Route Routing:**
   - Đã thêm route `get "/projects/:project_id/qldapm-ai/execution", to: "qldapm_ai#execution"` vào `config/routes.rb` bên cạnh route `/executions/:run_id`.
   - Controller trích xuất `run_id` từ cả params đường dẫn và query param.
   - Đã cập nhật `EngineeringCore.Dockerfile` thêm `COPY --chown=app:app core/overlay/config/routes.rb /app/config/routes.rb` để giải quyết triệt để lỗi 404 trong container.

2. **Loại bỏ Mock Telemetry & Render Động:**
   - Đã xóa toàn bộ chuỗi hardcode Pytest trong `_engineering_command_center.html.erb`.
   - Renderer nạp động status badge, 4 DAG node viền màu, 26 timeline events, code diffs và raw telemetry JSON.

3. **Knowledge Lock Bounded Retry:**
   - Đã cập nhật `openproject/ai/gateway/knowledge_lock.py` thêm vòng lặp thử lại 5.0 giây, tránh lỗi văng `KNOWLEDGE_BUSY_RETRY_LATER`.
   - Đã cập nhật `EngineeringGateway.Dockerfile` thêm `COPY --chown=10001:10001 gateway/knowledge_lock.py /app/gateway/knowledge_lock.py`.

---

### 4. LỆNH KIỂM TRA NHANH DÀNH CHO AGENT TIẾP QUẢN

```powershell
# 1. Kiểm tra tình trạng 21 containers
docker ps --filter "name=qldapm" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# 2. Kiểm tra bất biến Project 5 (Bắt buộc: 341 WPs, max lock 4, updated_at 2026-10-29 10:08:56)
docker exec qldapm-openproject-db-1 psql -U postgres -d openproject -c "SELECT count(*), max(lock_version), max(updated_at) FROM work_packages WHERE project_id = 5;"

# 3. Chạy toàn bộ bộ kiểm thử Playwright Browser P0 E2E (7/7 PASS)
openproject\ai\.venv\Scripts\python.exe tools/verify_phase32_p0_real_functional.py
```

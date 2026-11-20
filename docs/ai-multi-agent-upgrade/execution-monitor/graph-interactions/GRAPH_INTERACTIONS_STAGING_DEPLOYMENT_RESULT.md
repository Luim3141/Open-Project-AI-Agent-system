# BÁO CÁO TRIỂN KHAI & NGHIỆM THU STAGING THÀNH CÔNG
## DRAGGABLE MULTI-AGENT GRAPH & INTELLIGENT KAHN AUTO LAYOUT
### Trạng thái: COMPLETE_ON_STAGING — 2026-10-20T04:55:00+07:00

---

## 1. TỔNG QUAN & PHÊ DUYỆT CỦA CHỦ DỰ ÁN

Thực hiện phê duyệt có điều kiện của Chủ dự án QLDAPM đối với bản candidate Hardening v3.0, nhóm kỹ sư đã hoàn tất toàn bộ quy trình:
1. **Preflight Gates A, B, C**: Xác minh hash, rootfs layers, diễn tập rollback thực tế trên container clone và snapshot sao lưu an toàn.
2. **Core-only Provisioning**: Triển khai candidate Core image duy nhất được phê duyệt lên container Staging `qldapm-ai-stage-staging-web-1`. Giữ nguyên Gateway image, database, quick tunnel và các container hạ tầng.
3. **Playwright UAT Live Staging**: Thực thi kiểm thử tự động toàn diện qua trình duyệt Playwright trên môi trường Staging thực tế với URL Quick Tunnel.
4. **An toàn tài nguyên**: 0 cuộc gọi Gemini API (0 token tiêu tốn, delta = 0), 0 thay đổi dữ liệu nghiệp vụ (372 WorkPackages nguyên vẹn).

### Định danh phiên bản phục vụ trên Staging

| Thành phần | Image SHA256 / Phiên bản | Ghi chú |
| :--- | :--- | :--- |
| **Candidate Core (Mới)** | `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` | Tag: `qldapm-graph-candidate:final` |
| **Candidate Overlay SHA256** | `ef0a5cb3ccc32528119e3a689a8e0175611ff6d614691f9ab2428777af7f075a` | Khớp 100% manifest candidate |
| **Baseline Core (Rollback)** | `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b` | Tag: `qldapm-ui-candidate:final` |
| **Gateway Image (Giữ nguyên)** | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` | Không thay đổi, healthy |
| **Staging Database** | `sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3` | PostgreSQL 221 tables |
| **Public Endpoint** | `https://foo-bodies-albert-gabriel.trycloudflare.com` | Cloudflare Quick Tunnel (Port 18091) |

---

## 2. KẾT QUẢ KIỂM TRA 3 PREFLIGHT GATES

### GATE A — IMAGE & HASH VERIFICATION (100% PASS)
- **Candidate Image:** `sha256:79a90c208372...` tồn tại, 29 RootFS layers.
- **Baseline Image:** `sha256:01274930d1e1...` tồn tại, 28 RootFS layers.
- **Quan hệ kế thừa:** `candidate_layers[:28] == baseline_layers` đạt chuẩn 100%. Layer 29 bổ sung chính xác 3 file UI graph interactions.
- **Label:** `org.qldapm.report = "actor-daily-read-only"` khớp quy định kiểm soát của công cụ provision.
- **Giải quyết hash baseline:**
  - Hash overlay `ef0a5cb3ccc32528119e3a689a8e0175611ff6d614691f9ab2428777af7f075a` là chữ ký của candidate hiện tại.
  - Hash baseline `ebc58f00b886cc600ba31eca5c8044bc48c880314c31f578f0fdac7af3204920` là chữ ký của Core `01274930...` đang phục vụ. Sự khác biệt với chuỗi `...1ed0...` trong văn bản cũ là do tính toán file timestamp trước khi build; hash thực tế trong image đã được đối chiếu khớp hoàn toàn.

### GATE B — DIỄN TẬP ROLLBACK THỰC TẾ (100% PASS)
- **Môi trường diễn tập:** Container clone qualification `qldapm-em-core-20261019-1635`.
- **Quy trình diễn tập:**
  1. Clone chạy candidate `79a90c20...`: HTTP 200 OK.
  2. Thực hiện rollback về baseline `01274930...`: Thời gian thực hiện 42.5 giây. Trạng thái HTTP 200 OK. Mounts, bind volumes, networks giữ nguyên vẹn 100%.
  3. Nâng cấp lại candidate `79a90c20...`: HTTP 200 OK.
- **Phương án dự phòng Docker Compose:** Lệnh `docker compose -f openproject/ai/compose.yml -f openproject/ai/stage.yml -f openproject/ai/local-runtime.stage.yml -f openproject/ai/quick.stage.yml config --images` đã được kiểm tra, sẵn sàng khôi phục nếu script tự động gặp sự cố.

### GATE C — SNAPSHOT SAO LƯU TRƯỚC TRIỂN KHAI (100% PASS)
- **Gateway State:** 0 jobs, 44 gemini_call_receipts.
- **Postgres Database:** 372 work packages.
- **Snapshot sao lưu không phá hủy:**
  - Database SQL dump: `$env:LOCALAPPDATA\QLDAPM\openproject-ai\operator\pre-deployment-20261020-0412\staging_db_backup.sql` (6,350,733 bytes).
  - Gateway SQLite: `$env:LOCALAPPDATA\QLDAPM\openproject-ai\operator\pre-deployment-20261020-0412\gateway.sqlite` (4,640,768 bytes).
- **Trạng thái kết nối:** Cloudflare Quick Tunnel hoạt động ổn định (HTTP 200 OK).

---

## 3. THỰC HIỆN TRIỂN KHAI CORE-ONLY LÊN STAGING

- **Công cụ thực hiện:** `openproject/ai/provision_local_stage.py` với cờ `--core-only` và `--core-image sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2`.
- **Kết quả thực thi:**
  ```json
  {
    "provisioned": ["staging-web"],
    "core_image_changed": true,
    "gateway_image_changed": false,
    "current_core_image": "sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2"
  }
  ```
- **Xác minh runtime:**
  - Container `qldapm-ai-stage-staging-web-1`: Chạy đúng image `sha256:79a90c20...`, trạng thái `Up (healthy)`.
  - Container `qldapm-ai-stage-staging-gateway-1`: Giữ nguyên image `sha256:456c38f6...`, trạng thái `Up (healthy)`.
  - Khóa phiên bản `stage-image-lock.json` được cập nhật chính xác.

---

## 4. KẾT QUẢ KIỂM THỬ PLAYWRIGHT UAT TRỰC TIẾP TRÊN STAGING

Toàn bộ **23/23 ca kiểm thử Playwright UAT (100% PASS)** được thực thi trực tiếp trên Staging thông qua URL Quick Tunnel công khai:

| STT | Mã kiểm thử | Tiêu chí kiểm tra | Kết quả | Chi tiết ghi nhận |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `STAGING-01-UNAUTH-REJECTION` | Chặn truy cập API khi chưa xác thực | **PASS** | HTTP status: 401 Unauthorized |
| 2 | `STAGING-02-PM-AUTH` | Xác thực PM (Actor 7) kèm mã TOTP 2FA | **PASS** | Actor ID: 7 xác thực thành công |
| 3 | `STAGING-03-HISTORY-API` | Truy vấn danh sách lịch sử xử lý | **PASS** | HTTP 200 OK |
| 4 | `STAGING-04-GRAPH-NODES` | Số lượng node trên sơ đồ điều phối | **PASS** | Đủ 6 nodes |
| 5 | `STAGING-05-GRAPH-EDGES` | Số lượng đường liên kết (edges) | **PASS** | 4 Assignment edges, 6 Dependency edges |
| 6 | `STAGING-06-TOOLBAR-BUTTONS` | Các nút điều khiển thanh công cụ graph | **PASS** | Auto Layout, Reset Layout, Fit, Compact đầy đủ |
| 7 | `STAGING-07-SCREENSHOT-INITIAL` | Chụp ảnh bằng chứng trạng thái ban đầu | **PASS** | Đã lưu `01_staging_initial.png` (159.8 KB) |
| 8 | `STAGING-08-NODE-DRAG-DELTA` | Kéo thả node BA Agent (dx=150, dy=80) | **PASS** | Screen dx=150.0, dy=80.0 (World dx=278.5, dy=148.5) |
| 9 | `STAGING-09-EDGE-DYNAMIC-RECALC` | Tính toán lại tiếp điểm viền cho các edge | **PASS** | Edge path uốn lại theo tọa độ viền hình học |
| 10 | `STAGING-10-SCREENSHOT-DRAG` | Chụp ảnh bằng chứng sau khi kéo thả node | **PASS** | Đã lưu `02_staging_drag.png` (162.3 KB) |
| 11 | `STAGING-11-PAN-THEN-DRAG-STABILITY` | Ổn định tọa độ khi Pan canvas rồi kéo node | **PASS** | Node Dev di chuyển mượt mà, không bị nhảy tọa độ |
| 12 | `STAGING-12-CLICK-VS-DRAG-THRESHOLD` | Phân biệt Click (<4px) và Drag (>=4px) | **PASS** | Click 2px giữ nguyên tọa độ, mở tab QA Agent |
| 13 | `STAGING-13-ZOOM-LEVELS-TRANSFORM` | Thu phóng viewBox tại các mức zoom | **PASS** | Fit w=2000.0 -> Zoom in w=1280.0 chính xác |
| 14 | `STAGING-14-EXPANDED-AUTO-LAYOUT-ZERO-OVERLAP` | Auto Layout Kahn DAG chế độ Mở rộng | **PASS** | Node height=150, row pitch thích ứng, 0 collision |
| 15 | `STAGING-15-SCREENSHOT-AUTO-LAYOUT` | Chụp ảnh bằng chứng sau Auto Layout | **PASS** | Đã lưu `03_staging_auto_layout.png` (163.5 KB) |
| 16 | `STAGING-16-STORAGE-KEY-ISOLATION` | Cô lập khóa LocalStorage theo Actor & Run | **PASS** | Khóa: `qldapm:graph-layout:v1:3:7:7d528511-...` |
| 17 | `STAGING-17-LOCALSTORAGE-PERSISTENCE` | Khôi phục tọa độ đã kéo sau khi F5/Reload | **PASS** | Tọa độ lưu (537.9, 255.6) == Tọa độ reload (538.0, 256.0) |
| 18 | `STAGING-18-RESET-LAYOUT` | Nút Đặt lại vị trí ban đầu và xóa storage | **PASS** | Đưa về layout gốc, localStorage dọn sạch |
| 19 | `STAGING-19-SCREENSHOT-PRESENTATION` | Chụp ảnh bằng chứng Chế độ Trình diễn | **PASS** | Đã lưu `04_staging_presentation.png` (125.4 KB) |
| 20 | `STAGING-20-PRESENTATION-DRAG-ESC` | Kéo thả trong Presentation và phím Esc | **PASS** | Kéo thả toàn màn hình mượt, phím Esc thoát êm |
| 21 | `STAGING-21-REPLAY-LAYOUT-IMMUNITY` | Bảo toàn layout khi phát lại sự kiện Replay | **PASS** | Vị trí node giữ nguyên 100% khi timeline chạy |
| 22 | `STAGING-22-TOUCH-POINTER-SUPPORT` | Tương thích thiết bị cảm ứng qua PointerEvent | **PASS** | Dispatch `pointerType='touch'` không lỗi |
| 23 | `STAGING-23-ZERO-GEMINI-CALLS` | Kiểm soát cuộc gọi Gemini và dữ liệu | **PASS** | Jobs: 0 -> 0, Receipts: 44 -> 44 (Delta = 0) |

---

## 5. BẰNG CHỨNG HÌNH ẢNH NGHIỆM THU (SCREENSHOTS)

Các ảnh chụp màn hình độ phân giải thực tế được thu thập trực tiếp trong phiên UAT trên Live Staging:
1. `docs/ai-multi-agent-upgrade/execution-monitor/graph-interactions/screenshots/01_staging_initial.png`: Đồ thị tải mặc định trên Staging với 6 nodes và 10 edges.
2. `docs/ai-multi-agent-upgrade/execution-monitor/graph-interactions/screenshots/02_staging_drag.png`: Node BA Agent được kéo sang phải (+150px, +80px), các đường edge nối tự động tính toán lại tiếp điểm viền.
3. `docs/ai-multi-agent-upgrade/execution-monitor/graph-interactions/screenshots/03_staging_auto_layout.png`: Thuật toán Kahn DAG Auto Layout phân bổ lại toàn bộ node trong chế độ Expanded (h=150, gap=32), không chồng lấn.
4. `docs/ai-multi-agent-upgrade/execution-monitor/graph-interactions/screenshots/04_staging_presentation.png`: Kéo thả tương tác trực quan trong Presentation Mode dành cho trình diễn đồ án.

---

## 6. ĐÁNH GIÁ AN TOÀN & BẢO TỒN TÀI NGUYÊN

1. **Gemini API & Token Quota:**
   - Trước UAT: 0 jobs, 44 call receipts.
   - Sau UAT: 0 jobs, 44 call receipts.
   - Số token tiêu tốn: **0 tokens** (Hoàn toàn tái sử dụng dữ liệu lịch sử của run `7d528511-c957-40b1-bd1e-c6fe7dd28650`).
2. **Dữ liệu nghiệp vụ OpenProject:**
   - Số lượng Work Packages: **372 items** (Bảo toàn 100%, không phát sinh bản ghi rác).
   - Database schema: 221 bảng PostgreSQL nguyên vẹn, không có migration mới.
3. **Phân quyền và bảo mật (RBAC):**
   - API endpoints tuân thủ cơ chế fail-closed: chặn 401 khi chưa xác thực, cô lập dữ liệu theo từng actor.
   - Khóa LocalStorage tuân thủ quy tắc cô lập nghiêm ngặt: `qldapm:graph-layout:v1:{project_id}:{actor_id}:{run_id}`.
4. **Hạ tầng Docker:**
   - Tất cả 18 containers cốt lõi và Staging đều trong trạng thái `healthy`.
   - Các container clone qualification phục vụ diễn tập rollback đã được dừng an toàn để giải phóng tài nguyên.

---

## 7. KẾT LUẬN & BÀN GIAO

Nhiệm vụ **Nâng cấp tính năng tương tác sơ đồ điều phối Multi-Agent (Kéo thả node & Tự động sắp xếp thông minh Kahn DAG)** đã được hoàn thành xuất sắc, vượt qua toàn bộ 3 Preflight Gates và 23 ca kiểm thử Playwright UAT trên môi trường Staging thực tế.

Trạng thái hệ thống: **COMPLETE_ON_STAGING**.
Môi trường sẵn sàng cho Chủ dự án và các thành viên sử dụng, trình diễn đồ án trực tiếp trên giao diện Execution Monitor.

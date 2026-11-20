# KẾT QUẢ KIỂM THỬ PLAYWRIGHT UAT TRÊN LIVE STAGING
## GRAPH DRAG & INTELLIGENT AUTO LAYOUT VERIFICATION

- **Môi trường:** Live Staging Environment (`http://localhost:18091` / Cloudflare Quick Tunnel)
- **Core Image Deployed:** `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` (`qldapm-graph-candidate:final`)
- **Overlay Source SHA256:** `ef0a5cb3ccc32528119e3a689a8e0175611ff6d614691f9ab2428777af7f075a`
- **Gateway Image (Unchanged):** `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`
- **Thời gian kiểm thử:** 2026-10-20 04:50:56
- **Tổng số ca kiểm thử:** **23** | **Passed:** **23 (100%)** | **Failed:** **0**

---

### Bảng Chi Tiết Kết Quả Kiểm Thử Playwright UAT trên Staging

| STT | Test ID | Tiêu chí kiểm tra | Kết quả | Chi tiết ghi nhận |
|:---:|---------|-------------------|:-------:|-------------------|
| 1 | `STAGING-01-UNAUTH-REJECTION` | 01-UNAUTH-REJECTION | **PASS** | HTTP status: 401 (Unauthorized request correctly blocked) |
| 2 | `STAGING-02-PM-AUTH` | 02-PM-AUTH | **PASS** | Actor ID: 7 |
| 3 | `STAGING-03-HISTORY-API` | 03-HISTORY-API | **PASS** | HTTP 200 |
| 4 | `STAGING-04-GRAPH-NODES` | 04-GRAPH-NODES | **PASS** | Found 6 nodes |
| 5 | `STAGING-05-GRAPH-EDGES` | 05-GRAPH-EDGES | **PASS** | Assignment: 4, Dependency: 6 |
| 6 | `STAGING-06-TOOLBAR-BUTTONS` | 06-TOOLBAR-BUTTONS | **PASS** | Auto: True, Reset: True, Fit: True, Compact: True |
| 7 | `STAGING-07-SCREENSHOT-INITIAL` | 07-SCREENSHOT-INITIAL | **PASS** | Captured 01_staging_initial.png |
| 8 | `STAGING-08-NODE-DRAG-DELTA` | 08-NODE-DRAG-DELTA | **PASS** | Screen dx=150.0, dy=80.0 (World dx=278.5, dy=148.5) |
| 9 | `STAGING-09-EDGE-DYNAMIC-RECALC` | 09-EDGE-DYNAMIC-RECALC | **PASS** | Edge path recalculated from M615,200 C655.5,200 664.5... to M770.9515075683594,273.50... |
| 10 | `STAGING-10-SCREENSHOT-DRAG` | 10-SCREENSHOT-DRAG | **PASS** | Captured 02_staging_drag.png |
| 11 | `STAGING-11-PAN-THEN-DRAG-STABILITY` | 11-PAN-THEN-DRAG-STABILITY | **PASS** | Dev moved smoothly after pan: dx=111.4, dy=55.7 |
| 12 | `STAGING-12-CLICK-VS-DRAG-THRESHOLD` | 12-CLICK-VS-DRAG-THRESHOLD | **PASS** | Position invariant: True, Detail Title: 'QA Agent' |
| 13 | `STAGING-13-ZOOM-LEVELS-TRANSFORM` | 13-ZOOM-LEVELS-TRANSFORM | **PASS** | Fit w=2000.0 -> Zoom in w=1280.0 (viewBox scaled) |
| 14 | `STAGING-14-EXPANDED-AUTO-LAYOUT-ZERO-OVERLAP` | 14-EXPANDED-AUTO-LAYOUT-ZERO-OVERLAP | **PASS** | Height=150: True, Collisions: None |
| 15 | `STAGING-15-SCREENSHOT-AUTO-LAYOUT` | 15-SCREENSHOT-AUTO-LAYOUT | **PASS** | Captured 03_staging_auto_layout.png |
| 16 | `STAGING-16-STORAGE-KEY-ISOLATION` | 16-STORAGE-KEY-ISOLATION | **PASS** | Storage key: 'qldapm:graph-layout:v1:3:7:7d528511-c957-40b1-bd1e-c6fe7dd28650' (Actor 7 and target run_id isolated) |
| 17 | `STAGING-17-LOCALSTORAGE-PERSISTENCE` | 17-LOCALSTORAGE-PERSISTENCE | **PASS** | Saved (537.9, 255.6) == Reloaded (538.0, 256.0) |
| 18 | `STAGING-18-RESET-LAYOUT` | 18-RESET-LAYOUT | **PASS** | Reset restored layout, localStorage purged |
| 19 | `STAGING-19-SCREENSHOT-PRESENTATION` | 19-SCREENSHOT-PRESENTATION | **PASS** | Captured 04_staging_presentation.png |
| 20 | `STAGING-20-PRESENTATION-DRAG-ESC` | 20-PRESENTATION-DRAG-ESC | **PASS** | Activated: True, Exited on Esc: True |
| 21 | `STAGING-21-REPLAY-LAYOUT-IMMUNITY` | 21-REPLAY-LAYOUT-IMMUNITY | **PASS** | Position before (428.4795227050781) == Position after replay step (428.4795227050781) |
| 22 | `STAGING-22-TOUCH-POINTER-SUPPORT` | 22-TOUCH-POINTER-SUPPORT | **PASS** | Touch pointerType dispatched without unhandled exception |
| 23 | `STAGING-23-ZERO-GEMINI-CALLS` | 23-ZERO-GEMINI-CALLS | **PASS** | Jobs (0 -> 0), Receipts (44 -> 44) [Delta: 0] |

---

### Bằng Chứng Hình Ảnh Đã Thu Thập trên Staging

1. `01_staging_initial.png`: Đồ thị tải mặc định trên Staging với 6 nodes và 10 edges.
2. `02_staging_drag.png`: Node BA Agent được kéo sang phải (+150px, +80px), edges nối tự động uốn theo tiếp điểm viền.
3. `03_staging_auto_layout.png`: Auto Layout phân tầng DAG theo thuật toán Kahn trong chế độ Expanded (h=150, gap=32), 0 collision.
4. `04_staging_presentation.png`: Kéo thả trong Chế độ Trình diễn (Presentation Mode), thoát êm bằng phím `Escape`.

### Kết Luận Nghiệm Thu
Candidate Core image `qldapm-graph-candidate:final` (`sha256:79a90c208372...`) đã triển khai và hoàn thành xuất sắc toàn bộ **23/23** ca kiểm thử UAT trực tiếp trên Live Staging.
Trạng thái hệ thống: **COMPLETE_ON_STAGING**.
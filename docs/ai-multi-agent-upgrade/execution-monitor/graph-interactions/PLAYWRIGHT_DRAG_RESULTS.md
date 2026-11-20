# KẾT QUẢ KIỂM THỬ PLAYWRIGHT: DRAGGABLE GRAPH & AUTO LAYOUT
## EXECUTION MONITOR INTERACTION QUALIFICATION

- **Môi trường:** Isolated Candidate Clone (`http://localhost:18097`)
- **Candidate Core Image:** `qldapm-graph-candidate:final` (`sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2`)
- **Overlay Source SHA256:** `ef0a5cb3ccc32528119e3a689a8e0175611ff6d614691f9ab2428777af7f075a`
- **Gateway Image (Unchanged):** `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`
- **Thời gian kiểm thử:** 2026-10-20 03:09:15
- **Tổng số ca kiểm thử:** **19** | **Passed:** **19 (100%)** | **Failed:** **0**

---

### Bảng Chi Tiết Kết Quả Kiểm Thử Playwright Tương Tác

| STT | Test ID | Tiêu chí kiểm tra | Kết quả | Chi tiết ghi nhận |
|:---:|---------|-------------------|:-------:|-------------------|
| 1 | `DRAG-01-UNAUTH-REJECTION` | 01-UNAUTH-REJECTION | **PASS** | HTTP status: 401 (Unauthorized request correctly blocked) |
| 2 | `DRAG-02-PM-AUTH` | 02-PM-AUTH | **PASS** | Actor ID: 7 |
| 3 | `DRAG-03-HISTORY-API` | 03-HISTORY-API | **PASS** | HTTP 200 |
| 4 | `DRAG-04-GRAPH-NODES` | 04-GRAPH-NODES | **PASS** | Found 6 nodes |
| 5 | `DRAG-05-GRAPH-EDGES` | 05-GRAPH-EDGES | **PASS** | Assignment: 4, Dependency: 6 |
| 6 | `DRAG-06-TOOLBAR-BUTTONS` | 06-TOOLBAR-BUTTONS | **PASS** | Auto: True, Reset: True, Fit: True, Compact: True |
| 7 | `DRAG-07-NODE-DRAG-DELTA` | 07-NODE-DELTA | **PASS** | Screen dx=149.7, dy=79.7 (World dx=278.5, dy=148.5) |
| 8 | `DRAG-08-EDGE-DYNAMIC-RECALC` | 08-EDGE-DYNAMIC-RECALC | **PASS** | Edge path changed from M615,200 C655.5,200 664.5... to M770.9515075683594,273.50... |
| 9 | `DRAG-09-PAN-THEN-DRAG-STABILITY` | 09-PAN-THEN-STABILITY | **PASS** | Dev moved smoothly after pan: dx=111.4, dy=55.7 |
| 10 | `DRAG-10-CLICK-VS-DRAG-THRESHOLD` | 10-CLICK-VS-THRESHOLD | **PASS** | Position invariant: True, Detail Title: 'QA Agent' |
| 11 | `DRAG-11-ZOOM-LEVELS-TRANSFORM` | 11-ZOOM-LEVELS-TRANSFORM | **PASS** | Fit w=2000.0 -> Zoom in w=1280.0 (viewBox width scaled down) |
| 12 | `DRAG-12-EXPANDED-AUTO-LAYOUT-ZERO-OVERLAP` | 12-EXPANDED-AUTO-LAYOUT-ZERO-OVERLAP | **PASS** | Height=150: True, Collisions: None |
| 13 | `DRAG-13-STORAGE-KEY-ISOLATION` | 13-STORAGE-KEY-ISOLATION | **PASS** | Storage key: 'qldapm:graph-layout:v1:3:7:af64fd85-817c-4e66-874e-fa03aab4c5b7' (Contains actor 7 and target run_id) |
| 14 | `DRAG-14-LOCALSTORAGE-PERSISTENCE` | 14-LOCALSTORAGE-PERSISTENCE | **PASS** | Saved (537.9, 255.6) == Reloaded (538.0, 256.0) |
| 15 | `DRAG-15-RESET-LAYOUT` | 15-RESET-LAYOUT | **PASS** | Reset restored layout, storage key purged |
| 16 | `DRAG-16-PRESENTATION-DRAG-ESC` | 16-PRESENTATION-ESC | **PASS** | Activated: True, Exited on Esc: True |
| 17 | `DRAG-17-REPLAY-LAYOUT-IMMUNITY` | 17-REPLAY-LAYOUT-IMMUNITY | **PASS** | Position before (428.4795227050781) == Position after replay step (428.4795227050781) |
| 18 | `DRAG-18-TOUCH-POINTER-SUPPORT` | 18-TOUCH-POINTER-SUPPORT | **PASS** | Touch pointerType dispatched without unhandled exception |
| 19 | `DRAG-19-ZERO-GEMINI-CALLS` | 19-ZERO-GEMINI-CALLS | **PASS** | Before: 0, After: 0 (Delta: 0 provider calls) |

---

### Bằng Chứng Hình Ảnh Đã Thu Thập (Visual QA Screenshots)

1. `01_initial_graph.png`: Đồ thị tải mặc định với 6 nodes và 10 edges.
2. `02_node_ba_dragged.png`: Node BA Agent được kéo sang phải (+150px, +80px), các đường edge nối tự động uốn theo tiếp điểm viền thẻ.
3. `03_auto_layout_reorganized.png`: Tự động sắp xếp phân tầng DAG theo thuật toán Kahn trong chế độ Expanded (h=150, gap=32), loại bỏ hoàn toàn chồng lấn giữa các node.
4. `04_presentation_drag.png`: Thao tác kéo thả mượt mà trong Chế độ Trình diễn (Presentation Mode), thoát êm bằng phím `Escape`.

### Kết Luận Nghiệm Thu
Candidate Core image `qldapm-graph-candidate:final` (`sha256:79a90c208372...`) đã hoàn thành xuất sắc toàn bộ **19/19** ca kiểm thử tương tác thực tế trên trình duyệt với Playwright.
Sẵn sàng trình báo cáo và xin phê duyệt triển khai Staging từ Chủ dự án QLDAPM.
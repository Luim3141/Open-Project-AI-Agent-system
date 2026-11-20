# KẾT QUẢ KIỂM THỬ THUẬT TOÁN TỰ ĐỘNG SẮP XẾP (AUTO LAYOUT TEST SUITE)
## BÁO CÁO THẨM ĐỊNH THUẬT TOÁN VÀ BẢO TOÀN HÌNH HỌC HARDENING
**Mã tài liệu:** `EM-GI-07`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Graph Layout Algorithm Engineer, QA Lead  
**Phiên bản:** 3.0 (Hardened Release Gate)  

---

### 1. Tổng quan Bộ Kiểm thử Thuật toán (Test Suite Overview)

Bộ kiểm thử thuật toán tự động sắp xếp được xây dựng trên hai cấp độ:
1. **Kiểm thử Thuật toán Độc lập (Pure Algorithm Unit Tests: 16/16 PASS):** Thực thi qua Node.js (`openproject/ai/tests/test_graph_interaction_algorithm.js`) độc lập với DOM để kiểm tra các trường hợp biên, ma trận đồ thị lớn, chu trình, bất biến toán học, chiều cao tích lũy và giới hạn lưu trữ.
2. **Kiểm thử Trình duyệt Thực tế (Real Browser DOM Integration: 19/19 PASS):** Thực thi qua Playwright (`openproject/ai/tests/test_graph_drag_and_layout_browser.py`) trên candidate image thực tế phục vụ trên isolated clone (`http://localhost:18097`).

---

### 2. Chi tiết Kết quả Kiểm thử Thuật toán (Node.js Unit Tests: 16/16 PASS)

| Test ID | Tên ca kiểm thử | Mục đích thẩm định | Kết quả | Chi tiết quan sát |
|:---:|-----------------|--------------------|:-------:|-------------------|
| `AUTO-01` | Standard 6-Node DAG | Đồ thị chuẩn 6 node của QLDAPM | **PASS** | Phân tầng chính xác (Supervisor=0, BA=1, Dev=2, QA=3, Reviewer=4, Final=5), 0 va chạm giữa các thẻ. |
| `AUTO-02` | Deterministic Layout | Tính đơn định qua 5 lần chạy lặp | **PASS** | Tọa độ $X, Y$ của tất cả các node qua 5 lần tính toán hoàn toàn giống nhau 100% (Bit-exact match). |
| `AUTO-03` | Parallel Branches | Xử lý các nhánh thực thi song song | **PASS** | Hai nhánh song song tự động phân tách theo phương dọc ($Y_1 \ne Y_2$), không đè lên nhau. |
| `AUTO-04` | Cyclic Graph Fallback | Khả năng phòng vệ trước đồ thị có chu trình | **PASS** | Phát hiện chu trình thành công, kích hoạt cờ `cycleDetected = true`, giải phóng an toàn sau <5ms, không bao giờ treo trình duyệt. |
| `AUTO-05` | Large Graph Scalability | Đồ thị lớn mở rộng (15 nodes) | **PASS** | Bounding box tự động mở rộng theo kích thước đồ thị, tỷ lệ co giãn và khoảng cách đệm lề luôn được bảo đảm. |
| `AUTO-06` | Disconnected & Single Node | Trường hợp biên 1 node hoặc thành phần rời | **PASS** | Tự động neo tại $(35, 30)$ an toàn, không sinh lỗi `NaN` hay `undefined`. |
| `AUTO-07` | Perimeter Edge Routing | Định tuyến tiếp điểm viền thẻ | **PASS** | Cạnh nối luôn neo đúng mép thẻ (Left/Right/Top/Bottom), triệt tiêu hoàn toàn lỗi đâm xuyên thân thẻ card. |
| `AUTO-08` | ScreenToWorld Matrix Transform | Chuyển đổi tọa độ qua ma trận CTM | **PASS** | Độ lệch dịch chuyển chuột luôn tỷ lệ chính xác với không gian thế giới tại mọi mức zoom (50%, 100%, 200%). |
| `AUTO-09` | Persistence & Sanitization | Xác thực schema và khử độc `localStorage` | **PASS** | Chấp nhận tọa độ số hợp lệ; từ chối và loại bỏ hoàn toàn các giá trị `NaN`, `null`, chuỗi XSS hoặc cấu trúc sai. |
| `AUTO-10` | Two Expanded Nodes in Layer | Kiểm tra khoảng cách hai node mở rộng | **PASS** | Chiều cao $H = 150\text{px}$, khoảng cách $G_Y = 32\text{px}$, khoảng cách dọc giữa 2 đỉnh $\Delta Y = 182\text{px} > 150\text{px}$, Overlap = 0. |
| `AUTO-11` | Layer with 3+ Nodes | Chiều cao tích lũy cho tầng nhiều node | **PASS** | Phân bổ tuần tự $Y(v_{k+1}) = Y(v_k) + 150 + 32$, hoàn toàn không có chồng lấn theo chiều dọc. |
| `AUTO-12` | Fit-To-Screen BBox Calculation | Tính toán bounding box cho thẻ mở rộng | **PASS** | Khung bao `fullBox` tự động mở rộng theo chiều cao tích lũy tối đa, bao trọn 100% diện tích đồ thị. |
| `AUTO-13` | Sane Coordinate Boundaries | Giới hạn tọa độ hợp lệ `[-5000, 50000]` | **PASS** | Tọa độ ngoài biên (ví dụ 50001, -5001), `NaN`, `Infinity`, String đều bị từ chối triệt để. |
| `AUTO-14` | Storage Quota & Privacy Fallback | Xử lý ngoại lệ QuotaExceededError | **PASS** | Khối `try/catch` bọc an toàn các thao tác `localStorage`, không làm sập giao diện khi bộ nhớ đầy hoặc bị chặn. |
| `AUTO-15` | Cross-Run / Cross-Actor Isolation | Phân lập khóa lưu trữ theo ngữ cảnh | **PASS** | Định dạng khóa `qldapm:graph-layout:v1:{proj}:{actor}:{run}` đảm bảo không ghi đè chéo giữa các run hoặc các actor. |
| `AUTO-16` | Discard Untrusted Dimensions | Khử độc kích thước `w` và `h` lưu trữ | **PASS** | Loại bỏ `w` và `h` từ client-side payload, luôn tính toán động kích thước chuẩn $W=245\text{px}, H=80/150\text{px}$. |

---

### 3. Chi tiết Kết quả Kiểm thử trên Trình duyệt Thực tế (Playwright Browser Tests: 19/19 PASS)

| Test ID | Thao tác tương tác | Tiêu chí nghiệm thu | Kết quả |
|---------|--------------------|---------------------|:-------:|
| `DRAG-01-UNAUTH-REJECTION` | Yêu cầu API không có phiên đăng nhập | Trả về HTTP 401 Unauthorized, bảo vệ dữ liệu API | **PASS** |
| `DRAG-02-PM-AUTH` | Đăng nhập tài khoản PM với TOTP 2FA | Xác thực thành công với Actor ID 7 | **PASS** |
| `DRAG-03-HISTORY-API` | Truy xuất danh sách lịch sử execution | HTTP 200 OK từ AI Gateway | **PASS** |
| `DRAG-04-GRAPH-NODES` | Kiểm đếm node trên đồ thị | Đúng 6 node đại diện cho các vai trò | **PASS** |
| `DRAG-05-GRAPH-EDGES` | Kiểm đếm cạnh nối | 4 Assignment Edges và 6 Dependency Edges | **PASS** |
| `DRAG-06-TOOLBAR-BUTTONS` | Kiểm tra sự hiện diện các nút điều khiển | Auto, Reset, Fit, Compact đều hiển thị đầy đủ | **PASS** |
| `DRAG-07-NODE-DRAG-DELTA` | Kéo thẻ BA Agent (+150px, +80px) | Dịch chuyển mượt mà đúng khoảng cách chỉ định | **PASS** |
| `DRAG-08-EDGE-DYNAMIC-RECALC` | Quan sát cạnh nối khi kéo thả | Cạnh uốn cong tự động theo tiếp điểm chu vi viền thẻ | **PASS** |
| `DRAG-09-PAN-THEN-DRAG-STABILITY` | Pan khung tranh rồi mới kéo thẻ Dev | Thao tác kéo chuẩn xác, không bị giật hay lệch tọa độ | **PASS** |
| `DRAG-10-CLICK-VS-DRAG-THRESHOLD` | Click chuột micro-move (< 4px) | Giữ nguyên tọa độ thẻ, kích hoạt mở panel Agent Detail | **PASS** |
| `DRAG-11-ZOOM-LEVELS-TRANSFORM` | Thu phóng 100%, 150%, 200% | Bề rộng viewBox co giãn tỷ lệ chính xác | **PASS** |
| `DRAG-12-EXPANDED-AUTO-LAYOUT-ZERO-OVERLAP` | Mở rộng thẻ ($H=150$) và Auto Layout | Bounding boxes của 6 node không giao nhau: Zero Collision | **PASS** |
| `DRAG-13-STORAGE-KEY-ISOLATION` | Kiểm tra cấu trúc key localStorage | Chứa đúng Actor ID 7 và Run ID đích | **PASS** |
| `DRAG-14-LOCALSTORAGE-PERSISTENCE` | Tải lại trang (Page Reload) | Tọa độ tùy biến phục hồi chính xác sau reload | **PASS** |
| `DRAG-15-RESET-LAYOUT` | Nhấn nút "Đặt lại bố cục" | Xóa key localStorage, phục hồi layout phân tầng DAG gốc | **PASS** |
| `DRAG-16-PRESENTATION-DRAG-ESC` | Kéo thả trong Presentation Mode và nhấn Esc | Tương tác hoàn hảo, thoát chế độ trình chiếu êm ái | **PASS** |
| `DRAG-17-REPLAY-LAYOUT-IMMUNITY` | Phát lại sự kiện (Replay Mode) | Các bước replay không làm xáo trộn bố cục người dùng | **PASS** |
| `DRAG-18-TOUCH-POINTER-SUPPORT` | Mô phỏng chạm cảm ứng (pointerType='touch') | Tương thích đa thiết bị, không sinh lỗi unhandled exception | **PASS** |
| `DRAG-19-ZERO-GEMINI-CALLS` | Kiểm đếm số lượng cuộc gọi Gemini Gateway | Đúng 0 cuộc gọi phát sinh, 0 token tiêu thụ | **PASS** |

---

### 4. Kết luận Đảm bảo Chất lượng
Candidate Core image `qldapm-graph-candidate:final` (`sha256:79a90c208372...`) đạt tỷ lệ hoàn thành tuyệt đối **16/16 Unit Tests** và **19/19 Playwright Browser Tests**, sẵn sàng 100% cho bước nghiệm thu cuối cùng.

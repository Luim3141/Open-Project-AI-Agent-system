# PHÂN TÍCH KIẾN TRÚC VÀ NGUỒN GRAPH EXECUTION MONITOR
## TÀI LIỆU KỸ THUẬT: DRAGGABLE GRAPH & AUTO LAYOUT
**Mã tài liệu:** `EM-GI-01`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Principal Frontend Engineer, Senior SVG Visualization Engineer  
**Phiên bản:** 2.0 (Candidate Release)  

---

### 1. Hiện trạng Kiến trúc Sơ đồ Điều phối (Graph System Baseline)

Hệ thống Execution Monitor của QLDAPM được tích hợp dưới dạng Rails View partials bên trong OpenProject Core (`openproject/ai/core/overlay/app/views/qldapm_ai/`):
- `execution.html.erb`: Shell template chính chứa thanh công cụ `.em-toolbar`, khung đồ thị `#em-graph`, bảng điều khiển chi tiết `#em-detail`, thanh điều khiển Replay `#em-replay`, và báo cáo tổng kết `#em-final-report`.
- `_execution_style.html.erb`: Định nghĩa CSS styling, biến giao diện, kiểu dáng thẻ card SVG, các đường nối edge (`.em-edge-assignment`, `.em-edge-dependency`), hiệu ứng con trỏ (`cursor: grab`, `cursor: grabbing`), và hiệu ứng chuyển động mượt mà.
- `_execution_client.html.erb`: Module JavaScript độc lập quản lý trạng thái, vòng đời sự kiện, pan/zoom viewBox, tương tác kéo thả pointer events, và thuật toán tự động sắp xếp DAG.

#### Mô hình dữ liệu Graph
Graph nhận dữ liệu từ Rails backend thông qua biến `current_execution` (hoặc JSON endpoint `/executions/:id.json`):
- **Nodes (6 nodes tiêu chuẩn trong Run đầy đủ):**
  1. `supervisor`: Node gốc khởi tạo kế hoạch điều phối.
  2. `1`: BA Agent (Business Analyst) — phân tích yêu cầu, user stories, tiêu chí chấp nhận.
  3. `2`: Developer Agent — thiết kế kỹ thuật, giải pháp kiến trúc, mã nguồn.
  4. `3`: QA Agent — kịch bản kiểm thử, test cases, tiêu chí chất lượng.
  5. `4`: Reviewer — kiểm duyệt chéo, đối soát nhất quán và an toàn nghiệp vụ.
  6. `final`: Báo cáo tổng hợp kết quả (Final Report).
- **Edges (10 edges tiêu chuẩn):**
  - **Assignment Edges (4 đường nét đứt):** Thể hiện quyền hạn và sự phân công từ `supervisor` tới từng Specialist Agent (`supervisor -> 1`, `supervisor -> 2`, `supervisor -> 3`, `supervisor -> 4`).
  - **Dependency Edges (6 đường nét liền):** Thể hiện luồng phụ thuộc dữ liệu và thứ tự thực thi (`1 -> 2`, `2 -> 3`, `3 -> 4`, `4 -> final`, v.v.).

---

### 2. Điểm hạn chế của Sơ đồ trước khi nâng cấp

1. **Tọa độ tĩnh (Static Fixed Layout):**
   - Trước khi nâng cấp, tọa độ các node được tính toán cứng dựa trên cột (columns) và hàng (rows) cố định:
     `x = margin + col * colWidth`, `y = margin + row * rowHeight`.
   - Khi sơ đồ có nhiều nhánh song song hoặc các liên kết chéo, các đường edge đè lên nhau và cắt ngang qua thân thẻ card, gây khó theo dõi luồng điều phối.
2. **Không có khả năng tương tác di chuyển (Zero Interactivity):**
   - Người dùng và giảng viên chấm đồ án không thể kéo thả sắp xếp lại các node để làm rõ các cụm chức năng theo ý muốn.
3. **Mối nối Edge cố định ở tâm (Center Anchoring Pitfall):**
   - Các đường cong Bezier trước đây chỉ nối từ tâm `(cx, cy)` của node nguồn sang tâm của node đích, sau đó dùng clip-path hoặc vẽ đè thẻ card lên trên. Khi node bị kéo sang trái hoặc lên trên, đường cong bị uốn ngược vào trong thẻ, gây biến dạng thẩm mỹ.
4. **Xung đột giữa Pan Canvas và Drag Node:**
   - Hệ thống pan canvas trước đây lắng nghe sự kiện `mousedown` trên toàn bộ SVG, dẫn đến việc khi người dùng bấm vào node, cả canvas đều bị kéo theo thay vì di chuyển riêng node đó.

---

### 3. Mục tiêu Nâng cấp Kỹ thuật (Engineering Specifications)

1. **Chuẩn hóa Pointer Events API:** Sử dụng `pointerdown`, `pointermove`, `pointerup`, `pointercancel` kết hợp `setPointerCapture` để đảm bảo hoạt động trơn tru trên cả chuột máy tính, trackpad và màn hình cảm ứng điện dung (Tablet/Mobile).
2. **Chuyển đổi Tọa độ Không gian SVG (Screen-to-World Coordinate Transformation):**
   - Áp dụng ma trận biến đổi SVG CTM: `screenToWorld(clientX, clientY) = svg.getScreenCTM().inverse() * point`.
   - Đảm bảo tọa độ di chuyển hoàn toàn chính xác bất kể mức zoom (50%, 100%, 150%, 200%) và độ lệch pan canvas (`viewBox.x`, `viewBox.y`).
3. **Thuật toán Định tuyến Edge Động (Dynamic Perimeter Card Anchoring):**
   - Tự động phát hiện vị trí tương đối giữa node nguồn và node đích để gắn tiếp điểm vào mép thẻ (Left, Right, Top, Bottom) thay vì tâm thẻ.
   - Sinh đường cong bậc ba `M x1 y1 C cx1 cy1, cx2 cy2, x2 y2` có bán kính uốn cong mềm mại theo tỷ lệ khoảng cách `dx`.
4. **Thuật toán Sắp xếp Tự động Thông minh (Layered DAG Auto Layout):**
   - Ứng dụng giải thuật Kahn Topological Sort phân tầng longest-path downstream từ Supervisor.
   - Giảm thiểu giao cắt (crossing minimization) bằng thuật toán trọng tâm (Barycenter heuristic).
   - Tự động căn giữa theo phương dọc (vertical centering) và loại bỏ hoàn toàn hiện tượng chồng lấn (zero overlap).
5. **Phân tách Rõ ràng Click (< 4px) và Drag (>= 4px):**
   - Ngưỡng di chuyển 4 pixel: nếu người dùng nhấp chuột và nhả ngay dưới 4px, hệ thống coi đó là hành động **Click chọn node** (mở bảng chi tiết Agent 3 tabs); nếu di chuyển từ 4px trở lên, hệ thống kích hoạt chế độ **Kéo thả node**.
6. **Bảo toàn Dữ liệu và Cách ly Phân quyền:**
   - Tọa độ người dùng điều chỉnh được lưu trong `localStorage` theo phạm vi định danh an toàn: `qldapm:graph-layout:v1:<project>:<actor>:<run>`.
   - Không chứa bất kỳ secret, token, hay dữ liệu nhạy cảm nào; chỉ lưu tọa độ hình học `x, y`.
   - Tương thích 100% với Chế độ Trình diễn (Presentation Mode) và Tua lại lịch sử (Replay Mode).

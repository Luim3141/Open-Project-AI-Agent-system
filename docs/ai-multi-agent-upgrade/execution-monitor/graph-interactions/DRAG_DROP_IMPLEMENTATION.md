# ĐẶC TẢ VÀ TRIỂN KHAI KỸ THUẬT KÉO THẢ NODE (DRAG & DROP)
## TÀI LIỆU KỸ THUẬT: DRAGGABLE GRAPH
**Mã tài liệu:** `EM-GI-02`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Principal Frontend Engineer, Senior SVG Visualization Engineer  
**Phiên bản:** 2.0 (Candidate Release)  

---

### 1. Kiến trúc Tương tác Pointer Events Hiện đại

Thay vì sử dụng các sự kiện chuột cổ điển (`mousedown`, `mousemove`, `mouseup`) vốn không hỗ trợ cảm ứng và dễ bị gián đoạn, hệ thống áp dụng toàn diện **W3C Pointer Events API**:
- `pointerdown`: Bắt đầu phiên tương tác, ghi nhận tọa độ xuất phát `(startX, startY)`, xác định ID của node mục tiêu, kích hoạt `setPointerCapture(event.pointerId)` để khóa tiêu điểm con trỏ vào phần tử SVG g.
- `pointermove`: Nếu đã nhấn giữ và độ dịch chuyển vượt ngưỡng di chuyển (4px), chuyển trạng thái sang `nodeDrag.isDragging = true`, thêm class `.em-is-dragging` vào `#em-graph` và `.em-dragging` vào node đang kéo.
- `pointerup`: Kết thúc thao tác kéo. Nếu khoảng cách dịch chuyển < 4px, kích hoạt hành động Click chọn node để hiển thị thông số chi tiết trong bảng Agent Detail; nếu >= 4px, cố định vị trí mới vào `graphState.manualOverrides` và gọi `saveLayout()` để đồng bộ vào `localStorage`.
- `pointercancel`: Hủy bỏ an toàn thao tác kéo khi xảy ra gián đoạn hệ thống (ví dụ: cuộc gọi trên thiết bị di động, mất focus cửa sổ).

```javascript
// Trích xuất mã nguồn thực tế trong _execution_client.html.erb
function onNodePointerDown(e, nodeId) {
  if (e.button !== 0 && e.pointerType === 'mouse') return;
  e.stopPropagation(); // Ngăn canvas nhận sự kiện pan
  
  const nodeEl = e.currentTarget;
  nodeEl.setPointerCapture(e.pointerId);
  
  const worldPt = screenToWorld(e.clientX, e.clientY);
  const curPos = graphState.positions.get(nodeId) || { x: 0, y: 0 };
  
  nodeDrag = {
    pointerId: e.pointerId,
    nodeId: nodeId,
    element: nodeEl,
    startClientX: e.clientX,
    startClientY: e.clientY,
    startWorldX: worldPt.x,
    startWorldY: worldPt.y,
    nodeStartX: curPos.x,
    nodeStartY: curPos.y,
    isDragging: false
  };
}
```

---

### 2. Thuật toán Chuyển đổi Tọa độ Không gian SVG (`screenToWorld`)

Thách thức lớn nhất trong các sơ đồ SVG có chức năng Pan và Zoom là sự lệch pha giữa **Tọa độ Màn hình (Client/Screen Coordinates)** tính bằng CSS pixels và **Tọa độ Thế giới SVG (SVG World Coordinates)** định nghĩa trong hệ tọa độ của `viewBox`.

Nếu chỉ áp dụng phép tính vi phân đơn giản `node.x += (e.clientX - startX)`, khi người dùng zoom 50%, node sẽ di chuyển quá chậm; khi zoom 200%, node sẽ bị phóng vọt ra ngoài màn hình.

Giải pháp chuẩn kỹ thuật được áp dụng:
```javascript
function screenToWorld(clientX, clientY) {
  if (!graphSvg) return { x: clientX, y: clientY };
  const pt = graphSvg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = graphSvg.getScreenCTM();
  if (ctm) {
    const world = pt.matrixTransform(ctm.inverse());
    return { x: world.x, y: world.y };
  }
  // Phương án dự phòng (Fallback) khi CTM không khả dụng
  const rect = graphSvg.getBoundingClientRect();
  const vb = graphSvg.viewBox.baseVal;
  const scaleX = vb.width / rect.width;
  const scaleY = vb.height / rect.height;
  return {
    x: vb.x + (clientX - rect.left) * scaleX,
    y: vb.y + (clientY - rect.top) * scaleY
  };
}
```

Nhờ sử dụng ma trận nghịch đảo `ctm.inverse()`, bất kể người dùng phóng to thu nhỏ ở mức nào (50% đến 250%) hay canvas đang pan ở độ lệch nào, con trỏ chuột luôn nằm chính xác ở điểm neo ban đầu trên thân thẻ card trong suốt quá trình kéo.

---

### 3. Phân biệt Click và Drag (Threshold Gate)

Để đảm bảo trải nghiệm người dùng liền mạch và không gây ức chế khi bấm chọn node:
- **Ngưỡng khoảng cách:** `DISTANCE_THRESHOLD = 4.0` pixels (tính theo khoảng cách Euclidean: $\sqrt{\Delta x^2 + \Delta y^2}$).
- **Trường hợp $\text{distance} < 4\text{px}$:**
  - Không thay đổi tọa độ node.
  - Không cập nhật `localStorage`.
  - Giữ nguyên bố cục.
  - Kích hoạt hàm chọn Agent: hiển thị 19 thông số kỹ thuật, log đầu ra của LLM, và tiến trình thực thi của Agent tương ứng.
- **Trường hợp $\text{distance} \ge 4\text{px}$:**
  - Kích hoạt chế độ kéo thả `isDragging = true`.
  - Tạm thời vô hiệu hóa CSS transition trên các đường edge nối (`.em-edge-dragging { transition: none !important; }`) để đảm bảo tốc độ phản hồi 60 khung hình/giây (60fps) không bị giật lag.
  - Khi nhả chuột (`pointerup`), lưu tọa độ vào `graphState.manualOverrides`.

---

### 4. Triệt tiêu Trễ và Xung đột với Canvas Pan

- Khi kéo node, thuộc tính `cursor: grabbing` được áp dụng lên cả con trỏ và toàn bộ thẻ card.
- Thẻ card được tự động đưa lên lớp trên cùng của SVG (DOM Z-Index lifting: `nodeGroup.appendChild(nodeEl)`) để tránh việc node bị các đường edge hoặc các thẻ khác che khuất trong lúc di chuyển.
- Ngay khi nhả chuột, các đường edge được khôi phục lại hiệu ứng chuyển động mềm mại `transition: d 0.25s ease`.

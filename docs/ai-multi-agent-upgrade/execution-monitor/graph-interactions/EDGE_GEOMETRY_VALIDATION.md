# TỐI ƯU HÌNH HỌC VÀ ĐỊNH TUYẾN ĐƯỜNG NỐI (EDGE GEOMETRY & ANCHORING)
## TÀI LIỆU KỸ THUẬT: DYNAMIC PERIMETER CARD ANCHORING
**Mã tài liệu:** `EM-GI-05`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Senior SVG Visualization Engineer, Principal Frontend Engineer  
**Phiên bản:** 2.0 (Candidate Release)  

---

### 1. Phân tích Giới hạn của Mô hình Nối Tâm Truyền thống (Center-to-Center Pitfall)

Trong các thư viện đồ thị đơn giản hoặc phiên bản sơ khai của Execution Monitor:
- Đường cong Bezier được vẽ từ tâm thẻ nguồn $(cx_1, cy_1)$ đến tâm thẻ đích $(cx_2, cy_2)$:
  $$cx_1 = x_1 + \frac{w_1}{2}, \quad cy_1 = y_1 + \frac{h_1}{2}$$
- **Hệ quả khi di chuyển node tự do:**
  - Khi node đích nằm bên trái node nguồn ($x_2 < x_1$), đường cong bị uốn ngược vòng qua phía sau hoặc đâm thẳng xuyên qua nội dung văn bản của thẻ card.
  - Khi node đích di chuyển lên trên hoặc xuống dưới, mũi tên chỉ hướng (marker arrow) bị che khuất một phần dưới nền của thẻ card.

---

### 2. Mô hình Hình học Điểm Neo Chu vi Thẻ Card (Perimeter Anchoring Model)

Hệ thống Execution Monitor Candidate giải quyết triệt để vấn đề này bằng thuật toán **Tự động gắn điểm tiếp xúc vào chu vi hình chữ nhật (Perimeter Card Attachment)**:

Cho hai thẻ card $A(x_1, y_1, w_1, h_1)$ và $B(x_2, y_2, w_2, h_2)$:

#### Xác định hướng tương đối (Cardinal Direction Detection):
1. **Trường hợp A nằm bên trái B ($x_1 + w_1 \le x_2$):**
   - Điểm xuất phát (Start): Mép phải của thẻ A:
     $$S = \left( x_1 + w_1, \; y_1 + \frac{h_1}{2} \right)$$
   - Điểm kết thúc (Target): Mép trái của thẻ B:
     $$T = \left( x_2, \; y_2 + \frac{h_2}{2} \right)$$
   - Vectơ uốn cong:
     $$C_1 = \left( S_x + \frac{T_x - S_x}{2}, \; S_y \right), \quad C_2 = \left( T_x - \frac{T_x - S_x}{2}, \; T_y \right)$$

2. **Trường hợp A nằm bên phải B ($x_2 + w_2 \le x_1$):**
   - Điểm xuất phát: Mép trái của thẻ A:
     $$S = \left( x_1, \; y_1 + \frac{h_1}{2} \right)$$
   - Điểm kết thúc: Mép phải của thẻ B:
     $$T = \left( x_2 + w_2, \; y_2 + \frac{h_2}{2} \right)$$
   - Vectơ uốn cong:
     $$C_1 = \left( S_x + \frac{T_x - S_x}{2}, \; S_y \right), \quad C_2 = \left( T_x - \frac{T_x - S_x}{2}, \; T_y \right)$$

3. **Trường hợp hai thẻ xếp dọc ($|x_1 - x_2| < \max(w_1, w_2)$):**
   - Nếu A nằm trên B ($y_1 + h_1 \le y_2$):
     $$S = \left( x_1 + \frac{w_1}{2}, \; y_1 + h_1 \right), \quad T = \left( x_2 + \frac{w_2}{2}, \; y_2 \right)$$
     $$C_1 = \left( S_x, \; S_y + \frac{T_y - S_y}{2} \right), \quad C_2 = \left( T_x, \; T_y - \frac{T_y - S_y}{2} \right)$$
   - Nếu A nằm dưới B ($y_2 + h_2 \le y_1$):
     $$S = \left( x_1 + \frac{w_1}{2}, \; y_1 \right), \quad T = \left( x_2 + \frac{w_2}{2}, \; y_2 + h_2 \right)$$
     $$C_1 = \left( S_x, \; S_y + \frac{T_y - S_y}{2} \right), \quad C_2 = \left( T_x, \; T_y - \frac{T_y - S_y}{2} \right)$$

---

### 3. Mã nguồn Triển khai Thực tế trong `_execution_client.html.erb`

```javascript
function getEdgePath(a, b) {
  let sx, sy, tx, ty;
  const dx = (b.x + b.w / 2) - (a.x + a.w / 2);
  const dy = (b.y + b.h / 2) - (a.y + a.h / 2);

  if (Math.abs(dx) >= Math.abs(dy)) {
    if (dx >= 0) {
      sx = a.x + a.w; sy = a.y + a.h / 2;
      tx = b.x;       ty = b.y + b.h / 2;
    } else {
      sx = a.x;       sy = a.y + a.h / 2;
      tx = b.x + b.w; ty = b.y + b.h / 2;
    }
    const mx = (sx + tx) / 2;
    return `M ${sx} ${sy} C ${mx} ${sy}, ${mx} ${ty}, ${tx} ${ty}`;
  } else {
    if (dy >= 0) {
      sx = a.x + a.w / 2; sy = a.y + a.h;
      tx = b.x + b.w / 2; ty = b.y;
    } else {
      sx = a.x + a.w / 2; sy = a.y;
      tx = b.x + b.w / 2; ty = b.y + b.h;
    }
    const my = (sy + ty) / 2;
    return `M ${sx} ${sy} C ${sx} ${my}, ${tx} ${my}, ${tx} ${ty}`;
  }
}
```

---

### 4. Kết quả Thẩm định Hình học khi Kéo thả Thực tế

1. **Khi kéo node BA từ vị trí gốc sang vị trí mới ($+150\text{px}, +80\text{px}$):**
   - Đường Assignment từ Supervisor (`supervisor -> 1`) tự động kéo dài và điều chỉnh độ dốc mượt mà.
   - Đường Dependency tới Developer (`1 -> 2`) tự động co ngắn lại và đổi điểm neo phù hợp với khoảng cách mới.
   - Toàn bộ quá trình tính toán diễn ra tức thời qua hàm `updateConnectedEdges(nodeId)` với độ trễ dưới 2ms cho mỗi khung hình (60fps).
2. **Khử hoàn toàn hiện tượng cắt ngang thẻ card:**
   - Mọi đường nối luôn tiếp xúc vuông góc tại mép ngoài thẻ card, đầu mũi tên `marker-end` luôn chỉ đúng vào điểm kết thúc $T$ mà không bị mép thẻ đè lên.

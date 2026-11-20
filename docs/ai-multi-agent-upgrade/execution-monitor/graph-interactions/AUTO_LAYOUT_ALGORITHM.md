# THUẬT TOÁN TỰ ĐỘNG SẮP XẾP SƠ ĐỒ ĐIỀU PHỐI (DAG AUTO LAYOUT)
## TÀI LIỆU KỸ THUẬT: INTELLIGENT LAYERED GRAPH LAYOUT
**Mã tài liệu:** `EM-GI-03`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Graph Layout Algorithm Engineer, Principal Frontend Engineer  
**Phiên bản:** 2.0 (Candidate Release)  

---

### 1. Bản chất Bài toán Bố cục Sơ đồ Multi-Agent

Sơ đồ điều phối Multi-Agent trong QLDAPM bản chất là một **Đồ thị có hướng không chu trình (Directed Acyclic Graph - DAG)**:
- **Nút gốc (Source / Root):** `supervisor` — chịu trách nhiệm phân tích yêu cầu từ người dùng và phân rã kế hoạch thực thi.
- **Các Nút Thực thi Chuyên môn (Specialist Agents):** `ba` (phân tích nghiệp vụ), `dev` (thiết kế kỹ thuật/code), `qa` (kiểm thử/test cases), `reviewer` (kiểm soát chất lượng).
- **Nút Kết quả (Sink):** `final` — tổng hợp kết quả của toàn bộ quá trình điều phối.
- **Hệ thống liên kết kép:**
  - **Assignment Edges:** Luồng phân công công việc từ Supervisor đến các Specialist.
  - **Dependency Edges:** Luồng phụ thuộc dữ liệu tuần tự và song song giữa các Specialist.

Mục tiêu của thuật toán:
1. Phân tầng thứ tự thực thi rõ ràng từ trái sang phải ($X$ tăng dần theo thời gian và logic phụ thuộc).
2. Tách biệt rõ ràng các bước nối tiếp và các nhánh song song.
3. Không để xảy ra bất kỳ hiện tượng chồng lấn (zero overlap) giữa các thẻ card.
4. Giảm thiểu tối đa số lượng đường nối cắt nhau (crossing minimization).
5. Tự động căn giữa theo phương dọc (vertical centering) để sơ đồ luôn cân đối và trực quan.
6. Hoàn toàn an toàn trước dữ liệu bất thường: tự động phát hiện chu trình (cycle detection) và không bao giờ gây treo trình duyệt.

---

### 2. Chi tiết Thuật toán Phân tầng (Layer Assignment via Kahn's Topological Sort)

Thuật toán thực thi qua các bước toán học chặt chẽ:

#### Bước 1: Khởi tạo Đồ thị và Bán bậc vào (In-Degree)
- Lọc danh sách các cạnh phụ thuộc (`DEPENDENCY` edges) hợp lệ.
- Xây dựng danh sách kề `adj: Map<NodeId, NodeId[]>` và bảng đếm bán bậc vào `inDegree: Map<NodeId, number>`.

#### Bước 2: Thiết lập Phân tầng Cơ sở (Base Layering)
Trong mô hình Multi-Agent có Supervisor, nếu chỉ dựa vào bán bậc vào thuần túy, tất cả các agent không có cạnh phụ thuộc ban đầu sẽ bị xếp chung cột với Supervisor (Layer 0). Điều này làm vỡ cấu trúc chỉ huy.
Do đó:
$$\text{layer}(\text{supervisor}) = 0$$
Đối với tất cả các Specialist Agent được Supervisor phân công:
$$\text{layer}(v) = 1 \quad \forall v \ne \text{supervisor}$$

#### Bước 3: Lan truyền Phân tầng theo Đường đi Dài nhất (Longest-Path Propagation)
Sử dụng hàng đợi Kahn ($Q$) để duyệt đồ thị:
1. Đưa tất cả các node có $\text{inDegree} = 0$ vào hàng đợi $Q$.
2. Với mỗi node $u$ lấy ra từ $Q$, duyệt qua tất cả các node con $v \in \text{adj}(u)$:
   $$\text{layer}(v) = \max(\text{layer}(v), \text{layer}(u) + 1)$$
   $$\text{inDegree}(v) \leftarrow \text{inDegree}(v) - 1$$
   Nếu $\text{inDegree}(v) = 0$, đẩy $v$ vào $Q$.
3. Nếu số lượng node được duyệt qua nhỏ hơn tổng số node, đồ thị chứa chu trình (cycle detected). Hệ thống kích hoạt cờ `graphState.cycleDetected = true` và hiển thị cảnh báo an toàn trên UI, chuyển sang thuật toán fallback an toàn theo mức độ xuất hiện mà không làm gián đoạn hiển thị.

Đối với node `final`:
$$\text{layer}(\text{final}) = \max_{v \ne \text{final}}(\text{layer}(v)) + 1$$

---

### 3. Giảm thiểu Giao cắt (Crossing Minimization: Barycenter Heuristic)

Sau khi phân bổ các node vào từng tầng $L_0, L_1, \dots, L_k$:
- Thứ tự các node trong tầng $L_i$ ảnh hưởng trực tiếp đến số lượng giao cắt của các cạnh nối từ tầng $L_{i-1}$.
- Thuật toán tính trọng tâm (Barycenter) của mỗi node $v \in L_i$ dựa trên vị trí trung bình của các nút tiền nhiệm (predecessors) $u \in L_{i-1}$:
$$\text{barycenter}(v) = \frac{1}{|P(v)|} \sum_{u \in P(v)} \text{order}(u)$$
- Các node trong tầng $L_i$ được sắp xếp lại theo giá trị $\text{barycenter}(v)$ tăng dần. Nếu trọng tâm bằng nhau, giữ nguyên thứ tự định danh xác định (deterministic ordering) để kết quả layout luôn nhất quán 100% qua mọi lần chạy.

---

### 4. Định vị Tọa độ Hình học và Chiều cao Tích lũy Động (Dynamic Cumulative Geometry)

Nhằm triệt tiêu hoàn toàn rủi ro chồng lấn (overlap) khi người dùng mở rộng chi tiết các thẻ agent (expanded mode với $H = 150\text{px}$), thuật toán loại bỏ khoảng cách cố định (fixed row pitch) và áp dụng giải thuật **chiều cao tích lũy động (Dynamic Cumulative Height)**:

- **Kích thước thẻ card:** Chiều rộng chuẩn $W = 245\text{px}$, chiều cao $H = 80\text{px}$ (compact) hoặc $150\text{px}$ (expanded).
- **Khoảng cách tầng theo phương ngang (Layer Gap):** $G_X = 90\text{px}$.
- **Khoảng cách dọc giữa các thẻ (Node Gap):** $G_Y = 24\text{px}$ (compact) hoặc $32\text{px}$ (expanded).
- **Lề an toàn biên:** $\text{Margin}_X = 35\text{px}$, $\text{Margin}_Y = 30\text{px}$.

#### A. Tính Chiều cao Tích lũy từng Tầng:
Với mỗi tầng $L_i$, tổng chiều cao thực tế bao gồm toàn bộ chiều cao các node thành phần cộng khoảng cách cách ly giữa chúng:
$$H(L_i) = \sum_{v \in L_i} H(v) + \max(0, |L_i| - 1) \times G_Y$$

#### B. Xác định Chiều cao Toàn cục và Căn giữa Phương dọc:
$$H_{\max} = \max\left(340, \max_i H(L_i)\right)$$
Độ lệch bắt đầu theo trục dọc cho tầng $L_i$:
$$\text{startY}(L_i) = \text{Margin}_Y + \max\left(0, \frac{H_{\max} - H(L_i)}{2}\right)$$

#### C. Phân bổ Tọa độ Tuần tự không Trùng lặp:
- **Tọa độ X:**
  $$X(L_i) = \text{Margin}_X + i \times (W + G_X)$$
- **Tọa độ Y:** Bắt đầu tại $\text{startY}(L_i)$, mỗi node kế tiếp được đặt tại vị trí đáy của node trước cộng khoảng cách cách ly:
  $$Y(v_0) = \text{startY}(L_i)$$
  $$Y(v_{k+1}) = Y(v_k) + H(v_k) + G_Y$$

#### D. Chứng minh Toán học về Triệt tiêu Chồng lấn (Zero Overlap Proof):
- Khi ở chế độ mở rộng ($H = 150\text{px}, G_Y = 32\text{px}$):
  $$Y(v_{k+1}) - Y(v_k) = 150 + 32 = 182\text{px} > 150\text{px}$$
- Đáy của node $v_k$ tại $Y(v_k) + 150\text{px} < Y(v_{k+1}) = Y(v_k) + 182\text{px}$.
- Luôn tồn tại khoảng đệm an toàn tối thiểu $32\text{px}$ giữa hai thẻ liên tiếp trong cùng một tầng.
- Overlap dọc: **$0.0\text{px}$**.
- Overlap ngang: Khoảng cách giữa các cột là $G_X = 90\text{px} > 0\text{px}$ -> Overlap ngang: **$0.0\text{px}$**.
- Khung nhìn toàn cảnh `fullBox` tự động cập nhật:
  $$\text{viewBox} = [0, 0, \max(630, X_{\max} + W + 35), \max(340, Y_{\max} + H + 30)]$$
  giúp chức năng Fit-to-screen bao quát trọn vẹn 100% diện tích đồ thị trong mọi chế độ hiển thị.

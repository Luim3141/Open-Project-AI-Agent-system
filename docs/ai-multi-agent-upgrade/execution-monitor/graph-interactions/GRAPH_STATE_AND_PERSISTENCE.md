# MÔ THỨC QUẢN LÝ TRẠNG THÁI VÀ LƯU TRỮ CỤC BỘ (STATE & PERSISTENCE)
## TÀI LIỆU KỸ THUẬT: HARDENED GRAPH GEOMETRY PERSISTENCE & SECURITY ISOLATION
**Mã tài liệu:** `EM-GI-04`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** JavaScript Specialist, Security Auditor  
**Phiên bản:** 3.0 (Hardened Release Gate)  

---

### 1. Kiến trúc Quản lý Trạng thái Đồ thị (Graph Client State)

Trạng thái tương tác của sơ đồ điều phối được quản lý tập trung trong đối tượng `graphState` bên trong module `_execution_client.html.erb`:
```javascript
const graphState = {
  mode: 'auto',                        // 'auto' (mặc định) hoặc 'manual' (khi người dùng đã kéo node)
  positions: new Map(),                // Map<NodeId, { x: number, y: number, w: number, h: number }>
  manualOverrides: new Map(),          // Map<NodeId, boolean> ghi nhận các node đã bị di chuyển thủ công
  cycleDetected: false                 // Cờ cảnh báo nếu đồ thị đầu vào có chu trình phụ thuộc bất thường
};
```

#### Quy tắc chuyển đổi trạng thái:
1. **Khởi tạo ban đầu (`Init`):**
   - Khi tải trang, hệ thống kiểm tra `localStorage`.
   - Nếu tìm thấy bản lưu hợp lệ cho Run hiện tại, nạp lại tọa độ và đặt `graphState.mode = saved.mode`.
   - Nếu không có bản lưu, tự động kích hoạt thuật toán Kahn DAG Layout để sắp xếp tối ưu và đặt `graphState.mode = 'auto'`.
2. **Khi Kéo thả Node (`User Drag`):**
   - Ngay khi người dùng nhả chuột (`pointerup`) sau khi kéo $\ge 4\text{px}$, node đó được đánh dấu vào `graphState.manualOverrides.set(nodeId, true)`.
   - `graphState.mode = 'manual'`.
   - Gọi `saveLayout()` để đồng bộ trạng thái hình học xuống bộ nhớ trình duyệt.
3. **Khi Bấm "Tự động sắp xếp" (`#em-auto-layout`):**
   - Xóa bỏ toàn bộ manual overrides.
   - Chuyển `graphState.mode = 'auto'`.
   - Tính toán lại toàn bộ vị trí các tầng theo thuật toán Kahn với chiều cao tích lũy động, căn giữa đối xứng và lưu bản bố cục tự động mới.
4. **Khi Bấm "Đặt lại bố cục" (`#em-reset-layout`):**
   - Xóa bản ghi trong `localStorage` tương ứng với Run hiện tại.
   - Khôi phục lại trạng thái mặc định của hệ thống.

---

### 2. Định dạng Lưu trữ và Khóa Định danh Phân quyền (Hardened Storage Schema)

Để tuân thủ nghiêm ngặt nguyên tắc **Multi-tenant RBAC & Actor Isolation**, khóa lưu trữ không bao giờ dùng tên chung chung mà được cấu trúc phân cấp:
$$\text{StorageKey} = \texttt{qldapm:graph-layout:v1:\{projectId\}:\{actorId\}:\{runId\}}$$

#### Cấu trúc dữ liệu JSON lưu trữ:
```json
{
  "schema_version": 1,
  "run_id": "af64fd85-817c-4e66-874e-fa03aab4c5b7",
  "mode": "manual",
  "positions": {
    "supervisor": { "x": 35, "y": 95 },
    "1": { "x": 370, "y": 95 },
    "2": { "x": 705, "y": 95 },
    "3": { "x": 1040, "y": 95 },
    "4": { "x": 1375, "y": 95 },
    "final": { "x": 1710, "y": 95 }
  }
}
```

#### Các Chốt Chặn An Toàn Hardening:
1. **Kiểm tra Giới hạn Tọa độ Hợp lý (Sane Coordinate Boundaries):**
   - Toàn bộ tọa độ lưu trữ phải nằm trong khoảng hợp lý:
     $$\text{MIN\_COORD} = -5000 \le x, y \le \text{MAX\_COORD} = 50000$$
   - Các giá trị vượt biên, `NaN`, `Infinity`, `-Infinity`, `null`, `undefined` hoặc String đều bị từ chối triệt để.
2. **Khử độc Chiều rộng và Chiều cao (Untrusted Dimensions Sanitization):**
   - Bản lưu client-side **tuyệt đối không tin cậy thuộc tính `w` hoặc `h`**.
   - Chiều rộng luôn được gán cố định $W = 245\text{px}$, chiều cao được tính động theo trạng thái thu gọn/mở rộng $H = 80\text{px}$ (compact) hoặc $150\text{px}$ (expanded).
3. **Đối chiếu Định danh Node Hiện hữu:**
   - Chỉ chấp nhận các Node ID thực sự tồn tại trong `data.nodes`. Mọi Node ID lạ bị loại bỏ.
   - Bản lưu chỉ được chấp nhận khi chứa đầy đủ $100\%$ các node của run hiện tại (`valid.size === data.nodes.length`).
4. **Bảo vệ Ngoại lệ Lưu trữ (Storage Quota & Privacy Exceptions):**
   - Toàn bộ thao tác `localStorage.getItem`, `localStorage.setItem`, `localStorage.removeItem` đều được bọc trong khối `try / catch`.
   - Nếu người dùng bật chế độ ẩn danh (Private Browsing) hoặc bộ nhớ trình duyệt bị đầy (`QuotaExceededError`), ứng dụng ghi nhận ngoại lệ êm ái mà không gây sập giao diện người dùng.
5. **Zero Sensitive Data:**
   - Không lưu trữ prompt, output của LLM, API keys, tokens, session cookies hay thông tin cá nhân trong `localStorage`.

---

### 3. Khả năng Tương thích với Replay Mode và Presentation Mode

1. **Khả năng Miễn nhiễm Bố cục trong Replay Mode (`snapshot()`):**
   - Trong quá trình phát lại lịch sử (`#em-replay-play`, `#em-replay-step`), hàm `snapshot()` chỉ cập nhật các thuộc tính trạng thái CSS (`.em-node-running`, `.em-node-completed`, hiển thị badge thời gian).
   - Hàm `graph()` chỉ khởi tạo layout nếu `layout.size === 0`. Do đó, việc tua tiến hay tua lùi qua 16+ sự kiện timeline **hoàn toàn không làm dịch chuyển vị trí các node đã được người dùng sắp xếp**.
2. **Khả năng Tương tác trong Chế độ Trình diễn (`Presentation Mode`):**
   - Khi bật chế độ trình chiếu (`#em-presentation-toggle`), vùng chứa đồ thị được phóng to toàn màn hình.
   - Tọa độ thế giới SVG được bảo toàn nguyên vẹn nhờ thuật toán `screenToWorld` xử lý chính xác tỷ lệ co giãn mới qua ma trận CTM inverse.
   - Người dùng có thể kéo thả node trực tiếp trong khi trình diễn đồ án trước hội đồng và thoát êm bằng phím `Escape`.

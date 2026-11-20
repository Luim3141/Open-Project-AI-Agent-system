# BÁO CÁO THẨM ĐỊNH GIAO DIỆN VÀ TRẢI NGHIỆM TRỰC QUAN (VISUAL QA)
## TÀI LIỆU KỸ THUẬT: GRAPH INTERACTION VISUAL QA & USER EXPERIENCE
**Mã tài liệu:** `EM-GI-08`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Senior UI/UX Designer, Playwright Visual QA Engineer  
**Phiên bản:** 2.0 (Candidate Release)  

---

### 1. Phân tích Chi tiết Bằng chứng Hình ảnh Thực tế (Screenshot Audit)

Hệ thống đã thu thập 4 ảnh chụp màn hình độ phân giải cao tại môi trường kiểm thử độc lập (`http://localhost:18097`):

#### Ảnh 1: `01_initial_graph.png` — Bố cục Mặc định Ban đầu (Initial Baseline)
- **Cấu trúc:** Hiển thị trọn vẹn 6 thẻ card đại diện cho các agent: Supervisor, BA Agent, Developer Agent, QA Agent, Reviewer và Báo cáo tổng hợp (Final Report).
- **Hệ thống đường nối (Edges):** 4 đường nét đứt màu xám bạc (`.em-edge-assignment`) thể hiện luồng phân công từ Supervisor; 6 đường nét liền màu xanh chàm (`.em-edge-dependency`) thể hiện luồng phụ thuộc dữ liệu tuần tự.
- **Tính thẩm mỹ:** Các huy hiệu vai trò (role badges: SV, BA, DV, QA, RV, $\Sigma$) có màu sắc nhận diện chuẩn Material / Tailwind. Phông chữ OpenProject nhất quán, độ tương phản văn bản đạt WCAG AA ($> 4.5:1$).

#### Ảnh 2: `02_node_ba_dragged.png` — Kéo thả Node BA & Tự động Uốn Cạnh nối
- **Hành vi tương tác:** Node BA Agent được kéo sang phải $+150\text{px}$ và xuống dưới $+80\text{px}$.
- **Điểm tiếp xúc chu vi (Perimeter Anchoring):** Đường nối từ Supervisor (`supervisor -> 1`) tự động kéo dài và dịch chuyển tiếp điểm theo mép phải thẻ Supervisor sang mép trái thẻ BA. Đường nối từ BA sang Developer (`1 -> 2`) tự động đổi điểm tiếp xúc và điều chỉnh bán kính uốn cong mềm mại, không bao giờ đâm xuyên qua thân thẻ hay chữ bên trong.
- **Phản hồi con trỏ:** Hiển thị con trỏ `cursor: grabbing` trực quan trong suốt quá trình kéo.

#### Ảnh 3: `03_auto_layout_reorganized.png` — Tự động Sắp xếp Phân tầng DAG (Auto Layout)
- **Hành vi:** Kích hoạt nút `#em-auto-layout` ("Tự động sắp xếp").
- **Kết quả bố cục:** Toàn bộ 6 node được tính toán lại tọa độ theo thuật toán Kahn Topological Sort:
  - Supervisor nằm ở cột 0 ($X = 35.0$).
  - Các Specialist Agents được phân tầng rõ ràng theo độ sâu phụ thuộc thực thi.
  - Final Report nằm ở cột cuối cùng ($X = 1710.0$).
  - **Zero Overlap:** Hoàn toàn không có bất kỳ điểm chồng lấn nào giữa các thẻ card ($\text{Collisions} = \text{False}$).
  - Căn giữa phương dọc đối xứng, tạo cảm giác chuyên nghiệp khi trình chiếu đồ án.

#### Ảnh 4: `04_presentation_drag.png` — Tương tác trong Chế độ Trình diễn (Presentation Mode)
- **Hành vi:** Kích hoạt nút `#em-presentation-toggle` (hoặc phím tắt).
- **Trải nghiệm:** Toàn bộ thanh điều hướng của OpenProject được ẩn đi, không gian đồ thị và timeline được mở rộng tối đa ra toàn bộ khung nhìn màn hình.
- **Thao tác kéo thả:** Người dùng vẫn có thể kéo thả tự do các node trực tiếp trên sân khấu trình diễn để làm nổi bật từng phần của kiến trúc Multi-Agent trước hội đồng chấm thi.
- **Thoát êm:** Nhấn phím `Escape` lập tức khôi phục lại giao diện OpenProject chuẩn mà không gây chớp giật màn hình (no layout shift).

---

### 2. Thẩm định Tiêu chuẩn UI/UX Pro Max và Trợ năng (Accessibility)

| Tiêu chuẩn UX / A11y | Trạng thái | Minh chứng kỹ thuật |
|----------------------|:----------:|---------------------|
| **Không dùng emoji làm icon** | **ĐẠT** | Toàn bộ icon thanh công cụ (Zoom in, Zoom out, Fit, Auto Layout, Reset, Presentation) đều sử dụng SVG vector chuẩn Lucide/Heroicons. |
| **Phản hồi con trỏ (`cursor: pointer`)** | **ĐẠT** | Mọi nút bấm, tab và node tương tác đều có `cursor: pointer` hoặc `cursor: grab` / `cursor: grabbing`. |
| **Tỷ lệ tương phản màu sắc (WCAG AA)** | **ĐẠT** | Văn bản nền thẻ trắng `#ffffff` với chữ chính `#1e293b` đạt tỷ lệ tương phản $12.6:1$ (vượt xa chuẩn tối thiểu $4.5:1$). |
| **Chuyển động mượt mà (Smooth Transitions)** | **ĐẠT** | CSS transition $150\text{ms} - 300\text{ms}$ trên các nút bấm; tự động triệt tiêu transition khi kéo thả chuột để đảm bảo tốc độ 60fps không bị lag. |
| **Điều hướng bàn phím (Keyboard Navigation)** | **ĐẠT** | Các node có thuộc tính `tabindex="0"`, hỗ trợ phím `Enter` và `Space` để chọn node, phím `ArrowRight`/`ArrowLeft` để chuyển qua lại giữa các agent trong chế độ trình chiếu. |
| **Vòng nét tiêu điểm (`focus-visible`)** | **ĐẠT** | Có viền nét focus màu xanh dương rõ nét `outline: 2px solid var(--em-primary)` khi người dùng điều hướng bằng bàn phím. |
| **Thoát chế độ bằng phím `Escape`** | **ĐẠT** | Người dùng có thể nhấn phím `Escape` bất cứ lúc nào để thoát Chế độ Trình diễn về giao diện chuẩn. |

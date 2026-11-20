# BÁO CÁO ĐỐI CHIẾU SOURCE - IMAGE - RUNTIME PARITY
## TÀI LIỆU KỸ THUẬT: HARDENED GRAPH CANDIDATE ARTIFACT VERIFICATION
**Mã tài liệu:** `EM-GI-10`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Release Engineer, Senior DevOps Engineer  
**Phiên bản:** 3.0 (Hardened Candidate Release)  

---

### 1. Bảng Đối Chiếu Ma Trận Hiện Vật (Artifact Parity Matrix)

| Thành phần | Hiện vật / Chỉ số | Giá trị xác minh thực tế | Trạng thái |
|------------|-------------------|--------------------------|:----------:|
| **Candidate Tag** | Docker Repository:Tag | `qldapm-graph-candidate:final` | **VERIFIED** |
| **Candidate Image ID** | Full SHA256 Hash | `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` | **VERIFIED** |
| **Short Image ID** | First 12 Chars | `79a90c208372` | **VERIFIED** |
| **Parent Base Image** | Previous Approved Core Image | `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b` | **VERIFIED** |
| **Overlay Source Hash** | Label `org.qldapm.source.sha256` | `ef0a5cb3ccc32528119e3a689a8e0175611ff6d614691f9ab2428777af7f075a` | **VERIFIED** |
| **Deployment Label** | Label `org.qldapm.deployment` | `execution-monitor-candidate` | **VERIFIED** |
| **Daily Report Scope** | Label `org.qldapm.report` | `actor-daily-read-only` | **VERIFIED** |
| **Gateway Image** | Full SHA256 (Preserved) | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` | **UNCHANGED** |
| **OpenProject Base** | OpenProject Release | `v17.9.1 Community Edition` | **VERIFIED** |

---

### 2. Danh mục Tệp Nguồn Thay đổi (Source Delta Inventory)

Duy nhất 3 tệp Rails View Templates được chỉnh sửa và 1 tệp giữ nguyên trong cấu trúc Overlay (`openproject/ai/core/overlay/app/views/qldapm_ai/`):

1. **`execution.html.erb`:**
   - **Bổ sung:** Thêm nút `#em-auto-layout` ("Tự động sắp xếp") và `#em-reset-layout` ("Đặt lại bố cục") vào thanh công cụ `.em-toolbar`.
   - **Tích hợp:** Giữ nguyên toàn bộ cấu trúc breadcrumb, hero header, agent detail, timeline, replay và final report sections.
2. **`_execution_style.html.erb`:**
   - **Bổ sung:** Kiểu dáng con trỏ `.em-node { cursor: grab; }` và `.em-node.em-dragging { cursor: grabbing; ... }`.
   - **Hiệu năng:** Khai báo quy tắc `.em-edge.em-edge-dragging { transition: none !important; }` để triệt tiêu độ trễ khi kéo chuột ở tốc độ 60fps.
   - **Bảo toàn:** Giữ nguyên các biến giao diện Light Theme của OpenProject và mã màu các vai trò.
3. **`_execution_client.html.erb` (Hardened Geometry & Persistence):**
   - **Khởi tạo trạng thái:** Quản lý `graphState = { mode: 'auto', manualOverrides: new Map(), cycleDetected: false }`.
   - **Giải thuật tọa độ:** Triển khai `screenToWorld` qua ma trận CTM inverse, thích ứng hoàn hảo với các mức zoom (50% đến 200%).
   - **Giải thuật định tuyến:** Triển khai `getEdgePath` với cơ chế tính điểm tiếp xúc chu vi (Perimeter Anchoring) và đường cong bậc ba Bezier.
   - **Giải thuật phân tầng:** Triển khai `computeAutoLayout` dựa trên thuật toán Kahn Topological Sort và Barycenter crossing reduction.
   - **Hình học tích lũy động:** Tính toán chiều cao tầng theo tổng chiều cao thực tế ($H = 80\text{px}$ compact, $150\text{px}$ expanded, vertical gap $G_Y = 24/32\text{px}$), triệt tiêu hoàn toàn rủi ro chồng lấn node.
   - **Bảo vệ lưu trữ cục bộ:** Triển khai `saveLayout`, `loadSavedLayout` với kiểm tra biên tọa độ `[-5000, 50000]`, loại bỏ thuộc tính kích thước client không đáng tin cậy, khử độc `NaN`/chuỗi, và bắt ngoại lệ `QuotaExceededError` an toàn.
4. **`executions.html.erb` (Preserved):**
   - Giữ nguyên vẹn bảng lịch sử compact table và bộ lọc đa tiêu chí đã được nghiệm thu trước đó.

---

### 3. Quy trình Đóng gói Docker (Build Verification)

Hiện vật candidate được đóng gói qua `openproject/ai/automation/ExecutionMonitorCore.Dockerfile`:
```dockerfile
ARG CORE_IMAGE
FROM ${CORE_IMAGE}
ARG SOURCE_SHA256
COPY --chown=app:app core/overlay/ /app/
LABEL org.qldapm.source.sha256=${SOURCE_SHA256} org.qldapm.deployment="execution-monitor-candidate"
```
- Không cài thêm gem Ruby mới.
- Không sửa schema database.
- Không thay đổi assets tĩnh của OpenProject Core (Webpack/Angular bundles).
- Giảm thiểu kích thước build xuống mức tối ưu nhất (chỉ nạp các file view template dạng text).

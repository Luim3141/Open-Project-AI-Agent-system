# BÁO CÁO KIỂM THỬ GIAO DIỆN & TRẢI NGHIỆM (VISUAL QA)
## EXECUTION MONITOR UI/UX REFINEMENT

- **Môi trường kiểm thử:** Isolated Qualification Clone (`http://localhost:18097`)
- **Trình duyệt kiểm thử:** Playwright Chromium / Microsoft Edge Channel (Headless & Full Rendering)
- **Đối tượng:** Candidate Core Image `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b`

---

### 1. Ma trận kiểm thử kích thước màn hình (Responsive Viewports)

| Độ phân giải | Loại thiết bị | Tràn ngang (Overflow) | Trực quan Graph & Detail | Đánh giá |
|---|---|---|---|---|
| **1920 × 1080** | Desktop Màn hình rộng | `scrollWidth <= innerWidth` (PASS) | Grid 2 cột tối ưu; Sơ đồ hiển thị đầy đủ 6 node; Agent detail dạng tab dễ đọc | **PASS** |
| **1440 × 900** | Desktop Tiêu chuẩn / Laptop Pro | `scrollWidth <= innerWidth` (PASS) | Không bị đẩy sơ đồ xuống dưới fold; Typography cân đối; Metric cards 4 cột gọn | **PASS** |
| **1366 × 768** | Laptop Phổ thông | `scrollWidth <= innerWidth` (PASS) | Bảng history và sơ đồ co giãn tự động; không chồng chéo nút bấm | **PASS** |
| **768 × 1024** | Tablet (iPad dọc) | `scrollWidth <= innerWidth` (PASS) | Grid tự chuyển sang 1 cột xếp chồng (Graph trên, Detail dưới); Bảng dự phòng tự mở | **PASS** |
| **375 × 812** | Mobile (iPhone X / 12 / 13) | `scrollWidth <= innerWidth` (PASS) | Metric cards chuyển thành cột đơn; breadcrumbs tự ngắt dòng gọn; không vỡ chữ | **PASS** |

---

### 2. Khắc phục triệt để lỗi Theme Mismatch (Navy vs Light)

- **Trước khi sửa:** Do media query `@media (prefers-color-scheme: dark)` hardcode biến màu tối, bất cứ người dùng nào có hệ điều hành bật Dark Mode khi truy cập OpenProject Light Theme đều thấy Execution Monitor bị biến thành một khối đen navy `#172334` lệch tông hoàn toàn so với thanh công cụ và sidebar của OpenProject.
- **Sau khi sửa:** 
  - Toàn bộ biến màu của `.execution-monitor` được định nghĩa kế thừa từ biến Primer/OpenProject (`--bgColor-default`, `--borderColor-default`, `--fgColor-default`).
  - Màu tối chỉ kích hoạt khi OpenProject thực sự chuyển sang Dark Theme thông qua thuộc tính `html[data-color-mode="dark"]`, `[data-dark-theme="dark"]`, hoặc `body.theme-dark`.
  - **Kết quả đo kiểm:** Trong môi trường giả lập `color_scheme='dark'` trên trình duyệt, thẻ card và nền vẫn giữ màu trắng/sáng đồng bộ (`rgb(255, 255, 255)`), loại bỏ 100% hiện tượng xung đột màu navy.

---

### 3. Đánh giá chi tiết từng thành phần giao diện

#### 3.1. Trang Execution History
- **Thanh tìm kiếm & Lọc:** Input tìm kiếm, Select trạng thái, Select thứ tự sắp xếp và Nút lọc được chuẩn hóa chiều cao 38px, font chữ đồng bộ, có hiệu ứng hover mượt mà.
- **Bảng dữ liệu:** 
  - Chữ trạng thái (`COMPLETED`, `FAILED`, `RUNNING`) được đặt trong pill badge có thuộc tính `white-space: nowrap !important`, khắc phục dứt điểm lỗi rớt chữ thành hai dòng như trước đây (`COMPLETE` / `D`).
  - Cột Agent hiển thị các tag bo tròn chuyên nghiệp cho từng role (`BA`, `DEV`, `QA`, `REVIEWER`).
  - Nút bấm `Xem quá trình AI xử lý →` có mũi tên SVG thanh thoát, kèm mã Run ID dạng monospace phụ đề bên dưới.

#### 3.2. Sơ đồ điều phối Multi-Agent (Execution Graph)
- **Node Cards:** Được bo góc mềm mại `rx="12"`, đổ bóng nhẹ, phân biệt bằng avatar hình tròn mang màu đại diện của từng vai trò (`SV` - Indigo, `BA` - Sky Blue, `DEV` - Violet, `QA` - Emerald Green, `RV` - Amber, `Σ` - Rose).
- **Đường nối (Edges):**
  - Đường nét đứt màu xám biểu diễn luồng Supervisor giao việc (`ASSIGNMENT`).
  - Đường nét liền màu xanh biểu thị luồng phụ thuộc dữ liệu (`DEPENDENCY`).
  - Đường phát sáng xanh đậm nổi bật luồng thực thi của node đang được người dùng chọn.
- **Legend & Toolbar:** Có chú thích trực quan ngay dưới sơ đồ; thanh công cụ gồm Phóng to, Thu nhỏ, Vừa màn hình, Thu gọn node và nút kích hoạt Chế độ Trình chiếu.

#### 3.3. Bảng Chi tiết Agent (Agent Detail Panel)
- **Cấu trúc Tab hiện đại:** Thay thế danh sách dọc dài 18 trường bằng hệ thống Tab:
  1. **Thông tin chính:** Tóm tắt vai trò, trạng thái, phụ thuộc, calls, token, thời gian xử lý và mô hình.
  2. **Kết quả xử lý:** Khối hiển thị văn bản kết quả chuyên môn có định dạng font dễ đọc, nguồn tham chiếu Work Package dạng chip bấm được.
  3. **Tất cả thông số:** Lưu giữ toàn bộ 18 trường kỹ thuật chi tiết để phục vụ kiểm thử và tra cứu chuyên sâu mà không làm kéo dài màn hình chính.

#### 3.4. Timeline & Replay
- Đường timeline có các điểm nút trạng thái (xanh lá cho hoàn thành, xanh dương cho đang xử lý, đỏ cho thất bại).
- Thanh phát lại (Replay Controller) được thiết kế như trình phát media thu nhỏ với nút Play/Pause, thanh kéo sự kiện và bộ đếm tiến trình `X / Y`.

#### 3.5. Tổng hợp báo cáo cuối cùng (Final Report)
- Tự động phân tách các khối nội dung chuyên môn của **BA Agent**, **Developer Agent**, **QA Agent**, và **Reviewer** thành các card độc lập có tiêu đề rõ ràng.
- Cung cấp nút chuyển đổi sang chế độ xem "Nội dung nguyên bản" để phục vụ việc đối chiếu dữ liệu gốc.
- Dữ liệu hoàn toàn được escape an toàn bằng `textContent`, vượt qua kiểm tra chống tấn công XSS.

#### 3.6. Chế độ Trình chiếu (Presentation Mode)
- Nút `Chế độ trình chiếu` cho phép phóng to sơ đồ ra toàn màn hình, ẩn các thành phần thừa, tối ưu hóa không gian hiển thị khi thuyết trình trước hội đồng chấm đồ án.
- Hỗ trợ phím tắt `Escape` để thoát nhanh và phím mũi tên `ArrowRight` / `ArrowLeft` để chuyển qua lại giữa các Agent.

---

### 4. Tiêu chuẩn Tiếp cận & Khả dụng (Accessibility - WCAG AA)

- [x] **Độ tương phản chữ (Text Contrast):** Đạt tối thiểu 4.5:1 đối với văn bản thông thường và 3:1 đối với tiêu đề lớn.
- [x] **Không dùng Emoji làm icon:** Toàn bộ biểu tượng đều là SVG hoặc ký tự hình học UTF-8 chuẩn mực.
- [x] **Vùng bấm khả dụng:** Tất cả các nút bấm, select, và link đều có `min-height` từ 36px đến 44px, con trỏ `cursor: pointer`.
- [x] **Điều hướng bàn phím:** Hiển thị viền focus rõ ràng (`:focus-visible`) với outline 2px màu xanh primary.
- [x] **Hỗ trợ Screen Reader:** Cung cấp bảng dữ liệu có thể mở rộng (`<details id="em-table-view">`) thay thế cho người dùng khiếm thị không tương tác được với canvas SVG.

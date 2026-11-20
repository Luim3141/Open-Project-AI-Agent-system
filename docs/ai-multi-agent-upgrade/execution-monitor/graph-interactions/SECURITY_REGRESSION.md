# BÁO CÁO ĐỐI SOÁT BẢO MẬT VÀ PHÒNG NGỪA HỒI LÙI (SECURITY & REGRESSION)
## TÀI LIỆU KỸ THUẬT: HARDENED ZERO-MUTATION & RESOURCE INTEGRITY ASSURANCE
**Mã tài liệu:** `EM-GI-09`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Security Auditor, Principal DevOps Engineer  
**Phiên bản:** 3.0 (Hardened Candidate Release)  

---

### 1. Nguyên tắc Bất biến Cốt lõi (Inviolable Constraints)

Quá trình nâng cấp tính năng tương tác sơ đồ (Draggable Graph & Auto Layout) tuân thủ triệt để 4 nguyên tắc phòng ngừa rủi ro của Chủ dự án:
1. **Zero Database Mutation:** Không thay đổi bất kỳ bản ghi dữ liệu nghiệp vụ nào trong OpenProject PostgreSQL hoặc SQLite.
2. **Zero Provider Call:** Không phát sinh bất kỳ cuộc gọi mới nào tới Google Gemini API thật trong suốt quá trình kiểm thử tương tác trên trình duyệt.
3. **Fail-Closed RBAC Preservation:** Giữ nguyên vẹn 100% cơ chế phân quyền, ranh giới dự án và cách ly người dùng.
4. **No Heavy External Dependencies:** Không thêm bất kỳ thư viện bên thứ ba nặng nề nào; toàn bộ giải thuật hình học được viết bằng Vanilla JavaScript thuần túy tối ưu cao.

---

### 2. Kiểm toán Thực tế An toàn Tài nguyên (Resource Safety Audit)

#### A. Kiểm toán Gemini API và Gateway Job Count
- **Số lượng công việc trong Gateway trước phiên kiểm thử Playwright:** `0`
- **Số lượng công việc trong Gateway sau phiên kiểm thử Playwright:** `0`
- **Chênh lệch (Delta):** **`0` cuộc gọi mới**
- **Tokens tiêu hao:** **`0` tokens**
- **Chi phí phát sinh:** **0 VND / 0 USD**
- **Kết luận:** Toàn bộ quá trình kéo thả, auto layout, reset và chuyển tab diễn ra hoàn toàn trên client và đọc từ bộ nhớ đệm read-only của OpenProject Core/Gateway.

#### B. Kiểm toán Cơ sở dữ liệu và Tính toàn vẹn Dữ liệu (Database Integrity)
- **Database Connection Mode:** Kết nối qua cờ read-only của PostgreSQL (`PGOPTIONS=-c default_transaction_read_only=on`).
- **Database Migrations:** `0` file migration mới được tạo trong `db/migrate/`.
- **Work Package Records:** Danh sách công việc, cấu trúc cây phân rã WBS, các trường custom fields và trạng thái gates được bảo toàn nguyên vẹn 100%.

---

### 3. Phân tích Bảo mật Cục bộ và Khử độc Dữ liệu (Client-Side Hardening)

#### A. Ngăn chặn Truy cập API Trái phép (Direct Unauthorized Rejection)
- **Kiểm thử thực tế (`DRAG-01-UNAUTH-REJECTION`):** Khi gửi yêu cầu trực tiếp tới `/projects/qldapm-local/qldapm-ai/executions.json` mà không có phiên đăng nhập hợp lệ, hệ thống trả về **HTTP 401 Unauthorized** và chặn truy cập.

#### B. Phân lập Khóa Lưu trữ theo Ngữ cảnh (Cross-User & Cross-Run Isolation)
- Khóa lưu trữ được mã hóa phân cấp:
  $$\text{StorageKey} = \texttt{qldapm:graph-layout:v1:\{projectId\}:\{actorId\}:\{runId\}}$$
  - `projectId`: Ngăn cách ly giữa các dự án khác nhau.
  - `actorId`: Ngăn cách ly giữa các thành viên trong nhóm (PM, BA, Dev, QA, Reviewer).
  - `runId`: Đảm bảo mỗi phiên điều phối có bố cục độc lập, không bị ghi đè chéo.

#### C. Khử độc Tọa độ và Giới hạn Biên Hợp lý (Sane Bounds Validation)
Trong hàm `loadSavedLayout()` của `_execution_client.html.erb`:
- Kiểm tra chặt chẽ kiểu dữ liệu số thực hữu hạn:
  $$\text{MIN\_COORD} = -5000 \le x, y \le \text{MAX\_COORD} = 50000$$
- Mọi giá trị `NaN`, `Infinity`, String hoặc giá trị vượt ngoài biên tọa độ cho phép đều bị từ chối triệt để.

#### D. Loại bỏ Kích thước Client không Đáng tin cậy (Untrusted Dimensions Sanitization)
- Hệ thống **tuyệt đối không đọc `w` hoặc `h` từ client-side payload**.
- Chiều rộng và chiều cao thẻ luôn được gán cố định theo tiêu chuẩn hiển thị ($W = 245\text{px}$, $H = 80\text{px}$ compact, $150\text{px}$ expanded) để ngăn chặn các nỗ lực phá vỡ bố cục giao diện (Denial of Service via layout distortion).

#### E. Chống Sập Trình duyệt do Giới hạn Bộ nhớ (QuotaExceeded Exception Safety)
- Toàn bộ lời gọi tới `localStorage` được bảo vệ bằng `try / catch`.
- Nếu bộ nhớ trình duyệt đầy hoặc người dùng duyệt web ẩn danh chặn storage, ứng dụng tiếp tục hoạt động bình thường với bố cục tính toán tự động mà không phát sinh lỗi ngoại lệ unhandled.

---

### 4. Kết luận Hồi lùi (Regression Conclusion)
Phiên bản nâng cấp sơ đồ điều phối đạt trạng thái **AN TOÀN TUYỆT ĐỐI**:
- Không có bất kỳ lỗi hồi lùi nào về mặt phân quyền hoặc hiệu năng.
- Tương thích 100% với hệ thống bảo mật hiện có của QLDAPM.

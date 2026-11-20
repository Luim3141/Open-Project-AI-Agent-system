# BỘ TÀI LIỆU KIỂM THỬ NGHIỆM THU NGƯỜI DÙNG TOÀN DIỆN (HUMAN UAT PLAYBOOK)
## Hướng Dẫn Thực Nghiệm 14 Phân Hệ Chức Năng, Tiêu Chí Kiểm Chứng & Bảng Đánh Giá Dành Cho Project Owner

**Hệ thống:** QLDAPM MAIN — Trung Tâm Điều Hành Kỹ Sư Tác Nhân AI (AI Command Center)  
**Địa chỉ truy cập chính:** `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`  
**Đối tượng thực hiện:** Project Owner / Principal Stakeholder (Mạc Đăng Hiệp)  
**Nguyên tắc nghiệm thu:** Chỉ đánh giá dựa trên phản hồi thực tế quan sát được trên trình duyệt, trạng thái cơ sở dữ liệu và mã nguồn thật. Không chấp nhận ảnh chụp giả lập.

---

## BẢNG TỔNG QUAN 14 PHÂN HỆ NGHIỆM THU (UAT MATRIX)

| STT | Phân hệ / Nhóm chức năng | Mục tiêu kiểm chứng | Trạng thái kỹ thuật | Kết quả Owner đánh giá |
| :---: | :--- | :--- | :---: | :---: |
| **01** | Phân quyền & Kiểm soát truy cập (RBAC) | Chỉ tài khoản có vai trò PM/AI_SYSTEM_OWNER được điều hành; từ chối người dùng nặc danh | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **02** | Trung tâm Chỉ huy (Mission Control & KPIs) | Hiển thị chính xác tiến độ 5/5 Units, Quota Zero Cost, Uptime worker và chỉ số tích lũy | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **03** | Bộ điều khiển Vận hành Thời gian thực | Các nút RUN ONCE, AUTO, PAUSE, RESUME, CANCEL phản hồi rõ ràng, có thông báo giải thích | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **04** | Quản lý Backlog & AI Work Intake | Lọc tìm kiếm công việc tức thời; Form tiếp nhận yêu cầu mới kích hoạt PM/BA thành công | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **05** | Trung tâm Thực thi (Execution Center) | Danh sách lượt chạy hiển thị đầy đủ, có cột "Thời điểm chạy" định dạng chuẩn `dd/MM/yyyy HH:mm:ss` | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **06** | Giám sát Chi tiết (Run Inspector Modal) | Không bị treo LOADING; hiển thị đúng State; sơ đồ DAG trực quan; Diff mã nguồn; Log QA thật | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **07** | Quy trình Phát triển 8 Giai đoạn (AI Pipeline) | Trực quan hóa tiến trình từ Intake → Spec → Dev → Review → QA → GitHub → Deploy | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **08** | Lực lượng Tác nhân (Agent Workforce) | 6 Tác nhân chuyên trách; hiển thị đúng mô hình `gemini-3.5-flash-lite` và runtime OpenClaw | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **09** | Quản lý Kho lưu trữ & Bàn giao GitHub | Bảng PR phân định đúng `MERGED TO MAIN` (PR #1), `MERGED TO BRANCH` (PR #2), `OPEN` (PR #3–#5) | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **10** | Đối soát & Đồng bộ 2 Chiều (GitHub Sync) | Nút "Đồng bộ GitHub" nạp dữ liệu PR nhanh (<2s nhờ cache); không làm đơ Puma server | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **11** | Hệ thống Báo cáo Tự động (Reporting System) | Nút tạo báo cáo tức thời; Modal đọc báo cáo hiển thị toàn bộ nội dung phân tích Markdown | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **12** | Cơ sở Tri thức & Second Brain RAG | Tìm kiếm tài liệu nghiệp vụ; cơ chế nạp chỉ mục và thử lại có giới hạn (Bounded retry) | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **13** | Tích hợp Hệ thống (n8n & OpenClaw WSL2) | 16 Workflows n8n đang ACTIVE; OpenClaw Gateway lắng nghe tại cổng 18789 ổn định | **READY FOR UAT** | [ ] PASS  [ ] FAIL |
| **14** | An toàn, Bảo toàn Dữ liệu & Chi phí $0.00 | Dự án Project 5 nguyên vẹn 341 WPs; Không tốn chi phí API Gemini (Zero Billing Verified) | **READY FOR UAT** | [ ] PASS  [ ] FAIL |

---

## HƯỚNG DẪN CHI TIẾT TỪNG PHÂN HỆ KIỂM THỬ

### Phân hệ 01: Phân quyền & Kiểm soát Truy cập (RBAC)
- **Thao tác 1.1:** Đăng nhập tài khoản Quản trị viên / PM vào OpenProject. Mở đường dẫn:  
  `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`
  - *Kỳ vọng:* Giao diện Command Center mở ra đầy đủ với thanh công cụ điều hành.
- **Thao tác 1.2:** Mở cửa sổ ẩn danh (Incognito) hoặc chưa đăng nhập, truy cập cùng URL trên.
  - *Kỳ vọng:* Hệ thống chuyển hướng yêu cầu đăng nhập hoặc phản hồi HTTP 401/403, từ chối tuyệt đối quyền điều khiển của người dùng nặc danh.

### Phân hệ 02: Trung tâm Chỉ huy & KPI Cards
- **Thao tác 2.1:** Quan sát 4 thẻ KPI đầu trang:
  - Thẻ 1: **Tiến độ Dự án Demo:** Hiển thị 5/5 Units hoàn thành (100%).
  - Thẻ 2: **Chế độ Vận hành:** Trạng thái `OFF` hoặc `RUN_ONCE` có nhãn giải thích rõ ràng.
  - Thẻ 3: **Mô hình Trí tuệ Nhân tạo:** Ghi nhận `gemini-3.5-flash-lite (Free Tier · $0.00)`.
  - Thẻ 4: **Chi phí Vận hành:** `$0.00 / Free Tier Quota`.

### Phân hệ 03: Bộ Điều khiển Vận hành Thời gian thực
- **Thao tác 3.1 (RUN ONCE):** Nhấn nút **Chạy Đơn Lẻ (Run Once)** khi 5/5 Units đã hoàn tất.
  - *Kỳ vọng:* Xuất hiện Toast thông báo màu xanh/vàng với lời giải thích minh bạch:  
    `Toàn bộ 5/5 Backlog units đã hoàn tất bàn giao. Để chạy thêm, vui lòng tạo thêm công việc mới qua Work Intake.` (Không gây lỗi 403 hoặc crash).
- **Thao tác 3.2 (BẬT AUTO):** Nhấn nút **Bật Chế độ Tự Động (Auto)**.
  - *Kỳ vọng:* Hệ thống thông báo rõ ràng rằng do 5/5 unit đã hoàn tất nên hệ thống tự động ngắt an toàn (OFF) để bảo vệ tài nguyên, và hướng dẫn giao thêm việc.

### Phân hệ 04: Quản lý Backlog & AI Work Intake
- **Thao tác 4.1 (Lọc tìm kiếm):** Tại Tab **Backlog & Tasks**, nhập từ khóa `SQLite` hoặc `health` vào ô tìm kiếm nhanh.
  - *Kỳ vọng:* Bảng công việc tự động lọc các dòng tương ứng ngay tức thì.
- **Thao tác 4.2 (Giao việc mới):** Sao chép prompt từ file `DEMO_PROJECT_CURRENT_PROGRESS.md` dán vào ô **AI Work Intake** và nhấn **Giao việc mới cho AI**.
  - *Kỳ vọng:* Toast xanh xác nhận thành công. Một Work Package mới được ghi nhận vào OpenProject.

### Phân hệ 05: Trung tâm Thực thi & Chuẩn hóa Thời gian
- **Thao tác 5.1:** Mở Tab **Execution Center**.
- **Thao tác 5.2:** Kiểm tra cột **Thời điểm chạy**:
  - *Kỳ vọng:* Tất cả các dòng hiển thị ngày giờ chuẩn Việt Nam `dd/MM/yyyy HH:mm:ss` (ví dụ: `31/10/2026 14:07:16`).
  - Khi rê chuột vào thời gian, tooltip hiển thị định dạng chuẩn quốc tế ISO 8601 UTC.
  - Các giá trị trống hoặc chưa có dữ liệu hiển thị rõ: `Chưa có dữ liệu`.

### Phân hệ 06: Giám sát Chi tiết (Run Inspector Modal)
- **Thao tác 6.1:** Tại hàng của bất kỳ Run ID nào (ví dụ: `b1cca031-81f5-4df1-870b-cbeb23d51e66`), nhấn nút **Chi tiết** hoặc mã Run ID màu xanh.
  - *Kỳ vọng:*
    1. Modal mở ra ngay tức khắc.
    2. Huy hiệu trạng thái chuyển đổi chính xác từ đang nạp sang trạng thái thật (`FAILED`, `COMPLETED`, v.v.), **tuyệt đối không bị treo chữ LOADING... vô hạn**.
    3. Thẻ **Tokens (Lượt chạy này)** ghi nhận số token của riêng run này (ví dụ: `5,643`).
    4. Sơ đồ **DAG** vẽ trực quan các bước Supervisor → Dev → Reviewer → QA.
    5. Chuyển sang Tab **Dòng sự kiện (Timeline)**: Các sự kiện hiển thị thời điểm đầy đủ `dd/MM/yyyy HH:mm:ss`.
    6. Chuyển sang Tab **Mã nguồn & Diff**: Hiển thị file đã thay đổi hoặc output kỹ thuật.
    7. Chuyển sang Tab **Bằng chứng QA & Test**: Hiển thị log kiểm thử Pytest thật hoặc chi tiết lỗi nguyên nhân nếu FAILED.

### Phân hệ 07 & 08: AI Pipeline & Agent Workforce
- **Thao tác 7.1:** Mở Tab **AI Pipeline (8 Stages)**: Quan sát sơ đồ 8 giai đoạn kỹ thuật trực quan.
- **Thao tác 8.1:** Mở Tab **Agent Workforce**: Quan sát thông tin 6 Agent (Supervisor, PM, BA, Dev, Reviewer, QA) với cấu hình mô hình `gemini-3.5-flash-lite` và phân loại runtime chính xác.

### Phân hệ 09 & 10: GitHub & Delivery Stack
- **Thao tác 9.1:** Mở Tab **GitHub & Delivery**.
- **Thao tác 9.2:** Kiểm tra bảng Pull Requests:
  - **PR #1:** Hiển thị nhãn xanh lá **MERGED TO MAIN** kèm thời gian merge chính xác.
  - **PR #2:** Hiển thị nhãn tím **MERGED TO BRANCH** kèm thời gian merge.
  - **PR #3, #4, #5:** Hiển thị nhãn xanh **OPEN** và mục tiêu **UNMERGED / FEATURE_STACK**.
- **Thao tác 10.1:** Nhấn nút **Đồng bộ GitHub (Reconcile PRs)**.
  - *Kỳ vọng:* Nạp dữ liệu trong vòng 1-2 giây, không gây treo giao diện hoặc nghẽn Puma server.

### Phân hệ 11: Báo cáo & Phân tích (Reports & Analytics)
- **Thao tác 11.1:** Mở Tab **Reports & Analytics**.
- **Thao tác 11.2:** Nhấn nút **Tạo báo cáo nhanh (Snapshot)**.
  - *Kỳ vọng:* Một báo cáo mới được sinh ra và đưa vào danh sách.
- **Thao tác 11.3:** Nhấn nút **Đọc báo cáo** (biểu tượng con mắt) tại bất kỳ báo cáo nào.
  - *Kỳ vọng:* Modal Report Reader mở ra, hiển thị đầy đủ tiêu đề, thời gian tạo tiếng Việt, và toàn bộ nội dung phân tích Markdown chuyên sâu (không bị trống nội dung).

### Phân hệ 12: Cơ sở Tri thức & Second Brain
- **Thao tác 12.1:** Mở Tab **Knowledge / RAG**.
- **Thao tác 12.2:** Nhập từ khóa tìm kiếm (ví dụ: `architecture`, `quy trình`, `API`).
  - *Kỳ vọng:* Hiển thị các đoạn trích dẫn tri thức kèm điểm tương đồng (Relevance score).

### Phân hệ 13: Tích hợp n8n & OpenClaw Runtime
- **Thao tác 13.1:** Chạy lệnh kiểm tra n8n từ PowerShell:
  `openproject\ai\.venv\Scripts\python.exe tools\audit_n8n_workflows.py`
  - *Kỳ vọng:* 16/16 Workflows hiển thị trạng thái `[ACTIVE]`.
- **Thao tác 13.2:** Kiểm tra OpenClaw Gateway từ PowerShell:
  `curl.exe -s -I http://127.0.0.1:18789`
  - *Kỳ vọng:* Trả về `HTTP/1.1 200 OK`.

### Phân hệ 14: An toàn Dữ liệu & Bảo toàn Project 5
- **Thao tác 14.1:** Kiểm tra số lượng Work Package của Project 5:
  `docker exec qldapm-openproject-db-1 psql -U postgres -d openproject -t -c "SELECT count(*) FROM work_packages WHERE project_id=5;"`
  - *Kỳ vọng:* Trả về chính xác **341** Work Packages, lock_version tối đa là **4**, 0 thao tác ghi vào Project 5.
- **Thao tác 14.2:** Xác minh chi phí API:
  - *Kỳ vọng:* Toàn bộ các cuộc gọi tác nhân AI sử dụng Gemini Free Tier, chi phí phát sinh là **$0.00**.

---

## BIÊN BẢN KÝ DUYỆT NGHIỆM THU (SIGN-OFF)

- **Người thực hiện kiểm thử:** Mạc Đăng Hiệp (Project Owner)
- **Ngày kiểm thử:** ..... / 10 / 2026
- **Kết luận:**  
  [ ] **CHẤP THUẬN NGHIỆM THU (ACCEPTED)** — Toàn bộ 14 phân hệ đạt yêu cầu thực tế.  
  [ ] **YÊU CẦU ĐIỀU CHỈNH (CHANGES REQUESTED)** — Ghi chú chi tiết các điểm cần hoàn thiện:
  ...................................................................................................................................................

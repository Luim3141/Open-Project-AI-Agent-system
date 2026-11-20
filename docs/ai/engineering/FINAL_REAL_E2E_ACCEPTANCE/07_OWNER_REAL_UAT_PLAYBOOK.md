# SỔ TAY KIỂM THỬ CHẤP NHẬN DÀNH CHO PROJECT OWNER (REAL HUMAN UAT PLAYBOOK)

> **Tài liệu:** `07_OWNER_REAL_UAT_PLAYBOOK.md`  
> **Dành cho:** Project Owner trực tiếp thao tác trên trình duyệt web thực tế  
> **Cam kết:** 100% bằng chứng quan sát được bằng mắt, loại bỏ hoàn toàn false-positive.

---

## 1. BƯỚC 1: TRUY CẬP TRUNG TÂM ĐIỀU HÀNH AI COMMAND CENTER

1. Mở trình duyệt (Chrome, Edge hoặc Firefox).
2. Truy cập đường dẫn:
   ```text
   http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern
   ```
3. Đăng nhập tài khoản quản trị (nếu được yêu cầu).
4. **Tiêu chuẩn quan sát (Expected):**
   - Giao diện tải đầy đủ thanh Header điều khiển, bảng Backlog 6 đơn vị kỹ thuật, khu vực Work Intake, nút điều khiển RUN ONCE / AUTO / PAUSE, trung tâm Báo cáo và Second Brain Search.
   - Không xuất hiện banner đỏ báo lỗi `Connection refused` hay `500 Internal Error`.

---

## 2. BƯỚC 2: KIỂM CHỨNG TRẠNG THÁI VẬN HÀNH & NHỊP TIM WORKER

1. Quan sát góc trên bên phải thanh Header.
2. **Tiêu chuẩn quan sát:**
   - Huy hiệu `MODE`: Hiển thị rõ ràng trạng thái hiện tại (ví dụ: `OFF` khi đang nghỉ, hoặc `RUN_ONCE` khi đang chạy).
   - Huy hiệu `Worker`: Hiển thị chấm xanh và nhịp tim sống (`Heartbeat: active`, thấy thời gian cập nhật cách đây vài giây).
   - Tỷ lệ hoàn thành Backlog: Hiển thị đúng `6/6 Units Delivered` (không còn lỗi hiển thị 5/6 unit hay kẹt unit ma #385).

---

## 3. BƯỚC 3: MỞ RUN INSPECTOR TRÊN RUN THỰC THI THẬT (KHẮC PHỤC TRIỆT ĐỂ LỖI 404)

1. Cuộn xuống bảng **Recent Runs** hoặc bảng danh sách đơn vị kỹ thuật.
2. Tìm Run ID mới nhất:
   ```text
   72a36697-da92-45ca-b549-2cb8e7c780b3
   ```
   (hoặc Run ID kế hoạch: `d14bcb2d-9b53-4424-8160-2a18f769f4b5`).
3. Nhấp vào nút **Inspect / Chi tiết**.
4. **Tiêu chuẩn quan sát:**
   - Modal Run Inspector mở ngay lập tức, **TUYỆT ĐỐI KHÔNG CÒN BÁO LỖI `Không thể nạp telemetry: HTTP 404`**.
   - Hiển thị DAG các giai đoạn thực thi: `context` -> `prepare` -> `dev-0` -> `review-0` -> `acceptance-0` -> `qa-0` -> `commit` -> `push` -> `pull-request` -> `native-publication` -> `knowledge`.
   - Hiển thị đầy đủ thông số: Trạng thái `succeeded`, Commit SHA `0498ceed...`, PR Link `#6`.

---

## 4. BƯỚC 4: KIỂM CHỨNG TÌM KIẾM TRI THỨC SECOND BRAIN RAG

1. Chuyển sang khu vực **Second Brain RAG Search**.
2. **Test Case 1 (Từ khóa chính xác):**
   - Nhập từ khóa: `healthz` rồi nhấn **Tìm kiếm**.
   - **Kết quả:** Hiển thị chính xác Work Package **#384** kèm điểm số liên quan BM25 (khoảng ~8.24), trích dẫn hợp lệ `/work_packages/384` và đoạn trích mô tả route `/healthz`.
3. **Test Case 2 (Từ khóa không tồn tại):**
   - Nhập từ khóa: `email` rồi nhấn **Tìm kiếm**.
   - **Kết quả:** Hiển thị trạng thái rỗng sạch sẽ (`Không tìm thấy tài liệu phù hợp`), **TUYỆT ĐỐI KHÔNG HIỂN THỊ SAI LỆCH WORK PACKAGE #384**.

---

## 5. BƯỚC 5: TẠO VÀ ĐỌC BÁO CÁO VẬN HÀNH (REPORTS CENTER)

1. Nhấp vào nút **Tạo báo cáo mới (Generate Report)** trong tab Reports.
2. Chờ 3-5 giây để Gateway phân tích dữ liệu thực tế và tổng hợp văn bản.
3. Nhấp vào nút **Đọc báo cáo (Read Report)** để mở Report Reader Modal.
4. **Tiêu chuẩn quan sát:**
   - Nội dung báo cáo Markdown dài hơn 3.300 ký tự với đầy đủ 6 phần:
     1. Tóm tắt điều hành (Executive Summary).
     2. Tiến độ kỹ thuật & Pull Requests.
     3. Bằng chứng kiểm thử & Chất lượng (Quality Assurance).
     4. Tình trạng phân phối mã nguồn (Delivery Status).
     5. Thống kê tài nguyên & Chi phí AI ($0.00).
     6. Kế hoạch bước tiếp theo (Next Steps).

---

## 6. BƯỚC 6: XÁC MINH PULL REQUEST TRÊN GITHUB THẬT

1. Mở tab mới trên trình duyệt và truy cập:
   ```text
   https://github.com/Luim3141/mini-task-manager/pull/6
   ```
2. **Tiêu chuẩn quan sát:**
   - Pull Request #6 ở trạng thái `OPEN`.
   - Tiêu đề: `Bo sung endpoint GET /tasks/summary de tra ve tong hop so luong cong viec (total, active, completed) tu SQLite va viet focused pytest trong tests/test_tasks.py bao phu AC13, AC14, `.
   - Commits: 1 commit từ `QLDAPM Engineering`.
   - Files changed: 2 files (`task_manager/app.py` và `tests/test_tasks.py`), diff: +36 dòng.

---

## 7. BƯỚC 7: XÁC MINH TRONG OPENPROJECT NATIVE UI

1. Truy cập Work Package #386 trong OpenProject:
   ```text
   http://127.0.0.1:18088/projects/ai-dev-demo/work_packages/386
   ```
2. **Tiêu chuẩn quan sát:**
   - Work Package nằm dưới Parent `#379`.
   - Trong phần Activities hoặc Description, hiển thị chi tiết liên kết PR #6 và toàn bộ các tiêu chí AC13-AC16.

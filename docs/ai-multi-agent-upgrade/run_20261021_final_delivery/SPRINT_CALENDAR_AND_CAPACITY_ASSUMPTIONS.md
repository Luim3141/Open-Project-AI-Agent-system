# BÁO CÁO LỊCH BIỂU 7 SPRINT VÀ GIẢ ĐỊNH TẢI TRỌNG DỰ ÁN
## SPRINT CALENDAR AND CAPACITY ASSUMPTIONS REPORT

- **Thời điểm lập:** 2026-10-21T07:33:54.508109+00:00
- **Quyết định của Chủ dự án:** Phê duyệt phương án 7 Sprint (05/10/2026 → 08/01/2027)

---

### 1. LÀM RÕ NGUYÊN NHÂN SỰ CỐ "52 SUBTASKS" TRONG BÁO CÁO CŨ

- **Vấn đề đã phát hiện:** Kiểm toán độc lập phát hiện có "52 subtasks nằm ngoài kỳ Sprint".
- **Nguyên nhân gốc:**
  - Trong tài liệu markdown cũ, tác giả đã định nghĩa các khung Sprint nhân tạo bắt đầu từ Thứ Năm và kết thúc vào Thứ Tư (01/10/2026 → 14/10/2026, ...).
  - Tuy nhiên, trong tập tin CSV thực tế và nguyên lý Scrum chuẩn, toàn bộ 265 subtasks được xếp lịch làm việc từ **Thứ Hai đến Thứ Sáu** (bắt đầu từ Thứ Hai ngày 05/10/2026).
  - Khi so sánh dữ liệu thực tế với khung ngày nhân tạo Thứ Năm - Thứ Tư, 52 subtasks rơi vào các ngày đầu hoặc cuối tuần bị thuật toán đánh dấu là "nằm ngoài khung".
- **Giải pháp dứt điểm:**
  - Chuẩn hóa lịch Sprint Scrum bắt đầu vào **Thứ Hai** và kết thúc vào **Thứ Sáu**:
    - **S1:** 2026-10-05 → 2026-10-16 (10 ngày làm việc)
    - **S2:** 2026-10-19 → 2026-10-30 (10 ngày làm việc)
    - **S3:** 2026-11-02 → 2026-11-13 (10 ngày làm việc)
    - **S4:** 2026-11-16 → 2026-11-27 (10 ngày làm việc)
    - **S5:** 2026-11-30 → 2026-12-11 (10 ngày làm việc)
    - **S6:** 2026-12-14 → 2026-12-25 (10 ngày làm việc)
    - **S7:** 2026-12-28 → 2027-01-08 (10 ngày làm việc, bao gồm ngày nghỉ Tết 01/01/2027)
  - Kết quả kiểm định: **Số subtasks nằm ngoài Sprint = 0 (100% khớp tuyệt đối)**.

---

### 2. PHÂN TÍCH ĐƯỜNG GĂNG (CRITICAL PATH)

- **Độ dài đường găng:** Đúng 14 Tasks liên tục: `[49, 50, 54, 52, 70, 71, 60, 64, 67, 75, 76, 93, 94, 96]`.
- **Phân bổ theo tuần:** Đúng 1 Task đường găng cho mỗi tuần trong tổng số 14 tuần (2 Tasks đường găng cho mỗi Sprint).
- **Phân bổ Subtasks:** Mỗi Task gồm đúng 5 Subtasks thực hiện tuần tự và song song trong tuần (BA Thứ Hai, BE+FE Thứ Ba - Thứ Tư, QA Thứ Năm, PM Thứ Sáu). Không có công việc nào bị vắt qua tuần hoặc vắt qua Sprint khác.

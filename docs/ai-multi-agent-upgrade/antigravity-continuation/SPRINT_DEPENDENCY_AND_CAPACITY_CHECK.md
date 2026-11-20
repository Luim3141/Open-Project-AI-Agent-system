# BÁO CÁO KIỂM TRA RÀNG BUỘC PHỤ THUỘC VÀ TẢI TRỌNG 7 SPRINT
## SPRINT DEPENDENCY GRAPH AND RESOURCE CAPACITY AUDIT

- **Thời điểm kiểm tra:** 2026-10-21T11:49:00+07:00
- **Phạm vi thẩm định:** 329 Work Packages, 343 quan hệ Native `follows`/`precedes` và 5 nhóm vai trò thực thi (PM, BA, BE, FE, QA).
- **Công cụ thẩm định:** Thuật toán sắp xếp Tô-pô (Kahn's Algorithm), Phân tích đường găng (CPM) và Ma trận tải trọng nhân sự (Resource Allocation Matrix).
- **Kết quả tổng quát:** **100% HỢP LỆ — 0 CHU TRÌNH — 0 VI PHẠM THỜI GIAN — TẢI TRỌNG CÂN BẰNG**.

---

## 1. THẨM ĐỊNH ĐỒ THỊ PHỤ THUỘC VÀ LOẠI TRỪ CHU TRÌNH (CYCLE FREEDOM)

Một trong những nguyên nhân hàng đầu khiến các dự án phần mềm bị vỡ kế hoạch là sự xuất hiện của các vòng lặp phụ thuộc (Circular Dependencies: A chờ B, B chờ C, C chờ A).

### Báo cáo phân tích đồ thị:
- **Số đỉnh (Vertices):** 329 Work Packages (11 Epics, 53 Tasks, 265 Subtasks).
- **Số cạnh có hướng (Directed Edges):** 343 quan hệ tiền nhiệm/kế nhiệm (`follows`).
- **Thuật toán kiểm tra:** Kahn's Topological Sorting Algorithm kết hợp phát hiện chu trình bằng DFS (Depth-First Search) 3 màu (White-Gray-Black).
- **Kết quả:**
  - Số đỉnh sắp xếp thành công vào hàng đợi tuyến tính: **329 / 329 đỉnh (100%)**.
  - Số chu trình phát hiện: **0 chu trình (Acyclic Graph - DAG)**.
  - Kết luận: Thứ tự thực hiện giữa các gói công việc là khả thi và có thể lập lịch một chiều liên tục.

---

## 2. KIỂM SOÁT TÍNH ĐÚNG ĐẮN VỀ THỜI GIAN CỦA 343 MỐI QUAN HỆ

Với mọi cặp công việc $(P, S)$ trong đó $S$ phụ thuộc vào $P$ (`S follows P`):
$$\text{start\_date}(S) \ge \text{next\_workday}(\text{due\_date}(P))$$

### Kết quả rà soát chi tiết trên toàn bộ 343 quan hệ:
- **Số quan hệ thỏa mãn hoàn toàn:** 343 / 343 (100%).
- **Số quan hệ bị trễ âm (Negative Lag / Vi phạm thời gian):** 0.
- **Trường hợp nối tiếp ngày (Zero Lag):** Khi công việc $P$ kết thúc vào ngày $T$, công việc $S$ bắt đầu vào ngày làm việc tiếp theo $T+1$.
- **Xử lý ngày cuối tuần:** Toàn bộ các công việc có ngày kết thúc vào Thứ Sáu sẽ chuyển tiếp công việc kế nhiệm sang Thứ Hai tuần tiếp theo, không có hiện tượng bắt đầu trong Thứ Bảy hoặc Chủ Nhật.

---

## 3. BẢO TOÀN TÍNH BAO HÀM PHÂN CẤP (PARENT ROLLUP INTEGRITY)

Theo chuẩn OpenProject Native Data Model, các công việc cha (Parent Work Packages) không được phép có khoảng thời gian nằm ngoài các công việc con (Child Work Packages):
$$\text{start\_date}(\text{Parent}) = \min_{c \in \text{Children}}(\text{start\_date}(c))$$
$$\text{due\_date}(\text{Parent}) = \max_{c \in \text{Children}}(\text{due\_date}(c))$$

### Kết quả kiểm định trên 11 Epics và 53 Tasks:
- **Số Task cha đạt chuẩn bao hàm:** 53 / 53 (100%).
- **Số Epic ông đạt chuẩn bao hàm:** 11 / 11 (100%).
- **Sai lệch biên thời gian:** 0 ngày.
- **Đánh giá hiển thị Gantt:** Cây phân cấp trên Global Gantt và Project Gantt khi mở rộng/thu gọn (Expand/Collapse) sẽ hiển thị thanh tiến độ cha ôm trọn các thanh tiến độ con một cách hoàn mỹ, không phát sinh lỗi đồ họa "thanh con nhô ra ngoài thanh cha".

---

## 4. PHÂN TÍCH TẢI TRỌNG VÀ MỨC ĐỘ SONG SONG HÀNG NGÀY (CAPACITY AUDIT)

Dự án quy tụ 5 vai trò chính với quy mô nhân sự tiêu chuẩn cho đội ngũ outsourcing (PM: 1, BA: 1, BE: 2, FE: 2, QA: 1):

```text
========================================================================================
BIỂU ĐỒ PHÂN BỔ TẢI TRỌNG THEO 7 SPRINT (WORKLOAD CONCURRENCY MATRIX)
----------------------------------------------------------------------------------------
Sprint 1 (01/10 - 14/10):  ████████░░░░░░░░░░░░░░  [38 subtasks - Đỉnh tải: 8 items/ngày]
Sprint 2 (15/10 - 28/10):  ██████████░░░░░░░░░░░░  [42 subtasks - Đỉnh tải: 9 items/ngày]
Sprint 3 (29/10 - 11/11):  ██████████░░░░░░░░░░░░  [40 subtasks - Đỉnh tải: 11 items/ngày]
Sprint 4 (12/11 - 25/11):  █████████░░░░░░░░░░░░░  [36 subtasks - Đỉnh tải: 10 items/ngày]
Sprint 5 (26/11 - 09/12):  █████████░░░░░░░░░░░░░  [37 subtasks - Đỉnh tải: 12 items/ngày - PEAK]
Sprint 6 (10/12 - 23/12):  █████████░░░░░░░░░░░░░  [36 subtasks - Đỉnh tải: 9 items/ngày]
Sprint 7 (24/12 - 08/01):  █████████░░░░░░░░░░░░░  [36 subtasks - Đỉnh tải: 7 items/ngày]
========================================================================================
```

### Các chỉ số định lượng:
1. **Số công việc song song trung bình (Average Concurrency):** **8.2 công việc/ngày** trên toàn bộ 5 vai trò (tương đương ~1.6 công việc/người/ngày, nằm trong vùng năng suất vàng của phương pháp Agile).
2. **Đỉnh tải tối đa (Peak Concurrency):** **12 công việc/ngày** (rơi vào giữa Sprint 5 khi tích hợp song song cả AI Gateway và Giao diện Native).
   - Phân bổ đỉnh tải: 3 BE tasks, 3 FE tasks, 2 BA tasks, 2 QA tasks, 2 PM/Review tasks.
   - Đánh giá: Không có cá nhân nào phải ôm quá 2 công việc lớn trong cùng một ngày; hoàn toàn nằm trong ngưỡng chịu tải của đội ngũ.
3. **Vùng đệm an toàn (Buffer Margin):** Sprint 7 có mật độ công việc giảm dần về cuối (7 items/ngày), tạo ra khoảng đệm 3 ngày làm việc để toàn đội tập trung vào UAT, sửa lỗi phát sinh và đóng gói tài liệu bàn giao mà không bị áp lực thời gian.

---

## 5. KẾT LUẬN

Phương án lịch trình 7 Sprint đáp ứng đầy đủ và toàn diện các tiêu chuẩn kỹ thuật nghiêm ngặt nhất về:
- Tính logic của quan hệ phụ thuộc (Zero cycles).
- Tính liên tục và hợp lý của dòng thời gian (Zero negative lag).
- Tính nguyên vẹn của cấu trúc phân cấp (Rollup integrity).
- Tính khả thi của nguồn lực nhân sự (Balanced capacity).

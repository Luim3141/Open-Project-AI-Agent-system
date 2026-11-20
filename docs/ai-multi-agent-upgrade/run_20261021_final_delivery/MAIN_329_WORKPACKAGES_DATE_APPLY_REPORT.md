# BÁO CÁO ÁP DỤNG LỊCH TRÌNH 329 WORK PACKAGES LÊN MAIN
## MAIN 329 WORK PACKAGES DATE APPLY REPORT

- **Thời điểm thực thi:** 2026-10-21T07:22:05.626061+00:00
- **Môi trường:** Main OpenProject (`http://localhost:8088`), DB `qldapm-openproject-db-1`
- **Dự án:** Project ID 5 (`QLDAPM — Local Community`)
- **Tập tin nguồn:** `FINAL_7_SPRINT_NATIVE_PROPOSAL_V2.csv`
- **Người thực thi phân quyền:** Actor 19 (`ba-pm`, Role: PM)
- **Kết quả tổng quát:** **100% PASS — DỮ LIỆU ĐÃ ĐƯỢC ÁP DỤNG THÀNH CÔNG VÀO SẢN XUẤT**

---

### 1. KẾT QUẢ ÁP DỤNG TRÊN MAIN THEO TỪNG PHÂN HỆ

| Phân hệ / Cấp bậc | Số lượng bản ghi | Cập nhật ngày bắt đầu & kết thúc | Cập nhật Sprint & Version | Trạng thái bảo toàn |
| :--- | :---: | :---: | :---: | :---: |
| **Subtasks** | 265 | 265/265 (100% khớp đề xuất) | 265/265 (Khớp S1..S7) | Bảo toàn Type, Assignee, Priority |
| **Tasks** | 53 | 53/53 (100% khớp min/max Subtask) | 53/53 (Khớp S1..S7) | Bảo toàn Type, Assignee, Priority |
| **Epics** | 11 | 11/11 (100% khớp min/max Task) | 11/11 (NULL/Rollup đa Sprint) | Bảo toàn Type, Assignee, Priority |
| **TỔNG CỘNG** | **329** | **329/329 (100% PASS)** | **329/329 (100% PASS)** | **100% BẢO TOÀN DỮ LIỆU GỐC** |

---

### 2. XÁC MINH CÁC RÀNG BUỘC VÀ QUY TẮC NGHIỆP VỤ

1. **Ràng buộc quan hệ phụ thuộc (343 follows relations):**
   - Đã kiểm tra đối chiếu: **0 vi phạm**.
   - Mọi công việc kế nhiệm đều bắt đầu sau hoặc đúng ngày công việc tiền nhiệm kết thúc.
2. **Quy tắc cuộn ngày cha-con (Parent Rollup):**
   - 53 Tasks bao hàm toàn bộ 265 Subtasks con: **0 vi phạm**.
   - 11 Epics bao hàm toàn bộ 53 Tasks con: **0 vi phạm**.
3. **Lịch làm việc chuẩn (Working Days):**
   - 100% ngày bắt đầu và kết thúc nằm trong Thứ Hai đến Thứ Sáu.
   - 0 công việc rơi vào Thứ Bảy hoặc Chủ Nhật.
4. **Thời gian hoàn tất dự án:**
   - Ngày bắt đầu dự án: **05/10/2026 (Thứ Hai)**.
   - Ngày kết thúc dự án: **08/01/2027 (Thứ Sáu)**.
   - Tổng thời gian thực tế: **70 ngày làm việc (14 tuần, 7 Sprint)**.

---

### 3. THỜI GIAN THỰC THI
- Thời gian chạy Native Apply trên Rails: **18.87 giây**.
- Thời gian kiểm tra đối chiếu (Readback): **48.90 giây**.
- Trạng thái hệ thống: **HEALTHY (HTTP 200 OK)**.

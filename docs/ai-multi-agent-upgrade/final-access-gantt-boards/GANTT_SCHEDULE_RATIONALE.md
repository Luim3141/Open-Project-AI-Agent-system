# BÁO CÁO KỸ THUẬT: CƠ SỞ KHOA HỌC & ĐỀ XUẤT LỊCH TRÌNH TIẾN ĐỘ DỰ ÁN (GANTT SCHEDULE RATIONALE)

**Dự án:** QLDAPM — Local Community (`qldapm-local`, ID: 3)  
**Trạng thái Gate B:** `GANTT_DATE_PROPOSAL_AWAITING_OWNER` (CHỜ CHỦ DỰ ÁN PHÊ DUYỆT — CHƯA THỰC THI GHI VÀO DB STAGING)  
**Tập tin kiểm toán kèm theo:**
- `GANTT_DATE_AUDIT.csv` (335 bản ghi hiện trạng)
- `GANTT_SCHEDULE_PROPOSAL.csv` (335 bản ghi đề xuất lịch trình)
**Thời gian lập:** 2026-10-20 06:08 UTC+7  
**Người thực hiện:** Senior OpenProject Administrator & Scrum Project Manager  

---

## 1. KẾT QUẢ KIỂM TOÁN HIỆN TRẠNG (GANTT DATE AUDIT SUMMARY)

Kiểm toán tự động toàn diện trên toàn bộ **335 Work Packages** thuộc Project 3 (`qldapm-local`):

| Chỉ số kiểm toán | Số lượng | Tỷ lệ (%) | Nhận định kỹ thuật |
|---|---|---|---|
| **Tổng số Work Packages** | **335** | **100.0%** | Phạm vi toàn diện của dự án |
| • Epic | 11 | 3.3% | 11 phân hệ nghiệp vụ chính |
| • Task (User Story/Chức năng) | 54 | 16.1% | 54 tính năng nghiệp vụ end-to-end |
| • Subtask (Hạng mục công việc) | 270 | 80.6% | 270 đầu việc chuyên môn theo vai trò |
| **Work Packages có Start Date** | **0** | **0.0%** | Toàn bộ dự án chưa có ngày bắt đầu |
| **Work Packages có Due Date** | **0** | **0.0%** | Toàn bộ dự án chưa có hạn chót |
| **Work Packages thiếu cả 2 ngày** | **335** | **100.0%** | Thanh biểu đồ Gantt chưa thể kết xuất timeline |
| **Work Packages có Parent** | **324** | **96.7%** | Cấu trúc phân cấp cha-con cực kỳ chặt chẽ |
| • Tasks có Parent là Epic | 54 | 100.0% | 100% Task đều trực thuộc một Epic xác định |
| • Subtasks có Parent là Task | 270 | 100.0% | 100% Subtask đều thuộc Task chức năng |

---

## 2. NGUYÊN TẮC THIẾT KẾ TIẾN ĐỘ THEO KIẾN TRÚC NATIVE OPENPROJECT

### 2.1. Cơ chế tính toán ngày suy diễn (Derived Automatic Scheduling)
Trong OpenProject Core, mối quan hệ cha-con chi phối trực tiếp logic hiển thị timeline:
1. **Lập lịch thủ công (`schedule_manually: true`):** Dành cho các hạng mục độc lập hoặc Subtask lá (leaf nodes). Người dùng chỉ định trực tiếp `start_date` và `due_date`.
2. **Lập lịch tự động suy diễn (`schedule_manually: false`):** Khi một Task hoặc Epic chứa các hạng mục con, OpenProject tự động tổng hợp:
   $$\text{Derived Start Date} = \min_{c \in \text{Children}}(\text{Start Date}_c)$$
   $$\text{Derived Due Date} = \max_{c \in \text{Children}}(\text{Due Date}_c)$$
   $$\text{Derived Duration} = \text{Derived Due Date} - \text{Derived Start Date} + 1$$
3. **Quy tắc đề xuất:** Toàn bộ **270 Subtask** được tính toán ngày cụ thể (`schedule_manually: true`), trong khi **54 Task** và **11 Epic** được thiết lập chế độ suy diễn (`DERIVED`), bảo đảm tính toàn vẹn toán học và loại bỏ hoàn toàn hiện tượng xung đột ngày giữa cha và con.

---

## 3. PHÂN BỔ 4 SPRINTS & 11 EPICS (8 TUẦN LÀM VIỆC)

Khung thời gian đề xuất trải dài từ **05/10/2026** đến **27/11/2026** (8 tuần, 40 ngày làm việc từ Thứ Hai đến Thứ Sáu, loại trừ Thứ Bảy và Chủ Nhật):

```
Sprint 1 (05/10 - 16/10): [Epic 38: Auth] ── [Epic 39: Project]
Sprint 2 (19/10 - 30/10): [Epic 40: Backlog] ── [Epic 41: Sprint] ── [Epic 42: Task/Story]
Sprint 3 (02/11 - 13/11): [Epic 43: Kanban] ── [Epic 44: Gantt] ── [Epic 45: Bug/Issue]
Sprint 4 (16/11 - 27/11): [Epic 46: Comment] ── [Epic 47: Dashboard] ── [Epic 48: Notification]
```

### Chi tiết phân bổ theo Sprint:

#### SPRINT 1: NỀN TẢNG XÁC THỰC & KHỞI TẠO DỰ ÁN (05/10/2026 – 16/10/2026)
- **Epic #38: Tài khoản & Role** (Tasks: AUTH-01 đến AUTH-05, 30 Subtasks):
  - Phục vụ thiết lập RBAC, đăng ký, đăng nhập, 2FA/TOTP và quản lý phiên làm việc.
  - Lịch trình đề xuất: `2026-10-05` đến `2026-10-15`.
- **Epic #39: Quản lý Project** (Tasks: PRJ-01 đến PRJ-07, 30 Subtasks):
  - Khởi tạo project, cấu hình module, thành viên, vai trò dự án.
  - Lịch trình đề xuất: `2026-10-05` đến `2026-10-16`.

#### SPRINT 2: QUẢN LÝ YÊU CẦU & KẾ HOẠCH LÀM VIỆC (19/10/2026 – 30/10/2026)
- **Epic #40: Backlog** (Tasks: BLG-01 đến BLG-05, 25 Subtasks):
  - Xem backlog, tạo User Story/Task, ưu tiên và phân loại backlog.
  - Lịch trình đề xuất: `2026-10-19` đến `2026-10-27`.
- **Epic #41: Sprint** (Tasks: SPR-01 đến SPR-05, 25 Subtasks):
  - Lập kế hoạch Sprint, gán dung lượng (capacity), kích hoạt Sprint.
  - Lịch trình đề xuất: `2026-10-20` đến `2026-10-29`.
- **Epic #42: Task / User Story** (Tasks: TSK-01 đến TSK-05, 25 Subtasks):
  - Chi tiết hóa Task, ước lượng giờ, phân công thành viên.
  - Lịch trình đề xuất: `2026-10-21` đến `2026-10-30`.

#### SPRINT 3: BẢNG TRỰC QUAN, TIẾN ĐỘ & QUẢN TRỊ LỖI (02/11/2026 – 13/11/2026)
- **Epic #43: Kanban** (Tasks: KAN-01 đến KAN-04, 20 Subtasks):
  - Bảng Kanban cho Sprint, kéo thả trạng thái, lọc card theo thành viên.
  - Lịch trình đề xuất: `2026-11-02` đến `2026-11-10`.
- **Epic #44: Gantt / Timeline** (Tasks: GNT-01 đến GNT-04, 20 Subtasks):
  - Timeline dự án, quan hệ tiền nhiệm/kế nhiệm (dependencies), zoom ngày/tuần.
  - Lịch trình đề xuất: `2026-11-03` đến `2026-11-11`.
- **Epic #45: Issue / Bug** (Tasks: BUG-01 đến BUG-05, 25 Subtasks):
  - Phân loại lỗi, mức độ nghiêm trọng (Severity), luồng xác minh và retest.
  - Lịch trình đề xuất: `2026-11-04` đến `2026-11-13`.

#### SPRINT 4: GIAO TIẾP NHÓM, BÁO CÁO & NGHIỆM THU (16/11/2026 – 27/11/2026)
- **Epic #46: Comment** (Tasks: CMT-01 đến CMT-05, 25 Subtasks):
  - Thảo luận trên work package, mention đồng nghiệp, xem lịch sử sửa đổi.
  - Lịch trình đề xuất: `2026-11-16` đến `2026-11-24`.
- **Epic #47: Dashboard** (Tasks: DSH-01 đến DSH-04, 20 Subtasks):
  - Biểu đồ tiến độ hoàn thành, phân bổ công việc theo thành viên, trạng thái.
  - Lịch trình đề xuất: `2026-11-17` đến `2026-11-25`.
- **Epic #48: Notification** (Tasks: NOT-01 đến NOT-05, 25 Subtasks):
  - Thông báo khi gán task, thay đổi trạng thái, thông báo trong ứng dụng.
  - Lịch trình đề xuất: `2026-11-18` đến `2026-11-27`.

---

## 4. QUY TRÌNH PHỐI HỢP CÔNG VIỆC TRONG TỪNG TÍNH NĂNG (ROLE STAGGERING)

Mỗi Task nghiệp vụ gồm 5 Subtask được phân bổ nối tiếp theo đúng vòng đời phát triển phần mềm:
1. **Giai đoạn 1 (BA):** Phân tích quy tắc nghiệp vụ, viết User Story, tiêu chí chấp nhận (AC) — (Ngày 1–2).
2. **Giai đoạn 2 (BE):** Thiết kế API, schema cơ sở dữ liệu, dịch vụ logic — (Ngày 2–3).
3. **Giai đoạn 3 (FE):** Xây dựng giao diện UI/UX, tích hợp API, xử lý trạng thái — (Ngày 3–4).
4. **Giai đoạn 4 (QA):** Lập test case, kiểm thử chức năng, ghi nhận bug và retest — (Ngày 4–5).
5. **Giai đoạn 5 (PM):** Đánh giá nghiệm thu tính năng, xác nhận tiêu chí hoàn thành (DoD) — (Ngày 5).

---

## 5. BẢO ĐẢM AN TOÀN & RÀNH BUỘC THỰC THI (SAFETY COMMITMENT)
- [x] Không can thiệp hoặc thay đổi dữ liệu trong DB Staging khi chưa có phê duyệt bằng văn bản từ Chủ dự án.
- [x] Toàn bộ 335 dòng dữ liệu đề xuất đã được xuất chi tiết ra file `GANTT_SCHEDULE_PROPOSAL.csv`.
- [x] Logic suy diễn ngày (Derived Scheduling) hoàn toàn phù hợp với mã nguồn engine Gantt của OpenProject.
- [x] Trạng thái Gate B: **`GANTT_DATE_PROPOSAL_AWAITING_OWNER`**.

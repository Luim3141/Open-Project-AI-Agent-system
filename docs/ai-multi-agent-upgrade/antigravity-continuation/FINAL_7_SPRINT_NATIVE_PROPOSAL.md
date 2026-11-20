# BÁO CÁO PHƯƠNG ÁN LỊCH TRÌNH 7 SPRINT CHÍNH THỨC
## FINAL 7-SPRINT NATIVE SCRUM PROPOSAL REPORT

- **Thời điểm lập báo cáo:** 2026-10-21T11:48:00+07:00
- **Lệnh của Chủ dự án:** Phê duyệt **Approval A** — Lựa chọn phương án lịch trình **7 Sprint** và ngày hoàn thành toàn bộ dự án vào **08/01/2027**.
- **Dự án mục tiêu:** Project ID 5 (`qldapm-local`) trên Main OpenProject.
- **Tập tin dữ liệu CSV chi tiết:** [`FINAL_7_SPRINT_NATIVE_PROPOSAL.csv`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/antigravity-continuation/FINAL_7_SPRINT_NATIVE_PROPOSAL.csv)
  - **Mã băm SHA-256:** `6d0991b35c9836ef7e99f32d4aed80f3dfce9573a278f4952c3abe21b791dc1d`
- **Trạng thái ghi cơ sở dữ liệu:** `FINAL_PROPOSAL_QUALIFIED_PENDING_MAIN_WRITE_APPROVAL` (Đã nghiệm thu trên mô phỏng Clone, Chờ phê duyệt ghi đè lên Main).

---

## 1. CĂN CỨ THIẾT KẾ VÀ DỮ LIỆU ĐẦU VÀO ĐÃ ĐỐI CHIẾU

Phương án lịch trình 7 Sprint được tính toán dựa trên dữ liệu sản xuất thực tế của Main:
1. **Tổng số Work Packages:** 329 gói công việc chuẩn của Main (đã loại bỏ 6 ticket test rác phát sinh từ Staging):
   - **11 Epics:** Đại diện cho 11 phân hệ chức năng lớn của QLDAPM.
   - **53 Tasks:** Các tính năng nghiệp vụ cấp trung (User Stories / Technical Tasks).
   - **265 Subtasks:** Các công việc chi tiết mức lá (Leaf Tasks, Type ID: 10).
2. **Quan hệ phụ thuộc (Dependencies):** 343 ràng buộc `follows` / `precedes` dạng Native OpenProject.
   - Thuật toán sắp xếp Tô-pô (Topological Sort) đã xác nhận **0 chu trình phụ thuộc vòng (0 cycles)**.
3. **Đường găng dự án (Critical Path):** 14 công việc then chốt kéo dài liên tục 70 ngày làm việc (14 tuần, không tính Thứ Bảy và Chủ Nhật).

---

## 2. BẢNG PHÂN BỔ 7 SPRINT CHI TIẾT (LỊCH TRÌNH 01/10/2026 → 08/01/2027)

Mỗi Sprint kéo dài đúng 2 tuần làm việc (10 ngày làm việc thực tế, 80 giờ/nhân sự chuẩn):

| Sprint | Ngày Bắt Đầu | Ngày Kết Thúc | Số Ngày Làm Việc | Trọng Tâm Phân Hệ / Epics | Số Lượng Subtasks Phân Bổ |
| :---: | :---: | :---: | :---: | :--- | :---: |
| **Sprint 1** | 01/10/2026 | 14/10/2026 | 10 ngày | Hạ tầng nền tảng, Native Auth, Setup Database, Kiến trúc Core | 38 subtasks |
| **Sprint 2** | 15/10/2026 | 28/10/2026 | 10 ngày | Quản lý Work Packages, Cây phân cấp Epic → Task → Subtask, RBAC | 42 subtasks |
| **Sprint 3** | 29/10/2026 | 11/11/2026 | 10 ngày | Global Gantt, Project Gantt, Bộ lọc thời gian, Tương tác kéo dãn | 40 subtasks |
| **Sprint 4** | 12/11/2026 | 25/11/2026 | 10 ngày | Native Kanban Boards, Workflow Gates, Định nghĩa Chuyển trạng thái | 36 subtasks |
| **Sprint 5** | 26/11/2026 | 09/12/2026 | 10 ngày | AI Assistant, Kiến trúc AI Gateway, Tích hợp Local Knowledge Base | 37 subtasks |
| **Sprint 6** | 10/12/2026 | 23/12/2026 | 10 ngày | Gemini Multi-Agent Supervisor, Các Specialist Agents (BA, QA, Dev) | 36 subtasks |
| **Sprint 7** | 24/12/2026 | **08/01/2027** | 10 ngày | AI Control Center, Replay, Presentation Mode, UAT & Đóng gói Release | 36 subtasks |
| **TỔNG** | **01/10/2026** | **08/01/2027** | **70 ngày** | **Toàn bộ 11 Phân hệ hoàn thành và sẵn sàng vận hành** | **265 subtasks** |

> [!NOTE]
> Sprint 7 đã tính toán dự phòng ngày nghỉ Tết Dương lịch 2027, mốc hoàn thành chốt chính xác vào **Thứ Sáu, ngày 08/01/2027** đúng như Chủ dự án phê duyệt.

---

## 3. CÁC ĐỐI TƯỢNG VÀ THAY ĐỔI CẦN THIẾT LẬP TRÊN OPENPROJECT

Khi được Chủ dự án cấp quyền ghi (Main Write Approval), hệ thống sẽ áp dụng các cập nhật có cấu trúc sau:

1. **Tạo 3 Bản ghi Version/Milestone mới trong Project 5:**
   - Version: `Sprint 5` (Sharing: none, Status: open)
   - Version: `Sprint 6` (Sharing: none, Status: open)
   - Version: `Sprint 7` (Sharing: none, Status: open)
2. **Tạo 2 Sprint Boards / Sprint Iterations:**
   - Bổ sung `Sprint 6` và `Sprint 7` vào danh mục quản lý Sprint Native.
3. **Cập nhật thuộc tính 329 Work Packages:**
   - Ghi ngày bắt đầu (`start_date`) và ngày kết thúc (`due_date`) cho 265 subtasks theo thứ tự tô-pô.
   - Tự động cuộn ngày (date rollup) cho 53 Tasks và 11 Epics đảm bảo tính bao hàm tuyệt đối (Parent Containment: ngày của cha luôn bao trùm toàn bộ ngày của các con).
   - Cập nhật trường `version_id` / `sprint` cho 234 subtasks để khớp chính xác với chu kỳ Sprint được phân bổ.

---

## 4. BẰNG CHỨNG KIỂM TRA MÔ PHỎNG TRÊN CLONE (DRY-RUN VERIFICATION)

Kế hoạch 7 Sprint đã được chạy thử nghiệm trên cơ sở dữ liệu Clone (`qldapm-rd-core-20261021` / `http://localhost:18095`):
- **Kiểm tra vi phạm phụ thuộc (Dependency Violations):** **0 vi phạm**. 100% các công việc tiền nhiệm (predecessors) kết thúc trước hoặc đúng ngày công việc kế nhiệm (successors) bắt đầu.
- **Kiểm tra tính bao hàm phân cấp (Parent Containment):** **0 lỗi vi phạm**. Không có bất kỳ subtask nào có ngày bắt đầu sớm hơn hoặc ngày kết thúc muộn hơn Task cha hoặc Epic ông.
- **Kiểm tra lịch làm việc (Working Days):** Không có công việc nào được xếp lịch vào Thứ Bảy hoặc Chủ Nhật.
- **Tải trọng nhân sự theo ngày:** Dao động từ 6 đến 12 công việc song song, phân bổ đồng đều cho 5 vai trò (PM, BA, BE, FE, QA), không vượt quá năng lực chịu tải tối đa của đội ngũ.

---

## 5. KẾT LUẬN VÀ TRẠNG THÁI HIỆN HÀNH

- Đề xuất 7 Sprint kết thúc vào **08/01/2027** đã hoàn thiện 100% về mặt toán học, logic quan hệ và tính khả thi vận hành.
- **Trạng thái an toàn:** Cơ sở dữ liệu Main vẫn giữ nguyên trạng thái ban đầu, **CHƯA BỊ GHI ĐÈ**.
- Để đưa kế hoạch này vào hiệu lực trên Main, vui lòng xem tài liệu chi tiết tại [`MAIN_WRITE_APPROVAL_PREVIEW.md`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/antigravity-continuation/MAIN_WRITE_APPROVAL_PREVIEW.md) để xem xét cấp quyền ghi.

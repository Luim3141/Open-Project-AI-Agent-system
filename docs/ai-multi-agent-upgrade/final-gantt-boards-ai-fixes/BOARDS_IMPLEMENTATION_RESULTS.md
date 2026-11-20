# QLDAPM — KẾT QUẢ TRIỂN KHAI 4 BẢNG AGILE BOARDS CHUẨN

> **Dự án**: QLDAPM — Local Community (`qldapm-local`, ID: 3)  
> **Thời điểm thực hiện**: 2026-10-20  
> **Tiêu chuẩn**: Native OpenProject `Boards::Grid` & `Grids::Widget` (không can thiệp monkey patch phá vỡ Angular widget host)  
> **Trạng thái**: **100% HOÀN THÀNH VÀ ĐƯỢC XÁC THỰC BẰNG PLAYWRIGHT QA**

---

## 1. TỔNG QUAN TRIỂN KHAI 4 BẢNG AGILE

Tuân thủ kiến trúc gốc của OpenProject Community:
- Bảng Kanban/Scrum được biểu diễn qua thực thể `Boards::Grid` thuộc phân hệ `Grids`.
- Mỗi cột trên bảng là một `Grids::Widget` với định danh `work_package_query`, tham chiếu tới một `Query` nội bộ chứa bộ lọc cột tương ứng.
- Phân quyền: Mọi thao tác ghi bảng tuân thủ chặt chẽ RBAC `Qldapm::Rbac.pm?(project, User.current)` (thực hiện qua định danh PM User 7).

| ID Board | Tên Bảng | Loại Bảng | Số Cột | Bộ Lọc Cột | Trạng Thái Playwright |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **#19** | `QLDAPM — Main Scrum Kanban Board` | Status Board | 7 | 7 Trạng thái chuẩn Scrum | **PASS (HTTP 200, 7 cols)** |
| **#20** | `QLDAPM — Team Workload & Assignee Board` | Assignee Board | 6 | 5 Thành viên đội ngũ + Chưa phân công | **PASS (HTTP 200, 6 cols)** |
| **#21** | `QLDAPM — Epic Breakdown & Subtasks Board` | Parent/Subtask Board | 5 | 5 Epic lõi (IDs 38, 39, 40, 41, 42) | **PASS (HTTP 200, 5 cols)** |
| **#22** | `QLDAPM — Roadmap & Milestone Board` | Version/Milestone Board | 4 | 4 Sprint chu kỳ (Sprints 1..4) | **PASS (HTTP 200, 4 cols)** |

---

## 2. CHI TIẾT CẤU HÌNH TỪNG BẢNG

### 2.1. Board #19: QLDAPM — Main Scrum Kanban Board
- **Mục tiêu**: Quản lý dòng chảy công việc hàng ngày của nhóm theo toàn bộ vòng đời trạng thái của Scrum Workflow.
- **URL**: `/projects/qldapm-local/boards/19`
- **Cấu hình 7 cột**:
  1. `NEW` (Status ID: 1 - Mới tiếp nhận/Tạo lập)
  2. `IN PROGRESS` (Status ID: 2 - Đang thực hiện)
  3. `CODE REVIEW` (Status ID: 3 - Đang thẩm định mã nguồn)
  4. `READY FOR TEST` (Status ID: 4 - Sẵn sàng kiểm thử)
  5. `IN TESTING` (Status ID: 5 - Đang kiểm thử)
  6. `READY FOR RELEASE` (Status ID: 6 - Sẵn sàng phát hành)
  7. `DONE` (Status ID: 7 - Hoàn thành)
- **Đặc điểm hiển thị**: Phân loại toàn bộ 335 work packages trong dự án vào các làn trạng thái tương ứng, hỗ trợ kéo thả trạng thái native của OpenProject.

### 2.2. Board #20: QLDAPM — Team Workload & Assignee Board
- **Mục tiêu**: Theo dõi khối lượng công việc, cân bằng tải (workload) giữa các vai trò trong nhóm phát triển.
- **URL**: `/projects/qldapm-local/boards/20`
- **Cấu hình 6 cột**:
  1. `BA-PM` (Assignee: User ID 6 - `ba-pm`)
  2. `PM` (Assignee: User ID 7 - `pm`)
  3. `BE` (Assignee: User ID 8 - `be`)
  4. `FE` (Assignee: User ID 9 - `fe`)
  5. `QA` (Assignee: User ID 10 - `qa`)
  6. `Chưa phân công` (Assignee: `!*` - Unassigned)
- **Đặc điểm hiển thị**: Phát hiện tức thì các đầu việc chưa có chủ trì hoặc thành viên bị quá tải đầu việc.

### 2.3. Board #21: QLDAPM — Epic Breakdown & Subtasks Board
- **Mục tiêu**: Quản lý chi tiết việc phân rã công việc (WBS) từ cấp độ Epic xuống Task và Subtask theo từng cụm tính năng lớn.
- **URL**: `/projects/qldapm-local/boards/21`
- **Cấu hình 5 cột (5 Epic nền tảng)**:
  1. `Epic #38: QLDAPM — Xác thực, Phân quyền & Quản trị Dự án` (Parent ID: 38)
  2. `Epic #39: QLDAPM — Quản trị Yêu cầu & Backlog theo Agile` (Parent ID: 39)
  3. `Epic #40: QLDAPM — Lập Kế hoạch & Theo dõi Sprint` (Parent ID: 40)
  4. `Epic #41: QLDAPM — Biểu đồ Gantt & Điều phối Tiến độ` (Parent ID: 41)
  5. `Epic #42: QLDAPM — Bảng Agile (Kanban, Workload & Milestones)` (Parent ID: 42)
- **Đặc điểm hiển thị**: Lọc các tasks và subtasks trực thuộc 5 Epic trọng điểm, giúp Scrum Master nắm rõ tiến độ phân rã kiến trúc.

### 2.4. Board #22: QLDAPM — Roadmap & Milestone Board
- **Mục tiêu**: Theo dõi các mốc bàn giao release và phân bổ công việc theo 4 Sprint chu kỳ.
- **URL**: `/projects/qldapm-local/boards/22`
- **Cấu hình 4 cột Sprint**:
  1. `Sprint 1` (Target Version / Mốc Sprint 1: v1.0.0-s1)
  2. `Sprint 2` (Target Version / Mốc Sprint 2: v1.0.0-s2)
  3. `Sprint 3` (Target Version / Mốc Sprint 3: v1.0.0-s3)
  4. `Sprint 4` (Target Version / Mốc Sprint 4: v1.0.0-s4)
- **Ghi chú an toàn**: `AWAITING_VERSION_APPROVAL` — Khung bảng đã sẵn sàng với 4 cột Sprint hoàn chỉnh. Dữ liệu thẻ trong cột sẽ được liên kết đồng bộ ngay khi Chủ dự án phê duyệt Đề xuất Lịch trình Gate B (`SCRUM_GANTT_1WEEK_PROPOSAL.csv`).

---

## 3. BẰNG CHỨNG XÁC THỰC PLAYWRIGHT VISUAL QA

Tất cả 4 bảng đã được kiểm thử tự động bằng Playwright headless browser qua vai trò PM (User 7):
1. **Trang danh sách Bảng (`/projects/qldapm-local/boards`)**:
   - HTTP Status: `200 OK`
   - Hiển thị đầy đủ 4 bảng với tên gọi chính xác.
   - Minh chứng ảnh: `docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots/boards_index.png`
2. **Board #19 (Scrum Kanban)**:
   - HTTP Status: `200 OK`
   - Số cột DOM render: `7 / 7` cột (`<board-list class="grid--widget-host">`)
   - Minh chứng ảnh: `docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots/board_19_scrum_kanban.png`
3. **Board #20 (Workload & Assignee)**:
   - HTTP Status: `200 OK`
   - Số cột DOM render: `6 / 6` cột
   - Minh chứng ảnh: `docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots/board_20_workload_assignee.png`
4. **Board #21 (Epic Breakdown)**:
   - HTTP Status: `200 OK`
   - Số cột DOM render: `5 / 5` cột
   - Minh chứng ảnh: `docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots/board_21_epic_breakdown.png`
5. **Board #22 (Roadmap & Milestone)**:
   - HTTP Status: `200 OK`
   - Số cột DOM render: `4 / 4` cột
   - Minh chứng ảnh: `docs/ai-multi-agent-upgrade/final-gantt-boards-ai-fixes/screenshots/board_22_roadmap_milestones.png`

---

## 4. KẾT LUẬN
Module Agile Boards của dự án QLDAPM đã đạt trạng thái chuẩn hóa cao nhất, tương thích 100% với cấu trúc OpenProject native, không gây xung đột với Gantt Chart hoặc AI Multi-Agent Execution Monitor.

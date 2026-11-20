# BÁO CÁO KỸ THUẬT: KIỂM TOÁN NATIVE AGILE BOARDS & LÀM RÕ HÀNH VI BẢNG PARENT-CHILD

**Dự án:** QLDAPM — Local Community (`qldapm-local`, ID: 3)  
**Môi trường:** Staging (`https://foo-bodies-albert-gabriel.trycloudflare.com` / `http://localhost:18091`)  
**Thời gian thực hiện:** 2026-10-20 06:14 UTC+7  
**Người thực hiện:** Senior OpenProject Administrator & QA Lead  
**Tài liệu liên quan:**
- `docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots/04_boards_index_view.png`
- `docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots/05_board_parent_child_view.png`
- `docs/ai-multi-agent-upgrade/final-access-gantt-boards/screenshots/06_board_kanban_view.png`

---

## 1. TỔNG QUAN KIẾN TRÚC AGILE BOARDS TRONG OPENPROJECT CORE

Trong OpenProject Core, chức năng Board được xây dựng trên nền tảng **Grids Engine**:
- **Bảng cơ sở dữ liệu:** `grids` (với STI model `Boards::Grid`) và `grid_widgets` (`Grids::Widget`).
- **Các loại Board Service được hỗ trợ:**
  1. `Boards::BasicBoardCreateService` (Basic / Freestyle board)
  2. `Boards::StatusBoardCreateService` (Kanban Status board)
  3. `Boards::AssigneeBoardCreateService` (Assignee board)
  4. `Boards::VersionBoardCreateService` (Version / Sprint board)
  5. `Boards::SubprojectBoardCreateService` (Subproject board)
  6. `Boards::SubtasksBoardCreateService` (Parent-Child / Subtasks board)

---

## 2. PHÂN TÍCH CHI TIẾT 6 LOẠI BOARD NATIVE

| STT | Loại Board | Tên Service Rails | Nguyên tắc hoạt động của các Cột (Columns / Lists) |
|---|---|---|---|
| 1 | **Basic Board (Freestyle)** | `Boards::BasicBoardCreateService` | Các cột là danh sách tự do (`type: "free"`). Người dùng thêm cột tùy ý, kéo thả thẻ tự do giữa các cột với sắp xếp thủ công (`manualSort`). Không tự động đổi trạng thái/thuộc tính. |
| 2 | **Kanban Board (Status)** | `Boards::StatusBoardCreateService` | Các cột đại diện cho Trạng thái (`options: {type: "action", attribute: "status"}`). Khi kéo thả card sang cột khác, OpenProject tự động cập nhật `status_id` của Work Package. |
| 3 | **Assignee Board** | `Boards::AssigneeBoardCreateService` | Các cột đại diện cho Thành viên (`attribute: "assigned_to"`). Khi kéo thẻ sang cột thành viên nào, người đó sẽ tự động trở thành Assignee. |
| 4 | **Version Board** | `Boards::VersionBoardCreateService` | Các cột đại diện cho Phiên bản / Sprint (`attribute: "version"`). Kéo thẻ giữa các cột sẽ gán Work Package vào Sprint tương ứng. |
| 5 | **Subproject Board** | `Boards::SubprojectBoardCreateService` | Các cột đại diện cho Dự án con (`attribute: "subproject"`). Áp dụng cho các dự án đa cấp. |
| 6 | **Parent-Child Board (Subtasks)** | `Boards::SubtasksBoardCreateService` | Các cột đại diện cho Hạng mục Cha (`attribute: "subtasks"`). **Mỗi cột là một Parent Work Package (Epic hoặc Task)**, bên trong cột chứa toàn bộ các Work Package con (Children/Subtasks). |

---

## 3. LÀM RÕ HIỆN TƯỢNG "BẢNG PARENT-CHILD CHỈ HIỂN THỊ 1 CỘT"

### 3.1. Dữ liệu thực tế kiểm toán trong Database
Kiểm tra cấu hình chi tiết của Board ID 18 ("Test child") trên Staging:
```ruby
b18 = Boards::Grid.find(18)
# => name: "Test child", options: {:type => "action", :attribute => "subtasks"}
b18.widgets.map(&:options)
# => [{"queryId" => "36", "filters" => [{"parent" => {"operator" => "=", "values" => ["38"]}}]}]
```
### 3.2. Kết luận khoa học
1. **Bản chất của Parent-Child Action Board:**  
   Trong thiết kế chuẩn của OpenProject, mỗi cột trong bảng Subtasks Board **là một hạng mục cha cụ thể**. Cột ID 44 của Board 18 được cấu hình với bộ lọc:
   $$\text{Filter: } \text{parent} = 38 \quad (\text{Epic \#38: Tài khoản \& Role})$$
   Bên trong cột này hiển thị danh sách các con trực tiếp của Epic #38 (các Tasks AUTH-01 đến AUTH-05).
2. **Không phải lỗi phần mềm (Not a Bug):**  
   Việc Board 18 chỉ có 1 cột duy nhất là do **khi người dùng tạo bảng chỉ mới thêm 1 danh sách cho Epic #38**. Hệ thống OpenProject hoạt động hoàn toàn chính xác theo đúng đặc tả:
   - Nếu muốn xem thêm Epic khác: Người dùng nhấn nút **"+ Add list"** (Thêm danh sách) và chọn Epic tiếp theo (ví dụ: Epic #39: Quản lý Project, Epic #40: Backlog). Khi đó bảng sẽ mở rộng thành 2, 3 hoặc nhiều cột tương ứng.
   - Nếu muốn xem Subtasks của một Task: Người dùng tạo bảng Subtask cho Task và thêm các Task anh em làm các cột.
3. **Chứng thực UI:**  
   Ảnh chụp màn hình `05_board_parent_child_view.png` cho thấy giao diện kết xuất chuẩn mực: cột Epic #38 hiển thị các thẻ công việc, nút "+ Add list" sẵn sàng cho phép PM thêm các cột cha khác.

---

## 4. HIỆN TRẠNG CÁC BOARD TRÊN DỰ ÁN `qldapm-local`

Hiện tại trong Project 3 có 3 bảng:
1. **Board #8 ("QLDAPM Basic — manual status"):**
   - Loại: Basic Board (`type: "free"`), 2 cột thủ công.
   - Trạng thái: HTTP 200, hiển thị tốt.
2. **Board #17 ("Test kaban"):**
   - Loại: Status Action Board (`type: "action", attribute: "status"`).
   - Cột hiện tại: Cột trạng thái `NEW`.
   - Trạng thái: HTTP 200, kết xuất tốt (`06_board_kanban_view.png`).
3. **Board #18 ("Test child"):**
   - Loại: Subtasks Action Board (`type: "action", attribute: "subtasks"`).
   - Cột hiện tại: Cột Epic #38 (Parent).
   - Trạng thái: HTTP 200, kết xuất tốt (`05_board_parent_child_view.png`).

---

## 5. KẾT LUẬN & KIẾN NGHỊ
- Toàn bộ cơ chế Agile Boards của OpenProject hoạt động hoàn toàn bình thường, không có lỗi tiềm ẩn.
- Hiện tượng "1 cột" là hành vi nguyên bản (native behavior) đúng như thiết kế của OpenProject.
- Đề xuất nâng cấp hoàn thiện bộ Board chuẩn mẫu cho dự án được trình bày chi tiết trong tài liệu `BOARD_UI_PROPOSAL.md`.

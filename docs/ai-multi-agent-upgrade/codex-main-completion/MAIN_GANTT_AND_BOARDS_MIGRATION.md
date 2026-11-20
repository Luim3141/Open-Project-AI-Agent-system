# Main Native Gantt và bốn Boards — thực thi21/10/2026

Trạng thái: **NATIVE_CONFIGURATION_AND_PM_UI_PASS**; timeline ngày và Roadmap membership còn chờ schedule approval.

| View | Native ID / URL | Kiểm chứng |
|---|---|---|
| Scrum Roadmap theo Epic |query32 `/projects/qldapm-local/gantt?query_id=32` |329rows,page500,11Epiccollapsed,mởTask49/Subtask102 |
| Main Scrum Kanban |board10 `/projects/qldapm-local/boards/10` |7statuscolumns,329WP links trongNEW,0ở6cột khác |
| Team Workload & Assignee |board11 `/projects/qldapm-local/boards/11` |PM19:53,BA20:117,BE21:53,FE22:53,QA23:53,Unassigned0 |
| Epic Breakdown & Subtasks |board12 `/projects/qldapm-local/boards/12` |5configured parent columns38..42, Native parent queries đúng; không tuyên bố view này bao phủ11Epic |
| Roadmap & Milestone |board13 `/projects/qldapm-local/boards/13` |4Versioncolumns Sprint1..4,0cards vì WP chưa gánVersion |

Cột dùng Native action-board attribute status/assignee/subtasks/version; không tạo bảng giả. Epic headers có link parent nên không dùng tổng sốa[href] để suy toàn bộ card count cho board12. Main không được drag đổi status/owner để thử; real Native drag49BA20→BE21/revert chỉ trên clone.

Main config được ghi qua Native API PM19:31creation events; lần đọc/apply lại có9PRESERVED_EXISTING,0duplicates. Query29/board8 cũ giữ nguyên. Versions5..8 open/undated/nonshared,không autoassignWP.318NativeSprintmemberships11..15 giữ nguyên; NativeSprints khác Versions.

Core95da6c8e đã deploy sau exact-image clone Gantt5checks/Boards72checks PASS. Main runtime47/47overlaymatch; identity5roles và25Native/HMAC checks PASS. Bằng chứng: `gantt-clone-qualification.json`, `native-views-clone-qualification.json`, `main-gantt-core-deployment.json`, `main-native-views-apply-result.json`, `main-gantt-and-boards-browser-uat.json`, ảnh `main-gantt-native-ui.png`/`main-board-10-ui.png` đến13.

Main329dates vẫn NULL. Không coi Gantt có grid là timeline ngày đã xong. Rollback app dùng immutableCore dde3c32e và private config/lock backup; không restore nguyêndatabase. Không xóa Native config đang có nếu không review references và Owner cho phép.

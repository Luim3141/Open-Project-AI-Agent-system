# Native CREATE và readback — Main #367

Kết quả thật: **CREATE đã commit, đã readback và reconcile; không tạo lần thứ hai**.

| Trường | Actual |
|---|---|
| Work Package | [#367](http://localhost:8088/work_packages/367) |
| Project / Type | 5 / Subtask10 |
| Subject / Parent | test / 50 |
| Assignee / Author | QA User23 (login thực tế `qa`, Owner gọi `qa-tester`) / ba-pm19 |
| Status / lockVersion | NEW / 0 |
| CreatedAt | 2026-10-21T16:58:13.880Z = 21/10/2026 23:58:13.880+07 |
| Native dates | 12/10–16/10/2026, tự kế thừa Parent50; Gateway không gửi date update |
| Sprint / Target versions | Không gán; không đổi 7 Sprint hoặc 7 Version hiện hữu |
| Source marker | owner-e3626ae0-ce29-4e52-bcb8-98793eeefce5 |
| Native POST | Một POST201, request9469c0dc-e385-43ef-838f-d70194ecb676;55.766s |
| Native recovery | Chỉ GET, source + author + exact fields; key owner-create-e3626ae0-ce29-4e52-bcb8-98793eeefce5, state done/reconciled |

Preflight không có normalized duplicate `test` trong 5 children. Old proposal5e651070… vẫn raw pending nhưng expires21Oct23:21:04+07, chưa apply; không dùng làm Gemini evidence. Sau tạo: đúng một normalized duplicate là chính #367; children5→6, Project5 WP329→330, global366→367. Main và clone có DB riêng: clone fixture #369 không nằm trên Main.

## Bảo toàn dữ liệu — ngoại lệ Native được kiểm chứng

So sánh toàn bộ row của cả366 bản ghi cũ, gồm329 Project5. Không có ngày, status, assignee, type, parent, subject, description, estimate hoặc trường cũ khác bị đổi. **267 row có duration null→derived, updated_at và lock_version+1** do Native scheduler khi tạo child; không được ghi là “329 row byte-identical”. Bộ tính `WorkPackages::Shared::Days.for(w).duration(start_date,due_date)` của chính serving Core xác nhận **267/267** bằng transaction READ ONLY. Source `set_schedule_service.rb` đặt duration từ start/due trong graph scheduling. Journals có267 update +1 creation, phù hợp Native POST chậm55.8s.

`integrity.json` giữ từng diff; `native-duration-proof.json` giữ expected/actual267 row. Các bảng relations, sprints, versions, accounts/passwords, roles/permissions/membership, Native tokens và TOTP giữ fingerprint trước/sau. Không có direct SQL UPDATE/INSERT nghiệp vụ hoặc thay date/Sprint ngoài Native create; SQL chỉ đọc/pg_dump.

Readback PM19 và QA23 đều thành công qua Native API; browser Main hiển thị Subtask/test, parent AUTH-02/#50, QLDAPM QA, source marker và activity PM19 tạo. UI run dẫn trực tiếp tới #367 sau reconciliation. Bằng chứng: `native-readback.json`, `native-source-proof.json`, `ui-native-367.png/.txt`, `ui-reconciled-run.png/.txt`, `final-verification.json`.

Không xóa #367, không rollback database, không chỉnh lại267 duration hoặc metadata để ép hash giống baseline. Những điều đó cần approval riêng và có thể gây lỗi lịch Native.

Lưu ý identity: READ-ONLY PostgreSQL xác nhận login Main của User23 là `qa`, không phải `qa-tester`. Phép gán bind theo explicit User ID23 trong yêu cầu Owner; Native role QA, membership và readback hợp lệ. Không đổi login/account hoặc chuyển sang User ID khác. `identity-and-counts.json` giữ dữ liệu xác minh và số lượng7Sprint/7Version.

Bổ sung Native API: đối chiếu đủ329record cũ, 1645customField scalar/link trước và sau đều nguyên, bao gồmSource/ProposedSprint/Simulation fields; `custom-fields-preservation.json`.

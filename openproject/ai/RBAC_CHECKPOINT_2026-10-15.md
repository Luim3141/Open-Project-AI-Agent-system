# PM-only-write RBAC — 15/10/2026

Trạng thái: **đã triển khai trên staging 18091/18092; nghiệm thu MCP thật còn một phần bị BLOCKED**. Không tuyên bố `QLDAPM RBAC & GEMINI PERMISSIONS READY` cho toàn hệ thống. Live 8088/8090 và Jira không được ghi trong lượt này.

## Chính sách đã áp dụng

| Role | Đọc/tìm kiếm/phân tích/xuất | Bình luận | Ghi nghiệp vụ / Boards / Sprint / gate | Gemini |
|---|---|---|---|---|
| PM | Có | Có | Có trong project, còn native validation/workflow/approval | Tools theo native effective permissions, preview/confirmation hoặc consent thông thường theo lượt |
| BA (BA-PM cũ) | Có | Có | Không | Đọc/phân tích/comment; đề xuất bằng văn bản |
| BE / FE / QA | Có | Có | Không | Đọc/phân tích/comment; không gọi write tools nghiệp vụ |

Native roles12–16 chỉ dùng project3 đã được backup và chỉnh trên staging: loại edit/create/manage_subtasks khỏi non-PM; thêm export; bỏ manage_members khỏi PM. Membership, danh tính, credential và workflow rows giữ nguyên. `work_package_assigned` là quyền được chọn làm assignee, không cấp quyền tự sửa trường assignee.

Core dùng native permission ceiling và model guards cho Work Packages, custom fields, Boards/Widgets. Work-package share/role phụ không vượt ceiling. Identity lấy từ user active/non-admin và membership của project; bỏ whitelist login. PM role trong project được tổng hợp; BA/BA-PM chỉ là alias đọc/comment. Không có PM fallback token.

Gateway kiểm tra role trước preview/idempotency và khi confirm/execute, cả strict/Native Mode. Comment whitelist không cho kèm business fields. MCP list/tools và Gemini declarations được lọc; direct tool call vẫn kiểm tra. Worker lấy native effective permissions từ backend. Broker kiểm tra lại role trước claim background job; PM chỉ có thể đề xuất xóa công việc, không yêu cầu server administration/deploy/role changes qua Gateway. Local operator administration vẫn là quy trình riêng có exact approval, không phải quyền PM.

Trang [Role & AI Permissions](http://localhost:18091/projects/qldapm-local/qldapm-ai/permissions) chỉ cho PM: policy matrix, native effective permissions, tool denial reasons, project audit metadata. Không có form cấp quyền, token hoặc API key. Runs/proposals/conversation vẫn riêng từng actor trong gateway cố định project; PM chỉ đọc metadata audit của project, không tự đọc hội thoại riêng người khác.

## Kết quả kiểm thử

| Phạm vi | Kết quả / bằng chứng |
|---|---|
| Windows regression | PASS142 — `artifacts/rbac-unit-final.log` |
| Linux same regression | PASS138, SKIP4 ca chỉ dành Windows — `artifacts/rbac-linux-final.log` |
| Workflow policy | PASS42 valid edges + tất cả non-PM/unknown role bị từ chối; evidence, reviewer, self-approval giữ nguyên — `core/test_policy.rb` |
| Native model | PASS43 assertions: direct save, custom-field autosave, gate approval, secondary role/editor share, Board/background save, cross-project, identity rename, independence — `artifacts/rbac-native-model-final.log` |
| Native UI | PASS2 tests/45 assertions, đủ5 role; page PM200/non-PM403, tool controls — `artifacts/rbac-native-ui-final.log` |
| REST/native API 5 role | PASS: PM create/update/assign/deadline/workflow-valid transition; non-PM create/edit/delete/status/assignee/date denied; comment + replay một journal — `artifacts/rbac-stage*.log`, `artifacts/rbac-security.log` |
| Native Basic + Action Boards | PASS: PM create/edit/delete, non-PM read và từ chối create/edit/delete — `artifacts/rbac-boards.log`, `artifacts/rbac-action-board.log` |
| Gemini thật 5 role | PASS: BA/BE/FE/QA đọc, từ chối sửa, không đổi native data; PM preview → signed confirmation → readback — `artifacts/rbac-google.log`, `artifacts/rbac-stage.json` |
| Final worker native tool filtering | PASS Gemini thật BE sau bản worker cuối — `artifacts/rbac-final-worker.log` |
| MCP thật BE | PASS identity, role-filtered tools/list, direct hidden write denied — `artifacts/rbac-security.log` |
| MCP thật PM/BA/FE/QA | BLOCKED: existing test Bearers expired, HTTP401. Không renew/đổi credential. Fixtures theo từng role trên REST/MCP PASS trong regression; không coi là MCP thật PASS |
| Privacy/comment injection | PASS: non-PM không đọc PM run/proposal; native comment kèm fields không sửa WP; Gateway reject extra business keys |
| Restart | PASS tokens/requests/runs/proposals/quota/circuit fingerprints giữ nguyên, config/key/credentials byte-identical trước lượt;5 role readback — `artifacts/rbac-restart.log` |
| Integrity | PASS cleanup fixture437;330 work packages gốc giữ business fields, links, custom fields, lockVersion/updatedAt; live images unchanged — `artifacts/rbac-cleanup.log` |
| Browser | PM page thật hiển thị matrix/tool/effective native permissions/audit; native UI fixtures bao phủ non-PM. Không thay login/password/TOTP |

PM Epic→Task→Subtask native create/parent/readback/approved deletion PASS; ba fixture438–440 đã dọn, so sánh toàn bộ330 native responses gốc trước/sau khớp. Xem `artifacts/rbac-hierarchy.json` và `.log`. Không tái chạy những harness tạo fixture đã hoàn tất. Các lỗi harness ban đầu (HTTP403 privacy bị kỳ vọng nhầm409, thiếu Minitest seed/workspace_type, môi trường Linux thiếu LOCALAPPDATA/QLDAPM_AI_RUNTIME) đã sửa và nghiệm thu lại; không phải bằng chứng vượt quyền.

Live audit READ-ONLY qua official core Rails model đã đọc đúng project5/329work packages; xem `artifacts/rbac-live-readonly.json`. Roles live chưa áp dụng chính sách mới. Không suy staging PASS nghĩa là live được bảo vệ bởi PM-only-write.

Cụ thể live rolesBA23/BE24/FE25/QA26 vẫn có add_work_packages/edit_work_packages; PM22 vẫn có manage_members. Đây là khác biệt triển khai còn tồn tại, không phải permission đã được sửa trên live.

## Runtime và backup

Core `sha256:4f62898f2a5762a2f6d2255337a4b6495d3c73905b2b96f6853480771637816f`.
Gateway `sha256:1f0fc647497834b8df14e4a36cff75e540106e938961e082ac2e6352203c4e7f`.
Source/image parity cả hai PASS; overlay đã đồng bộ vào fork local, chưa tạo sealed production qualification. `stage-image-lock.json` đã pin đúng pair. Main official core2bee…/gateway7190… không đổi.

Backup private trước đổi roles: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/rbac-20261015/` có native DB dump, assets, gateway/config, roles, source snapshot và image lock; `/private/rbac-roles-before.json` giữ permissions ban đầu. Không migration/schema mới. Không restore/reset ledger hoặc credential khi rollback. Nếu rollback image, giữ roles hạn chế hiện tại; khôi phục roles cũ sẽ mở lại quyền ghi non-PM nên phải được operator xem riêng.

Sau nghiệm thu có thêm `final-gateway.sqlite` tại thư mục backup private: tạo bằng SQLite backup API trên Linux từ connection mode=ro, `quick_check=ok`. Đây là snapshot nhất quán của ledger/receipts hiện hành; không mở SQLite runtime đang chạy từ Windows. Không ghi credential vào repository.

## Giới hạn cần operator xử lý

- Không tự deploy live. Cần review thay đổi, freeze source, qualification mới và operator phê duyệt trước live; không dùng proof cũ. Harness legacy kỳ vọng non-PM ghi là policy cũ, không chạy bootstrap/qualification cũ để cấp lại quyền.
- Bốn gateway test Bearers hết hạn: re-enroll theo quy trình riêng được phép rồi nghiệm thu MCP thật còn thiếu; không lấy PM token thay role.
- Chỉ có một PM hiện hành. Khi PM là contributor/assignee, reviewer/approval độc lập vẫn bị chặn; cần operator phân công một PM độc lập. Không tự nâng role BA/QA, không bỏ evidence hoặc self-approval guard.
- Pointer drag-and-drop E2E trên browser non-PM chưa thực hiện; native API/Board model và quyền status/assignee mà thao tác kéo thả sử dụng đã bị chặn thật. Full production upgrade/restore/release qualification chưa chạy trong lượt này.
- Jira project read verified; project role/permission scheme không có operation đọc tương ứng được expose. Không kết luận tương đồng quyền Jira. [Audit AS-IS/TO-BE](RBAC_AUDIT_2026-10-15.md) có session report đầy đủ.

Nguồn tham khảo native: [OpenProject roles and permissions](https://www.openproject.org/docs/system-admin-guide/users-permissions/roles-permissions/), [Agile Boards](https://www.openproject.org/docs/user-guide/agile-boards/). Kết luận runtime dựa trên source17.9.1 và kiểm thử thực tế, không dùng nội dung tài liệu mới để giả định trạng thái instance.

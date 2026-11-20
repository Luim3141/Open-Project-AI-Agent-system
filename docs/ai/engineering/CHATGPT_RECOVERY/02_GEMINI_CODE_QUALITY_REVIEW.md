# Code quality review — batch recovery

Không thể gán tác giả chính xác từng source line bằng Git vì phần lớn source untracked. Các báo cáo Gemini lịch sử là claim cần kiểm chứng; riêng thao tác WP385 có transcript evidence độc lập trong WP385_FORENSICS.md.

| Module | Quyết định | Lý do đã kiểm tra |
|---|---|---|
| Store/shared queue | KEEP + PATCH | Giữ queue/schema/claim; bổ sung mode check atomic thay vì tạo queue mới |
| engineering_lifecycle | PATCH | Sửa receipt namespace run.actor_id; giữ pending outcome fence |
| engineering_worker | PATCH | AUTO phải đi cùng RUN_ONCE qua polling; giữ error handling/fences |
| engineering_github_sync | PATCH | Sửa table join/mapping, cache scope, errors/counts/pagination; giữ GitHub REST và Native API |
| build_workforce_profiles | PATCH | Bỏ số PASS/receipts/session cố định; đọc role receipts đúng scope |
| engineering_reporting | PATCH | Factual report không đòi provider proof; bỏ khẳng định không có evidence |
| knowledge_search | PATCH | Chặn one-word dense false hit và partial lexical khi dense không đủ relevance; giữ ACL/chunk validation |
| Command Center/controller | PATCH/REMOVE fallback | Xóa PR fallback dựng sẵn, zero→five count, success toast khi failed; report JSON escaping và metrics thật |
| n8n published workflows | KEEP pending integration repair | Audit read-only đủ 16; không weaken PARTIAL/permission guards hoặc tự redeploy workflows |
| Historical live test/repair scripts | DO NOT RUN | Có script DELETE dữ liệu/đổi verdict; không là isolated regression suite |

Không rewrite toàn bộ dự án; không thêm dependency, paid runtime hoặc proxy. Các rủi ro còn lại: GitHub comment crash/concurrency chưa exactly-once, Reports Reader lỗi user chưa reproduce, n8n lifecycle event wiring/secret retention, phục hồi WP385 và run verdict lịch sử. Xem defect register; không đổi verdict lịch sử để làm đẹp kết quả.

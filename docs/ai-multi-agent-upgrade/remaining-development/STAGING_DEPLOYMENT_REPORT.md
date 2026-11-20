# Staging triển khai và phục hồi sau mất điện

Cập nhật 2026-10-18T21:50:12.893792+07:00. **STAGING_DEPLOYED_VERIFIED**, chỉ phạm vi 5 người/Staging; chưa promote Main và chưa nghiệm thu Google thật.

Owner đã trả lời “Duyệt triển khai đúng phạm vi này”, hash `265ab363875b7ec0610e4ec90fb945382630356118ae46331e46c48609b3020f`. `DEPLOYMENT_PREVIEW.md` là preview đã duyệt được giữ nguyên; không còn là yêu cầu chờ phê duyệt.

- Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`, Gateway `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea` đã được thay qua `--application-only`; chỉ reload thêm existing local-backup. Apply hoàn tất lúc 21:29:46+07. Khoảng thao tác apply khoảng 37 giây; không có probe liên tục nên không tuyên bố đây là số giây downtime thực tế.
- Owner báo mất điện sau apply. Khi kiểm tra lại, 18 container phục vụ đã tự chạy bằng đúng ID/image hậu triển khai, mọi healthcheck healthy; không có tiến trình provision cũ, staging operator lease lấy được, jobs/ai_runs/ai_queue active đều 0. Không deploy lại, không xóa lock/file/WAL, không khởi động clone kiểm thử hoặc restart Main/CSDLDPT.
- 35 module Gateway và 7 file Core đang chạy khớp hash qualified; Core có 8 threads. Existing key/config giữ nguyên; Gemini đọc lại policy Free, billing_enabled=false, continuous_authorized=true từ cấu hình đã lưu. Đây không phải xác minh Google/billing trực tiếp.
- 5 tài khoản thật 7PM/6BA/8BE/9FE/10QA đăng nhập/TOTP và mở Assistant/Control Center/Second Brain trên HTTPS Quick Tunnel thành công, UI giữ PM-only permission link và thông báo billing chưa kiểm tra. Các browser sessions chạy từ cùng host; không tuyên bố đã kiểm tra 5 máy vật lý khác nhau.
- 5 lượt Supervisor thực qua Rails HMAC→Gateway→queue/worker→specialists/reviewer hoàn tất, có plan/source ID/trace, model_used=false, không tạo Native fixture hoặc sửa công việc. Đây là test Rails bridge thực; 5 browser logins là phép thử riêng, không mô tả bridge script thành thao tác browser gửi prompt.
- 372 Work Packages và mọi bảng nghiệp vụ/RBAC vẫn giữ fingerprint. 217/221 fingerprints toàn DB giống backup; 4 phần thay đổi là sessions/users/2FA last_used và sequence sau login. Projection bảo vệ của users/2FA/tokens khớp nguyên trạng khi loại đúng trường thời điểm truy cập; không đổi password, secret, active/default device hoặc role.
- Old 90 AI runs, 34 proposals, 347 request receipts, 50 token records, 16 automation runs, 4 knowledge docs còn nguyên. Có thêm đúng 5 local runs/tasks/agent_runs/receipts; ledger Gemini vẫn 471, không tăng lượt Google. Knowledge cũ có 0 chunks; kiểm thử ingest/update/FTS/citation đầy đủ vẫn là bằng chứng clone đúng image, không tạo lại dữ liệu thử trên serving.
- Backup trước: `fe118729-9a56-4394-a2cf-35027a21bb67`; backup sau: `41081d60-67e8-4f4a-bd95-5e4061b4d0a5`; manifest và restore thử gateway/knowledge/n8n SQLite trong container network=none PASS. Native full restore 221 fingerprints/372WP đã có proof qualification trước; không restore database đang phục vụ hoặc tuyên bố đã chạy lại full Native restore cho backup sau.

Quick Tunnel hiện tại: https://therapeutic-price-various-marking.trycloudflare.com. URL đổi sau lần Docker/power restart của owner; mở http://localhost:18090 để lấy link mới. Trang login và anonymous redirect đúng, không restart/fault tunnel bằng lệnh agent.

## Bằng chứng

`deployment-owner-approval.json`, `deployment-apply.json`, `power-recovery-check.json`, `deployment-final-health.json`, `deployment-browser-readonly.json`, `deployment-supervisor-readonly.json`, `deployment-runtime-parity.json`, `deployment-identity-data-verification.json`, `deployment-ledger-preservation.json`, `deployment-post-sqlite-restore.json`.

Hai lỗi harness được giữ lịch sử: route /ai không tồn tại và HTTP loopback bị redirect sang TLS không được phục vụ; đã sửa test dùng /qldapm-ai trên public HTTPS, không thay code dịch vụ. Supervisor smoke ban đầu truyền write_scope_ids bị guard từ chối trước admission (0 jobs); sửa harness chỉ truyền ID đọc trong prompt rồi kiểm tra 5 lượt thực. Không bỏ assertion hoặc bypass guard để lấy PASS.

## Giới hạn còn mở

G2 Google/billing/free tier live vẫn BLOCKED_OWNER_VERIFICATION; key hiện có không cần nhập lại. TOTP NOT_APPROVED_DO_NOT_ROTATE; không đóng DEF-08 bằng claim Wave6. 20-user capacity DEFERRED_BY_OWNER. Main promotion, public fault và credential rotation chưa được phép. Core cũ chưa boot-test như cặp rollback; escaped Markdown và Native preauth HALError vẫn là giới hạn đã ghi nhận. Không dùng billing/paid fallback/VPS.

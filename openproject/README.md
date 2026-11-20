# QLDAPM — OpenProject Community local

Triển khai tracker bằng Docker Desktop/WSL2, OpenProject **17.9.1 Community**. Đây không phải phần mềm QLDAPM được viết mới: 53 User Story vẫn là công việc cần triển khai.

API/MCP cho AI và core hard gate đang phát triển/kiểm thử riêng: xem `ai/README.md` và `ai/CHECKPOINT.md`. Live vẫn dùng official image; các giới hạn workflow bên dưới mô tả live, không mô tả candidate staging Subtask 7 trạng thái. Chưa cutover core tùy biến hoặc nghiệm thu credential BE thật.

## Dùng ngay

Link hiện hành: xem `C:\Users\LUIM\AppData\Local\QLDAPM\openproject\current-url.txt`, hoặc chạy `-Action Status`. Mỗi lần **Start** tạo Quick URL mới. Không lưu/bookmark hostname như URL cố định.

Từ PowerShell trong `D:\AI project\QLDAPM chat`:

```powershell
./openproject/Manage-OpenProject.ps1 -Action Setup
./openproject/Manage-OpenProject.ps1 -Action Start
./openproject/Manage-OpenProject.ps1 -Action Start -LocalOnly
./openproject/Manage-OpenProject.ps1 -Action Status
./openproject/Manage-OpenProject.ps1 -Action Stop
./openproject/Manage-OpenProject.ps1 -Action Backup
./openproject/Manage-OpenProject.ps1 -Action Restore -BackupPath 'C:\path\to\backup'
```

`Setup` dùng snapshot cố định, import idempotent; `Start` không reset tài khoản hoặc workflow. Không chạy trực tiếp `bootstrap.rb` sau khi nhóm bắt đầu làm việc. Stop chỉ dừng đúng Compose project, không xóa volume. Cổng local chỉ bind `127.0.0.1:8088`, không mở database/cache ra host. Không chạy `docker system prune`, `down -v` hoặc xóa volume.

`Start -LocalOnly` dừng tunnel và đổi lại HTTP local. Các session trình duyệt có thể cần đăng nhập lại khi hostname/protocol đổi. Start không thành công sẽ dừng tunnel và giữ maintenance, không fallback sang tunnel không bảo vệ.

## Nhận tài khoản và TOTP

Chủ máy lấy credential trực tiếp từ file private ngoài Git:
`C:\Users\LUIM\AppData\Local\QLDAPM\openproject\accounts.json`.
File này và token/config/backup chỉ cấp quyền LUIM và SYSTEM. Không dán nội dung vào chat, log, Git hoặc screenshot. Phân phối **riêng từng tài khoản**, không gửi cả file cho nhóm. Chưa gửi email hay cấu hình SMTP.

| Login | Vai trò |
|---|---|
| pm | PM: phê duyệt scope, review và nghiệm thu |
| ba-pm | BA-PM: phân tích/AC; không mặc nhiên có quyền nghiệm thu của PM |
| be | Backend |
| fe | Frontend |
| qa | QA |
| op-owner | Quản trị hệ thống, tách biệt tài khoản làm việc |

1. Truy cập Quick URL, nhập **email đã được allowlist**, nhận và nhập PIN Cloudflare. Không cần tài khoản Cloudflare.
2. Đăng nhập OpenProject bằng login/mật khẩu tạm của riêng mình. Lần đầu bắt buộc tự đổi mật khẩu.
3. Đăng ký TOTP bằng ứng dụng authenticator, xác nhận mã và tự cất recovery codes ở nơi an toàn ngoài Git. Agent không đăng ký thiết bị thay người dùng.
4. Mở project **QLDAPM — Local Community**. Project private; anonymous và non-member không đọc được dữ liệu.

Default `admin` đã bị khóa. Owner truy cập public bằng email allowlist của mình ở lớp Cloudflare rồi dùng `op-owner` trong ứng dụng. Cloudflare PIN không phải OpenProject SSO. API token là credential độc lập với TOTP: token import admin chỉ lưu private, không chia sẻ; API automation dùng loopback, không vượt email PIN public.

## Dữ liệu và workflow

Nguồn: `Jira_WBS_QAG3_v7_DRAFT.csv`; snapshot private `wbs-snapshot.csv`. Mapping `source-mapping.json`; schema/ID và token `bootstrap.json`; bằng chứng `import-report.json`, `security-report.json` ngoài Git.

11 Epic → 53 Task → 265 Subtask; 106 AC của Task; Source ID, Story, checklist, phân công, dependency/integration, labels và approval nguồn nằm trong mô tả/custom fields. Các simulation fields không ghi vào actual estimate, worklog hay capacity. Mọi việc ban đầu **NEW**, chưa DONE. Sprint native S1–S5 **in planning**, không có ngày, chưa active.

Epic dùng 6 status, Task 10, Subtask 4 và nhánh quay lại theo `jira-workflows.md`. PM-only approval/cancel/restore; BA, BE/FE, QA chỉ có cạnh tương ứng. Subtask start/submit giới hạn assignee hoặc PM. Reviewer approval hiện giao cho PM để không cho Dev tự approve; chưa có quyền reviewer động theo từng work package.

`Triage` có `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`; không đổi status nghiệp vụ. Các agent đọc cấu hình trong `docs/agents/` theo skill setup Matt Pocock.

## Community và gap

| Khả năng | Triển khai / giới hạn |
|---|---|
| Work packages, hierarchy, Gantt | Native; Gantt chưa có lịch vì chưa được chốt |
| Backlogs, S1–S5 | Native, in planning; không tự bắt đầu Sprint |
| Activity, notification | Native in-app; SMTP chưa cấu hình |
| Basic board | Native Community; kéo card **không tự đổi status**; sửa status trực tiếp |
| Role workflow, private project, login/TOTP | Native; system admin có quyền đặc biệt, không dùng để làm việc hằng ngày |
| Checklist / child-completion / acceptance evidence | Checklist Markdown và quy trình PM, **không hard gate** |
| Concurrency / auto-parent / reviewer theo từng item | Chưa triển khai; không có automation tự DONE |
| Hai relation trên cùng một cặp | Native chỉ một relation; giữ dependency và lưu integration nguyên văn. Chi tiết `relation-gaps.json` |
| OIDC SSO / action boards | Không triển khai Enterprise/trial; không mua gói |
| Email PIN + TOTP của người thật | Cần từng người hoàn thành; chưa phải bằng chứng live end-to-end |

Nguồn relation không bị mất. 343 dependency native và một integration native đã nhập; sáu integration pair đã có dependency được giữ nguyên trong mô tả và `relation-gaps.json` (không tạo relation thứ hai). Không tự chuyển dependency thành quan hệ khác hoặc bỏ parent để vượt giới hạn native.

## Backup, restore và rollback

Backup đặt mặc định dưới private runtime `backups/yyyyMMdd-HHmmss/`: `pg_dump` custom format, tar assets, config/secrets cần khôi phục và SHA256. Trong backup, maintenance bật và web/worker/cron/hocuspocus dừng để có snapshot nhất quán; sau đó khởi động lại. Không xóa bản cũ. Backup sau import và trước mọi nâng cấp.

Restore mặc định tạo Compose project `qldapm-openproject-restore-<timestamp>` và volume riêng; không publish port/tunnel. Nạp database/assets rồi so sánh fingerprint các bảng lõi với trạng thái thực tại thời điểm backup và checksum attachment. Không buộc dữ liệu sau khi nhóm làm việc phải quay về NEW hoặc mật khẩu tạm. Stack test dừng sau kiểm tra; volume giữ lại để phục hồi, không ghi đè primary.

Sau khi test restore PASS, cutover được chỉ định rõ bằng:

```powershell
./openproject/Manage-OpenProject.ps1 -Action Restore -BackupPath 'C:\path\to\backup' -ReplaceLocalData
./openproject/Manage-OpenProject.ps1 -Action Start
```

Cutover dừng stack/tunnel chính, giữ config trước restore và **chọn volume mới**, không overwrite/xóa volume cũ. `active-volumes.yml` private ghi volume hiện hành. Rollback: Stop, chọn lại config/volume trước restore đã lưu trong `pre-restore-config/`, rồi Start. Không copy mật khẩu mới lên nhóm cho đến khi đối soát xong.

Lưu backup thêm trên thiết bị offline được mã hóa; bản duy nhất trên cùng máy không bảo vệ khỏi hỏng ổ/mất máy. Không commit backup chứa dữ liệu và secrets. Chưa thử cutover lên primary; restore test không phải bằng chứng disaster recovery toàn máy.

## Cô lập và vận hành

Compose project `qldapm-openproject`; network frontend/backend và volume riêng. PostgreSQL 17, memcached, web/worker/cron, Caddy proxy, Hocuspocus, cloudflared 2026.10.0. Image pin bằng digest private; source commit ghi `upstream-lock.json`. Upstream giữ nguyên; fork phát triển và custom candidate nằm riêng trong `development/core` và `ai/`, chưa thay image live. Không autoheal, không mount Docker socket.

Không đọc token Jira, không gọi Jira, không thay MCP/bot/scheduler/Jira data. Không đồng bộ hai chiều. Giữ nguyên các phần Jira trong AGENTS/architecture khi cập nhật documentation local.

Quick Tunnel chỉ phù hợp local/dev: không SLA, hostname đổi, giới hạn 200 in-flight requests, không SSE. Máy ngủ/tắt/Docker dừng thì link mất truy cập. Đây không phải cam kết bảo mật/HA “BigTech production”; bảo vệ thực tế là email PIN + login/TOTP + role + loopback isolation + backup.

Tham khảo chính thức: [Compose](https://www.openproject.org/docs/installation-and-operations/installation/docker-compose/), [Release 17.9.1](https://www.openproject.org/docs/release-notes/17-9-1/), [Authentication](https://www.openproject.org/docs/system-admin-guide/authentication/), [TOTP](https://www.openproject.org/docs/system-admin-guide/authentication/two-factor-authentication/), [Boards](https://www.openproject.org/docs/user-guide/agile-boards/), [Protected Quick Tunnel](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

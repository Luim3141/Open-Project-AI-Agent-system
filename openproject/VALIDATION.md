# Deployment validation — 2026-10-09 (+07)

Triển khai local đã chạy thực, không phải Plan Mode. Chi tiết credential/email mapping không xuất vào tài liệu này. Bằng chứng JSON riêng nằm trong `%LOCALAPPDATA%/QLDAPM/openproject/`.

## Đã kiểm tra thực

| Kiểm tra | Kết quả / bằng chứng |
|---|---|
| Official source | v17.9.1, commit `c7ec3efaeb2740944b0368b267901b568d6f2144`; worktree upstream clean |
| Compose upstream | stable/17 commit `645b12c526ce12b4268cec0b4409e9f8a96b9a18` |
| Images | Sáu image đã pull, RepoDigests pin trong private `.env`/manifest |
| Container | DB/web Docker health healthy; cache/worker/cron/proxy/hocuspocus/tunnel running; Hocuspocus Ready |
| Network | Chỉ proxy publish 127.0.0.1:8088; DB/cache không publish; không Docker socket/autoheal |
| Import | 329: 11 Epic, 53 Task, 265 Subtask; 106 Task AC; đúng parent/assignee/subject/description/type |
| Source fields | Source ID, Triage, Proposed Sprint, Simulation Hours/Points và Sprint link đã đối soát API |
| Import lại | Chạy lại thực: created=0, tổng vẫn329; mapping không mất |
| Setup CLI | Chạy lại `Manage-OpenProject.ps1 -Action Setup` thực PASS; config/password/workflow giữ nguyên, import created=0 |
| Relations | 343 follows và1 relates;350 quan hệ nguồn gồm6 integration trùng cặp dependency được giữ trong description/gap report |
| Native board | Basic board đã có53 Task cards; chỉ Epic/Task/Subtask enabled cho project |
| Private/auth | Rails readback: private project,5members,login_required,self-registration0,TOTP-only enforced,defaultadminlocked |
| Permission API | Anonymous/non-member không đọc project/work package;6PATCH sai role/direct completion bị422/403; không thay status |
| First login | HTTP login với password tạm vào form đổi mật khẩu bắt buộc của OpenProject; không tự đổi password/enroll TOTP |
| WebSocket local | HTTP Upgrade qua Caddy/Hocuspocus trả101 cả trước và sau khi cấu hình public; CSP chứa đúng hostname WSS hiện hành. Chưa chứng minh collaborative editing qua email PIN public end-to-end |
| Protected Quick URL | CLI có --allowed-mail; đúng5email/no wildcard; anonymous API trả302 sang login.trycloudflare.com/authorize; UI hiển thị Cloudflare Access |
| Restart | Recreate/restart app qua Start và Backup;329 việc,5members/Sprint in planning/TOTP/defaultadminlocked giữ nguyên |
| Secrets | Runtime ACL chỉ LUIM/SYSTEM; ngoài Git; token6actor kiểm thử đã thu hồi, outsider test account đã xóa |
| Local tests | 4Python assert/unit checks PASS; Python compile, PowerShell parse và Compose config PASS |
| Cô lập | Không gọi/chỉnh Jira MCP/bot/scheduler/credential/data; stack birdsong-retrieval vẫn running/healthy |

Các thao tác account/workflow/import dùng API v3 và Rails administration trong container riêng. Browser chỉ quan sát login/Cloudflare Access, không được gọi là Jira MCP hoặc bằng chứng authenticated E2E.

## Backup/restore

Backup database/assets/config có checksum, nằm ngoài Git với ACL private. Restore thử ban đầu vào `qldapm-openproject-restore-20261009152743` PASS:329 việc,parent/AC/assignee,workflow/TOTP,checksum attachments; stack thử đã dừng, volume giữ lại.

Bản backup vận hành cuối: `C:\Users\LUIM\AppData\Local\QLDAPM\openproject\backups\20261009-153438`. Restore vào `qldapm-openproject-restore-20261009153707` **PASS**: fingerprint28bảng lõi khớp hoàn toàn, gồm role permissions,password/TOTP,hierarchy,workflow,custom-field mappings và board; checksum attachments khớp. Stack test đã dừng và volume giữ lại. Không buộc dữ liệu sau khi làm việc phải quay về NEW.

Bản thử `20261009-153245` bị lỗi khi capture fingerprint và không có manifest hoàn tất, **không dùng để restore**. Những bản trước đó không có database-state fingerprint của phiên bản script cuối; bản được bàn giao để restore là `20261009-153438`.

## Chưa kiểm tra / cần người dùng

- Email PIN của một trong5người và từ chối một người có email đã xác minh ngoài allowlist. Đã xác minh challenge và CLI allowlist, chưa chứng minh bằng hai mailbox người thật.
- Tự đổi password, enrollment TOTP,recovery code,login OTP của người thật; authenticated UI cho từng role.
- Collaborative editing/WebSocket sau PIN+TOTP qua hostname mới; Quick URL rotation được quan sát nhưng login/WS public E2E còn thiếu.
- Restore cutover vào primary, reboot/sleep/recovery toàn máy,load/HA/security penetration test.
- Checklist/child-completion/evidence/concurrency gate,auto-parent và reviewer per-item là gap; không giả làm hard gate.

Quick Tunnel không SLA/SSE,hostname đổi khi Start; máy sleep/off mất truy cập. Có backup trên cùng máy chưa đủ chống hỏng ổ/mất máy. Chưa SMTP/SSO Enterprise hoặc Jira sync; không có chi phí add-on/trial.

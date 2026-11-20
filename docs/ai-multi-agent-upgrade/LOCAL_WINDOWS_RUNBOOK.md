# LOCAL WINDOWS RUNBOOK — user manually starts Docker; everything else restores

**16Oct n8n owner đã provision:** editor chỉ http://localhost:5678; một owner Community local, credential lưu một lần trong `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/n8n-owner/owner.json` với ACL owner/SYSTEM. Không nhập lại Gemini key hoặc tạo lại owner mỗi lần mở Docker. Không gửi file này qua chat/Git; không chạy user-management reset nếu mất quyền đăng nhập. Năm tài khoản nghiệp vụ vẫn dùng QLDAPM, không dùng chung editor owner.

**Workflow manual đã cài:** trong editor chọn `QLDAPM — Manual Gateway status (zero LLM)` rồi Execute workflow. Output của node `Gateway status` chứa trạng thái Gateway và `trace_id`; history lưu trong n8n. Workflow chỉ chạy khi chủ máy bấm, chưa có schedule; không gọi Gemini/ghi OpenProject. Hai credential header/HMAC lưu mã hóa trong volume n8n, master riêng ở private runtime; JSON workflow trong repo chỉ tham chiếu ID. Không dán key vào node parameters. Script enrollment dừng nếu phát hiện workflow đã được sửa, không ghi đè thay đổi của chủ máy.

**17Oct Daily brief đã cài trên staging:** `QLDAPM — Daily brief (5 roles, zero LLM)` đang active, lịch09:00 Asia/Bangkok và current-day catch-up khi n8n khởi động. Mỗi ngày chỉ giữ một receipt cho năm snapshot theo quyền native; lượt seed đầu17Oct execution2/5READY. Trong trang QLDAPM AI, card “Tóm tắt hôm nay” chỉ hiển thị snapshot của tài khoản đang đăng nhập, thời điểm UTC+7 và trace. Không có assignee/personnel trong snapshot, không dùng Gemini hoặc tự ghi nghiệp vụ. Manual status ở trên vẫn chỉ chạy bằng tay.

Chạy lại Daily trong cùng ngày trả cùng receipt, không làm mới snapshot hay tạo thông báo trùng. Nếu dữ liệu/quyền hiện tại đã đổi, UI ẩn số liệu cũ và báo STALE; dùng số liệu native hiện tại trên cùng trang. OFFLINE/DENIED không hiển thị snapshot cũ. Lượt collection bị ngắt được giữ FAILED_NO_REPLAY; không xoá SQLite/nonces để ép chạy lại. Bảo toàn trạng thái và kiểm tra history/trace; chính sách outage hoàn chỉnh tiếp tục ở P04-10. Test schedule/startup/restart/fresh restore trên clone đã PASS; không thay cho kiểm thử05thiết bị hoặc03vòng Desktop/sleep P09. Không cần nhập lại key/owner sau mỗi lần mở Docker.

Backup sidecar chỉ mount read-only thư mục owner riêng; bản sao private gồm `config/n8n-owner.json`, `n8n.sqlite`, `n8n-files.tar`, `n8n.key` và manifest SHA256. Một instance đã có owner mà thiếu credential backup sẽ báo lỗi. Khôi phục phải dùng đúng SQLite/files/encryption key/owner cùng bộ backup; không tạo encryption key mới cho dữ liệu cũ, không ghi đè volume live. Kiểm thử restore riêng trước khi xem xét cutover. n8n MCP catalog ngoài hệ thống đã tắt qua `N8N_DISABLED_MODULES=mcp-registry`; network automation vẫn internal.

**17Oct workflow JSON recovery:** hai source v1 ở `openproject/ai/automation/workflows/` đã lưu trong Git (commit local de7fe8f), chỉ credential ID/name. Admin có thể dùng `n8n_workflow_export.py --output <thư-mục-mới>` để export sau khi kiểm tra source/live khớp; thư mục cũ hoặc owner edits sẽ bị từ chối. Manifest lưu SHA256/source version và installed activation version riêng. JSON import luôn inactive; chỉ publish daily sau manual5READY. Empty-instance import/restart với owner/encryption key cũ đã thử trên clone; private encrypted credentials phải phục hồi riêng cùng key, tuyệt đối không đưa vào Git. Các lệnh này chỉ dùng khi admin backup/recovery, không phải bước mở Docker hằng ngày.

**LATEST15/10:** owner chọn Quick Tunnel thay Radmin. Trang vào ổn định trên host: http://localhost:18090, tự cập nhật public native HTTPS URL. Chỉ OpenProject được tunnel, privileged services vẫn private; không cần client CA/Radmin. Xem QUICK_TUNNEL_RUNBOOK.md; các đoạn LAN/Radmin phía dưới là scope trước. Gemini readiness riêng; key không nhập lại, native login có thể cần lại khi hostname đổi.

**P02 update16/10:** Gemini staging enabled under saved continuous-free-only consent, owner-confirmed Free/No billing account, existing key retained. Fixed synthetic smoke PASS18+6tokens; cached readiness bound to exact key/policy/model, current circuit overrides READY. Health/status do not call Gemini. No hourly key/proof entry. Old CONFIGURED_DISABLED/one-hour comments below are historical. Owner attestation/proof/readiness and keys must stay in private backups; never attach them to chat/source. Local attestation cannot detect an external administrator enabling Google billing; retain No billing account and reverify if changed.

## Implemented P01 staging operator —15/10/2026

Private backup sidecar is provisioned after initial image build: first due check120seconds after start, then hourly, at most1successful backup per24hours; missed days do not cause a flood. Output `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/local-backups`, owner/SYSTEM only, includes paired private keys; never share this folder.5GiB disk floor, no automatic backup deletion; inspect backup health/disk. Restore uses existing `jira_sync_backup.py rehearse --data-only --backup <private-folder>` plus `check_backup_sqlite.py <private-folder>`, always isolated temporary targets. Never restore over running main/staging from these commands. Actual data-only receipt is not permission to release/promote or qualify Jira imports.

P00gate PASS; pinned staging core/Gateway and new n8n/editor are provisioned. Normal day: open Docker Desktop, allow up to5minutes for cold health checks. One real engine restart restored all5services without commands/key entry;3cycle acceptance remains a separate task. Gemini currently CONFIGURED_DISABLED, not provider READY. n8n owner/workflows and Supervisor are later phase work.

Exception scripts live under `D:\AI project\QLDAPM chat\openproject\ai`:

- `Start-QLDAPM-Local.ps1`: initial overlay provision on existing audited staging or exception start; existing .venv/private runtime required. Uses locked existing images, no build/pull/seeder/main.
- `Status-QLDAPM-Local.ps1`: process health/exit/OOM and key presence; stopped_requires_repair is factual stopped state, not an inference that every exit was intentional.
- `Logs-QLDAPM-Local.ps1`: capture bounded logs to owner/SYSTEM private operator folder; logs may contain user data, do not paste/upload them wholesale.
- `Stop-QLDAPM-Local.ps1`: refuses active/unknown native jobs; stops only fixed staging containers and retains volumes/keys. This intentionally disables unless-stopped recovery for those containers.
- `Repair-QLDAPM-Local.ps1`: one-time restore after explicit Stop, checks ownership/image/key, starts DB/core/Gateway in health order and pinned idempotent overlay up-d. Missing/wrong-image core or DB fails closed and requires operator reconciliation; never creates/reseeds business data.

No script registers Task Scheduler, Windows service, Startup shortcut or login autorun. Radmin VPN service was already Automatic; this upgrade does not change it. New Radmin HTTPS is opt-in via operator `provision_local_stage.py --radmin`; see LAN_PREVIEW.md for actual acceptance, CA trust and remaining checks. Existing firewall remains enabled/unmodified by owner choice.

## Mục tiêu đúng của người dùng

**BÌNH THƯỜNG:** Windows đã bật → user **mở Docker Desktop** → đợi Docker engine/containers healthy → dùng OpenProject từ LAN; các agent/n8n/AI Gateway **tự** lên, credentials Gemini hiện có được load private runtime. Không cần bật auto-start Windows, Task Scheduler, shortcut startup, terminal, `docker compose up -d` hoặc nhập lại key.

**LẦN ĐẦU CHỈ MỘT LẦN:** Codex kiểm tra source/ports/backup, provision Compose+n8n+DB+agents, nạp credentials existing, setup URL LAN/TLS trusted cho 5 máy và 5 accounts, kiểm tra Free Tier/model/quota và chạy smoke. Không khẳng định zero-touch trước khi onboarding xong.

**NGOẠI LỆ:** Nếu ai đó manually stop container hoặc `compose down`, `unless-stopped` sẽ **không phục hồi container đã stop** chỉ bằng restart Docker. Admin dùng `Repair-QLDAPM-Local.ps1` một lần để `up -d` idempotently; Codex phải test và ghi rõ. Key invalid/Google 429/503 không thể 'tự làm Google sẵn sàng' bằng Docker: native app healthy, AI degraded với lý do.

## Existing target (phải xác minh thực tế)

| Environment | Main | Staging |
|---|---|---|
| OpenProject UI | localhost:8088 | localhost:18091 |
| Gateway | localhost:8090 | localhost:18092 |
| n8n | chưa có bằng chứng | thêm loopback 127.0.0.1:5678 nếu port rảnh |

**5 người dùng:** dùng **một** URL LAN của OpenProject (proxy + HTTPS trusted one-time), không cho user truy cập n8n editor (chỉ admin local), Gateway/DB không expose WAN/LAN trực tiếp. Không tự chọn IP, hostname, hoặc HTTPS trust kiểu bỏ xác minh. Nếu không có giải pháp HTTPS/trust phù hợp, Gate local-five-user chưa PASS và phải nêu blocker; không expose mật khẩu qua HTTP không tin cậy.

## Cấu hình Compose khuyến nghị (mẫu, KHÔNG tự thay compose hiện có)

```yaml
services:
  ai_gateway:
    restart: unless-stopped
    # giữ existing image/network/secret mounts; healthcheck không gọi Gemini
  n8n:
    restart: unless-stopped
    # 127.0.0.1:5678:5678; named volumes; N8N_ENCRYPTION_KEY từ secret store
  agent_runtime:
    restart: unless-stopped
    # internal Docker network only; optional if agent runs in gateway process
```

Gắn healthcheck native/SQLite/network theo dependencies và dịch vụ hiện có; không tách server mới nếu mã hiện hành tích hợp an toàn được. Docker Compose `restart: unless-stopped` chỉ phục hồi khi daemon/containers đáp ứng điều kiện đã được start thành công; **đừng quảng cáo guarantee**.

## PowerShell audit an toàn

```powershell
cd 'D:\AI project\QLDAPM chat'
docker version
docker compose version
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in 8088,8090,18091,18092,5678 }
git status --short
```

Không chạy `down -v`, `system prune`, `volume rm`, reset/stash/clean, seeder production. Audit actual project/container IDs trước restart. Nếu Desktop chưa chạy, admin mở bằng UI (không cài Windows Startup task).

## Tình huống thao tác

| Action | Người dùng cần làm | Kết quả kỳ vọng |
|---|---|---|
| Bật Windows | Không yêu cầu hệ thống tự lên | Docker vẫn tắt theo cài đặt manual |
| Mở Docker Desktop | **Một thao tác duy nhất** | Các containers đã provision trước đó restart, health pass; UI/agents/n8n có trạng thái |
| Tắt Docker Desktop | Không làm gì thêm | Services tắt; dữ liệu persistent |
| Mở lại Docker | Một thao tác | Pending jobs/volumes/quota ledger/credentials nguyên vẹn |
| Gemini free hết quota | Không mua gì | Chỉ AI chờ; OpenProject business data vẫn truy cập được |
| Có container bị stop thủ công | Admin chạy `Repair-QLDAPM-Local.ps1` (ngoại lệ) | Phục hồi idempotent; không tạo service trùng |
| Cần backup/restore | Theo backup script an toàn | WAL-consistent backup, restore tested staging |

## Acceptance thực tế

1. Stop Docker Desktop (không stop containers individually) → mở lại; chạy 3 vòng; so volumes/data/job ID.
2. Không cần nhập lại API key/project Gemini; free configured model readiness được kiểm tra thận trọng. Khi model 503/429 UI báo rõ chứ không để toàn hệ thống crash.
3. 20 accounts (2 PM, 3 BA, 5 FE, 5 BE, 5 QA) trên các thiết bị LAN truy cập HTTPS, login riêng biệt, role PM-only-write bảo toàn.
4. n8n scheduled jobs local và workflow JSON còn nguyên, catch-up không nhân job sau downtime.
5. `docker compose config`, health + regressions pass; native DB readback + receipts intact.
6. Không có Windows login startup automation, VPS, Internet port forwarding, n8n editor LAN public, paid API.
7. Điều phối AI: 20 user được quản lý bằng Fair-Share FIFO Queue, cách ly context người dùng, tự động hoãn khi cạn Free Quota mà không gây lỗi giao dịch.


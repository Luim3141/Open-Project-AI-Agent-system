# Five-user LAN topology, permissions and initial onboarding [SUPERSEDED]

> **LƯU Ý LỊCH SỬ:** Tài liệu này phản ánh giai đoạn 5 người dùng ban đầu. Đã được thay thế chính thức bởi [LAN_ACCESS_20_USERS.md](LAN_ACCESS_20_USERS.md) theo Change Request **CR-USER-CAPACITY-20** (hỗ trợ tối đa 20 người dùng LAN). File này được giữ lại làm bằng chứng lịch sử.

**LATEST OWNER15/10:** bỏ prerequisite Radmin máy khác, dùng Quick Tunnel public HTTPS chỉ OpenProject. Không cần local CA trust; CF TLS certificate dùng system trust. Native login/private projects/self-registration off vẫn bắt buộc, Gateway/DB/n8n không public. Mở http://localhost:18090 trên host để lấy link hiện tại, tự cập nhật khi connector restart. Các ghi chú Radmin/no-tunnel dưới đây là lịch sử bị quyết định này thay thế. Xem QUICK_TUNNEL_RUNBOOK.md.

**Owner update15/10/2026:** dùng mạng Radmin VPN đã tạo, host26.88.211.101, thay LAN vật lý; chọn Radmin thay Quick Tunnel. Owner cho phép tạm chưa thêm firewall allowlist từng peer; giữ Windows Firewall hiện hữu. Preview/evidence và giới hạn nghiệm thu tại `LAN_PREVIEW.md`. Quy tắc không tự bật tunnel bên dưới được áp dụng cùng authorization mới này; không mở public Quick Tunnel hoặc Gateway/n8n.

## One host, five people, one web address

- Host Windows Docker Desktop + WSL2, một OpenProject instance đã hiện hữu + n8n Community instance nội bộ. Five logins mapped to roles **PM/BA/FE/BE/QA**, no shared admin account.
- OpenProject frontend 1 hostname/IP trong **LAN private**, tốt nhất HTTPS thông qua existing Caddy/reverse proxy. Cấu hình local DNS/DHCP reservation hoặc hostname mDNS đáng tin; không yêu cầu Internet hostname/public DNS/VPS.
- Cài/trust local CA/cert trên thiết bị client là **bước đầu tiên duy nhất** nếu dùng self-signed/internal CA (tránh browser security warnings hằng lần). Codex phải phân biệt được việc thiết lập một lần với vận hành mỗi lần mở Docker.
- Windows Defender Firewall: chỉ inbound HTTPS từ subnet LAN Private đã kiểm chứng, không `0.0.0.0` cho DB/Gateway/n8n; n8n admin editor chỉ `127.0.0.1:5678`, password và volume encryption; router **KHÔNG port-forward**.
- Nếu thiết bị ở mạng khác, out of scope; không tự kích hoạt tunnel, public endpoint hay VPS.

## Permissions giữ nguyên policy host

| Role | Native read | Comment/report | Native write via AI | Workflow change |
|---|---|---|---|---|
| PM | Đúng membership | Có | Có qua preview + explicit approve + native gates | Không sửa n8n trực tiếp mặc định |
| BA | Có trong project | Có | Không | Không |
| FE | Có trong project | Có | Không | Không |
| BE | Có trong project | Có | Không | Không |
| QA | Có trong project | Có | Không | Không |

- N8n machine identity **read-only**, not acting as PM/admin; trigger AI proposals and notifications, not native business write.
- Owner/admin chỉ dùng n8n editor nội bộ. Vì n8n Community thiếu một số user/project/sharing features, **không cho 5 end-user cùng chỉnh workflow** (điều đó không cần cho use case).
- Dữ liệu Gemini API Free Tier: role ACL filter + classification/redaction trước khi gửi provider; approval của PM không override provider privacy policy.

## Initial setup vs day 2

**Initial provision by Codex/admin:** test 5 devices, local DNS/IP, TLS CA trust, user accounts, persistent Gemini existing credential, provider Free Tier, basic restore and n8n setup. Nếu cần thao tác user một lần (cài trusted CA/đăng nhập lần đầu) ghi rõ; không giả vờ hoàn toàn zero touch khi chưa setup.

**Everyday:** sau Windows đã bật, user mở Docker Desktop là stack tự phục hồi, người khác truy cập URL LAN đã cấu hình; không nhập key vào backend, không chạy Compose thủ công, không Google OAuth consumer login.

**Test matrix:** cross-role data leakage × 5 accounts, browser certificate validation × 5 devices, inactivity/session behavior, Gemini provider down, host IP change, firewall block from untrusted network.

# Quick Tunnel — native OpenProject staging

**Gemini16/10:** owner đã xác nhận Free/No billing account và lưu consent lâu dài; key cũ được dùng lại. Strict Free-only và fixed synthetic smoke thật PASS. Private config/proof/ledger giữ qua restart; không nhập key hoặc xác minh lại mỗi giờ. Status phân biệt authorization và cached READY/WAITING_QUOTA/PROVIDER_UNAVAILABLE; cached READY là lần kiểm thành công gần nhất, không bảo đảm Google đang online. Không thay billing/project/model bên Google; nếu thay phải xác minh lại. Không tự dùng paid fallback.

Owner15/10/2026 chọn Quick Tunnel thay Radmin và không cần thử máy Radmin khác để đi tiếp. Không đổi số người/quyền/free-only hoặc tự promote main.

Hằng ngày mở Docker Desktop, chờ khoảng2–3phút cho các service đã provision. Trên host mở **http://localhost:18090**: trang link tự refresh10giây, chỉ báo trạng thái OpenProject; chọn link HTTPS hiện tại và đăng nhập native account riêng. Có thể chia sẻ link cho5người. Không cần PowerShell/Compose/API key mỗi lần. URL trycloudflare đổi khi connector được tạo lại; cookie native gắn hostname nên người dùng có thể phải login lại, key Gemini vẫn trong backend private.

Tunnel chỉ tới http://staging-web:8080 trong Docker; metadata2000không publish, không tunnel Gateway/DB/n8n. n8n editor chỉlocalhost5678; link page chỉ127.0.0.1:18090 và chỉ mount folder public-link riêng, không credentials. Mọi project hiệnprivate, login_required=true, self_registration=0 được kiểm trước exposure. Không CF account/token/domain/paid plan hoặc email auth được tạo. Windows Firewall/profile/trust-store không đổi. Radmin proxy cũ được stop; CA/container/dữ liệu giữ để rollback.

Native wrapper đọc fixed private /quicktunnel metadata, chỉ nhận một hostname DNS hợp lệ trong trycloudflare.com; boot cùng core image hiện có, native HTTPS/Secure cookie/CSRF. Khi hostname thay đổi, chỉ web child shutdown graceful/boot lại, không migration/seeder/provider call hay replay native writes. Gateway retains uncertain-write/receipt rules. Host status/landing page phân biệt starting/ready; Gemini/n8n có readiness riêng.

Quick Tunnel là endpoint tạm cho development/test, không có uptime guarantee,200inflight và không hỗ trợ SSE. Assistant hiệnpoll GET. Khi Cloudflare/network mất: trang localhost vẫn có last URL/status; không hứa remote luôn READY. Không chuyển sang paid/fixed-domain service tự động. Nguồn: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/ và pinned cloudflared2026.10.0 /quicktunnel + tunnel ready CLI đã kiểm thực.

Exception Start/Repair/Stop/Status scripts vẫn dùng được. Stop dừng cả connector và giữ volumes/keys. Normal Docker daemon restart dùng unless-stopped, không phải manual container stop. Rollback operator: giữ source/config backup trước switch, dừng riêng quick-tunnel, provision overlay Radmin nếu được chọn lại; không restore DB/ledger cũ để rollback URL. Không bật old Gateway public profile.

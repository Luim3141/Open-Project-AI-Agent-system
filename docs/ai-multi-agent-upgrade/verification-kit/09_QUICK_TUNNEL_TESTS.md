# 09 — CLOUDFLARE QUICK TUNNEL: CHÍNH THỨC ĐƯỢC CHẤP NHẬN

**Yêu cầu owner:** Giữ Cloudflare Quick Tunnel (`trycloudflare.com`) làm kênh truy cập từ Internet tới QLDAPM local. Không xoá container `quick-tunnel`, không đổi sang LAN-only, không tự thay domain/tunnel kiểu khác.

## Giới hạn Cloudflare cần hiểu
Tài liệu chính thức: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/
- Quick Tunnel tạo hostname tạm; có thể đổi mỗi khi `cloudflared` restart. Không thể nghiệm thu như tên miền cố định.
- Dành cho thử nghiệm, không có SLA/uptime guarantee; Cloudflare ghi nhận trần 200 in-flight requests và không hỗ trợ SSE. Không giả định mọi streaming mode hoạt động; kiểm tra WebSocket riêng.
- Theo bản docs 2026 có option `--allowed-mail` để hạn chế bằng email OTP, nhưng phải kiểm tra binary local `cloudflared tunnel --help`/CLI thực tế và nhu cầu của 20 users trước khi đưa vào config; không phải bắt buộc.

## Preflight bắt buộc (KHÔNG tắt tunnel)
- [ ] Inspect `cloudflared` image/version, args, target local service và proxy chain Caddy/OpenProject; không leak token/hostname khi viết public report.
- [ ] Đường dẫn người dùng và cổng n8n editor/Postgres/Gateway operator tách biệt; verify route whitelist và origin allowlist.
- [ ] Determine public HTTPS URL currently used; test URL belongs to **owner-created tunnel**, không scan Internet người khác.
- [ ] Kiểm tra Rails `Host`/X-Forwarded-Proto/CSRF origin, proxy trusted lists, `Secure`+`HttpOnly`+`SameSite` cookie.

## Remote verification, low-rate only
- [ ] From **different network** (LTE/5G): TLS succeeds; login page loads.
- [ ] Unauthenticated request to known protected WP URL is denied or login redirect; MUST assert actual private content absent.
- [ ] PM authenticated reads and authorized write test on disposable stage; non-PM cannot mutate.
- [ ] Two independent accounts cannot reuse each other's cookie, cannot access other's private chat/audit.
- [ ] Logout invalidates session and block stale session access.
- [ ] CSRF invalid/replayed request rejected; signed UI bridge is not public machine API.
- [ ] n8n admin/editor, local operator, Docker daemon, Postgres/SQLite, internal signed bridge, monitoring secrets are not unintentionally exposed.
- [ ] Unexpected guessed paths return correct deny; do not fuzz/brute-force or perform active scanning against tunnel.
- [ ] Check redirects do not rewrite to `localhost`/internal IP; health/errors do not disclose env, path or keys.
- [ ] Inspect WebSocket and SSE if app uses them; if SSE breaks, propose bounded polling fallback and test realtime behavior after fix.

## Controlled restart acceptance
Only after owner approval and backup of stage config:
1. Capture before restart: current public hostname **privately**, service target, browser auth status; no public log of hostname.
2. Restart **tunnel service only**, not database or main app. Observe cloudflared logs and `docker compose ps`.
3. Discover current hostname after startup, re-run small HTTPS/login smoke from external network.
4. Verify app survives tunnel URL change. Document manual/automated way owner shares new address with 20 allowed users.
5. If tunnel fails but LAN works, diagnose Cloudflare/edge/QUIC/port network separately; do not rebuild OpenProject.

## Security decision if public route unsafe
- **Không tắt tunnel làm giải pháp đầu tiên.** Find root cause at proxy route/host auth, lock n8n editor/internal APIs, implement app authentication+rate limits, update test.
- If P0 data leak cannot be remediated immediately, STOP unsafe external testing, báo owner và đề xuất giới hạn route tạm thời **chỉ khi được owner phê duyệt**, bảo toàn intent về remote access.
- Quick Tunnel random hostname không phải authentication. User authorization vẫn ở Rails/native gateway.

## Không kiểm thử như thế nào
- Không dùng k6 20 users stress lên trycloudflare.com. Đo 20 users trên LAN/stage; qua tunnel chỉ smoke remote 1–2 users.
- Không chạy OWASP ZAP active attack qua tunnel. Không dò subdomain hay endpoints bên thứ ba.
- Không hardcode Cloudflare URL của hôm nay vào frontend/API config như URL vĩnh viễn.

## Deliverable
`QUICK_TUNNEL_ACCESS_AUDIT.md`: source SHA, cloudflared version, target/proxy summary, network vantage point, HTTPS/auth/role results, anonymous checks, internal route exposure, session/cookie/CSRF, URL rotation, streaming compatibility, remediation+retest, limits and remaining risk. Tài liệu public phải che URL/session IDs và secrets.

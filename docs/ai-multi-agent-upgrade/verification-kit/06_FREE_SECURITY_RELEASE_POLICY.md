# 06 — FREE + SECURITY POLICY (CÓ QUICK TUNNEL)

## Bất biến được owner xác nhận
- Máy Windows + Docker Desktop/WSL2 là server thực; không VPS; tối đa 20 người dùng; nhiều role cùng user, nhiều user cùng role.
- Cloudflare **Quick Tunnel được yêu cầu và phải giữ** để truy cập từ xa. Public URL là do Cloudflare cấp động; không đồng nghĩa public được DB, n8n editor hoặc private Gateway API.
- n8n Community tự host, không bắt user mua n8n Cloud.
- Gemini API Free Tier hợp lệ và dùng quota chung; Google AI Pro subscription **không** đồng nghĩa billing API free unlimited. Không tạo paid Google project, không nâng tier, không auto-enable billing.
- Không triển khai GitHub Research sản phẩm. Research GitHub để lập trình/QA được phép, phải kiểm tra nguồn.
- Không yêu cầu 20 Gemini calls đồng thời. Hệ thống phải phục vụ 20 users bằng application sessions và queue có giới hạn.
- Policy RBAC stage hiện hành PM-only-write, gate/receipt/consent/idempotency, native authoritative DB, audit actor scope.

## Chính sách Quick Tunnel
1. Chỉ proxy qua entrypoint được thiết kế cho remote người dùng, có login/session. Không expose Postgres, n8n editor, Docker daemon, operator endpoints, machine bearer tokens, signed UI bridge.
2. Owner có thể bật biện pháp bảo vệ email OTP `cloudflared --allowed-mail` nếu phiên bản cloudflared và nhu cầu người dùng tương thích; phải xác minh cờ và danh sách email thực. Không coi cờ đó thay thế Rails/RBAC.
3. Kiểm tra cookies session HTTPS/Secure/SameSite, CSRF, redirect loops, trusted proxy headers, logout, session expiry, IDOR và error pages có leak.
4. URL thay đổi theo restart là đặc tính Quick Tunnel, phải có cơ chế tìm URL mới và cung cấp có kiểm soát cho nhóm 20 người. Nếu cần URL cố định, đưa ra trade-off named tunnel/domain nhưng **không tự thay đổi** khi người dùng chưa đồng ý.
5. Quick Tunnel dành cho thử nghiệm/phát triển, không có SLA; với use case nội bộ của owner, báo rõ giới hạn uptime/SSE/200 in-flight nhưng đừng coi nó là defect nếu vẫn đạt use case. Không được cam kết vận hành 24/7.
6. Internet smoke chỉ low rate và test app của mình. 20-user stress/load chạy direct LAN/staging, không stress Cloudflare public edge.

## Quy tắc secret / chi phí
- Không in key, token, cookies, n8n credentials, connection strings vào test output, prompt hoặc screenshots.
- Policy flags trong YAML/code chỉ là intent. Xác minh usage tier, billing project trong AI Studio/Cloud Console bằng quyền owner. Nếu thiếu bằng chứng, kết quả `BLOCKED_BILLING_VERIFICATION`, không khẳng định 0 đồng tuyệt đối.
- Model name và quota lấy từ project/API thực, không dùng hard-coded report 15RPM/250kTPM/500RPD làm sự thật. Reset rate limits dựa nguồn API/docs và timezone thích hợp; test bằng clock fake.
- Backup+restore trước destructive staging test; main/live data không bị xóa hoặc ghi đè. Giữ quyền cấp credential của user.

## Priorities
**P0:** mất dữ liệu, vượt phân quyền, bị lộ private endpoints/secret qua tunnel, paid billing không được đồng ý, không có rollback; chặn phát hành.
**P1:** lỗi nghiệp vụ chính, 20-session không đạt theo acceptance, 429/503 gây mất receipt, n8n duplicate writes, restore fail; khắc phục hoặc owner xác nhận giới hạn.
**P2:** UI polish, latency chưa tối ưu, minor docs; có thể đưa vào backlog nếu không gây nguy hiểm.

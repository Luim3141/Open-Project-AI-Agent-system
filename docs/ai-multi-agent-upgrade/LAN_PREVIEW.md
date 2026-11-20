# P01-11 — Radmin VPN preview, chưa áp dụng

**Actual deployed15/10/2026:** staging HTTPS26.88.211.101:443, same pinned core image with native hostname/HTTPS environment, independent Caddy internal CA persisted privately. TLS1.3 + native login/CSRF/Secure cookie PASS on host; wrong hostname rejected; Wi-Fi443/localhost443 and VPN Gateway/n8n/DB ports refuse host TCP. Evidence artifacts/P01-11-host-https-final.json. Public CA + fingerprint/trust instructions in certs/README.md. No firewall/profile/Windows trust-store change. P01-11 REVIEW pending one-time client trust and remote access; no claim5clients or firewall allowlist.

**Owner update15/10/2026:** yêu cầu LAN ảo Radmin hoặc Quick Tunnel, xác nhận đã tạo mạng Radmin; cho phép tạm chưa thêm firewall allowlist từng peer. Chọn Radmin đã cài, IP26.88.211.101. Giữ Windows Firewall hiện bật cả3profiles và không đổi rule/profile/router. Dự kiến HTTPS bind riêng26.88.211.101:443; native login/TLS trust vẫn bắt buộc, DB/Gateway/n8n không expose VPN. Chưa biết4peerIPs và chưa test5client. Không tuyên bố giới hạn đúng5thiết bị bằng firewall hoặc đã nghiệm thu LAN. Không hỏi lại IP khi owner đã cho phép hoãn. Nếu existing firewall chặn, báo kết quả thực trước thay đổi.

Các dòng physical Wi-Fi bên dưới là preview lịch sử, đã được owner thay thế bằng Radmin; chưa áp dụng.

Observed15/10/2026: physical Wi-Fi profile **Bang Lai Xe T3**, address **192.168.1.124/24**, DHCP, currently **Public**. Radmin VPN26.88.211.101/8 và các VMware/WSL networks không thuộc LAN được chọn.

Đề xuất phạm vi sau khi owner xác nhận đây là mạng riêng tin cậy của năm người:

- Một HTTPS endpoint cho OpenProject trên Wi-Fi192.168.1.124:443, inbound chỉ192.168.1.0/24 và interface Wi-Fi/Private; không bind Radmin VPN/all interfaces. DB/Gateway/n8n giữ private/loopback.
- Local CA/certificate trust cài một lần trên năm client. Không bỏ xác minh TLS/browser warning. Native login riêng PM/BA/BE/FE/QA; admin/editor n8n chỉ host.
- Cần endpoint ổn định: owner router DHCP reservation hoặc local DNS được kiểm chứng. Chưa coi DHCP hiện tại là fixed IP. Không đổi IP/network profile/firewall/trust store/router hoặc hostname native trong lượt preview.
- Ban đầu thử staging có native gates; main giữ deployment riêng cho tới P10 approved promotion. Native hostname/HTTPS/signed bridge/internal API phải được test trước khi mở endpoint; không proxy bằng cách giả kết quả login hoặc bỏ origin/CSRF.
- Rollback đề xuất: tắt riêng LAN proxy/rule mang tên QLDAPM, giữ source DB/volumes/keys và localhost18091/18092. Không thay rule hệ thống hoặc xóa CA không thuộc deployment này.

Thông tin owner cần xác nhận: Wi-Fi này có phải mạng tin cậy của nhóm, và năm thiết bị có thể onboarding/trust cert hay chưa. Nếu chưa, giữ localhost; P01 LAN gate chưa thể PASS và không gọi đó là five-user acceptance.

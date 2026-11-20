# Demo startup checklist

1. Đăng nhập Windows bằng tài khoản LUIM đang sở hữu Task, khởi động Docker Desktop và đợi engine sẵn sàng. Task/worker và WSL OpenClaw tự khởi động; không cần mở thêm worker hay gõ lệnh start.
2. Mở [AI Control Center](http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai). Nếu hết phiên, đăng nhập Owner/MFA bình thường.
3. Chờ CONNECTED; System Integrations: Gateway/Core/n8n healthy; Mission: OpenClaw READY, Worker ALIVE. Nếu đang SERVICE_STARTING/DISCONNECTED, chờ retry hội tụ; không bật AUTO để sửa kết nối.
4. Kiểm desired/effective PAUSED, delegation OFF, READY/ACTIVE queue0. Provider READINESS_STALE sau5phút là contract thật; mở dashboard không gọi inference. Không hứa một task AI mới chạy được khi gate còn stale/unavailable.
5. Demo an toàn: xem existing runs/Inspector và sáu WP READY FOR RELEASE; GitHub Sync; Reports → Xem toàn văn/Raw/Copy/Export; deterministic Sprint Risk → WF08 receipt. Không replay385/391/394. OFF→AUTO_IDLE→PAUSE chỉ khi vẫn không eligible work; không dùng AUTO nếu có việc mới.
6. Schedule UI: Daily08:00, WeeklyMonday09:00 (UTC+7), daemon Gateway độc lập. WF12 n8n là Friday17:00, Save UI không đổi WF12. Không chỉnh giờ chỉ để demo nếu không cần.
7. Kết thúc: PAUSED, delegation OFF, queue0, không có active run; đóng modal. Nếu runtime còn DOWN, giữ PAUSED và đọc lý do, không tạo task/provider retries để ép xanh.

Phạm vi chứng minh restart: Gateway/OpenClaw/n8n và coordinated QLDAPM10containers đã thử; **Docker Desktop restart thực, WSL distro termination và Windows reboot chưa thử** vì workload/phiên khác. Không được gọi fallback này là full cold-boot PASS. RAG FAILED/FROZEN.

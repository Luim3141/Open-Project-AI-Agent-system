# Bảo mật

Repository là source snapshot; không có cam kết hỗ trợ phiên bản hay SLA bảo mật. Dùng commit đã kiểm tra, dependencies đã pin và quyền tối thiểu.

## Báo cáo lỗ hổng

Không đăng secrets, payload chứa dữ liệu thật hoặc hướng dẫn khai thác một hệ thống đang chạy vào public issue. Nếu repository có **Security → Report a vulnerability**, dùng kênh đó. Nếu chưa bật, liên hệ owner qua kênh riêng đã xác minh; không tự suy đoán địa chỉ liên hệ.

## Secrets và runtime

- Tạo credentials mới trên máy triển khai; giữ ngoài Git, ưu tiên private runtime và ACL.
- `.env.example` chỉ mô tả biến, không chứa giá trị thật. Không commit `.env`, session/browser state, TOTP seed, database hay backup.
- Sau khi stage file đã xem, quét `python scripts/check_publication.py` trước commit. Công cụ kiểm tra pattern trên Git index; chạy thêm `python -m unittest discover -s tests -p test_secret_redaction_guard.py` cho credential digest lịch sử. Các kiểm tra này không chứng minh tuyệt đối không có secrets.
- Nếu đã lộ credential: thu hồi/rotate ngay, kiểm audit, sau đó xử lý history theo kế hoạch riêng. Xóa khỏi commit mới không thu hồi giá trị cũ.
- Không mở dịch vụ nội bộ ra Internet trước khi xác minh authentication, TLS, RBAC và phạm vi tunnel.

CI không có production secrets và không chạy live model/Jira/Telegram/Docker mutation.

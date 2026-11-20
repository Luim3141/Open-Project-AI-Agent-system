# QLDAPM Radmin TLS — initial client trust

Staging URL: **https://26.88.211.101**. Máy client phải ở cùng mạng Radmin đã tạo; dùng native account riêng PM/BA/BE/FE/QA. n8n editor vẫn chỉ host localhost:5678.

Chỉ file `QLDAPM-Radmin-Root-CA.crt` trong thư mục này là public. Không chuyển file `.key`, private runtime hoặc backup cho client. SHA256 certificate DER đã kiểm tra trên host:

`81abba0b41f846fe345f9200a7a3e258bd9bc1d80bc5a1efbdef7b9e450df957`

Client Windows kiểm tra fingerprint rồi import certificate này vào **Current User → Trusted Root Certification Authorities** một lần, chỉ sau khi chủ thiết bị chấp nhận CA của host. Có thể dùng Certificate Import Wizard trên file public này; không cần admin máy để cài Current User. Không chọn bỏ qua browser warning, không dùng certificate từ người lạ. Những máy khác dùng trust store tương ứng; cần kiểm tra thực trên từng trình duyệt/thiết bị.

Host đã test TLS1.3, hostname validation, native login/CSRF/Secure cookie và các port khác không lắng nghe trên VPN. **Chưa import CA vào trust store Windows/client và chưa test5thiết bị.** Windows Firewall giữ nguyên theo yêu cầu owner; nếu peer bị chặn, cần kiểm tra thực trước khi thêm rule giới hạn. Không tắt firewall để thử.

CA private key lưu ngoài Git trong owner/SYSTEM runtime `radmin-caddy`, được Caddy sử dụng lại sau Docker restart; không tạo CA mới mỗi phiên. Rollback access: dừng riêng radmin-proxy, giữ dữ liệu/keys; client có thể gỡ đúng certificate fingerprint trên khi không còn dùng hệ thống.

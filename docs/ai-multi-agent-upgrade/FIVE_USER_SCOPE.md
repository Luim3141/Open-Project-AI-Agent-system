# P00-11 — Five-user scope / native identities

Scope do chủ dự án chốt: đúng 5 business users PM/BA/BE/FE/QA trong cùng trusted LAN. Giữ tài khoản native hiện có; không tạo lại/đổi credential, không dùng chung admin. Native IDs không dùng lẫn giữa main/staging.

| Role | Main project5 | Staging project3 |
|---|---|---|
| PM | user19 / ba-pm | user7 / pm |
| BA | user20 / pm | user6 / ba-pm |
| BE | user21 / be | user8 / be |
| FE | user22 / fe | user9 / fe |
| QA | user23 / qa | user10 / qa |

Danh tính/membership/active/non-admin và quyền effective đã đọc thật từ native Rails trong read-only transaction; `artifacts/P00-06-native-role-matrix.json`. Stage Administrator12 giữ riêng ngoài năm business identities; không thay thế PM hoặc machine identity. Cả ba project hiện có và mọi membership khác được giữ nguyên; agent chỉ project QLDAPM được cấp quyền.

Staging có PM-only business write, mọi role read/comment; main còn quyền legacy như `RBAC_FREEZE.md`, chưa được nâng cấp. Không coi test account staging là đăng nhập bằng năm người thật trên LAN; password/TOTP enrollment và bốn Bearer hết hạn cần quy trình riêng.

Network readiness: **NOT_READY**. Host profile của LAN Wi-Fi hiện Public, thêm Radmin VPN cũng Public; chưa xác nhận subnet tin cậy/IP reservation/DNS, local TLS CA và năm thiết bị. P01-11 phải thiết lập đúng LAN vật lý, không coi VPN là LAN được duyệt; DB/Gateway/n8n giữ private/loopback, không WAN/router-forward/tunnel. Chưa thay network profile/firewall/trust store. Chưa chạy LAN/browser acceptance. Scope được chốt, deployment gate còn mở.
